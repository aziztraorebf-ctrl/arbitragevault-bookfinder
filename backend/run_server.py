#!/usr/bin/env python3
"""
Startup script for FastAPI server with proper event loop configuration.

This script MUST run before uvicorn initializes to ensure Windows
uses SelectorEventLoop instead of ProactorEventLoop.
"""

# === CRITICAL: Configure event loop BEFORE any other imports ===
import sys
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# =================================================================

# Now import and run uvicorn
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Enable for development
    )
