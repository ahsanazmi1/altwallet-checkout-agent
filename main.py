"""
AltWallet Checkout Agent - Python FastAPI Version
"""

import os
import uuid
from datetime import datetime
from typing import Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AltWallet Checkout Agent",
    description="A checkout agent system for AltWallet payment processing",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class TransactionRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(
        ..., min_length=3, max_length=3, description="Currency code (e.g., USD)"
    )
    merchant_id: str = Field(..., description="Merchant identifier")
    description: str | None = Field(None, description="Transaction description")
    customer_email: str | None = Field(None, description="Customer email")


class TransactionResponse(BaseModel):
    transaction_id: str
    success: bool
    message: str
    data: dict[str, Any] | None = None
    timestamp: datetime


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str


# Global state (in production, use a proper database)
transactions: dict[str, dict[str, Any]] = {}
agent_status = "ready"


class CheckoutAgent:
    def __init__(self):
        self.transactions = {}
        self.status = "idle"
        from altwallet_agent.config import get_config
        config = get_config()
        self.config = {
            "api_key": config.api_key,
            "endpoint": config.api_endpoint,
            "timeout": config.timeout,
        }

    async def initialize(self):
        """Initialize the checkout agent"""
        try:
            self.status = "initializing"
            logger.info("🔄 Initializing AltWallet Checkout Agent...")

            # Validate configuration
            if not self.config["api_key"]:
                logger.warning("⚠️ AltWallet API key not configured")

            self.status = "ready"
            logger.info("✅ AltWallet Checkout Agent initialized successfully")
            return True
        except Exception as error:
            self.status = "error"
            logger.error(f"❌ Failed to initialize checkout agent: {error}")
            raise error

    async def process_checkout(
        self, transaction_data: TransactionRequest
    ) -> TransactionResponse:
        """Process a checkout transaction"""
        try:
            transaction_id = self.generate_transaction_id()

            logger.info(f"💳 Processing checkout transaction: {transaction_id}")

            # Create transaction record
            transaction = {
                "id": transaction_id,
                "data": transaction_data.dict(),
                "status": "processing",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            self.transactions[transaction_id] = transaction

            # Process the payment
            result = await self.process_payment(transaction_data)

            # Update transaction status
            transaction["status"] = "completed" if result["success"] else "failed"
            transaction["result"] = result
            transaction["updated_at"] = datetime.utcnow()

            logger.info(f"✅ Transaction {transaction_id} {transaction['status']}")

            return TransactionResponse(
                transaction_id=transaction_id,
                success=result["success"],
                message=result["message"],
                data=result.get("data"),
                timestamp=datetime.utcnow(),
            )

        except Exception as error:
            logger.error(f"❌ Checkout processing failed: {error}")
            raise HTTPException(status_code=500, detail=str(error))

    async def process_payment(
        self, transaction_data: TransactionRequest
    ) -> dict[str, Any]:
        """Process payment with AltWallet API"""
        # TODO: Implement actual AltWallet API integration
        logger.info("💰 Processing payment with AltWallet...")

        # Simulate API call
        import asyncio

        await asyncio.sleep(1)

        # Simulate successful payment
        return {
            "success": True,
            "message": "Payment processed successfully",
            "data": {
                "payment_id": f"pay_{int(datetime.utcnow().timestamp())}",
                "amount": transaction_data.amount,
                "currency": transaction_data.currency,
                "status": "approved",
            },
        }

    def generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        return f"txn_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:8]}"

    def get_transaction_status(self, transaction_id: str) -> dict[str, Any] | None:
        """Get transaction status"""
        transaction = self.transactions.get(transaction_id)
        if transaction:
            return {
                "id": transaction["id"],
                "status": transaction["status"],
                "created_at": transaction["created_at"],
                "updated_at": transaction["updated_at"],
            }
        return None

    def get_status(self) -> dict[str, Any]:
        """Get agent status"""
        return {
            "status": self.status,
            "active_transactions": len(self.transactions),
            "uptime": datetime.utcnow(),
        }


# Initialize the checkout agent
checkout_agent = CheckoutAgent()


@app.on_event("startup")
async def startup_event():
    """Initialize the checkout agent on startup"""
    await checkout_agent.initialize()


# API Routes
@app.get("/", response_model=dict[str, Any])
async def root():
    """Root endpoint"""
    return {
        "message": "AltWallet Checkout Agent API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow(),
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy", timestamp=datetime.utcnow(), version="1.0.0"
    )


@app.post("/checkout", response_model=TransactionResponse)
async def process_checkout(transaction: TransactionRequest):
    """Process a checkout transaction"""
    return await checkout_agent.process_checkout(transaction)


@app.get("/transaction/{transaction_id}")
async def get_transaction_status(transaction_id: str):
    """Get transaction status"""
    status = checkout_agent.get_transaction_status(transaction_id)
    if not status:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return status


@app.get("/status")
async def get_agent_status():
    """Get agent status"""
    return checkout_agent.get_status()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
