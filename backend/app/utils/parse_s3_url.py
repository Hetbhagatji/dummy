def parse_s3_url(s3_url: str) -> tuple[str, str]:
    s3_url = s3_url.removeprefix("s3://")
    bucket, _, key = s3_url.partition("/")
    return bucket, key