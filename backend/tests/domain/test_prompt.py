import pytest

from src.domain.exceptions.chat_exception import InvalidPromptError, PromptTooLongError
from src.domain.value_objects.chat.prompt import Prompt


@pytest.mark.parametrize("raw", ["", " ", "　", "\n\t　"])
def test_prompt_rejects_blank_values(raw: str) -> None:
    with pytest.raises(InvalidPromptError):
        Prompt(raw)


def test_prompt_trims_general_whitespace() -> None:
    assert Prompt("\n\t　 hello 　\t").value == "hello"


def test_prompt_accepts_one_character() -> None:
    assert Prompt("a").value == "a"


def test_prompt_accepts_999_characters() -> None:
    assert len(Prompt("a" * 999).value) == 999


def test_prompt_accepts_1000_characters() -> None:
    assert len(Prompt("a" * 1000).value) == 1000


def test_prompt_rejects_1001_characters() -> None:
    with pytest.raises(PromptTooLongError):
        Prompt("a" * 1001)
