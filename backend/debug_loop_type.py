"""Debug: Check what type of event loop is created"""
import sys
import asyncio

print("=" * 80)
print("TESTING EVENT LOOP CREATION WITH POLICY")
print("=" * 80)

# Step 1: Check default policy
default_policy = asyncio.get_event_loop_policy()
print(f"1. Default policy: {type(default_policy).__name__}")

# Step 2: Set WindowsSelectorEventLoopPolicy
if sys.platform == "win32":
    print("\n2. Setting WindowsSelectorEventLoopPolicy...")
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    new_policy = asyncio.get_event_loop_policy()
    print(f"   Policy after set: {type(new_policy).__name__}")

# Step 3: Create new event loop
print("\n3. Creating new event loop with new_event_loop()...")
loop = asyncio.new_event_loop()
print(f"   Loop type: {type(loop).__name__}")
print(f"   Is ProactorEventLoop: {type(loop).__name__ == '_ProactorEventLoop'}")
print(f"   Is SelectorEventLoop: {type(loop).__name__ == '_WindowsSelectorEventLoop'}")

asyncio.set_event_loop(loop)

# Step 4: Verify running loop
async def test():
    running_loop = asyncio.get_running_loop()
    print(f"\n4. Running loop type: {type(running_loop).__name__}")
    return type(running_loop).__name__

result = loop.run_until_complete(test())
print(f"   Result: {result}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print(f"Final loop type: {type(loop).__name__}")
print(f"SUCCESS: Loop is SelectorEventLoop" if 'Selector' in type(loop).__name__ else "FAIL: Loop is still ProactorEventLoop")
