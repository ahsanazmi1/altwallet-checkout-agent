#!/usr/bin/env python3
"""Start the AltWallet Checkout Agent API server."""

import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    import uvicorn
    from altwallet_agent.api import app

    print("🚀 Starting AltWallet Checkout Agent API Server...")
    print(f"📁 Project root: {project_root}")
    print(f"📁 Source path: {src_path}")
    print("🌐 API will be available at: http://localhost:8000")
    print("📚 API docs: http://localhost:8000/docs")
    print("🔍 Health check: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server\n")

    uvicorn.run(
        "altwallet_agent.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
