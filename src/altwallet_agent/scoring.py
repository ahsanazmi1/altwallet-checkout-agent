"""Deterministic Scoring v1 for AltWallet Checkout Agent."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from .logger import get_logger
from .models import Context, LoyaltyTier
from .policy import (
    BASE_SCORE,
    HIGH_TICKET_THRESHOLD,
    LOYALTY_BOOST_VALUES,
    MAX_SCORE,
    MCC_TO_NETWORK_MAPPING,
    MIN_SCORE,
    RISK_SCORE_CHARGEBACKS,
    RISK_SCORE_HIGH_TICKET,
    RISK_SCORE_LOCATION_MISMATCH,
    RISK_SCORE_VELOCITY_FLAG,
)


class ScoreResult(BaseModel):
    """Result of deterministic scoring calculation."""

    risk_score: int = Field(..., description="Risk score (0-100)")
    loyalty_boost: int = Field(..., description="Loyalty boost points")
    final_score: int = Field(..., description="Final score (0-120)")
    routing_hint: str = Field(..., description="Payment network preference")
    signals: dict[str, Any] = Field(
        default_factory=dict, description="Detailed scoring signals and components"
    )

    @classmethod
    def create(
        cls,
        risk_score: int,
        loyalty_boost: int,
        final_score: int,
        routing_hint: str,
        signals: dict[str, Any],
    ) -> "ScoreResult":
        """Create a ScoreResult with validation."""
        return cls(
            risk_score=risk_score,
            loyalty_boost=loyalty_boost,
            final_score=final_score,
            routing_hint=routing_hint,
            signals=signals,
        )


def calculate_risk_score(context: Context) -> tuple[int, dict[str, Any]]:
    """
    Calculate risk score based on context data.

    Args:
        context: Transaction context containing all relevant data

    Returns:
        Tuple of (risk_score, signals_dict)
    """
    risk_score = 0
    signals = {
        "location_mismatch": False,
        "velocity_flag": False,
        "chargebacks_present": False,
        "high_ticket": False,
        "risk_factors": [],
    }

    # Check location mismatch
    if context.flags.get("mismatch_location", False):  # type: ignore[attr-defined]
        risk_score += RISK_SCORE_LOCATION_MISMATCH
        signals["location_mismatch"] = True
        signals["risk_factors"].append("location_mismatch")  # type: ignore[attr-defined]

    # Check velocity flag
    if context.flags.get("velocity_24h_flag", False):  # type: ignore[attr-defined]
        risk_score += RISK_SCORE_VELOCITY_FLAG
        signals["velocity_flag"] = True
        signals["risk_factors"].append("high_velocity_24h")  # type: ignore[attr-defined]

    # Check chargebacks
    if context.customer.chargebacks_12m > 0:
        risk_score += RISK_SCORE_CHARGEBACKS
        signals["chargebacks_present"] = True
        signals["risk_factors"].append("chargebacks_12m")  # type: ignore[attr-defined]

    # Check high ticket amount
    if context.cart.total >= HIGH_TICKET_THRESHOLD:  # type: ignore[operator]
        risk_score += RISK_SCORE_HIGH_TICKET
        signals["high_ticket"] = True
        signals["risk_factors"].append("high_ticket_amount")  # type: ignore[attr-defined]

    # Add detailed signals
    signals.update(
        {
            "cart_total": float(context.cart.total),  # type: ignore[arg-type]
            "customer_velocity_24h": context.customer.historical_velocity_24h,
            "customer_chargebacks_12m": context.customer.chargebacks_12m,
            "loyalty_tier": context.customer.loyalty_tier.value,
        }
    )

    return risk_score, signals


def calculate_loyalty_boost(loyalty_tier: LoyaltyTier) -> int:
    """
    Calculate loyalty boost based on customer tier.

    Args:
        loyalty_tier: Customer's loyalty tier

    Returns:
        Loyalty boost points
    """
    return LOYALTY_BOOST_VALUES.get(loyalty_tier.value, 0)


def calculate_final_score(risk_score: int, loyalty_boost: int) -> int:
    """
    Calculate final score with bounds checking.

    Args:
        risk_score: Calculated risk score
        loyalty_boost: Loyalty boost points

    Returns:
        Final score clamped to [0, 120]
    """
    # Formula: max(0, 100 - risk_score) + loyalty_boost
    base_adjusted = max(0, BASE_SCORE - risk_score)
    final_score = base_adjusted + loyalty_boost

    # Clamp to bounds
    return max(MIN_SCORE, min(MAX_SCORE, final_score))


def determine_routing_hint(context: Context) -> str:
    """
    Determine payment network routing preference.

    Priority:
    1. Merchant network preferences (first one)
    2. MCC-based inference
    3. Default to "any"

    Args:
        context: Transaction context

    Returns:
        Routing hint string
    """
    # Check merchant network preferences first
    if context.merchant.network_preferences:
        first_pref = context.merchant.network_preferences[0].lower()
        if first_pref in ["visa", "mc", "mastercard"]:
            return f"prefer_{first_pref}"

    # Check MCC-based inference
    if context.merchant.mcc:
        mcc_hint = MCC_TO_NETWORK_MAPPING.get(context.merchant.mcc)
        if mcc_hint:
            return mcc_hint

    # Default to "any"
    return "any"


def score_transaction(context: Context) -> ScoreResult:
    """
    Main scoring function that calculates all components.

    Args:
        context: Complete transaction context

    Returns:
        ScoreResult with all scoring components
    """
    logger = get_logger(__name__)

    # Calculate risk score and signals
    risk_score, signals = calculate_risk_score(context)
    logger.debug("Risk score calculated", risk_score=risk_score)

    # Calculate loyalty boost
    loyalty_boost = calculate_loyalty_boost(context.customer.loyalty_tier)
    logger.debug("Loyalty boost calculated", loyalty_boost=loyalty_boost)

    # Calculate final score
    final_score = calculate_final_score(risk_score, loyalty_boost)
    logger.debug("Final score calculated", final_score=final_score)

    # Determine routing hint
    routing_hint = determine_routing_hint(context)
    logger.debug("Routing hint determined", routing_hint=routing_hint)

    # Add routing information to signals
    signals.update(
        {
            "merchant_mcc": context.merchant.mcc,
            "merchant_network_preferences": context.merchant.network_preferences,
            "routing_hint": routing_hint,
            "loyalty_boost": loyalty_boost,
            "final_score": final_score,
        }
    )

    logger.info(
        "Transaction scoring completed",
        risk_score=risk_score,
        loyalty_boost=loyalty_boost,
        final_score=final_score,
        routing_hint=routing_hint,
    )

    return ScoreResult.create(
        risk_score=risk_score,
        loyalty_boost=loyalty_boost,
        final_score=final_score,
        routing_hint=routing_hint,
        signals=signals,
    )


# Pure functions for unit testing
def is_location_mismatch(
    device_location: dict[str, str], geo_location: dict[str, str]
) -> bool:
    """
    Pure function to check location mismatch.

    Args:
        device_location: Device location dict with city/country
        geo_location: Transaction location dict with city/country

    Returns:
        True if locations don't match
    """
    if not device_location or not geo_location:
        return False

    device_city = device_location.get("city", "").lower()
    device_country = device_location.get("country", "").lower()
    geo_city = geo_location.get("city", "").lower()
    geo_country = geo_location.get("country", "").lower()

    return device_city != geo_city or device_country != geo_country


def is_high_velocity(velocity_24h: int, threshold: int = 10) -> bool:
    """
    Pure function to check if velocity is high.

    Args:
        velocity_24h: Number of transactions in 24h
        threshold: Velocity threshold

    Returns:
        True if velocity exceeds threshold
    """
    return velocity_24h > threshold


def is_high_ticket(
    cart_total: Decimal, threshold: Decimal = HIGH_TICKET_THRESHOLD
) -> bool:
    """
    Pure function to check if transaction is high ticket.

    Args:
        cart_total: Cart total amount
        threshold: High ticket threshold

    Returns:
        True if cart total >= threshold
    """
    return cart_total >= threshold
