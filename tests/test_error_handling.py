"""
Test error handling and edge cases for the Erasmus Partner Agent.

This module tests various failure scenarios, error recovery mechanisms,
and boundary conditions to ensure robust agent behavior.
"""
import pytest
import asyncio
import httpx
from unittest.mock import patch, MagicMock, AsyncMock
from pydantic import ValidationError

from ..agent import run_search, search_organizations, search_projects, analyze_search_intent
from ..tools import (
    search_otlas_organizations, 
    search_otlas_projects,
    extract_structured_data,
    validate_organization_data,
    validate_project_data
)
from ..models import SearchResponse, PartnerOrganization, ProjectOpportunity
from ..dependencies import AgentDependencies
from ..settings import load_settings


class TestNetworkErrorHandling:
    """Test handling of network-related errors."""

    @pytest.mark.asyncio
    async def test_connection_timeout_error(self, test_dependencies):
        """Test handling of connection timeout errors."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("Connection timed out")
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        result = await search_otlas_organizations(mock_ctx, "test query")
        
        assert result["success"] is False
        assert "timed out" in result["error"].lower() or "timeout" in result["error"].lower()
        assert result["raw_html"] == ""
        assert result["total_found"] == 0

    @pytest.mark.asyncio
    async def test_connection_refused_error(self, test_dependencies):
        """Test handling of connection refused errors."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        result = await search_otlas_projects(mock_ctx, "test query")
        
        assert result["success"] is False
        assert "refused" in result["error"].lower() or "connect" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_dns_resolution_error(self, test_dependencies):
        """Test handling of DNS resolution errors."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("Name resolution failed")
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        result = await search_otlas_organizations(mock_ctx, "test query")
        
        assert result["success"] is False
        assert result["error"] is not None

    @pytest.mark.asyncio
    async def test_ssl_certificate_error(self, test_dependencies):
        """Test handling of SSL certificate errors."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("SSL certificate verification failed")
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        result = await search_otlas_projects(mock_ctx, "test query")
        
        assert result["success"] is False
        assert "ssl" in result["error"].lower() or "certificate" in result["error"].lower()


class TestHTTPErrorHandling:
    """Test handling of HTTP status errors."""

    @pytest.mark.asyncio
    async def test_404_not_found_error(self, test_dependencies):
        """Test handling of 404 Not Found errors."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", 
            request=MagicMock(), 
            response=mock_response
        )
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        result = await search_otlas_organizations(mock_ctx, "test query")
        
        assert result["success"] is False
        assert "404" in result["error"] or "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_500_server_error(self, test_dependencies):
        """Test handling of 500 Internal Server Error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error", 
            request=MagicMock(), 
            response=mock_response
        )
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        result = await search_otlas_projects(mock_ctx, "test query")
        
        assert result["success"] is False
        assert "500" in result["error"] or "server error" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_429_rate_limit_error(self, test_dependencies):
        """Test handling of 429 Too Many Requests."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429 Too Many Requests", 
            request=MagicMock(), 
            response=mock_response
        )
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        result = await search_otlas_organizations(mock_ctx, "test query")
        
        assert result["success"] is False
        assert ("429" in result["error"] or 
                "rate limit" in result["error"].lower() or 
                "too many requests" in result["error"].lower())

    @pytest.mark.asyncio
    async def test_403_forbidden_error(self, test_dependencies):
        """Test handling of 403 Forbidden errors."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "403 Forbidden", 
            request=MagicMock(), 
            response=mock_response
        )
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        result = await search_otlas_projects(mock_ctx, "test query")
        
        assert result["success"] is False
        assert "403" in result["error"] or "forbidden" in result["error"].lower()


class TestDataParsingErrors:
    """Test handling of data parsing and validation errors."""

    def test_malformed_html_parsing(self):
        """Test extraction from severely malformed HTML."""
        malformed_html = "<html><body><div class='incomplete"
        
        result = extract_structured_data(malformed_html, "organizations", max_items=10)
        
        # Should handle gracefully, not crash
        assert result["success"] is True  # BeautifulSoup is very forgiving
        assert result["data"] == []
        assert result["parsed_count"] == 0

    def test_empty_html_response(self):
        """Test handling of empty HTML response."""
        result = extract_structured_data("", "organizations", max_items=10)
        
        assert result["success"] is True
        assert result["data"] == []
        assert result["parsed_count"] == 0

    def test_none_html_response(self):
        """Test handling of None HTML response."""
        result = extract_structured_data(None, "organizations", max_items=10)
        
        assert result["success"] is False
        assert result["data"] == []
        assert result["error"] is not None

    def test_html_with_no_matching_selectors(self):
        """Test HTML that doesn't contain expected CSS selectors."""
        html_without_expected_classes = '''
        <html>
            <body>
                <div class="unexpected-class">
                    <span>Some content</span>
                </div>
            </body>
        </html>
        '''
        
        result = extract_structured_data(html_without_expected_classes, "organizations", max_items=10)
        
        assert result["success"] is True
        assert result["data"] == []
        assert result["parsed_count"] == 0

    def test_html_with_partial_data(self):
        """Test HTML with incomplete organization/project data."""
        partial_html = '''
        <html>
            <body>
                <div class="org-item">
                    <div class="org-name">Incomplete Organization</div>
                    <!-- Missing other required fields -->
                </div>
            </body>
        </html>
        '''
        
        result = extract_structured_data(partial_html, "organizations", max_items=10)
        
        assert result["success"] is True
        assert len(result["data"]) == 1
        org_data = result["data"][0]
        assert org_data["name"] == "Incomplete Organization"
        # Other fields should be empty strings or empty lists
        assert org_data["country"] == ""
        assert org_data["target_groups"] == []


class TestDataValidationErrors:
    """Test Pydantic model validation error handling."""

    def test_organization_validation_with_missing_required_fields(self):
        """Test organization validation with missing required fields."""
        incomplete_data = {
            "name": "Test Organization"
            # Missing required fields: country, organization_type, experience_level
        }
        
        with pytest.raises((ValidationError, ValueError)):
            validate_organization_data(incomplete_data)

    def test_organization_validation_with_empty_required_fields(self):
        """Test organization validation with empty required fields."""
        data_with_empty_fields = {
            "name": "",  # Empty required field
            "country": "Germany",
            "organization_type": "NGO",
            "experience_level": "Experienced"
        }
        
        with pytest.raises((ValidationError, ValueError)):
            validate_organization_data(data_with_empty_fields)

    def test_project_validation_with_missing_required_fields(self):
        """Test project validation with missing required fields."""
        incomplete_data = {
            "title": "Test Project"
            # Missing required field: project_type
        }
        
        with pytest.raises((ValidationError, ValueError)):
            validate_project_data(incomplete_data)

    def test_validation_with_invalid_data_types(self):
        """Test validation with invalid data types."""
        invalid_data = {
            "name": 123,  # Should be string
            "country": ["Germany"],  # Should be string, not list
            "organization_type": None,  # Required field as None
            "experience_level": "Experienced",
            "target_groups": "Not a list"  # Should be list
        }
        
        with pytest.raises((ValidationError, ValueError, TypeError)):
            validate_organization_data(invalid_data)


class TestAgentErrorRecovery:
    """Test agent's error recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_agent_graceful_degradation_on_tool_failure(self, test_dependencies):
        """Test that agent handles tool failures gracefully."""
        with patch('agents.erasmus_partner_agent.agent.search_organizations') as mock_search:
            # Mock tool failure
            mock_search.side_effect = Exception("Tool execution failed")
            
            result = await run_search("find partner organizations", test_dependencies)
            
            assert isinstance(result, SearchResponse)
            assert result.success is False
            assert "Tool execution failed" in result.error_message

    @pytest.mark.asyncio
    async def test_agent_partial_tool_success_handling(self, test_dependencies):
        """Test handling when some tools succeed but others fail."""
        with patch('agents.erasmus_partner_agent.tools.search_otlas_organizations') as mock_search, \
             patch('agents.erasmus_partner_agent.tools.extract_structured_data') as mock_extract:
            
            # Search succeeds but extraction fails
            mock_search.return_value = {
                "success": True,
                "raw_html": "<html>test</html>",
                "total_found": 1,
                "error": None
            }
            
            mock_extract.side_effect = Exception("Extraction failed")
            
            # Test through the search_organizations tool
            from pydantic_ai import RunContext
            mock_ctx = MagicMock(spec=RunContext)
            mock_ctx.deps = test_dependencies
            
            result = await search_organizations(
                mock_ctx, "test query"
            )
            
            assert result["success"] is False
            assert "Extraction failed" in result.get("error", "")

    @pytest.mark.asyncio
    async def test_agent_empty_results_handling(self, test_dependencies):
        """Test agent behavior with empty search results."""
        with patch('agents.erasmus_partner_agent.tools.search_otlas_organizations') as mock_search, \
             patch('agents.erasmus_partner_agent.tools.extract_structured_data') as mock_extract:
            
            mock_search.return_value = {
                "success": True,
                "raw_html": "<html></html>",
                "total_found": 0,
                "error": None
            }
            
            mock_extract.return_value = {
                "success": True,
                "data": [],
                "parsed_count": 0,
                "error": None
            }
            
            mock_ctx = MagicMock()
            mock_ctx.deps = test_dependencies
            
            result = await search_organizations(mock_ctx, "nonexistent query")
            
            assert result["success"] is True
            assert result["organizations"] == []
            assert result["total_found"] == 0


class TestConcurrencyErrorHandling:
    """Test error handling in concurrent scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_requests_with_mixed_success(self, test_dependencies):
        """Test handling of mixed success/failure in concurrent requests."""
        # Mock responses: some succeed, some fail
        responses = [
            # Success
            MagicMock(text="<html>success 1</html>", status_code=200, url="http://test1.com"),
            # Failure
            None,  # Will cause get() to raise exception
            # Success  
            MagicMock(text="<html>success 2</html>", status_code=200, url="http://test2.com")
        ]
        
        call_count = 0
        async def mock_get(*args, **kwargs):
            nonlocal call_count
            if call_count == 1:  # Second call fails
                raise httpx.ConnectError("Connection failed")
            response = responses[call_count]
            call_count += 1
            response.raise_for_status = MagicMock()
            return response
        
        mock_client = AsyncMock()
        mock_client.get = mock_get
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        # Run multiple concurrent searches
        tasks = [
            search_otlas_organizations(mock_ctx, f"query {i}", max_results=5)
            for i in range(3)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should have 2 successes and 1 failure
        successes = [r for r in results if isinstance(r, dict) and r.get("success")]
        failures = [r for r in results if isinstance(r, dict) and not r.get("success")]
        
        assert len(successes) == 2
        assert len(failures) == 1

    @pytest.mark.asyncio
    async def test_rate_limiting_with_backoff(self, test_dependencies):
        """Test rate limiting behavior under heavy load."""
        # Set very short delay for testing
        test_dependencies.request_delay = 0.05
        
        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_response.status_code = 200
        mock_response.url = "http://test.com"
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        start_time = asyncio.get_event_loop().time()
        
        # Multiple concurrent requests
        tasks = [
            search_otlas_organizations(mock_ctx, f"query {i}", max_results=1)
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time
        
        # Should have taken at least 5 * delay due to rate limiting
        expected_min_time = 5 * test_dependencies.request_delay
        assert elapsed >= expected_min_time
        
        # All requests should succeed
        assert all(r["success"] for r in results)


class TestResourceManagementErrors:
    """Test resource management and cleanup error handling."""

    @pytest.mark.asyncio
    async def test_http_client_cleanup_on_error(self, test_dependencies):
        """Test that HTTP client is properly cleaned up even on errors."""
        # Initialize the HTTP client
        client = test_dependencies.http_client
        assert test_dependencies._http_client is not None
        
        # Simulate an error during cleanup
        with patch.object(client, 'aclose', side_effect=Exception("Cleanup failed")):
            # Should not raise exception, just handle gracefully
            try:
                await test_dependencies.cleanup()
            except Exception as e:
                pytest.fail(f"Cleanup should handle errors gracefully, but got: {e}")

    def test_dependency_creation_with_invalid_settings(self):
        """Test dependency creation with invalid settings."""
        with patch('agents.erasmus_partner_agent.settings.load_settings') as mock_settings:
            mock_settings.side_effect = ValueError("Invalid API key")
            
            with pytest.raises(ValueError):
                AgentDependencies.from_settings()

    def test_settings_loading_with_missing_env_file(self):
        """Test settings loading when .env file is missing."""
        with patch('agents.erasmus_partner_agent.settings.load_dotenv') as mock_load_dotenv:
            mock_load_dotenv.return_value = False  # .env file not found
            
            # Should still work with environment variables or defaults
            try:
                settings = load_settings()
                # This might fail if LLM_API_KEY is not set in environment
            except ValueError as e:
                # Expected if no API key is available
                assert "llm_api_key" in str(e).lower()


class TestInputValidationErrors:
    """Test handling of invalid input parameters."""

    @pytest.mark.asyncio
    async def test_search_with_extremely_long_query(self, test_dependencies):
        """Test handling of extremely long search queries."""
        very_long_query = "A" * 10000  # 10KB query string
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        with patch('agents.erasmus_partner_agent.tools.search_otlas_organizations') as mock_search:
            mock_search.return_value = {
                "success": True,
                "raw_html": "<html></html>",
                "total_found": 0,
                "error": None
            }
            
            # Should handle long queries without crashing
            result = await search_organizations(mock_ctx, very_long_query)
            
            assert result["success"] is True
            mock_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_special_characters(self, test_dependencies):
        """Test handling of queries with special characters."""
        special_queries = [
            "query with & symbols",
            "query with %20 encoding",
            "query with <script>alert('xss')</script>",
            "query with üñíçødé characters",
            "query with 中文字符",
            "query\nwith\nnewlines",
            "query\twith\ttabs"
        ]
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        with patch('agents.erasmus_partner_agent.tools.search_otlas_organizations') as mock_search:
            mock_search.return_value = {
                "success": True,
                "raw_html": "<html></html>",
                "total_found": 0,
                "error": None
            }
            
            for query in special_queries:
                result = await search_organizations(mock_ctx, query)
                assert result["success"] is True, f"Failed for query: {query}"

    @pytest.mark.asyncio
    async def test_search_with_invalid_parameters(self, test_dependencies):
        """Test handling of invalid search parameters."""
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        with patch('agents.erasmus_partner_agent.tools.search_otlas_organizations') as mock_search:
            mock_search.return_value = {
                "success": True,
                "raw_html": "<html></html>",
                "total_found": 0,
                "error": None
            }
            
            # Test with negative max_results
            result = await search_organizations(
                mock_ctx, "test", max_results=-5
            )
            
            # Should handle gracefully (implementation might clamp to minimum)
            assert isinstance(result, dict)
            assert "success" in result

    def test_intent_analysis_with_empty_query(self):
        """Test intent analysis with empty or None query."""
        # Empty string
        result = asyncio.run(analyze_search_intent(MagicMock(), ""))
        assert result["intent"] in ["organizations", "projects"]
        assert result["confidence"] >= 0
        
        # Whitespace only
        result = asyncio.run(analyze_search_intent(MagicMock(), "   \n\t   "))
        assert result["intent"] in ["organizations", "projects"]

    def test_parameter_extraction_edge_cases(self):
        """Test parameter extraction with edge cases."""
        from ..agent import extract_search_parameters
        
        # Empty query
        params = extract_search_parameters("")
        assert isinstance(params, dict)
        
        # None query (should not crash)
        try:
            params = extract_search_parameters(None)
        except (TypeError, AttributeError):
            # Expected for None input
            pass
        
        # Query with only special characters
        params = extract_search_parameters("!@#$%^&*()")
        assert isinstance(params, dict)
        
        # Very long country names that don't match
        params = extract_search_parameters("organizations in nonexistentcountryname")
        assert "country" not in params


class TestMemoryAndResourceLimits:
    """Test behavior under resource constraints."""

    @pytest.mark.asyncio
    async def test_large_html_response_handling(self, test_dependencies):
        """Test handling of very large HTML responses."""
        # Create a large HTML response (1MB)
        large_html = "<html><body>" + "A" * (1024 * 1024) + "</body></html>"
        
        mock_response = MagicMock()
        mock_response.text = large_html
        mock_response.status_code = 200
        mock_response.url = "http://test.com"
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        # Should handle large responses without crashing
        result = await search_otlas_organizations(mock_ctx, "test query")
        
        assert result["success"] is True
        assert len(result["raw_html"]) > 1000000  # Confirms large response was handled

    def test_extraction_with_many_items(self):
        """Test data extraction with many items (stress test)."""
        # Create HTML with many organization items
        org_items = []
        for i in range(1000):
            org_items.append(f'''
            <div class="org-item">
                <div class="org-name">Organization {i}</div>
                <div class="org-country">Country {i % 27}</div>
                <div class="org-type">NGO</div>
                <div class="exp-level">Experienced</div>
            </div>
            ''')
        
        large_html = f"<html><body>{''.join(org_items)}</body></html>"
        
        # Should handle many items efficiently
        result = extract_structured_data(large_html, "organizations", max_items=100)
        
        assert result["success"] is True
        assert len(result["data"]) == 100  # Should respect max_items limit
        assert result["parsed_count"] == 100