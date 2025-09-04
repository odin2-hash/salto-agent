"""
Pydantic models for structured output from the Erasmus Partner Agent.

These models define the structure of data returned by the agent for
organizations, projects, and search responses.
"""
from typing import List, Optional, Union, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class PartnerOrganization(BaseModel):
    """Model for partner organizations from SALTO-YOUTH Otlas."""
    
    name: str = Field(description="Organization name")
    country: str = Field(description="Country where organization is based")
    organization_type: str = Field(description="Type of organization (NGO, School, etc.)")
    experience_level: str = Field(description="Experience level in Erasmus+ projects")
    target_groups: List[str] = Field(
        default_factory=list,
        description="Target groups the organization works with"
    )
    activity_types: List[str] = Field(
        default_factory=list,
        description="Types of activities the organization conducts"
    )
    contact_info: str = Field(
        default="",
        description="Contact information if available"
    )
    profile_url: str = Field(
        default="",
        description="URL to organization profile"
    )
    last_active: Optional[str] = Field(
        default=None,
        description="Last activity date if available"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
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
        }


class ProjectOpportunity(BaseModel):
    """Model for project opportunities from SALTO-YOUTH Otlas."""
    
    title: str = Field(description="Project title")
    project_type: str = Field(description="Erasmus+ action type (KA152, KA210, etc.)")
    countries_involved: List[str] = Field(
        default_factory=list,
        description="Countries already involved in the project"
    )
    deadline: Optional[str] = Field(
        default=None,
        description="Application deadline if available"
    )
    target_groups: List[str] = Field(
        default_factory=list,
        description="Target groups for the project"
    )
    themes: List[str] = Field(
        default_factory=list,
        description="Project themes and topics"
    )
    description: str = Field(
        default="",
        description="Project description (max 500 characters)"
    )
    contact_organization: str = Field(
        default="",
        description="Organization seeking partners"
    )
    project_url: str = Field(
        default="",
        description="URL to project details"
    )
    created_date: str = Field(
        default="",
        description="Date when project was posted"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Digital Skills for Youth Workers",
                "project_type": "KA152",
                "countries_involved": ["Germany", "France"],
                "deadline": "2024-03-01",
                "target_groups": ["Youth workers", "Trainers"],
                "themes": ["Digital skills", "Media literacy"],
                "description": "Training course focusing on digital competencies for youth work professionals",
                "contact_organization": "European Youth Network",
                "project_url": "https://www.salto-youth.net/tools/otlas-partner-finding/project/456",
                "created_date": "2024-01-10"
            }
        }


class SearchResponse(BaseModel):
    """Unified response model for all search operations."""
    
    search_type: Literal["organizations", "projects"] = Field(
        description="Type of search performed"
    )
    query_parameters: Dict[str, Any] = Field(
        description="Parameters used for the search"
    )
    total_results: int = Field(
        description="Total number of results found"
    )
    results: Union[List[PartnerOrganization], List[ProjectOpportunity]] = Field(
        description="List of search results"
    )
    search_timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When the search was performed"
    )
    success: bool = Field(
        default=True,
        description="Whether the search was successful"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if search failed"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "search_type": "organizations",
                "query_parameters": {
                    "query": "youth exchange",
                    "country": "DE",
                    "max_results": 20
                },
                "total_results": 15,
                "results": [
                    {
                        "name": "Youth for Europe Foundation",
                        "country": "Germany",
                        "organization_type": "NGO",
                        "experience_level": "Experienced"
                    }
                ],
                "search_timestamp": "2024-01-27T10:30:00",
                "success": True,
                "error_message": None
            }
        }


class SearchError(BaseModel):
    """Model for search error responses."""
    
    error_type: str = Field(description="Type of error")
    message: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When the error occurred"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_type": "HTTP_ERROR",
                "message": "Failed to connect to SALTO-YOUTH website",
                "details": {"status_code": 503, "retry_after": "60s"},
                "timestamp": "2024-01-27T10:30:00"
            }
        }


# Union type for all possible agent responses
AgentResponse = Union[SearchResponse, SearchError]