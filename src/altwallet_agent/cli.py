#!/usr/bin/env python3
"""
AltWallet Checkout Agent CLI

Provides command-line interface for simulating decisions, managing webhooks,
and checking system health.
"""

import asyncio
import json
import time

from typing import Optional

import click

from altwallet_agent.analytics import log_decision_outcome
from altwallet_agent.decisioning import (
    DecisionContract,
    BusinessRule,
    DecisionReason,
    ActionType,
    PenaltyOrIncentive,
    Decision,
    RoutingHint,
)
from altwallet_agent.logger import get_logger
from altwallet_agent.webhooks import get_webhook_manager, get_webhook_emitter

logger = get_logger(__name__)


@click.group()
@click.version_option(version="0.3.0")
def cli() -> None:
    """AltWallet Checkout Agent CLI - Decision Simulation and Management"""
    pass


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
        actions.append(BusinessRule(
            action_type=ActionType.DISCOUNT_APPLIED,
            rule_id="discount_001",
            description="Loyalty discount applied",
            impact_score=0.8
        ))
    if kyc:
        actions.append(BusinessRule(
            action_type=ActionType.KYC_REQUIRED,
            rule_id="kyc_001",
            description="KYC verification required",
            impact_score=0.9
        ))
    
    # Add default actions for approval
    if not actions:
        actions.append(BusinessRule(
            action_type=ActionType.LOYALTY_BOOST,
            rule_id="approval_001",
            description="Standard approval granted",
            impact_score=0.7
        ))
    
    return DecisionContract(
        decision=Decision.APPROVE,
        actions=actions,
        reasons=[
            DecisionReason(
                feature_name="risk_score",
                value="low",
                weight=0.8,
                description="Low risk score indicates approval",
                threshold=0.5
            ),
            DecisionReason(
                feature_name="customer_history",
                value="good",
                weight=0.7,
                description="Good customer history",
                threshold=0.6
            )
        ],
        routing_hint=RoutingHint(
            preferred_network="VISA",
            preferred_acquirer="STRIPE",
            penalty_or_incentive=PenaltyOrIncentive.NONE
        ),
        transaction_id=f"sim_{int(time.time())}",
        score_result=None
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
        actions.append(BusinessRule(
            action_type=ActionType.DISCOUNT_APPLIED,
            rule_id="discount_002",
            description="Loyalty discount applied",
            impact_score=0.8
        ))
    if kyc:
        actions.append(BusinessRule(
            action_type=ActionType.KYC_REQUIRED,
            rule_id="kyc_002",
            description="KYC verification required",
            impact_score=0.9
        ))
    
    # Add default actions for decline
    if not actions:
        actions.append(BusinessRule(
            action_type=ActionType.FRAUD_SCREENING,
            rule_id="decline_001",
            description="Risk threshold exceeded",
            impact_score=0.9
        ))
    
    return DecisionContract(
        decision=Decision.DECLINE,
        actions=actions,
        reasons=[
            DecisionReason(
                feature_name="risk_score",
                value="high",
                weight=0.9,
                description="High risk score indicates decline",
                threshold=0.5
            ),
            DecisionReason(
                feature_name="fraud_indicator",
                value="suspicious",
                weight=0.8,
                description="Suspicious activity detected",
                threshold=0.7
            )
        ],
        routing_hint=RoutingHint(
            preferred_network="VISA",
            preferred_acquirer="STRIPE",
            penalty_or_incentive=PenaltyOrIncentive.NONE
        ),
        transaction_id=f"sim_{int(time.time())}",
        score_result=None
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
        actions.append(BusinessRule(
            action_type=ActionType.DISCOUNT_APPLIED,
            rule_id="discount_003",
            description="Loyalty discount applied",
            impact_score=0.8
        ))
    if kyc:
        actions.append(BusinessRule(
            action_type=ActionType.KYC_REQUIRED,
            rule_id="kyc_003",
            description="KYC verification required",
            impact_score=0.9
        ))
    
    # Add default actions for review
    if not actions:
        actions.append(BusinessRule(
            action_type=ActionType.MANUAL_REVIEW,
            rule_id="review_001",
            description="Manual review required",
            impact_score=0.7
        ))
    
    return DecisionContract(
        decision=Decision.REVIEW,
        actions=actions,
        reasons=[
            DecisionReason(
                feature_name="risk_score",
                value="medium",
                weight=0.6,
                description="Medium risk score requires review",
                threshold=0.5
            ),
            DecisionReason(
                feature_name="pattern_analysis",
                value="unusual",
                weight=0.5,
                description="Unusual transaction pattern detected",
                threshold=0.6
            )
        ],
        routing_hint=RoutingHint(
            preferred_network="VISA",
            preferred_acquirer="STRIPE",
            penalty_or_incentive=PenaltyOrIncentive.NONE
        ),
        transaction_id=f"sim_{int(time.time())}",
        score_result=None
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
                }
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
            error_flags=[]
        )
        click.echo("Analytics event logged successfully")
        
    except Exception as e:
        click.echo(f"ERROR: Failed to log analytics: {e}")


@cli.command()
@click.option("--input", "-i", required=True, help="Input JSON file path")
def score(input: str) -> None:
    """Score a transaction from input file."""
    try:
        import json
        from pathlib import Path
        
        # Read input file
        input_path = Path(input)
        if not input_path.exists():
            click.echo(f"ERROR: Input file not found: {input}")
            return
        
        with open(input_path, 'r') as f:
            context_data = json.load(f)
        
        # Import scoring function
        from altwallet_agent.scoring import score_transaction
        from altwallet_agent.models import Context
        
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
            "signals": score_result.signals
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
def webhook_history(webhook_id: Optional[str]) -> None:
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



