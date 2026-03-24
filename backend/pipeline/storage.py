"""Cloudflare R2 storage for PDF files."""

from pathlib import Path

import boto3

from app.config import settings


class R2Storage:
    """Upload and manage PDF files in Cloudflare R2."""

    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",
        )
        self.bucket = settings.r2_bucket_name

    def upload_pdf(self, local_path: str | Path, object_key: str) -> str:
        """Upload a PDF to R2 and return the public URL."""
        local_path = Path(local_path)
        self.client.upload_file(
            str(local_path),
            self.bucket,
            object_key,
            ExtraArgs={"ContentType": "application/pdf"},
        )
        return f"{settings.r2_endpoint}/{self.bucket}/{object_key}"

    def download_pdf(self, object_key: str, local_path: str | Path) -> None:
        """Download a PDF from R2."""
        self.client.download_file(self.bucket, object_key, str(local_path))

    def get_presigned_url(self, object_key: str, expires_in: int = 3600) -> str:
        """Generate a presigned URL for temporary access."""
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": object_key},
            ExpiresIn=expires_in,
        )

    def list_pdfs(self, prefix: str = "") -> list[str]:
        """List all PDF keys in the bucket."""
        response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        return [obj["Key"] for obj in response.get("Contents", [])]
