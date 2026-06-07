from dataclasses import dataclass
from uuid import UUID

from fastapi import Header


class AuthenticationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    user_id: UUID


async def get_authenticated_user(
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
) -> AuthenticatedUser:
    if x_user_id is None:
        raise AuthenticationError
    try:
        return AuthenticatedUser(user_id=UUID(x_user_id))
    except ValueError as error:
        raise AuthenticationError from error
