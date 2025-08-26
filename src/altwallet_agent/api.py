"""FastAPI application for AltWallet Checkout Agent."""

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .core import CheckoutAgent
from .models import CheckoutRequest, CheckoutResponse, ScoreRequest, ScoreResponse

# Create FastAPI app
app = FastAPI(
    title="AltWallet Checkout Agent API",
    description="Core Engine MVP for checkout processing and scoring",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Global agent instance
agent = CheckoutAgent()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: str


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    import datetime
    from . import __version__

    return HealthResponse(
        status="healthy",
        version=__version__,
        timestamp=datetime.datetime.utcnow().isoformat(),
    )


@app.post("/score", response_model=ScoreResponse)
async def score_endpoint(request: ScoreRequest) -> ScoreResponse:
    """Score a transaction based on provided data."""
    try:
        return agent.score_transaction(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/checkout", response_model=CheckoutResponse)
async def checkout_endpoint(request: CheckoutRequest) -> CheckoutResponse:
    """Process a checkout request and return recommendations."""
    try:
        return agent.process_checkout(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/openapi.json")
async def get_openapi_schema() -> Dict[str, Any]:
    """Get OpenAPI schema."""
    return app.openapi()


@app.on_event("startup")
async def startup_event() -> None:
    """Generate OpenAPI schema on startup."""
    # Ensure the OpenAPI schema is generated
    app.openapi()

    # Optionally save to file
    openapi_schema = app.openapi()
    schema_path = Path("openapi.json")
    with open(schema_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "altwallet_agent.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
