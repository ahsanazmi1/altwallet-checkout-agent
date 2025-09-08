"""Merchant Penalty Module for AltWallet Checkout Agent.

This module calculates merchant-specific penalties based on merchant preferences,
network requirements, and MCC categories. Penalties are applied when merchant
preferences don't align with card capabilities.
"""

import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

try:
    import yaml

    _HAS_YAML = True
except Exception:  # pragma: no cover - allow running without PyYAML
    yaml = None  # type: ignore
    _HAS_YAML = False

from .logger import get_logger
from .models import Context

logger = get_logger(__name__)


class MerchantPenalty:
    """Calculates merchant-specific penalties based on preferences and requirements."""

    def __init__(self, config_path: str | None = None):
        """Initialize the merchant penalty module.

        Args:
            config_path: Path to merchant penalty configuration file
        """
        self.config = self._load_config(config_path)
        logger.info("Merchant penalty module initialized")

    def _load_config(self, config_path: str | None = None) -> dict[str, Any]:
        """Load merchant penalty configuration from YAML file.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary
        """
        if config_path is None:
            config_path = str(
                Path(__file__).parent.parent.parent
                / "config"
                / "merchant_penalties.yaml"
            )

        # If PyYAML is unavailable, use defaults
        if not _HAS_YAML:
            logger.warning(
                "PyYAML not installed, using default merchant penalty configuration"
            )
            return self._get_default_config()

        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded merchant penalty config from {config_path}")
            if isinstance(config, dict):
                return config
            return self._get_default_config()
        except FileNotFoundError:
            logger.warning(
                f"Merchant penalty config not found at {config_path}, using defaults"
            )
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Error parsing merchant penalty config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration when config file is not available."""
        return {
            "merchants": {
                "amazon.com": {
                    "5999": 0.85,
                    "default": 0.90,
                },
                "walmart.com": {
                    "5311": 0.88,
                    "5411": 0.88,
                    "default": 0.92,
                },
            },
            "mcc_families": {
                "4511": 0.90,  # Airlines
                "5411": 0.95,  # Grocery stores
                "5541": 0.92,  # Gas stations
                "5542": 0.92,  # Automated fuel
                "default": 1.0,
            },
            "network_penalties": {
                "debit_preference": 0.85,
                "visa_preference": 0.90,
                "mastercard_preference": 0.90,
                "amex_preference": 0.80,
                "discover_preference": 0.85,
                "no_amex": 0.75,
                "no_discover": 0.90,
                "no_visa": 0.70,
                "no_mastercard": 0.70,
            },
            "fuzzy_matching": {
                "similarity_threshold": 0.8,
                "variations": {
                    "amazon": ["amazon.com", "amzn", "amazon-"],
                    "walmart": ["walmart.com", "walmart-", "walmart"],
                },
            },
            "calculation": {
                "min_penalty": 0.8,
                "max_penalty": 1.0,
                "base_penalty": 1.0,
                "factor_weights": {
                    "merchant_specific": 0.4,
                    "mcc_family": 0.3,
                    "network_preference": 0.3,
                },
            },
        }

    def merchant_penalty(self, context: Context) -> float:
        """Calculate merchant penalty for a transaction context.

        Args:
            context: Transaction context containing merchant and card information

        Returns:
            Penalty value in range [0.8, 1.0] where 1.0 = no penalty
        """
        try:
            # Get merchant name and MCC
            merchant_name = self._normalize_merchant_name(context.merchant.name)
            mcc = self._get_mcc_from_context(context)

            # Calculate individual penalty components
            merchant_specific_penalty = self._calculate_merchant_specific_penalty(
                merchant_name, mcc
            )
            mcc_family_penalty = self._calculate_mcc_family_penalty(mcc)
            network_penalty = self._calculate_network_penalty(context)

            # Combine penalties using weighted average
            factor_weights = self.config["calculation"]["factor_weights"]
            merchant_weight = factor_weights.get("merchant_specific", 0.4)
            mcc_weight = factor_weights.get("mcc_family", 0.3)
            network_weight = factor_weights.get("network_preference", 0.3)

            if (
                isinstance(merchant_weight, (int, float))
                and isinstance(mcc_weight, (int, float))
                and isinstance(network_weight, (int, float))
            ):
                final_penalty = (
                    merchant_specific_penalty * float(merchant_weight)
                    + mcc_family_penalty * float(mcc_weight)
                    + network_penalty * float(network_weight)
                )
            else:
                final_penalty = (
                    merchant_specific_penalty * 0.4
                    + mcc_family_penalty * 0.3
                    + network_penalty * 0.3
                )

            # Apply bounds
            min_penalty = self.config["calculation"]["min_penalty"]
            max_penalty = self.config["calculation"]["max_penalty"]
            if isinstance(min_penalty, (int, float)) and isinstance(
                max_penalty, (int, float)
            ):
                final_penalty = max(
                    float(min_penalty), min(float(max_penalty), final_penalty)
                )

            logger.debug(
                f"Merchant {merchant_name} (MCC: {mcc}): "
                f"merchant_specific={merchant_specific_penalty:.3f}, "
                f"mcc_family={mcc_family_penalty:.3f}, "
                f"network={network_penalty:.3f}, "
                f"final={final_penalty:.3f}"
            )

            return final_penalty

        except Exception as e:
            logger.error(f"Error calculating merchant penalty: {e}")
            base_penalty = self.config["calculation"]["base_penalty"]
            if isinstance(base_penalty, (int, float)):
                return float(base_penalty)
            return 1.0

    def _normalize_merchant_name(self, merchant_name: str) -> str:
        """Normalize merchant name for consistent matching."""
        if not merchant_name:
            return ""

        # Convert to lowercase and remove common suffixes
        normalized = merchant_name.lower().strip()
        normalized = re.sub(r"\.(com|net|org|co|us)$", "", normalized)
        normalized = re.sub(r"[^\w\s-]", "", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()

        return normalized

    def _get_mcc_from_context(self, context: Context) -> str:
        """Extract MCC from transaction context."""
        # Try merchant MCC first
        if context.merchant and context.merchant.mcc:
            return context.merchant.mcc

        # Try cart items MCC
        if context.cart and context.cart.items:
            for item in context.cart.items:
                if item.mcc:
                    return item.mcc

        return "default"

    def _calculate_merchant_specific_penalty(
        self, merchant_name: str, mcc: str
    ) -> float:
        """Calculate penalty based on exact merchant name and MCC match."""
        merchants = self.config.get("merchants", {})

        # Try exact match first
        if merchant_name in merchants:
            merchant_config = merchants[merchant_name]
            if mcc in merchant_config:
                penalty = merchant_config[mcc]
                if isinstance(penalty, (int, float)):
                    return float(penalty)
                return 1.0
            elif "default" in merchant_config:
                penalty = merchant_config["default"]
                if isinstance(penalty, (int, float)):
                    return float(penalty)
                return 1.0

        # Try fuzzy matching
        fuzzy_match = self._find_fuzzy_merchant_match(merchant_name)
        if fuzzy_match and fuzzy_match in merchants:
            merchant_config = merchants[fuzzy_match]
            if mcc in merchant_config:
                penalty = merchant_config[mcc]
                if isinstance(penalty, (int, float)):
                    return float(penalty)
                return 1.0
            elif "default" in merchant_config:
                penalty = merchant_config["default"]
                if isinstance(penalty, (int, float)):
                    return float(penalty)
                return 1.0

        # No merchant-specific penalty found
        base_penalty = self.config["calculation"]["base_penalty"]
        if isinstance(base_penalty, (int, float)):
            return float(base_penalty)
        return 1.0

    def _find_fuzzy_merchant_match(self, merchant_name: str) -> str | None:
        """Find fuzzy match for merchant name using variations."""
        if not merchant_name:
            return None

        variations = self.config.get("fuzzy_matching", {}).get("variations", {})
        threshold = self.config.get("fuzzy_matching", {}).get(
            "similarity_threshold", 0.8
        )

        best_match = None
        best_score = 0.0

        # Check each variation group
        for _base_name, variation_list in variations.items():
            for variation in variation_list:
                score = SequenceMatcher(None, merchant_name, variation).ratio()
                if score > best_score and score >= threshold:
                    best_score = score
                    best_match = variation

        # Also check against base names
        for base_name in variations.keys():
            score = SequenceMatcher(None, merchant_name, base_name).ratio()
            if score > best_score and score >= threshold:
                best_score = score
                best_match = base_name

        return best_match

    def _calculate_mcc_family_penalty(self, mcc: str) -> float:
        """Calculate penalty based on MCC family."""
        mcc_families = self.config.get("mcc_families", {})

        if mcc in mcc_families:
            penalty = mcc_families[mcc]
            if isinstance(penalty, (int, float)):
                return float(penalty)
            return 1.0

        default_penalty = mcc_families.get("default", 1.0)
        if isinstance(default_penalty, (int, float)):
            return float(default_penalty)
        return 1.0

    def _calculate_network_penalty(self, context: Context) -> float:
        """Calculate penalty based on network preferences."""
        if not context.merchant or not context.merchant.network_preferences:
            base_penalty = self.config["calculation"]["base_penalty"]
            if isinstance(base_penalty, (int, float)):
                return float(base_penalty)
            return 1.0

        network_preferences = [
            pref.lower() for pref in context.merchant.network_preferences
        ]
        network_penalties = self.config.get("network_penalties", {})

        # Check for specific network preferences
        if "debit" in network_preferences:
            penalty = network_penalties.get("debit_preference", 0.85)
            if isinstance(penalty, (int, float)):
                return float(penalty)
            return 0.85

        # Check for specific card network preferences
        if "visa" in network_preferences:
            penalty = network_penalties.get("visa_preference", 0.90)
            if isinstance(penalty, (int, float)):
                return float(penalty)
            return 0.90
        elif "mastercard" in network_preferences:
            penalty = network_penalties.get("mastercard_preference", 0.90)
            if isinstance(penalty, (int, float)):
                return float(penalty)
            return 0.90
        elif "amex" in network_preferences or "american express" in network_preferences:
            penalty = network_penalties.get("amex_preference", 0.80)
            if isinstance(penalty, (int, float)):
                return float(penalty)
            return 0.80
        elif "discover" in network_preferences:
            penalty = network_penalties.get("discover_preference", 0.85)
            if isinstance(penalty, (int, float)):
                return float(penalty)
            return 0.85

        # Check for network exclusions
        if (
            "no_amex" in network_preferences
            or "no_american_express" in network_preferences
        ):
            penalty = network_penalties.get("no_amex", 0.75)
            if isinstance(penalty, (int, float)):
                return float(penalty)
            return 0.75
        elif "no_discover" in network_preferences:
            penalty = network_penalties.get("no_discover", 0.90)
            if isinstance(penalty, (int, float)):
                return float(penalty)
            return 0.90
        elif "no_visa" in network_preferences:
            penalty = network_penalties.get("no_visa", 0.70)
            if isinstance(penalty, (int, float)):
                return float(penalty)
            return 0.70
        elif "no_mastercard" in network_preferences:
            penalty = network_penalties.get("no_mastercard", 0.70)
            if isinstance(penalty, (int, float)):
                return float(penalty)
            return 0.70

        base_penalty = self.config["calculation"]["base_penalty"]
        if isinstance(base_penalty, (int, float)):
            return float(base_penalty)
        return 1.0
