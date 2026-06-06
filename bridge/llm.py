"""LLM client shared across bridge modules.

Usage:
    export UMOS_LLM_API_KEY="sk-..."
    export UMOS_LLM_BASE_URL="https://api.openai.com/v1"  # or Ollama, etc.
    export UMOS_LLM_MODEL="gpt-4o"  # default
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMConfig:
    api_key: str = field(default_factory=lambda: os.environ.get("UMOS_LLM_API_KEY", ""))
    base_url: str = field(default_factory=lambda: os.environ.get("UMOS_LLM_BASE_URL", "https://api.openai.com/v1"))
    model: str = field(default_factory=lambda: os.environ.get("UMOS_LLM_MODEL", "gpt-4o-mini"))


_client: Any = None


def get_client(cfg: LLMConfig | None = None) -> Any | None:
    global _client
    if _client is not None:
        return _client

    cfg = cfg or LLMConfig()
    if not cfg.api_key:
        return None

    try:
        from openai import OpenAI
        _client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
        return _client
    except ImportError:
        return None


def chat(prompt: str, system: str = "", cfg: LLMConfig | None = None) -> str | None:
    client = get_client(cfg)
    if client is None:
        return None

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        resp = client.chat.completions.create(
            model=(cfg or LLMConfig()).model,
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"<LLM error: {e}>"
