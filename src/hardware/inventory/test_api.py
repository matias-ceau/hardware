"""Interactive API testing for OCR services and database operations."""

import argparse
import os
import tempfile
import json
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import utils
from . import config

console = Console()


def test_api_keys():
    """Test API key availability and display status."""
    console.print("\n[bold cyan]API Key Status[/]")
    
    api_keys = {
        "Mistral": os.getenv("MISTRAL_API_KEY"),
        "OpenAI": os.getenv("OPENAI_API_KEY"),
        "OpenRouter": os.getenv("OPENROUTER_API_KEY"),
        "OCR.Space": os.getenv("OCR_SPACE_API_KEY"),
    }
    
    table = Table()
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Key Preview", style="dim")
    
    for service, key in api_keys.items():
        if key:
            status = "[green]✓ Available[/]"
            preview = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else key[:8] + "..."
        else:
            status = "[red]✗ Missing[/]"
            preview = "[dim]Not set[/]"
        
        table.add_row(service, status, preview)
    
    console.print(table)
    return api_keys


def test_database_operations():
    """Test database operations with example data."""
    console.print("\n[bold cyan]Database Operations Test[/]")
    
    # Check for example data
    example_data = Path(__file__).parent.parent.parent.parent / "data" / "electronics_updated_1.jsonld"
    
    if not example_data.exists():
        console.print("[red]Example database not found at data/electronics_updated_1.jsonld[/]")
        return False
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Create temporary database
            temp_db = Path(tempfile.mkdtemp()) / "test_inventory.db"
            
            task = progress.add_task("Creating test database...", total=None)
            db = utils.SQLiteDB(temp_db)
            
            progress.update(task, description="Importing example data...")
            db.import_db(example_data)
            
            progress.update(task, description="Testing database operations...")
            
            # Test basic operations
            stats = db.get_stats()
            components = db.list_all(limit=5)
            search_results = db.search("resistor")
            
            progress.update(task, description="Complete!", completed=100)
        
        # Display results
        console.print(f"[green]✓ Database test successful[/]")
        console.print(f"Total components: {stats['total_components']}")
        console.print(f"Component types: {len(stats.get('types', {}))}")
        console.print(f"Search results for 'resistor': {len(search_results)}")
        
        # Cleanup
        temp_db.unlink()
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Database test failed: {e}[/]")
        return False


def test_ocr_parsing():
    """Test OCR text parsing functionality."""
    console.print("\n[bold cyan]OCR Text Parsing Test[/]")
    
    test_texts = [
        "10kΩ resistor ±5% tolerance Carbon film 25 pieces $0.05 each",
        "100uF electrolytic capacitor 16V 50 pcs €1.20",
        "BC547 NPN transistor TO-92 package 10 pieces",
        "LM358 dual op-amp DIP-8 package 5 pcs $0.75",
        "1N4148 switching diode DO-35 100 pieces",
    ]
    
    table = Table()
    table.add_column("Input Text", style="white", width=40)
    table.add_column("Parsed Fields", style="cyan")
    
    for text in test_texts:
        parsed = utils.parse_fields(text)
        parsed_str = json.dumps(parsed, indent=None) if parsed else "[dim]No fields parsed[/]"
        table.add_row(text[:37] + "..." if len(text) > 40 else text, parsed_str)
    
    console.print(table)
    console.print("[green]✓ OCR parsing test complete[/]")


def interactive_ocr_test():
    """Interactive OCR service testing."""
    console.print("\n[bold cyan]Interactive OCR Service Test[/]")
    
    # Check available APIs
    available_services = []
    if os.getenv("MISTRAL_API_KEY"):
        available_services.append("mistral")
    if os.getenv("OPENAI_API_KEY"):
        available_services.append("openai")
    if os.getenv("OPENROUTER_API_KEY"):
        available_services.append("openrouter")
    
    if not available_services:
        console.print("[yellow]No API keys found for testing. Set MISTRAL_API_KEY, OPENAI_API_KEY, or OPENROUTER_API_KEY[/]")
        return
    
    console.print(f"Available services: {', '.join(available_services)}")
    
    # Get test image path
    image_path = Prompt.ask("Enter path to test image (or press Enter to skip)")
    if not image_path or not Path(image_path).exists():
        console.print("[yellow]Skipping OCR test - no valid image provided[/]")
        return
    
    image_path = Path(image_path)
    
    # Test each available service
    for service in available_services:
        if Confirm.ask(f"Test {service} OCR service?"):
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn(f"[progress.description]Testing {service}..."),
                    console=console
                ) as progress:
                    task = progress.add_task("Processing image...", total=None)
                    
                    result = utils.ocr_extract(image_path, service)
                    
                    progress.update(task, description="Complete!", completed=100)
                
                console.print(Panel(
                    result[:500] + "..." if len(result) > 500 else result,
                    title=f"{service.title()} OCR Result",
                    border_style="green"
                ))
                
                # Parse fields from result
                parsed = utils.parse_fields(result)
                if parsed:
                    console.print(f"Parsed fields: {json.dumps(parsed, indent=2)}")
                
            except Exception as e:
                console.print(f"[red]✗ {service} OCR failed: {e}[/]")


def test_component_search():
    """Test component search with different queries."""
    console.print("\n[bold cyan]Component Search Test[/]")
    
    # Use example database if available
    example_data = Path(__file__).parent.parent.parent.parent / "data" / "electronics_updated_1.jsonld"
    
    if not example_data.exists():
        console.print("[yellow]Example database not found - skipping search test[/]")
        return
    
    try:
        # Create temporary database with example data
        temp_db = Path(tempfile.mkdtemp()) / "test_search.db"
        db = utils.SQLiteDB(temp_db)
        db.import_db(example_data)
        
        test_queries = [
            "resistor",
            "10k",
            "capacitor",
            "uF",
            "transistor",
            "ceramic"
        ]
        
        table = Table()
        table.add_column("Query", style="cyan")
        table.add_column("Results", style="white")
        table.add_column("Sample Component", style="dim")
        
        for query in test_queries:
            results = db.search(query)
            count = len(results)
            sample = results[0].get("description", "N/A")[:30] + "..." if results else "No results"
            table.add_row(query, str(count), sample)
        
        console.print(table)
        console.print("[green]✓ Search test complete[/]")
        
        # Cleanup
        temp_db.unlink()
        
    except Exception as e:
        console.print(f"[red]✗ Search test failed: {e}[/]")


def main():
    """Main test interface."""
    parser = argparse.ArgumentParser(description="Interactive API and database testing")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--api-keys", action="store_true", help="Test API key availability")
    parser.add_argument("--database", action="store_true", help="Test database operations")
    parser.add_argument("--parsing", action="store_true", help="Test OCR text parsing")
    parser.add_argument("--ocr", action="store_true", help="Interactive OCR testing")
    parser.add_argument("--search", action="store_true", help="Test component search")
    
    args = parser.parse_args()
    
    console.print(Panel.fit(
        "[bold cyan]Hardware Inventory API & Database Testing[/]",
        border_style="cyan"
    ))
    
    if args.all or not any([args.api_keys, args.database, args.parsing, args.ocr, args.search]):
        # Run all tests if no specific test requested
        test_api_keys()
        test_database_operations()
        test_ocr_parsing()
        test_component_search()
        
        if Confirm.ask("\nRun interactive OCR test with real APIs?"):
            interactive_ocr_test()
    else:
        if args.api_keys:
            test_api_keys()
        if args.database:
            test_database_operations()
        if args.parsing:
            test_ocr_parsing()
        if args.search:
            test_component_search()
        if args.ocr:
            interactive_ocr_test()
    
    console.print("\n[bold green]Testing complete![/]")


if __name__ == "__main__":
    main()