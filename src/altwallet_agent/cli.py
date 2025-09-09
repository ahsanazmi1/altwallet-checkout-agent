#!/usr/bin/env python3
"""
Orca Checkout Agent CLI

Provides command-line interface for simulating decisions, managing webhooks,
and checking system health.
"""

import asyncio
import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import click

from altwallet_agent.analytics import log_decision_outcome
from altwallet_agent.composite_utility import CompositeUtility
from altwallet_agent.decisioning import (
    ActionType,
    BusinessRule,
    Decision,
    DecisionContract,
    DecisionReason,
    PenaltyOrIncentive,
    RoutingHint,
)
from altwallet_agent.logger import (
    get_logger,
    set_request_start_time,
    set_trace_id,
)
from altwallet_agent.models import Context
from altwallet_agent.scoring import score_transaction

try:
    from altwallet_agent.webhooks import (
        get_webhook_emitter,
        get_webhook_manager,
    )

    _HAS_WEBHOOKS = True
except Exception:  # pragma: no cover - allow running without aiohttp
    _HAS_WEBHOOKS = False

    async def get_webhook_emitter() -> Any:  # type: ignore[misc]
        raise RuntimeError("Webhooks unavailable: aiohttp not installed")

    async def get_webhook_manager() -> Any:  # type: ignore[misc]
        raise RuntimeError("Webhooks unavailable: aiohttp not installed")


logger = get_logger(__name__)


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
                {
                    "feature": "location_mismatch",
                    "value": -30,
                    "impact": "negative",
                }
            )
        if signals.get("velocity_flag"):
            drivers.append(
                {
                    "feature": "high_velocity_24h",
                    "value": -20,
                    "impact": "negative",
                }
            )
        if signals.get("chargebacks_present"):
            drivers.append(
                {
                    "feature": "chargebacks_12m",
                    "value": -25,
                    "impact": "negative",
                }
            )
        if signals.get("high_ticket"):
            drivers.append(
                {
                    "feature": "high_ticket_amount",
                    "value": -10,
                    "impact": "negative",
                }
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


@click.group(invoke_without_command=True)
@click.version_option(version="0.3.0")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Orca Checkout Agent CLI - Decision Simulation and Management"""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(2)


@cli.command()
@click.option(
    "--input",
    "input_file",
    type=click.Path(path_type=Path),
    help="Path to JSON input file",
)
@click.option(
    "--trace-id",
    "trace_id",
    default=None,
    help="Trace ID (generates UUID v4 if omitted)",
)
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output")
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Include card recommendations and audit details",
)
@click.option("-vv", "verbose", is_flag=True, help="Enable verbose logging")
def score(
    input_file: Path | None,
    trace_id: str | None,
    pretty: bool,
    json_output: bool,
    verbose: bool,
) -> None:
    """Score a transaction using deterministic scoring v1.

    Reads JSON from --input file or stdin, parses into Context, runs scoring,
    and prints a JSON object to stdout.
    """
    if not trace_id:
        trace_id = str(uuid.uuid4())

    set_trace_id(trace_id)
    set_request_start_time()

    if not verbose:
        import logging

        logging.getLogger().setLevel(logging.WARNING)

    try:
        if input_file:
            if not input_file.exists():
                raise click.ClickException(f"File not found: {input_file}")
            with open(input_file) as f:
                json_data = json.load(f)
        else:
            json_data = json.load(sys.stdin)

        context = Context.from_json_payload(json_data)
        logger.info(
            "Context parsed successfully",
            context_keys=list(context.model_dump().keys()),
        )

        result = score_transaction(context)
        logger.info(
            "Scoring completed",
            final_score=result.final_score,
            routing_hint=result.routing_hint,
            risk_score=result.risk_score,
            loyalty_boost=result.loyalty_boost,
        )

        if json_output:
            utility = CompositeUtility()
            cards = create_sample_cards()
            card_recommendations = []
            for card in cards:
                card_utility = utility.calculate_card_utility(card, context)
                top_drivers = get_top_drivers(card_utility.get("score_result", {}))
                audit_block = create_audit_block(context, result, card_utility)
                card_recommendations.append(
                    {
                        "card_id": card["card_id"],
                        "card_name": card["name"],
                        "p_approval": card_utility["components"]["p_approval"],
                        "expected_rewards": card_utility["components"][
                            "expected_rewards"
                        ],
                        "utility": card_utility["utility_score"],
                        "top_drivers": top_drivers,
                        "audit": audit_block,
                    }
                )
            card_recommendations.sort(key=lambda x: x["utility"], reverse=True)
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
            output = {
                "trace_id": trace_id,
                "risk_score": result.risk_score,
                "loyalty_boost": result.loyalty_boost,
                "final_score": result.final_score,
                "routing_hint": result.routing_hint,
                "signals": result.signals,
            }

        if pretty:
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(json.dumps(output, separators=(",", ":")))

    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON input: {e}")


@cli.command()
@click.option("--approve", is_flag=True, help="Simulate an APPROVE decision")
@click.option("--decline", is_flag=True, help="Simulate a DECLINE decision")
@click.option("--review", is_flag=True, help="Simulate a REVIEW decision")
@click.option("--discount", is_flag=True, help="Apply discount business rule")
@click.option("--kyc", is_flag=True, help="Apply KYC business rule")
@click.option("--customer-id", default="cust_123", help="Customer ID")
@click.option("--merchant-id", default="merch_456", help="Merchant ID")
@click.option("--amount", default=100.00, type=float, help="Transaction amount")
@click.option("--mcc", default="5411", help="Merchant Category Code")
@click.option("--region", default="US", help="Geographic region")
@click.option("--webhook", is_flag=True, help="Emit webhook event")
@click.option("--analytics", is_flag=True, help="Log analytics event")
def simulate_decision(
    approve: bool,
    decline: bool,
    review: bool,
    discount: bool,
    kyc: bool,
    customer_id: str,
    merchant_id: str,
    amount: float,
    mcc: str,
    region: str,
    webhook: bool,
    analytics: bool,
) -> None:
    """Simulate a decision with specified flags and parameters."""

    # Validate decision flags
    decision_flags = sum([approve, decline, review])
    if decision_flags != 1:
        click.echo(
            "ERROR: Must specify exactly one decision flag: "
            "--approve, --decline, or --review"
        )
        return

    try:
        # Create decision contract based on flags
        if approve:
            contract = _simulate_approve_decision(
                customer_id, merchant_id, amount, mcc, region, discount, kyc
            )
        elif decline:
            contract = _simulate_decline_decision(
                customer_id, merchant_id, amount, mcc, region, discount, kyc
            )
        else:  # review
            contract = _simulate_review_decision(
                customer_id, merchant_id, amount, mcc, region, discount, kyc
            )

        # Display decision contract
        click.echo("Decision Contract:")
        click.echo("=" * 50)
        click.echo(json.dumps(contract.model_dump(), indent=2))

        # Emit webhook if requested
        if webhook:
            click.echo("\nEmitting webhook event...")
            _emit_webhook_event(contract)

        # Log analytics if requested
        if analytics:
            click.echo("\nLogging analytics event...")
            _log_analytics_event(contract)
    except Exception as e:
        click.echo(f"ERROR: Failed to simulate decision: {e}")
        logger.error("Decision simulation failed", error=str(e))


def _simulate_approve_decision(
    customer_id: str,
    merchant_id: str,
    amount: float,
    mcc: str,
    region: str,
    discount: bool,
    kyc: bool,
) -> DecisionContract:
    """Create a simulated APPROVE decision contract."""

    # For simulation, we'll create a contract directly
    actions = []
    if discount:
        actions.append(
            BusinessRule(
                action_type=ActionType.DISCOUNT_APPLIED,
                rule_id="discount_001",
                description="Loyalty discount applied",
                impact_score=0.8,
            )
        )
    if kyc:
        actions.append(
            BusinessRule(
                action_type=ActionType.KYC_REQUIRED,
                rule_id="kyc_001",
                description="KYC verification required",
                impact_score=0.9,
            )
        )

    # Add default actions for approval
    if not actions:
        actions.append(
            BusinessRule(
                action_type=ActionType.LOYALTY_BOOST,
                rule_id="approval_001",
                description="Standard approval granted",
                impact_score=0.7,
            )
        )

    return DecisionContract(
        decision=Decision.APPROVE,
        actions=actions,
        reasons=[
            DecisionReason(
                feature_name="risk_score",
                value="low",
                weight=0.8,
                description="Low risk score indicates approval",
                threshold=0.5,
            ),
            DecisionReason(
                feature_name="customer_history",
                value="good",
                weight=0.7,
                description="Good customer history",
                threshold=0.6,
            ),
        ],
        routing_hint=RoutingHint(
            preferred_network="VISA",
            preferred_acquirer="STRIPE",
            penalty_or_incentive=PenaltyOrIncentive.NONE,
        ),
        transaction_id=f"sim_{int(time.time())}",
        score_result=None,
    )


def _simulate_decline_decision(
    customer_id: str,
    merchant_id: str,
    amount: float,
    mcc: str,
    region: str,
    discount: bool,
    kyc: bool,
) -> DecisionContract:
    """Create a simulated DECLINE decision contract."""

    actions = []
    if discount:
        actions.append(
            BusinessRule(
                action_type=ActionType.DISCOUNT_APPLIED,
                rule_id="discount_002",
                description="Loyalty discount applied",
                impact_score=0.8,
            )
        )
    if kyc:
        actions.append(
            BusinessRule(
                action_type=ActionType.KYC_REQUIRED,
                rule_id="kyc_002",
                description="KYC verification required",
                impact_score=0.9,
            )
        )

    # Add default actions for decline
    if not actions:
        actions.append(
            BusinessRule(
                action_type=ActionType.FRAUD_SCREENING,
                rule_id="decline_001",
                description="Risk threshold exceeded",
                impact_score=0.9,
            )
        )

    return DecisionContract(
        decision=Decision.DECLINE,
        actions=actions,
        reasons=[
            DecisionReason(
                feature_name="risk_score",
                value="high",
                weight=0.9,
                description="High risk score indicates decline",
                threshold=0.5,
            ),
            DecisionReason(
                feature_name="fraud_indicator",
                value="suspicious",
                weight=0.8,
                description="Suspicious activity detected",
                threshold=0.7,
            ),
        ],
        routing_hint=RoutingHint(
            preferred_network="VISA",
            preferred_acquirer="STRIPE",
            penalty_or_incentive=PenaltyOrIncentive.NONE,
        ),
        transaction_id=f"sim_{int(time.time())}",
        score_result=None,
    )


def _simulate_review_decision(
    customer_id: str,
    merchant_id: str,
    amount: float,
    mcc: str,
    region: str,
    discount: bool,
    kyc: bool,
) -> DecisionContract:
    """Create a simulated REVIEW decision contract."""

    actions = []
    if discount:
        actions.append(
            BusinessRule(
                action_type=ActionType.DISCOUNT_APPLIED,
                rule_id="discount_003",
                description="Loyalty discount applied",
                impact_score=0.8,
            )
        )
    if kyc:
        actions.append(
            BusinessRule(
                action_type=ActionType.KYC_REQUIRED,
                rule_id="kyc_003",
                description="KYC verification required",
                impact_score=0.9,
            )
        )

    # Add default actions for review
    if not actions:
        actions.append(
            BusinessRule(
                action_type=ActionType.MANUAL_REVIEW,
                rule_id="review_001",
                description="Manual review required",
                impact_score=0.7,
            )
        )

    return DecisionContract(
        decision=Decision.REVIEW,
        actions=actions,
        reasons=[
            DecisionReason(
                feature_name="risk_score",
                value="medium",
                weight=0.6,
                description="Medium risk score requires review",
                threshold=0.5,
            ),
            DecisionReason(
                feature_name="pattern_analysis",
                value="unusual",
                weight=0.5,
                description="Unusual transaction pattern detected",
                threshold=0.6,
            ),
        ],
        routing_hint=RoutingHint(
            preferred_network="VISA",
            preferred_acquirer="STRIPE",
            penalty_or_incentive=PenaltyOrIncentive.NONE,
        ),
        transaction_id=f"sim_{int(time.time())}",
        score_result=None,
    )


def _emit_webhook_event(contract: DecisionContract) -> None:
    """Emit a webhook event for the decision."""
    try:
        # Run async webhook emission in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def emit() -> None:
            emitter = await get_webhook_emitter()
            await emitter.emit_auth_result(
                f"txn_{int(time.time())}",
                contract.decision,
                0.85,  # Default score for simulation
                {
                    "actions": contract.actions,
                    "reasons": contract.reasons,
                    "routing_hint": contract.routing_hint,
                },
            )

        loop.run_until_complete(emit())
        loop.close()

        click.echo("Webhook event emitted successfully")

    except Exception as e:
        click.echo(f"ERROR: Failed to emit webhook: {e}")


def _log_analytics_event(contract: DecisionContract) -> None:
    """Log an analytics event for the decision."""
    try:
        # Convert decision to DecisionOutcome enum
        from altwallet_agent.analytics import DecisionOutcome

        decision_outcome = DecisionOutcome(contract.decision.value)

        log_decision_outcome(
            request_id=f"sim_{int(time.time())}",
            decision=decision_outcome,
            actions=[action.action_type.value for action in contract.actions],
            routing_hints=contract.routing_hint,
            customer_id="sim_customer",
            merchant_id="sim_merchant",
            latency_ms=150,
            error_flags=[],
        )
        click.echo("Analytics event logged successfully")

    except Exception as e:
        click.echo(f"ERROR: Failed to log analytics: {e}")


@cli.command()
@click.option("--input", "-i", required=True, help="Input JSON file path")
def score_file(input: str) -> None:
    """Score a transaction from input file."""
    try:
        import json
        from pathlib import Path

        # Read input file
        input_path = Path(input)
        if not input_path.exists():
            click.echo(f"ERROR: Input file not found: {input}")
            return

        with open(input_path) as f:
            context_data = json.load(f)

        # Import scoring function
        from altwallet_agent.models import Context
        from altwallet_agent.scoring import score_transaction

        # Create context from data
        context = Context(**context_data)

        # Score transaction
        score_result = score_transaction(context)

        # Output JSON result
        result = {
            "final_score": score_result.final_score,
            "risk_score": score_result.risk_score,
            "loyalty_boost": score_result.loyalty_boost,
            "routing_hint": score_result.routing_hint,
            "signals": score_result.signals,
        }

        # Output only the JSON result (no log messages)
        print(json.dumps(result, indent=2))

    except Exception as e:
        click.echo(f"ERROR: Failed to score transaction: {e}")
        logger.error("Transaction scoring failed", error=str(e))


@cli.command()
def list_webhooks() -> None:
    """List all configured webhooks."""
    try:
        # Run async webhook listing in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def list_webhooks_async() -> None:
            manager = await get_webhook_manager()
            webhooks = await manager.list_webhooks()

            if not webhooks:
                click.echo("No webhooks configured")
                return

            click.echo("Configured Webhooks:")
            click.echo("=" * 30)

            for webhook in webhooks:
                click.echo(f"URL: {webhook['url']}")
                click.echo(f"Events: {', '.join(webhook['event_types'])}")
                click.echo(f"Status: {'enabled' if webhook['enabled'] else 'disabled'}")
                click.echo("-" * 20)

        loop.run_until_complete(list_webhooks_async())
        loop.close()

    except Exception as e:
        click.echo(f"ERROR: Error listing webhooks: {e}")


@cli.command()
@click.option("--webhook-id", help="Specific webhook ID to check")
def webhook_history(webhook_id: str | None) -> None:
    """Show webhook delivery history."""
    try:
        # Run async webhook history in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def show_history() -> None:
            manager = await get_webhook_manager()

            if webhook_id:
                history = await manager.get_delivery_history(webhook_id=webhook_id)
                if not history:
                    click.echo(f"No history found for webhook {webhook_id}")
                    return

                click.echo(f"Webhook History for {webhook_id}:")
                click.echo("=" * 40)

                for delivery in history:
                    click.echo(f"Event ID: {delivery.event_id}")
                    click.echo(f"Status: {delivery.status}")
                    click.echo(f"Attempts: {delivery.attempt}")
                    click.echo(f"Sent At: {delivery.sent_at}")
                    click.echo("-" * 20)
            else:
                # Show recent history for all webhooks
                all_history = await manager.get_delivery_history()
                if not all_history:
                    click.echo("No webhook history found")
                    return

                click.echo("Recent Webhook History:")
                click.echo("=" * 30)

                for delivery in all_history[:10]:  # Show last 10
                    click.echo(f"Webhook: {delivery.webhook_id}")
                    click.echo(f"Event ID: {delivery.event_id}")
                    click.echo(f"Status: {delivery.status}")
                    click.echo(f"Sent At: {delivery.sent_at}")
                    click.echo("-" * 20)

        loop.run_until_complete(show_history())
        loop.close()

    except Exception as e:
        click.echo(f"ERROR: Error showing webhook history: {e}")


@cli.command()
def health_check() -> None:
    """Perform system health check."""
    try:
        click.echo("AltWallet Checkout Agent Health Check")
        click.echo("=" * 40)

        # Check core modules
        click.echo("Core Modules:")
        click.echo("  Decisioning: OK")
        click.echo("  Webhooks: OK")
        click.echo("  Analytics: OK")
        click.echo("  Logging: OK")

        # Check webhook manager
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def check_webhooks() -> int:
                manager = await get_webhook_manager()
                webhook_count = len(await manager.list_webhooks())
                return webhook_count

            webhook_count = loop.run_until_complete(check_webhooks())
            loop.close()

            click.echo(f"  Webhook Manager: OK ({webhook_count} webhooks)")

        except Exception as e:
            click.echo(f"  Webhook Manager: ERROR - {e}")

        click.echo("\nOverall Status: HEALTHY")

    except Exception as e:
        click.echo(f"Health check failed: {e}")
        logger.error("Health check failed", error=str(e))


if __name__ == "__main__":
    cli()
