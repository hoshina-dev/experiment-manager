"""OpenTelemetry setup and request log correlation."""

import logging
import time
from dataclasses import dataclass
from importlib import import_module
from typing import Any

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import format_span_id, format_trace_id
from opentelemetry.trace.propagation import tracecontext

logger = logging.getLogger(__name__)
request_logger = logging.getLogger("experiment_manager.request")

_providers: "TelemetryProviders | None" = None
_sqlalchemy_instrumented = False
_botocore_instrumented = False


@dataclass
class TelemetryProviders:
    tracer_provider: TracerProvider
    meter_provider: MeterProvider


class RequestLoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status = 500

        async def send_wrapper(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = int(message["status"])
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            latency_ms = int((time.perf_counter() - start) * 1000)
            client = scope.get("client")
            ip = client[0] if client else ""
            span_context = trace.get_current_span().get_span_context()

            message = (
                "request completed method=%s path=%s status=%s latency_ms=%s ip=%s"
            )
            args: list[Any] = [
                scope["method"],
                scope.get("path", ""),
                status,
                latency_ms,
                ip,
            ]

            if span_context.is_valid:
                message += " trace_id=%s span_id=%s"
                args.extend(
                    [
                        format_trace_id(span_context.trace_id),
                        format_span_id(span_context.span_id),
                    ]
                )

            request_logger.log(
                logging.ERROR if status >= 500 else logging.INFO, message, *args
            )


def setup_telemetry(
    app: FastAPI,
    *,
    enabled: bool,
    service_name: str,
    otlp_endpoint: str | None = None,
    sqlalchemy_engine=None,
) -> TelemetryProviders | None:
    """Initialise OpenTelemetry providers and auto-instrument FastAPI."""
    app.add_middleware(RequestLoggingMiddleware)

    if not enabled:
        logger.info("opentelemetry disabled")
        return None

    global _providers
    if _providers is None:
        if not service_name:
            service_name = "experiment-manager"

        endpoint = otlp_endpoint or None
        resource = Resource.create({SERVICE_NAME: service_name})

        otlp_trace_exporter = import_module(
            "opentelemetry.exporter.otlp.proto.grpc.trace_exporter"
        ).OTLPSpanExporter(endpoint=endpoint)
        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))
        trace.set_tracer_provider(tracer_provider)

        otlp_metric_exporter = import_module(
            "opentelemetry.exporter.otlp.proto.grpc.metric_exporter"
        ).OTLPMetricExporter(endpoint=endpoint)
        meter_provider = MeterProvider(
            metric_readers=[PeriodicExportingMetricReader(otlp_metric_exporter)],
            resource=resource,
        )
        metrics.set_meter_provider(meter_provider)

        set_global_textmap(
            CompositePropagator(
                [
                    tracecontext.TraceContextTextMapPropagator(),
                    W3CBaggagePropagator(),
                ]
            )
        )

        _providers = TelemetryProviders(
            tracer_provider=tracer_provider,
            meter_provider=meter_provider,
        )

    _instrument_dependencies(sqlalchemy_engine)
    FastAPIInstrumentor.instrument_app(app)
    logger.info("opentelemetry initialized service=%s", service_name)
    return _providers


def shutdown_telemetry(providers: TelemetryProviders | None) -> None:
    if providers is None:
        return

    errors: list[Exception] = []
    try:
        providers.tracer_provider.shutdown()
    except Exception as exc:
        errors.append(exc)

    try:
        providers.meter_provider.shutdown()
    except Exception as exc:
        errors.append(exc)

    global _providers
    _providers = None

    if errors:
        raise errors[0]


def _instrument_dependencies(sqlalchemy_engine) -> None:
    global _botocore_instrumented, _sqlalchemy_instrumented

    if not _botocore_instrumented:
        BotocoreInstrumentor().instrument()
        _botocore_instrumented = True

    if sqlalchemy_engine is not None and not _sqlalchemy_instrumented:
        SQLAlchemyInstrumentor().instrument(engine=sqlalchemy_engine)
        _sqlalchemy_instrumented = True
