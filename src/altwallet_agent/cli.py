"""CLI interface for AltWallet Checkout Agent."""

import json
import sys
import uuid
from decimal import Decimal
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .core import CheckoutAgent
from .logger import get_logger, set_trace_id
from .models import CheckoutRequest, Context
from .scoring import score_transaction

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
    user_id: str | None = typer.Option(None, "--user-id", "-u", help="User ID"),
    config_file: Path | None = typer.Option(None, "--config", help="Config file path"),
) -> None:
    """Process a checkout request and get card recommendations."""

    # Generate trace ID for this checkout
    trace_id = str(uuid.uuid4())
    set_trace_id(trace_id)
    logger = get_logger(__name__)

    console.print(
        Panel.fit(
            "[bold blue]AltWallet Checkout Agent[/bold blue]\n"
            f"Processing checkout for merchant: {merchant_id}",
            title="Checkout Processing",
        )
    )

    logger.info(
        "Starting checkout processing",
        merchant_id=merchant_id,
        amount=amount,
        currency=currency,
        user_id=user_id,
        trace_id=trace_id,
    )

    # Load configuration if provided
    config = {}
    if config_file and config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
        logger.debug("Configuration loaded from file", config_file=str(config_file))

    # Create agent
    agent = CheckoutAgent(config=config)

    # Create request
    request = CheckoutRequest(
        merchant_id=merchant_id,
        amount=Decimal(str(amount)),
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
        logger.info("Processing checkout request")
        response = agent.process_checkout(request)
        progress.update(task, completed=True)

    logger.info(
        "Checkout processing completed",
        response_status="success",
        recommendations_count=(
            len(response.recommendations) if hasattr(response, "recommendations") else 0
        ),
    )

    # Display results
    agent.display_recommendations(response)


@app.command()
def score(
    input_file: Path | None = typer.Option(
        None, "--input", "-i", help="Path to JSON input file"
    ),
    trace_id: str | None = typer.Option(
        None, "--trace-id", "-t", help="Trace ID (generates UUID v4 if omitted)"
    ),
    pretty: bool = typer.Option(
        False, "--pretty", "-p", help="Pretty-print JSON output"
    ),
) -> None:
    """
    Score a transaction using deterministic scoring v1.

    Reads JSON from --input file or stdin, parses into Context,
    runs scoring, and outputs single-line JSON result.
    """

    # Generate trace ID if not provided
    if not trace_id:
        trace_id = str(uuid.uuid4())

    # Set trace_id in context for logging
    set_trace_id(trace_id)

    # Get logger for this command
    logger = get_logger(__name__)

    try:
        # Read JSON input
        if input_file:
            if not input_file.exists():
                console.print(f"[red]Error: File {input_file} not found[/red]")
                raise typer.Exit(1)
            with open(input_file) as f:
                json_data = json.load(f)
        else:
            # Read from stdin
            json_data = json.load(sys.stdin)

        # Parse into Context using ingestion helper
        context = Context.from_json_payload(json_data)
        logger.info(
            "Context parsed successfully", context_keys=list(context.dict().keys())
        )

        # Run deterministic scoring
        logger.info("Starting transaction scoring")
        result = score_transaction(context)
        logger.info(
            "Scoring completed",
            final_score=result.final_score,
            routing_hint=result.routing_hint,
            risk_score=result.risk_score,
            loyalty_boost=result.loyalty_boost,
        )

        # Prepare output
        output = {
            "trace_id": trace_id,
            "risk_score": result.risk_score,
            "loyalty_boost": result.loyalty_boost,
            "final_score": result.final_score,
            "routing_hint": result.routing_hint,
            "signals": result.signals,
        }

        # Output JSON
        if pretty:
            json.dump(output, sys.stdout, indent=2)
        else:
            json.dump(output, sys.stdout, separators=(",", ":"))

        # Ensure newline at end
        print()

    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON input: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


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
