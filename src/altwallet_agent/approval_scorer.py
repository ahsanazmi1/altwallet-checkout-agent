"""Two-stage approval-odds module for AltWallet Checkout Agent."""

import math
import random
from decimal import Decimal
from typing import Any

import yaml
from pydantic import BaseModel, Field

from .logger import get_logger
from .models import Context


class FeatureContribution(BaseModel):
    """Individual feature contribution to the raw score."""

    feature: str = Field(..., description="Feature name")
    value: float = Field(
        ..., description="Contribution value (can be positive or negative)"
    )


class AdditiveAttributions(BaseModel):
    """Additive feature attributions on pre-calibration scale."""

    baseline: float = Field(..., description="Baseline score contribution")
    contribs: list[FeatureContribution] = Field(
        ..., description="List of feature contributions"
    )
    sum: float = Field(
        ..., description="Total raw score (baseline + sum of contributions)"
    )


class FeatureAttributions(BaseModel):
    """Feature attributions for explainability."""

    mcc_contribution: float = Field(0.0, description="MCC weight contribution")
    amount_contribution: float = Field(0.0, description="Amount weight contribution")
    issuer_contribution: float = Field(0.0, description="Issuer family contribution")
    cross_border_contribution: float = Field(
        0.0, description="Cross-border contribution"
    )
    location_mismatch_contribution: float = Field(
        0.0, description="Location mismatch contribution"
    )
    velocity_24h_contribution: float = Field(
        0.0, description="24h velocity contribution"
    )
    velocity_7d_contribution: float = Field(0.0, description="7d velocity contribution")
    chargeback_contribution: float = Field(
        0.0, description="Chargeback history contribution"
    )
    merchant_risk_contribution: float = Field(
        0.0, description="Merchant risk contribution"
    )
    loyalty_contribution: float = Field(0.0, description="Loyalty tier contribution")
    base_contribution: float = Field(0.0, description="Base score contribution")


class ApprovalResult(BaseModel):
    """Result of approval odds calculation."""

    p_approval: float = Field(..., description="Approval probability", ge=0.0, le=1.0)
    raw_score: float = Field(..., description="Raw log-odds score")
    calibration: dict[str, Any] = Field(
        ..., description="Calibration method and parameters"
    )
    attributions: FeatureAttributions | None = Field(
        None, description="Feature attributions"
    )
    additive_attributions: AdditiveAttributions | None = Field(
        None, description="Additive feature attributions on pre-calibration scale"
    )


class Calibrator:
    """Base class for probability calibration."""

    def calibrate(self, raw_score: float) -> float:
        """Convert raw score to probability."""
        raise NotImplementedError


class LogisticCalibrator(Calibrator):
    """Logistic (Platt) calibration."""

    def __init__(self, bias: float = 0.0, scale: float = 1.0):
        self.bias = bias
        self.scale = scale

    def calibrate(self, raw_score: float) -> float:
        """Apply logistic transformation: 1 / (1 + exp(-(scale * raw_score + bias)))."""
        z = self.scale * raw_score + self.bias
        return 1.0 / (1.0 + math.exp(-z))


class IsotonicCalibrator(Calibrator):
    """Isotonic calibration (placeholder for future implementation)."""

    def __init__(self, **kwargs) -> None:
        # TODO: Implement isotonic calibration with learned parameters
        self.bias = kwargs.get("bias", 0.0)
        self.scale = kwargs.get("scale", 1.0)

    def calibrate(self, raw_score: float) -> float:
        """Placeholder implementation using logistic as fallback."""
        # TODO: Replace with actual isotonic calibration
        z = self.scale * raw_score + self.bias
        return 1.0 / (1.0 + math.exp(-z))


class ApprovalScorer:
    """Two-stage approval-odds scorer."""

    def __init__(self, config_path: str = "config/approval.yaml"):
        """Initialize the approval scorer with configuration."""
        self.logger = get_logger(__name__)
        self.config = self._load_config(config_path)
        self.calibrator = self._create_calibrator()

        # Set random seed for deterministic behavior
        random.seed(self.config["output"]["random_seed"])

        self.logger.info("ApprovalScorer initialized with config from %s", config_path)

    def _load_config(self, config_path: str) -> dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            self.logger.info("Loaded approval configuration from %s", config_path)
            return config
        except FileNotFoundError:
            self.logger.warning("Config file %s not found, using defaults", config_path)
            return self._get_default_config()
        except Exception as e:
            self.logger.error("Error loading config from %s: %s", config_path, e)
            return self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration."""
        return {
            "rules_layer": {
                "mcc_weights": {"default": 0.0},
                "amount_weights": {"0-100": 0.0, "100+": -0.5},
                "issuer_family_weights": {"unknown": 0.0},
                "cross_border_weight": -1.0,
                "location_mismatch_weights": {"0-10": 0.0, "10+": -1.0},
                "velocity_weights": {
                    "24h": {"0-10": 0.0, "10+": -1.0},
                    "7d": {"0-50": 0.0, "50+": -1.0},
                },
                "chargeback_weights": {"0": 0.0, "1+": -1.0},
                "merchant_risk_weights": {"unknown": 0.0},
                "loyalty_weights": {"NONE": 0.0},
                "base_score": 0.0,
            },
            "calibration_layer": {
                "method": "logistic",
                "logistic": {"bias": 0.0, "scale": 1.0},
            },
            "output": {
                "min_probability": 0.01,
                "max_probability": 0.99,
                "random_seed": 42,
            },
        }

    def _create_calibrator(self) -> Calibrator:
        """Create calibrator based on configuration."""
        method = self.config["calibration_layer"]["method"]

        if method == "logistic":
            params = self.config["calibration_layer"]["logistic"]
            return LogisticCalibrator(**params)
        elif method == "isotonic":
            params = self.config["calibration_layer"].get("isotonic", {})
            return IsotonicCalibrator(**params)
        else:
            self.logger.warning("Unknown calibration method %s, using logistic", method)
            return LogisticCalibrator()

    def _get_mcc_weight(self, mcc: str) -> float:
        """Get MCC weight from configuration."""
        weights = self.config["rules_layer"]["mcc_weights"]
        return weights.get(mcc, weights.get("default", 0.0))

    def _get_amount_weight(self, amount: Decimal) -> float:
        """Get amount weight based on amount ranges."""
        amount_float = float(amount)
        weights = self.config["rules_layer"]["amount_weights"]

        for range_str, weight in weights.items():
            if range_str.endswith("+"):
                min_val = float(range_str[:-1])
                if amount_float >= min_val:
                    return weight
            else:
                min_val, max_val = map(float, range_str.split("-"))
                if min_val <= amount_float < max_val:
                    return weight

        return weights.get("default", 0.0)

    def _get_velocity_weight(self, velocity: int, period: str) -> float:
        """Get velocity weight for 24h or 7d period."""
        weights = self.config["rules_layer"]["velocity_weights"][period]

        for range_str, weight in weights.items():
            if range_str.endswith("+"):
                min_val = float(range_str[:-1])
                if velocity >= min_val:
                    return weight
            else:
                min_val, max_val = map(float, range_str.split("-"))
                if min_val <= velocity < max_val:
                    return weight

        return 0.0

    def _get_chargeback_weight(self, chargebacks: int) -> float:
        """Get chargeback weight."""
        weights = self.config["rules_layer"]["chargeback_weights"]

        if chargebacks >= 3:
            return weights.get("3+", -2.0)
        else:
            return weights.get(str(chargebacks), 0.0)

    def _calculate_location_mismatch_distance(self, context: Context) -> float:
        """Calculate distance between device and geo locations."""
        try:
            device = context.device
            geo = context.geo

            if not device or not geo:
                return 0.0

            # Simple distance calculation (in practice, would use proper geocoding)
            device_location = device.location or {}
            device_city = device_location.get("city", "")
            device_country = device_location.get("country", "")
            
            if device_city == geo.city and device_country == geo.country:
                return 0.0
            elif device_country == geo.country:
                return 50.0  # Same country, different city
            else:
                return 200.0  # Different country
        except Exception:
            return 0.0

    def _get_location_mismatch_weight(self, distance: float) -> float:
        """Get location mismatch weight based on distance."""
        weights = self.config["rules_layer"]["location_mismatch_weights"]

        for range_str, weight in weights.items():
            if range_str.endswith("+"):
                min_val = float(range_str[:-1])
                if distance >= min_val:
                    return weight
            else:
                min_val, max_val = map(float, range_str.split("-"))
                if min_val <= distance < max_val:
                    return weight

        return 0.0

    def score(self, context: dict[str, Any]) -> ApprovalResult:
        """
        Calculate approval odds for a transaction context.

        Args:
            context: Transaction context dictionary

        Returns:
            ApprovalResult with p_approval, raw_score, and calibration info
        """
        # Stage 1: Rules Layer - Calculate raw log-odds score
        raw_score, attributions, additive_attribs = self._calculate_raw_score(context)

        # Stage 2: Calibration Layer - Convert to probability
        p_approval = self.calibrator.calibrate(raw_score)

        # Clamp probability to configured bounds
        min_prob = self.config["output"]["min_probability"]
        max_prob = self.config["output"]["max_probability"]
        p_approval = max(min_prob, min(max_prob, p_approval))

        # Prepare calibration info
        calibration_info = {
            "method": self.config["calibration_layer"]["method"],
            "params": self.config["calibration_layer"].get(
                self.config["calibration_layer"]["method"], {}
            ),
        }

        return ApprovalResult(
            p_approval=p_approval,
            raw_score=raw_score,
            calibration=calibration_info,
            attributions=attributions,
            additive_attributions=additive_attribs,
        )

    def _calculate_raw_score(
        self, context: dict[str, Any]
    ) -> tuple[float, FeatureAttributions, AdditiveAttributions]:
        """Calculate raw log-odds score from deterministic signals."""
        attributions = FeatureAttributions(
            mcc_contribution=0.0,
            amount_contribution=0.0,
            issuer_contribution=0.0,
            cross_border_contribution=0.0,
            location_mismatch_contribution=0.0,
            velocity_24h_contribution=0.0,
            velocity_7d_contribution=0.0,
            chargeback_contribution=0.0,
            merchant_risk_contribution=0.0,
            loyalty_contribution=0.0,
            base_contribution=0.0,
        )

        # MCC weight - default to unknown (neutral) if missing
        mcc = context.get("mcc", "unknown")
        mcc_weight = self._get_mcc_weight(mcc)
        attributions.mcc_contribution = mcc_weight

        # Amount weight - default to 0 if missing (treat as very small amount)
        amount = context.get("amount", Decimal("0"))
        amount_weight = self._get_amount_weight(amount)
        attributions.amount_contribution = amount_weight

        # Issuer family weight - default to unknown (higher risk) if missing
        issuer_family = context.get("issuer_family", "unknown")
        issuer_weights = self.config["rules_layer"]["issuer_family_weights"]
        issuer_weight = issuer_weights.get(
            issuer_family, issuer_weights.get("unknown", 0.0)
        )
        attributions.issuer_contribution = issuer_weight

        # Cross-border weight - default to False (domestic) if missing
        cross_border = context.get("cross_border", False)
        cross_border_weight = (
            self.config["rules_layer"]["cross_border_weight"] if cross_border else 0.0
        )
        attributions.cross_border_contribution = cross_border_weight

        # Location mismatch weight - default to 0 (no mismatch) if missing
        location_mismatch_distance = context.get("location_mismatch_distance", 0.0)
        location_weight = self._get_location_mismatch_weight(location_mismatch_distance)
        attributions.location_mismatch_contribution = location_weight

        # Velocity weights - default to 0 (no velocity) if missing
        velocity_24h = context.get("velocity_24h", 0)
        velocity_24h_weight = self._get_velocity_weight(velocity_24h, "24h")
        attributions.velocity_24h_contribution = velocity_24h_weight

        velocity_7d = context.get("velocity_7d", 0)
        velocity_7d_weight = self._get_velocity_weight(velocity_7d, "7d")
        attributions.velocity_7d_contribution = velocity_7d_weight

        # Chargeback weight - default to 0 (no chargebacks) if missing
        chargebacks = context.get("chargebacks_12m", 0)
        chargeback_weight = self._get_chargeback_weight(chargebacks)
        attributions.chargeback_contribution = chargeback_weight

        # Merchant risk weight - default to unknown (higher risk) if missing
        merchant_risk = context.get("merchant_risk_tier", "unknown")
        merchant_weights = self.config["rules_layer"]["merchant_risk_weights"]
        merchant_weight = merchant_weights.get(
            merchant_risk, merchant_weights.get("unknown", 0.0)
        )
        attributions.merchant_risk_contribution = merchant_weight

        # Loyalty weight - default to NONE (no loyalty) if missing
        loyalty_tier = context.get("loyalty_tier", "NONE")
        loyalty_weights = self.config["rules_layer"]["loyalty_weights"]
        loyalty_weight = loyalty_weights.get(
            loyalty_tier, loyalty_weights.get("NONE", 0.0)
        )
        attributions.loyalty_contribution = loyalty_weight

        # Base score
        base_score = self.config["rules_layer"]["base_score"]
        attributions.base_contribution = base_score

        # Sum all contributions
        raw_score = (
            mcc_weight
            + amount_weight
            + issuer_weight
            + cross_border_weight
            + location_weight
            + velocity_24h_weight
            + velocity_7d_weight
            + chargeback_weight
            + merchant_weight
            + loyalty_weight
            + base_score
        )

        # Create additive attributions
        additive_attribs = self._create_additive_attributions(
            mcc_weight,
            amount_weight,
            issuer_weight,
            cross_border_weight,
            location_weight,
            velocity_24h_weight,
            velocity_7d_weight,
            chargeback_weight,
            merchant_weight,
            loyalty_weight,
            base_score,
        )

        return raw_score, attributions, additive_attribs

    def _create_additive_attributions(
        self,
        mcc_weight: float,
        amount_weight: float,
        issuer_weight: float,
        cross_border_weight: float,
        location_weight: float,
        velocity_24h_weight: float,
        velocity_7d_weight: float,
        chargeback_weight: float,
        merchant_weight: float,
        loyalty_weight: float,
        base_score: float,
    ) -> AdditiveAttributions:
        """Create additive attributions from individual feature weights."""
        # Define feature names for better readability
        feature_mapping = {
            "mcc": mcc_weight,
            "amount": amount_weight,
            "issuer_family": issuer_weight,
            "cross_border": cross_border_weight,
            "location_mismatch": location_weight,
            "velocity_24h": velocity_24h_weight,
            "velocity_7d": velocity_7d_weight,
            "chargebacks_12m": chargeback_weight,
            "merchant_risk": merchant_weight,
            "loyalty_tier": loyalty_weight,
        }

        # Create contributions list, excluding zero contributions
        contribs = []
        for feature, value in feature_mapping.items():
            if abs(value) > 1e-10:  # Small epsilon to avoid floating point issues
                contribs.append(FeatureContribution(feature=feature, value=value))

        # Calculate total raw score
        raw_score = sum(feature_mapping.values()) + base_score

        # Validate additivity within epsilon
        contrib_sum = sum(contrib.value for contrib in contribs) + base_score
        epsilon = 1e-10
        if abs(contrib_sum - raw_score) > epsilon:
            self.logger.warning(
                "Additivity validation failed: contrib_sum=%.10f, raw_score=%.10f",
                contrib_sum,
                raw_score,
            )

        return AdditiveAttributions(
            baseline=base_score, contribs=contribs, sum=raw_score
        )

    def _extract_top_drivers(
        self, additive_attribs: AdditiveAttributions, top_k: int = 3
    ) -> dict[str, list[FeatureContribution]]:
        """Extract top positive and negative feature drivers."""
        # Sort contributions by absolute value
        sorted_contribs = sorted(
            additive_attribs.contribs, key=lambda x: abs(x.value), reverse=True
        )

        # Separate positive and negative contributions
        positive_contribs = [c for c in sorted_contribs if c.value > 0]
        negative_contribs = [c for c in sorted_contribs if c.value < 0]

        return {
            "top_positive": positive_contribs[:top_k],
            "top_negative": negative_contribs[:top_k],
        }

    def explain(self, context: dict[str, Any]) -> AdditiveAttributions:
        """
        Explain the approval decision by returning additive feature attributions.

        Args:
            context: Transaction context dictionary

        Returns:
            AdditiveAttributions with baseline, contributions list, and sum
        """
        _, _, additive_attribs = self._calculate_raw_score(context)
        return additive_attribs
