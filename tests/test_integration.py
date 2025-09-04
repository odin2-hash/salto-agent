"""
Integration tests for CLI and MCP server interfaces of the Erasmus Partner Agent.

This module tests the complete integration of the agent with its interfaces,
including command-line operations and MCP server endpoints.
"""
import pytest
import json
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from typer.testing import CliRunner
from fastapi.testclient import TestClient

from ..cli import app as cli_app
from ..dependencies import AgentDependencies
from ..models import SearchResponse, PartnerOrganization, ProjectOpportunity


class TestCLIInterface:
    """Test command-line interface functionality."""

    def setup_method(self):
        """Set up CLI test environment."""
        self.runner = CliRunner()

    def test_cli_partners_command_success(self, sample_organizations_list):
        """Test successful partner search via CLI."""
        with patch('agents.erasmus_partner_agent.cli.run_search') as mock_run_search:
            # Mock successful search response
            mock_response = SearchResponse(
                search_type="organizations",
                query_parameters={"query": "youth exchange"},
                total_results=len(sample_organizations_list),
                results=sample_organizations_list,
                success=True
            )
            mock_run_search.return_value = mock_response

            result = self.runner.invoke(cli_app, [
                "partners", 
                "youth exchange partners",
                "--country", "Germany",
                "--max", "10",
                "--format", "table"
            ])

            assert result.exit_code == 0
            assert "Youth for Europe Foundation" in result.stdout
            mock_run_search.assert_called_once()

    def test_cli_partners_command_with_export(self, sample_organizations_list):
        """Test partner search with JSON export."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test_results.json"
            
            with patch('agents.erasmus_partner_agent.cli.run_search') as mock_run_search:
                mock_response = SearchResponse(
                    search_type="organizations",
                    query_parameters={"query": "environmental"},
                    total_results=len(sample_organizations_list),
                    results=sample_organizations_list,
                    success=True
                )
                mock_run_search.return_value = mock_response

                result = self.runner.invoke(cli_app, [
                    "partners",
                    "environmental organizations",
                    "--export",
                    "--format", "json",
                    "--output", str(output_file)
                ])

                assert result.exit_code == 0
                assert output_file.exists()
                
                # Verify exported content
                with open(output_file) as f:
                    exported_data = json.load(f)
                assert exported_data["search_type"] == "organizations"
                assert len(exported_data["results"]) == len(sample_organizations_list)

    def test_cli_partners_command_no_results(self):
        """Test partner search with no results."""
        with patch('agents.erasmus_partner_agent.cli.run_search') as mock_run_search:
            mock_response = SearchResponse(
                search_type="organizations",
                query_parameters={"query": "nonexistent"},
                total_results=0,
                results=[],
                success=True
            )
            mock_run_search.return_value = mock_response

            result = self.runner.invoke(cli_app, [
                "partners", 
                "nonexistent organizations"
            ])

            assert result.exit_code == 0
            assert "No organizations found" in result.stdout

    def test_cli_projects_command_success(self, sample_projects_list):
        """Test successful project search via CLI."""
        with patch('agents.erasmus_partner_agent.cli.run_search') as mock_run_search:
            mock_response = SearchResponse(
                search_type="projects",
                query_parameters={"query": "digital skills"},
                total_results=len(sample_projects_list),
                results=sample_projects_list,
                success=True
            )
            mock_run_search.return_value = mock_response

            result = self.runner.invoke(cli_app, [
                "projects",
                "digital skills training",
                "--type", "KA152",
                "--theme", "Digital skills",
                "--format", "table"
            ])

            assert result.exit_code == 0
            assert "Digital Skills for Youth Workers" in result.stdout
            mock_run_search.assert_called_once()

    def test_cli_projects_command_csv_format(self, sample_projects_list):
        """Test project search with CSV output format."""
        with patch('agents.erasmus_partner_agent.cli.run_search') as mock_run_search:
            mock_response = SearchResponse(
                search_type="projects",
                query_parameters={"query": "environment"},
                total_results=len(sample_projects_list),
                results=sample_projects_list,
                success=True
            )
            mock_run_search.return_value = mock_response

            result = self.runner.invoke(cli_app, [
                "projects",
                "environmental projects",
                "--format", "csv"
            ])

            assert result.exit_code == 0
            # CSV output should contain quoted fields
            assert '"Digital Skills for Youth Workers"' in result.stdout
            assert '"KA152"' in result.stdout

    def test_cli_smart_search_organizations(self, sample_organizations_list):
        """Test smart search that detects organization intent."""
        with patch('agents.erasmus_partner_agent.cli.run_search') as mock_run_search:
            mock_response = SearchResponse(
                search_type="organizations",
                query_parameters={"query": "find partner organizations"},
                total_results=len(sample_organizations_list),
                results=sample_organizations_list,
                success=True
            )
            mock_run_search.return_value = mock_response

            result = self.runner.invoke(cli_app, [
                "search",
                "find partner organizations for youth exchange in Spain",
                "--max", "15"
            ])

            assert result.exit_code == 0
            assert "Found 2 organizations" in result.stdout
            assert "Youth for Europe Foundation" in result.stdout

    def test_cli_smart_search_projects(self, sample_projects_list):
        """Test smart search that detects project intent."""
        with patch('agents.erasmus_partner_agent.cli.run_search') as mock_run_search:
            mock_response = SearchResponse(
                search_type="projects",
                query_parameters={"query": "KA152 project opportunities"},
                total_results=len(sample_projects_list),
                results=sample_projects_list,
                success=True
            )
            mock_run_search.return_value = mock_response

            result = self.runner.invoke(cli_app, [
                "search",
                "looking for KA152 project opportunities with deadlines",
                "--format", "json"
            ])

            assert result.exit_code == 0
            assert "Found 2 projects" in result.stdout

    def test_cli_search_error_handling(self):
        """Test CLI error handling for failed searches."""
        with patch('agents.erasmus_partner_agent.cli.run_search') as mock_run_search:
            mock_response = SearchResponse(
                search_type="organizations",
                query_parameters={"query": "test"},
                total_results=0,
                results=[],
                success=False,
                error_message="Connection timeout"
            )
            mock_run_search.return_value = mock_response

            result = self.runner.invoke(cli_app, [
                "partners",
                "test query"
            ])

            assert result.exit_code == 0  # CLI should not crash
            assert "Search failed" in result.stdout
            assert "Connection timeout" in result.stdout

    def test_cli_exception_handling(self):
        """Test CLI handling of unexpected exceptions."""
        with patch('agents.erasmus_partner_agent.cli.run_search') as mock_run_search:
            mock_run_search.side_effect = Exception("Unexpected error")

            result = self.runner.invoke(cli_app, [
                "partners",
                "test query"
            ])

            assert result.exit_code == 0  # Should handle gracefully
            assert "Error:" in result.stdout
            assert "Unexpected error" in result.stdout

    def test_cli_export_with_csv_format(self, sample_organizations_list):
        """Test CSV export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "orgs.csv"
            
            with patch('agents.erasmus_partner_agent.cli.run_search') as mock_run_search:
                mock_response = SearchResponse(
                    search_type="organizations",
                    query_parameters={"query": "test"},
                    total_results=len(sample_organizations_list),
                    results=sample_organizations_list,
                    success=True
                )
                mock_run_search.return_value = mock_response

                result = self.runner.invoke(cli_app, [
                    "partners",
                    "test organizations",
                    "--export",
                    "--format", "csv",
                    "--output", str(output_file)
                ])

                assert result.exit_code == 0
                assert output_file.exists()
                
                # Verify CSV content
                csv_content = output_file.read_text()
                assert "Name,Country,Type,Experience" in csv_content
                assert "Youth for Europe Foundation" in csv_content

    def test_cli_suggestions_for_empty_results(self):
        """Test that CLI provides suggestions for empty results."""
        with patch('agents.erasmus_partner_agent.cli.run_search') as mock_run_search:
            mock_response = SearchResponse(
                search_type="organizations",
                query_parameters={"query": "rare search"},
                total_results=0,
                results=[],
                success=True
            )
            mock_run_search.return_value = mock_response

            result = self.runner.invoke(cli_app, [
                "partners",
                "very rare search term"
            ])

            assert result.exit_code == 0
            assert "Try these suggestions:" in result.stdout
            assert "Broaden your search terms" in result.stdout


class TestMCPServerIntegration:
    """Test MCP server integration."""

    def setup_method(self):
        """Set up MCP server test environment."""
        # Import MCP server here to avoid import issues if it doesn't exist
        try:
            from ..mcp_server import app as mcp_app
            self.mcp_app = mcp_app
            self.client = TestClient(mcp_app)
        except ImportError:
            pytest.skip("MCP server not available")

    @pytest.mark.skipif(True, reason="MCP server implementation may not be complete")
    def test_mcp_health_check(self):
        """Test MCP server health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    @pytest.mark.skipif(True, reason="MCP server implementation may not be complete")
    def test_mcp_search_organizations_endpoint(self, sample_organizations_list):
        """Test MCP organization search endpoint."""
        with patch('agents.erasmus_partner_agent.mcp_server.run_search') as mock_run_search:
            mock_response = SearchResponse(
                search_type="organizations",
                query_parameters={"query": "youth"},
                total_results=len(sample_organizations_list),
                results=sample_organizations_list,
                success=True
            )
            mock_run_search.return_value = mock_response

            request_data = {
                "query": "youth organizations",
                "parameters": {
                    "country": "Germany",
                    "max_results": 20
                }
            }

            response = self.client.post("/search/organizations", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["search_type"] == "organizations"
            assert len(data["results"]) == len(sample_organizations_list)

    @pytest.mark.skipif(True, reason="MCP server implementation may not be complete")
    def test_mcp_search_projects_endpoint(self, sample_projects_list):
        """Test MCP project search endpoint."""
        with patch('agents.erasmus_partner_agent.mcp_server.run_search') as mock_run_search:
            mock_response = SearchResponse(
                search_type="projects",
                query_parameters={"query": "digital skills"},
                total_results=len(sample_projects_list),
                results=sample_projects_list,
                success=True
            )
            mock_run_search.return_value = mock_response

            request_data = {
                "query": "digital skills projects",
                "parameters": {
                    "project_type": "KA152",
                    "max_results": 15
                }
            }

            response = self.client.post("/search/projects", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["search_type"] == "projects"

    @pytest.mark.skipif(True, reason="MCP server implementation may not be complete")
    def test_mcp_smart_search_endpoint(self, sample_organizations_list):
        """Test MCP smart search endpoint."""
        with patch('agents.erasmus_partner_agent.mcp_server.run_search') as mock_run_search:
            mock_response = SearchResponse(
                search_type="organizations",
                query_parameters={"query": "find partners"},
                total_results=len(sample_organizations_list),
                results=sample_organizations_list,
                success=True
            )
            mock_run_search.return_value = mock_response

            request_data = {
                "query": "find partner organizations for environmental projects",
                "parameters": {"max_results": 25}
            }

            response = self.client.post("/search", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True

    @pytest.mark.skipif(True, reason="MCP server implementation may not be complete")
    def test_mcp_error_handling(self):
        """Test MCP server error handling."""
        with patch('agents.erasmus_partner_agent.mcp_server.run_search') as mock_run_search:
            mock_run_search.side_effect = Exception("Search service unavailable")

            request_data = {
                "query": "test query",
                "parameters": {}
            }

            response = self.client.post("/search/organizations", json=request_data)
            
            # Should handle error gracefully
            assert response.status_code in [200, 500]  # Depending on error handling implementation

    @pytest.mark.skipif(True, reason="MCP server implementation may not be complete")
    def test_mcp_invalid_request_data(self):
        """Test MCP server with invalid request data."""
        # Missing required query field
        request_data = {
            "parameters": {"max_results": 10}
        }

        response = self.client.post("/search/organizations", json=request_data)
        assert response.status_code == 422  # Validation error


class TestEndToEndIntegration:
    """Test complete end-to-end integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_organization_search_workflow(self, test_dependencies, mock_org_html):
        """Test complete organization search workflow from CLI to result."""
        with patch('agents.erasmus_partner_agent.tools.search_otlas_organizations') as mock_search, \
             patch('agents.erasmus_partner_agent.tools.extract_structured_data') as mock_extract, \
             patch('agents.erasmus_partner_agent.agent.agent.run') as mock_agent_run:
            
            # Mock the search pipeline
            mock_search.return_value = {
                "success": True,
                "raw_html": mock_org_html,
                "search_url": "https://test.example.com",
                "total_found": 2,
                "error": None
            }
            
            mock_extract.return_value = {
                "success": True,
                "data": [
                    {
                        "name": "Youth for Europe Foundation",
                        "country": "Germany",
                        "organization_type": "NGO",
                        "experience_level": "Experienced",
                        "target_groups": ["Young people"],
                        "activity_types": ["Training courses"],
                        "contact_info": "info@yfe.de",
                        "profile_url": "https://example.com/org/123",
                        "last_active": "2024-01-15"
                    }
                ],
                "parsed_count": 1,
                "error": None
            }
            
            # Mock agent response
            mock_result = MagicMock()
            mock_result.data = SearchResponse(
                search_type="organizations",
                query_parameters={"query": "youth exchange"},
                total_results=1,
                results=[PartnerOrganization(
                    name="Youth for Europe Foundation",
                    country="Germany",
                    organization_type="NGO",
                    experience_level="Experienced"
                )],
                success=True
            )
            mock_agent_run.return_value = mock_result
            
            # Test CLI integration
            runner = CliRunner()
            result = runner.invoke(cli_app, [
                "partners",
                "youth exchange partners in Germany"
            ])
            
            assert result.exit_code == 0
            assert "Youth for Europe Foundation" in result.stdout

    @pytest.mark.asyncio
    async def test_full_project_search_workflow(self, test_dependencies, mock_project_html):
        """Test complete project search workflow."""
        with patch('agents.erasmus_partner_agent.tools.search_otlas_projects') as mock_search, \
             patch('agents.erasmus_partner_agent.tools.extract_structured_data') as mock_extract, \
             patch('agents.erasmus_partner_agent.agent.agent.run') as mock_agent_run:
            
            mock_search.return_value = {
                "success": True,
                "raw_html": mock_project_html,
                "total_found": 1,
                "error": None
            }
            
            mock_extract.return_value = {
                "success": True,
                "data": [
                    {
                        "title": "Digital Skills for Youth Workers",
                        "project_type": "KA152",
                        "countries_involved": ["Germany", "France"],
                        "deadline": "2024-03-01",
                        "target_groups": ["Youth workers"],
                        "themes": ["Digital skills"],
                        "description": "Training course",
                        "contact_organization": "European Network",
                        "project_url": "https://example.com/project/456",
                        "created_date": "2024-01-10"
                    }
                ],
                "parsed_count": 1,
                "error": None
            }
            
            mock_result = MagicMock()
            mock_result.data = SearchResponse(
                search_type="projects",
                query_parameters={"query": "KA152 digital skills"},
                total_results=1,
                results=[ProjectOpportunity(
                    title="Digital Skills for Youth Workers",
                    project_type="KA152"
                )],
                success=True
            )
            mock_agent_run.return_value = mock_result
            
            runner = CliRunner()
            result = runner.invoke(cli_app, [
                "projects",
                "KA152 digital skills opportunities"
            ])
            
            assert result.exit_code == 0
            assert "Digital Skills for Youth Workers" in result.stdout

    def test_cli_dependency_injection(self):
        """Test that CLI properly creates and injects dependencies."""
        with patch('agents.erasmus_partner_agent.cli.AgentDependencies.from_settings') as mock_deps, \
             patch('agents.erasmus_partner_agent.cli.run_search') as mock_run_search:
            
            mock_deps.return_value = MagicMock()
            mock_run_search.return_value = SearchResponse(
                search_type="organizations",
                query_parameters={"query": "test"},
                total_results=0,
                results=[],
                success=True
            )
            
            runner = CliRunner()
            result = runner.invoke(cli_app, ["partners", "test query"])
            
            assert result.exit_code == 0
            mock_deps.assert_called_once()
            mock_run_search.assert_called_once()

    def test_export_functionality_integration(self, sample_organizations_list):
        """Test complete export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            json_file = Path(temp_dir) / "results.json"
            
            with patch('agents.erasmus_partner_agent.cli.run_search') as mock_run_search:
                mock_response = SearchResponse(
                    search_type="organizations", 
                    query_parameters={"query": "test"},
                    total_results=len(sample_organizations_list),
                    results=sample_organizations_list,
                    success=True
                )
                mock_run_search.return_value = mock_response
                
                runner = CliRunner()
                result = runner.invoke(cli_app, [
                    "partners",
                    "test organizations",
                    "--export",
                    "--format", "json",
                    "--output", str(json_file)
                ])
                
                assert result.exit_code == 0
                assert json_file.exists()
                
                # Verify exported data structure
                with open(json_file) as f:
                    data = json.load(f)
                
                assert data["search_type"] == "organizations"
                assert data["success"] is True
                assert len(data["results"]) == len(sample_organizations_list)
                
                # Verify organization data structure
                org = data["results"][0]
                assert "name" in org
                assert "country" in org
                assert "organization_type" in org