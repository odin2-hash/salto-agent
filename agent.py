"""
Main Erasmus Partner Agent implementation.

This module defines the core Pydantic AI agent for searching partner organizations
and project opportunities on the SALTO-YOUTH Otlas platform.
"""
import re
from typing import Dict, Any, List
from pydantic_ai import Agent, RunContext
from .providers import get_llm_model
from .dependencies import AgentDependencies
from .models import SearchResponse, PartnerOrganization, ProjectOpportunity
from .prompts import (
    SYSTEM_PROMPT, 
    INTENT_DETECTION_PROMPT,
    OUTPUT_FORMAT_PROMPT,
    SEARCH_STRATEGY_PROMPT,
    ERROR_HANDLING_PROMPT
)
from . import tools


# Create the main agent
agent = Agent(
    get_llm_model(),
    deps_type=AgentDependencies,
    result_type=SearchResponse,
    system_prompt=SYSTEM_PROMPT
)


@agent.tool
async def search_organizations(
    ctx: RunContext[AgentDependencies], 
    query: str,
    country: str = None,
    activity_type: str = None,
    target_group: str = None,
    max_results: int = 20
) -> Dict[str, Any]:
    """
    Search for partner organizations on SALTO-YOUTH Otlas.
    
    Args:
        query: Search query text
        country: Filter by country (optional)
        activity_type: Filter by activity type (optional)  
        target_group: Filter by target group (optional)
        max_results: Maximum results to return
    
    Returns:
        Dictionary with search results and metadata
    """
    try:
        # Build comprehensive search query
        search_terms = [query]
        if activity_type:
            search_terms.append(activity_type)
        if target_group:
            search_terms.append(target_group)
        
        combined_query = " ".join(search_terms)
        
        # Perform the search
        search_result = await tools.search_otlas_organizations(
            ctx, combined_query, country, max_results
        )
        
        if not search_result["success"]:
            return search_result
        
        # Extract structured data
        extraction_result = tools.extract_structured_data(
            search_result["raw_html"], 
            "organizations", 
            max_results
        )
        
        # Validate and clean the data
        organizations = []
        for org_data in extraction_result.get("data", []):
            try:
                org = tools.validate_organization_data(org_data)
                organizations.append(org)
            except Exception as e:
                # Skip invalid organizations but log the issue
                continue
        
        return {
            "success": True,
            "search_type": "organizations",
            "query_parameters": {
                "query": query,
                "country": country,
                "activity_type": activity_type,
                "target_group": target_group,
                "max_results": max_results
            },
            "total_found": search_result["total_found"],
            "organizations": organizations,
            "search_url": search_result["search_url"],
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "search_type": "organizations", 
            "error": str(e),
            "organizations": []
        }


@agent.tool
async def search_projects(
    ctx: RunContext[AgentDependencies],
    query: str,
    project_type: str = None,
    theme: str = None,
    target_group: str = None,
    max_results: int = 20
) -> Dict[str, Any]:
    """
    Search for project opportunities on SALTO-YOUTH Otlas.
    
    Args:
        query: Search query text
        project_type: Filter by project type (KA152, etc.)
        theme: Filter by theme (optional)
        target_group: Filter by target group (optional)
        max_results: Maximum results to return
    
    Returns:
        Dictionary with search results and metadata
    """
    try:
        # Build comprehensive search query
        search_terms = [query]
        if theme:
            search_terms.append(theme)
        if target_group:
            search_terms.append(target_group)
            
        combined_query = " ".join(search_terms)
        
        # Perform the search
        search_result = await tools.search_otlas_projects(
            ctx, combined_query, project_type, max_results
        )
        
        if not search_result["success"]:
            return search_result
        
        # Extract structured data
        extraction_result = tools.extract_structured_data(
            search_result["raw_html"],
            "projects",
            max_results
        )
        
        # Validate and clean the data
        projects = []
        for project_data in extraction_result.get("data", []):
            try:
                project = tools.validate_project_data(project_data)
                projects.append(project)
            except Exception as e:
                # Skip invalid projects but log the issue
                continue
        
        return {
            "success": True,
            "search_type": "projects",
            "query_parameters": {
                "query": query,
                "project_type": project_type,
                "theme": theme,
                "target_group": target_group,
                "max_results": max_results
            },
            "total_found": search_result["total_found"],
            "projects": projects,
            "search_url": search_result["search_url"],
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "search_type": "projects",
            "error": str(e),
            "projects": []
        }


@agent.tool
async def analyze_search_intent(
    ctx: RunContext[AgentDependencies],
    user_query: str
) -> Dict[str, Any]:
    """
    Analyze user query to determine search intent (partners vs projects).
    
    Args:
        user_query: The user's search request
    
    Returns:
        Dictionary with intent analysis
    """
    # Convert to lowercase for analysis
    query_lower = user_query.lower()
    
    # Keywords that indicate partner search
    partner_keywords = [
        "partner", "organization", "ngo", "collaborator", "suitable",
        "who can help", "organizations in", "experience with"
    ]
    
    # Keywords that indicate project search
    project_keywords = [
        "project", "opportunity", "call", "deadline", "join", "participate",
        "ka152", "ka153", "ka210", "ka220", "looking for partners"
    ]
    
    # Count keyword matches
    partner_score = sum(1 for keyword in partner_keywords if keyword in query_lower)
    project_score = sum(1 for keyword in project_keywords if keyword in query_lower)
    
    # Determine intent
    if project_score > partner_score:
        intent = "projects"
        confidence = project_score / (project_score + partner_score + 1)
    elif partner_score > project_score:
        intent = "organizations"
        confidence = partner_score / (project_score + partner_score + 1)
    else:
        # Default to organizations for ambiguous cases
        intent = "organizations"
        confidence = 0.5
    
    return {
        "intent": intent,
        "confidence": confidence,
        "partner_score": partner_score,
        "project_score": project_score,
        "explanation": f"Detected '{intent}' search based on keyword analysis"
    }


# Main agent run function
async def run_search(
    user_query: str, 
    deps: AgentDependencies,
    force_search_type: str = None
) -> SearchResponse:
    """
    Run the agent with a user query and return structured results.
    
    Args:
        user_query: User's search request
        deps: Agent dependencies
        force_search_type: Force specific search type ("organizations" or "projects")
    
    Returns:
        SearchResponse with results
    """
    try:
        # Use the agent to process the query
        result = await agent.run(user_query, deps=deps)
        
        # The agent should return a SearchResponse
        if isinstance(result.data, SearchResponse):
            return result.data
        else:
            # If result is not properly structured, create error response
            return SearchResponse(
                search_type="organizations",
                query_parameters={"query": user_query},
                total_results=0,
                results=[],
                success=False,
                error_message="Agent returned invalid response format"
            )
    
    except Exception as e:
        # Return error response
        return SearchResponse(
            search_type="organizations",
            query_parameters={"query": user_query},
            total_results=0,
            results=[],
            success=False,
            error_message=str(e)
        )
    
    finally:
        # Cleanup resources
        await deps.cleanup()


# Helper function to extract common search parameters from natural language
def extract_search_parameters(query: str) -> Dict[str, Any]:
    """
    Extract search parameters from natural language query.
    
    Args:
        query: Natural language search query
    
    Returns:
        Dictionary with extracted parameters
    """
    params = {}
    query_lower = query.lower()
    
    # Extract country mentions
    eu_countries = [
        "germany", "france", "spain", "italy", "poland", "netherlands",
        "belgium", "greece", "portugal", "czech", "hungary", "sweden",
        "austria", "denmark", "finland", "ireland", "latvia", "lithuania",
        "luxembourg", "malta", "slovakia", "slovenia", "estonia", "croatia",
        "cyprus", "bulgaria", "romania"
    ]
    
    for country in eu_countries:
        if country in query_lower:
            params["country"] = country.title()
            break
    
    # Extract project types
    project_types = ["ka152", "ka153", "ka154", "ka210", "ka220", "ka226"]
    for pt in project_types:
        if pt in query_lower:
            params["project_type"] = pt.upper()
            break
    
    # Extract common themes
    if any(word in query_lower for word in ["digital", "technology", "tech"]):
        params["theme"] = "Digital skills"
    elif any(word in query_lower for word in ["environment", "green", "climate"]):
        params["theme"] = "Environment"
    elif any(word in query_lower for word in ["inclusion", "inclusive", "disability"]):
        params["theme"] = "Social inclusion"
    
    # Extract target groups
    if any(word in query_lower for word in ["youth worker", "trainer"]):
        params["target_group"] = "Youth workers"
    elif "young people" in query_lower:
        params["target_group"] = "Young people"
    elif "teacher" in query_lower:
        params["target_group"] = "Teachers"
    
    return params