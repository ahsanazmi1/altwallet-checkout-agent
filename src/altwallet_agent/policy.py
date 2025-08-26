"""Scoring policy constants for AltWallet Checkout Agent."""

from decimal import Decimal
from typing import Dict

# Risk scoring constants
RISK_SCORE_LOCATION_MISMATCH = 30
RISK_SCORE_VELOCITY_FLAG = 20
RISK_SCORE_CHARGEBACKS = 25
RISK_SCORE_HIGH_TICKET = 10

# High ticket threshold (in USD)
HIGH_TICKET_THRESHOLD = Decimal("500.00")

# Velocity threshold for flagging
VELOCITY_THRESHOLD_24H = 10

# Loyalty boost values
LOYALTY_BOOST_VALUES = {
    "NONE": 0,
    "SILVER": 5,
    "GOLD": 10,
    "PLATINUM": 15,
}

# Score bounds
MIN_SCORE = 0
MAX_SCORE = 120
BASE_SCORE = 100

# MCC to network preference mapping
# This is a simplified mapping - in production, this would be more
# comprehensive
MCC_TO_NETWORK_MAPPING: Dict[str, str] = {
    # Gas stations typically prefer Visa/MC
    "5541": "prefer_visa",
    "5542": "prefer_visa",
    # Grocery stores
    "5411": "prefer_mc",
    # Department stores
    "5311": "prefer_visa",
    # Electronics stores
    "5732": "prefer_mc",
    # Online retail
    "5940": "prefer_visa",
    # Travel agencies
    "4722": "prefer_visa",
    # Airlines
    "4511": "prefer_visa",
    # Hotels
    "7011": "prefer_mc",
    # Restaurants
    "5812": "prefer_visa",
    "5813": "prefer_visa",
    "5814": "prefer_visa",
}

# Supported routing hints
ROUTING_HINTS = ["prefer_visa", "prefer_mc", "any"]
