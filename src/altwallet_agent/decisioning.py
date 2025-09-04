"""Decisioning module for AltWallet Checkout Agent.

This module provides a standardized decision contract that can be returned
consistently across CLI, API, and logs. It integrates with the existing
scoring system to make final transaction decisions and includes routing hints.
"""

import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, computed_field

from .logger import get_logger
from .models import Context
from .policy import (
    HIGH_TICKET_THRESHOLD,
    RISK_SCORE_CHARGEBACKS,
    RISK_SCORE_HIGH_TICKET,
    RISK_SCORE_LOCATION_MISMATCH,
    RISK_SCORE_VELOCITY_FLAG,
    VELOCITY_THRESHOLD_24H,
)
from .scoring import ScoreResult, score_transaction


class Decision(str, Enum):
    """Transaction decision enumeration."""

    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    DECLINE = "DECLINE"


class ActionType(str, Enum):
    """Business rule action types."""

    # Risk mitigation actions
    KYC_REQUIRED = "KYC_REQUIRED"
    ADDITIONAL_VERIFICATION = "ADDITIONAL_VERIFICATION"
    MANUAL_REVIEW = "MANUAL_REVIEW"

    # Loyalty and rewards actions
    LOYALTY_BOOST = "LOYALTY_BOOST"
    LOYALTY_ADJUSTMENT = "LOYALTY_ADJUSTMENT"

    # Discount and pricing actions
    DISCOUNT_APPLIED = "DISCOUNT_APPLIED"
    SURCHARGE_APPLIED = "SURCHARGE_APPLIED"

    # Network routing actions
    NETWORK_ROUTING = "NETWORK_ROUTING"

    # Fraud prevention actions
    FRAUD_SCREENING = "FRAUD_SCREENING"
    VELOCITY_LIMIT = "VELOCITY_LIMIT"


class PenaltyOrIncentive(str, Enum):
    """Penalty or incentive types for routing."""

    SURCHARGE = "surcharge"  # Additional fee applied
    SUPPRESSION = "suppression"  # Fee suppressed/waived
    NONE = "none"  # No penalty or incentive


class RoutingHint(BaseModel):
    """Routing hint information for transaction processing."""

    preferred_network: str = Field(
        default="any", description="Preferred payment network (visa, mc, any)"
    )
    preferred_acquirer: str | None = Field(
        default=None, description="Preferred acquirer identifier"
    )
    penalty_or_incentive: PenaltyOrIncentive = Field(
        default=PenaltyOrIncentive.NONE,
        description="Type of penalty or incentive applied",
    )
    approval_odds: float | None = Field(
        default=None, description="Phase 2 scoring: approval probability (0.0 to 1.0)"
    )
    network_preferences: list[str] = Field(
        default_factory=list,
        description="List of network preferences in priority order",
    )
    mcc_based_hint: str | None = Field(
        default=None, description="MCC-based routing hint if applicable"
    )
    confidence: float = Field(
        default=0.8, description="Confidence in routing recommendation (0.0 to 1.0)"
    )

    @computed_field
    def has_preference(self) -> bool:
        """Check if there's a specific network preference."""
        return self.preferred_network != "any"

    @computed_field
    def has_penalty_or_incentive(self) -> bool:
        """Check if penalty or incentive is applied."""
        return self.penalty_or_incentive != PenaltyOrIncentive.NONE


class BusinessRule(BaseModel):
    """Individual business rule that was applied."""

    rule_id: str = Field(..., description="Unique identifier for the business rule")
    action_type: ActionType = Field(..., description="Type of action taken")
    description: str = Field(..., description="Human-readable description of the rule")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Parameters used in rule evaluation"
    )
    impact_score: float | None = Field(
        None, description="Impact of this rule on the final decision"
    )


class DecisionReason(BaseModel):
    """Reason contributing to the decision."""

    feature_name: str = Field(..., description="Name of the feature or flag")
    value: Any = Field(..., description="Value of the feature")
    threshold: Any | None = Field(
        None, description="Threshold that triggered this reason"
    )
    weight: float = Field(..., description="Weight/importance of this feature")
    description: str = Field(
        ..., description="Human-readable description of the reason"
    )


class DecisionContract(BaseModel):
    """Standardized decision contract for transaction processing."""

    decision: Decision = Field(..., description="Final transaction decision")
    actions: list[BusinessRule] = Field(
        default_factory=list, description="List of applied business rules"
    )
    reasons: list[DecisionReason] = Field(
        default_factory=list,
        description="List of features/flags contributing to the decision",
    )

    # Routing hints
    routing_hint: RoutingHint = Field(..., description="Routing hint information")

    # Additional metadata for consistency across interfaces
    transaction_id: str | None = Field(
        None, description="Unique transaction identifier"
    )
    score_result: ScoreResult | None = Field(
        None, description="Underlying scoring result"
    )
    confidence: float = Field(
        default=1.0, description="Confidence in the decision (0.0 to 1.0)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @computed_field
    def is_approved(self) -> bool:
        """Check if transaction is approved."""
        return self.decision == Decision.APPROVE

    @computed_field
    def requires_review(self) -> bool:
        """Check if transaction requires manual review."""
        return self.decision == Decision.REVIEW

    @computed_field
    def is_declined(self) -> bool:
        """Check if transaction is declined."""
        return self.decision == Decision.DECLINE

    def to_json(self) -> str:
        """Convert decision contract to JSON string."""
        return json.dumps(self.model_dump(), default=str)

    def to_dict(self) -> dict[str, Any]:
        """Convert decision contract to dictionary."""
        return self.model_dump(mode="json")


class DecisionEngine:
    """Engine for making transaction decisions based on scoring and business rules."""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

        # Decision thresholds
        self.approve_threshold = 70  # Score >= 70 for approval
        self.review_threshold = 40  # Score >= 40 for review (below is decline)

        # Business rule configurations
        self.business_rules = self._initialize_business_rules()

    def _initialize_business_rules(self) -> dict[str, dict[str, Any]]:
        """Initialize business rule configurations."""
        return {
            "high_risk_location": {
                "action_type": ActionType.ADDITIONAL_VERIFICATION,
                "description": (
                    "Location mismatch detected - " "additional verification required"
                ),
                "score_impact": RISK_SCORE_LOCATION_MISMATCH,
            },
            "high_velocity": {
                "action_type": ActionType.VELOCITY_LIMIT,
                "description": (
                    "High transaction velocity detected - " "velocity limit applied"
                ),
                "score_impact": RISK_SCORE_VELOCITY_FLAG,
            },
            "chargebacks_present": {
                "action_type": ActionType.KYC_REQUIRED,
                "description": (
                    "Customer has chargeback history - " "KYC verification required"
                ),
                "score_impact": RISK_SCORE_CHARGEBACKS,
            },
            "high_ticket": {
                "action_type": ActionType.MANUAL_REVIEW,
                "description": ("High ticket amount - " "manual review recommended"),
                "score_impact": RISK_SCORE_HIGH_TICKET,
            },
            "loyalty_boost": {
                "action_type": ActionType.LOYALTY_BOOST,
                "description": "Loyalty tier boost applied to score",
                "score_impact": None,  # Positive impact
            },
            "network_routing": {
                "action_type": ActionType.NETWORK_ROUTING,
                "description": "Payment network routing preference applied",
                "score_impact": None,
            },
        }

    def _calculate_routing_hint(
        self, context: Context, score_result: ScoreResult
    ) -> RoutingHint:
        """
        Calculate comprehensive routing hint based on context and scoring.

        Args:
            context: Transaction context
            score_result: Scoring result

        Returns:
            RoutingHint with all routing information
        """
        # Start with basic routing hint from scoring
        preferred_network = score_result.routing_hint

        # Determine preferred acquirer (placeholder for Phase 2)
        preferred_acquirer = self._determine_preferred_acquirer(context)

        # Calculate penalty or incentive based on scoring
        penalty_or_incentive = self._calculate_penalty_or_incentive(
            context, score_result
        )

        # Calculate approval odds (Phase 2 scoring)
        approval_odds = self._calculate_approval_odds(score_result)

        # Get network preferences
        network_preferences = context.merchant.network_preferences

        # Get MCC-based hint
        mcc_based_hint = self._get_mcc_based_hint(context.merchant.mcc)

        # Calculate confidence in routing
        confidence = self._calculate_routing_confidence(
            context, score_result, preferred_network
        )

        return RoutingHint(
            preferred_network=preferred_network,
            preferred_acquirer=preferred_acquirer,
            penalty_or_incentive=penalty_or_incentive,
            approval_odds=approval_odds,
            network_preferences=network_preferences,
            mcc_based_hint=mcc_based_hint,
            confidence=confidence,
        )

    def _determine_preferred_acquirer(self, context: Context) -> str | None:
        """
        Determine preferred acquirer based on context.

        This is a placeholder for Phase 2 scoring integration.
        In production, this would use ML models and business rules.
        """
        # For now, return None (no preference)
        # Phase 2: This would use approval odds, preferences, penalties
        return None

    def _calculate_penalty_or_incentive(
        self, context: Context, score_result: ScoreResult
    ) -> PenaltyOrIncentive:
        """
        Calculate penalty or incentive based on scoring and context.

        Args:
            context: Transaction context
            score_result: Scoring result

        Returns:
            PenaltyOrIncentive type
        """
        # High-risk transactions get surcharge
        if score_result.final_score < 30:
            return PenaltyOrIncentive.SURCHARGE

        # High-value transactions might get surcharge
        if context.cart.total >= HIGH_TICKET_THRESHOLD:  # type: ignore
            return PenaltyOrIncentive.SURCHARGE

        # Premium customers get suppression
        if context.customer.loyalty_tier in ["GOLD", "PLATINUM"]:
            return PenaltyOrIncentive.SUPPRESSION

        # Default: no penalty or incentive
        return PenaltyOrIncentive.NONE

    def _calculate_approval_odds(self, score_result: ScoreResult) -> float:
        """
        Calculate approval odds based on final score.

        This is a simplified Phase 2 scoring implementation.
        In production, this would use ML models and historical data.

        Args:
            score_result: Scoring result

        Returns:
            Approval probability (0.0 to 1.0)
        """
        # Simple linear mapping from score to approval odds
        # Score 0-20: 0.0-0.2 (very low)
        # Score 20-40: 0.2-0.4 (low)
        # Score 40-70: 0.4-0.7 (medium)
        # Score 70-100: 0.7-0.95 (high)
        # Score 100-120: 0.95-1.0 (very high)

        score = score_result.final_score

        if score <= 20:
            return max(0.0, score / 100.0)
        elif score <= 40:
            return 0.2 + (score - 20) * 0.01  # 0.2 to 0.4
        elif score <= 70:
            return 0.4 + (score - 40) * 0.01  # 0.4 to 0.7
        elif score <= 100:
            return 0.7 + (score - 70) * 0.0083  # 0.7 to 0.95
        else:
            return 0.95 + (score - 100) * 0.0025  # 0.95 to 1.0

    def _get_mcc_based_hint(self, mcc: str | None) -> str | None:
        """
        Get MCC-based routing hint.

        Args:
            mcc: Merchant Category Code

        Returns:
            Routing hint string or None
        """
        if not mcc:
            return None

        # Import here to avoid circular imports
        from .policy import MCC_TO_NETWORK_MAPPING

        return MCC_TO_NETWORK_MAPPING.get(mcc)

    def _calculate_routing_confidence(
        self, context: Context, score_result: ScoreResult, preferred_network: str
    ) -> float:
        """
        Calculate confidence in routing recommendation.

        Args:
            context: Transaction context
            score_result: Scoring result
            preferred_network: Preferred network

        Returns:
            Confidence value (0.0 to 1.0)
        """
        confidence = 0.8  # Base confidence

        # Higher confidence if merchant has explicit preferences
        if context.merchant.network_preferences:
            confidence += 0.15

        # Higher confidence if MCC-based hint matches merchant preference
        if (
            context.merchant.mcc
            and self._get_mcc_based_hint(context.merchant.mcc) == preferred_network
        ):
            confidence += 0.1

        # Lower confidence for edge cases
        if score_result.final_score < 30 or score_result.final_score > 100:
            confidence -= 0.1

        # Clamp to bounds
        return max(0.0, min(1.0, confidence))

    def make_decision(
        self, context: Context, transaction_id: str | None = None
    ) -> DecisionContract:
        """
        Make a transaction decision based on context and scoring.

        Args:
            context: Transaction context
            transaction_id: Optional transaction identifier

        Returns:
            DecisionContract with decision, actions, reasons, and routing hints
        """
        self.logger.info("Starting decision process", transaction_id=transaction_id)

        # Get scoring result
        score_result = score_transaction(context)

        # Determine decision based on score
        decision = self._determine_decision(score_result.final_score)

        # Generate business rules
        actions = self._generate_business_rules(context, score_result)

        # Generate decision reasons
        reasons = self._generate_decision_reasons(context, score_result)

        # Calculate routing hint
        routing_hint = self._calculate_routing_hint(context, score_result)

        # Calculate confidence
        confidence = self._calculate_confidence(score_result, context)

        # Create decision contract
        contract = DecisionContract(
            decision=decision,
            actions=actions,
            reasons=reasons,
            routing_hint=routing_hint,
            transaction_id=transaction_id,
            score_result=score_result,
            confidence=confidence,
            metadata={
                "decision_engine_version": "1.0",
                "scoring_version": "1.0",
                "context_flags": context.flags,
            },
        )

        self.logger.info(
            "Decision made",
            decision=decision.value,
            final_score=score_result.final_score,
            actions_count=len(actions),
            reasons_count=len(reasons),
            confidence=confidence,
            transaction_id=transaction_id,
        )

        return contract

    def _determine_decision(self, final_score: int) -> Decision:
        """Determine decision based on final score."""
        if final_score >= self.approve_threshold:
            return Decision.APPROVE
        elif final_score >= self.review_threshold:
            return Decision.REVIEW
        else:
            return Decision.DECLINE

    def _generate_business_rules(
        self, context: Context, score_result: ScoreResult
    ) -> list[BusinessRule]:
        """Generate business rules based on context and scoring."""
        rules = []

        # Location mismatch rule
        if context.flags["mismatch_location"]:  # type: ignore
            rules.append(
                BusinessRule(
                    rule_id="LOC_001",
                    action_type=ActionType.ADDITIONAL_VERIFICATION,
                    description=(
                        "Location mismatch detected - "
                        "additional verification required"
                    ),
                    parameters={
                        "device_location": context.device.location,
                        "transaction_location": {
                            "city": context.geo.city,
                            "country": context.geo.country,
                        },
                        "ip_distance_km": context.device.ip_distance_km,
                    },
                    impact_score=float(RISK_SCORE_LOCATION_MISMATCH),
                )
            )

        # Velocity rule
        if context.flags["velocity_24h_flag"]:  # type: ignore
            rules.append(
                BusinessRule(
                    rule_id="VEL_001",
                    action_type=ActionType.VELOCITY_LIMIT,
                    description=(
                        "High transaction velocity detected - " "velocity limit applied"
                    ),
                    parameters={
                        "velocity_24h": context.customer.historical_velocity_24h,
                        "threshold": VELOCITY_THRESHOLD_24H,
                    },
                    impact_score=float(RISK_SCORE_VELOCITY_FLAG),
                )
            )

        # Chargebacks rule
        if context.customer.chargebacks_12m > 0:
            rules.append(
                BusinessRule(
                    rule_id="CHB_001",
                    action_type=ActionType.KYC_REQUIRED,
                    description=(
                        "Customer has chargeback history - " "KYC verification required"
                    ),
                    parameters={
                        "chargebacks_12m": context.customer.chargebacks_12m,
                    },
                    impact_score=float(RISK_SCORE_CHARGEBACKS),
                )
            )

        # High ticket rule
        if context.cart.total >= HIGH_TICKET_THRESHOLD:  # type: ignore
            rules.append(
                BusinessRule(
                    rule_id="HTK_001",
                    action_type=ActionType.MANUAL_REVIEW,
                    description=("High ticket amount - " "manual review recommended"),
                    parameters={
                        "cart_total": float(context.cart.total),  # type: ignore
                        "threshold": float(HIGH_TICKET_THRESHOLD),
                    },
                    impact_score=float(RISK_SCORE_HIGH_TICKET),
                )
            )

        # Loyalty boost rule
        if score_result.loyalty_boost > 0:
            rules.append(
                BusinessRule(
                    rule_id="LOY_001",
                    action_type=ActionType.LOYALTY_BOOST,
                    description=f"Loyalty tier {context.customer.loyalty_tier.value} boost applied",
                    parameters={
                        "loyalty_tier": context.customer.loyalty_tier.value,
                        "boost_points": score_result.loyalty_boost,
                    },
                    impact_score=None,  # Positive impact
                )
            )

        # Network routing rule
        if score_result.routing_hint != "any":
            rules.append(
                BusinessRule(
                    rule_id="NET_001",
                    action_type=ActionType.NETWORK_ROUTING,
                    description=f"Payment network routing preference: {score_result.routing_hint}",
                    parameters={
                        "routing_hint": score_result.routing_hint,
                        "merchant_mcc": context.merchant.mcc,
                        "merchant_preferences": context.merchant.network_preferences,
                    },
                    impact_score=None,
                )
            )

        return rules

    def _generate_decision_reasons(
        self, context: Context, score_result: ScoreResult
    ) -> list[DecisionReason]:
        """Generate decision reasons based on context and scoring."""
        reasons = []

        # Location mismatch reason
        if context.flags.get("mismatch_location", False):  # type: ignore
            reasons.append(
                DecisionReason(
                    feature_name="location_mismatch",
                    value=True,
                    threshold=False,
                    weight=float(RISK_SCORE_LOCATION_MISMATCH) / 100.0,
                    description="Device location differs from transaction location",
                )
            )

        # Velocity reason
        if context.flags["velocity_24h_flag"]:  # type: ignore
            reasons.append(
                DecisionReason(
                    feature_name="high_velocity_24h",
                    value=context.customer.historical_velocity_24h,
                    threshold=VELOCITY_THRESHOLD_24H,
                    weight=float(RISK_SCORE_VELOCITY_FLAG) / 100.0,
                    description=f"Customer has {context.customer.historical_velocity_24h} transactions in 24h",
                )
            )

        # Chargebacks reason
        if context.customer.chargebacks_12m > 0:
            reasons.append(
                DecisionReason(
                    feature_name="chargebacks_12m",
                    value=context.customer.chargebacks_12m,
                    threshold=0,
                    weight=float(RISK_SCORE_CHARGEBACKS) / 100.0,
                    description=f"Customer has {context.customer.chargebacks_12m} chargebacks in 12 months",
                )
            )

        # High ticket reason
        if context.cart.total >= HIGH_TICKET_THRESHOLD:  # type: ignore
            reasons.append(
                DecisionReason(
                    feature_name="high_ticket_amount",
                    value=float(context.cart.total),  # type: ignore
                    threshold=float(HIGH_TICKET_THRESHOLD),
                    weight=float(RISK_SCORE_HIGH_TICKET) / 100.0,
                    description=f"Transaction amount ${context.cart.total} exceeds threshold ${HIGH_TICKET_THRESHOLD}",
                )
            )

        # Loyalty tier reason
        reasons.append(
            DecisionReason(
                feature_name="loyalty_tier",
                value=context.customer.loyalty_tier.value,
                threshold="NONE",
                weight=float(score_result.loyalty_boost) / 100.0,
                description=f"Customer loyalty tier: {context.customer.loyalty_tier.value}",
            )
        )

        # Final score reason
        reasons.append(
            DecisionReason(
                feature_name="final_score",
                value=score_result.final_score,
                threshold=self.approve_threshold,
                weight=1.0,
                description=f"Final calculated score: {score_result.final_score}",
            )
        )

        return reasons

    def _calculate_confidence(
        self, score_result: ScoreResult, context: Context
    ) -> float:
        """Calculate confidence in the decision."""
        # Base confidence starts at 0.8
        confidence = 0.8

        # Increase confidence for very high or very low scores
        if score_result.final_score >= 90 or score_result.final_score <= 20:
            confidence += 0.15

        # Decrease confidence for edge cases (scores near thresholds)
        if 35 <= score_result.final_score <= 45 or 65 <= score_result.final_score <= 75:
            confidence -= 0.2

        # Decrease confidence for missing context data
        if not context.device.location or not context.geo:
            confidence -= 0.1

        # Clamp confidence to [0.0, 1.0]
        return max(0.0, min(1.0, confidence))


# Convenience function for making decisions
def make_transaction_decision(
    context: Context, transaction_id: str | None = None
) -> DecisionContract:
    """
    Convenience function to make a transaction decision.

    Args:
        context: Transaction context
        transaction_id: Optional transaction identifier

    Returns:
        DecisionContract with decision, actions, reasons, and routing hints
    """
    engine = DecisionEngine()
    return engine.make_decision(context, transaction_id)


# Pure functions for testing
def calculate_decision_thresholds() -> dict[str, int]:
    """Calculate decision thresholds for testing."""
    return {
        "approve": 70,
        "review": 40,
        "decline": 0,
    }


def is_decision_approved(decision: Decision) -> bool:
    """Check if decision is approved."""
    return decision == Decision.APPROVE


def is_decision_review_required(decision: Decision) -> bool:
    """Check if decision requires review."""
    return decision == Decision.REVIEW


def is_decision_declined(decision: Decision) -> bool:
    """Check if decision is declined."""
    return decision == Decision.DECLINE
