# Docker Guide - Erasmus Partner Agent

Complete Docker setup for running the Erasmus Partner Agent in containers.

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Clone the repository
git clone https://github.com/odin2-hash/erasmus-partner-agent.git
cd erasmus-partner-agent

# Copy environment file and add your OpenAI API key
cp .env.docker .env
# Edit .env and add: LLM_API_KEY=your-openai-api-key-here
```

### 2. Run with Docker Compose
```bash
# Start the service (development mode with hot reload)
docker-compose up -d

# Check logs
docker-compose logs -f erasmus-partner-agent

# Test the service
curl http://localhost:8000/health
```

### 3. Use the Service
```bash
# Test partner search via API
curl -X POST http://localhost:8000/search/partners \
  -H "Content-Type: application/json" \
  -d '{"query": "youth exchange partners in Germany", "max_results": 5}'

# Test project search
curl -X POST http://localhost:8000/search/projects \
  -H "Content-Type: application/json" \
  -d '{"query": "digital skills projects looking for partners", "max_results": 5}'
```

## 🔧 Configuration Options

### Basic Setup (.env file)
```bash
# Required
LLM_API_KEY=your-openai-api-key-here

# Optional customization
LLM_MODEL=gpt-4
LOG_LEVEL=INFO
REQUEST_DELAY=1.0
CONCURRENT_REQUESTS=3
```

### Advanced Configuration
```bash
# Performance tuning
REQUEST_DELAY=0.5
CONCURRENT_REQUESTS=5
CONNECTION_POOL_SIZE=20
ENABLE_CACHING=true

# Debug mode
DEBUG=true
LOG_LEVEL=DEBUG
```

## 🐳 Docker Commands

### Basic Operations
```bash
# Build and start services
docker-compose up -d

# Rebuild after code changes
docker-compose build
docker-compose up -d

# View logs
docker-compose logs -f
docker-compose logs erasmus-partner-agent

# Stop services
docker-compose down

# Restart specific service
docker-compose restart erasmus-partner-agent
```

### CLI Usage in Docker
```bash
# Run CLI commands through Docker
docker-compose exec erasmus-partner-agent python -m erasmus_partner_agent.cli search "test query"

# Run partners search
docker-compose exec erasmus-partner-agent python -m erasmus_partner_agent.cli partners "youth exchange" --country Germany

# Run projects search
docker-compose exec erasmus-partner-agent python -m erasmus_partner_agent.cli projects "digital skills" --type KA152
```

### Direct Docker Usage (without compose)
```bash
# Build image
docker build -t erasmus-partner-agent .

# Run container
docker run -d \
  --name erasmus-agent \
  -p 8000:8000 \
  -e LLM_API_KEY="your-api-key" \
  -v $(pwd)/exports:/app/exports \
  erasmus-partner-agent

# Run CLI in container
docker exec erasmus-agent python -m erasmus_partner_agent.cli search "test query"
```

## 🏭 Production Deployment

### Production with Nginx
```bash
# Start with production profile (includes nginx reverse proxy)
docker-compose --profile production up -d

# Services will be available at:
# http://localhost:80 (nginx proxy)
# http://localhost:8000 (direct agent access)
```

### Production Environment Variables
```bash
# .env for production
LLM_API_KEY=your-production-api-key
APP_ENV=production
LOG_LEVEL=INFO
DEBUG=false
MCP_SERVER_RELOAD=false

# Performance optimizations
REQUEST_DELAY=0.5
CONCURRENT_REQUESTS=5
CONNECTION_POOL_SIZE=20
ENABLE_CACHING=true
CACHE_TTL=1800
```

## 📊 Advanced Features

### With Redis Caching
```bash
# Start with caching profile
docker-compose --profile caching up -d

# Redis will be available at localhost:6379
# Configure agent to use Redis for caching
```

### With Monitoring (Prometheus)
```bash
# Start with monitoring profile
docker-compose --profile monitoring up -d

# Prometheus will be available at http://localhost:9090
# Add metrics endpoint to agent configuration
```

### All Services Combined
```bash
# Start all services (production + caching + monitoring)
docker-compose --profile production --profile caching --profile monitoring up -d
```

## 🔍 Health Monitoring

### Health Check Endpoints
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed status via nginx (if using production profile)
curl http://localhost:80/health

# Check service status
docker-compose ps
```

### Container Logs
```bash
# All services logs
docker-compose logs

# Specific service logs
docker-compose logs erasmus-partner-agent
docker-compose logs nginx
docker-compose logs redis

# Follow logs in real-time
docker-compose logs -f erasmus-partner-agent
```

### Resource Usage
```bash
# Monitor resource usage
docker stats

# Specific container stats
docker stats erasmus-partner-agent
```

## 🔧 Development Setup

### Development with Hot Reload
```bash
# The docker-compose.override.yml automatically provides hot reload
docker-compose up -d

# Code changes will automatically restart the server
# Logs will show debug information
```

### Development Commands
```bash
# Run tests in container
docker-compose exec erasmus-partner-agent python -m pytest

# Run linting
docker-compose exec erasmus-partner-agent python -m ruff check .

# Run formatting
docker-compose exec erasmus-partner-agent python -m black .

# Access container shell
docker-compose exec erasmus-partner-agent bash
```

### Development Environment Variables
The `docker-compose.override.yml` automatically sets:
```bash
APP_ENV=development
LOG_LEVEL=DEBUG
DEBUG=true
MCP_SERVER_RELOAD=true
```

## 🚨 Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs for startup errors
docker-compose logs erasmus-partner-agent

# Common issues:
# 1. Missing LLM_API_KEY in .env file
# 2. Invalid API key format
# 3. Port 8000 already in use
```

#### API Key Issues
```bash
# Check if API key is set correctly
docker-compose exec erasmus-partner-agent env | grep LLM_API_KEY

# Test API key validation
docker-compose exec erasmus-partner-agent python -c "
from erasmus_partner_agent.settings import load_settings
print('API key loaded:', load_settings().llm_api_key[:10] + '...')
"
```

#### Port Conflicts
```bash
# Check what's using port 8000
netstat -tulpn | grep :8000
lsof -i :8000

# Use different port
# Edit docker-compose.yml to change "8001:8000" instead of "8000:8000"
```

#### Memory Issues
```bash
# Check container memory usage
docker stats erasmus-partner-agent

# Increase memory limit in docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 2G
```

#### Permission Issues
```bash
# Fix volume permissions
sudo chown -R $USER:$USER ./exports ./logs

# Or run container as root (not recommended for production)
docker-compose exec --user root erasmus-partner-agent bash
```

### Debug Commands
```bash
# Test agent configuration
docker-compose exec erasmus-partner-agent python -c "
from erasmus_partner_agent import AgentDependencies
deps = AgentDependencies.from_settings()
print('Agent configuration loaded successfully')
"

# Test basic search functionality
docker-compose exec erasmus-partner-agent python -c "
import asyncio
from erasmus_partner_agent import run_search, AgentDependencies

async def test():
    deps = AgentDependencies.from_settings()
    result = await run_search('test query', deps)
    print('Search result:', result.success)
    await deps.cleanup()

asyncio.run(test())
"

# Check network connectivity
docker-compose exec erasmus-partner-agent curl -I https://www.salto-youth.net
```

## 📈 Performance Tuning

### Container Resource Limits
```yaml
# Add to docker-compose.yml services section
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### Environment Variables for Performance
```bash
# High-performance configuration
REQUEST_DELAY=0.2
CONCURRENT_REQUESTS=10
CONNECTION_POOL_SIZE=50
TIMEOUT_SECONDS=15
ENABLE_CACHING=true
CACHE_TTL=900  # 15 minutes
```

### Scaling with Multiple Replicas
```bash
# Scale the service to multiple replicas
docker-compose up -d --scale erasmus-partner-agent=3

# Use nginx for load balancing (already configured in nginx.conf)
```

## 🔐 Security Considerations

### Production Security
```bash
# Use secure API key storage
# Don't put API keys in docker-compose.yml directly
# Use .env file with proper permissions
chmod 600 .env

# Run as non-root user (already configured in Dockerfile)
# Use nginx reverse proxy for rate limiting
# Enable HTTPS with SSL certificates
```

### Network Security
```yaml
# Create custom network for isolation
networks:
  erasmus-secure:
    driver: bridge
    internal: true  # No internet access except for specific services
```

This Docker setup provides a complete containerized deployment of the Erasmus Partner Agent with development and production configurations.