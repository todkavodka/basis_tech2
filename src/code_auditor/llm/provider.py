"""Multi-provider LLM wrapper via LiteLLM."""

from __future__ import annotations

import litellm


def chat_completion(
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.1,
    max_tokens: int = 4096,
) -> str:
    """Send a chat completion request to any supported provider.

    Supported model strings:
      - openai/gpt-4o
      - anthropic/claude-sonnet-4-20250514
      - ollama/llama3
    """
    response = litellm.completion(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""
