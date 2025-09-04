"""
Test configuration for Erasmus Partner Agent tests.

This module provides fixtures and configuration for pytest testing,
including mock dependencies, test data, and test utilities.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
from pathlib import Path

from pydantic_ai.models.test import TestModel
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelTextResponse

from ..agent import agent
from ..dependencies import AgentDependencies
from ..models import PartnerOrganization, ProjectOpportunity, SearchResponse
from ..settings import Settings


# Test configuration
@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Test models and dependencies
@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings(
        llm_api_key="test-api-key",
        otlas_base_url="https://test.salto-youth.net/tools/otlas-partner-finding",
        user_agent="TestAgent/1.0",
        request_delay=0.1,  # Faster for tests
        max_retries=1,
        timeout_seconds=5,
        enable_caching=False,  # Disable caching in tests
        debug=True
    )


@pytest.fixture
def test_dependencies(test_settings):
    """Create test dependencies with mocked HTTP client."""
    return AgentDependencies(
        otlas_base_url=test_settings.otlas_base_url,
        user_agent=test_settings.user_agent,
        request_delay=test_settings.request_delay,
        max_retries=test_settings.max_retries,
        timeout=test_settings.timeout_seconds,
        cache_enabled=False,
        session_id="test-session-123",
        user_id="test-user-456"
    )


@pytest.fixture
def mock_http_client():
    """Create a mocked HTTP client for testing."""
    mock_client = AsyncMock()
    
    # Default successful response
    mock_response = MagicMock()
    mock_response.text = MOCK_ORG_HTML
    mock_response.status_code = 200
    mock_response.url = "https://test.salto-youth.net/tools/otlas-partner-finding/search"
    mock_response.raise_for_status.return_value = None
    
    mock_client.get.return_value = mock_response
    return mock_client


@pytest.fixture
def test_agent():
    """Create agent with TestModel for basic testing."""
    test_model = TestModel()
    return agent.override(model=test_model)


@pytest.fixture
def function_test_agent():
    """Create agent with FunctionModel for controlled behavior testing."""
    def create_test_function():
        call_count = 0
        
        async def test_function(messages, tools):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                # First call - analyze intent
                return ModelTextResponse(
                    content="I'll search for organizations based on your query"
                )
            elif call_count == 2:
                # Second call - perform search
                return {
                    "search_organizations": {
                        "query": "youth exchange",
                        "country": "Germany",
                        "max_results": 10
                    }
                }
            else:
                # Final response with structured data
                return ModelTextResponse(
                    content="Search completed successfully"
                )
        
        return test_function
    
    function_model = FunctionModel(create_test_function())
    return agent.override(model=function_model)


# Sample test data
@pytest.fixture
def sample_organization():
    """Sample organization for testing."""
    return PartnerOrganization(
        name="Youth for Europe Foundation",
        country="Germany",
        organization_type="NGO",
        experience_level="Experienced",
        target_groups=["Young people", "Youth workers"],
        activity_types=["Training courses", "Youth exchanges"],
        contact_info="info@yfe.de",
        profile_url="https://www.salto-youth.net/tools/otlas-partner-finding/organisation/123",
        last_active="2024-01-15"
    )


@pytest.fixture
def sample_project():
    """Sample project for testing."""
    return ProjectOpportunity(
        title="Digital Skills for Youth Workers",
        project_type="KA152",
        countries_involved=["Germany", "France"],
        deadline="2024-03-01",
        target_groups=["Youth workers", "Trainers"],
        themes=["Digital skills", "Media literacy"],
        description="Training course focusing on digital competencies for youth work professionals",
        contact_organization="European Youth Network",
        project_url="https://www.salto-youth.net/tools/otlas-partner-finding/project/456",
        created_date="2024-01-10"
    )


@pytest.fixture
def sample_organizations_list(sample_organization):
    """List of sample organizations."""
    return [
        sample_organization,
        PartnerOrganization(
            name="European Youth Council",
            country="Belgium",
            organization_type="NGO",
            experience_level="Expert",
            target_groups=["Youth workers", "Policy makers"],
            activity_types=["Seminars", "Study visits"],
            contact_info="info@youthcouncil.eu",
            profile_url="https://www.salto-youth.net/tools/otlas-partner-finding/organisation/124",
            last_active="2024-01-20"
        )
    ]


@pytest.fixture
def sample_projects_list(sample_project):
    """List of sample projects."""
    return [
        sample_project,
        ProjectOpportunity(
            title="Green Youth Exchange",
            project_type="KA153",
            countries_involved=["Spain", "Italy", "Portugal"],
            deadline="2024-04-15",
            target_groups=["Young people"],
            themes=["Environment", "Climate change"],
            description="Youth exchange focused on environmental awareness and action",
            contact_organization="Eco Youth Network",
            project_url="https://www.salto-youth.net/tools/otlas-partner-finding/project/457",
            created_date="2024-01-12"
        )
    ]


# Mock HTML data for web scraping tests
MOCK_ORG_HTML = '''
<html>
<body>
<div class="search-results">
    <div class="org-item">
        <div class="org-name">Youth for Europe Foundation</div>
        <div class="org-country">Germany</div>
        <div class="org-type">NGO</div>
        <div class="exp-level">Experienced</div>
        <div class="target-group">Young people</div>
        <div class="target-group">Youth workers</div>
        <div class="activity-type">Training courses</div>
        <div class="activity-type">Youth exchanges</div>
        <div class="contact-info">info@yfe.de</div>
        <a href="/organisation/123" class="org-link">View Profile</a>
        <div class="last-active">2024-01-15</div>
    </div>
    <div class="org-item">
        <div class="org-name">European Youth Council</div>
        <div class="org-country">Belgium</div>
        <div class="org-type">NGO</div>
        <div class="exp-level">Expert</div>
        <div class="target-group">Youth workers</div>
        <div class="target-group">Policy makers</div>
        <div class="activity-type">Seminars</div>
        <div class="activity-type">Study visits</div>
        <div class="contact-info">info@youthcouncil.eu</div>
        <a href="/organisation/124" class="org-link">View Profile</a>
        <div class="last-active">2024-01-20</div>
    </div>
</div>
</body>
</html>
'''

MOCK_PROJECT_HTML = '''
<html>
<body>
<div class="search-results">
    <div class="project-item">
        <div class="project-title">Digital Skills for Youth Workers</div>
        <div class="project-type">KA152</div>
        <div class="countries">Germany</div>
        <div class="countries">France</div>
        <div class="deadline">2024-03-01</div>
        <div class="target-groups">Youth workers</div>
        <div class="target-groups">Trainers</div>
        <div class="themes">Digital skills</div>
        <div class="themes">Media literacy</div>
        <div class="description">Training course focusing on digital competencies for youth work professionals</div>
        <div class="contact-org">European Youth Network</div>
        <a href="/project/456" class="project-link">View Project</a>
        <div class="created-date">2024-01-10</div>
    </div>
    <div class="project-item">
        <div class="project-title">Green Youth Exchange</div>
        <div class="project-type">KA153</div>
        <div class="countries">Spain</div>
        <div class="countries">Italy</div>
        <div class="countries">Portugal</div>
        <div class="deadline">2024-04-15</div>
        <div class="target-groups">Young people</div>
        <div class="themes">Environment</div>
        <div class="themes">Climate change</div>
        <div class="description">Youth exchange focused on environmental awareness and action</div>
        <div class="contact-org">Eco Youth Network</div>
        <a href="/project/457" class="project-link">View Project</a>
        <div class="created-date">2024-01-12</div>
    </div>
</div>
</body>
</html>
'''

MOCK_EMPTY_HTML = '''
<html>
<body>
<div class="search-results">
    <div class="no-results">No results found</div>
</div>
</body>
</html>
'''


@pytest.fixture
def mock_org_html():
    """Mock HTML response for organization search."""
    return MOCK_ORG_HTML


@pytest.fixture
def mock_project_html():
    """Mock HTML response for project search."""
    return MOCK_PROJECT_HTML


@pytest.fixture
def mock_empty_html():
    """Mock HTML response for empty search."""
    return MOCK_EMPTY_HTML


# Test utilities
class MockResponse:
    """Mock HTTP response for testing."""
    
    def __init__(self, text: str, status_code: int = 200, url: str = None):
        self.text = text
        self.status_code = status_code
        self.url = url or "https://test.example.com"
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code} error")


# Performance testing utilities
@pytest.fixture
def performance_timer():
    """Timer for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Async context managers for testing
@pytest.fixture
async def cleanup_dependencies():
    """Ensure dependencies are properly cleaned up after tests."""
    dependencies_to_cleanup = []
    
    def register(deps):
        dependencies_to_cleanup.append(deps)
        return deps
    
    yield register
    
    # Cleanup
    for deps in dependencies_to_cleanup:
        await deps.cleanup()