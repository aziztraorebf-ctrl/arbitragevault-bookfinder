#!/usr/bin/env python3
"""
Debug Amazon Detection Logic
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "app"))

from app.services.amazon_filter_service import AmazonFilterService
from app.utils.keepa_data_adapter import KeepaDataAdapter


def debug_detection():
    """Debug pourquoi la détection ne fonctionne pas."""
    service = AmazonFilterService(detection_level="smart")
    adapter = KeepaDataAdapter()
    
    # Test cas problématiques
    test_cases = [
        ("Clean", adapter.create_test_product('B001', 'Clean Book', is_amazon=False, availability_amazon=-1)),
        ("Direct", adapter.create_test_product('B002', 'Amazon Direct', is_amazon=True, availability_amazon=0)),
        ("Delayed", adapter.create_test_product('B003', 'Amazon Delayed', is_amazon=False, availability_amazon=5)),
        ("BuyBox", {
            **adapter.create_test_product('B004', 'Had Amazon', is_amazon=False, availability_amazon=-1),
            'buyBoxSellerIdHistory': [5, 8, 1, 5, 7]
        }),
        ("Clean2", adapter.create_test_product('B005', 'Truly Clean', is_amazon=False, availability_amazon=-1)),
    ]
    
    print("🔍 DEBUG DÉTECTION AMAZON:")
    for name, product in test_cases:
        has_amazon, reason = service._detect_amazon_presence(product)
        print(f"   {name}: {has_amazon} - {reason}")
        print(f"      availabilityAmazon: {product.get('availabilityAmazon')}")
        print(f"      isAmazon: {product.get('isAmazon')}")
        print(f"      buyBoxSellerIdHistory: {product.get('buyBoxSellerIdHistory', 'None')}")
        print()


if __name__ == "__main__":
    debug_detection()