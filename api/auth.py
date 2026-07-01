import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str | None = Security(api_key_header)) -> None:
    expected_key = os.getenv("API_KEY")
    if not expected_key or api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )
