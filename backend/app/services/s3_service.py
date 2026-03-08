from pathlib import Path
import json
from typing import Union
from app.config.s3_client import s3


class S3Service:

    def __init__(self, bucket_name: str = "my-bucket"):
        self.bucket_name = bucket_name

    def upload_file(self, local_path: Union[str, Path], s3_key: str) -> str:
        """Upload a file to S3. Returns the S3 key."""
        s3.upload_file(str(local_path), self.bucket_name, s3_key)
        return s3_key

    def upload_json(self, data: dict, s3_key: str) -> str:
        """Upload JSON directly to S3 (without saving locally)."""
        s3.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=json.dumps(data, indent=4, default=str),
            ContentType="application/json"
        )
        return s3_key

    def upload_text(self, text: str, s3_key: str) -> str:
        """Upload plain text string directly to S3."""
        s3.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=text.encode("utf-8"),
            ContentType="text/plain"
        )
        return s3_key

    def list_files(self, prefix: str) -> list:
        """List all objects under a given S3 prefix."""
        response = s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
        return response.get("Contents", [])

    def download_file(self, s3_key: str, local_path: Path) -> None:
        """
        Download a file from S3 using the default bucket (self.bucket_name).
        Used by old flows that don't pass bucket dynamically.
        """
        s3.download_file(self.bucket_name, s3_key, str(local_path))

    def download_file_from_bucket(self, bucket: str, key: str, local_path: Path) -> None:
        """
        Download a file from a SPECIFIC bucket + key.
        Used by prepare_job_full() which parses bucket name from the S3 URL.

        Example:
            s3://my-bucket/d5934e4a/jd/jd.pdf
            → bucket = "my-bucket"
            → key    = "d5934e4a/jd/jd.pdf"
        """
        s3.download_file(bucket, key, str(local_path))

    def download_json(self, s3_key: str) -> dict:
        """Downloads and parses a JSON file directly from S3 without temp file."""
        response = s3.get_object(Bucket=self.bucket_name, Key=s3_key)
        content = response["Body"].read().decode("utf-8")
        return json.loads(content)