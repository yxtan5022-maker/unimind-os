"""Intent Execution Protocol (IEP) — standardised Agent-to-Kernel contract.

Any LLM Agent (AstrBot, OpenAI, etc.) can send a JSON intent;
the Intent Dispatcher resolves it against available resources and
routes it to the correct backend.
"""

from bridge.iep.dispatcher import IntentDispatcher, IntentResult
from bridge.iep.schema import (
    IntentMessage, IntentResponse, IntentAction, ResourceCapability,
)

__all__ = [
    "IntentDispatcher", "IntentResult",
    "IntentMessage", "IntentResponse", "IntentAction", "ResourceCapability",
]