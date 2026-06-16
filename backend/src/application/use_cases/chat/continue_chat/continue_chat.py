from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from src.application.exceptions import ChatContinuationExpiredError
from src.application.ports.out.chat_generation_client_protocol import (
    ChatGenerationClientProtocol,
)
from src.application.use_cases.chat.continue_chat.continue_chat_dto import (
    ContinueChatInput,
    ContinueChatOutput,
)
from src.domain.entities.chat.chat import ChatMessage
from src.domain.repositories.chat_command_repository_protocol import (
    ChatCommandRepositoryProtocol,
)
from src.domain.value_objects.chat.chat_turn_id import ChatTurnId
from src.domain.value_objects.chat.message_sender import MessageSender
from src.domain.value_objects.chat.prompt import Prompt


class ContinueChatUseCase:
    _CONTINUATION_LIMIT = timedelta(hours=24)

    def __init__(
        self,
        chat_generation_client: ChatGenerationClientProtocol,
        chat_command_repository: ChatCommandRepositoryProtocol,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._chat_generation_client = chat_generation_client
        self._chat_command_repository = chat_command_repository
        self._now = now or (lambda: datetime.now(timezone.utc))

    async def execute(self, command: ContinueChatInput) -> ContinueChatOutput:
        prompt = Prompt(command.prompt)
        # 所有者確認済みのチャットを取得してから外部生成を呼び、
        # 権限外リクエストで副作用を起こさない。
        chat = await self._chat_command_repository.get_chat_for_continuation(
            chat_id=command.chat_id,
            user_id=command.user_id,
        )
        user_sent_at = self._now()
        # 会話継続期限は外部生成前に判定し、
        # 期限切れのチャットで回答だけが生成される状態を避ける。
        if user_sent_at - chat.last_updated_at >= self._CONTINUATION_LIMIT:
            raise ChatContinuationExpiredError

        generated = await self._chat_generation_client.continue_chat(
            chat.session_id, prompt.value
        )
        answered_at = self._now()
        turn_id = ChatTurnId.generate()
        user_message = ChatMessage(
            chat_id=chat.chat_id,
            turn_id=turn_id,
            sender=MessageSender.USER,
            content=prompt,
            sent_at=user_sent_at,
        )
        llm_message = ChatMessage(
            chat_id=chat.chat_id,
            turn_id=turn_id,
            sender=MessageSender.LLM,
            content=generated.answer,
            sent_at=answered_at,
        )
        # Domain側で発信順序と更新バージョンを確定してから、
        # Repository側の楽観排他保存へ渡す。
        chat.record_exchange(user_message=user_message, llm_message=llm_message)
        await self._chat_command_repository.save_exchange(
            chat, user_message, llm_message
        )
        return ContinueChatOutput(
            chat_id=chat.chat_id,
            answer=generated.answer,
            title=chat.title,
            last_updated_at=chat.last_updated_at,
        )
