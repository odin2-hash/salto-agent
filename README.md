# Erasmus Partner Agent

An AI-powered agent for discovering Erasmus+ partnerships and project opportunities through the SALTO-YOUTH Otlas platform. Built with Pydantic AI, this agent provides both CLI and MCP server interfaces for seamless integration with various systems.

## 🎯 Features

- **Dual Search Functionality**: Find partner organizations OR project opportunities
- **Intelligent Intent Detection**: Automatically determines search type from natural language
- **Flexible Search Criteria**: Country, theme, target group, activity type, and more
- **Structured Data Output**: Returns validated Pydantic models for easy integration
- **Multiple Interfaces**: CLI, MCP server for n8n/Flowise/OpenWebUI integration
- **Respectful Web Scraping**: Rate-limited, ethical scraping of SALTO-YOUTH Otlas

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- Internet connection for accessing SALTO-YOUTH Otlas

### Installation

1. **Clone and navigate to the agent directory:**
   ```bash
   cd agents/erasmus_partner_agent
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Test the installation:**
   ```bash
   python -m erasmus_partner_agent.cli search "youth exchange partners in Germany"
   ```

## 📋 Environment Configuration

Create a `.env` file with these required settings:

```bash
# Required
LLM_API_KEY=your-openai-api-key-here
LLM_MODEL=gpt-4

# Optional (defaults shown)
OTLAS_BASE_URL=https://www.salto-youth.net/tools/otlas-partner-finding
REQUEST_DELAY=1.0
MAX_RESULTS=50
```

## 🖥️ Command Line Usage

### Basic Search (Auto-detect intent)
```bash
python -m erasmus_partner_agent.cli search "digital skills training partners"
```

### Partner Search
```bash
python -m erasmus_partner_agent.cli partners "youth exchange" --country Germany --max 10
```

### Project Search
```bash
python -m erasmus_partner_agent.cli projects "looking for partners" --type KA152
```

### Export Results
```bash
python -m erasmus_partner_agent.cli search "environmental projects" --export --format json
```

### CLI Options
- `--country`: Filter by country
- `--activity`: Filter by activity type
- `--theme`: Filter by project theme
- `--target`: Filter by target group
- `--max`: Maximum results (default: 20)
- `--export`: Export results to file
- `--format`: Output format (table, json, csv)

## 🌐 MCP Server Usage

### Start the Server
```bash
python -m erasmus_partner_agent.mcp_server
```

### API Endpoints

#### Search Partners
```http
POST /search/partners
Content-Type: application/json

{
  "query": "youth exchange partners",
  "country": "Germany",
  "activity_type": "Training course",
  "max_results": 20
}
```

#### Search Projects
```http
POST /search/projects
Content-Type: application/json

{
  "query": "digital skills project",
  "project_type": "KA152",
  "themes": ["Digital skills", "Media literacy"],
  "max_results": 20
}
```

#### Smart Search (Auto-detect)
```http
POST /search/smart
Content-Type: application/json

{
  "query": "I need partners for environmental youth exchange in Nordic countries",
  "max_results": 15
}
```

### Integration Examples

#### n8n Workflow
```json
{
  "nodes": [
    {
      "name": "Search Partners",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:8000/search/partners",
        "method": "POST",
        "body": {
          "query": "{{$json.search_query}}",
          "country": "{{$json.country}}",
          "max_results": 10
        }
      }
    }
  ]
}
```

#### OpenWebUI Integration
Add as an external service endpoint:
- URL: `http://localhost:8000/search/smart`
- Method: POST
- Use for Erasmus+ partnership discovery

## 🔧 Python API Usage

```python
import asyncio
from erasmus_partner_agent import run_search, AgentDependencies

async def search_partners():
    deps = AgentDependencies.from_settings()
    result = await run_search(
        "Find youth organizations in Spain for cultural exchange", 
        deps
    )
    
    if result.success:
        for org in result.results:
            print(f"{org.name} - {org.country}")
    
    await deps.cleanup()

# Run the search
asyncio.run(search_partners())
```

## 📊 Data Models

### PartnerOrganization
```python
{
  "name": "Youth for Europe Foundation",
  "country": "Germany",
  "organization_type": "NGO",
  "experience_level": "Experienced",
  "target_groups": ["Young people", "Youth workers"],
  "activity_types": ["Training courses", "Youth exchanges"],
  "contact_info": "info@yfe.de",
  "profile_url": "https://www.salto-youth.net/tools/otlas-partner-finding/organisation/123",
  "last_active": "2024-01-15"
}
```

### ProjectOpportunity
```python
{
  "title": "Digital Skills for Youth Workers",
  "project_type": "KA152",
  "countries_involved": ["Germany", "France"],
  "deadline": "2024-03-01",
  "target_groups": ["Youth workers", "Trainers"],
  "themes": ["Digital skills", "Media literacy"],
  "description": "Training course focusing on digital competencies...",
  "contact_organization": "European Youth Network",
  "project_url": "https://www.salto-youth.net/tools/otlas-partner-finding/project/456",
  "created_date": "2024-01-10"
}
```

### SearchResponse
```python
{
  "search_type": "organizations",  # or "projects"
  "query_parameters": {"query": "youth exchange", "country": "DE"},
  "total_results": 15,
  "results": [...],  # List of PartnerOrganization or ProjectOpportunity
  "search_timestamp": "2024-01-27T10:30:00",
  "success": true,
  "error_message": null
}
```

## 🔍 Search Parameters

### Countries
All EU member states plus Partner Countries:
- Germany, France, Spain, Italy, Poland, Netherlands, etc.

### Project Types
- **KA152**: Youth mobility projects
- **KA153**: Small-scale partnerships
- **KA154**: Participation activities
- **KA210**: Small-scale partnerships
- **KA220**: Cooperation partnerships
- **KA226**: Digital education readiness

### Themes
- Digital skills, Environment, Social inclusion
- Education, Democracy, Health, Culture
- Media literacy, Entrepreneurship, Employment

### Target Groups
- Young people, Youth workers, Teachers
- Trainers, Students, Researchers, Social workers

### Activity Types
- Training course, Study visit, Seminar
- Youth exchange, Cooperation project
- Strategic partnership, Capacity building

## ⚠️ Important Notes

### Web Scraping Ethics
- **Rate Limited**: 1-second delay between requests
- **Respectful**: Proper User-Agent identification
- **Public Data**: Only searches publicly available information
- **No Personal Data**: Contact info only if publicly listed

### Data Accuracy
- **Real-time**: Searches live SALTO-YOUTH Otlas platform
- **Validation**: All data validated with Pydantic models
- **Limitations**: Subject to website structure changes
- **Verification**: Always verify critical information manually

### API Keys
- **Required**: OpenAI API key for LLM functionality
- **Security**: Store in .env file, never commit to version control
- **Cost**: API usage charges apply per search

## 🧪 Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
black .
ruff check .
mypy .
```

### Adding New Features
1. Update models in `models.py`
2. Add tools in `tools.py`
3. Extend agent in `agent.py`
4. Update CLI/MCP interfaces as needed

## 🔧 Troubleshooting

### Common Issues

#### "LLM_API_KEY not found"
```bash
# Make sure .env file exists and contains:
LLM_API_KEY=your-actual-api-key-here
```

#### "No results found"
- Try broader search terms
- Check spelling of country/theme names
- Verify SALTO-YOUTH Otlas is accessible

#### "Rate limit exceeded"
- Increase `REQUEST_DELAY` in .env
- Reduce `CONCURRENT_REQUESTS`
- Wait before retrying searches

#### MCP Server won't start
```bash
# Check port availability
netstat -an | grep 8000

# Try different port
MCP_SERVER_PORT=8001 python -m erasmus_partner_agent.mcp_server
```

### Debug Mode
```bash
DEBUG=true python -m erasmus_partner_agent.cli search "test query"
```

## 📈 Performance

### Typical Response Times
- **Partner Search**: 3-8 seconds
- **Project Search**: 3-8 seconds
- **Smart Search**: 4-10 seconds

### Optimization Tips
- Use specific search terms
- Limit max_results for faster responses
- Enable caching for repeated searches
- Use concurrent_requests for batch operations

## 🤝 Integration Examples

### Zapier Integration
Use the MCP server endpoints in Zapier webhooks for automated partnership discovery.

### Slack Bot Integration
```python
from slack_bolt import App
from erasmus_partner_agent import run_search, AgentDependencies

app = App(token="your-slack-token")

@app.message("find partners")
async def find_partners(message, say):
    deps = AgentDependencies.from_settings()
    result = await run_search(message['text'], deps)
    
    if result.success:
        response = f"Found {len(result.results)} {result.search_type}:\\n"
        for item in result.results[:3]:  # Show top 3
            response += f"• {item.name}\\n"
    else:
        response = f"Search failed: {result.error_message}"
    
    await say(response)
    await deps.cleanup()
```

### Discord Bot Integration
Similar pattern using discord.py library with async/await support.

## 📋 Roadmap

### Planned Features
- [ ] Real-time project notifications
- [ ] Advanced filtering and sorting
- [ ] Batch search operations
- [ ] Export to multiple formats
- [ ] Integration templates for popular platforms
- [ ] Caching and offline mode
- [ ] Multi-language support

### Contributions
Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🆘 Support

### Documentation
- [Pydantic AI Documentation](https://ai.pydantic.dev/)
- [SALTO-YOUTH Otlas Platform](https://www.salto-youth.net/tools/otlas-partner-finding/)
- [Erasmus+ Programme Guide](https://ec.europa.eu/programmes/erasmus-plus/)

### Issues
Report issues at: [GitHub Issues](https://github.com/your-repo/issues)

### Community
- Join discussions about Erasmus+ partnerships
- Share your success stories
- Request new features

---

**Built with ❤️ for the Erasmus+ community**

*Empowering European youth organizations to find perfect partnerships and create impactful projects across borders.*