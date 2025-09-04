# Erasmus Partner Agent - Simple Requirements

## What This Agent Does
A specialized Pydantic AI agent that searches the SALTO-YOUTH Otlas platform to help users find partner organizations for Erasmus+ projects and discover interesting projects looking for partners. The agent adapts its search focus based on user prompts and returns structured data for integration with other AI systems.

## Core Features (MVP)
1. **Partner Organization Search**: Find suitable partner organizations from 17,000+ organizations using flexible search criteria (country, theme, target group, activity type, experience level)
2. **Project Opportunity Search**: Discover active projects looking for partners from 11,000+ projects with detailed filtering capabilities
3. **Intelligent Search Focus**: Automatically determine whether to search for partners or projects based on user prompt context and intent

## Technical Setup

### Agent Type Classification
- **Tool-Enabled Agent**: External integrations focus with web scraping capabilities
- **Structured Output Agent**: Complex data validation and structured responses for tool usage
- **Dual Interface Agent**: Both CLI and MCP server support

### Model
- **Provider**: OpenAI
- **Model**: gpt-4
- **Why**: Reliable reasoning for search intent detection and result interpretation

### Required Tools
1. **Web Scraper Tool**: Extract data from SALTO-YOUTH Otlas search pages with intelligent parsing
2. **Search Parameter Builder**: Construct search URLs with flexible filter combinations (country, activity, theme, target group, deadline)
3. **Data Structure Validator**: Parse and validate scraped results into structured Pydantic models

### External Services
- **SALTO-YOUTH Otlas Platform**: Primary data source for organizations and projects
- **Web Scraping Service**: Extract data from search result pages (no public API available)

## Environment Variables
```bash
LLM_API_KEY=your-openai-api-key
OTLAS_BASE_URL=https://www.salto-youth.net/tools/otlas-partner-finding
USER_AGENT=ErasmusPartnerAgent/1.0
REQUEST_DELAY=1.0
```

## Data Models (Structured Output)

### Organization Model
```python
class PartnerOrganization(BaseModel):
    name: str
    country: str
    organization_type: str
    experience_level: str
    target_groups: List[str]
    activity_types: List[str]
    contact_info: str
    profile_url: str
    last_active: Optional[str]
```

### Project Model
```python
class ProjectOpportunity(BaseModel):
    title: str
    project_type: str
    countries_involved: List[str]
    deadline: Optional[str]
    target_groups: List[str]
    themes: List[str]
    description: str
    contact_organization: str
    project_url: str
    created_date: str
```

### Search Response Model
```python
class SearchResponse(BaseModel):
    search_type: Literal["organizations", "projects"]
    query_parameters: Dict[str, Any]
    total_results: int
    results: Union[List[PartnerOrganization], List[ProjectOpportunity]]
    search_timestamp: str
```

## Interface Requirements

### CLI Interface
- Interactive mode for direct user queries
- Batch mode for processing multiple search criteria
- Export results to JSON/CSV formats

### MCP Server Interface
- RESTful endpoints for integration with n8n, Flowise, OpenWebUI
- Standardized request/response schemas
- Authentication support for secure integrations

## Success Criteria
- [ ] Successfully scrapes and parses SALTO-YOUTH Otlas search results
- [ ] Correctly identifies user intent (partner search vs project search) from natural language prompts
- [ ] Returns structured data in consistent Pydantic models
- [ ] Handles search errors and rate limiting gracefully
- [ ] Provides both CLI and MCP server interfaces
- [ ] Supports flexible search criteria combinations
- [ ] Maintains reasonable response times (<30 seconds per search)

## Search Capabilities

### Maximum Flexibility Parameters
- **Country**: Any EU country, Partner Countries, specific regions
- **Activity Type**: Training courses, Study visits, Seminars, Youth exchanges, etc.
- **Theme**: Education, Social inclusion, Environment, Digital skills, etc.
- **Target Group**: Young people, Youth workers, Teachers, Trainers, etc.
- **Project Type**: KA152, KA153, KA154, KA210, KA220, etc.
- **Experience Level**: Newcomers, Experienced, Expert organizations
- **Deadline Filters**: Upcoming, Recent, All time periods

## Assumptions Made
- **No Public API**: Web scraping required as SALTO-YOUTH Otlas doesn't provide public API access
- **Rate Limiting**: Implement 1-second delays between requests to be respectful
- **Search Intent Detection**: Use LLM reasoning to determine if user wants partners or projects
- **Structured Output Priority**: Focus on Pydantic models over natural language responses
- **Authentication**: Assume public search capabilities, may need MySALTO account for full contact details
- **Error Handling**: Graceful degradation when website structure changes or becomes unavailable

## Technical Architecture Notes
- **Web Scraping Strategy**: BeautifulSoup + requests for HTML parsing
- **Async Support**: Implement async/await patterns for concurrent searches
- **Caching**: Simple in-memory caching for repeated searches within session
- **Logging**: Comprehensive logging for debugging scraping issues
- **Configuration**: Environment-based settings for easy deployment

## Integration Considerations
- **MCP Protocol**: Follow MCP specification for server implementation
- **Data Validation**: Strict Pydantic validation for all outputs
- **Error Response Format**: Consistent error models for both CLI and MCP interfaces
- **Extensibility**: Design for easy addition of new search parameters

---
Generated: 2025-01-27
Archon Project ID: b2dd2b4e-ba2e-468c-8bf4-e0dc503bd4ab
Note: This is an MVP focusing on core search functionality. Advanced features like real-time notifications, saved searches, and detailed analytics can be added after the basic agent works.