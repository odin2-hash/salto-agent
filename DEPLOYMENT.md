# Deployment Guide - Erasmus Partner Agent

This guide covers deployment options for the Erasmus Partner Agent in various environments.

## 🚀 Quick Deployment Options

### Local Development
```bash
# 1. Set up environment
cp .env.example .env
# Edit .env with your OpenAI API key

# 2. Install dependencies
pip install -r requirements.txt

# 3. Test CLI
python -m erasmus_partner_agent.cli search "test query"

# 4. Start MCP server
python -m erasmus_partner_agent.mcp_server
```

### Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Set environment
ENV PYTHONPATH=/app

# Expose MCP server port
EXPOSE 8000

# Default command
CMD ["python", "-m", "erasmus_partner_agent.mcp_server"]
```

```bash
# Build and run
docker build -t erasmus-partner-agent .
docker run -p 8000:8000 --env-file .env erasmus-partner-agent
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  erasmus-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LLM_API_KEY=${LLM_API_KEY}
      - MCP_SERVER_HOST=0.0.0.0
      - MCP_SERVER_PORT=8000
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## ☁️ Cloud Deployment

### AWS Deployment

#### AWS ECS with Fargate
```json
{
  "family": "erasmus-partner-agent",
  "taskDefinition": {
    "requiresCompatibilities": ["FARGATE"],
    "networkMode": "awsvpc",
    "cpu": "512",
    "memory": "1024",
    "containerDefinitions": [
      {
        "name": "erasmus-agent",
        "image": "your-repo/erasmus-partner-agent:latest",
        "portMappings": [
          {
            "containerPort": 8000,
            "protocol": "tcp"
          }
        ],
        "environment": [
          {
            "name": "LLM_API_KEY",
            "valueFrom": "arn:aws:secretsmanager:region:account:secret:erasmus-api-key"
          }
        ],
        "logConfiguration": {
          "logDriver": "awslogs",
          "options": {
            "awslogs-group": "/ecs/erasmus-partner-agent",
            "awslogs-region": "us-west-2",
            "awslogs-stream-prefix": "ecs"
          }
        }
      }
    ]
  }
}
```

#### AWS Lambda (Serverless)
```python
# lambda_handler.py
import json
from mangum import Mangum
from erasmus_partner_agent.mcp_server import app

# Wrap FastAPI app for Lambda
handler = Mangum(app)

def lambda_handler(event, context):
    return handler(event, context)
```

```yaml
# serverless.yml
service: erasmus-partner-agent

provider:
  name: aws
  runtime: python3.11
  region: us-west-2
  environment:
    LLM_API_KEY: ${env:LLM_API_KEY}
  
functions:
  api:
    handler: lambda_handler.handler
    events:
      - http:
          path: /{proxy+}
          method: ANY
    timeout: 30
    memorySize: 1024

plugins:
  - serverless-python-requirements
```

### Google Cloud Deployment

#### Cloud Run
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/erasmus-partner-agent
gcloud run deploy erasmus-partner-agent \
  --image gcr.io/PROJECT_ID/erasmus-partner-agent \
  --platform managed \
  --region us-central1 \
  --set-env-vars LLM_API_KEY="your-api-key"
```

#### Cloud Functions
```python
# main.py for Cloud Functions
from flask import Request
from erasmus_partner_agent import run_search, AgentDependencies

def erasmus_search(request: Request):
    """HTTP Cloud Function for partner search."""
    request_json = request.get_json()
    
    if not request_json or 'query' not in request_json:
        return {'error': 'Missing query parameter'}, 400
    
    # Run search
    deps = AgentDependencies.from_settings()
    result = run_search(request_json['query'], deps)
    
    return result.dict()
```

### Azure Deployment

#### Azure Container Instances
```bash
# Deploy to ACI
az container create \
  --resource-group myResourceGroup \
  --name erasmus-partner-agent \
  --image erasmus-partner-agent:latest \
  --dns-name-label erasmus-agent \
  --ports 8000 \
  --environment-variables LLM_API_KEY="your-api-key"
```

#### Azure Functions
```python
# function_app.py
import azure.functions as func
import json
from erasmus_partner_agent import run_search, AgentDependencies

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="search", methods=["POST"])
def search_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        query = req_body.get('query')
        
        deps = AgentDependencies.from_settings()
        result = run_search(query, deps)
        
        return func.HttpResponse(
            json.dumps(result.dict()),
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
```

## 🔗 Integration Deployments

### n8n Integration

#### Self-hosted n8n
```yaml
# docker-compose-n8n.yml
version: '3.8'
services:
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=your-password
    volumes:
      - n8n_data:/home/node/.n8n
    depends_on:
      - erasmus-agent
      
  erasmus-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LLM_API_KEY=${LLM_API_KEY}

volumes:
  n8n_data:
```

#### n8n Workflow Template
```json
{
  "name": "Erasmus Partner Search",
  "nodes": [
    {
      "parameters": {
        "url": "http://erasmus-agent:8000/search/smart",
        "options": {
          "bodyContentType": "json"
        },
        "body": {
          "query": "{{ $json.search_query }}",
          "max_results": 10
        }
      },
      "name": "Search Partners",
      "type": "n8n-nodes-base.httpRequest"
    }
  ]
}
```

### Flowise Integration

#### Flowise with Custom Tool
```javascript
// Custom Flowise tool configuration
{
  "name": "ErasmusPartnerSearch",
  "description": "Search for Erasmus+ partners and projects",
  "baseURL": "http://localhost:8000",
  "endpoints": {
    "searchPartners": "/search/partners",
    "searchProjects": "/search/projects",
    "smartSearch": "/search/smart"
  }
}
```

### OpenWebUI Integration

#### OpenWebUI Function
```python
"""
title: Erasmus Partner Search
author: Erasmus Agent
version: 1.0.0
"""

import requests
import json

class Tools:
    def __init__(self):
        self.base_url = "http://localhost:8000"
    
    def search_erasmus_partners(self, query: str, country: str = None) -> str:
        """
        Search for Erasmus+ partner organizations.
        
        Args:
            query (str): Search query for partners
            country (str): Optional country filter
        """
        payload = {"query": query}
        if country:
            payload["country"] = country
        
        response = requests.post(
            f"{self.base_url}/search/partners",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                organizations = result.get("organizations", [])
                return f"Found {len(organizations)} partner organizations:\n" + \
                       "\n".join([f"• {org['name']} ({org['country']})" for org in organizations[:5]])
            else:
                return f"Search failed: {result.get('error_message')}"
        else:
            return f"Request failed with status {response.status_code}"
```

## 🔧 Environment Configuration

### Production Environment Variables
```bash
# Required
LLM_API_KEY=your-production-openai-key
LLM_MODEL=gpt-4

# Performance
REQUEST_DELAY=0.5
CONCURRENT_REQUESTS=5
CONNECTION_POOL_SIZE=20

# Logging
LOG_LEVEL=INFO
DEBUG=false

# MCP Server
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
MCP_SERVER_RELOAD=false

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

### Kubernetes ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: erasmus-agent-config
data:
  LLM_MODEL: "gpt-4"
  REQUEST_DELAY: "0.5"
  LOG_LEVEL: "INFO"
  MCP_SERVER_HOST: "0.0.0.0"
  MCP_SERVER_PORT: "8000"
---
apiVersion: v1
kind: Secret
metadata:
  name: erasmus-agent-secrets
type: Opaque
stringData:
  LLM_API_KEY: "your-openai-api-key"
```

## 🔍 Monitoring & Observability

### Health Checks
```python
# health_check.py
import requests
import time

def check_agent_health():
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data['status']}")
            print(f"Agent Status: {data['agent_status']}")
            return True
    except Exception as e:
        print(f"Health check failed: {e}")
    return False

# Continuous monitoring
while True:
    if not check_agent_health():
        print("⚠️ Agent unhealthy - alerts should fire")
    time.sleep(30)
```

### Prometheus Metrics
```python
# Add to mcp_server.py
from prometheus_client import Counter, Histogram, generate_latest

search_counter = Counter('erasmus_searches_total', 'Total searches', ['search_type'])
search_duration = Histogram('erasmus_search_duration_seconds', 'Search duration')

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Logging Configuration
```python
# logging_config.py
import structlog
import logging

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

## 🛡️ Security Considerations

### API Key Management
```bash
# Use secret management services
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name erasmus-agent/openai-key \
  --secret-string "your-api-key"

# Azure Key Vault  
az keyvault secret set \
  --vault-name erasmus-vault \
  --name openai-api-key \
  --value "your-api-key"

# Google Secret Manager
echo -n "your-api-key" | gcloud secrets create openai-api-key --data-file=-
```

### Network Security
```yaml
# Kubernetes NetworkPolicy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: erasmus-agent-netpol
spec:
  podSelector:
    matchLabels:
      app: erasmus-agent
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: allowed-clients
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS for external APIs
```

### Rate Limiting
```python
# Add to mcp_server.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/search/partners")
@limiter.limit("10/minute")
def search_partners(request: Request, ...):
    # Implementation
```

## 🚨 Troubleshooting Deployment

### Common Issues

#### Port Binding Issues
```bash
# Check port availability
netstat -tulpn | grep :8000

# Use different port
MCP_SERVER_PORT=8001 python -m erasmus_partner_agent.mcp_server
```

#### Memory Issues
```bash
# Monitor memory usage
docker stats erasmus-partner-agent

# Increase memory limit
docker run -m 2g -p 8000:8000 erasmus-partner-agent
```

#### API Key Issues
```bash
# Verify API key is set
python -c "from erasmus_partner_agent.settings import load_settings; print(load_settings().llm_api_key[:10])"

# Test API connection
python -c "from erasmus_partner_agent.providers import get_llm_model; print('LLM model configured')"
```

### Debugging Commands
```bash
# Enable debug mode
DEBUG=true LOG_LEVEL=DEBUG python -m erasmus_partner_agent.mcp_server

# Test specific endpoints
curl -X POST http://localhost:8000/health
curl -X POST http://localhost:8000/search/partners -H "Content-Type: application/json" -d '{"query": "test"}'

# Check logs
docker logs erasmus-partner-agent --tail 50 --follow
```

## 📊 Performance Tuning

### Optimization Settings
```bash
# High-performance configuration
CONCURRENT_REQUESTS=10
CONNECTION_POOL_SIZE=50
REQUEST_DELAY=0.2
ENABLE_CACHING=true
CACHE_TTL=1800

# Memory optimization
PYTHON_OPTS="-O -u"
UVICORN_WORKERS=4
UVICORN_WORKER_CLASS="uvicorn.workers.UvicornWorker"
```

### Scaling Configuration
```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: erasmus-agent-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: erasmus-agent
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

This deployment guide covers all major deployment scenarios from local development to enterprise-scale cloud deployments. Choose the option that best fits your infrastructure and requirements.