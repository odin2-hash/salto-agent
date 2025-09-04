"""
Erasmus Partner Agent - AI-powered Erasmus+ partnership discovery.

This package provides a Pydantic AI agent for searching partner organizations
and project opportunities on the SALTO-YOUTH Otlas platform. The agent supports
both CLI and MCP server interfaces for integration with various systems.

Main Components:
- agent: Core Pydantic AI agent implementation
- cli: Command-line interface using Typer
- mcp_server: MCP server for external integrations
- tools: Web scraping and data extraction tools
- models: Pydantic models for structured output
- dependencies: Dependency injection classes
- providers: LLM and HTTP client providers
- settings: Configuration management
"""

from .agent import agent, run_search
from .models import SearchResponse, PartnerOrganization, ProjectOpportunity
from .dependencies import AgentDependencies
from .settings import load_settings

__version__ = "1.0.0"
__all__ = [
    "agent",
    "run_search", 
    "SearchResponse",
    "PartnerOrganization",
    "ProjectOpportunity",
    "AgentDependencies",
    "load_settings"
]