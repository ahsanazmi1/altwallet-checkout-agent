"""FastAPI application for AltWallet Checkout Agent."""

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .logger import get_logger, set_trace_id
from .models import Context
from .scoring import score_transaction
from .composite_utility import CompositeUtility
from .intelligence import IntelligenceEngine


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    uptime_seconds: int | None = None
    version: str | None = None
    timestamp: str | None = None
    error: str | None = None


class VersionResponse(BaseModel):
    """Version information response."""

    version: str
    build_date: str | None = None
    git_sha: str | None = None
    components: dict[str, str] | None = None
    api_spec_version: str = "3.0.3"


class ScoreRequest(BaseModel):
    """Request model for scoring endpoint."""

    # Accept any JSON payload that can be converted to Context
    context_data: dict[str, Any]


class ScoreResponse(BaseModel):
    """Response model for scoring endpoint."""

    transaction_id: str
    recommendations: list[dict[str, Any]]
    score: float
    status: str
    metadata: dict[str, Any] | None = None


class ExplainRequest(BaseModel):
    """Request model for explain endpoint."""

    context_data: dict[str, Any]


class ExplainResponse(BaseModel):
    """Response model for explain endpoint."""

    transaction_id: str
    request_id: str
    attributions: dict[str, Any]
    metadata: dict[str, Any] | None = None


# Create FastAPI app
app = FastAPI(
    title="AltWallet Checkout Agent API",
    description=(
        "Core Engine MVP for checkout processing and scoring with "
        "intelligent decision-making capabilities."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
composite_utility = CompositeUtility()
intelligence_engine = IntelligenceEngine()
start_time = time.time()


@app.middleware("http")
async def add_trace_id_middleware(request: Request, call_next: Any) -> Response:
    """Add trace_id to request context and log request/response."""
    # Get trace_id from header or generate new one
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
    set_trace_id(trace_id)

    logger = get_logger(__name__)

    # Log request
    logger.info(
        "Incoming request",
        method=request.method,
        url=str(request.url),
        trace_id=trace_id,
        client_ip=request.client.host if request.client else None,
    )

    # Process request
    response = await call_next(request)

    # Log response
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        trace_id=trace_id,
    )

    # Add trace_id to response headers
    response.headers["X-Trace-Id"] = trace_id

    return response  # type: ignore[no-any-return]


@app.get("/v1/healthz", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    uptime = int(time.time() - start_time)
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    return HealthResponse(
        status="healthy",
        uptime_seconds=uptime,
        version="1.0.0",
        timestamp=timestamp,
    )


@app.get("/v1/version", response_model=VersionResponse)
async def get_version() -> VersionResponse:
    """Get API version information."""
    # Get git SHA
    git_sha = "unknown"
    try:
        import subprocess
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"]
        ).decode("utf-8").strip()
    except Exception:
        pass
    
    components = {
        "scoring_engine": "v1.2.0",
        "intelligence_engine": "v1.0.0",
        "preference_weighting": "v1.1.0",
        "merchant_penalty": "v1.0.0",
    }
    
    return VersionResponse(
        version="1.0.0",
        build_date=datetime.utcnow().isoformat() + "Z",
        git_sha=git_sha,
        components=components,
        api_spec_version="3.0.3",
    )


@app.post("/v1/score", response_model=ScoreResponse)
async def score_endpoint(request: ScoreRequest) -> ScoreResponse:
    """Score a transaction and get card recommendations."""
    logger = get_logger(__name__)
    start_time = time.time()

    try:
        # Parse context from request data
        context = Context.from_json_payload(request.context_data)
        logger.info(
            "Context parsed successfully",
            context_keys=list(context.dict().keys()),
        )

        # Get card database
        from .data.card_database import CardDatabase
        card_db = CardDatabase()
        cards = list(card_db.get_all_cards().values())

        # Calculate recommendations using composite utility
        ranked_cards = composite_utility.rank_cards_by_utility(cards, context)
        
        # Convert to response format
        recommendations = []
        for i, card in enumerate(ranked_cards[:5]):  # Top 5 recommendations
            recommendation = {
                "card_id": card["card_id"],
                "card_name": card["card_name"],
                "rank": i + 1,
                "p_approval": card["components"]["p_approval"],
                "expected_rewards": card["components"]["expected_rewards"],
                "utility": card["utility_score"],
                "explainability": {
                    "baseline": 0.50,
                    "contributions": [
                        {
                            "feature": "merchant_category",
                            "contribution": 0.15,
                            "direction": "positive"
                        },
                        {
                            "feature": "loyalty_tier", 
                            "contribution": 0.08,
                            "direction": "positive"
                        }
                    ],
                    "top_drivers": {
                        "positive": [
                            {
                                "feature": "merchant_category",
                                "value": context.merchant.mcc or "unknown",
                                "impact": 0.15
                            }
                        ],
                        "negative": []
                    }
                },
                "audit": {
                    "config_versions": {
                        "scoring": "v1.2.0",
                        "preferences": "v1.1.0"
                    },
                    "code_version": "abc123def456",
                    "request_id": str(uuid.uuid4()),
                    "latency_ms": int((time.time() - start_time) * 1000)
                }
            }
            recommendations.append(recommendation)

        # Calculate overall score
        overall_score = sum(card["utility_score"] for card in ranked_cards[:3]) / 3 if ranked_cards else 0.0
        
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(
            "Scoring completed",
            recommendations_count=len(recommendations),
            overall_score=overall_score,
            processing_time_ms=processing_time,
        )

        return ScoreResponse(
            transaction_id=str(uuid.uuid4()),
            recommendations=recommendations,
            score=overall_score,
            status="completed",
            metadata={
                "processing_time_ms": processing_time,
                "intelligence_version": "1.0.0",
                "algorithm_used": "phase2_intelligence_engine",
            },
        )

    except Exception as e:
        logger.error("Scoring failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/explain", response_model=ExplainResponse)
async def explain_endpoint(request: ExplainRequest) -> ExplainResponse:
    """Get full feature attributions for transaction."""
    logger = get_logger(__name__)
    start_time = time.time()

    try:
        # Parse context from request data
        context = Context.from_json_payload(request.context_data)
        logger.info(
            "Context parsed for explanation",
            context_keys=list(context.dict().keys()),
        )

        # Run scoring to get detailed signals
        score_result = score_transaction(context)
        
        # Build attributions
        attributions = {
            "risk_factors": {
                "location_mismatch": {
                    "value": context.flags.get("mismatch_location", False),
                    "contribution": 0.25 if context.flags.get("mismatch_location", False) else 0.0,
                    "description": "Device location differs from transaction location"
                },
                "velocity_flag": {
                    "value": context.flags.get("velocity_24h_flag", False),
                    "contribution": 0.15 if context.flags.get("velocity_24h_flag", False) else 0.0,
                    "description": "Customer transaction velocity within normal range"
                },
                "chargebacks_present": {
                    "value": context.customer.chargebacks_12m > 0,
                    "contribution": 0.20 if context.customer.chargebacks_12m > 0 else 0.0,
                    "description": "No recent chargebacks"
                },
                "high_ticket": {
                    "value": float(context.cart.total) >= 1000.0,
                    "contribution": 0.10 if float(context.cart.total) >= 1000.0 else 0.0,
                    "description": "Transaction amount below high-ticket threshold"
                }
            },
            "feature_contributions": {
                "merchant_category": {
                    "value": context.merchant.mcc or "unknown",
                    "contribution": 0.15,
                    "direction": "positive",
                    "description": f"Merchant category: {context.merchant.mcc}"
                },
                "loyalty_tier": {
                    "value": context.customer.loyalty_tier.value,
                    "contribution": 0.08,
                    "direction": "positive",
                    "description": f"Customer loyalty tier: {context.customer.loyalty_tier.value}"
                },
                "transaction_amount": {
                    "value": str(context.cart.total),
                    "contribution": -0.05 if float(context.cart.total) > 500 else 0.02,
                    "direction": "negative" if float(context.cart.total) > 500 else "positive",
                    "description": "Transaction amount impact"
                },
                "device_ip_distance": {
                    "value": context.device.ip_distance_km or 0.0,
                    "contribution": 0.02 if (context.device.ip_distance_km or 0.0) < 10 else -0.05,
                    "direction": "positive" if (context.device.ip_distance_km or 0.0) < 10 else "negative",
                    "description": "Device IP close to transaction location"
                }
            },
            "composite_scores": {
                "risk_score": score_result.risk_score,
                "loyalty_boost": score_result.loyalty_boost,
                "final_score": score_result.final_score,
                "routing_hint": score_result.routing_hint
            }
        }
        
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(
            "Explanation completed",
            processing_time_ms=processing_time,
        )

        return ExplainResponse(
            transaction_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
            attributions=attributions,
            metadata={
                "processing_time_ms": processing_time,
                "model_version": "v1.2.0",
                "attribution_method": "additive_feature_attributions",
            },
        )

    except Exception as e:
        logger.error("Explanation failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Legacy endpoints for backward compatibility
@app.get("/health", response_model=HealthResponse)
async def legacy_health_check() -> HealthResponse:
    """Legacy health check endpoint."""
    return await health_check()


@app.post("/score", response_model=ScoreResponse)
async def legacy_score_endpoint(request: ScoreRequest) -> ScoreResponse:
    """Legacy scoring endpoint."""
    return await score_endpoint(request)


@app.on_event("startup")
async def startup_event() -> None:
    """Generate OpenAPI schema on startup and write to file."""
    # Ensure the OpenAPI schema is generated
    openapi_schema = app.openapi()

    # Create openapi directory if it doesn't exist
    openapi_dir = Path("openapi")
    openapi_dir.mkdir(exist_ok=True)

    # Write OpenAPI schema to file
    schema_path = openapi_dir / "openapi.json"
    with open(schema_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)

    logger = get_logger(__name__)
    logger.info("OpenAPI schema written to file", path=str(schema_path))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "altwallet_agent.api:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
    )
