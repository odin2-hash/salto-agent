"""
MCP Server implementation for the Erasmus Partner Agent.

This module provides an MCP-compliant server interface for integration
with external systems like n8n, Flowise, and OpenWebUI.
"""
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import uvicorn

from .agent import run_search, extract_search_parameters
from .dependencies import AgentDependencies
from .models import SearchResponse, PartnerOrganization, ProjectOpportunity


# Request Models
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
    target_group: Optional[str] = None
    deadline_after: Optional[str] = None
    max_results: int = 20


class SmartSearchRequest(BaseModel):
    """Request model for intelligent search with automatic intent detection."""
    query: str
    max_results: int = 20
    force_search_type: Optional[str] = None  # "organizations" or "projects"


# Response Models
class PartnerSearchResponse(BaseModel):
    """Response model for partner search."""
    success: bool
    search_type: str = "organizations"
    query_parameters: Dict[str, Any]
    total_results: int
    organizations: List[PartnerOrganization]
    search_timestamp: str
    error_message: Optional[str] = None


class ProjectSearchResponse(BaseModel):
    """Response model for project search."""
    success: bool
    search_type: str = "projects"
    query_parameters: Dict[str, Any]
    total_results: int
    projects: List[ProjectOpportunity]
    search_timestamp: str
    error_message: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    agent_status: str
    timestamp: str


# Create FastAPI app
app = FastAPI(
    title="Erasmus Partner Agent MCP Server",
    version="1.0.0",
    description="MCP server for Erasmus+ partnership search and discovery",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to create agent dependencies
async def get_agent_deps() -> AgentDependencies:
    """Create and return agent dependencies."""
    return AgentDependencies.from_settings()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    from datetime import datetime
    
    return HealthResponse(
        status="healthy",
        agent_status="ready",
        timestamp=datetime.now().isoformat()
    )


@app.post("/search/partners", response_model=PartnerSearchResponse)
async def search_partners(
    request: PartnerSearchRequest,
    deps: AgentDependencies = Depends(get_agent_deps)
):
    """
    Search for partner organizations based on criteria.
    
    This endpoint searches the SALTO-YOUTH Otlas platform for organizations
    that could serve as partners for Erasmus+ projects.
    """
    try:
        # Build enhanced query
        enhanced_query = f"Find partner organizations: {request.query}"
        
        # Add filters to query
        filters = []
        if request.country:
            filters.append(f"in {request.country}")
        if request.activity_type:
            filters.append(f"for {request.activity_type}")
        if request.theme:
            filters.append(f"theme {request.theme}")
        if request.target_group:
            filters.append(f"target group {request.target_group}")
        if request.experience_level:
            filters.append(f"experience level {request.experience_level}")
            
        if filters:
            enhanced_query += " " + " ".join(filters)
        
        # Run search
        result = await run_search(enhanced_query, deps)
        
        # Convert to response format
        if result.success and result.search_type == "organizations":
            return PartnerSearchResponse(
                success=True,
                query_parameters=result.query_parameters,
                total_results=result.total_results,
                organizations=result.results,
                search_timestamp=result.search_timestamp,
                error_message=result.error_message
            )
        else:
            return PartnerSearchResponse(
                success=False,
                query_parameters={"query": request.query},
                total_results=0,
                organizations=[],
                search_timestamp=result.search_timestamp,
                error_message=result.error_message or "Search returned projects instead of organizations"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/projects", response_model=ProjectSearchResponse)
async def search_projects(
    request: ProjectSearchRequest,
    deps: AgentDependencies = Depends(get_agent_deps)
):
    """
    Search for project opportunities seeking partners.
    
    This endpoint searches the SALTO-YOUTH Otlas platform for projects
    that are looking for partner organizations.
    """
    try:
        # Build enhanced query
        enhanced_query = f"Find project opportunities: {request.query}"
        
        # Add filters to query
        filters = []
        if request.project_type:
            filters.append(f"type {request.project_type}")
        if request.countries:
            filters.append(f"countries {', '.join(request.countries)}")
        if request.themes:
            filters.append(f"themes {', '.join(request.themes)}")
        if request.target_group:
            filters.append(f"target group {request.target_group}")
        if request.deadline_after:
            filters.append(f"deadline after {request.deadline_after}")
            
        if filters:
            enhanced_query += " " + " ".join(filters)
        
        # Run search
        result = await run_search(enhanced_query, deps)
        
        # Convert to response format
        if result.success and result.search_type == "projects":
            return ProjectSearchResponse(
                success=True,
                query_parameters=result.query_parameters,
                total_results=result.total_results,
                projects=result.results,
                search_timestamp=result.search_timestamp,
                error_message=result.error_message
            )
        else:
            return ProjectSearchResponse(
                success=False,
                query_parameters={"query": request.query},
                total_results=0,
                projects=[],
                search_timestamp=result.search_timestamp,
                error_message=result.error_message or "Search returned organizations instead of projects"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/smart")
async def smart_search(
    request: SmartSearchRequest,
    deps: AgentDependencies = Depends(get_agent_deps)
):
    """
    Intelligent search that automatically detects intent and returns appropriate results.
    
    This endpoint analyzes the query to determine whether the user is looking for
    partner organizations or project opportunities, then returns the appropriate results.
    """
    try:
        # Run search with automatic intent detection
        result = await run_search(request.query, deps, request.force_search_type)
        
        # Return the raw SearchResponse (which includes both types)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search/parameters")
async def get_search_parameters():
    """
    Get available search parameters and their possible values.
    
    This endpoint provides information about the available filters
    and parameters that can be used in search requests.
    """
    return {
        "countries": [
            "Germany", "France", "Spain", "Italy", "Poland", "Netherlands",
            "Belgium", "Greece", "Portugal", "Czech Republic", "Hungary", 
            "Sweden", "Austria", "Denmark", "Finland", "Ireland", "Latvia",
            "Lithuania", "Luxembourg", "Malta", "Slovakia", "Slovenia",
            "Estonia", "Croatia", "Cyprus", "Bulgaria", "Romania"
        ],
        "project_types": [
            "KA152", "KA153", "KA154", "KA210", "KA220", "KA226"
        ],
        "activity_types": [
            "Training course", "Study visit", "Seminar", "Youth exchange",
            "Cooperation project", "Strategic partnership", "Capacity building"
        ],
        "themes": [
            "Digital skills", "Environment", "Social inclusion", "Education",
            "Democracy", "Health", "Culture", "Sport", "Media literacy",
            "Entrepreneurship", "Employment", "Rural development"
        ],
        "target_groups": [
            "Young people", "Youth workers", "Teachers", "Trainers",
            "Students", "Researchers", "Social workers", "Policy makers"
        ],
        "experience_levels": [
            "Newcomer", "Experienced", "Expert"
        ]
    }


# Main server runner
def run_server(host: str = "localhost", port: int = 8000, reload: bool = False):
    """Run the MCP server."""
    uvicorn.run(
        "erasmus_partner_agent.mcp_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    from .settings import load_settings
    
    settings = load_settings()
    run_server(
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
        reload=settings.mcp_server_reload
    )