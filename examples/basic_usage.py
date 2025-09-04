#!/usr/bin/env python3
"""
Basic usage examples for the Erasmus Partner Agent.

This script demonstrates how to use the agent programmatically
for different search scenarios.
"""
import asyncio
import json
from erasmus_partner_agent import run_search, AgentDependencies


async def example_partner_search():
    """Example: Search for partner organizations."""
    print("🔍 Searching for partner organizations...")
    
    deps = AgentDependencies.from_settings()
    
    try:
        result = await run_search(
            "Find youth organizations in Germany for cultural exchange projects",
            deps
        )
        
        if result.success:
            print(f"✅ Found {len(result.results)} organizations:")
            for org in result.results[:3]:  # Show first 3
                print(f"  • {org.name} ({org.country})")
                print(f"    Type: {org.organization_type}")
                print(f"    Experience: {org.experience_level}")
                print(f"    Target Groups: {', '.join(org.target_groups[:2])}")
                print()
        else:
            print(f"❌ Search failed: {result.error_message}")
            
    finally:
        await deps.cleanup()


async def example_project_search():
    """Example: Search for project opportunities."""
    print("🔍 Searching for project opportunities...")
    
    deps = AgentDependencies.from_settings()
    
    try:
        result = await run_search(
            "Find KA152 projects looking for partners in digital skills",
            deps
        )
        
        if result.success:
            print(f"✅ Found {len(result.results)} projects:")
            for project in result.results[:3]:  # Show first 3
                print(f"  • {project.title}")
                print(f"    Type: {project.project_type}")
                print(f"    Countries: {', '.join(project.countries_involved)}")
                print(f"    Deadline: {project.deadline or 'Not specified'}")
                print(f"    Themes: {', '.join(project.themes[:2])}")
                print()
        else:
            print(f"❌ Search failed: {result.error_message}")
            
    finally:
        await deps.cleanup()


async def example_smart_search():
    """Example: Let the agent decide search type automatically."""
    queries = [
        "I need collaborators for environmental education project",
        "Looking for training course opportunities in Nordic countries",
        "Find NGOs experienced in youth exchanges in Eastern Europe"
    ]
    
    print("🧠 Testing smart search with automatic intent detection...")
    
    for query in queries:
        print(f"\nQuery: {query}")
        deps = AgentDependencies.from_settings()
        
        try:
            result = await run_search(query, deps)
            
            if result.success:
                search_type = "organizations" if result.search_type == "organizations" else "projects"
                print(f"  ➜ Detected: {search_type} search")
                print(f"  ➜ Found: {len(result.results)} results")
            else:
                print(f"  ❌ Failed: {result.error_message}")
                
        finally:
            await deps.cleanup()


async def example_structured_output():
    """Example: Working with structured data output."""
    print("📊 Demonstrating structured data output...")
    
    deps = AgentDependencies.from_settings()
    
    try:
        result = await run_search(
            "Find partner organizations in France for youth exchanges",
            deps
        )
        
        if result.success:
            # Convert to JSON for external systems
            json_output = json.dumps(result.dict(), indent=2, default=str)
            print("JSON output (truncated):")
            print(json_output[:500] + "...")
            
            # Access structured data
            print(f"\nStructured data access:")
            print(f"Search type: {result.search_type}")
            print(f"Total results: {result.total_results}")
            print(f"Query parameters: {result.query_parameters}")
            print(f"Search timestamp: {result.search_timestamp}")
            
        else:
            print(f"❌ Search failed: {result.error_message}")
            
    finally:
        await deps.cleanup()


async def main():
    """Run all examples."""
    print("🚀 Erasmus Partner Agent - Basic Usage Examples")
    print("=" * 50)
    
    examples = [
        example_partner_search,
        example_project_search,
        example_smart_search,
        example_structured_output
    ]
    
    for example in examples:
        print(f"\n{'-' * 50}")
        await example()
        print(f"{'-' * 50}")


if __name__ == "__main__":
    # Make sure you have a .env file with LLM_API_KEY
    asyncio.run(main())