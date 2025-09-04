"""
Test tool implementations for the Erasmus Partner Agent.

This module tests web scraping tools, data extraction functions, and
validation utilities used by the agent for interacting with SALTO-YOUTH Otlas.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from bs4 import BeautifulSoup
import httpx

from ..tools import (
    search_otlas_organizations,
    search_otlas_projects, 
    extract_structured_data,
    extract_text,
    extract_list,
    extract_url,
    validate_organization_data,
    validate_project_data
)
from ..models import PartnerOrganization, ProjectOpportunity
from ..dependencies import AgentDependencies


class TestWebScrapingTools:
    """Test web scraping functionality."""

    @pytest.mark.asyncio
    async def test_search_otlas_organizations_success(self, test_dependencies, mock_org_html):
        """Test successful organization search."""
        # Mock HTTP client response
        mock_response = MagicMock()
        mock_response.text = mock_org_html
        mock_response.status_code = 200
        mock_response.url = "https://test.salto-youth.net/search?searchType=organizations"
        mock_response.raise_for_status.return_value = None
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        test_dependencies._http_client = mock_client
        
        # Create a mock RunContext
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        result = await search_otlas_organizations(
            mock_ctx,
            "youth exchange",
            country="Germany",
            max_results=20
        )
        
        assert result["success"] is True
        assert result["raw_html"] == mock_org_html
        assert result["total_found"] >= 0
        assert result["error"] is None
        
        # Verify HTTP request was made correctly
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "search" in str(call_args[0][0])
        
        # Check query parameters
        params = call_args.kwargs.get("params", {})
        assert params["search"] == "youth exchange"
        assert params["searchType"] == "organizations"
        assert params["country"] == "Germany"
        assert params["limit"] == 20

    @pytest.mark.asyncio
    async def test_search_otlas_organizations_with_rate_limiting(self, test_dependencies):
        """Test that rate limiting is applied."""
        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_response.status_code = 200
        mock_response.url = "https://test.example.com"
        mock_response.raise_for_status.return_value = None
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        test_dependencies._http_client = mock_client
        test_dependencies.request_delay = 0.1  # Short delay for testing
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        start_time = asyncio.get_event_loop().time()
        
        await search_otlas_organizations(mock_ctx, "test", max_results=5)
        
        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time
        
        # Should have waited at least the delay time
        assert elapsed >= test_dependencies.request_delay

    @pytest.mark.asyncio
    async def test_search_otlas_organizations_http_error(self, test_dependencies):
        """Test handling of HTTP errors."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "404 Not Found", 
            request=MagicMock(), 
            response=MagicMock()
        )
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        result = await search_otlas_organizations(mock_ctx, "test query")
        
        assert result["success"] is False
        assert result["raw_html"] == ""
        assert result["total_found"] == 0
        assert "404" in result["error"] or "HTTPStatusError" in result["error"]

    @pytest.mark.asyncio
    async def test_search_otlas_projects_success(self, test_dependencies, mock_project_html):
        """Test successful project search."""
        mock_response = MagicMock()
        mock_response.text = mock_project_html
        mock_response.status_code = 200
        mock_response.url = "https://test.salto-youth.net/search?searchType=projects"
        mock_response.raise_for_status.return_value = None
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        result = await search_otlas_projects(
            mock_ctx,
            "digital skills",
            project_type="KA152",
            max_results=15
        )
        
        assert result["success"] is True
        assert result["raw_html"] == mock_project_html
        assert result["total_found"] >= 0
        assert result["error"] is None
        
        # Verify request parameters
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        params = call_args.kwargs.get("params", {})
        assert params["search"] == "digital skills"
        assert params["searchType"] == "projects"
        assert params["projectType"] == "KA152"
        assert params["limit"] == 15

    @pytest.mark.asyncio
    async def test_search_otlas_projects_connection_error(self, test_dependencies):
        """Test handling of connection errors."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("Connection failed")
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        result = await search_otlas_projects(mock_ctx, "test query")
        
        assert result["success"] is False
        assert "Connection failed" in result["error"] or "ConnectError" in result["error"]


class TestDataExtraction:
    """Test HTML data extraction functionality."""

    def test_extract_structured_data_organizations(self, mock_org_html):
        """Test extracting organization data from HTML."""
        result = extract_structured_data(mock_org_html, "organizations", max_items=5)
        
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["parsed_count"] == 2
        assert result["error"] is None
        
        # Check first organization data
        org1 = result["data"][0]
        assert org1["name"] == "Youth for Europe Foundation"
        assert org1["country"] == "Germany"
        assert org1["organization_type"] == "NGO"
        assert org1["experience_level"] == "Experienced"
        assert "Young people" in org1["target_groups"]
        assert "Training courses" in org1["activity_types"]
        assert org1["contact_info"] == "info@yfe.de"

    def test_extract_structured_data_projects(self, mock_project_html):
        """Test extracting project data from HTML."""
        result = extract_structured_data(mock_project_html, "projects", max_items=5)
        
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["parsed_count"] == 2
        
        # Check first project data
        project1 = result["data"][0]
        assert project1["title"] == "Digital Skills for Youth Workers"
        assert project1["project_type"] == "KA152"
        assert "Germany" in project1["countries_involved"]
        assert project1["deadline"] == "2024-03-01"
        assert "Digital skills" in project1["themes"]
        assert project1["contact_organization"] == "European Youth Network"

    def test_extract_structured_data_empty_html(self, mock_empty_html):
        """Test extraction from HTML with no results."""
        result = extract_structured_data(mock_empty_html, "organizations", max_items=10)
        
        assert result["success"] is True
        assert len(result["data"]) == 0
        assert result["parsed_count"] == 0

    def test_extract_structured_data_malformed_html(self):
        """Test extraction from malformed HTML."""
        malformed_html = "<html><body><div>Invalid structure</div></body></html>"
        
        result = extract_structured_data(malformed_html, "organizations", max_items=10)
        
        assert result["success"] is True
        assert len(result["data"]) == 0
        assert result["parsed_count"] == 0

    def test_extract_structured_data_invalid_type(self, mock_org_html):
        """Test extraction with invalid data type."""
        result = extract_structured_data(mock_org_html, "invalid_type", max_items=10)
        
        assert result["success"] is True
        assert len(result["data"]) == 0
        assert result["parsed_count"] == 0

    def test_extract_structured_data_exception_handling(self):
        """Test extraction with HTML that causes parsing errors."""
        # Completely invalid HTML that might cause BeautifulSoup issues
        invalid_html = None
        
        result = extract_structured_data(invalid_html, "organizations", max_items=10)
        
        assert result["success"] is False
        assert result["data"] == []
        assert result["parsed_count"] == 0
        assert result["error"] is not None


class TestHTMLHelperFunctions:
    """Test HTML parsing helper functions."""

    def test_extract_text_success(self):
        """Test successful text extraction."""
        html = '<div><span class="test-class">Test Content</span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        result = extract_text(soup, '.test-class')
        assert result == "Test Content"

    def test_extract_text_missing_element(self):
        """Test text extraction from missing element."""
        html = '<div><span class="other-class">Content</span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        result = extract_text(soup, '.test-class')
        assert result == ""

    def test_extract_text_empty_content(self):
        """Test text extraction from empty element."""
        html = '<div><span class="test-class"></span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        result = extract_text(soup, '.test-class')
        assert result == ""

    def test_extract_text_with_whitespace(self):
        """Test text extraction with whitespace handling."""
        html = '<div><span class="test-class">  \n  Test Content  \n  </span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        result = extract_text(soup, '.test-class')
        assert result == "Test Content"

    def test_extract_list_multiple_elements(self):
        """Test list extraction with multiple elements."""
        html = '''
        <div>
            <span class="item">Item 1</span>
            <span class="item">Item 2</span>
            <span class="item">Item 3</span>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        result = extract_list(soup, '.item')
        assert result == ["Item 1", "Item 2", "Item 3"]

    def test_extract_list_no_elements(self):
        """Test list extraction with no matching elements."""
        html = '<div><span class="other">Content</span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        result = extract_list(soup, '.item')
        assert result == []

    def test_extract_list_with_empty_elements(self):
        """Test list extraction filtering out empty elements."""
        html = '''
        <div>
            <span class="item">Item 1</span>
            <span class="item"></span>
            <span class="item">Item 2</span>
            <span class="item">   </span>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        result = extract_list(soup, '.item')
        assert result == ["Item 1", "Item 2"]

    def test_extract_url_absolute_url(self):
        """Test URL extraction with absolute URL."""
        html = '<div><a href="https://example.com/page" class="link">Link</a></div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        result = extract_url(soup, '.link')
        assert result == "https://example.com/page"

    def test_extract_url_relative_url(self):
        """Test URL extraction with relative URL conversion."""
        html = '<div><a href="/organisation/123" class="link">Link</a></div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        result = extract_url(soup, '.link')
        assert result == "https://www.salto-youth.net/organisation/123"

    def test_extract_url_missing_element(self):
        """Test URL extraction from missing element."""
        html = '<div><a href="/page" class="other">Link</a></div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        result = extract_url(soup, '.link')
        assert result == ""

    def test_extract_url_missing_href(self):
        """Test URL extraction from element without href."""
        html = '<div><a class="link">Link</a></div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        result = extract_url(soup, '.link')
        assert result == ""


class TestDataValidation:
    """Test data validation functions."""

    def test_validate_organization_data_complete(self):
        """Test organization data validation with complete data."""
        data = {
            "name": "  Youth for Europe Foundation  ",
            "country": "Germany",
            "organization_type": "NGO",
            "experience_level": "Experienced",
            "target_groups": ["Young people", "Youth workers", ""],
            "activity_types": ["Training courses", "", "Youth exchanges"],
            "contact_info": "info@yfe.de",
            "profile_url": "https://example.com/org/123",
            "last_active": "2024-01-15"
        }
        
        org = validate_organization_data(data)
        
        assert isinstance(org, PartnerOrganization)
        assert org.name == "Youth for Europe Foundation"  # Trimmed
        assert org.country == "Germany"
        assert org.target_groups == ["Young people", "Youth workers"]  # Empty strings filtered
        assert org.activity_types == ["Training courses", "Youth exchanges"]  # Empty strings filtered

    def test_validate_organization_data_minimal(self):
        """Test organization data validation with minimal data."""
        data = {
            "name": "Test Organization",
            "country": "Spain",
            "organization_type": "School",
            "experience_level": "Newcomer"
        }
        
        org = validate_organization_data(data)
        
        assert isinstance(org, PartnerOrganization)
        assert org.name == "Test Organization"
        assert org.target_groups == []
        assert org.activity_types == []
        assert org.contact_info == ""
        assert org.profile_url == ""
        assert org.last_active is None

    def test_validate_organization_data_invalid(self):
        """Test organization data validation with invalid data."""
        data = {
            "name": "",  # Empty name should cause validation error
            "country": "Germany"
        }
        
        with pytest.raises(Exception):  # Should raise validation error
            validate_organization_data(data)

    def test_validate_project_data_complete(self):
        """Test project data validation with complete data."""
        data = {
            "title": "  Digital Skills Training  ",
            "project_type": "KA152",
            "countries_involved": ["Germany", "France", ""],
            "deadline": "2024-03-01",
            "target_groups": ["Youth workers", "", "Trainers"],
            "themes": ["Digital skills", "Media literacy"],
            "description": "Comprehensive training program",
            "contact_organization": "European Network",
            "project_url": "https://example.com/project/456",
            "created_date": "2024-01-10"
        }
        
        project = validate_project_data(data)
        
        assert isinstance(project, ProjectOpportunity)
        assert project.title == "Digital Skills Training"  # Trimmed
        assert project.countries_involved == ["Germany", "France"]  # Empty strings filtered
        assert project.target_groups == ["Youth workers", "Trainers"]  # Empty strings filtered

    def test_validate_project_data_minimal(self):
        """Test project data validation with minimal data."""
        data = {
            "title": "Test Project",
            "project_type": "KA210"
        }
        
        project = validate_project_data(data)
        
        assert isinstance(project, ProjectOpportunity)
        assert project.title == "Test Project"
        assert project.countries_involved == []
        assert project.target_groups == []
        assert project.themes == []
        assert project.deadline is None

    def test_validate_project_data_long_description(self):
        """Test project data validation with long description (should be truncated in extraction)."""
        data = {
            "title": "Test Project",
            "project_type": "KA152",
            "description": "A" * 600  # Very long description
        }
        
        project = validate_project_data(data)
        
        assert isinstance(project, ProjectOpportunity)
        assert len(project.description) == 600  # Should not be truncated in validation, only in extraction


class TestRateLimitingAndConcurrency:
    """Test rate limiting and concurrent request handling."""

    @pytest.mark.asyncio
    async def test_concurrent_requests_with_rate_limiting(self, test_dependencies):
        """Test that concurrent requests respect rate limiting."""
        # Mock HTTP client for multiple requests
        responses = []
        for i in range(3):
            mock_response = MagicMock()
            mock_response.text = f"<html>Response {i}</html>"
            mock_response.status_code = 200
            mock_response.url = f"https://test.example.com/{i}"
            mock_response.raise_for_status.return_value = None
            responses.append(mock_response)
        
        mock_client = AsyncMock()
        mock_client.get.side_effect = responses
        test_dependencies._http_client = mock_client
        test_dependencies.request_delay = 0.1
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        start_time = asyncio.get_event_loop().time()
        
        # Make multiple concurrent requests
        tasks = [
            search_otlas_organizations(mock_ctx, f"query {i}", max_results=5)
            for i in range(3)
        ]
        
        results = await asyncio.gather(*tasks)
        
        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time
        
        # Should have taken at least 3 * delay time due to rate limiting
        expected_min_time = 3 * test_dependencies.request_delay
        assert elapsed >= expected_min_time
        
        # All requests should have succeeded
        assert all(result["success"] for result in results)
        assert len(results) == 3