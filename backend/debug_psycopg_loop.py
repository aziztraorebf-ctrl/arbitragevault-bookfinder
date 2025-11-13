"""Debug: Test psycopg3 connection with different event loops"""
import sys
import asyncio

# Set policy FIRST
if sys.platform == "win32":
    print("Setting WindowsSelectorEventLoopPolicy...")
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.settings import get_settings

async def test_connection():
    # Check which loop we're running in
    loop = asyncio.get_running_loop()
    print(f"\n1. Running loop type: {type(loop).__name__}")
    print(f"   Is Selector: {'Selector' in type(loop).__name__}")
    print(f"   Is Proactor: {'Proactor' in type(loop).__name__}")

    settings = get_settings()

    print(f"\n2. Creating async engine...")
    print(f"   Database URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else '***'}")

    try:
        engine = create_async_engine(
            settings.database_url,
            pool_size=1,
            max_overflow=0,
            pool_pre_ping=True,
            echo=False,
            connect_args={"ssl": "require"} if "render.com" in settings.database_url else {}
        )

        print(f"\n3. Testing connection...")
        async with engine.connect() as conn:
            result = await conn.execute(sqlalchemy.text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"   Connection SUCCESS: {row}")

        await engine.dispose()
        print("\n✅ SUCCESS: psycopg3 accepted the event loop")

    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}")
        print(f"   Message: {str(e)[:200]}")
        if "ProactorEventLoop" in str(e):
            print("\n   >>> This is the ProactorEventLoop error!")

if __name__ == "__main__":
    import sqlalchemy

    print("=" * 80)
    print("TESTING PSYCOPG3 WITH EVENT LOOP")
    print("=" * 80)

    # Run with our event loop
    asyncio.run(test_connection())

    print("\n" + "=" * 80)
