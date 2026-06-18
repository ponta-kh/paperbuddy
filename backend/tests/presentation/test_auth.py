from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import cast
from uuid import UUID

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.presentation.auth import (
    AuthenticatedUser,
    AuthenticationError,
    CognitoJwtVerifier,
    SigningKey,
    get_authenticated_user,
)
from src.presentation.exception_handlers import register_exception_handlers

USER_ID = UUID("00000000-0000-0000-0000-000000000001")
ISSUER = "https://cognito-idp.ap-northeast-1.amazonaws.com/ap-northeast-1_test"
CLIENT_ID = "client-id"
PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class StubSigningKeyClient:
    def get_signing_key_from_jwt(self, token: str) -> SigningKey:
        return cast(SigningKey, SimpleNamespace(key=PRIVATE_KEY.public_key()))


def create_token(**overrides: object) -> str:
    claims = {
        "client_id": CLIENT_ID,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        "iss": ISSUER,
        "sub": str(USER_ID),
        "token_use": "access",
        **overrides,
    }
    return jwt.encode(claims, PRIVATE_KEY, algorithm="RS256")


def create_verifier() -> CognitoJwtVerifier:
    return CognitoJwtVerifier(
        user_pool_id="ap-northeast-1_test",
        user_pool_client_id=CLIENT_ID,
        aws_region="ap-northeast-1",
        signing_key_client=StubSigningKeyClient(),
    )


def test_verifies_cognito_access_token() -> None:
    assert create_verifier().verify(create_token()) == AuthenticatedUser(
        user_id=USER_ID
    )


@pytest.mark.parametrize(
    "claims",
    [
        {"client_id": "other-client"},
        {"iss": "https://example.com"},
        {"sub": "not-a-uuid"},
        {"token_use": "id"},
        {"exp": datetime.now(timezone.utc) - timedelta(seconds=1)},
    ],
)
def test_rejects_invalid_cognito_access_token(claims: dict[str, object]) -> None:
    with pytest.raises(AuthenticationError):
        create_verifier().verify(create_token(**claims))


def test_endpoint_rejects_missing_bearer_token() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/protected")
    async def protected(_: AuthenticatedUser = Depends(get_authenticated_user)) -> None:
        return None

    response = TestClient(app).get("/protected")

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_failed"
