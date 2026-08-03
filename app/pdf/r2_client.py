"""
S3 / Cloudflare R2 storage — upload PDFs and generate presigned download URLs.

Both functions are synchronous and must be called from a thread (run_in_executor),
never directly from the async event loop.

Key convention: pdfs/{exp_id}.pdf — deterministic; put_object overwrites on retry.
Store only the key in the DB; generate a fresh presigned URL on demand.

Supports:
- AWS S3 with IAM roles (ECS, EC2, Lambda)
- AWS S3 with local AWS credentials (`aws configure`)
- Cloudflare R2 (static access keys)
- Other S3-compatible storage (MinIO, LocalStack)
"""

from typing import Protocol

import boto3
from botocore.config import Config as BotocoreConfig


class S3Config(Protocol):
    """Structural interface — any object with these attributes is accepted."""

    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    region: str


def _client(cfg: S3Config):
    """Create an S3 client.

    Credential resolution:
    - If access_key + secret_key are provided, use them (R2, MinIO, etc.).
    - Otherwise, let boto3 use its default credential chain
      (IAM Role, ~/.aws/credentials, environment variables, etc.).
    """

    kwargs = {
        "region_name": cfg.region,
    }

    # Custom endpoint (Cloudflare R2, MinIO, LocalStack, etc.)
    if cfg.endpoint:
        kwargs["endpoint_url"] = cfg.endpoint
        kwargs["config"] = BotocoreConfig(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        )
    else:
        kwargs["config"] = BotocoreConfig(
            signature_version="s3v4",
        )

    # Optional static credentials
    if cfg.access_key and cfg.secret_key:
        kwargs["aws_access_key_id"] = cfg.access_key
        kwargs["aws_secret_access_key"] = cfg.secret_key

    return boto3.client("s3", **kwargs)


def check_connection(cfg: S3Config) -> None:
    """Verify storage is reachable and the bucket exists."""
    _client(cfg).head_bucket(Bucket=cfg.bucket)


def upload_pdf(pdf_bytes: bytes, key: str, cfg: S3Config) -> None:
    """Upload PDF bytes to storage at *key*."""
    _client(cfg).put_object(
        Bucket=cfg.bucket,
        Key=key,
        Body=pdf_bytes,
        ContentType="application/pdf",
    )


def presign_download(
    key: str,
    cfg: S3Config,
    filename: str,
    expires_in: int = 900,
) -> str:
    """Return a presigned GET URL for *key*.

    The ResponseContentDisposition is signed into the URL so it cannot be
    tampered with. Default TTL: 15 minutes. Never store the returned URL.
    """
    return _client(cfg).generate_presigned_url(
        "get_object",
        Params={
            "Bucket": cfg.bucket,
            "Key": key,
            "ResponseContentDisposition": (
                f'attachment; filename="{filename}"'
            ),
        },
        ExpiresIn=expires_in,
    )
