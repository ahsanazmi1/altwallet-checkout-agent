"""Data models for the AltWallet Python SDK.

These models define the request and response schemas that match the OpenAPI specification.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, validator


class SDKConfig(BaseModel):
    """Configuration for the AltWallet SDK client."""

    # API Configuration
    api_endpoint: str = Field(
        default="http://localhost:8000", description="AltWallet API endpoint URL"
    )

    api_key: str | None = Field(
        default=None, description="API key for authentication"
    )

    timeout: int = Field(default=30, description="Request timeout in seconds")

    # Retry Configuration
    retry_attempts: int = Field(
        default=3, description="Number of retry attempts for failed requests"
    )

    retry_delay: float = Field(
        default=1.0, description="Delay between retry attempts in seconds"
    )

    # Connection Configuration
    connection_pool_size: int = Field(
        default=10, description="HTTP connection pool size"
    )

    keep_alive: bool = Field(default=True, description="Enable HTTP keep-alive")

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")

    enable_logging: bool = Field(default=True, description="Enable SDK logging")

    @validator("timeout")
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v

    @validator("retry_attempts")
    def validate_retry_attempts(cls, v):
        if v < 0:
            raise ValueError("Retry attempts must be non-negative")
        return v


class CartItem(BaseModel):
    """Individual item in a shopping cart."""

    item_id: str = Field(description="Unique item identifier")
    name: str = Field(description="Item name")
    unit_price: float = Field(description="Unit price of the item")
    quantity: int = Field(description="Quantity of the item")
    category: str | None = Field(default=None, description="Item category")
    mcc: str | None = Field(default=None, description="Merchant category code")


class Cart(BaseModel):
    """Shopping cart containing items and metadata."""

    items: list[CartItem] = Field(description="List of cart items")
    currency: str = Field(default="USD", description="Currency code")
    total_amount: float | None = Field(default=None, description="Total cart amount")
    tax_amount: float | None = Field(default=None, description="Tax amount")
    shipping_amount: float | None = Field(
        default=None, description="Shipping amount"
    )

    @validator("currency")
    def validate_currency(cls, v):
        if len(v) != 3:
            raise ValueError("Currency must be a 3-character code")
        return v.upper()


class Customer(BaseModel):
    """Customer information for personalization."""

    customer_id: str = Field(description="Unique customer identifier")
    loyalty_tier: str | None = Field(
        default=None, description="Customer loyalty tier"
    )
    preferred_cards: list[str] | None = Field(
        default=None, description="Preferred card IDs"
    )
    risk_profile: str | None = Field(
        default=None, description="Customer risk profile"
    )
    location: dict[str, str] | None = Field(
        default=None, description="Customer location"
    )


class Context(BaseModel):
    """Additional context for the transaction."""

    merchant_id: str = Field(description="Merchant identifier")
    merchant_name: str | None = Field(default=None, description="Merchant name")
    device_type: str | None = Field(
        default=None, description="Device type (mobile, desktop, etc.)"
    )
    user_agent: str | None = Field(default=None, description="User agent string")
    ip_address: str | None = Field(default=None, description="Customer IP address")
    session_id: str | None = Field(default=None, description="Session identifier")
    referrer: str | None = Field(default=None, description="Referrer URL")
    campaign_id: str | None = Field(
        default=None, description="Marketing campaign ID"
    )


class QuoteRequest(BaseModel):
    """Request for getting card recommendations."""

    cart: Cart = Field(description="Shopping cart information")
    customer: Customer = Field(description="Customer information")
    context: Context = Field(description="Transaction context")
    request_id: str | None = Field(
        default=None, description="Unique request identifier"
    )

    class Config:
        schema_extra = {
            "example": {
                "cart": {
                    "items": [
                        {
                            "item_id": "item_123",
                            "name": "Grocery Items",
                            "unit_price": 45.99,
                            "quantity": 1,
                            "category": "groceries",
                            "mcc": "5411",
                        }
                    ],
                    "currency": "USD",
                    "total_amount": 45.99,
                },
                "customer": {
                    "customer_id": "cust_12345",
                    "loyalty_tier": "SILVER",
                    "preferred_cards": ["amex_gold", "chase_freedom"],
                },
                "context": {
                    "merchant_id": "grocery_store_123",
                    "merchant_name": "Local Grocery Store",
                    "device_type": "mobile",
                    "ip_address": "192.168.1.100",
                },
            }
        }


class Recommendation(BaseModel):
    """Card recommendation with scoring and reasoning."""

    card_id: str = Field(description="Unique card identifier")
    card_name: str = Field(description="Card name")
    issuer: str = Field(description="Card issuer")
    rank: int = Field(description="Recommendation rank (1 = best)")
    approval_probability: float = Field(description="Probability of approval (0.0-1.0)")
    expected_rewards: float = Field(description="Expected rewards rate")
    utility_score: float = Field(description="Overall utility score")
    reasoning: str | None = Field(
        default=None, description="Human-readable reasoning"
    )
    features: dict[str, Any] | None = Field(
        default=None, description="Feature attributions"
    )


class QuoteResponse(BaseModel):
    """Response containing card recommendations."""

    request_id: str = Field(description="Unique request identifier")
    transaction_id: str = Field(description="Transaction identifier")
    score: float = Field(description="Overall transaction score")
    status: str = Field(description="Processing status")
    recommendations: list[Recommendation] = Field(description="Card recommendations")
    processing_time_ms: int = Field(description="Processing time in milliseconds")
    timestamp: datetime = Field(description="Response timestamp")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )

    class Config:
        schema_extra = {
            "example": {
                "request_id": "req_12345",
                "transaction_id": "txn_67890",
                "score": 0.85,
                "status": "completed",
                "recommendations": [
                    {
                        "card_id": "amex_gold",
                        "card_name": "American Express Gold",
                        "issuer": "American Express",
                        "rank": 1,
                        "approval_probability": 0.92,
                        "expected_rewards": 0.04,
                        "utility_score": 0.88,
                        "reasoning": "High rewards for grocery purchases",
                    }
                ],
                "processing_time_ms": 45,
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }


class DecisionRequest(BaseModel):
    """Request for getting decision details."""

    request_id: str = Field(description="Request identifier to look up")

    class Config:
        schema_extra = {"example": {"request_id": "req_12345"}}


class DecisionResponse(BaseModel):
    """Response containing decision details."""

    request_id: str = Field(description="Request identifier")
    transaction_id: str = Field(description="Transaction identifier")
    decision: str = Field(description="Decision result")
    confidence: float = Field(description="Decision confidence (0.0-1.0)")
    reasoning: str = Field(description="Decision reasoning")
    risk_factors: list[str] | None = Field(
        default=None, description="Identified risk factors"
    )
    timestamp: datetime = Field(description="Decision timestamp")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )

    class Config:
        schema_extra = {
            "example": {
                "request_id": "req_12345",
                "transaction_id": "txn_67890",
                "decision": "approve",
                "confidence": 0.92,
                "reasoning": "Low risk transaction with good customer profile",
                "risk_factors": [],
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }


class ErrorResponse(BaseModel):
    """Error response from the API."""

    error_code: str = Field(description="Error code")
    error_message: str = Field(description="Error message")
    request_id: str | None = Field(default=None, description="Request identifier")
    timestamp: datetime = Field(description="Error timestamp")
    details: dict[str, Any] | None = Field(
        default=None, description="Additional error details"
    )

    class Config:
        schema_extra = {
            "example": {
                "error_code": "VALIDATION_ERROR",
                "error_message": "Invalid cart data provided",
                "request_id": "req_12345",
                "timestamp": "2024-01-15T10:30:00Z",
                "details": {
                    "field": "cart.items",
                    "issue": "Missing required field: unit_price",
                },
            }
        }
