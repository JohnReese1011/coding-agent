"""Provider factories for chat and embedding models.

Supported chat providers:
- ollama: local Ollama models
- openai: OpenAI API
- openai_compatible: DeepSeek, Qwen/DashScope compatible mode, SiliconFlow,
  OpenRouter, vLLM, LM Studio and other OpenAI-compatible endpoints
- anthropic: Anthropic Claude API

Supported embedding providers:
- ollama
- openai
- openai_compatible
"""
from __future__ import annotations

from coding_agent.settings import (
    EMBEDDING_API_KEY,
    EMBEDDING_BASE_URL,
    EMBEDDING_MODEL,
    EMBEDDING_PROVIDER,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_PROVIDER,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    OLLAMA_NUM_CTX,
)


def chat_model():
    """Create the configured chat model. Call once per agent process."""
    common = {"temperature": LLM_TEMPERATURE}

    if LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=LLM_MODEL,
            base_url=LLM_BASE_URL,
            streaming=True,
            num_ctx=OLLAMA_NUM_CTX,
            **common,
        )

    if LLM_PROVIDER in {"openai", "openai_compatible"}:
        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": LLM_MODEL,
            "api_key": LLM_API_KEY,
            "temperature": LLM_TEMPERATURE,
            "streaming": True,
            "max_tokens": LLM_MAX_TOKENS,
        }
        if LLM_PROVIDER == "openai_compatible":
            if not LLM_BASE_URL or LLM_BASE_URL == "http://localhost:11434":
                raise ValueError("LLM_PROVIDER=openai_compatible 时必须配置 LLM_BASE_URL")
            kwargs["base_url"] = LLM_BASE_URL
        return ChatOpenAI(**kwargs)

    if LLM_PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=LLM_MODEL,
            api_key=LLM_API_KEY,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            streaming=True,
        )


    raise ValueError(
        f"不支持的 LLM_PROVIDER={LLM_PROVIDER!r}。"
        "可选：ollama、openai、openai_compatible、anthropic。"
    )


def embeddings():
    """Create the configured embedding model independently of the chat model."""
    if EMBEDDING_PROVIDER == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=EMBEDDING_BASE_URL)

    if EMBEDDING_PROVIDER in {"openai", "openai_compatible"}:
        from langchain_openai import OpenAIEmbeddings

        kwargs = {"model": EMBEDDING_MODEL, "api_key": EMBEDDING_API_KEY}
        if EMBEDDING_PROVIDER == "openai_compatible":
            if not EMBEDDING_BASE_URL or EMBEDDING_BASE_URL == "http://localhost:11434":
                raise ValueError(
                    "EMBEDDING_PROVIDER=openai_compatible 时必须配置 EMBEDDING_BASE_URL"
                )
            kwargs["base_url"] = EMBEDDING_BASE_URL
        return OpenAIEmbeddings(**kwargs)

    raise ValueError(
        f"不支持的 EMBEDDING_PROVIDER={EMBEDDING_PROVIDER!r}。"
        "可选：ollama、openai、openai_compatible。"
    )
