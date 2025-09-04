# Erasmus Partner Agent - Tool Specifications

Tools for searching and extracting partner organizations and project opportunities from SALTO-YOUTH Otlas platform.

## Tool Overview

The agent requires 3 minimal, focused tools for web scraping and data processing:

1. **search_otlas_organizations** - Search for partner organizations
2. **search_otlas_projects** - Search for project opportunities  
3. **extract_structured_data** - Parse HTML results into structured models

---

## Tool 1: search_otlas_organizations

**Purpose**: Search for partner organizations on SALTO-YOUTH Otlas platform

**Implementation Pattern**: `@agent.tool` (requires HTTP client and rate limiting)

**Parameters**:
- `query_text: str` - General search query
- `country: Optional[str]` - Target country filter
- `max_results: int = 20` - Maximum results to return (1-100)

**Return Type**: `Dict[str, Any]`
```python
{
    "success": bool,
    "raw_html": str,
    "search_url": str,
    "total_found": int,
    "error": Optional[str]
}
```

**Core Logic**:
```python
@agent.tool
async def search_otlas_organizations(
    ctx: RunContext[AgentDependencies],
    query_text: str,
    country: Optional[str] = None,
    max_results: int = 20
) -> Dict[str, Any]:
    """
    Search for partner organizations on SALTO-YOUTH Otlas.
    
    Args:
        query_text: General search terms
        country: ISO country code filter
        max_results: Maximum results (1-100)
    
    Returns:
        Dictionary with search results and metadata
    """
    import httpx
    import asyncio
    
    try:
        # Rate limiting - respect 1 second delay
        await asyncio.sleep(ctx.deps.request_delay)
        
        # Build search URL
        base_url = ctx.deps.otlas_base_url
        params = {
            "search": query_text,
            "searchType": "organizations",
            "limit": min(max_results, 100)
        }
        if country:
            params["country"] = country
        
        # Make request with proper headers
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{base_url}/search",
                params=params,
                headers={
                    "User-Agent": ctx.deps.user_agent,
                    "Accept": "text/html,application/xhtml+xml"
                }
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "raw_html": response.text,
                "search_url": str(response.url),
                "total_found": response.text.count('class="org-item"'),
                "error": None
            }
            
    except Exception as e:
        return {
            "success": False,
            "raw_html": "",
            "search_url": "",
            "total_found": 0,
            "error": str(e)
        }
```

**Error Handling**:
- HTTP timeouts and connection errors
- Rate limiting delays
- Invalid country codes
- HTML parsing failures

---

## Tool 2: search_otlas_projects

**Purpose**: Search for project opportunities on SALTO-YOUTH Otlas platform

**Implementation Pattern**: `@agent.tool` (requires HTTP client and rate limiting)

**Parameters**:
- `query_text: str` - General search query
- `project_type: Optional[str]` - KA152, KA153, etc.
- `max_results: int = 20` - Maximum results to return (1-100)

**Return Type**: `Dict[str, Any]`
```python
{
    "success": bool,
    "raw_html": str,
    "search_url": str,
    "total_found": int,
    "error": Optional[str]
}
```

**Core Logic**:
```python
@agent.tool
async def search_otlas_projects(
    ctx: RunContext[AgentDependencies],
    query_text: str,
    project_type: Optional[str] = None,
    max_results: int = 20
) -> Dict[str, Any]:
    """
    Search for project opportunities on SALTO-YOUTH Otlas.
    
    Args:
        query_text: General search terms
        project_type: Project type filter (KA152, KA153, etc.)
        max_results: Maximum results (1-100)
    
    Returns:
        Dictionary with search results and metadata
    """
    import httpx
    import asyncio
    
    try:
        # Rate limiting
        await asyncio.sleep(ctx.deps.request_delay)
        
        # Build search URL
        base_url = ctx.deps.otlas_base_url
        params = {
            "search": query_text,
            "searchType": "projects",
            "limit": min(max_results, 100)
        }
        if project_type:
            params["projectType"] = project_type
        
        # Make request
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{base_url}/search",
                params=params,
                headers={
                    "User-Agent": ctx.deps.user_agent,
                    "Accept": "text/html,application/xhtml+xml"
                }
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "raw_html": response.text,
                "search_url": str(response.url),
                "total_found": response.text.count('class="project-item"'),
                "error": None
            }
            
    except Exception as e:
        return {
            "success": False,
            "raw_html": "",
            "search_url": "",
            "total_found": 0,
            "error": str(e)
        }
```

**Error Handling**:
- HTTP timeouts and connection errors
- Rate limiting delays
- Invalid project type codes
- HTML parsing failures

---

## Tool 3: extract_structured_data

**Purpose**: Parse HTML results into structured Pydantic models

**Implementation Pattern**: `@agent.tool_plain` (pure HTML processing, no external dependencies)

**Parameters**:
- `raw_html: str` - HTML content from search results
- `data_type: Literal["organizations", "projects"]` - Type of data to extract
- `max_items: int = 20` - Maximum items to process

**Return Type**: `Dict[str, Any]`
```python
{
    "success": bool,
    "data": List[Dict[str, Any]],
    "parsed_count": int,
    "error": Optional[str]
}
```

**Core Logic**:
```python
@agent.tool_plain
def extract_structured_data(
    raw_html: str,
    data_type: Literal["organizations", "projects"],
    max_items: int = 20
) -> Dict[str, Any]:
    """
    Extract structured data from SALTO-YOUTH HTML search results.
    
    Args:
        raw_html: HTML content from search
        data_type: Type of data to extract
        max_items: Maximum items to process
    
    Returns:
        Dictionary with extracted structured data
    """
    from bs4 import BeautifulSoup
    import re
    
    try:
        soup = BeautifulSoup(raw_html, 'html.parser')
        extracted_items = []
        
        if data_type == "organizations":
            # Parse organization items
            org_items = soup.find_all('div', class_='org-item')[:max_items]
            
            for item in org_items:
                org_data = {
                    "name": extract_text(item, '.org-name'),
                    "country": extract_text(item, '.org-country'),
                    "organization_type": extract_text(item, '.org-type'),
                    "experience_level": extract_text(item, '.exp-level'),
                    "target_groups": extract_list(item, '.target-group'),
                    "activity_types": extract_list(item, '.activity-type'),
                    "contact_info": extract_text(item, '.contact-info'),
                    "profile_url": extract_url(item, '.org-link'),
                    "last_active": extract_text(item, '.last-active')
                }
                extracted_items.append(org_data)
                
        elif data_type == "projects":
            # Parse project items
            project_items = soup.find_all('div', class_='project-item')[:max_items]
            
            for item in project_items:
                project_data = {
                    "title": extract_text(item, '.project-title'),
                    "project_type": extract_text(item, '.project-type'),
                    "countries_involved": extract_list(item, '.countries'),
                    "deadline": extract_text(item, '.deadline'),
                    "target_groups": extract_list(item, '.target-groups'),
                    "themes": extract_list(item, '.themes'),
                    "description": extract_text(item, '.description'),
                    "contact_organization": extract_text(item, '.contact-org'),
                    "project_url": extract_url(item, '.project-link'),
                    "created_date": extract_text(item, '.created-date')
                }
                extracted_items.append(project_data)
        
        return {
            "success": True,
            "data": extracted_items,
            "parsed_count": len(extracted_items),
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "parsed_count": 0,
            "error": str(e)
        }


def extract_text(soup_element, selector: str) -> str:
    """Helper to extract text from CSS selector."""
    element = soup_element.select_one(selector)
    return element.get_text(strip=True) if element else ""

def extract_list(soup_element, selector: str) -> List[str]:
    """Helper to extract list of text from CSS selector."""
    elements = soup_element.select(selector)
    return [elem.get_text(strip=True) for elem in elements]

def extract_url(soup_element, selector: str) -> str:
    """Helper to extract URL from href attribute."""
    element = soup_element.select_one(selector)
    return element.get('href', '') if element else ""
```

**Error Handling**:
- Invalid HTML structure
- Missing CSS selectors
- Data type validation
- Empty result sets

---

## Tool Dependencies

**Required in AgentDependencies**:
```python
@dataclass
class AgentDependencies:
    otlas_base_url: str = "https://www.salto-youth.net/tools/otlas-partner-finding"
    user_agent: str = "ErasmusPartnerAgent/1.0"
    request_delay: float = 1.0
```

**Required Python Packages**:
```
httpx>=0.24.0        # Async HTTP client
beautifulsoup4>=4.12.0  # HTML parsing
lxml>=4.9.0          # Fast XML/HTML parser
```

---

## Usage Workflow

**Typical Agent Flow**:
1. User asks for "find partners in Germany for youth exchange"
2. Agent determines this is organization search
3. Calls `search_otlas_organizations(query_text="youth exchange", country="DE")`
4. Calls `extract_structured_data(raw_html, "organizations")`
5. Returns structured PartnerOrganization models

**Error Recovery**:
- If search fails, retry once with simplified parameters
- If parsing fails, return raw data with warning
- If rate limited, increase delay and retry

---

## Rate Limiting Strategy

**Respectful Scraping**:
- 1-second minimum delay between requests
- Maximum 10 concurrent requests per minute
- Exponential backoff on HTTP errors
- Proper User-Agent identification

**Implementation**:
```python
# In agent dependencies
request_delay: float = 1.0
max_requests_per_minute: int = 10
```

---

## Security Considerations

**Web Scraping Safety**:
- Validate all URLs before requests
- Sanitize HTML input before parsing
- Respect robots.txt (check manually)
- Handle CSRF tokens if required
- No credential storage in tools

**Input Validation**:
- Country codes against ISO standard
- Project types against known values
- HTML size limits (max 10MB)
- Search query length limits

---

## Testing Strategy

**Mock Testing**:
- Use sample HTML files for parsing tests
- Mock HTTP responses for search tests
- Validate Pydantic model creation
- Test error scenarios

**Integration Testing**:
- Test against live SALTO-YOUTH site (sparingly)
- Validate rate limiting behavior
- Test with various search parameters

---

Generated: 2025-01-27
Archon Project ID: b2dd2b4e-ba2e-468c-8bf4-e0dc503bd4ab