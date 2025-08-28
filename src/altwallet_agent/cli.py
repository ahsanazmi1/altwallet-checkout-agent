"""CLI interface for AltWallet Checkout Agent."""

import json
import sys
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .composite_utility import CompositeUtility
from .core import CheckoutAgent
from .logger import get_logger, set_request_start_time, set_trace_id
from .models import CheckoutRequest, Context
from .scoring import score_transaction

app = typer.Typer(
    name="altwallet-agent",
    help="AltWallet Checkout Agent - Core Engine MVP",
    add_completion=False,
)
console = Console()


def create_sample_cards() -> list[dict[str, Any]]:
    """Create sample cards for demonstration."""
    return [
        {
            "card_id": "chase_sapphire_preferred",
            "name": "Chase Sapphire Preferred",
            "cashback_rate": 0.01,
            "category_bonuses": {
                "4511": 2.0,  # Airlines
                "5812": 2.0,  # Restaurants
            },
            "issuer": "chase",
            "annual_fee": 95,
            "rewards_type": "points",
        },
        {
            "card_id": "amex_gold",
            "name": "American Express Gold",
            "cashback_rate": 0.04,
            "category_bonuses": {
                "5812": 4.0,  # Restaurants
                "5411": 4.0,  # Grocery stores
            },
            "issuer": "american_express",
            "annual_fee": 250,
            "rewards_type": "points",
        },
        {
            "card_id": "citi_double_cash",
            "name": "Citi Double Cash",
            "cashback_rate": 0.02,
            "category_bonuses": {},
            "issuer": "citi",
            "annual_fee": 0,
            "rewards_type": "cashback",
        },
        {
            "card_id": "chase_freedom_unlimited",
            "name": "Chase Freedom Unlimited",
            "cashback_rate": 0.015,
            "category_bonuses": {
                "5411": 3.0,  # Grocery stores
            },
            "issuer": "chase",
            "annual_fee": 0,
            "rewards_type": "cashback",
        },
    ]


def get_top_drivers(
    attributions: dict[str, Any], max_drivers: int = 5
) -> list[dict[str, Any]]:
    """Extract top positive and negative drivers from attributions."""
    if not attributions:
        return []

    # Extract feature contributions
    drivers = []

    # Add scoring signals as drivers
    if "signals" in attributions:
        signals = attributions["signals"]
        if signals.get("location_mismatch"):
            drivers.append(
                {"feature": "location_mismatch", "value": -30, "impact": "negative"}
            )
        if signals.get("velocity_flag"):
            drivers.append(
                {"feature": "high_velocity_24h", "value": -20, "impact": "negative"}
            )
        if signals.get("chargebacks_present"):
            drivers.append(
                {"feature": "chargebacks_12m", "value": -25, "impact": "negative"}
            )
        if signals.get("high_ticket"):
            drivers.append(
                {"feature": "high_ticket_amount", "value": -10, "impact": "negative"}
            )

    # Add loyalty boost as positive driver
    if "loyalty_boost" in attributions:
        loyalty_boost = attributions.get("loyalty_boost", 0)
        if loyalty_boost > 0:
            drivers.append(
                {
                    "feature": "loyalty_tier_boost",
                    "value": loyalty_boost,
                    "impact": "positive",
                }
            )

    # Sort by absolute value and take top drivers
    def get_abs_value(x: dict[str, Any]) -> float:
        value = x["value"]
        if isinstance(value, (int, float)):
            return abs(value)
        return 0.0

    drivers.sort(key=get_abs_value, reverse=True)
    return drivers[:max_drivers]


def create_audit_block(
    context: Context, score_result: Any, utility_result: dict[str, Any]
) -> dict[str, Any]:
    """Create audit block with detailed scoring information."""
    return {
        "scoring_audit": {
            "risk_score": score_result.risk_score,
            "loyalty_boost": score_result.loyalty_boost,
            "final_score": score_result.final_score,
            "routing_hint": score_result.routing_hint,
            "signals": score_result.signals,
        },
        "utility_audit": {
            "components": utility_result.get("components", {}),
            "score_result": utility_result.get("score_result", {}),
            "context_info": utility_result.get("context_info", {}),
        },
        "transaction_context": {
            "merchant": {
                "name": (context.merchant.name if context.merchant else "Unknown"),
                "mcc": context.merchant.mcc if context.merchant else "Unknown",
                "network_preferences": (
                    context.merchant.network_preferences if context.merchant else []
                ),
            },
            "cart": {
                "total": float(context.cart.total) if context.cart else 0.0,  # type: ignore[arg-type]
                "currency": context.cart.currency if context.cart else "USD",
                "item_count": len(context.cart.items) if context.cart else 0,
            },
            "customer": {
                "loyalty_tier": context.customer.loyalty_tier.value,
                "velocity_24h": context.customer.historical_velocity_24h,
                "chargebacks_12m": context.customer.chargebacks_12m,
            },
        },
    }


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

    # Set request start time for latency tracking
    set_request_start_time()

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
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON with card recommendations",
    ),
    verbose: bool = typer.Option(
        False, "-vv", help="Enable verbose logging (JSON logs to stdout only when set)"
    ),
) -> None:
    """
    Score a transaction using deterministic scoring v1.

    Reads JSON from --input file or stdin, parses into Context,
    runs scoring, and outputs single-line JSON result.

    With --json flag, outputs comprehensive card recommendations including
    p_approval, expected_rewards, utility, top drivers, and audit block.
    """

    # Generate trace ID if not provided
    if not trace_id:
        trace_id = str(uuid.uuid4())

    # Set trace_id in context for logging
    set_trace_id(trace_id)

    # Set request start time for latency tracking
    set_request_start_time()

    # Get logger for this command
    logger = get_logger(__name__)

    # Configure logging based on verbosity
    if not verbose:
        # Suppress info and debug logs when not verbose
        import logging

        logging.getLogger().setLevel(logging.WARNING)

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

        if json_output:
            # Generate comprehensive card recommendations
            utility = CompositeUtility()
            cards = create_sample_cards()

            # Calculate utility for each card
            card_recommendations = []
            for card in cards:
                card_utility = utility.calculate_card_utility(card, context)

                # Get top drivers
                top_drivers = get_top_drivers(card_utility.get("score_result", {}))

                # Create audit block
                audit_block = create_audit_block(context, result, card_utility)

                card_recommendation = {
                    "card_id": card["card_id"],
                    "card_name": card["name"],
                    "p_approval": card_utility["components"]["p_approval"],
                    "expected_rewards": card_utility["components"]["expected_rewards"],
                    "utility": card_utility["utility_score"],
                    "top_drivers": top_drivers,
                    "audit": audit_block,
                }
                card_recommendations.append(card_recommendation)

            # Sort by utility (highest first)
            card_recommendations.sort(key=lambda x: x["utility"], reverse=True)

            # Prepare comprehensive output
            output = {
                "trace_id": trace_id,
                "risk_score": result.risk_score,
                "loyalty_boost": result.loyalty_boost,
                "final_score": result.final_score,
                "routing_hint": result.routing_hint,
                "signals": result.signals,
                "card_recommendations": card_recommendations,
            }
        else:
            # Prepare basic output
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
