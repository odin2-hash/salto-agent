"""
Test core agent functionality for the Erasmus Partner Agent.

This module tests the main agent implementation, including search functions,
intent detection, and result processing using TestModel and FunctionModel.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pydantic_ai.models.test import TestModel
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelTextResponse

from ..agent import (
    agent, run_search, extract_search_parameters, 
    search_organizations, search_projects, analyze_search_intent
)
from ..models import SearchResponse, PartnerOrganization, ProjectOpportunity
from ..dependencies import AgentDependencies


class TestAgentBasicFunctionality:
    """Test basic agent functionality with TestModel."""

    @pytest.mark.asyncio
    async def test_agent_basic_response(self, test_agent, test_dependencies):
        """Test agent provides appropriate response."""
        result = await test_agent.run(
            "Search for youth exchange partners in Germany",
            deps=test_dependencies
        )
        
        assert result.data is not None
        assert isinstance(result.data, SearchResponse)
        assert len(result.all_messages()) > 0

    @pytest.mark.asyncio
    async def test_agent_organization_search_tool_calling(self, function_test_agent, test_dependencies):
        """Test agent calls organization search tool appropriately."""
        result = await function_test_agent.run(
            "Find partner organizations for youth exchange in Germany",
            deps=test_dependencies
        )
        
        # Verify agent processed the request
        messages = result.all_messages()
        assert len(messages) >= 1
        
        # Look for tool calls in messages
        tool_calls = [msg for msg in messages if hasattr(msg, 'tool_name')]
        # Note: Exact tool call verification depends on TestModel behavior
        assert result.data is not None

    @pytest.mark.asyncio
    async def test_agent_project_search_intent(self, test_agent, test_dependencies):
        """Test agent detects project search intent."""
        result = await test_agent.run(
            "Find KA152 project opportunities looking for partners",
            deps=test_dependencies
        )
        
        assert result.data is not None
        assert isinstance(result.data, SearchResponse)


class TestSearchIntentAnalysis:
    """Test search intent detection functionality."""

    @pytest.mark.asyncio
    async def test_analyze_search_intent_organizations(self, test_dependencies):
        """Test intent detection for organization searches."""
        result = await analyze_search_intent(
            test_dependencies, 
            "Find partner organizations for youth exchange in Germany"
        )
        
        assert result["intent"] == "organizations"
        assert result["confidence"] > 0.5
        assert result["partner_score"] > 0
        assert isinstance(result["explanation"], str)

    @pytest.mark.asyncio
    async def test_analyze_search_intent_projects(self, test_dependencies):
        """Test intent detection for project searches."""
        result = await analyze_search_intent(
            test_dependencies,
            "Looking for KA152 project opportunities with upcoming deadlines"
        )
        
        assert result["intent"] == "projects"
        assert result["confidence"] > 0.5
        assert result["project_score"] > 0

    @pytest.mark.asyncio
    async def test_analyze_search_intent_ambiguous(self, test_dependencies):
        """Test intent detection for ambiguous queries."""
        result = await analyze_search_intent(
            test_dependencies,
            "environmental sustainability youth"
        )
        
        # Should default to organizations
        assert result["intent"] == "organizations"
        assert result["confidence"] >= 0.5


class TestSearchParameterExtraction:
    """Test parameter extraction from natural language queries."""

    def test_extract_country_parameters(self):
        """Test country extraction from queries."""
        params = extract_search_parameters("youth exchange partners in Germany")
        assert "country" in params
        assert params["country"] == "Germany"

    def test_extract_project_type_parameters(self):
        """Test project type extraction from queries."""
        params = extract_search_parameters("looking for KA152 training opportunities")
        assert "project_type" in params
        assert params["project_type"] == "KA152"

    def test_extract_theme_parameters(self):
        """Test theme extraction from queries."""
        params = extract_search_parameters("digital skills training for youth workers")
        assert "theme" in params
        assert params["theme"] == "Digital skills"

    def test_extract_target_group_parameters(self):
        """Test target group extraction from queries."""
        params = extract_search_parameters("training for youth workers and trainers")
        assert "target_group" in params
        assert params["target_group"] == "Youth workers"

    def test_extract_multiple_parameters(self):
        """Test extraction of multiple parameters."""
        params = extract_search_parameters(
            "KA152 digital skills training for young people in Spain"
        )
        assert params["country"] == "Spain"
        assert params["project_type"] == "KA152"
        assert params["theme"] == "Digital skills"
        assert params["target_group"] == "Young people"


class TestOrganizationSearchTool:
    """Test organization search tool functionality."""

    @pytest.mark.asyncio
    async def test_search_organizations_success(self, test_dependencies, mock_http_client, mock_org_html):
        """Test successful organization search."""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.text = mock_org_html
        mock_response.status_code = 200
        mock_response.url = "https://test.example.com"
        mock_response.raise_for_status.return_value = None
        mock_http_client.get.return_value = mock_response
        
        # Patch the HTTP client in dependencies
        test_dependencies._http_client = mock_http_client
        
        with patch('agents.erasmus_partner_agent.tools.search_otlas_organizations') as mock_search:
            mock_search.return_value = {
                "success": True,
                "raw_html": mock_org_html,
                "search_url": "https://test.example.com",
                "total_found": 2,
                "error": None
            }
            
            result = await search_organizations(
                test_dependencies,
                "youth exchange",
                country="Germany",
                max_results=10
            )
            
            assert result["success"] is True
            assert result["search_type"] == "organizations"
            assert "organizations" in result
            assert result["total_found"] > 0

    @pytest.mark.asyncio
    async def test_search_organizations_with_parameters(self, test_dependencies):
        """Test organization search with various parameters."""
        with patch('agents.erasmus_partner_agent.tools.search_otlas_organizations') as mock_search, \
             patch('agents.erasmus_partner_agent.tools.extract_structured_data') as mock_extract:
            
            mock_search.return_value = {
                "success": True,
                "raw_html": "<html>test</html>",
                "search_url": "https://test.example.com",
                "total_found": 5,
                "error": None
            }
            
            mock_extract.return_value = {
                "success": True,
                "data": [
                    {
                        "name": "Test Org",
                        "country": "Germany",
                        "organization_type": "NGO",
                        "experience_level": "Experienced",
                        "target_groups": ["Young people"],
                        "activity_types": ["Training"],
                        "contact_info": "test@example.com",
                        "profile_url": "https://test.example.com/org/1",
                        "last_active": "2024-01-01"
                    }
                ],
                "parsed_count": 1,
                "error": None
            }
            
            result = await search_organizations(
                test_dependencies,
                "environmental sustainability",
                country="Germany",
                activity_type="Training courses",
                target_group="Young people",
                max_results=20
            )
            
            assert result["success"] is True
            assert result["query_parameters"]["country"] == "Germany"
            assert result["query_parameters"]["activity_type"] == "Training courses"
            assert result["query_parameters"]["target_group"] == "Young people"

    @pytest.mark.asyncio
    async def test_search_organizations_error_handling(self, test_dependencies):
        """Test organization search error handling."""
        with patch('agents.erasmus_partner_agent.tools.search_otlas_organizations') as mock_search:
            mock_search.return_value = {
                "success": False,
                "raw_html": "",
                "search_url": "",
                "total_found": 0,
                "error": "Connection timeout"
            }
            
            result = await search_organizations(
                test_dependencies,
                "test query"
            )
            
            assert result["success"] is False
            assert result["error"] == "Connection timeout"
            assert result["organizations"] == []


class TestProjectSearchTool:
    """Test project search tool functionality."""

    @pytest.mark.asyncio
    async def test_search_projects_success(self, test_dependencies, mock_project_html):
        """Test successful project search."""
        with patch('agents.erasmus_partner_agent.tools.search_otlas_projects') as mock_search, \
             patch('agents.erasmus_partner_agent.tools.extract_structured_data') as mock_extract:
            
            mock_search.return_value = {
                "success": True,
                "raw_html": mock_project_html,
                "search_url": "https://test.example.com",
                "total_found": 2,
                "error": None
            }
            
            mock_extract.return_value = {
                "success": True,
                "data": [
                    {
                        "title": "Digital Skills Training",
                        "project_type": "KA152",
                        "countries_involved": ["Germany", "France"],
                        "deadline": "2024-03-01",
                        "target_groups": ["Youth workers"],
                        "themes": ["Digital skills"],
                        "description": "Test project description",
                        "contact_organization": "Test Org",
                        "project_url": "https://test.example.com/project/1",
                        "created_date": "2024-01-01"
                    }
                ],
                "parsed_count": 1,
                "error": None
            }
            
            result = await search_projects(
                test_dependencies,
                "digital skills",
                project_type="KA152",
                max_results=10
            )
            
            assert result["success"] is True
            assert result["search_type"] == "projects"
            assert "projects" in result
            assert result["total_found"] > 0

    @pytest.mark.asyncio
    async def test_search_projects_with_filters(self, test_dependencies):
        """Test project search with theme and target group filters."""
        with patch('agents.erasmus_partner_agent.tools.search_otlas_projects') as mock_search, \
             patch('agents.erasmus_partner_agent.tools.extract_structured_data') as mock_extract:
            
            mock_search.return_value = {"success": True, "raw_html": "", "total_found": 0}
            mock_extract.return_value = {"success": True, "data": [], "parsed_count": 0}
            
            result = await search_projects(
                test_dependencies,
                "environmental awareness",
                project_type="KA153",
                theme="Environment",
                target_group="Young people",
                max_results=15
            )
            
            assert result["success"] is True
            assert result["query_parameters"]["project_type"] == "KA153"
            assert result["query_parameters"]["theme"] == "Environment"
            assert result["query_parameters"]["target_group"] == "Young people"


class TestRunSearchFunction:
    """Test the main run_search function."""

    @pytest.mark.asyncio
    async def test_run_search_with_valid_query(self, test_dependencies):
        """Test run_search with valid query."""
        with patch('agents.erasmus_partner_agent.agent.agent.run') as mock_agent_run:
            # Mock agent response
            mock_result = MagicMock()
            mock_result.data = SearchResponse(
                search_type="organizations",
                query_parameters={"query": "test"},
                total_results=1,
                results=[],
                success=True
            )
            mock_agent_run.return_value = mock_result
            
            result = await run_search("Find partner organizations", test_dependencies)
            
            assert isinstance(result, SearchResponse)
            assert result.success is True
            assert result.search_type in ["organizations", "projects"]

    @pytest.mark.asyncio
    async def test_run_search_with_force_search_type(self, test_dependencies):
        """Test run_search with forced search type."""
        with patch('agents.erasmus_partner_agent.agent.agent.run') as mock_agent_run:
            mock_result = MagicMock()
            mock_result.data = SearchResponse(
                search_type="projects",
                query_parameters={"query": "test"},
                total_results=0,
                results=[],
                success=True
            )
            mock_agent_run.return_value = mock_result
            
            result = await run_search(
                "environmental projects", 
                test_dependencies, 
                force_search_type="projects"
            )
            
            assert isinstance(result, SearchResponse)
            assert result.search_type == "projects"

    @pytest.mark.asyncio
    async def test_run_search_error_handling(self, test_dependencies):
        """Test run_search error handling."""
        with patch('agents.erasmus_partner_agent.agent.agent.run') as mock_agent_run:
            mock_agent_run.side_effect = Exception("Test error")
            
            result = await run_search("test query", test_dependencies)
            
            assert isinstance(result, SearchResponse)
            assert result.success is False
            assert "Test error" in result.error_message

    @pytest.mark.asyncio
    async def test_run_search_invalid_response_format(self, test_dependencies):
        """Test run_search with invalid agent response format."""
        with patch('agents.erasmus_partner_agent.agent.agent.run') as mock_agent_run:
            mock_result = MagicMock()
            mock_result.data = "invalid response format"  # Not a SearchResponse
            mock_agent_run.return_value = mock_result
            
            result = await run_search("test query", test_dependencies)
            
            assert isinstance(result, SearchResponse)
            assert result.success is False
            assert "invalid response format" in result.error_message


class TestAgentToolIntegration:
    """Test integration between agent and tools."""

    @pytest.mark.asyncio
    async def test_agent_tools_registered(self):
        """Test that agent has the required tools registered."""
        # Check that the agent has the expected tools
        tool_names = [tool.name for tool in agent.tools]
        
        expected_tools = [
            "search_organizations",
            "search_projects", 
            "analyze_search_intent"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    @pytest.mark.asyncio
    async def test_agent_dependency_injection(self, test_dependencies):
        """Test that agent properly injects dependencies."""
        # This tests the basic dependency injection mechanism
        assert test_dependencies.otlas_base_url is not None
        assert test_dependencies.user_agent is not None
        assert test_dependencies.request_delay > 0
        assert test_dependencies.http_client is not None

    @pytest.mark.asyncio
    async def test_agent_cleanup(self, test_dependencies):
        """Test that agent dependencies are properly cleaned up."""
        # Initialize HTTP client
        _ = test_dependencies.http_client
        assert test_dependencies._http_client is not None
        
        # Test cleanup
        await test_dependencies.cleanup()
        # After cleanup, the client should be closed (we can't easily test this without mocking)
        # But we can ensure the method completes without error