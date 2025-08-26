"""FastAPI application for AltWallet Checkout Agent."""

import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .logger import get_logger, set_trace_id
from .models import Context
from .scoring import score_transaction


class HealthResponse(BaseModel):
    """Health check response."""

    status: str


class ScoreRequest(BaseModel):
    """Request model for scoring endpoint."""

    # Accept any JSON payload that can be converted to Context
    context_data: dict[str, Any]


class ScoreResponse(BaseModel):
    """Response model for scoring endpoint."""

    trace_id: str
    risk_score: int
    loyalty_boost: int
    final_score: int
    routing_hint: str
    signals: dict[str, Any]


# Create FastAPI app
app = FastAPI(
    title="AltWallet Checkout Agent API",
    description="Core Engine MVP for checkout processing and scoring",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

    return response


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok")


@app.post("/score", response_model=ScoreResponse)
async def score_endpoint(request: ScoreRequest) -> ScoreResponse:
    """Score a transaction based on provided context data."""
    logger = get_logger(__name__)

    try:
        # Parse context from request data
        context = Context.from_json_payload(request.context_data)
        logger.info(
            "Context parsed successfully",
            context_keys=list(context.dict().keys()),
        )

        # Run scoring
        logger.info("Starting transaction scoring")
        result = score_transaction(context)

        logger.info(
            "Scoring completed",
            final_score=result.final_score,
            routing_hint=result.routing_hint,
            risk_score=result.risk_score,
            loyalty_boost=result.loyalty_boost,
        )

        # Get trace_id from context
        from .logger import trace_id_var

        trace_id = trace_id_var.get() or "unknown"

        # Return response in same format as CLI
        return ScoreResponse(
            trace_id=trace_id,
            risk_score=result.risk_score,
            loyalty_boost=result.loyalty_boost,
            final_score=result.final_score,
            routing_hint=result.routing_hint,
            signals=result.signals,
        )

    except Exception as e:
        logger.error("Scoring failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
