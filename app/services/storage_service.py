from __future__ import annotations

import os
import io
from typing import Optional
from datetime import datetime

class StorageService:
    def upload_bytes(self, path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        raise NotImplementedError

class LocalStorage(StorageService):
    def __init__(self, base_dir: str = "uploads/exports", base_url: Optional[str] = None) -> None:
        self.base_dir = base_dir
        self.base_url = base_url  # optional CDN/static mapping
        os.makedirs(self.base_dir, exist_ok=True)

    def upload_bytes(self, path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        full_path = os.path.join(self.base_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data)
        if self.base_url:
            return f"{self.base_url.rstrip('/')}/{path}"
        # return relative file path by default
        return full_path

class S3Storage(StorageService):  # optional, not used in tests
    def __init__(self, bucket: str, prefix: str = "exports/") -> None:
        self.bucket = bucket
        self.prefix = prefix
        try:
            import boto3  # type: ignore
            self.client = boto3.client("s3")
        except Exception as e:
            raise RuntimeError("boto3 not available") from e

    def upload_bytes(self, path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        key = f"{self.prefix}{path}"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return f"s3://{self.bucket}/{key}"

class GCSStorage(StorageService):  # optional, not used in tests
    def __init__(self, bucket: str, prefix: str = "exports/") -> None:
        self.bucket = bucket
        self.prefix = prefix
        try:
            from google.cloud import storage  # type: ignore
            self.client = storage.Client()
            self._bucket = self.client.bucket(bucket)
        except Exception as e:
            raise RuntimeError("google-cloud-storage not available") from e

    def upload_bytes(self, path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        key = f"{self.prefix}{path}"
        blob = self._bucket.blob(key)
        blob.upload_from_string(data, content_type=content_type)
        return f"gs://{self.bucket}/{key}"


def get_storage() -> StorageService:
    provider = (os.getenv("CLOUD_STORAGE_PROVIDER") or "local").lower()
    if provider == "local":
        return LocalStorage()
    if provider == "s3":
        bucket = os.getenv("AWS_S3_BUCKET")
        if not bucket:
            raise RuntimeError("AWS_S3_BUCKET is required for s3 storage")
        return S3Storage(bucket=bucket)
    if provider == "gcs":
        bucket = os.getenv("GCS_BUCKET")
        if not bucket:
            raise RuntimeError("GCS_BUCKET is required for gcs storage")
        return GCSStorage(bucket=bucket)
    # fallback
    return LocalStorage()
