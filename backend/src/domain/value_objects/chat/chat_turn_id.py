from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class ChatTurnId:
    value: UUID

    @classmethod
    def generate(cls) -> "ChatTurnId":
        return cls(value=uuid4())
