"""CLI interface for AltWallet Merchant Agent."""

import json
from decimal import Decimal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .core import CardRecommender, Purchase

app = typer.Typer(
    name="altwallet-merchant-agent",
    help="AltWallet Agent for Merchant - Get the best card recommendation for your purchase",
    add_completion=False,
)
console = Console()


@app.command()
def recommend(
    amount: float = typer.Argument(..., help="Purchase amount in dollars"),
    category: str = typer.Option(
        "general",
        "--category",
        "-c",
        help="Purchase category (e.g., groceries, travel, gas)",
    ),
    merchant: str = typer.Option("Unknown", "--merchant", "-m", help="Merchant name"),
):
    """Get the best card recommendation for a purchase."""
    try:
        # Create purchase object
        purchase = Purchase(
            amount=Decimal(str(amount)), category=category.lower(), merchant=merchant
        )

        # Get recommendation
        recommender = CardRecommender()
        best_card = recommender.get_best_card(purchase)

        # Calculate cashback
        if best_card.category_bonus and best_card.category_bonus in purchase.category:
            effective_rate = best_card.cashback_rate * best_card.category_multiplier
            bonus_text = f" (includes {best_card.category_multiplier}x category bonus)"
        else:
            effective_rate = best_card.cashback_rate
            bonus_text = ""

        cashback_amount = purchase.amount * effective_rate

        # Display results
        display_recommendation(
            purchase, best_card, cashback_amount, effective_rate, bonus_text
        )

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def _demo_logic(
    merchant: str,
    amount: float,
    location: str = "New York",
    json_output: bool = False,
    verbose: bool = False,
    p_approval: float = 0.95,
    geo_promo: bool = False,
):
    """Internal demo logic that can be called directly by tests."""
    try:
        # Validate p_approval range
        if not 0 <= p_approval <= 1:
            raise ValueError("p_approval must be between 0 and 1")

        # Compute deterministic demo result
        base_reward_rate = Decimal("0.03")  # 3% base reward
        merchant_penalty = Decimal("0")  # 0 merchant penalty

        # Calculate rewards and penalties
        rewards_value_usd = Decimal(str(amount)) * base_reward_rate
        merchant_penalty_usd = merchant_penalty

        # Apply geographic promotion if enabled
        geo_promo_bonus = Decimal("1.50") if geo_promo else Decimal("0")
        rewards_value_usd += geo_promo_bonus

        # Calculate final score (rewards minus penalties, then apply p_approval multiplier)
        base_score = float(rewards_value_usd - merchant_penalty_usd)
        score = base_score * p_approval

        # Create signals dictionary
        signals = {
            "merchant": merchant,
            "location": location,
            "rewards_value_usd": float(rewards_value_usd),
            "merchant_penalty_usd": float(merchant_penalty_usd),
            "p_approval_used": p_approval,
            "geo_promo_applied": geo_promo,
        }

        # Determine recommended card (deterministic based on merchant name)
        recommended_card = get_demo_card(merchant)

        if json_output:
            # Output as JSON
            result = {
                "recommended_card": recommended_card,
                "score": score,
                "signals": signals,
            }
            console.print(json.dumps(result, indent=2))
        else:
            # Human-readable output
            display_demo_result(recommended_card, score, signals, verbose)

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def demo(
    merchant: str = typer.Option(..., "--merchant", "-m", help="Merchant name"),
    amount: float = typer.Option(..., "--amount", "-a", help="Purchase amount in USD"),
    location: str = typer.Option("New York", "--location", "-l", help="Location"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    p_approval: float = typer.Option(
        0.95, "--p-approval", help="Probability approval multiplier (0-1, default 0.95)"
    ),
    geo_promo: bool = typer.Option(
        False, "--geo-promo", help="Apply geographic promotion bonus"
    ),
):
    """Get a deterministic demo recommendation with pretend rewards and penalties."""
    _demo_logic(merchant, amount, location, json_output, verbose, p_approval, geo_promo)


def get_demo_card(merchant: str) -> str:
    """Get deterministic demo card based on merchant name."""
    merchant_lower = merchant.lower()

    if any(word in merchant_lower for word in ["grocery", "food", "market", "fresh"]):
        return "Amex Blue Cash Preferred"
    elif any(
        word in merchant_lower for word in ["travel", "airline", "hotel", "booking"]
    ):
        return "Chase Sapphire Preferred"
    elif any(word in merchant_lower for word in ["gas", "fuel", "station"]):
        return "Chase Freedom Unlimited"
    else:
        return "Citi Double Cash"


def display_demo_result(
    recommended_card: str, score: float, signals: dict, verbose: bool
):
    """Display demo result in human-readable format."""

    # Create main panel
    title = Text("🎯 AltWallet Demo Recommendation", style="bold green")
    panel = Panel(
        f"[bold green]Recommended Card:[/bold green] {recommended_card}\n"
        f"[bold]Score:[/bold] {score:.2f}",
        title=title,
        border_style="green",
    )

    console.print(panel)

    if verbose:
        # Display each signal on its own line
        console.print("\n[bold cyan]Signals:[/bold cyan]")
        for key, value in signals.items():
            if isinstance(value, float):
                console.print(f"  {key.replace('_', ' ').title()}: ${value:.2f}")
            else:
                console.print(f"  {key.replace('_', ' ').title()}: {value}")
    else:
        # Display signals in a compact table
        table = Table(title="Signals")
        table.add_column("Signal", style="cyan")
        table.add_column("Value", style="magenta")

        for key, value in signals.items():
            if isinstance(value, float):
                table.add_row(key.replace("_", " ").title(), f"${value:.2f}")
            else:
                table.add_row(key.replace("_", " ").title(), str(value))

        console.print(table)


def display_recommendation(
    purchase: Purchase,
    card,
    cashback_amount: Decimal,
    effective_rate: Decimal,
    bonus_text: str,
):
    """Display the recommendation in a beautiful format."""

    # Create main panel
    title = Text("💳 AltWallet Card Recommendation", style="bold blue")
    panel = Panel(
        f"[bold green]Recommended Card:[/bold green] {card.name}\n"
        f"[bold]Purchase:[/bold] ${purchase.amount:,.2f} at {purchase.merchant}\n"
        f"[bold]Category:[/bold] {purchase.category.title()}\n"
        f"[bold]Cashback Rate:[/bold] {effective_rate:.1%}{bonus_text}\n"
        f"[bold green]Cashback Amount:[/bold green] ${cashback_amount:.2f}",
        title=title,
        border_style="blue",
    )

    console.print(panel)

    # Create card details table
    table = Table(title="Card Details")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Card Name", card.name)
    table.add_row("Base Cashback Rate", f"{card.cashback_rate:.1%}")
    table.add_row("Annual Fee", f"${card.annual_fee}")
    if card.category_bonus:
        table.add_row(
            "Category Bonus",
            f"{card.category_bonus.title()} ({card.category_multiplier}x)",
        )

    console.print(table)


@app.command()
def version():
    """Show version information."""
    from . import __version__

    console.print(f"AltWallet Merchant Agent v{__version__}")


if __name__ == "__main__":
    app()
