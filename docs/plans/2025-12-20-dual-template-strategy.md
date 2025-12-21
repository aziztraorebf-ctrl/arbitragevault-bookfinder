# Dual Template Strategy + Pre-Purchase Verification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement Standard and Patience textbook templates aligned with PDF guide strategy, plus a lightweight pre-purchase verification button.

**Architecture:**
- Add two new strategy types to STRATEGY_CONFIGS: `textbooks_standard` and `textbooks_patience`
- Update existing textbook templates to use corrected parameters based on test results
- Add single `/verify` endpoint for real-time product status check
- Frontend gets one new "Verify" button component

**Tech Stack:** FastAPI, Pydantic, React, TypeScript, Keepa API

---

## Task 1: Add New Strategy Configs

**Files:**
- Modify: `backend/app/services/niche_templates.py:26-45`
- Test: `backend/tests/unit/test_niche_templates_hostile.py`

**Step 1: Write the failing test**

Add to `backend/tests/unit/test_niche_templates_hostile.py`:

```python
class TestDualTemplateStrategy:
    """Tests for Standard and Patience textbook strategies."""

    def test_textbooks_standard_config_exists(self):
        """Standard textbook strategy must exist."""
        assert "textbooks_standard" in STRATEGY_CONFIGS
        config = STRATEGY_CONFIGS["textbooks_standard"]
        assert config["bsr_range"] == (100000, 250000)
        assert config["min_margin"] == 15.0
        assert config["max_fba_sellers"] == 5
        assert config["price_range"] == (40.0, 150.0)

    def test_textbooks_patience_config_exists(self):
        """Patience textbook strategy must exist with stricter criteria."""
        assert "textbooks_patience" in STRATEGY_CONFIGS
        config = STRATEGY_CONFIGS["textbooks_patience"]
        assert config["bsr_range"] == (250000, 400000)
        assert config["min_margin"] == 25.0
        assert config["max_fba_sellers"] == 3
        assert config["price_range"] == (40.0, 150.0)

    def test_patience_has_warning_message(self):
        """Patience strategy must include rotation warning."""
        config = STRATEGY_CONFIGS["textbooks_patience"]
        assert "warning" in config
        assert "4-6" in config["warning"] or "semaines" in config["warning"].lower()
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/unit/test_niche_templates_hostile.py::TestDualTemplateStrategy -v
```

Expected: FAIL with "KeyError: 'textbooks_standard'"

**Step 3: Write minimal implementation**

Modify `backend/app/services/niche_templates.py` - replace STRATEGY_CONFIGS (lines 26-45):

```python
# Strategy type definitions for filtering
STRATEGY_CONFIGS = {
    "smart_velocity": {
        "description": "Fast rotation books with reasonable margin - BSR 10K-80K",
        "bsr_range": (10000, 80000),
        "min_margin": 12.0,
        "max_fba_sellers": 5,
        "price_range": (15.0, 60.0),
        "min_roi": 30,
        "min_velocity": 50
    },
    "textbooks": {
        "description": "Legacy textbook strategy - use textbooks_standard or textbooks_patience instead",
        "bsr_range": (30000, 250000),
        "min_margin": 20.0,
        "max_fba_sellers": 3,
        "price_range": (30.0, 150.0),
        "min_roi": 50,
        "min_velocity": 30
    },
    "textbooks_standard": {
        "description": "PDF Golden Rule textbooks - BSR 100K-250K, balanced rotation/profit",
        "bsr_range": (100000, 250000),
        "min_margin": 15.0,
        "max_fba_sellers": 5,
        "price_range": (40.0, 150.0),
        "min_roi": 40,
        "min_velocity": 30,
        "estimated_rotation_days": "7-14"
    },
    "textbooks_patience": {
        "description": "Under-the-radar textbooks - BSR 250K-400K, higher profit, slower rotation",
        "bsr_range": (250000, 400000),
        "min_margin": 25.0,
        "max_fba_sellers": 3,
        "price_range": (40.0, 150.0),
        "min_roi": 50,
        "min_velocity": 20,
        "estimated_rotation_days": "28-42",
        "warning": "Rotation lente (4-6 semaines minimum). Capital immobilise plus longtemps."
    }
}
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/unit/test_niche_templates_hostile.py::TestDualTemplateStrategy -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/niche_templates.py backend/tests/unit/test_niche_templates_hostile.py
git commit -m "feat(templates): add textbooks_standard and textbooks_patience strategies"
```

---

## Task 2: Create Standard Textbook Templates

**Files:**
- Modify: `backend/app/services/niche_templates.py:168-270`
- Test: `backend/tests/unit/test_niche_templates_hostile.py`

**Step 1: Write the failing test**

Add to `backend/tests/unit/test_niche_templates_hostile.py`:

```python
def test_standard_textbook_templates_exist(self):
    """At least one template with type textbooks_standard must exist."""
    standard_templates = [t for t in CURATED_NICHES if t["type"] == "textbooks_standard"]
    assert len(standard_templates) >= 1, "No textbooks_standard templates found"

    for tmpl in standard_templates:
        assert tmpl["bsr_range"][0] >= 100000, f"{tmpl['id']}: BSR min should be >= 100K"
        assert tmpl["bsr_range"][1] <= 250000, f"{tmpl['id']}: BSR max should be <= 250K"
        assert tmpl["price_range"][0] >= 40.0, f"{tmpl['id']}: Price min should be >= $40"
        assert tmpl["max_fba_sellers"] == 5, f"{tmpl['id']}: max_fba should be 5"

def test_patience_textbook_templates_exist(self):
    """At least one template with type textbooks_patience must exist."""
    patience_templates = [t for t in CURATED_NICHES if t["type"] == "textbooks_patience"]
    assert len(patience_templates) >= 1, "No textbooks_patience templates found"

    for tmpl in patience_templates:
        assert tmpl["bsr_range"][0] >= 250000, f"{tmpl['id']}: BSR min should be >= 250K"
        assert tmpl["bsr_range"][1] <= 400000, f"{tmpl['id']}: BSR max should be <= 400K"
        assert tmpl["min_margin"] >= 25.0, f"{tmpl['id']}: min_margin should be >= $25"
        assert tmpl["max_fba_sellers"] <= 3, f"{tmpl['id']}: max_fba should be <= 3"
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/unit/test_niche_templates_hostile.py::TestDualTemplateStrategy::test_standard_textbook_templates_exist -v
```

Expected: FAIL

**Step 3: Write minimal implementation**

Add new templates to CURATED_NICHES in `backend/app/services/niche_templates.py` after line 269:

```python
    # ============================================
    # TEXTBOOK STANDARD TEMPLATES (BSR 100K-250K, $15+ margin)
    # PDF Golden Rule aligned - balanced rotation and profit
    # ============================================
    {
        "id": "textbook-standard-general",
        "name": "[STANDARD] General Textbooks",
        "description": "General academic textbooks - PDF Golden Rule BSR range, balanced approach",
        "type": "textbooks_standard",
        "categories": [283155],  # Books root
        "bsr_range": (100000, 250000),
        "price_range": (40.0, 150.0),
        "min_margin": 15.0,
        "max_fba_sellers": 5,
        "min_roi": 40,
        "min_velocity": 30,
        "icon": "TEXTBOOK"
    },
    {
        "id": "textbook-standard-business",
        "name": "[STANDARD] Business Textbooks",
        "description": "Business/Economics textbooks - moderate rotation, good profit",
        "type": "textbooks_standard",
        "categories": [2, 2766, 2767],
        "bsr_range": (100000, 250000),
        "price_range": (40.0, 150.0),
        "min_margin": 15.0,
        "max_fba_sellers": 5,
        "min_roi": 40,
        "min_velocity": 30,
        "icon": "BUSINESS"
    },
    # ============================================
    # TEXTBOOK PATIENCE TEMPLATES (BSR 250K-400K, $25+ margin)
    # Under the radar - higher profit, slower rotation
    # ============================================
    {
        "id": "textbook-patience-general",
        "name": "[PATIENCE] Under-Radar Textbooks",
        "description": "Higher BSR textbooks - less competition, higher profit, 4-6 week rotation",
        "type": "textbooks_patience",
        "categories": [283155],
        "bsr_range": (250000, 400000),
        "price_range": (40.0, 150.0),
        "min_margin": 25.0,
        "max_fba_sellers": 3,
        "min_roi": 50,
        "min_velocity": 20,
        "icon": "PATIENCE"
    },
    {
        "id": "textbook-patience-specialized",
        "name": "[PATIENCE] Specialized Academic",
        "description": "Niche academic subjects - very low competition, premium profit margins",
        "type": "textbooks_patience",
        "categories": [75, 173514, 13611],  # Science, Medical, Engineering
        "bsr_range": (250000, 400000),
        "price_range": (50.0, 150.0),
        "min_margin": 25.0,
        "max_fba_sellers": 3,
        "min_roi": 50,
        "min_velocity": 15,
        "icon": "SPECIALIZED"
    },
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/unit/test_niche_templates_hostile.py::TestDualTemplateStrategy -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/niche_templates.py backend/tests/unit/test_niche_templates_hostile.py
git commit -m "feat(templates): add Standard and Patience textbook templates"
```

---

## Task 3: Create Verification Schema

**Files:**
- Create: `backend/app/schemas/verification.py`
- Test: `backend/tests/schemas/test_verification_schema.py`

**Step 1: Write the failing test**

Create `backend/tests/schemas/test_verification_schema.py`:

```python
"""Tests for product verification schema."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.verification import (
    VerificationRequest,
    VerificationResponse,
    VerificationStatus,
    VerificationChanges,
)


class TestVerificationSchema:
    """Tests for verification Pydantic models."""

    def test_verification_request_valid(self):
        """Valid ASIN should pass."""
        req = VerificationRequest(asin="B0B3DB4FJ3")
        assert req.asin == "B0B3DB4FJ3"

    def test_verification_request_invalid_asin(self):
        """Empty ASIN should fail."""
        with pytest.raises(ValidationError):
            VerificationRequest(asin="")

    def test_verification_response_ok_status(self):
        """OK status response structure."""
        resp = VerificationResponse(
            asin="B0B3DB4FJ3",
            verified_at=datetime.now(),
            status=VerificationStatus.OK,
            changes=VerificationChanges(
                amazon_now_selling=False,
                fba_count_increased=False,
                price_dropped=False,
                original_price=89.0,
                current_price=89.0
            )
        )
        assert resp.status == VerificationStatus.OK

    def test_verification_response_avoid_status(self):
        """AVOID status when Amazon is selling."""
        resp = VerificationResponse(
            asin="B0B3DB4FJ3",
            verified_at=datetime.now(),
            status=VerificationStatus.AVOID,
            changes=VerificationChanges(
                amazon_now_selling=True,
                fba_count_increased=False,
                price_dropped=False,
                original_price=89.0,
                current_price=89.0
            ),
            reason="Amazon is now selling this product"
        )
        assert resp.status == VerificationStatus.AVOID
        assert "Amazon" in resp.reason
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/schemas/test_verification_schema.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `backend/app/schemas/verification.py`:

```python
"""
Product Verification Schemas

Used for pre-purchase verification of product status.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class VerificationStatus(str, Enum):
    """Status of product verification."""
    OK = "OK"           # No changes, safe to buy
    CHANGED = "CHANGED" # Some metrics changed, review needed
    AVOID = "AVOID"     # Critical change, do not buy


class VerificationChanges(BaseModel):
    """Details of what changed since last check."""
    amazon_now_selling: bool = Field(
        False,
        description="True if Amazon started selling this product"
    )
    fba_count_increased: bool = Field(
        False,
        description="True if FBA seller count increased significantly"
    )
    price_dropped: bool = Field(
        False,
        description="True if price dropped more than 10%"
    )
    original_price: Optional[float] = Field(
        None,
        description="Price at discovery time"
    )
    current_price: Optional[float] = Field(
        None,
        description="Current price"
    )
    original_fba_count: Optional[int] = Field(
        None,
        description="FBA count at discovery"
    )
    current_fba_count: Optional[int] = Field(
        None,
        description="Current FBA count"
    )


class VerificationRequest(BaseModel):
    """Request to verify a product before purchase."""
    asin: str = Field(..., min_length=10, max_length=10, description="Product ASIN")
    original_price: Optional[float] = Field(None, description="Price when discovered")
    original_fba_count: Optional[int] = Field(None, description="FBA count when discovered")

    @field_validator("asin")
    @classmethod
    def validate_asin(cls, v: str) -> str:
        if not v or len(v) != 10:
            raise ValueError("ASIN must be exactly 10 characters")
        return v.upper()


class VerificationResponse(BaseModel):
    """Response from product verification."""
    asin: str
    verified_at: datetime
    status: VerificationStatus
    changes: VerificationChanges
    reason: Optional[str] = Field(
        None,
        description="Human-readable reason for status"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "asin": "B0B3DB4FJ3",
                "verified_at": "2025-12-20T18:45:00Z",
                "status": "OK",
                "changes": {
                    "amazon_now_selling": False,
                    "fba_count_increased": False,
                    "price_dropped": False,
                    "original_price": 89.0,
                    "current_price": 89.0
                },
                "reason": None
            }
        }
    }
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/schemas/test_verification_schema.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
mkdir -p backend/tests/schemas
touch backend/tests/schemas/__init__.py
git add backend/app/schemas/verification.py backend/tests/schemas/
git commit -m "feat(schemas): add verification request/response models"
```

---

## Task 4: Create Verification Service

**Files:**
- Create: `backend/app/services/verification_service.py`
- Test: `backend/tests/services/test_verification_service.py`

**Step 1: Write the failing test**

Create `backend/tests/services/test_verification_service.py`:

```python
"""Tests for verification service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.verification_service import VerificationService
from app.schemas.verification import VerificationStatus


class TestVerificationService:
    """Tests for VerificationService."""

    @pytest.fixture
    def mock_keepa_service(self):
        """Mock Keepa service."""
        service = MagicMock()
        service.get_product_data = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_verify_product_ok(self, mock_keepa_service):
        """Product unchanged returns OK status."""
        mock_keepa_service.get_product_data.return_value = {
            "products": [{
                "asin": "B0B3DB4FJ3",
                "availabilityAmazon": -1,
                "stats": {
                    "current": [None, 8900, None, 100000, None, None, None, None, None, None, None, 3]
                }
            }]
        }

        service = VerificationService(mock_keepa_service)
        result = await service.verify_product(
            asin="B0B3DB4FJ3",
            original_price=89.0,
            original_fba_count=3
        )

        assert result.status == VerificationStatus.OK
        assert result.changes.amazon_now_selling is False

    @pytest.mark.asyncio
    async def test_verify_product_amazon_selling(self, mock_keepa_service):
        """Amazon selling returns AVOID status."""
        mock_keepa_service.get_product_data.return_value = {
            "products": [{
                "asin": "B0B3DB4FJ3",
                "availabilityAmazon": 0,  # Amazon is selling
                "stats": {
                    "current": [8900, 8900, None, 100000, None, None, None, None, None, None, None, 3]
                }
            }]
        }

        service = VerificationService(mock_keepa_service)
        result = await service.verify_product(
            asin="B0B3DB4FJ3",
            original_price=89.0,
            original_fba_count=3
        )

        assert result.status == VerificationStatus.AVOID
        assert result.changes.amazon_now_selling is True
        assert "Amazon" in result.reason

    @pytest.mark.asyncio
    async def test_verify_product_price_dropped(self, mock_keepa_service):
        """Price dropped >10% returns CHANGED status."""
        mock_keepa_service.get_product_data.return_value = {
            "products": [{
                "asin": "B0B3DB4FJ3",
                "availabilityAmazon": -1,
                "stats": {
                    "current": [None, 7500, None, 100000, None, None, None, None, None, None, None, 3]
                }
            }]
        }

        service = VerificationService(mock_keepa_service)
        result = await service.verify_product(
            asin="B0B3DB4FJ3",
            original_price=89.0,
            original_fba_count=3
        )

        assert result.status == VerificationStatus.CHANGED
        assert result.changes.price_dropped is True
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/services/test_verification_service.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `backend/app/services/verification_service.py`:

```python
"""
Product Verification Service

Provides real-time verification of product status before purchase.
Uses Keepa API to check current Amazon availability, price, and competition.
"""

from datetime import datetime
from typing import Optional

from app.services.keepa_service import KeepaService
from app.schemas.verification import (
    VerificationResponse,
    VerificationStatus,
    VerificationChanges,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class VerificationService:
    """Service for pre-purchase product verification."""

    def __init__(self, keepa_service: KeepaService):
        self.keepa = keepa_service

    async def verify_product(
        self,
        asin: str,
        original_price: Optional[float] = None,
        original_fba_count: Optional[int] = None,
    ) -> VerificationResponse:
        """
        Verify product status before purchase.

        Args:
            asin: Product ASIN to verify
            original_price: Price when product was discovered (optional)
            original_fba_count: FBA seller count when discovered (optional)

        Returns:
            VerificationResponse with status and changes
        """
        logger.info(f"[VERIFY] Checking product {asin}")

        # Fetch fresh data from Keepa
        data = await self.keepa.get_product_data(asin)

        if not data or "products" not in data or not data["products"]:
            return VerificationResponse(
                asin=asin,
                verified_at=datetime.now(),
                status=VerificationStatus.AVOID,
                changes=VerificationChanges(),
                reason="Product not found or API error"
            )

        product = data["products"][0]
        stats = product.get("stats", {})
        current = stats.get("current", [])

        # Extract current values
        availability_amazon = product.get("availabilityAmazon", -1)
        current_price_cents = current[1] if len(current) > 1 else None
        current_price = current_price_cents / 100 if current_price_cents else None
        current_fba = current[11] if len(current) > 11 else None

        # Build changes object
        changes = VerificationChanges(
            original_price=original_price,
            current_price=current_price,
            original_fba_count=original_fba_count,
            current_fba_count=current_fba
        )

        # Check for critical issues
        reasons = []

        # 1. Amazon selling = AVOID
        if availability_amazon is not None and availability_amazon >= 0:
            changes.amazon_now_selling = True
            reasons.append("Amazon is now selling this product")

        # 2. FBA count increased significantly
        if original_fba_count is not None and current_fba is not None:
            if current_fba > original_fba_count + 2:
                changes.fba_count_increased = True
                reasons.append(f"FBA sellers increased from {original_fba_count} to {current_fba}")

        # 3. Price dropped >10%
        if original_price is not None and current_price is not None:
            price_change = (current_price - original_price) / original_price
            if price_change < -0.10:
                changes.price_dropped = True
                reasons.append(f"Price dropped {abs(price_change)*100:.0f}% (${original_price:.2f} -> ${current_price:.2f})")

        # Determine status
        if changes.amazon_now_selling:
            status = VerificationStatus.AVOID
        elif changes.fba_count_increased or changes.price_dropped:
            status = VerificationStatus.CHANGED
        else:
            status = VerificationStatus.OK

        reason = "; ".join(reasons) if reasons else None

        logger.info(f"[VERIFY] {asin} status={status.value} reason={reason}")

        return VerificationResponse(
            asin=asin,
            verified_at=datetime.now(),
            status=status,
            changes=changes,
            reason=reason
        )
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/services/test_verification_service.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/verification_service.py backend/tests/services/test_verification_service.py
git commit -m "feat(services): add VerificationService for pre-purchase checks"
```

---

## Task 5: Create Verification API Endpoint

**Files:**
- Modify: `backend/app/api/v1/endpoints/products.py`
- Test: `backend/tests/api/test_verification_api.py`

**Step 1: Write the failing test**

Create `backend/tests/api/test_verification_api.py`:

```python
"""Tests for verification API endpoint."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app


class TestVerificationAPI:
    """Tests for /products/{asin}/verify endpoint."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_verify_endpoint_exists(self, client):
        """Endpoint should exist and return 200 or 422 for validation."""
        response = client.get("/api/v1/products/B0B3DB4FJ3/verify")
        # Should not be 404
        assert response.status_code != 404

    @patch("app.api.v1.endpoints.products.VerificationService")
    def test_verify_returns_status(self, mock_service_class, client):
        """Verify endpoint returns proper response structure."""
        from app.schemas.verification import VerificationResponse, VerificationStatus, VerificationChanges
        from datetime import datetime

        mock_service = AsyncMock()
        mock_service.verify_product.return_value = VerificationResponse(
            asin="B0B3DB4FJ3",
            verified_at=datetime.now(),
            status=VerificationStatus.OK,
            changes=VerificationChanges()
        )
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/products/B0B3DB4FJ3/verify")

        assert response.status_code == 200
        data = response.json()
        assert "asin" in data
        assert "status" in data
        assert data["status"] in ["OK", "CHANGED", "AVOID"]

    def test_verify_invalid_asin_fails(self, client):
        """Invalid ASIN format should return 422."""
        response = client.get("/api/v1/products/INVALID/verify")
        assert response.status_code == 422
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/api/test_verification_api.py -v
```

Expected: FAIL

**Step 3: Write minimal implementation**

Add to `backend/app/api/v1/endpoints/products.py`:

```python
# Add imports at top
from app.schemas.verification import (
    VerificationRequest,
    VerificationResponse,
)
from app.services.verification_service import VerificationService

# Add endpoint after existing endpoints
@router.get(
    "/{asin}/verify",
    response_model=VerificationResponse,
    summary="Verify product before purchase",
    description="Real-time check of product status. Returns OK, CHANGED, or AVOID.",
)
async def verify_product(
    asin: str,
    original_price: Optional[float] = Query(None, description="Price when discovered"),
    original_fba_count: Optional[int] = Query(None, description="FBA count when discovered"),
    keepa_service: KeepaService = Depends(get_keepa_service),
):
    """
    Verify product status before purchase.

    Checks:
    - Is Amazon now selling?
    - Did FBA seller count increase?
    - Did price drop significantly?

    Returns status: OK (safe), CHANGED (review), AVOID (don't buy)
    """
    # Validate ASIN format
    if not asin or len(asin) != 10:
        raise HTTPException(
            status_code=422,
            detail="ASIN must be exactly 10 characters"
        )

    service = VerificationService(keepa_service)
    result = await service.verify_product(
        asin=asin.upper(),
        original_price=original_price,
        original_fba_count=original_fba_count
    )

    return result
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/api/test_verification_api.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/api/v1/endpoints/products.py backend/tests/api/test_verification_api.py
git commit -m "feat(api): add GET /products/{asin}/verify endpoint"
```

---

## Task 6: Update Existing Textbook Templates Parameters

**Files:**
- Modify: `backend/app/services/niche_templates.py:172-269`
- Test: `backend/tests/unit/test_niche_templates_hostile.py`

**Step 1: Write the failing test**

Add to `backend/tests/unit/test_niche_templates_hostile.py`:

```python
def test_legacy_textbook_templates_have_correct_price_min(self):
    """All textbook templates must have price_min >= $40 (PDF guide)."""
    textbook_templates = [t for t in CURATED_NICHES if "textbook" in t["type"]]
    for tmpl in textbook_templates:
        assert tmpl["price_range"][0] >= 40.0, \
            f"{tmpl['id']}: price_min {tmpl['price_range'][0]} < $40"

def test_textbook_max_fba_appropriate(self):
    """Standard templates: FBA <= 5, Patience templates: FBA <= 3."""
    for tmpl in CURATED_NICHES:
        if tmpl["type"] == "textbooks_standard":
            assert tmpl["max_fba_sellers"] == 5, f"{tmpl['id']}: should have max_fba=5"
        elif tmpl["type"] == "textbooks_patience":
            assert tmpl["max_fba_sellers"] <= 3, f"{tmpl['id']}: should have max_fba<=3"
```

**Step 2: Run test to verify current state**

```bash
cd backend && pytest tests/unit/test_niche_templates_hostile.py::TestDualTemplateStrategy::test_legacy_textbook_templates_have_correct_price_min -v
```

Check if existing templates need updates.

**Step 3: Update existing textbook templates**

Modify existing textbook templates in `backend/app/services/niche_templates.py` to align with PDF guide:

For each template with `type: "textbooks"`, update:
- `price_range`: Change `(30.0, X)` to `(40.0, 150.0)`
- `max_fba_sellers`: Keep at 3 for legacy templates

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/unit/test_niche_templates_hostile.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/niche_templates.py backend/tests/unit/test_niche_templates_hostile.py
git commit -m "fix(templates): align textbook templates with PDF guide ($40+ price min)"
```

---

## Task 7: Integration Test - Full Flow

**Files:**
- Create: `backend/tests/integration/test_dual_template_integration.py`

**Step 1: Write the integration test**

Create `backend/tests/integration/test_dual_template_integration.py`:

```python
"""Integration tests for dual template strategy."""

import pytest
from app.services.niche_templates import CURATED_NICHES, STRATEGY_CONFIGS


class TestDualTemplateIntegration:
    """End-to-end validation of dual template strategy."""

    def test_strategy_configs_complete(self):
        """All four strategy types must exist."""
        required = ["smart_velocity", "textbooks", "textbooks_standard", "textbooks_patience"]
        for strategy in required:
            assert strategy in STRATEGY_CONFIGS, f"Missing strategy: {strategy}"

    def test_templates_cover_all_strategies(self):
        """Templates exist for each strategy type."""
        template_types = set(t["type"] for t in CURATED_NICHES)
        assert "smart_velocity" in template_types
        assert "textbooks_standard" in template_types
        assert "textbooks_patience" in template_types

    def test_no_bsr_overlap_standard_patience(self):
        """Standard and Patience BSR ranges should not overlap."""
        standard_config = STRATEGY_CONFIGS["textbooks_standard"]
        patience_config = STRATEGY_CONFIGS["textbooks_patience"]

        std_max = standard_config["bsr_range"][1]
        pat_min = patience_config["bsr_range"][0]

        assert std_max <= pat_min, "Standard BSR max should be <= Patience BSR min"

    def test_patience_has_stricter_criteria(self):
        """Patience strategy must have stricter profit requirements."""
        standard = STRATEGY_CONFIGS["textbooks_standard"]
        patience = STRATEGY_CONFIGS["textbooks_patience"]

        assert patience["min_margin"] > standard["min_margin"], \
            "Patience should require higher margin"
        assert patience["max_fba_sellers"] <= standard["max_fba_sellers"], \
            "Patience should allow fewer FBA sellers"

    def test_all_textbook_templates_have_books_category(self):
        """All textbook templates must include Books root or subcategory."""
        from app.services.keepa_product_finder import ROOT_CATEGORY_MAPPING, BOOKS_ROOT_CATEGORY

        textbook_templates = [t for t in CURATED_NICHES if "textbook" in t["type"]]

        for tmpl in textbook_templates:
            categories = tmpl["categories"]
            has_books = any(
                c == BOOKS_ROOT_CATEGORY or ROOT_CATEGORY_MAPPING.get(c) == BOOKS_ROOT_CATEGORY
                for c in categories
            )
            assert has_books, f"{tmpl['id']}: No Books category found"
```

**Step 2: Run test**

```bash
cd backend && pytest tests/integration/test_dual_template_integration.py -v
```

Expected: PASS

**Step 3: Commit**

```bash
git add backend/tests/integration/test_dual_template_integration.py
git commit -m "test(integration): add dual template strategy validation"
```

---

## Summary

| Task | Description | Files Modified | Tests Added |
|------|-------------|----------------|-------------|
| 1 | Add STRATEGY_CONFIGS | niche_templates.py | 3 |
| 2 | Create Standard/Patience templates | niche_templates.py | 2 |
| 3 | Create verification schema | schemas/verification.py | 4 |
| 4 | Create verification service | services/verification_service.py | 3 |
| 5 | Create verify endpoint | endpoints/products.py | 3 |
| 6 | Update legacy template params | niche_templates.py | 2 |
| 7 | Integration tests | test_dual_template_integration.py | 5 |

**Total: 7 tasks, ~22 tests**

**Estimated time:** 45-60 minutes

---

## Post-Implementation Checklist

- [ ] All tests pass: `pytest tests/ -v`
- [ ] No regressions: `pytest tests/unit/test_niche_templates_hostile.py -v`
- [ ] API documentation updated (Swagger)
- [ ] Frontend `Verify` button component (separate frontend task)
