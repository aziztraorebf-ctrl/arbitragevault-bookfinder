#!/usr/bin/env python3
"""Debug status validation."""

from app.models.batch import BatchStatus

# Test les valeurs
print("BatchStatus values:")
for s in BatchStatus:
    print(f"  {s.name} = {s.value}")

print(f"\nValid statuses list: {[s.value for s in BatchStatus]}")
print(f"'pending' in list: {'pending' in [s.value for s in BatchStatus]}")

# Test with string
test_status = "pending"
print(f"\nTest status: {test_status}")
print(f"Type: {type(test_status)}")

# Import schema
from app.schemas.batch import BatchStatusUpdate
data = {"status": "pending"}
try:
    update = BatchStatusUpdate(**data)
    print(f"✅ Schema parsing OK: {update.status}, type: {type(update.status)}")
except Exception as e:
    print(f"❌ Schema parsing error: {e}")