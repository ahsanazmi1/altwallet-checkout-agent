"""Core CheckoutAgent implementation."""

import contextvars
import time
import uuid
from typing import Any
import subprocess

import structlog
from rich.console import Console
from rich.table import Table

from .models import (
    CheckoutRequest, CheckoutResponse, ScoreRequest, ScoreResponse, 
    EnhancedCheckoutResponse
)

# Context variables for request/trace IDs
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
trace_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "trace_id", default=None
)

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


class CheckoutAgent:
    """Core checkout agent for processing transactions and providing recommendations."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the checkout agent.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = structlog.get_logger(__name__)
        self.console = Console()

    def _get_logger(self) -> structlog.BoundLogger:
        """Get a logger with current context."""
        request_id = request_id_var.get()
        trace_id = trace_id_var.get()

        return self.logger.bind(  # type: ignore[no-any-return]
            request_id=request_id,
            trace_id=trace_id,
        )

    def _get_git_sha(self) -> str:
        """Get the current git SHA."""
        try:
            # Attempt to get the SHA from a git log command
            sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
            return sha
        except subprocess.CalledProcessError:
            return "unknown"
    
    def _get_approval_scorer(self):
        """Get approval scorer instance."""
        from .approval_scorer import ApprovalScorer
        return ApprovalScorer()
    
    def _get_card_database(self) -> list[dict[str, Any]]:
        """Get card database for recommendations."""
        from .data.card_database import get_card_database
        return get_card_database()

    def _request_to_context(self, request: CheckoutRequest):
        """Convert CheckoutRequest to Context for scoring."""
        from .models import Context, Customer, Merchant, Cart, CartItem, Device, Geo, LoyaltyTier
        from decimal import Decimal
        
        # Try to get data from metadata or use defaults
        metadata = getattr(request, 'metadata', {})
        
        # Get cart data
        cart_data = metadata.get('cart', {})
        cart_items = []
        for item_data in cart_data.get("items", []):
            cart_items.append(CartItem(
                item=item_data.get("item", "Unknown"),
                unit_price=Decimal(str(item_data.get("unit_price", "0.00"))),
                qty=item_data.get("qty", 1),
                mcc=item_data.get("mcc")
            ))
        
        # Get customer data
        customer_data = metadata.get('customer', {})
        
        # Get merchant data
        merchant_data = metadata.get('merchant', {})
        
        # Get device data
        device_data = metadata.get('device', {})
        
        # Get geo data
        geo_data = metadata.get('geo', {})
        
        # Create context
        return Context(
            customer=Customer(
                id=customer_data.get("id", "unknown"),
                loyalty_tier=LoyaltyTier(customer_data.get("loyalty_tier", "NONE")),
                historical_velocity_24h=customer_data.get("historical_velocity_24h", 0),
                chargebacks_12m=customer_data.get("chargebacks_12m", 0)
            ),
            merchant=Merchant(
                name=merchant_data.get("name", "Unknown"),
                mcc=merchant_data.get("mcc", "0000"),
                network_preferences=merchant_data.get("network_preferences", []),
                location=merchant_data.get("location", {"city": "Unknown", "country": "US"})
            ),
            cart=Cart(items=cart_items),
            device=Device(
                ip=device_data.get("ip", "0.0.0.0"),
                location=device_data.get("location", {"city": "Unknown", "country": "US"})
            ),
            geo=Geo(
                city=geo_data.get("city", "Unknown"),
                country=geo_data.get("country", "US")
            )
        )

    def process_checkout(self, request: CheckoutRequest) -> CheckoutResponse:
        """Process a checkout request and return recommendations.

        Args:
            request: The checkout request to process

        Returns:
            CheckoutResponse with recommendations and score
        """
        # Set context for this request
        request_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        trace_id_var.set(trace_id)

        logger = self._get_logger()
        logger.info(
            "Processing checkout request",
            merchant_id=request.merchant_id,
            amount=str(request.amount),
            currency=request.currency,
        )

        # Use intelligence engine for enhanced processing
        try:
            from .intelligence import IntelligenceEngine
            
            # Initialize intelligence engine if not already done
            if not hasattr(self, '_intelligence_engine'):
                self._intelligence_engine = IntelligenceEngine()
            
            # Process with intelligence engine
            response = self._intelligence_engine.process_checkout_intelligence(request)
            
            logger.info(
                "Intelligent checkout processing completed",
                transaction_id=response.transaction_id,
                score=response.score,
                processing_time_ms=self._intelligence_engine.processing_time_ms,
            )
            
            return response
            
        except ImportError:
            # Fallback to basic processing if intelligence module not available
            logger.warning("Intelligence engine not available, using basic processing")
            return self._process_checkout_basic(request)
        except Exception as e:
            # Fallback to basic processing on any error
            logger.error(
                "Intelligence processing failed, falling back to basic",
                error=str(e),
            )
            return self._process_checkout_basic(request)

    def process_checkout_enhanced(self, request: CheckoutRequest) -> EnhancedCheckoutResponse:
        """Process a checkout request with enhanced recommendations and explainability.

        Args:
            request: The checkout request to process

        Returns:
            EnhancedCheckoutResponse with detailed recommendations and explainability
        """
        # Set context for this request
        request_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        trace_id_var.set(trace_id)

        logger = self._get_logger()
        logger.info(
            "Processing enhanced checkout request",
            merchant_id=request.merchant_id,
            amount=str(request.amount),
            currency=request.currency,
        )

        start_time = time.time()

        try:
            # Get approval scorer and card database
            approval_scorer = self._get_approval_scorer()
            cards = self._get_card_database()
            
            # Convert request to context
            context = self._request_to_context(request)
            
            # Convert context to dict for approval scorer
            context_dict = {
                "mcc": context.merchant.mcc,
                "amount": context.cart.total,
                "issuer_family": "visa",  # Default
                "cross_border": False,
                "location_mismatch_distance": 0.0,
                "velocity_24h": context.customer.historical_velocity_24h,
                "velocity_7d": context.customer.historical_velocity_24h * 4,  # Estimate
                "chargebacks_12m": context.customer.chargebacks_12m,
                "merchant_risk_tier": "low",
                "loyalty_tier": context.customer.loyalty_tier.value,
            }
            
            # Calculate scores and recommendations
            recommendations = []
            total_latency_ms = int((time.time() - start_time) * 1000)
            
            for card in cards[:5]:  # Top 5 cards
                # Get approval score
                approval_result = approval_scorer.score(context_dict)
                
                # Calculate utility (simplified)
                utility = approval_result.p_approval * 0.7 + 0.3  # Base utility
                
                # Create recommendation
                recommendation = {
                    "card_id": card.get("id", "unknown"),
                    "card_name": card.get("name", "Unknown Card"),
                    "rank": len(recommendations) + 1,
                    "p_approval": approval_result.p_approval,
                    "expected_rewards": card.get("cashback_rate", 0.02),
                    "utility": utility,
                    "explainability": {
                        "baseline": 0.5,
                        "contributions": [
                            {"feature": "amount", "value": 0.1, "impact": "positive"},
                            {"feature": "merchant_category", "value": -0.05, "impact": "negative"}
                        ],
                        "calibration": "logistic",
                        "top_drivers": {
                            "positive": [{"feature": "amount", "value": 0.1, "magnitude": 0.1}],
                            "negative": [{"feature": "merchant_category", "value": -0.05, "magnitude": 0.05}]
                        }
                    },
                    "audit": {
                        "config_versions": {
                            "scorer": "1.0", 
                            "utility": "1.0",
                            "config/approval.yaml": "1.0",
                            "config/preferences.yaml": "1.0"
                        },
                        "code_version": "1.0.0",
                        "request_id": request_id,
                        "latency_ms": total_latency_ms
                    }
                }
                recommendations.append(recommendation)
            
            # Calculate overall score
            overall_score = sum(r["utility"] for r in recommendations) / len(recommendations)
            
            return EnhancedCheckoutResponse(
                transaction_id=request_id,
                score=overall_score,
                status="completed",
                recommendations=recommendations,
                metadata={
                    "processing_time_ms": int((time.time() - start_time) * 1000),
                    "method": "enhanced",
                    "cards_evaluated": len(cards)
                }
            )
            
        except Exception as e:
            logger.error(f"Enhanced checkout processing failed: {e}")
            # Return error response
            return EnhancedCheckoutResponse(
                transaction_id=request_id,
                score=0.0,
                status="error",
                recommendations=[],
                metadata={"error": str(e)}
            )

    def _process_checkout_basic(self, request: CheckoutRequest) -> CheckoutResponse:
        """Basic checkout processing (fallback method).
        
        Args:
            request: The checkout request to process
            
        Returns:
            CheckoutResponse with basic recommendations
        """
        recommendations = [
            {
                "card_id": "chase_sapphire_preferred",
                "name": "Chase Sapphire Preferred",
                "cashback_rate": 0.02,
                "reason": "Best overall value for this transaction",
            },
            {
                "card_id": "amex_gold",
                "name": "American Express Gold",
                "cashback_rate": 0.04,
                "reason": "High rewards for dining category",
            },
        ]

        score = 0.85  # Basic score

        return CheckoutResponse(
            transaction_id=request_id_var.get() or str(uuid.uuid4()),
            recommendations=recommendations,
            score=score,
            status="completed",
            metadata={"processing_time_ms": 150, "method": "basic"},
        )

    def score_transaction(self, request: ScoreRequest) -> ScoreResponse:
        """Score a transaction based on various factors.

        Args:
            request: The scoring request

        Returns:
            ScoreResponse with calculated score and confidence
        """
        # Set context for this request
        request_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        trace_id_var.set(trace_id)

        logger = self._get_logger()
        logger.info(
            "Scoring transaction",
            transaction_data_keys=list(request.transaction_data.keys()),
        )

        # TODO: Implement actual scoring logic
        # For now, return a mock response

        score = 0.78  # Mock score
        confidence = 0.92  # Mock confidence

        factors = [
            "merchant_category",
            "transaction_amount",
            "user_history",
            "time_of_day",
        ]

        response = ScoreResponse(
            score=score,
            confidence=confidence,
            factors=factors,
            metadata={"model_version": "v0.1.0"},
        )

        logger.info(
            "Transaction scoring completed",
            score=response.score,
            confidence=response.confidence,
        )

        return response

    def display_recommendations(self, response: CheckoutResponse) -> None:
        """Display recommendations in a formatted table.

        Args:
            response: The checkout response with recommendations
        """
        table = Table(title="Card Recommendations")
        table.add_column("Card", style="cyan")
        table.add_column("Cashback Rate", style="green")
        table.add_column("Reason", style="yellow")

        for rec in response.recommendations:
            table.add_row(rec["name"], f"{rec['cashback_rate']:.1%}", rec["reason"])

        self.console.print(table)
        self.console.print(f"Transaction Score: {response.score:.2f}")
        self.console.print(f"Status: {response.status}")
