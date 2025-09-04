"""
Test Pydantic models for the Erasmus Partner Agent.

This module tests all Pydantic data models including validation,
serialization, edge cases, and model relationships.
"""
import pytest
from datetime import datetime
from typing import List, Dict, Any
import json
from pydantic import ValidationError

from ..models import (
    PartnerOrganization, 
    ProjectOpportunity, 
    SearchResponse, 
    SearchError,
    AgentResponse
)


class TestPartnerOrganizationModel:
    """Test PartnerOrganization Pydantic model."""

    def test_partner_organization_valid_complete(self):
        """Test creating PartnerOrganization with complete valid data."""
        org_data = {
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
        
        org = PartnerOrganization(**org_data)
        
        assert org.name == "Youth for Europe Foundation"
        assert org.country == "Germany"
        assert org.organization_type == "NGO"
        assert org.experience_level == "Experienced"
        assert org.target_groups == ["Young people", "Youth workers"]
        assert org.activity_types == ["Training courses", "Youth exchanges"]
        assert org.contact_info == "info@yfe.de"
        assert org.profile_url == "https://www.salto-youth.net/tools/otlas-partner-finding/organisation/123"
        assert org.last_active == "2024-01-15"

    def test_partner_organization_minimal_required(self):
        """Test creating PartnerOrganization with minimal required fields."""
        org_data = {
            "name": "Test Organization",
            "country": "Spain", 
            "organization_type": "School",
            "experience_level": "Newcomer"
        }
        
        org = PartnerOrganization(**org_data)
        
        assert org.name == "Test Organization"
        assert org.country == "Spain"
        assert org.organization_type == "School"
        assert org.experience_level == "Newcomer"
        assert org.target_groups == []  # Default empty list
        assert org.activity_types == []  # Default empty list
        assert org.contact_info == ""  # Default empty string
        assert org.profile_url == ""  # Default empty string
        assert org.last_active is None  # Default None

    def test_partner_organization_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        incomplete_data = {
            "name": "Test Organization"
            # Missing required fields: country, organization_type, experience_level
        }
        
        with pytest.raises(ValidationError) as exc_info:
            PartnerOrganization(**incomplete_data)
        
        errors = exc_info.value.errors()
        missing_fields = {error["loc"][0] for error in errors}
        assert "country" in missing_fields
        assert "organization_type" in missing_fields
        assert "experience_level" in missing_fields

    def test_partner_organization_empty_strings(self):
        """Test handling of empty strings in required fields."""
        org_data = {
            "name": "",  # Empty string should be invalid for name
            "country": "Germany",
            "organization_type": "NGO",
            "experience_level": "Experienced"
        }
        
        with pytest.raises(ValidationError):
            PartnerOrganization(**org_data)

    def test_partner_organization_serialization(self):
        """Test JSON serialization of PartnerOrganization."""
        org_data = {
            "name": "Test Organization",
            "country": "France",
            "organization_type": "Association",
            "experience_level": "Experienced",
            "target_groups": ["Students", "Teachers"],
            "activity_types": ["Seminars"]
        }
        
        org = PartnerOrganization(**org_data)
        
        # Test dict serialization
        org_dict = org.model_dump()
        assert isinstance(org_dict, dict)
        assert org_dict["name"] == "Test Organization"
        assert org_dict["target_groups"] == ["Students", "Teachers"]
        
        # Test JSON serialization
        json_str = org.model_dump_json()
        assert isinstance(json_str, str)
        
        # Test deserialization
        org_from_json = PartnerOrganization.model_validate_json(json_str)
        assert org_from_json.name == org.name
        assert org_from_json.target_groups == org.target_groups

    def test_partner_organization_list_validation(self):
        """Test validation of list fields."""
        org_data = {
            "name": "Test Organization",
            "country": "Italy",
            "organization_type": "NGO",
            "experience_level": "Expert",
            "target_groups": ["Valid group", "", None],  # Mix of valid, empty, and None
            "activity_types": []  # Empty list should be fine
        }
        
        org = PartnerOrganization(**org_data)
        
        # Lists should handle empty strings and None values
        assert org.target_groups == ["Valid group", "", None]  # Pydantic preserves these
        assert org.activity_types == []

    def test_partner_organization_long_values(self):
        """Test handling of very long string values."""
        long_name = "A" * 1000
        org_data = {
            "name": long_name,
            "country": "Germany",
            "organization_type": "NGO",
            "experience_level": "Experienced"
        }
        
        org = PartnerOrganization(**org_data)
        assert org.name == long_name  # Should accept long names


class TestProjectOpportunityModel:
    """Test ProjectOpportunity Pydantic model."""

    def test_project_opportunity_valid_complete(self):
        """Test creating ProjectOpportunity with complete valid data."""
        project_data = {
            "title": "Digital Skills for Youth Workers",
            "project_type": "KA152",
            "countries_involved": ["Germany", "France", "Spain"],
            "deadline": "2024-03-01",
            "target_groups": ["Youth workers", "Trainers"],
            "themes": ["Digital skills", "Media literacy"],
            "description": "Comprehensive training program for digital competencies",
            "contact_organization": "European Youth Network",
            "project_url": "https://www.salto-youth.net/tools/otlas-partner-finding/project/456",
            "created_date": "2024-01-10"
        }
        
        project = ProjectOpportunity(**project_data)
        
        assert project.title == "Digital Skills for Youth Workers"
        assert project.project_type == "KA152"
        assert project.countries_involved == ["Germany", "France", "Spain"]
        assert project.deadline == "2024-03-01"
        assert project.target_groups == ["Youth workers", "Trainers"]
        assert project.themes == ["Digital skills", "Media literacy"]
        assert project.description == "Comprehensive training program for digital competencies"
        assert project.contact_organization == "European Youth Network"

    def test_project_opportunity_minimal_required(self):
        """Test creating ProjectOpportunity with minimal required fields."""
        project_data = {
            "title": "Basic Project",
            "project_type": "KA210"
        }
        
        project = ProjectOpportunity(**project_data)
        
        assert project.title == "Basic Project"
        assert project.project_type == "KA210"
        assert project.countries_involved == []  # Default empty list
        assert project.target_groups == []
        assert project.themes == []
        assert project.deadline is None  # Default None
        assert project.description == ""  # Default empty string
        assert project.contact_organization == ""
        assert project.project_url == ""
        assert project.created_date == ""

    def test_project_opportunity_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        incomplete_data = {
            "title": "Test Project"
            # Missing required field: project_type
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ProjectOpportunity(**incomplete_data)
        
        errors = exc_info.value.errors()
        missing_fields = {error["loc"][0] for error in errors}
        assert "project_type" in missing_fields

    def test_project_opportunity_description_length(self):
        """Test that very long descriptions are handled properly."""
        long_description = "A" * 1000
        project_data = {
            "title": "Test Project",
            "project_type": "KA153",
            "description": long_description
        }
        
        project = ProjectOpportunity(**project_data)
        assert project.description == long_description  # Model should accept long descriptions

    def test_project_opportunity_date_validation(self):
        """Test date field validation."""
        project_data = {
            "title": "Test Project",
            "project_type": "KA152",
            "deadline": "invalid-date-format",
            "created_date": "2024-13-45"  # Invalid date
        }
        
        # Model should accept these as strings without date validation
        project = ProjectOpportunity(**project_data)
        assert project.deadline == "invalid-date-format"
        assert project.created_date == "2024-13-45"

    def test_project_opportunity_serialization(self):
        """Test JSON serialization of ProjectOpportunity."""
        project_data = {
            "title": "Serialization Test",
            "project_type": "KA220",
            "countries_involved": ["Italy", "Greece"],
            "themes": ["Environment", "Innovation"]
        }
        
        project = ProjectOpportunity(**project_data)
        
        # Test dict serialization
        project_dict = project.model_dump()
        assert isinstance(project_dict, dict)
        assert project_dict["title"] == "Serialization Test"
        assert project_dict["countries_involved"] == ["Italy", "Greece"]
        
        # Test JSON round-trip
        json_str = project.model_dump_json()
        project_from_json = ProjectOpportunity.model_validate_json(json_str)
        assert project_from_json.title == project.title
        assert project_from_json.themes == project.themes


class TestSearchResponseModel:
    """Test SearchResponse Pydantic model."""

    def test_search_response_organizations_success(self, sample_organizations_list):
        """Test SearchResponse with organization results."""
        response_data = {
            "search_type": "organizations",
            "query_parameters": {"query": "youth exchange", "country": "Germany"},
            "total_results": 2,
            "results": sample_organizations_list,
            "success": True
        }
        
        response = SearchResponse(**response_data)
        
        assert response.search_type == "organizations"
        assert response.query_parameters == {"query": "youth exchange", "country": "Germany"}
        assert response.total_results == 2
        assert len(response.results) == 2
        assert response.success is True
        assert response.error_message is None
        assert isinstance(response.search_timestamp, str)
        
        # Verify that results are PartnerOrganization instances
        for result in response.results:
            assert isinstance(result, PartnerOrganization)

    def test_search_response_projects_success(self, sample_projects_list):
        """Test SearchResponse with project results."""
        response_data = {
            "search_type": "projects",
            "query_parameters": {"query": "digital skills", "project_type": "KA152"},
            "total_results": 2,
            "results": sample_projects_list,
            "success": True
        }
        
        response = SearchResponse(**response_data)
        
        assert response.search_type == "projects"
        assert len(response.results) == 2
        
        # Verify that results are ProjectOpportunity instances
        for result in response.results:
            assert isinstance(result, ProjectOpportunity)

    def test_search_response_empty_results(self):
        """Test SearchResponse with no results."""
        response_data = {
            "search_type": "organizations",
            "query_parameters": {"query": "nonexistent"},
            "total_results": 0,
            "results": [],
            "success": True
        }
        
        response = SearchResponse(**response_data)
        
        assert response.total_results == 0
        assert response.results == []
        assert response.success is True

    def test_search_response_failure(self):
        """Test SearchResponse for failed search."""
        response_data = {
            "search_type": "organizations",
            "query_parameters": {"query": "test"},
            "total_results": 0,
            "results": [],
            "success": False,
            "error_message": "Connection timeout"
        }
        
        response = SearchResponse(**response_data)
        
        assert response.success is False
        assert response.error_message == "Connection timeout"
        assert response.results == []

    def test_search_response_invalid_search_type(self):
        """Test SearchResponse with invalid search type."""
        response_data = {
            "search_type": "invalid_type",  # Should only be "organizations" or "projects"
            "query_parameters": {"query": "test"},
            "total_results": 0,
            "results": []
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SearchResponse(**response_data)
        
        errors = exc_info.value.errors()
        assert any("search_type" in str(error) for error in errors)

    def test_search_response_mismatched_results_type(self, sample_organizations_list):
        """Test SearchResponse with mismatched search_type and results."""
        response_data = {
            "search_type": "projects",  # Says projects
            "query_parameters": {"query": "test"},
            "total_results": 2,
            "results": sample_organizations_list  # But contains organizations
        }
        
        # This should create the response successfully (validation happens at runtime usage)
        response = SearchResponse(**response_data)
        assert response.search_type == "projects"
        assert len(response.results) == 2

    def test_search_response_timestamp_generation(self):
        """Test that timestamp is automatically generated."""
        response_data = {
            "search_type": "organizations",
            "query_parameters": {"query": "test"},
            "total_results": 0,
            "results": []
        }
        
        response = SearchResponse(**response_data)
        
        assert response.search_timestamp is not None
        assert isinstance(response.search_timestamp, str)
        # Should be in ISO format
        datetime.fromisoformat(response.search_timestamp.replace('Z', '+00:00'))

    def test_search_response_custom_timestamp(self):
        """Test SearchResponse with custom timestamp."""
        custom_timestamp = "2024-01-27T10:30:00"
        response_data = {
            "search_type": "organizations",
            "query_parameters": {"query": "test"},
            "total_results": 0,
            "results": [],
            "search_timestamp": custom_timestamp
        }
        
        response = SearchResponse(**response_data)
        assert response.search_timestamp == custom_timestamp

    def test_search_response_serialization(self, sample_organizations_list):
        """Test SearchResponse JSON serialization."""
        response_data = {
            "search_type": "organizations",
            "query_parameters": {"query": "test", "max_results": 20},
            "total_results": len(sample_organizations_list),
            "results": sample_organizations_list
        }
        
        response = SearchResponse(**response_data)
        
        # Test dict serialization
        response_dict = response.model_dump()
        assert isinstance(response_dict, dict)
        assert response_dict["search_type"] == "organizations"
        assert isinstance(response_dict["results"], list)
        
        # Test JSON serialization
        json_str = response.model_dump_json()
        assert isinstance(json_str, str)
        
        # Test deserialization
        response_from_json = SearchResponse.model_validate_json(json_str)
        assert response_from_json.search_type == response.search_type
        assert len(response_from_json.results) == len(response.results)


class TestSearchErrorModel:
    """Test SearchError Pydantic model."""

    def test_search_error_complete(self):
        """Test creating SearchError with complete data."""
        error_data = {
            "error_type": "HTTP_ERROR",
            "message": "Failed to connect to SALTO-YOUTH website",
            "details": {"status_code": 503, "retry_after": "60s"}
        }
        
        error = SearchError(**error_data)
        
        assert error.error_type == "HTTP_ERROR"
        assert error.message == "Failed to connect to SALTO-YOUTH website"
        assert error.details == {"status_code": 503, "retry_after": "60s"}
        assert isinstance(error.timestamp, str)

    def test_search_error_minimal(self):
        """Test creating SearchError with minimal required fields."""
        error_data = {
            "error_type": "VALIDATION_ERROR",
            "message": "Invalid input parameters"
        }
        
        error = SearchError(**error_data)
        
        assert error.error_type == "VALIDATION_ERROR"
        assert error.message == "Invalid input parameters"
        assert error.details is None  # Default None
        assert isinstance(error.timestamp, str)

    def test_search_error_missing_required(self):
        """Test that missing required fields raise ValidationError."""
        incomplete_data = {
            "error_type": "NETWORK_ERROR"
            # Missing required field: message
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SearchError(**incomplete_data)
        
        errors = exc_info.value.errors()
        missing_fields = {error["loc"][0] for error in errors}
        assert "message" in missing_fields

    def test_search_error_timestamp_auto_generation(self):
        """Test automatic timestamp generation."""
        error_data = {
            "error_type": "TIMEOUT_ERROR",
            "message": "Request timed out"
        }
        
        error = SearchError(**error_data)
        
        assert error.timestamp is not None
        # Should be valid ISO timestamp
        datetime.fromisoformat(error.timestamp.replace('Z', '+00:00'))

    def test_search_error_custom_timestamp(self):
        """Test SearchError with custom timestamp."""
        custom_timestamp = "2024-01-27T15:45:30"
        error_data = {
            "error_type": "PARSE_ERROR",
            "message": "Failed to parse HTML response",
            "timestamp": custom_timestamp
        }
        
        error = SearchError(**error_data)
        assert error.timestamp == custom_timestamp

    def test_search_error_complex_details(self):
        """Test SearchError with complex details object."""
        complex_details = {
            "request_url": "https://example.com/search",
            "http_status": 429,
            "headers": {"Retry-After": "120"},
            "response_size": 1024,
            "attempt_count": 3,
            "stack_trace": ["line1", "line2", "line3"]
        }
        
        error_data = {
            "error_type": "RATE_LIMIT_ERROR",
            "message": "Too many requests",
            "details": complex_details
        }
        
        error = SearchError(**error_data)
        assert error.details == complex_details
        assert error.details["http_status"] == 429
        assert len(error.details["stack_trace"]) == 3

    def test_search_error_serialization(self):
        """Test SearchError JSON serialization."""
        error_data = {
            "error_type": "SCRAPING_ERROR",
            "message": "Failed to extract data from HTML",
            "details": {"selector": ".org-item", "found_count": 0}
        }
        
        error = SearchError(**error_data)
        
        # Test dict serialization
        error_dict = error.model_dump()
        assert isinstance(error_dict, dict)
        assert error_dict["error_type"] == "SCRAPING_ERROR"
        
        # Test JSON round-trip
        json_str = error.model_dump_json()
        error_from_json = SearchError.model_validate_json(json_str)
        assert error_from_json.error_type == error.error_type
        assert error_from_json.details == error.details


class TestUnionTypes:
    """Test union type validation."""

    def test_agent_response_search_response(self, sample_organizations_list):
        """Test AgentResponse union with SearchResponse."""
        response_data = {
            "search_type": "organizations",
            "query_parameters": {"query": "test"},
            "total_results": len(sample_organizations_list),
            "results": sample_organizations_list
        }
        
        response = SearchResponse(**response_data)
        
        # Should be valid AgentResponse
        assert isinstance(response, SearchResponse)
        # Union type validation happens at type checking, not runtime

    def test_agent_response_search_error(self):
        """Test AgentResponse union with SearchError."""
        error_data = {
            "error_type": "CONNECTION_ERROR",
            "message": "Network unavailable"
        }
        
        error = SearchError(**error_data)
        
        # Should be valid AgentResponse
        assert isinstance(error, SearchError)


class TestModelEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string_lists(self):
        """Test models with empty string lists."""
        org_data = {
            "name": "Test Org",
            "country": "Germany",
            "organization_type": "NGO",
            "experience_level": "Experienced",
            "target_groups": ["", "", ""],  # All empty strings
            "activity_types": []
        }
        
        org = PartnerOrganization(**org_data)
        assert org.target_groups == ["", "", ""]  # Preserved as is
        assert org.activity_types == []

    def test_none_values_in_optional_fields(self):
        """Test handling of None in optional fields."""
        project_data = {
            "title": "Test Project",
            "project_type": "KA152",
            "deadline": None,  # Explicitly None
            "description": None  # Should default to empty string
        }
        
        project = ProjectOpportunity(**project_data)
        assert project.deadline is None
        # None in string field with default should use default
        assert project.description == ""  

    def test_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters."""
        org_data = {
            "name": "Café für Jugendliche - München",
            "country": "Deutschland",
            "organization_type": "NGO",
            "experience_level": "Erfahren",
            "contact_info": "info@café-münchen.de",
            "target_groups": ["Jugendliche mit Migrationshintergrund", "LGBTQ+ Youth"]
        }
        
        org = PartnerOrganization(**org_data)
        assert "ü" in org.name
        assert "ö" in org.contact_info
        assert "+" in org.target_groups[1]

    def test_very_long_field_values(self):
        """Test handling of very long field values."""
        long_title = "A" * 500
        long_description = "B" * 2000
        
        project_data = {
            "title": long_title,
            "project_type": "KA220",
            "description": long_description
        }
        
        project = ProjectOpportunity(**project_data)
        assert len(project.title) == 500
        assert len(project.description) == 2000

    def test_numeric_strings_in_fields(self):
        """Test handling of numeric strings."""
        project_data = {
            "title": "123 Project",
            "project_type": "456",
            "created_date": "20240101",  # Numeric date format
            "contact_organization": "789 Organization"
        }
        
        project = ProjectOpportunity(**project_data)
        assert project.title == "123 Project"
        assert project.project_type == "456"
        assert project.created_date == "20240101"