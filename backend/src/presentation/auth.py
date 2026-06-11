from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Protocol
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from starlette.concurrency import run_in_threadpool

from src.dependencies.settings import Settings, get_settings


class AuthenticationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    user_id: UUID


class SigningKey(Protocol):
    key: Any


class SigningKeyClient(Protocol):
    def get_signing_key_from_jwt(self, token: str) -> SigningKey: ...


class CognitoJwtVerifier:
    def __init__(
        self,
        *,
        user_pool_id: str,
        user_pool_client_id: str,
        aws_region: str,
        signing_key_client: SigningKeyClient | None = None,
    ) -> None:
        if not user_pool_id or not user_pool_client_id or not aws_region:
            raise ValueError("Cognito JWT verification settings are required")

        self._user_pool_client_id = user_pool_client_id
        self._issuer = f"https://cognito-idp.{aws_region}.amazonaws.com/{user_pool_id}"
        self._signing_key_client = signing_key_client or PyJWKClient(
            f"{self._issuer}/.well-known/jwks.json",
            cache_keys=True,
            timeout=5,
        )

    def verify(self, token: str) -> AuthenticatedUser:
        try:
            signing_key = self._signing_key_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=self._issuer,
                options={
                    "verify_aud": False,
                    "require": ["client_id", "exp", "iss", "sub", "token_use"],
                },
            )
            if claims["client_id"] != self._user_pool_client_id:
                raise AuthenticationError
            if claims["token_use"] != "access":
                raise AuthenticationError
            return AuthenticatedUser(user_id=UUID(claims["sub"]))
        except (jwt.PyJWTError, KeyError, TypeError, ValueError) as error:
            raise AuthenticationError from error


_bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def _create_cognito_jwt_verifier(
    user_pool_id: str,
    user_pool_client_id: str,
    aws_region: str,
) -> CognitoJwtVerifier:
    return CognitoJwtVerifier(
        user_pool_id=user_pool_id,
        user_pool_client_id=user_pool_client_id,
        aws_region=aws_region,
    )


def get_cognito_jwt_verifier(
    settings: Settings = Depends(get_settings),
) -> CognitoJwtVerifier:
    if not settings.cognito_user_pool_id or not settings.cognito_user_pool_client_id:
        raise AuthenticationError
    return _create_cognito_jwt_verifier(
        settings.cognito_user_pool_id,
        settings.cognito_user_pool_client_id,
        settings.aws_region,
    )


async def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError
    verifier = get_cognito_jwt_verifier(get_settings())
    return await run_in_threadpool(verifier.verify, credentials.credentials)
