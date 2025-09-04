"""
Provider configurations for the Erasmus Partner Agent.

This module provides configured LLM and HTTP providers for agent operations.
"""
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
import httpx
from .settings import load_settings


def get_llm_model():
    """Get configured LLM model with proper environment loading."""
    settings = load_settings()
    provider = OpenAIProvider(
        base_url=settings.llm_base_url, 
        api_key=settings.llm_api_key
    )
    return OpenAIModel(settings.llm_model, provider=provider)


def get_http_client() -> httpx.AsyncClient:
    """Get configured async HTTP client for web scraping."""
    settings = load_settings()
    return httpx.AsyncClient(
        timeout=httpx.Timeout(settings.timeout_seconds),
        headers={
            "User-Agent": settings.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        },
        limits=httpx.Limits(
            max_connections=settings.connection_pool_size,
            max_keepalive_connections=5
        )
    )