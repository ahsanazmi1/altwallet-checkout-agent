"""Core CheckoutAgent implementation."""

import contextvars
import uuid
from typing import Any
import subprocess

import structlog
from rich.console import Console
from rich.table import Table

from .models import CheckoutRequest, CheckoutResponse, ScoreRequest, ScoreResponse

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
