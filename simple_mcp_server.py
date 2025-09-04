#!/usr/bin/env python3
"""
Simple MCP Server for Erasmus Partner Agent
Works with n8n, OpenWebUI, and other MCP clients
"""
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
from tools import search_otlas_organizations
from dependencies import AgentDependencies

# Initialize FastAPI app
app = FastAPI(
    title="Erasmus Partner Agent MCP Server",
    description="Find Erasmus+ partner organizations and projects via SALTO-YOUTH Otlas",
    version="1.0.0"
)

class MockRunContext:
    def __init__(self, deps):
        self.deps = deps

class SearchRequest(BaseModel):
    query: str
    country: Optional[str] = None
    max_results: Optional[int] = 20

class SearchResponse(BaseModel):
    success: bool
    results_found: int
    search_url: str
    organizations: List[Dict[str, Any]] = []
    error_message: Optional[str] = None

# Global dependencies
deps = None

@app.on_event("startup")
async def startup_event():
    """Initialize dependencies on server startup."""
    global deps
    try:
        deps = AgentDependencies.from_settings()
        print("✅ Erasmus Partner Agent MCP Server initialized")
        print("🔐 Authentication configured")
        print("🌐 Ready to accept requests on http://localhost:8000")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        raise

@app.on_event("shutdown") 
async def shutdown_event():
    """Cleanup on server shutdown."""
    global deps
    if deps:
        await deps.cleanup()

@app.get("/")
async def root():
    """Root endpoint with server info."""
    return {
        "name": "Erasmus Partner Agent MCP Server",
        "version": "1.0.0",
        "description": "Find Erasmus+ partner organizations via SALTO-YOUTH Otlas",
        "endpoints": {
            "search_partners": "POST /search/partners - Search for partner organizations",
            "health": "GET /health - Server health check"
        },
        "status": "ready"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Erasmus Partner Agent MCP Server is running"}

@app.post("/search/partners", response_model=SearchResponse)
async def search_partners(request: SearchRequest):
    """
    Search for Erasmus+ partner organizations.
    
    This endpoint searches the SALTO-YOUTH Otlas platform for organizations
    matching the specified criteria.
    """
    global deps
    
    if not deps:
        raise HTTPException(status_code=500, detail="Server not properly initialized")
    
    try:
        # Create mock context and run search
        ctx = MockRunContext(deps)
        result = await search_otlas_organizations(
            ctx, 
            request.query, 
            country=request.country, 
            max_results=request.max_results
        )
        
        if result['success']:
            return SearchResponse(
                success=True,
                results_found=result['total_found'],
                search_url=result['search_url'],
                organizations=[],  # Raw HTML parsing would go here
                error_message=None
            )
        else:
            return SearchResponse(
                success=False,
                results_found=0,
                search_url="",
                organizations=[],
                error_message=result['error']
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# MCP-compatible endpoints for various clients

@app.post("/mcp/search")
async def mcp_search(request: Dict[str, Any]):
    """MCP-compatible search endpoint for generic clients."""
    search_req = SearchRequest(
        query=request.get("query", ""),
        country=request.get("country"),
        max_results=request.get("max_results", 20)
    )
    return await search_partners(search_req)

@app.get("/api/partners")
async def get_partners(
    q: str,
    country: Optional[str] = None,
    limit: Optional[int] = 20
):
    """REST API endpoint for easy integration."""
    search_req = SearchRequest(query=q, country=country, max_results=limit)
    return await search_partners(search_req)

def main():
    """Run the MCP server."""
    import os
    port = int(os.getenv('MCP_SERVER_PORT', 8000))
    
    print("🚀 Starting Erasmus Partner Agent MCP Server...")
    print(f"📍 Server will be available at: http://localhost:{port}")
    print(f"📖 API docs at: http://localhost:{port}/docs")
    print(f"🔍 Search endpoint: POST http://localhost:{port}/search/partners")
    
    uvicorn.run(
        "simple_mcp_server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()