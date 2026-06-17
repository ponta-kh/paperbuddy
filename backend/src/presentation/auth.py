from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Protocol
from uuid import UUID

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from starlette.concurrency import run_in_threadpool

from src.dependencies.logging_config import set_log_context
from src.dependencies.settings import Settings, get_settings


class AuthenticationError(Exception):
    """HTTP認証に失敗した場合の例外。"""

    pass


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """認証済みユーザーを表すPresentation層の値。"""

    user_id: UUID


class SigningKey(Protocol):
    """JWT検証に使用する署名鍵のProtocol。"""

    key: Any


class SigningKeyClient(Protocol):
    """JWTから署名鍵を取得するClient契約。"""

    def get_signing_key_from_jwt(self, token: str) -> SigningKey:
        """JWT検証に使用する署名鍵を取得する。"""
        ...


class CognitoJwtVerifier:
    """Amazon CognitoのAccess Tokenを検証するVerifier。"""

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
        """Cognito Access Tokenを検証して認証済みユーザーを返す。

        Raises:
            AuthenticationError: トークンの署名、Issuer、Client ID、用途、ユーザーIDが不正な場合。
        """

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
    """Cognito JWT Verifierを返すFastAPI依存性注入関数。"""

    if not settings.cognito_user_pool_id or not settings.cognito_user_pool_client_id:
        raise AuthenticationError
    return _create_cognito_jwt_verifier(
        settings.cognito_user_pool_id,
        settings.cognito_user_pool_client_id,
        settings.aws_region,
    )


async def get_authenticated_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> AuthenticatedUser:
    """Bearer Tokenを検証して認証済みユーザーを返すFastAPI依存性注入関数。"""

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError
    verifier = get_cognito_jwt_verifier(get_settings())
    user = await run_in_threadpool(verifier.verify, credentials.credentials)
    request.state.user_id = user.user_id
    set_log_context(user_id=user.user_id)
    return user
