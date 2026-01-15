"""Tests for ProductScore URL fields."""


def test_product_score_has_url_fields():
    """Test that ProductScore schema has amazon_url and seller_central_url fields."""
    from app.api.v1.routers.views import ProductScore

    # Create ProductScore with required fields + URL fields
    score = ProductScore(
        asin="B00TEST123",
        score=75.0,
        rank=1,
        weights_applied={"roi": 0.5, "velocity": 0.5, "stability": 0.3},
        components={"roi_contribution": 40.0, "velocity_contribution": 35.0},
        raw_metrics={"roi_pct": 80.0, "velocity_score": 70.0, "stability_score": 60.0},
        amazon_url="https://www.amazon.com/dp/B00TEST123",
        seller_central_url="https://sellercentral.amazon.com/product-search/search?q=B00TEST123"
    )

    assert score.amazon_url == "https://www.amazon.com/dp/B00TEST123"
    assert score.seller_central_url == "https://sellercentral.amazon.com/product-search/search?q=B00TEST123"


def test_product_score_url_fields_optional():
    """Test that URL fields are optional."""
    from app.api.v1.routers.views import ProductScore

    # Create ProductScore without URL fields
    score = ProductScore(
        asin="B00TEST123",
        score=75.0,
        rank=1,
        weights_applied={"roi": 0.5, "velocity": 0.5, "stability": 0.3},
        components={"roi_contribution": 40.0, "velocity_contribution": 35.0},
        raw_metrics={"roi_pct": 80.0, "velocity_score": 70.0, "stability_score": 60.0}
    )

    assert score.amazon_url is None
    assert score.seller_central_url is None
