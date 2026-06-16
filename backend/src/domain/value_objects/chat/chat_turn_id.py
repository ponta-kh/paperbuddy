from dataclasses import dataclass
from uuid import UUID, uuid7


@dataclass(frozen=True, slots=True)
class ChatTurnId:
    value: UUID

    @classmethod
    def generate(cls) -> "ChatTurnId":
        return cls(value=uuid7())
