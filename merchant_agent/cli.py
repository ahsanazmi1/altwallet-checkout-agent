import json
import typer
from rich import print as rprint
from merchant_agent.core import Context, score_purchase

app = typer.Typer(add_completion=False, help="Merchant Agent CLI (starter)")

@app.command()
def demo(
    merchant: str = typer.Option(..., "-m", "--merchant", help="Merchant name"),
    amount: float = typer.Option(..., "-a", "--amount", help="Purchase amount (USD)"),
    location: str = typer.Option("New York", "-l", "--location", help="City/Region"),
    json_: bool = typer.Option(False, "--json", help="Output JSON"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
):
    """
    Run a deterministic demo recommendation (no external calls).
    """
    ctx = Context(merchant=merchant, amount=amount, location=location)
    result = score_purchase(ctx)

    if json_:
        typer.echo(json.dumps(result, indent=2))
    else:
        rprint(f"[bold]Recommended Card:[/bold] {result['recommended_card']}")
        rprint(f"[bold]Score:[/bold] {result['score']}")
        if verbose:
            rprint("[bold]Signals:[/bold]")
            for k, v in result["signals"].items():
                rprint(f"  - {k}: {v}")

if __name__ == "__main__":
    app()
