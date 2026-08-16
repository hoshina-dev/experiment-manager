from types import SimpleNamespace

from app.pdf.r2_client import presign_download


def test_presign_download_prefers_public_url_for_cdn_delivery():
    cfg = SimpleNamespace(
        endpoint="https://example.invalid",
        access_key="",
        secret_key="",
        bucket="reports",
        region="auto",
        public_url="https://d111111abcdef8.cloudfront.net/",
    )

    assert (
        presign_download("pdfs/exp-123.pdf", cfg, "report.pdf")
        == "https://d111111abcdef8.cloudfront.net/pdfs/exp-123.pdf"
    )