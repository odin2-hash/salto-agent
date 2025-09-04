"""
Performance and rate limiting tests for the Erasmus Partner Agent.

This module tests performance characteristics, rate limiting behavior,
concurrent request handling, and resource usage patterns.
"""
import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock, AsyncMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

from ..agent import run_search, search_organizations, search_projects
from ..tools import search_otlas_organizations, search_otlas_projects, extract_structured_data
from ..dependencies import AgentDependencies
from ..models import SearchResponse, PartnerOrganization, ProjectOpportunity


class TestPerformanceBenchmarks:
    """Test performance benchmarks for key operations."""

    @pytest.mark.asyncio
    async def test_single_search_response_time(self, test_dependencies, performance_timer, mock_org_html):
        """Test response time for a single search operation."""
        with patch('agents.erasmus_partner_agent.tools.search_otlas_organizations') as mock_search, \
             patch('agents.erasmus_partner_agent.tools.extract_structured_data') as mock_extract:
            
            # Mock fast responses
            mock_search.return_value = {
                "success": True,
                "raw_html": mock_org_html,
                "total_found": 2,
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
                        "profile_url": "https://test.com/org/1",
                        "last_active": "2024-01-01"
                    }
                ],
                "parsed_count": 1,
                "error": None
            }
            
            mock_ctx = MagicMock()
            mock_ctx.deps = test_dependencies
            
            performance_timer.start()
            result = await search_organizations(mock_ctx, "youth exchange")
            performance_timer.stop()
            
            assert result["success"] is True
            # Should complete within reasonable time (without network delay)
            assert performance_timer.elapsed < 1.0, f"Search took {performance_timer.elapsed}s, expected < 1.0s"

    @pytest.mark.asyncio
    async def test_data_extraction_performance(self, performance_timer):
        """Test performance of HTML data extraction."""
        # Generate HTML with many items for performance testing
        org_items = []
        for i in range(100):
            org_items.append(f'''
            <div class="org-item">
                <div class="org-name">Organization {i}</div>
                <div class="org-country">Country{i % 27}</div>
                <div class="org-type">NGO</div>
                <div class="exp-level">Experienced</div>
                <div class="target-group">Young people</div>
                <div class="target-group">Youth workers</div>
                <div class="activity-type">Training courses</div>
                <div class="contact-info">org{i}@example.com</div>
                <a href="/org/{i}" class="org-link">Profile</a>
                <div class="last-active">2024-01-0{(i % 9) + 1}</div>
            </div>
            ''')
        
        large_html = f"<html><body>{''.join(org_items)}</body></html>"
        
        performance_timer.start()
        result = extract_structured_data(large_html, "organizations", max_items=100)
        performance_timer.stop()
        
        assert result["success"] is True
        assert result["parsed_count"] == 100
        # Extraction should be reasonably fast
        assert performance_timer.elapsed < 2.0, f"Extraction took {performance_timer.elapsed}s, expected < 2.0s"

    @pytest.mark.asyncio
    async def test_model_validation_performance(self, performance_timer):
        """Test performance of Pydantic model validation."""
        # Test data for 100 organizations
        org_data_list = [
            {
                "name": f"Organization {i}",
                "country": f"Country{i % 27}",
                "organization_type": "NGO",
                "experience_level": "Experienced",
                "target_groups": ["Young people", "Youth workers"],
                "activity_types": ["Training courses"],
                "contact_info": f"org{i}@example.com",
                "profile_url": f"https://example.com/org/{i}",
                "last_active": "2024-01-01"
            }
            for i in range(100)
        ]
        
        performance_timer.start()
        
        organizations = []
        for org_data in org_data_list:
            org = PartnerOrganization(**org_data)
            organizations.append(org)
        
        performance_timer.stop()
        
        assert len(organizations) == 100
        # Model validation should be fast
        assert performance_timer.elapsed < 1.0, f"Validation took {performance_timer.elapsed}s, expected < 1.0s"

    @pytest.mark.asyncio
    async def test_search_response_serialization_performance(self, sample_organizations_list, performance_timer):
        """Test performance of SearchResponse serialization."""
        # Create a large response
        large_results = sample_organizations_list * 50  # 100 organizations
        
        response = SearchResponse(
            search_type="organizations",
            query_parameters={"query": "performance test"},
            total_results=len(large_results),
            results=large_results,
            success=True
        )
        
        performance_timer.start()
        
        # Test JSON serialization
        json_str = response.model_dump_json()
        
        # Test deserialization
        response_copy = SearchResponse.model_validate_json(json_str)
        
        performance_timer.stop()
        
        assert len(response_copy.results) == len(large_results)
        # Serialization should be reasonable fast
        assert performance_timer.elapsed < 2.0, f"Serialization took {performance_timer.elapsed}s, expected < 2.0s"

    @pytest.mark.asyncio
    async def test_concurrent_search_performance(self, test_dependencies):
        """Test performance with concurrent searches."""
        # Mock responses for concurrent testing
        mock_response = MagicMock()
        mock_response.text = "<html><body></body></html>"
        mock_response.status_code = 200
        mock_response.url = "https://test.example.com"
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        test_dependencies._http_client = mock_client
        test_dependencies.request_delay = 0.1  # Short delay for testing
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        start_time = time.time()
        
        # Run 5 concurrent searches
        tasks = [
            search_otlas_organizations(mock_ctx, f"query {i}", max_results=10)
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should complete all 5 searches
        assert len(results) == 5
        assert all(r["success"] for r in results)
        
        # With rate limiting, should take at least 5 * 0.1 = 0.5s
        assert elapsed >= 0.5
        # But should not take too much longer (parallel execution)
        assert elapsed < 2.0, f"Concurrent searches took {elapsed}s, expected < 2.0s"


class TestRateLimitingBehavior:
    """Test rate limiting implementation and behavior."""

    @pytest.mark.asyncio
    async def test_rate_limiting_delay_enforcement(self, test_dependencies):
        """Test that rate limiting delays are properly enforced."""
        test_dependencies.request_delay = 0.2  # 200ms delay
        
        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_response.status_code = 200
        mock_response.url = "https://test.example.com"
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        # Measure time for sequential requests
        times = []
        
        for i in range(3):
            start = time.time()
            await search_otlas_organizations(mock_ctx, f"query {i}", max_results=1)
            end = time.time()
            times.append(end - start)
        
        # Each request should take at least the delay time
        for elapsed in times:
            assert elapsed >= test_dependencies.request_delay, f"Request took {elapsed}s, expected >= {test_dependencies.request_delay}s"

    @pytest.mark.asyncio
    async def test_rate_limiting_with_different_delays(self, test_dependencies):
        """Test rate limiting with different delay configurations."""
        delays_to_test = [0.05, 0.1, 0.3, 0.5]
        
        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_response.status_code = 200
        mock_response.url = "https://test.example.com"
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        for delay in delays_to_test:
            test_dependencies.request_delay = delay
            
            start_time = time.time()
            await search_otlas_organizations(mock_ctx, "test query", max_results=1)
            end_time = time.time()
            
            elapsed = end_time - start_time
            assert elapsed >= delay, f"With delay {delay}s, request took {elapsed}s"

    @pytest.mark.asyncio
    async def test_concurrent_requests_respect_rate_limits(self, test_dependencies):
        """Test that concurrent requests still respect global rate limits."""
        test_dependencies.request_delay = 0.1
        
        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_response.status_code = 200
        mock_response.url = "https://test.example.com"
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        start_time = time.time()
        
        # Start 4 concurrent requests
        tasks = [
            search_otlas_organizations(mock_ctx, f"query {i}", max_results=1)
            for i in range(4)
        ]
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_elapsed = end_time - start_time
        
        assert len(results) == 4
        assert all(r["success"] for r in results)
        
        # Total time should be at least 4 * delay (sequential due to rate limiting)
        expected_min_time = 4 * test_dependencies.request_delay
        assert total_elapsed >= expected_min_time, f"Total time {total_elapsed}s, expected >= {expected_min_time}s"

    @pytest.mark.asyncio
    async def test_rate_limiting_doesnt_affect_parsing(self, test_dependencies, mock_org_html):
        """Test that rate limiting only affects network requests, not parsing."""
        test_dependencies.request_delay = 0.2
        
        # Test pure parsing performance (no rate limiting should apply)
        start_time = time.time()
        
        result = extract_structured_data(mock_org_html, "organizations", max_items=10)
        
        end_time = time.time()
        parsing_elapsed = end_time - start_time
        
        assert result["success"] is True
        # Parsing should be much faster than rate limit delay
        assert parsing_elapsed < test_dependencies.request_delay, f"Parsing took {parsing_elapsed}s, rate limit is {test_dependencies.request_delay}s"


class TestResourceUsageOptimization:
    """Test resource usage and optimization."""

    @pytest.mark.asyncio
    async def test_memory_usage_with_large_datasets(self, test_dependencies):
        """Test memory usage with large search results."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create a large dataset
        large_org_list = []
        for i in range(1000):
            org = PartnerOrganization(
                name=f"Large Organization {i}",
                country=f"Country{i % 50}",
                organization_type="NGO",
                experience_level="Experienced",
                target_groups=[f"Group{j}" for j in range(5)],
                activity_types=[f"Activity{j}" for j in range(3)],
                contact_info=f"contact{i}@example.com",
                profile_url=f"https://example.com/org/{i}",
                last_active="2024-01-01"
            )
            large_org_list.append(org)
        
        # Create response with large dataset
        response = SearchResponse(
            search_type="organizations",
            query_parameters={"query": "memory test"},
            total_results=len(large_org_list),
            results=large_org_list,
            success=True
        )
        
        # Get peak memory usage
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for 1000 items)
        assert memory_increase < 100, f"Memory increased by {memory_increase}MB, expected < 100MB"
        
        # Cleanup
        del large_org_list
        del response

    @pytest.mark.asyncio
    async def test_http_connection_pooling_efficiency(self, test_dependencies):
        """Test efficiency of HTTP connection pooling."""
        # Mock multiple responses
        responses = []
        for i in range(10):
            mock_response = MagicMock()
            mock_response.text = f"<html>Response {i}</html>"
            mock_response.status_code = 200
            mock_response.url = f"https://test.example.com/{i}"
            mock_response.raise_for_status = MagicMock()
            responses.append(mock_response)
        
        mock_client = AsyncMock()
        mock_client.get.side_effect = responses
        test_dependencies._http_client = mock_client
        test_dependencies.request_delay = 0.01  # Very short delay for this test
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        start_time = time.time()
        
        # Make multiple requests using the same client
        tasks = [
            search_otlas_organizations(mock_ctx, f"query {i}", max_results=1)
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        assert len(results) == 10
        assert all(r["success"] for r in results)
        
        # Should complete efficiently with connection pooling
        # 10 requests with 0.01s delay each = minimum 0.1s
        assert total_time >= 0.1
        # But should not take too long due to efficient connection reuse
        assert total_time < 1.0, f"10 requests took {total_time}s, expected < 1.0s with connection pooling"

    @pytest.mark.asyncio
    async def test_dependency_cleanup_efficiency(self, test_dependencies):
        """Test efficiency of dependency cleanup."""
        # Initialize HTTP client
        client = test_dependencies.http_client
        assert test_dependencies._http_client is not None
        
        start_time = time.time()
        
        # Test cleanup
        await test_dependencies.cleanup()
        
        end_time = time.time()
        cleanup_time = end_time - start_time
        
        # Cleanup should be very fast
        assert cleanup_time < 1.0, f"Cleanup took {cleanup_time}s, expected < 1.0s"


class TestScalabilityLimits:
    """Test behavior at scale and identify limits."""

    @pytest.mark.asyncio
    async def test_maximum_concurrent_requests(self, test_dependencies):
        """Test maximum number of concurrent requests that can be handled."""
        test_dependencies.request_delay = 0.01  # Very short delay
        test_dependencies.concurrent_requests = 10  # Allow more concurrency
        
        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_response.status_code = 200
        mock_response.url = "https://test.example.com"
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        # Test different concurrency levels
        concurrency_levels = [1, 5, 10, 20, 50]
        
        for level in concurrency_levels:
            start_time = time.time()
            
            tasks = [
                search_otlas_organizations(mock_ctx, f"query {i}", max_results=1)
                for i in range(level)
            ]
            
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()
                elapsed = end_time - start_time
                
                # Check how many succeeded
                successes = len([r for r in results if isinstance(r, dict) and r.get("success")])
                
                print(f"Concurrency {level}: {successes}/{level} succeeded in {elapsed:.2f}s")
                
                # Should handle reasonable concurrency levels
                if level <= 20:
                    assert successes >= level * 0.9, f"Only {successes}/{level} succeeded at concurrency {level}"
                
            except Exception as e:
                print(f"Failed at concurrency level {level}: {e}")
                if level <= 10:  # Should handle at least 10 concurrent requests
                    raise

    def test_maximum_result_set_size(self):
        """Test handling of very large result sets."""
        # Test with increasing result set sizes
        sizes_to_test = [10, 100, 500, 1000, 5000]
        
        for size in sizes_to_test:
            try:
                # Create HTML with many items
                org_items = [
                    f'<div class="org-item"><div class="org-name">Org {i}</div><div class="org-country">Country</div><div class="org-type">NGO</div><div class="exp-level">Experienced</div></div>'
                    for i in range(size)
                ]
                
                html = f"<html><body>{''.join(org_items)}</body></html>"
                
                start_time = time.time()
                result = extract_structured_data(html, "organizations", max_items=size)
                end_time = time.time()
                
                elapsed = end_time - start_time
                
                assert result["success"] is True
                assert result["parsed_count"] == size
                
                print(f"Processed {size} items in {elapsed:.2f}s ({size/elapsed:.0f} items/sec)")
                
                # Performance should degrade gracefully
                if size <= 1000:
                    assert elapsed < 5.0, f"Processing {size} items took {elapsed}s, expected < 5.0s"
                
            except Exception as e:
                print(f"Failed at size {size}: {e}")
                if size <= 500:  # Should handle at least 500 items
                    raise

    @pytest.mark.asyncio
    async def test_long_running_session_stability(self, test_dependencies):
        """Test stability over extended usage periods."""
        test_dependencies.request_delay = 0.01
        
        mock_response = MagicMock()
        mock_response.text = "<html><body></body></html>"
        mock_response.status_code = 200
        mock_response.url = "https://test.example.com"
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        test_dependencies._http_client = mock_client
        
        mock_ctx = MagicMock()
        mock_ctx.deps = test_dependencies
        
        # Simulate extended usage
        success_count = 0
        total_requests = 100
        
        for i in range(total_requests):
            try:
                result = await search_otlas_organizations(mock_ctx, f"query {i}", max_results=1)
                if result.get("success"):
                    success_count += 1
                
                # Add small delay to simulate real usage
                await asyncio.sleep(0.001)
                
            except Exception as e:
                print(f"Request {i} failed: {e}")
        
        # Should maintain high success rate throughout the session
        success_rate = success_count / total_requests
        assert success_rate >= 0.95, f"Success rate was {success_rate:.2%}, expected >= 95%"
        
        # Clean up should work after extended usage
        await test_dependencies.cleanup()


class TestPerformanceRegression:
    """Test for performance regressions."""

    @pytest.mark.asyncio
    async def test_search_performance_benchmarks(self, test_dependencies, mock_org_html):
        """Establish performance benchmarks for regression testing."""
        with patch('agents.erasmus_partner_agent.tools.search_otlas_organizations') as mock_search, \
             patch('agents.erasmus_partner_agent.tools.extract_structured_data') as mock_extract:
            
            mock_search.return_value = {
                "success": True,
                "raw_html": mock_org_html,
                "total_found": 2,
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
                        "profile_url": "https://test.com/org/1",
                        "last_active": "2024-01-01"
                    }
                ],
                "parsed_count": 1,
                "error": None
            }
            
            # Benchmark: Complete search operation
            times = []
            for _ in range(10):  # Run multiple times for average
                start = time.time()
                result = await run_search("test query", test_dependencies)
                end = time.time()
                times.append(end - start)
                
                assert isinstance(result, SearchResponse)
                assert result.success is True
            
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            
            print(f"Search performance - Avg: {avg_time:.3f}s, Median: {median_time:.3f}s")
            
            # Performance benchmarks (without actual network calls)
            assert avg_time < 0.5, f"Average search time {avg_time:.3f}s exceeded benchmark of 0.5s"
            assert median_time < 0.3, f"Median search time {median_time:.3f}s exceeded benchmark of 0.3s"
            
            # Consistency check (standard deviation should be low)
            std_dev = statistics.stdev(times)
            assert std_dev < 0.1, f"Performance variance too high: std dev {std_dev:.3f}s"