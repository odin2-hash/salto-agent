# Erasmus Partner Agent - Dependency Configuration

This document specifies the minimal dependency configuration for the Erasmus+ partnership agent, focusing on web scraping, LLM integration, and dual interface support (CLI + MCP server).

## Python Package Dependencies

### Core Framework
```
# Pydantic AI Core
pydantic-ai>=0.1.0
pydantic>=2.5.0
pydantic-settings>=2.0.0

# Environment Management
python-dotenv>=1.0.0
```

### LLM Provider
```
# OpenAI Integration
openai>=1.10.0
```

### Web Scraping
```
# Web Scraping Stack
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0  # Fast XML/HTML parser
fake-useragent>=1.4.0  # Rotate user agents
```

### Async Support
```
# Async HTTP Client
httpx>=0.26.0
aiofiles>=23.0.0
```

### CLI Interface
```
# Command Line Interface
typer>=0.9.0
rich>=13.0.0  # Pretty CLI output
click>=8.1.0  # CLI utilities
```

### MCP Server
```
# MCP Server Implementation
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic-core>=2.14.0
```

### Data Processing
```
# Data Export and Validation
pandas>=2.1.0  # CSV export
jsonlines>=4.0.0  # JSON streaming
```

### Development & Testing
```
# Testing Framework
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-httpx>=0.25.0
httpx-mock>=0.10.0

# Code Quality
black>=23.0.0
ruff>=0.1.0
mypy>=1.7.0
```

### Logging & Monitoring
```
# Enhanced Logging
loguru>=0.7.0
structlog>=23.2.0
```

## Environment Variables Configuration

### Essential Configuration (.env template)
```bash
# LLM Configuration (REQUIRED)
LLM_PROVIDER=openai
LLM_API_KEY=your-openai-api-key-here
LLM_MODEL=gpt-4
LLM_BASE_URL=https://api.openai.com/v1

# SALTO-YOUTH Otlas Configuration
OTLAS_BASE_URL=https://www.salto-youth.net/tools/otlas-partner-finding
USER_AGENT=ErasmusPartnerAgent/1.0
REQUEST_DELAY=1.0
MAX_RETRIES=3
TIMEOUT_SECONDS=30

# Application Settings
APP_ENV=development
LOG_LEVEL=INFO
DEBUG=false
ENABLE_CACHING=true
CACHE_TTL=3600

# MCP Server Configuration
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000
MCP_SERVER_RELOAD=false
MCP_AUTH_ENABLED=false

# CLI Configuration
CLI_EXPORT_FORMAT=json
CLI_MAX_RESULTS=50
CLI_INTERACTIVE_MODE=true

# Rate Limiting & Performance
CONCURRENT_REQUESTS=3
SCRAPING_DELAY=1.0
CONNECTION_POOL_SIZE=10
```

### Optional Environment Variables
```bash
# Advanced Scraping (optional)
PROXY_URL=http://proxy:port
PROXY_USERNAME=username
PROXY_PASSWORD=password
CUSTOM_HEADERS={"Accept-Language": "en-US"}

# Session Management (optional)
SESSION_TIMEOUT=1800
PERSISTENT_SESSIONS=false

# Export Options (optional)
EXPORT_DIRECTORY=./exports
AUTO_EXPORT=false
```

## Provider Configuration

### LLM Provider Setup
```python
# Minimal OpenAI configuration pattern
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

def get_llm_model():
    """Get configured OpenAI model."""
    provider = OpenAIProvider(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key
    )
    return OpenAIModel(settings.llm_model, provider=provider)
```

### Web Scraping Provider
```python
# HTTP client configuration pattern
import httpx
from fake_useragent import UserAgent

def get_http_client():
    """Get configured async HTTP client."""
    ua = UserAgent()
    return httpx.AsyncClient(
        timeout=httpx.Timeout(settings.timeout_seconds),
        headers={"User-Agent": ua.random},
        limits=httpx.Limits(max_connections=settings.connection_pool_size)
    )
```

## Dependency Classes

### Agent Dependencies
```python
@dataclass
class AgentDependencies:
    """
    Core dependencies for Erasmus Partner Agent.
    All external services and configurations injected through RunContext.
    """
    
    # Web Scraping Configuration
    otlas_base_url: str
    user_agent: str
    request_delay: float = 1.0
    max_retries: int = 3
    timeout: int = 30
    
    # Session Management
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    cache_enabled: bool = True
    
    # Search Configuration
    max_results: int = 50
    concurrent_requests: int = 3
    enable_detailed_parsing: bool = True
    
    # Export Settings
    export_format: str = "json"
    export_directory: str = "./exports"
    
    # HTTP Client (lazy initialization)
    _http_client: Optional[httpx.AsyncClient] = field(default=None, init=False, repr=False)
    _cache: Optional[dict] = field(default_factory=dict, init=False, repr=False)
    
    @property
    def http_client(self) -> httpx.AsyncClient:
        """Lazy initialization of HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={"User-Agent": self.user_agent}
            )
        return self._http_client
    
    async def cleanup(self):
        """Cleanup resources when done."""
        if self._http_client:
            await self._http_client.aclose()
    
    @classmethod
    def from_settings(cls, settings, **kwargs):
        """Create dependencies from settings with overrides."""
        return cls(
            otlas_base_url=kwargs.get('otlas_base_url', settings.otlas_base_url),
            user_agent=kwargs.get('user_agent', settings.user_agent),
            request_delay=kwargs.get('request_delay', settings.request_delay),
            max_retries=kwargs.get('max_retries', settings.max_retries),
            timeout=kwargs.get('timeout', settings.timeout_seconds),
            max_results=kwargs.get('max_results', getattr(settings, 'cli_max_results', 50)),
            concurrent_requests=kwargs.get('concurrent_requests', getattr(settings, 'concurrent_requests', 3)),
            export_format=kwargs.get('export_format', getattr(settings, 'cli_export_format', 'json')),
            cache_enabled=kwargs.get('cache_enabled', getattr(settings, 'enable_caching', True)),
            **{k: v for k, v in kwargs.items() 
               if k not in ['otlas_base_url', 'user_agent', 'request_delay', 'max_retries', 'timeout']}
        )
```

### Search Context Dependencies
```python
@dataclass
class SearchContext:
    """
    Context for individual search operations.
    """
    search_type: Literal["organizations", "projects"]
    query_parameters: Dict[str, Any]
    max_pages: int = 5
    parse_detailed: bool = True
    cache_key: Optional[str] = None
    
    def generate_cache_key(self) -> str:
        """Generate cache key from search parameters."""
        import hashlib
        params_str = json.dumps(self.query_parameters, sort_keys=True)
        return hashlib.md5(f"{self.search_type}:{params_str}".encode()).hexdigest()
```

## MCP Server Configuration

### Server Dependencies
```python
# MCP server specific dependencies
from fastapi import FastAPI, Depends
from pydantic import BaseModel

class MCPServerConfig:
    """Configuration for MCP server deployment."""
    
    def __init__(self):
        self.app = FastAPI(
            title="Erasmus Partner Agent MCP Server",
            version="1.0.0",
            description="MCP server for Erasmus+ partnership search"
        )
        self.host = settings.mcp_server_host
        self.port = settings.mcp_server_port
        self.reload = settings.mcp_server_reload
    
    def configure_routes(self, agent, dependencies_factory):
        """Configure MCP server routes with agent integration."""
        
        @self.app.post("/search/partners")
        async def search_partners(request: PartnerSearchRequest):
            deps = dependencies_factory()
            try:
                result = await agent.run(
                    f"Find partner organizations: {request.query}",
                    deps=deps
                )
                return result.data
            finally:
                await deps.cleanup()
        
        @self.app.post("/search/projects") 
        async def search_projects(request: ProjectSearchRequest):
            deps = dependencies_factory()
            try:
                result = await agent.run(
                    f"Find project opportunities: {request.query}",
                    deps=deps
                )
                return result.data
            finally:
                await deps.cleanup()
```

### MCP Request Models
```python
class PartnerSearchRequest(BaseModel):
    """Request model for partner organization search."""
    query: str
    country: Optional[str] = None
    activity_type: Optional[str] = None
    theme: Optional[str] = None
    target_group: Optional[str] = None
    experience_level: Optional[str] = None
    max_results: int = 20

class ProjectSearchRequest(BaseModel):
    """Request model for project opportunity search."""
    query: str
    project_type: Optional[str] = None
    countries: Optional[List[str]] = None
    themes: Optional[List[str]] = None
    deadline_after: Optional[str] = None
    max_results: int = 20
```

## CLI Dependencies

### CLI Configuration
```python
# CLI interface dependencies using Typer
import typer
from rich.console import Console
from rich.table import Table

class CLIConfig:
    """Configuration for CLI interface."""
    
    def __init__(self):
        self.app = typer.Typer(
            name="erasmus-partner-agent",
            help="Search for Erasmus+ partners and projects",
            rich_markup_mode="rich"
        )
        self.console = Console()
    
    def setup_commands(self, agent, dependencies_factory):
        """Setup CLI commands with agent integration."""
        
        @self.app.command("partners")
        def search_partners(
            query: str = typer.Argument(..., help="Search query for partners"),
            country: Optional[str] = typer.Option(None, "--country", "-c"),
            export: bool = typer.Option(False, "--export", "-e"),
            format: str = typer.Option("json", "--format", "-f")
        ):
            """Search for partner organizations."""
            # Implementation will use agent with dependencies
            pass
        
        @self.app.command("projects")
        def search_projects(
            query: str = typer.Argument(..., help="Search query for projects"),
            project_type: Optional[str] = typer.Option(None, "--type", "-t"),
            export: bool = typer.Option(False, "--export", "-e"),
            format: str = typer.Option("json", "--format", "-f") 
        ):
            """Search for project opportunities."""
            # Implementation will use agent with dependencies
            pass
```

## Security Considerations

### API Key Management
- Store all API keys in .env file (never in code)
- Validate API keys on startup
- Support key rotation without code changes
- Use secure storage in production (AWS Secrets Manager, etc.)

### Web Scraping Security
- Implement respectful rate limiting (1-second delays)
- Rotate User-Agent strings to avoid blocking
- Handle HTTP errors gracefully
- Respect robots.txt (though scraping is for research purposes)
- Use secure HTTP clients with proper SSL verification

### Input Validation
- Validate all search parameters using Pydantic models
- Sanitize user inputs before web requests
- Limit search result counts to prevent abuse
- Validate URLs before making requests

## Performance Configuration

### Async Patterns
```python
# Concurrent search pattern
async def concurrent_search(queries: List[str], dependencies: AgentDependencies):
    """Execute multiple searches concurrently with rate limiting."""
    semaphore = asyncio.Semaphore(dependencies.concurrent_requests)
    
    async def limited_search(query: str):
        async with semaphore:
            await asyncio.sleep(dependencies.request_delay)
            return await perform_search(query, dependencies)
    
    tasks = [limited_search(query) for query in queries]
    return await asyncio.gather(*tasks)
```

### Caching Strategy
```python
# Simple in-memory caching
class SearchCache:
    """Simple cache for search results within session."""
    
    def __init__(self, ttl: int = 3600):
        self.cache = {}
        self.ttl = ttl
        self.timestamps = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None
    
    def set(self, key: str, value: Any):
        self.cache[key] = value
        self.timestamps[key] = time.time()
```

## Quality Checklist

Before implementation, ensure:
- ✅ All required packages identified with versions
- ✅ Environment variables documented and validated
- ✅ LLM provider properly configured
- ✅ Web scraping dependencies secure and respectful
- ✅ MCP server requirements specified
- ✅ CLI interface dependencies included
- ✅ Async patterns supported
- ✅ Caching strategy defined
- ✅ Security measures specified
- ✅ Performance considerations addressed
- ✅ Error handling patterns included
- ✅ Resource cleanup properly managed

## Integration Notes

This dependency configuration supports:
- **Pydantic AI Agent**: Core agent with structured outputs
- **Web Scraping Tools**: BeautifulSoup + httpx for async scraping
- **Dual Interface**: Both CLI (Typer) and MCP server (FastAPI)
- **Environment Management**: python-dotenv for secure configuration
- **Testing**: Comprehensive test framework with mocks
- **Development**: Code quality tools and async support

The agent will be able to:
1. Search SALTO-YOUTH Otlas platform efficiently
2. Parse and validate search results into structured data
3. Serve both CLI and MCP server interfaces
4. Handle errors gracefully with proper logging
5. Export results in multiple formats
6. Maintain respectful scraping practices