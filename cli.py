"""
Command Line Interface for the Erasmus Partner Agent.

This module provides a Typer-based CLI for interacting with the agent
directly from the command line.
"""
import asyncio
import json
from typing import Optional
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from .agent import run_search, extract_search_parameters
from .dependencies import AgentDependencies
from .models import SearchResponse, PartnerOrganization, ProjectOpportunity


app = typer.Typer(
    name="erasmus-partner-agent",
    help="Search for Erasmus+ partners and project opportunities",
    rich_markup_mode="rich"
)
console = Console()


@app.command("partners")
def search_partners(
    query: str = typer.Argument(..., help="Search query for partner organizations"),
    country: Optional[str] = typer.Option(None, "--country", "-c", help="Filter by country"),
    activity_type: Optional[str] = typer.Option(None, "--activity", "-a", help="Filter by activity type"),
    target_group: Optional[str] = typer.Option(None, "--target", "-t", help="Filter by target group"),
    max_results: int = typer.Option(20, "--max", "-m", help="Maximum number of results"),
    export: bool = typer.Option(False, "--export", "-e", help="Export results to file"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json, csv"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path")
):
    """Search for partner organizations on SALTO-YOUTH Otlas."""
    
    async def _search():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Searching for partner organizations...", total=None)
            
            # Create dependencies
            deps = AgentDependencies.from_settings()
            
            # Build search query with parameters
            search_params = extract_search_parameters(query)
            if country:
                search_params["country"] = country
            if activity_type:
                search_params["activity_type"] = activity_type
            if target_group:
                search_params["target_group"] = target_group
                
            # Run the search
            try:
                enhanced_query = f"Find partner organizations: {query}"
                if country:
                    enhanced_query += f" in {country}"
                if activity_type:
                    enhanced_query += f" for {activity_type}"
                
                result = await run_search(enhanced_query, deps)
                
                # Display results
                if result.success and result.results:
                    if format == "table":
                        display_organizations_table(result.results)
                    elif format == "json":
                        display_json(result)
                    elif format == "csv":
                        display_csv(result.results, "organizations")
                    
                    if export:
                        export_results(result, output_file, format, "partners")
                        
                elif result.success and not result.results:
                    rprint("[yellow]No organizations found matching your criteria.[/yellow]")
                    suggest_alternatives(query, "organizations")
                else:
                    rprint(f"[red]Search failed: {result.error_message}[/red]")
                    
            except Exception as e:
                rprint(f"[red]Error: {str(e)}[/red]")
    
    asyncio.run(_search())


@app.command("projects")
def search_projects(
    query: str = typer.Argument(..., help="Search query for project opportunities"),
    project_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by project type (KA152, etc.)"),
    theme: Optional[str] = typer.Option(None, "--theme", help="Filter by theme"),
    target_group: Optional[str] = typer.Option(None, "--target", help="Filter by target group"),
    max_results: int = typer.Option(20, "--max", "-m", help="Maximum number of results"),
    export: bool = typer.Option(False, "--export", "-e", help="Export results to file"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json, csv"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path")
):
    """Search for project opportunities on SALTO-YOUTH Otlas."""
    
    async def _search():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Searching for project opportunities...", total=None)
            
            # Create dependencies
            deps = AgentDependencies.from_settings()
            
            # Build search query with parameters
            enhanced_query = f"Find project opportunities: {query}"
            if project_type:
                enhanced_query += f" type {project_type}"
            if theme:
                enhanced_query += f" theme {theme}"
            
            # Run the search
            try:
                result = await run_search(enhanced_query, deps)
                
                # Display results
                if result.success and result.results:
                    if format == "table":
                        display_projects_table(result.results)
                    elif format == "json":
                        display_json(result)
                    elif format == "csv":
                        display_csv(result.results, "projects")
                    
                    if export:
                        export_results(result, output_file, format, "projects")
                        
                elif result.success and not result.results:
                    rprint("[yellow]No projects found matching your criteria.[/yellow]")
                    suggest_alternatives(query, "projects")
                else:
                    rprint(f"[red]Search failed: {result.error_message}[/red]")
                    
            except Exception as e:
                rprint(f"[red]Error: {str(e)}[/red]")
    
    asyncio.run(_search())


@app.command("search")
def smart_search(
    query: str = typer.Argument(..., help="Natural language search query"),
    max_results: int = typer.Option(20, "--max", "-m", help="Maximum number of results"),
    export: bool = typer.Option(False, "--export", "-e", help="Export results to file"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json, csv"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path")
):
    """Smart search that automatically detects whether you want partners or projects."""
    
    async def _search():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Analyzing query and searching...", total=None)
            
            # Create dependencies
            deps = AgentDependencies.from_settings()
            
            try:
                # Run the search - agent will determine intent automatically
                result = await run_search(query, deps)
                
                # Display results
                if result.success and result.results:
                    rprint(f"[green]Found {len(result.results)} {result.search_type}[/green]")
                    
                    if format == "table":
                        if result.search_type == "organizations":
                            display_organizations_table(result.results)
                        else:
                            display_projects_table(result.results)
                    elif format == "json":
                        display_json(result)
                    elif format == "csv":
                        display_csv(result.results, result.search_type)
                    
                    if export:
                        export_results(result, output_file, format, result.search_type)
                        
                elif result.success and not result.results:
                    rprint("[yellow]No results found matching your criteria.[/yellow]")
                    suggest_alternatives(query, result.search_type)
                else:
                    rprint(f"[red]Search failed: {result.error_message}[/red]")
                    
            except Exception as e:
                rprint(f"[red]Error: {str(e)}[/red]")
    
    asyncio.run(_search())


def display_organizations_table(organizations):
    """Display organizations in a formatted table."""
    table = Table(title="Partner Organizations")
    table.add_column("Name", style="cyan", no_wrap=True, min_width=20)
    table.add_column("Country", style="magenta", min_width=10)
    table.add_column("Type", style="green", min_width=10)
    table.add_column("Experience", style="yellow", min_width=12)
    table.add_column("Target Groups", style="blue", min_width=15)
    
    for org in organizations:
        table.add_row(
            org.name[:30] + "..." if len(org.name) > 30 else org.name,
            org.country,
            org.organization_type,
            org.experience_level,
            ", ".join(org.target_groups[:2]) + ("..." if len(org.target_groups) > 2 else "")
        )
    
    console.print(table)


def display_projects_table(projects):
    """Display projects in a formatted table."""
    table = Table(title="Project Opportunities")
    table.add_column("Title", style="cyan", no_wrap=True, min_width=25)
    table.add_column("Type", style="magenta", min_width=8)
    table.add_column("Countries", style="green", min_width=12)
    table.add_column("Deadline", style="red", min_width=10)
    table.add_column("Themes", style="blue", min_width=15)
    
    for project in projects:
        table.add_row(
            project.title[:35] + "..." if len(project.title) > 35 else project.title,
            project.project_type,
            ", ".join(project.countries_involved[:2]) + ("..." if len(project.countries_involved) > 2 else ""),
            project.deadline or "Not specified",
            ", ".join(project.themes[:2]) + ("..." if len(project.themes) > 2 else "")
        )
    
    console.print(table)


def display_json(result: SearchResponse):
    """Display results in JSON format."""
    rprint(json.dumps(result.dict(), indent=2, default=str))


def display_csv(results, data_type: str):
    """Display results in CSV format."""
    if data_type == "organizations":
        headers = ["Name", "Country", "Type", "Experience", "Target Groups", "Activity Types", "Profile URL"]
        for org in results:
            row = [
                org.name,
                org.country, 
                org.organization_type,
                org.experience_level,
                "; ".join(org.target_groups),
                "; ".join(org.activity_types),
                org.profile_url
            ]
            rprint(",".join(f'"{cell}"' for cell in row))
    else:
        headers = ["Title", "Type", "Countries", "Deadline", "Themes", "Contact Org", "Project URL"]
        for project in results:
            row = [
                project.title,
                project.project_type,
                "; ".join(project.countries_involved),
                project.deadline or "",
                "; ".join(project.themes),
                project.contact_organization,
                project.project_url
            ]
            rprint(",".join(f'"{cell}"' for cell in row))


def export_results(result: SearchResponse, output_file: Optional[str], format: str, search_type: str):
    """Export results to file."""
    if not output_file:
        timestamp = result.search_timestamp.replace(":", "-").split("T")[0]
        output_file = f"erasmus_{search_type}_{timestamp}.{format}"
    
    output_path = Path(output_file)
    
    try:
        if format == "json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result.dict(), f, indent=2, default=str)
        elif format == "csv":
            with open(output_path, 'w', encoding='utf-8') as f:
                if result.search_type == "organizations":
                    f.write("Name,Country,Type,Experience,Target Groups,Activity Types,Profile URL\n")
                    for org in result.results:
                        f.write(f'"{org.name}","{org.country}","{org.organization_type}","{org.experience_level}","{"; ".join(org.target_groups)}","{"; ".join(org.activity_types)}","{org.profile_url}"\n')
                else:
                    f.write("Title,Type,Countries,Deadline,Themes,Contact Org,Project URL\n")
                    for project in result.results:
                        f.write(f'"{project.title}","{project.project_type}","{"; ".join(project.countries_involved)}","{project.deadline or ""}","{"; ".join(project.themes)}","{project.contact_organization}","{project.project_url}"\n')
        
        rprint(f"[green]Results exported to {output_path}[/green]")
        
    except Exception as e:
        rprint(f"[red]Export failed: {str(e)}[/red]")


def suggest_alternatives(query: str, search_type: str):
    """Suggest alternative search strategies."""
    rprint("\n[blue]Try these suggestions:[/blue]")
    if search_type == "organizations":
        rprint("- Broaden your search terms")
        rprint("- Try searching without country filter")
        rprint("- Use more general activity types")
    else:
        rprint("- Check for recent project postings")
        rprint("- Try different project types (KA152, KA210, etc.)")
        rprint("- Search with broader themes")


if __name__ == "__main__":
    app()