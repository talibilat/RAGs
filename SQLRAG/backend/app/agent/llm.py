"""Chat model factory with provider fallback (Azure OpenAI -> OpenAI)."""

from __future__ import annotations

from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings
from app.core.exceptions import LLMError
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def _has_azure_config() -> bool:
    return bool(
        settings.azure_openai_endpoint
        and settings.azure_openai_api_key
        and settings.azure_openai_deployment
    )


def _has_openai_config() -> bool:
    return bool(settings.openai_api_key)


def get_chat_model(*, temperature: float = 0) -> BaseChatModel:
    """
    Return a chat model based on available credentials.

    Priority:
    1) Azure OpenAI (AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY)
    2) OpenAI (OPENAI_API_KEY)
    """
    if _has_azure_config():
        return AzureChatOpenAI(
            azure_deployment=settings.azure_openai_deployment,
            openai_api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            temperature=temperature,
            request_timeout=settings.query_timeout,
        )

    if _has_openai_config():
        return ChatOpenAI(
            model=settings.openai_model or "gpt-4o-mini",
            api_key=settings.openai_api_key,
            temperature=temperature,
            request_timeout=settings.query_timeout,
        )

    raise LLMError(
        "Missing LLM credentials",
        {
            "required": [
                "AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY (recommended)",
                "or OPENAI_API_KEY",
            ]
        },
    )

