"""Data models for AltWallet Checkout Agent."""

import json
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
)


class CheckoutRequest(BaseModel):
    """Request model for checkout processing."""

    merchant_id: str = Field(..., description="Unique merchant identifier")
    amount: Decimal = Field(..., description="Transaction amount", ge=0)
    currency: str = Field(default="USD", description="Transaction currency")
    user_id: str | None = Field(None, description="User identifier")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "merchant_id": "merchant_123",
                    "amount": "100.00",
                    "currency": "USD",
                    "user_id": "user_456",
                    "metadata": {"source": "web"},
                }
            ]
        }
    )


class CheckoutResponse(BaseModel):
    """Response model for checkout processing."""

    transaction_id: str = Field(..., description="Unique transaction identifier")
    recommendations: list[dict[str, Any]] = Field(
        default_factory=list, description="Card recommendations"
    )
    score: float = Field(..., description="Transaction score", ge=0, le=1)
    status: str = Field(..., description="Processing status")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Response metadata"
    )


class ScoreRequest(BaseModel):
    """Request model for scoring."""

    transaction_data: dict[str, Any] = Field(
        ..., description="Transaction data to score"
    )
    user_context: dict[str, Any] | None = Field(
        None, description="User context information"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "transaction_data": {"amount": "100.00", "merchant": "test"},
                    "user_context": {"user_id": "user_123"},
                }
            ]
        }
    )


class ScoreResponse(BaseModel):
    """Response model for scoring."""

    score: float = Field(..., description="Calculated score", ge=0, le=1)
    confidence: float = Field(..., description="Confidence in the score", ge=0, le=1)
    factors: list[str] = Field(
        default_factory=list, description="Factors influencing the score"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


# Context Ingestion Models


class LoyaltyTier(str, Enum):
    """Customer loyalty tier enumeration."""

    NONE = "NONE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"


class CartItem(BaseModel):
    """Individual item in a shopping cart."""

    item: str = Field(..., description="Item name or identifier")
    unit_price: Decimal = Field(..., description="Price per unit", ge=0)
    qty: int = Field(default=1, description="Quantity of items", gt=0)
    mcc: str | None = Field(None, description="Merchant Category Code")
    merchant_category: str | None = Field(
        None, description="Human-readable merchant category"
    )

    @field_validator("unit_price")
    @classmethod
    def validate_unit_price(cls, v: Decimal) -> Decimal:
        """Validate unit price is non-negative."""
        if v < 0:
            raise ValueError("Unit price must be non-negative")
        return v

    @field_validator("qty")
    @classmethod
    def validate_qty(cls, v: int) -> int:
        """Validate quantity is positive."""
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v

    @computed_field
    def total_price(self) -> Decimal:
        """Calculate total price for this item."""
        return self.unit_price * self.qty


class Cart(BaseModel):
    """Shopping cart containing multiple items."""

    items: list[CartItem] = Field(
        default_factory=list, description="List of cart items"
    )
    currency: str = Field(default="USD", description="Currency code for the cart")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code format."""
        if not v.isalpha() or len(v) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")
        return v.upper()

    @computed_field
    def total(self) -> Decimal:
        """Calculate total cart value."""
        return sum(item.total_price for item in self.items)

    @computed_field
    def item_count(self) -> int:
        """Get total number of items in cart."""
        return sum(item.qty for item in self.items)


class Merchant(BaseModel):
    """Merchant information."""

    name: str = Field(..., description="Merchant name")
    mcc: str | None = Field(None, description="Merchant Category Code")
    network_preferences: list[str] = Field(
        default_factory=list,
        description=("Preferred payment networks " "(e.g., ['visa', 'mc'])"),
    )
    location: dict[str, str] | None = Field(
        None, description="Merchant location with city and country"
    )

    @field_validator("network_preferences")
    @classmethod
    def validate_network_preferences(cls, v: list[str]) -> list[str]:
        """Validate network preferences are lowercase."""
        return [network.lower() for network in v if network]

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: dict[str, str] | None) -> dict[str, str] | None:
        """Validate location has required fields."""
        if v is not None:
            required_fields = ["city", "country"]
            missing_fields = [field for field in required_fields if field not in v]
            if missing_fields:
                raise ValueError(f"Location must include: {', '.join(missing_fields)}")
        return v


class Customer(BaseModel):
    """Customer information and history."""

    id: str = Field(..., description="Unique customer identifier")
    loyalty_tier: LoyaltyTier = Field(
        default=LoyaltyTier.NONE, description="Customer loyalty tier"
    )
    historical_velocity_24h: int = Field(
        default=0, description="Number of transactions in last 24 hours", ge=0
    )
    chargebacks_12m: int = Field(
        default=0, description="Number of chargebacks in last 12 months", ge=0
    )

    @field_validator("historical_velocity_24h")
    @classmethod
    def validate_velocity(cls, v: int) -> int:
        """Validate velocity is non-negative."""
        if v < 0:
            raise ValueError("Historical velocity must be non-negative")
        return v

    @field_validator("chargebacks_12m")
    @classmethod
    def validate_chargebacks(cls, v: int) -> int:
        """Validate chargebacks is non-negative."""
        if v < 0:
            raise ValueError("Chargebacks count must be non-negative")
        return v


class Device(BaseModel):
    """Device information for transaction."""

    ip: str = Field(..., description="Device IP address")
    device_id: str | None = Field(None, description="Unique device identifier")
    ip_distance_km: float | None = Field(
        None,
        description="Distance between IP location and transaction location in kilometers",
        ge=0,
    )
    location: dict[str, str] | None = Field(
        None, description="Device location with city and country"
    )

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        """Basic IP address validation."""
        if not v or len(v.strip()) == 0:
            raise ValueError("IP address cannot be empty")
        return v.strip()

    @field_validator("ip_distance_km")
    @classmethod
    def validate_ip_distance(cls, v: float | None) -> float | None:
        """Validate IP distance is non-negative."""
        if v is not None and v < 0:
            raise ValueError("IP distance must be non-negative")
        return v

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: dict[str, str] | None) -> dict[str, str] | None:
        """Validate location has required fields."""
        if v is not None:
            required_fields = ["city", "country"]
            missing_fields = [field for field in required_fields if field not in v]
            if missing_fields:
                raise ValueError(f"Location must include: {', '.join(missing_fields)}")
        return v


class Geo(BaseModel):
    """Geographic location information."""

    city: str = Field(..., description="City name")
    region: str | None = Field(None, description="Region or state")
    country: str = Field(..., description="Country name or code")
    lat: float | None = Field(None, description="Latitude coordinate")
    lon: float | None = Field(None, description="Longitude coordinate")

    @field_validator("lat")
    @classmethod
    def validate_lat(cls, v: float | None) -> float | None:
        """Validate latitude is within valid range."""
        if v is not None and (v < -90 or v > 90):
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("lon")
    @classmethod
    def validate_lon(cls, v: float | None) -> float | None:
        """Validate longitude is within valid range."""
        if v is not None and (v < -180 or v > 180):
            raise ValueError("Longitude must be between -180 and 180")
        return v


class Context(BaseModel):
    """Complete transaction context for risk assessment."""

    cart: Cart = Field(..., description="Shopping cart information")
    merchant: Merchant = Field(..., description="Merchant information")
    customer: Customer = Field(..., description="Customer information")
    device: Device = Field(..., description="Device information")
    geo: Geo = Field(..., description="Geographic location")

    @computed_field
    def flags(self) -> dict[str, bool]:
        """Compute risk flags based on context data."""
        flags = {}

        # Location mismatch flag
        flags["mismatch_location"] = self._check_location_mismatch()

        # Velocity flag
        flags["velocity_24h_flag"] = self._check_velocity_flag()

        return flags

    def _check_location_mismatch(self) -> bool:
        """Check if there's a location mismatch between device and transaction."""
        if not self.device.location or not self.geo:
            return False

        device_city = self.device.location.get("city", "").lower()
        device_country = self.device.location.get("country", "").lower()
        geo_city = self.geo.city.lower()
        geo_country = self.geo.country.lower()

        return device_city != geo_city or device_country != geo_country

    def _check_velocity_flag(self) -> bool:
        """Check if customer velocity is concerning."""
        # Flag if customer has more than 10 transactions in 24h
        return self.customer.historical_velocity_24h > 10

    @classmethod
    def from_json_payload(cls, payload: str | dict[str, Any]) -> "Context":
        """
        Build Context from a single JSON payload with defaults and safe coercions.

        Args:
            payload: JSON string or dictionary containing context data

        Returns:
            Context object with validated data

        Raises:
            ValidationError: If payload cannot be converted to valid Context
        """
        try:
            # Parse JSON string if needed
            if isinstance(payload, str):
                data = json.loads(payload)
            else:
                data = payload.copy()

            # Apply safe coercions and defaults
            data = cls._apply_defaults_and_coercions(data)

            # Validate and create Context
            return cls(**data)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON payload: {e}")
        except Exception as e:
            raise ValueError(f"Failed to create Context: {e}")

    @staticmethod
    def _apply_defaults_and_coercions(data: dict[str, Any]) -> dict[str, Any]:
        """Apply safe defaults and type coercions to input data."""
        # Ensure required top-level sections exist
        for section in ["cart", "merchant", "customer", "device", "geo"]:
            if section not in data:
                data[section] = {}

        # Cart defaults and coercions
        cart_data = data.get("cart", {})
        if "items" not in cart_data:
            cart_data["items"] = []
        if "currency" not in cart_data:
            cart_data["currency"] = "USD"

        # Ensure cart items have required fields
        for item in cart_data.get("items", []):
            if "qty" not in item:
                item["qty"] = 1
            if "unit_price" in item and isinstance(item["unit_price"], (int, float)):
                item["unit_price"] = str(item["unit_price"])

        # Customer defaults
        customer_data = data.get("customer", {})
        if "loyalty_tier" not in customer_data:
            customer_data["loyalty_tier"] = "NONE"
        if "historical_velocity_24h" not in customer_data:
            customer_data["historical_velocity_24h"] = 0
        if "chargebacks_12m" not in customer_data:
            customer_data["chargebacks_12m"] = 0

        # Device defaults
        device_data = data.get("device", {})
        if "network_preferences" not in device_data:
            device_data["network_preferences"] = []

        # Geo defaults
        geo_data = data.get("geo", {})
        if "city" not in geo_data:
            geo_data["city"] = ""
        if "country" not in geo_data:
            geo_data["country"] = ""

        return data
