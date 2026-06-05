"""
Cloudflare R2 storage — upload PDFs and generate presigned download URLs.

Both functions are synchronous and must be called from a thread (run_in_executor),
never directly from the async event loop.

Key convention: pdfs/{exp_id}.pdf — deterministic; put_object overwrites on retry.
Store only the key in the DB; generate a fresh presigned URL on demand.
"""

from typing import Protocol

import boto3
from botocore.config import Config as BotocoreConfig


class R2Config(Protocol):
    """Structural interface — any object with these attributes is accepted."""

    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    region: str


def _client(cfg: R2Config):
    return boto3.client(
        "s3",
        endpoint_url=cfg.endpoint,
        aws_access_key_id=cfg.access_key,
        aws_secret_access_key=cfg.secret_key,
        region_name=cfg.region,
        config=BotocoreConfig(
            signature_version="s3v4",
            s3={"addressing_style": "path"},  # required for R2
        ),
    )


def check_connection(cfg: R2Config) -> None:
    """Verify R2 is reachable and the bucket exists. Raises on any failure."""
    _client(cfg).head_bucket(Bucket=cfg.bucket)


def upload_pdf(pdf_bytes: bytes, key: str, cfg: R2Config) -> None:
    """Upload PDF bytes to R2 at *key*. Raises on any error — no fallback."""
    _client(cfg).put_object(
        Bucket=cfg.bucket,
        Key=key,
        Body=pdf_bytes,
        ContentType="application/pdf",
    )


def presign_download(key: str, cfg: R2Config, filename: str, expires_in: int = 900) -> str:
    """Return a presigned GET URL for *key* with a suggested download filename.

    The ResponseContentDisposition is signed into the URL so it cannot be
    tampered with. Default TTL: 15 minutes. Never store the returned URL.
    """
    return _client(cfg).generate_presigned_url(
        "get_object",
        Params={
            "Bucket": cfg.bucket,
            "Key": key,
            "ResponseContentDisposition": f'attachment; filename="{filename}"',
        },
        ExpiresIn=expires_in,
    )
