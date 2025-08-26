"""Data models for AltWallet Checkout Agent."""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CheckoutRequest(BaseModel):
    """Request model for checkout processing."""

    merchant_id: str = Field(..., description="Unique merchant identifier")
    amount: Decimal = Field(..., description="Transaction amount", ge=0)
    currency: str = Field(default="USD", description="Transaction currency")
    user_id: Optional[str] = Field(None, description="User identifier")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    class Config:
        json_encoders = {Decimal: str}


class CheckoutResponse(BaseModel):
    """Response model for checkout processing."""

    transaction_id: str = Field(..., description="Unique transaction identifier")
    recommendations: List[Dict[str, Any]] = Field(
        default_factory=list, description="Card recommendations"
    )
    score: float = Field(..., description="Transaction score", ge=0, le=1)
    status: str = Field(..., description="Processing status")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Response metadata"
    )


class ScoreRequest(BaseModel):
    """Request model for scoring."""

    transaction_data: Dict[str, Any] = Field(
        ..., description="Transaction data to score"
    )
    user_context: Optional[Dict[str, Any]] = Field(
        None, description="User context information"
    )

    class Config:
        json_encoders = {Decimal: str}


class ScoreResponse(BaseModel):
    """Response model for scoring."""

    score: float = Field(..., description="Calculated score", ge=0, le=1)
    confidence: float = Field(..., description="Confidence in the score", ge=0, le=1)
    factors: List[str] = Field(
        default_factory=list, description="Factors influencing the score"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
