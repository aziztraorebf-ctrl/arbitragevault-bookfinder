"""Start uvicorn server with output redirected to file to avoid console encoding issues"""
import sys

# FIX: Set event loop policy BEFORE anything else on Windows
# ProactorEventLoop (Windows default) is incompatible with psycopg3
# This MUST execute BEFORE uvicorn creates its event loop
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import io
import uvicorn
from pathlib import Path

# Redirect stdout/stderr to UTF-8 files to avoid Windows CP1252 encoding issues
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

stdout_log = log_dir / "uvicorn_stdout.log"
stderr_log = log_dir / "uvicorn_stderr.log"

# Open log files with UTF-8 encoding
sys.stdout = open(stdout_log, "w", encoding="utf-8", buffering=1)
sys.stderr = open(stderr_log, "w", encoding="utf-8", buffering=1)

if __name__ == "__main__":
    print("Starting Uvicorn server with UTF-8 logging...")
    print(f"Stdout log: {stdout_log}")
    print(f"Stderr log: {stderr_log}")

    # CRITICAL: For Windows + Python 3.14 + psycopg3 async compatibility
    # We must create the event loop AFTER setting the policy
    # Standard uvicorn.run() creates ProactorEventLoop before we can intervene
    if sys.platform == "win32":
        import asyncio
        from uvicorn import Config, Server

        # FIRST: Set the policy BEFORE creating any loop
        # (The policy set at top of file doesn't affect new_event_loop())
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        # THEN: Create event loop (will use the policy we just set)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        config = Config(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            loop="none"  # Don't let uvicorn create its own loop
        )
        server = Server(config)

        print("Windows: Using SelectorEventLoop for psycopg3 compatibility")
        loop.run_until_complete(server.serve())
    else:
        # Linux/Mac: Standard uvicorn.run()
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
