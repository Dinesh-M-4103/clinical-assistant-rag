"""Understanding the question before retrieval.

Two cheap steps run first: a deterministic router that answers small talk
without any model call, and a rewriter that makes follow-up questions
self-contained so retrieval does not need the chat history.
"""

import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass

from app.rag import prompts
from app.rag.errors import LLMUnavailableError
from app.rag.llm import LLMClient
from app.rag.types import Intent, Turn

logger = logging.getLogger(__name__)

_MAX_REWRITE_CHARS = 500
_NON_WORD = re.compile(r"[^a-z0-9]+")


_GREETING = re.compile(
    r"(?:hi+|hello+|hey+|hiya|howdy|yo|namaste|greetings|good (?:morning|afternoon|evening|day))"
    r"(?: (?:there|doc|doctor|team|assistant|everyone|all))?(?: how are you(?: doing| today)?)?"
    r"|how are you(?: doing| today)?"
)
_THANKS = re.compile(
    r"(?:(?:ok|okay|great|perfect|cool|awesome|nice) )?"
    r"(?:thanks?|thank you|thx|ty|many thanks|much appreciated|cheers)"
    r"(?: (?:a lot|so much|very much|again|doc|doctor|that helps|for your help|for the help))*"
)
_FAREWELL = re.compile(
    r"bye+(?: bye)?|goodbye|good bye|see you(?: later| soon| tomorrow)?|take care|good night"
    r"|cya|thats all(?: for now)?|nothing else"
)
_IDENTITY = re.compile(
    r"(?:who|what) (?:are|r) you|what is your name|whats your name|what can you do"
    r"|what do you do|how can you help(?: me)?|introduce yourself|are you (?:a )?(?:bot|ai|human)"
)
_OFF_TOPIC = re.compile(
    r"(?:tell|give|write|sing|show) (?:me )?(?:a |an |some )?(?:joke|poem|song|story|recipe)s?.*"
    r"|(?:what is|whats|how is) the (?:weather|temperature outside).*"
    r"|(?:write|generate) (?:me )?(?:a |an )?(?:python|javascript|java|sql|code|program|script).*"
    r"|who won .*(?:cricket|football|world cup|match).*"
)

_SOCIAL_ROUTES: tuple[tuple[re.Pattern[str], str], ...] = (
    (_GREETING, prompts.GREETING_REPLY),
    (_THANKS, prompts.THANKS_REPLY),
    (_FAREWELL, prompts.FAREWELL_REPLY),
    (_IDENTITY, prompts.IDENTITY_REPLY),
)


@dataclass(frozen=True)
class RoutedReply:
    """A canned answer that needs neither retrieval nor the language model."""

    intent: Intent
    reply: str


def route(question: str) -> RoutedReply | None:
    """Return a canned reply for small talk and obvious off-topic asks, else ``None``.

    The whole normalised message must match, so "hi, what was the HbA1c?" is a
    real question and goes on to retrieval.
    """
    normalised = _NON_WORD.sub(" ", question.lower().replace("'", "")).strip()
    for pattern, reply in _SOCIAL_ROUTES:
        if pattern.fullmatch(normalised):
            return RoutedReply("greeting", reply)
    if _OFF_TOPIC.fullmatch(normalised):
        return RoutedReply("off_topic", prompts.OFF_TOPIC_REPLY)
    return None


class QueryRewriter:
    """Rewrites a follow-up into a standalone query using the conversation."""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def rewrite(self, question: str, history: Sequence[Turn]) -> str:
        """Standalone query; the original question when there is no history or on any failure.

        Rewriting only sharpens retrieval, so a model outage here must not fail the
        whole answer.
        """
        if not history:
            return question
        try:
            result = self._llm.generate(prompts.build_rewrite_prompt(question, history))
        except LLMUnavailableError:
            logger.warning("Query rewrite failed; using the original question", exc_info=True)
            return question
        lines = result.text.strip().splitlines()
        rewritten = lines[0].strip().strip("\"'") if lines else ""
        return rewritten if 0 < len(rewritten) <= _MAX_REWRITE_CHARS else question
