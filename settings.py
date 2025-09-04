"""
Configuration settings for the Erasmus Partner Agent.

This module handles environment variables and application settings using
pydantic-settings and python-dotenv for secure configuration management.
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from dotenv import load_dotenv


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # LLM Configuration
    llm_provider: str = Field(default="openai", description="LLM provider")
    llm_api_key: str = Field(..., description="API key for the LLM provider")
    llm_model: str = Field(default="gpt-4", description="Model name to use")
    llm_base_url: str = Field(
        default="https://api.openai.com/v1", 
        description="Base URL for the LLM API"
    )
    
    # SALTO-YOUTH Otlas Configuration
    otlas_base_url: str = Field(
        default="https://www.salto-youth.net/tools/otlas-partner-finding",
        description="Base URL for SALTO-YOUTH Otlas platform"
    )
    user_agent: str = Field(
        default="ErasmusPartnerAgent/1.0",
        description="User agent string for web requests"
    )
    request_delay: float = Field(
        default=1.0,
        description="Delay between requests in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of request retries"
    )
    timeout_seconds: int = Field(
        default=30,
        description="HTTP request timeout in seconds"
    )
    
    # Application Settings
    app_env: str = Field(default="development", description="Application environment")
    log_level: str = Field(default="INFO", description="Log level")
    debug: bool = Field(default=False, description="Debug mode")
    enable_caching: bool = Field(default=True, description="Enable result caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    
    # MCP Server Configuration
    mcp_server_host: str = Field(
        default="localhost",
        description="MCP server host"
    )
    mcp_server_port: int = Field(
        default=8000,
        description="MCP server port"
    )
    mcp_server_reload: bool = Field(
        default=False,
        description="Enable auto-reload for development"
    )
    mcp_auth_enabled: bool = Field(
        default=False,
        description="Enable authentication for MCP server"
    )
    
    # CLI Configuration
    cli_export_format: str = Field(
        default="json",
        description="Default export format for CLI"
    )
    cli_max_results: int = Field(
        default=50,
        description="Maximum results for CLI searches"
    )
    cli_interactive_mode: bool = Field(
        default=True,
        description="Enable interactive mode for CLI"
    )
    
    # Rate Limiting & Performance
    concurrent_requests: int = Field(
        default=3,
        description="Maximum concurrent requests"
    )
    scraping_delay: float = Field(
        default=1.0,
        description="Delay between scraping requests"
    )
    connection_pool_size: int = Field(
        default=10,
        description="HTTP connection pool size"
    )


def load_settings() -> Settings:
    """Load settings with proper error handling and environment loading."""
    # Load environment variables from .env file
    load_dotenv()
    
    try:
        return Settings()
    except Exception as e:
        error_msg = f"Failed to load settings: {e}"
        if "llm_api_key" in str(e).lower():
            error_msg += "\nMake sure to set LLM_API_KEY in your .env file"
        raise ValueError(error_msg) from e