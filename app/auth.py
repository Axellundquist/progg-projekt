from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBasic, HTTPBasicCredentials

from .config import Settings, get_settings

api_key_scheme = APIKeyHeader(name="x-api-key", auto_error=False)
basic_scheme = HTTPBasic(auto_error=False)


def verify_request(
    api_key_header: str | None = Security(api_key_scheme),
    basic_credentials: HTTPBasicCredentials | None = Depends(basic_scheme),
    settings: Settings = Depends(get_settings),
) -> None:
    api_key = settings.api_key
    user = settings.basic_auth_user
    password = settings.basic_auth_password

    api_key_valid = api_key_header is not None and api_key_header == api_key
    basic_valid = (
        user is not None
        and password is not None
        and basic_credentials is not None
        and basic_credentials.username == user
        and basic_credentials.password == password
    )

    if not (api_key_valid or basic_valid):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
