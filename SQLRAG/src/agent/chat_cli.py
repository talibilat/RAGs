
from __future__ import annotations
import typer
import logging
from rich.console import Console
from rich.markdown import Markdown

from .chat_sql import answer_question
from core.config import settings, validate_config
from core.database import optimize_database_connections, check_database_health
from core.monitoring import graceful_shutdown, get_system_health, is_shutdown_requested

app = typer.Typer(add_completion=False)
console = Console()


@app.callback()
def main():
    """SQLRAG Agent with simplified configuration."""
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    
    # Reduce noisy transport logs
    for noisy_logger in ("httpx", "httpcore"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting SQLRAG Agent")
    
    # Validate configuration
    try:
        validate_config()
        logger.info("Configuration validated successfully")
    except Exception as exc:
        console.print(f"[red]Configuration error:[/red] {exc}")
        raise typer.Exit(1)
    
    # Optimize database
    try:
        optimize_database_connections()
        logger.info("Database optimized")
    except Exception as exc:
        console.print(f"[yellow]Database optimization warning:[/yellow] {exc}")


@app.command()
def chat():
    """Start interactive chat interface."""
    with graceful_shutdown():
        console.print("[bold blue]🤖 9fin SQL Agent[/bold blue]  •  type 'exit' to quit")
        console.print()
        
        while not is_shutdown_requested():
            try:
                # Get user input with better styling
                console.print("[bold cyan]👤 You:[/bold cyan]", end=" ")
                user = input().strip()
            except (EOFError, KeyboardInterrupt):
                break
            
            if not user:
                continue
            if user.lower() in {"exit", "quit"}:
                console.print("[bold yellow]👋 Goodbye![/bold yellow]")
                break
            
            # Display user question with clear formatting
            console.print()
            console.print("[bold cyan]📝 Question:[/bold cyan]")
            console.print(f"[italic]{user}[/italic]")
            console.print()
            
            try:
                # Show thinking indicator
                console.print("[bold blue]🤔 Agent:[/bold blue] [dim]Thinking...[/dim]")
                
                # Get answer (now handles both database and general questions)
                answer = answer_question(user)
                console.print()
                console.print("[bold green]✅ Answer:[/bold green]")
                console.print(Markdown(answer))
                console.print()
                console.print("[dim]" + "─" * 60 + "[/dim]")
                console.print()
                
            except Exception as exc:
                console.print()
                console.print(f"[bold red]❌ Error:[/bold red] {exc}")
                console.print()
                console.print("[dim]" + "─" * 60 + "[/dim]")
                console.print()


@app.command()
def health():
    """Check system health."""
    health_status = get_system_health()
    
    if health_status["status"] == "healthy":
        console.print("[green]✓ System is healthy[/green]")
    elif health_status["status"] == "degraded":
        console.print("[yellow]⚠ System is degraded[/yellow]")
    else:
        console.print("[red]✗ System is unhealthy[/red]")
    
    console.print(f"Timestamp: {health_status['timestamp']}")
    
    for component, status in health_status["components"].items():
        if status["status"] == "healthy":
            console.print(f"[green]✓ {component}[/green]")
        else:
            console.print(f"[red]✗ {component}: {status.get('error', 'Unknown error')}[/red]")


if __name__ == "__main__":
    app()
