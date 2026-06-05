"""OpenTelemetry setup: TracerProvider, exporter selection, and FastAPI auto-instrumentation."""

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_telemetry(
    app: FastAPI, service_name: str, otlp_endpoint: str | None = None
) -> None:
    """Initialise the global TracerProvider and auto-instrument FastAPI.

    When ``otlp_endpoint`` is set, spans are exported via OTLP/HTTP (e.g. to
    Jaeger or an OTel Collector).  Otherwise they are printed to stdout, which
    is useful during local development.
    """
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    # no endpoint → no exporter, spans are created but silently discarded

    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
