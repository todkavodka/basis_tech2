"""Multi-provider LLM wrapper via LiteLLM."""

from __future__ import annotations

import os
from typing import Any

import litellm

from code_auditor.config import LLMConfig


def chat_completion(
    model: str,
    messages: list[dict[str, str]],
    config: LLMConfig | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """Send a chat completion request to any supported provider.

    Config priority: explicit args > config file > defaults.

    Supported model strings:
      - openai/gpt-4o
      - openai/o3-mini
      - anthropic/claude-sonnet-4-20250514
      - anthropic/claude-3-5-haiku-20241022
      - ollama/llama3
      - ollama/codellama
      - deepseek/deepseek-chat
      - groq/llama-3.1-70b-versatile
    """
    cfg = config or LLMConfig()
    final_model = model or cfg.model
    final_temp = temperature if temperature is not None else cfg.temperature
    final_tokens = max_tokens if max_tokens is not None else cfg.max_tokens

    # Set API key from config if provided
    if cfg.api_key:
        provider = final_model.split("/")[0] if "/" in final_model else "openai"
        env_key = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "groq": "GROQ_API_KEY",
        }.get(provider, "OPENAI_API_KEY")
        os.environ[env_key] = cfg.api_key

    # Set custom API base if provided (for Ollama, proxies, etc.)
    if cfg.api_base:
        provider = final_model.split("/")[0] if "/" in final_model else "openai"
        env_key = {
            "openai": "OPENAI_API_BASE",
            "ollama": "OLLAMA_API_BASE",
            "deepseek": "DEEPSEEK_API_BASE",
            "groq": "GROQ_API_BASE",
        }.get(provider, "OPENAI_API_BASE")
        os.environ[env_key] = cfg.api_base

    kwargs: dict[str, Any] = {
        "model": final_model,
        "messages": messages,
        "temperature": final_temp,
        "max_tokens": final_tokens,
    }

    response = litellm.completion(**kwargs)
    return response.choices[0].message.content or ""
