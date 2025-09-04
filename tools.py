"""
Tool implementations for the Erasmus Partner Agent.

This module provides the core tools for searching and extracting data
from the SALTO-YOUTH Otlas platform.
"""
from typing import Dict, Any, Optional, List, Literal
import asyncio
import re
from bs4 import BeautifulSoup
from pydantic_ai import RunContext
from .dependencies import AgentDependencies
from .models import PartnerOrganization, ProjectOpportunity


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
    try:
        # Rate limiting - respect delay
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
        response = await ctx.deps.http_client.get(
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
        response = await ctx.deps.http_client.get(
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
                    "description": extract_text(item, '.description')[:500],  # Limit description
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
    return [elem.get_text(strip=True) for elem in elements if elem.get_text(strip=True)]


def extract_url(soup_element, selector: str) -> str:
    """Helper to extract URL from href attribute."""
    element = soup_element.select_one(selector)
    if element:
        href = element.get('href', '')
        # Convert relative URLs to absolute
        if href and not href.startswith(('http://', 'https://')):
            return f"https://www.salto-youth.net{href}"
        return href
    return ""


# Helper function to validate extracted data
def validate_organization_data(data: Dict[str, Any]) -> PartnerOrganization:
    """Validate and clean organization data before creating Pydantic model."""
    # Clean and validate fields
    cleaned_data = {
        "name": data.get("name", "").strip(),
        "country": data.get("country", "").strip(),
        "organization_type": data.get("organization_type", "").strip(),
        "experience_level": data.get("experience_level", "").strip(),
        "target_groups": [tg.strip() for tg in data.get("target_groups", []) if tg.strip()],
        "activity_types": [at.strip() for at in data.get("activity_types", []) if at.strip()],
        "contact_info": data.get("contact_info", "").strip(),
        "profile_url": data.get("profile_url", "").strip(),
        "last_active": data.get("last_active", None)
    }
    
    return PartnerOrganization(**cleaned_data)


def validate_project_data(data: Dict[str, Any]) -> ProjectOpportunity:
    """Validate and clean project data before creating Pydantic model."""
    # Clean and validate fields
    cleaned_data = {
        "title": data.get("title", "").strip(),
        "project_type": data.get("project_type", "").strip(),
        "countries_involved": [c.strip() for c in data.get("countries_involved", []) if c.strip()],
        "deadline": data.get("deadline", None),
        "target_groups": [tg.strip() for tg in data.get("target_groups", []) if tg.strip()],
        "themes": [t.strip() for t in data.get("themes", []) if t.strip()],
        "description": data.get("description", "").strip(),
        "contact_organization": data.get("contact_organization", "").strip(),
        "project_url": data.get("project_url", "").strip(),
        "created_date": data.get("created_date", "").strip()
    }
    
    return ProjectOpportunity(**cleaned_data)