"""
Windows-specific server launcher with ProactorEventLoop fix for psycopg3
This ensures psycopg3 async works correctly on Windows with Python 3.14+
"""
import sys
import os
import asyncio
from pathlib import Path

# CRITICAL: Force SelectorEventLoop BEFORE any imports
if sys.platform == "win32":
    # For Python 3.14+, we need to use the deprecated API but it still works
    import selectors
    selector = selectors.SelectSelector()
    loop = asyncio.SelectorEventLoop(selector)
    asyncio.set_event_loop(loop)

# Redirect output to UTF-8 files
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

stdout_log = log_dir / "uvicorn_stdout.log"
stderr_log = log_dir / "uvicorn_stderr.log"

sys.stdout = open(stdout_log, "w", encoding="utf-8", buffering=1)
sys.stderr = open(stderr_log, "w", encoding="utf-8", buffering=1)

print("=" * 80)
print("WINDOWS SERVER LAUNCHER WITH PROACTOR FIX")
print("=" * 80)
print(f"Python version: {sys.version}")
print(f"Platform: {sys.platform}")
print(f"Stdout log: {stdout_log}")
print(f"Stderr log: {stderr_log}")

# Now import uvicorn and app AFTER setting the loop
from uvicorn import Config, Server

async def main():
    """Run server in existing SelectorEventLoop"""
    # Verify we have the right loop
    current_loop = asyncio.get_running_loop()
    print(f"Event loop type: {type(current_loop).__name__}")

    if "Selector" not in type(current_loop).__name__:
        print("WARNING: Not using SelectorEventLoop!")
    else:
        print("SUCCESS: Using SelectorEventLoop for psycopg3 compatibility")

    # Configure server
    config = Config(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        loop="asyncio",  # Use asyncio integration
        access_log=True
    )

    server = Server(config)
    await server.serve()

if __name__ == "__main__":
    print("\nStarting server...")

    # Run with our pre-configured SelectorEventLoop
    try:
        loop = asyncio.get_event_loop()
        print(f"Using event loop: {type(loop).__name__}")
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"\nServer error: {e}")
        import traceback
        traceback.print_exc()