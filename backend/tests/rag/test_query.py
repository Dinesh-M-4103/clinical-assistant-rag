import pytest

from app.rag import prompts
from app.rag.errors import LLMUnavailableError
from app.rag.query import QueryRewriter, route
from app.rag.types import Turn

from .fakes import ScriptedLLM

HISTORY = [Turn("user", "What is the latest HbA1c?"), Turn("assistant", "7.8% [C1]")]


@pytest.mark.parametrize(
    "message",
    [
        "hi",
        "Hello!",
        "HELLO!!!",
        "heyyy",
        "Hi there",
        "good morning",
        "Good Morning, doctor.",
        "hi, how are you?",
    ],
)
def test_greetings_are_answered_without_the_pipeline(message: str) -> None:
    routed = route(message)

    assert routed is not None
    assert (routed.intent, routed.reply) == ("greeting", prompts.GREETING_REPLY)


@pytest.mark.parametrize("message", ["thanks", "Thank you!", "thanks a lot", "ok thanks :)", "Thx"])
def test_thanks_gets_a_polite_reply(message: str) -> None:
    routed = route(message)

    assert routed is not None
    assert routed.reply == prompts.THANKS_REPLY


@pytest.mark.parametrize(
    "message", ["bye", "Goodbye!", "see you later", "that's all", "Take care."]
)
def test_farewells_get_a_goodbye(message: str) -> None:
    routed = route(message)

    assert routed is not None
    assert routed.reply == prompts.FAREWELL_REPLY


@pytest.mark.parametrize(
    "message", ["who are you", "Who are you?", "what can you do", "What's your name?", "WHO R YOU"]
)
def test_identity_questions_are_answered_locally(message: str) -> None:
    routed = route(message)

    assert routed is not None
    assert routed.reply == prompts.IDENTITY_REPLY


@pytest.mark.parametrize(
    "message",
    [
        "tell me a joke",
        "What's the weather today?",
        "write me a python script",
        "Who won the cricket world cup?",
    ],
)
def test_obviously_non_clinical_requests_are_marked_off_topic(message: str) -> None:
    routed = route(message)

    assert routed is not None
    assert (routed.intent, routed.reply) == ("off_topic", prompts.OFF_TOPIC_REPLY)


@pytest.mark.parametrize(
    "message",
    [
        "hi, what was the HbA1c?",
        "thanks, and what about creatinine?",
        "What is the latest HbA1c?",
        "Who prescribed the metformin?",
        "Any joint pain or weather-related symptoms?",
        "Who won the case against the hospital?",
        "",
    ],
)
def test_real_questions_are_never_hijacked_by_the_router(message: str) -> None:
    assert route(message) is None


def test_rewriter_skips_the_llm_when_there_is_no_history() -> None:
    llm = ScriptedLLM("should not be used")

    assert QueryRewriter(llm).rewrite("What is the HbA1c?", []) == "What is the HbA1c?"
    assert llm.prompts == []


def test_rewriter_returns_the_standalone_query_from_the_llm() -> None:
    llm = ScriptedLLM('  "HbA1c value one year ago"\nextra commentary')

    rewritten = QueryRewriter(llm).rewrite("and last year?", HISTORY)

    assert rewritten == "HbA1c value one year ago"
    assert "User: What is the latest HbA1c?" in llm.prompts[0].user


def test_rewriter_falls_back_to_the_raw_question_when_the_llm_fails() -> None:
    llm = ScriptedLLM(fail_with=LLMUnavailableError("down"))

    assert QueryRewriter(llm).rewrite("and last year?", HISTORY) == "and last year?"


@pytest.mark.parametrize("junk", ["", "   ", "x" * 600])
def test_rewriter_ignores_empty_or_runaway_output(junk: str) -> None:
    assert QueryRewriter(ScriptedLLM(junk)).rewrite("and last year?", HISTORY) == "and last year?"
