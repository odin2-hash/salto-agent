# 🐳 SALTO Agent - Docker Quick Start

Run SALTO Agent without cloning the repository! Just download the docker-compose file and start.

## Quick Start (No Repository Clone Needed)

### 1. Download and Run
```bash
# Download the standalone docker-compose file
curl -O https://raw.githubusercontent.com/odin2-hash/salto-agent/main/docker-compose.standalone.yml

# Download environment template
curl -O https://raw.githubusercontent.com/odin2-hash/salto-agent/main/.env.example

# Copy and configure environment
cp .env.example .env
# Edit .env with your credentials and configuration

# Start the application
docker-compose -f docker-compose.standalone.yml up -d
```

### 2. Access the Application
- **MCP Server**: http://localhost:8095
- **Health Check**: http://localhost:8095/health

## Environment Configuration

Before starting, you **must** configure your `.env` file with:

### Required Configuration
```bash
# LLM Configuration
LLM_API_KEY=your_openai_api_key_here

# SALTO-YOUTH Credentials (Register at salto-youth.net)
SALTO_USERNAME=your_salto_username
SALTO_PASSWORD=your_salto_password
```

### Optional Configuration
```bash
# LLM Settings
LLM_MODEL=gpt-4o-mini
LLM_PROVIDER=openai

# Application Settings
APP_ENV=production
LOG_LEVEL=INFO
DEBUG=false

# Performance
CONCURRENT_REQUESTS=3
SCRAPING_DELAY=1.0
CACHE_TTL=3600
```

## Optional Profiles

### With Nginx Reverse Proxy
```bash
docker-compose -f docker-compose.standalone.yml --profile with-nginx up -d
```
Access via: http://localhost (port 80)

### With Redis Caching
```bash
docker-compose -f docker-compose.standalone.yml --profile with-redis up -d
```

### With Monitoring
```bash
docker-compose -f docker-compose.standalone.yml --profile with-monitoring up -d
```
Access Prometheus: http://localhost:9090

## Management Commands

```bash
# Start services
docker-compose -f docker-compose.standalone.yml up -d

# Stop services
docker-compose -f docker-compose.standalone.yml down

# View logs
docker-compose -f docker-compose.standalone.yml logs -f salto-agent

# Update to latest images
docker-compose -f docker-compose.standalone.yml pull
docker-compose -f docker-compose.standalone.yml up -d
```

## Health Checks

The SALTO Agent includes health checks available at:
- `http://localhost:8095/health` - Basic health check

## Usage Examples

### Using as MCP Server
Connect to the MCP server at `http://localhost:8095` from your MCP client.

### CLI Usage
```bash
# Execute commands inside the container
docker-compose -f docker-compose.standalone.yml exec salto-agent python cli.py

# Or run one-off commands
docker-compose -f docker-compose.standalone.yml run --rm salto-agent python -c "
from salto_agent import run_partner_search
result = run_partner_search('youth work Germany')
print(result)
"
```

### API Integration
```python
import requests

# Search for partners
response = requests.post('http://localhost:8095/search', json={
    'query': 'digital skills training',
    'country': 'Germany',
    'organization_type': 'NGO'
})

partners = response.json()
```

## Data Persistence

The container creates volumes for:
- **Exports**: `/app/exports` - Downloaded partner data and reports
- **Logs**: `/app/logs` - Application logs and debug information

## Troubleshooting

### Port Conflicts
If you have port conflicts, modify the docker-compose.standalone.yml:
```yaml
ports:
  - "YOUR_PORT:8095"  # Change YOUR_PORT to available port
```

### View Container Status
```bash
docker-compose -f docker-compose.standalone.yml ps
```

### Debug Logs
```bash
docker-compose -f docker-compose.standalone.yml logs -f salto-agent
```

### Reset Everything
```bash
docker-compose -f docker-compose.standalone.yml down -v
docker-compose -f docker-compose.standalone.yml up -d
```

## SALTO-YOUTH Account Setup

1. **Register Account**: Visit https://salto-youth.net and create an account
2. **Access OTLAS**: Navigate to Tools → OTLAS Partner Finding
3. **Get Credentials**: Use your login email and password in `.env` file
4. **Test Access**: Ensure you can login to OTLAS manually first

## Image Information

Images are automatically built and published to GitHub Container Registry:
- **SALTO Agent**: `ghcr.io/odin2-hash/salto-agent:latest`

## Development Mode

For development with live code changes, clone the repository and use:
```bash
git clone https://github.com/odin2-hash/salto-agent.git
cd salto-agent
docker-compose up -d
```

## Security Notes

- Never commit your `.env` file with real credentials
- Use environment variables for production deployments
- Consider using Docker secrets for sensitive data in production
- Regularly update the Docker image for security patches