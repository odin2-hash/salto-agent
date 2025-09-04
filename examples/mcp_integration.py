#!/usr/bin/env python3
"""
MCP Server integration examples for the Erasmus Partner Agent.

This script demonstrates how to integrate with the MCP server
for use in n8n, Flowise, OpenWebUI, and other systems.
"""
import asyncio
import httpx
import json
from typing import Dict, Any


class ErasmusPartnerClient:
    """Client for interacting with Erasmus Partner Agent MCP server."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search_partners(
        self,
        query: str,
        country: str = None,
        activity_type: str = None,
        theme: str = None,
        target_group: str = None,
        max_results: int = 20
    ) -> Dict[str, Any]:
        """Search for partner organizations."""
        payload = {
            "query": query,
            "max_results": max_results
        }
        
        if country:
            payload["country"] = country
        if activity_type:
            payload["activity_type"] = activity_type
        if theme:
            payload["theme"] = theme
        if target_group:
            payload["target_group"] = target_group
        
        response = await self.client.post(
            f"{self.base_url}/search/partners",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def search_projects(
        self,
        query: str,
        project_type: str = None,
        countries: list = None,
        themes: list = None,
        target_group: str = None,
        max_results: int = 20
    ) -> Dict[str, Any]:
        """Search for project opportunities."""
        payload = {
            "query": query,
            "max_results": max_results
        }
        
        if project_type:
            payload["project_type"] = project_type
        if countries:
            payload["countries"] = countries
        if themes:
            payload["themes"] = themes
        if target_group:
            payload["target_group"] = target_group
        
        response = await self.client.post(
            f"{self.base_url}/search/projects",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def smart_search(
        self,
        query: str,
        max_results: int = 20,
        force_search_type: str = None
    ) -> Dict[str, Any]:
        """Intelligent search with automatic intent detection."""
        payload = {
            "query": query,
            "max_results": max_results
        }
        
        if force_search_type:
            payload["force_search_type"] = force_search_type
        
        response = await self.client.post(
            f"{self.base_url}/search/smart",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def get_search_parameters(self) -> Dict[str, Any]:
        """Get available search parameters."""
        response = await self.client.get(f"{self.base_url}/search/parameters")
        response.raise_for_status()
        return response.json()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check server health."""
        response = await self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def example_basic_integration():
    """Basic integration example."""
    print("🔌 Basic MCP integration example...")
    
    client = ErasmusPartnerClient()
    
    try:
        # Health check
        health = await client.health_check()
        print(f"Server status: {health['status']}")
        
        # Search for partners
        result = await client.search_partners(
            query="youth exchange partners",
            country="Germany",
            max_results=5
        )
        
        print(f"Found {len(result.get('organizations', []))} organizations:")
        for org in result.get('organizations', [])[:3]:
            print(f"  • {org['name']} ({org['country']})")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await client.close()


async def example_n8n_workflow():
    """Example for n8n workflow integration."""
    print("📊 n8n workflow integration example...")
    
    # Simulate n8n workflow data
    workflow_data = {
        "organization_name": "My Youth NGO",
        "project_theme": "environmental education",
        "target_countries": ["Sweden", "Finland", "Norway"],
        "project_type": "KA152"
    }
    
    client = ErasmusPartnerClient()
    
    try:
        # Step 1: Find partners in target countries
        partners_by_country = []
        for country in workflow_data["target_countries"]:
            result = await client.search_partners(
                query=f"{workflow_data['project_theme']} partners",
                country=country,
                max_results=3
            )
            
            if result.get('success'):
                partners_by_country.extend(result.get('organizations', []))
        
        print(f"Found {len(partners_by_country)} potential partners across Nordic countries")
        
        # Step 2: Find existing projects to join
        project_result = await client.search_projects(
            query=workflow_data['project_theme'],
            project_type=workflow_data['project_type'],
            countries=workflow_data['target_countries'],
            max_results=5
        )
        
        print(f"Found {len(project_result.get('projects', []))} existing projects to potentially join")
        
        # Step 3: Format for n8n output
        n8n_output = {
            "potential_partners": partners_by_country,
            "existing_projects": project_result.get('projects', []),
            "search_metadata": {
                "search_date": project_result.get('search_timestamp'),
                "organization": workflow_data['organization_name'],
                "theme": workflow_data['project_theme']
            }
        }
        
        print("📋 N8N workflow output formatted successfully")
        print(f"   Partners: {len(n8n_output['potential_partners'])}")
        print(f"   Projects: {len(n8n_output['existing_projects'])}")
        
    except Exception as e:
        print(f"❌ N8N workflow error: {str(e)}")
    finally:
        await client.close()


async def example_flowise_chatbot():
    """Example for Flowise chatbot integration."""
    print("🤖 Flowise chatbot integration example...")
    
    # Simulate user questions from chatbot
    user_questions = [
        "I need partners for a digital skills project in Eastern Europe",
        "Are there any environmental projects looking for partners?",
        "Find training opportunities for youth workers in Scandinavia"
    ]
    
    client = ErasmusPartnerClient()
    
    try:
        for question in user_questions:
            print(f"\nUser: {question}")
            
            # Use smart search for chatbot interactions
            result = await client.smart_search(
                query=question,
                max_results=3
            )
            
            if result.get('success'):
                search_type = result.get('search_type')
                results = result.get('results', [])
                
                if search_type == "organizations":
                    response = f"I found {len(results)} organizations that might be suitable partners:\n"
                    for org in results:
                        response += f"• {org['name']} from {org['country']} - {org['organization_type']}\n"
                else:
                    response = f"I found {len(results)} project opportunities:\n"
                    for project in results:
                        response += f"• {project['title']} ({project['project_type']}) - Deadline: {project.get('deadline', 'Not specified')}\n"
                
                print(f"Bot: {response}")
            else:
                print(f"Bot: I'm sorry, I couldn't find relevant information. Error: {result.get('error_message')}")
                
    except Exception as e:
        print(f"❌ Flowise integration error: {str(e)}")
    finally:
        await client.close()


async def example_openwebui_integration():
    """Example for OpenWebUI integration."""
    print("🌐 OpenWebUI integration example...")
    
    client = ErasmusPartnerClient()
    
    try:
        # Get available parameters for UI
        params = await client.get_search_parameters()
        print("Available search parameters:")
        print(f"  Countries: {len(params['countries'])} options")
        print(f"  Project types: {params['project_types']}")
        print(f"  Themes: {len(params['themes'])} options")
        
        # Example advanced search with multiple filters
        advanced_result = await client.search_partners(
            query="cultural heritage education",
            country="Italy",
            activity_type="Training course",
            theme="Culture",
            target_group="Youth workers",
            max_results=10
        )
        
        if advanced_result.get('success'):
            organizations = advanced_result.get('organizations', [])
            print(f"\nAdvanced search found {len(organizations)} specialized organizations")
            
            # Format for web UI display
            ui_data = {
                "search_summary": {
                    "query": "cultural heritage education",
                    "filters": {
                        "country": "Italy",
                        "activity_type": "Training course",
                        "theme": "Culture",
                        "target_group": "Youth workers"
                    },
                    "results_count": len(organizations)
                },
                "organizations": organizations,
                "export_options": ["JSON", "CSV", "Excel"],
                "contact_recommendations": [
                    "Verify contact information before reaching out",
                    "Mention specific project themes in initial contact",
                    "Include your organization's experience level"
                ]
            }
            
            print("📱 OpenWebUI data structure prepared")
            print(f"   Ready for frontend display with {len(ui_data['organizations'])} results")
            
    except Exception as e:
        print(f"❌ OpenWebUI integration error: {str(e)}")
    finally:
        await client.close()


async def example_webhook_integration():
    """Example for webhook/API integration."""
    print("🔗 Webhook integration example...")
    
    client = ErasmusPartnerClient()
    
    try:
        # Simulate incoming webhook data
        webhook_data = {
            "event_type": "project_submission",
            "project_id": "PRJ-2024-001",
            "project_title": "Digital Youth Inclusion",
            "required_partners": 3,
            "partner_criteria": {
                "countries": ["Poland", "Czech Republic", "Slovakia"],
                "experience_level": "Experienced",
                "focus_areas": ["Digital inclusion", "Social work"]
            },
            "deadline": "2024-03-15"
        }
        
        # Process webhook: find suitable partners
        all_partners = []
        for country in webhook_data["partner_criteria"]["countries"]:
            result = await client.search_partners(
                query=" ".join(webhook_data["partner_criteria"]["focus_areas"]),
                country=country,
                max_results=5
            )
            
            if result.get('success'):
                # Filter by experience level
                experienced_orgs = [
                    org for org in result.get('organizations', [])
                    if org.get('experience_level', '').lower() == 'experienced'
                ]
                all_partners.extend(experienced_orgs)
        
        # Prepare webhook response
        webhook_response = {
            "project_id": webhook_data["project_id"],
            "partner_matches": all_partners[:webhook_data["required_partners"]],
            "match_quality": "high" if len(all_partners) >= webhook_data["required_partners"] else "medium",
            "recommendations": [
                f"Found {len(all_partners)} experienced organizations",
                f"Top {webhook_data['required_partners']} partners selected",
                "Manual review recommended before contact"
            ],
            "next_steps": [
                "Review partner profiles",
                "Prepare project pitch",
                "Schedule introduction calls"
            ]
        }
        
        print(f"🎯 Webhook processed successfully")
        print(f"   Project: {webhook_data['project_title']}")
        print(f"   Partners found: {len(all_partners)}")
        print(f"   Match quality: {webhook_response['match_quality']}")
        
    except Exception as e:
        print(f"❌ Webhook integration error: {str(e)}")
    finally:
        await client.close()


async def main():
    """Run all integration examples."""
    print("🌍 Erasmus Partner Agent - MCP Integration Examples")
    print("=" * 60)
    
    examples = [
        example_basic_integration,
        example_n8n_workflow,
        example_flowise_chatbot,
        example_openwebui_integration,
        example_webhook_integration
    ]
    
    for example in examples:
        print(f"\n{'-' * 60}")
        await example()
        print(f"{'-' * 60}")


if __name__ == "__main__":
    print("📝 Note: Make sure the MCP server is running on localhost:8000")
    print("   Start it with: python -m erasmus_partner_agent.mcp_server")
    print()
    
    # Uncomment to run examples (requires server to be running)
    # asyncio.run(main())