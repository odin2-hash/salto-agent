"""
Dependency classes for the Erasmus Partner Agent.

This module defines the dependency injection classes used by the agent
for external service integration and context management.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import httpx
import json
import hashlib
import asyncio
from .settings import load_settings


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
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "text/html,application/xhtml+xml"
                },
                limits=httpx.Limits(max_connections=10)
            )
        return self._http_client
    
    async def cleanup(self):
        """Cleanup resources when done."""
        if self._http_client:
            await self._http_client.aclose()
    
    @classmethod
    def from_settings(cls, **kwargs):
        """Create dependencies from settings with overrides."""
        settings = load_settings()
        return cls(
            otlas_base_url=kwargs.get('otlas_base_url', settings.otlas_base_url),
            user_agent=kwargs.get('user_agent', settings.user_agent),
            request_delay=kwargs.get('request_delay', settings.request_delay),
            max_retries=kwargs.get('max_retries', settings.max_retries),
            timeout=kwargs.get('timeout', settings.timeout_seconds),
            max_results=kwargs.get('max_results', settings.cli_max_results),
            concurrent_requests=kwargs.get('concurrent_requests', settings.concurrent_requests),
            export_format=kwargs.get('export_format', settings.cli_export_format),
            cache_enabled=kwargs.get('cache_enabled', settings.enable_caching),
            **{k: v for k, v in kwargs.items() 
               if k not in ['otlas_base_url', 'user_agent', 'request_delay', 'max_retries', 'timeout']}
        )


@dataclass  
class SearchContext:
    """
    Context for individual search operations.
    """
    search_type: str  # "organizations" or "projects"
    query_parameters: Dict[str, Any]
    max_pages: int = 5
    parse_detailed: bool = True
    cache_key: Optional[str] = None
    
    def generate_cache_key(self) -> str:
        """Generate cache key from search parameters."""
        params_str = json.dumps(self.query_parameters, sort_keys=True)
        return hashlib.md5(f"{self.search_type}:{params_str}".encode()).hexdigest()
    
    def __post_init__(self):
        """Generate cache key after initialization."""
        if self.cache_key is None:
            self.cache_key = self.generate_cache_key()


async def concurrent_search(queries: list[str], dependencies: AgentDependencies):
    """Execute multiple searches concurrently with rate limiting."""
    semaphore = asyncio.Semaphore(dependencies.concurrent_requests)
    
    async def limited_search(query: str):
        async with semaphore:
            await asyncio.sleep(dependencies.request_delay)
            # This would call the actual search function
            return f"Search result for: {query}"
    
    tasks = [limited_search(query) for query in queries]
    return await asyncio.gather(*tasks)


class SearchCache:
    """Simple cache for search results within session."""
    
    def __init__(self, ttl: int = 3600):
        self.cache = {}
        self.ttl = ttl
        self.timestamps = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if still valid."""
        if key in self.cache:
            import time
            if time.time() - self.timestamps[key] < self.ttl:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None
    
    def set(self, key: str, value: Any):
        """Cache a value with timestamp."""
        import time
        self.cache[key] = value
        self.timestamps[key] = time.time()