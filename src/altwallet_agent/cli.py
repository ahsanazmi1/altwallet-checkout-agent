"""CLI interface for AltWallet Checkout Agent."""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .core import CheckoutAgent
from .models import CheckoutRequest, ScoreRequest

app = typer.Typer(
    name="altwallet-agent",
    help="AltWallet Checkout Agent - Core Engine MVP",
    add_completion=False,
)
console = Console()


@app.command()
def checkout(
    merchant_id: str = typer.Option(..., "--merchant-id", "-m", help="Merchant ID"),
    amount: float = typer.Option(..., "--amount", "-a", help="Transaction amount"),
    currency: str = typer.Option("USD", "--currency", "-c", help="Currency code"),
    user_id: Optional[str] = typer.Option(None, "--user-id", "-u", help="User ID"),
    config_file: Optional[Path] = typer.Option(
        None, "--config", help="Config file path"
    ),
) -> None:
    """Process a checkout request and get card recommendations."""

    console.print(
        Panel.fit(
            "[bold blue]AltWallet Checkout Agent[/bold blue]\n"
            f"Processing checkout for merchant: {merchant_id}",
            title="Checkout Processing",
        )
    )

    # Load configuration if provided
    config = {}
    if config_file and config_file.exists():
        with open(config_file) as f:
            config = json.load(f)

    # Create agent
    agent = CheckoutAgent(config=config)

    # Create request
    request = CheckoutRequest(
        merchant_id=merchant_id,
        amount=amount,
        currency=currency,
        user_id=user_id,
    )

    # Process with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing checkout...", total=None)
        response = agent.process_checkout(request)
        progress.update(task, completed=True)

    # Display results
    agent.display_recommendations(response)


@app.command()
def score(
    transaction_file: Path = typer.Option(
        ..., "--file", "-f", help="Transaction data file"
    ),
    config_file: Optional[Path] = typer.Option(
        None, "--config", help="Config file path"
    ),
) -> None:
    """Score a transaction based on provided data."""

    console.print(
        Panel.fit(
            "[bold blue]AltWallet Checkout Agent[/bold blue]\n" "Scoring transaction",
            title="Transaction Scoring",
        )
    )

    # Load configuration if provided
    config = {}
    if config_file and config_file.exists():
        with open(config_file) as f:
            config = json.load(f)

    # Load transaction data
    if not transaction_file.exists():
        console.print(f"[red]Error: File {transaction_file} not found[/red]")
        raise typer.Exit(1)

    with open(transaction_file) as f:
        transaction_data = json.load(f)

    # Create agent
    agent = CheckoutAgent(config=config)

    # Create request
    request = ScoreRequest(transaction_data=transaction_data)

    # Process with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scoring transaction...", total=None)
        response = agent.score_transaction(request)
        progress.update(task, completed=True)

    # Display results
    console.print(f"\n[bold green]Score: {response.score:.3f}[/bold green]")
    console.print(f"[bold blue]Confidence: {response.confidence:.3f}[/bold blue]")
    console.print(f"[bold yellow]Factors: {', '.join(response.factors)}[/bold yellow]")


@app.command()
def version() -> None:
    """Show version information."""
    from . import __version__

    console.print(
        Panel.fit(
            f"[bold blue]AltWallet Checkout Agent[/bold blue]\n"
            f"Version: {__version__}\n"
            "Core Engine MVP",
            title="Version Info",
        )
    )


if __name__ == "__main__":
    app()
