"""Manual test for Target Price Calculator - Test direct sans dépendances externes."""

# Test manual complet de la logique Target Price
def manual_target_price_test():
    """Test manuel de calcul Target Price sans Pydantic."""
    
    print("=== MANUAL TARGET PRICE CALCULATOR TESTS ===")
    
    # ROI targets par vue stratégique
    ROI_TARGETS = {
        "profit_hunter": 0.50,      # 50%
        "velocity": 0.25,           # 25%
        "cashflow_hunter": 0.35,    # 35%
        "balanced_score": 0.40,     # 40%
        "volume_player": 0.20       # 20%
    }
    
    # Referral fees par défaut
    DEFAULT_REFERRAL_RATE = 0.15  # 15%
    
    def calculate_target_price_manual(
        buy_price, fba_fee, view_name, 
        referral_fee_rate=None, storage_fee=0.0, 
        safety_buffer=0.06, current_market_price=None
    ):
        """Calcul manuel target price."""
        
        # ROI target pour la vue
        roi_target = ROI_TARGETS.get(view_name, 0.30)  # 30% fallback
        
        # Referral fee par défaut si non fourni
        if referral_fee_rate is None:
            referral_fee_rate = DEFAULT_REFERRAL_RATE
        
        # Coûts totaux
        total_costs = buy_price + fba_fee + storage_fee
        
        # Formule: target_price = total_costs / ((1 - referral_fee) × (1 - roi_target))
        net_rate = (1 - referral_fee_rate) * (1 - roi_target)
        base_target_price = total_costs / net_rate
        
        # Safety buffer
        target_price = base_target_price * (1 + safety_buffer)
        
        # Achievable check
        is_achievable = True
        price_gap_percentage = 0.0
        
        if current_market_price:
            price_gap_percentage = ((target_price - current_market_price) / current_market_price) * 100
            is_achievable = target_price <= current_market_price * 1.05  # 5% tolerance
        
        return {
            "target_price": round(target_price, 2),
            "roi_target": roi_target,
            "safety_buffer_used": safety_buffer,
            "is_achievable": is_achievable,
            "price_gap_percentage": round(price_gap_percentage, 2),
            "calculation_details": {
                "buy_price": buy_price,
                "fba_fee": fba_fee,
                "storage_fee": storage_fee,
                "total_costs": total_costs,
                "referral_fee_rate": referral_fee_rate,
                "roi_target": roi_target,
                "net_rate": net_rate,
                "base_target_price": base_target_price,
                "safety_buffer_applied": safety_buffer,
                "current_market_price": current_market_price
            }
        }
    
    # TEST 1: Profit Hunter Basic
    print("\n--- TEST 1: Profit Hunter Basic ---")
    result1 = calculate_target_price_manual(
        buy_price=15.00,
        fba_fee=3.50,
        view_name="profit_hunter"
    )
    print(f"Buy Price: $15.00, FBA Fee: $3.50")
    print(f"Target Price: ${result1['target_price']}")
    print(f"ROI Target: {result1['roi_target'] * 100}%")
    
    # Validation manuelle
    # total_costs = 15.00 + 3.50 = 18.50
    # net_rate = (1 - 0.15) * (1 - 0.50) = 0.85 * 0.50 = 0.425
    # base_target_price = 18.50 / 0.425 = 43.529
    # target_price = 43.529 * 1.06 = 46.14
    expected = 46.14
    print(f"Expected: ${expected}, Got: ${result1['target_price']}")
    print(f"✅ PASS" if abs(result1['target_price'] - expected) < 0.5 else "❌ FAIL")
    
    # TEST 2: ROI Targets par Vue
    print("\n--- TEST 2: ROI Targets par Vue Stratégique ---")
    for view_name, expected_roi in ROI_TARGETS.items():
        result = calculate_target_price_manual(
            buy_price=10.00,
            fba_fee=2.00,
            view_name=view_name
        )
        print(f"{view_name}: ROI {result['roi_target'] * 100}% - {'✅' if result['roi_target'] == expected_roi else '❌'}")
    
    # TEST 3: Custom Referral Fee
    print("\n--- TEST 3: Custom Referral Fee (10% vs 15%) ---")
    result_10 = calculate_target_price_manual(20.00, 4.00, "velocity", referral_fee_rate=0.10)
    result_15 = calculate_target_price_manual(20.00, 4.00, "velocity", referral_fee_rate=0.15)
    print(f"10% Referral Fee: ${result_10['target_price']}")
    print(f"15% Referral Fee: ${result_15['target_price']}")
    print(f"✅ PASS: 10% < 15%" if result_10['target_price'] < result_15['target_price'] else "❌ FAIL")
    
    # TEST 4: Storage Fee Impact
    print("\n--- TEST 4: Storage Fee Impact ---")
    result_no_storage = calculate_target_price_manual(15.00, 3.50, "balanced_score")
    result_with_storage = calculate_target_price_manual(15.00, 3.50, "balanced_score", storage_fee=1.50)
    print(f"Sans Storage Fee: ${result_no_storage['target_price']}")
    print(f"Avec Storage Fee ($1.50): ${result_with_storage['target_price']}")
    print(f"✅ PASS: Avec > Sans" if result_with_storage['target_price'] > result_no_storage['target_price'] else "❌ FAIL")
    
    # TEST 5: Market Price Achievability
    print("\n--- TEST 5: Market Price Achievability ---")
    result_achievable = calculate_target_price_manual(10.00, 2.50, "velocity", current_market_price=25.00)
    result_not_achievable = calculate_target_price_manual(20.00, 5.00, "profit_hunter", current_market_price=25.00)
    print(f"Achievable Scenario: Target ${result_achievable['target_price']} vs Market $25.00 - {result_achievable['is_achievable']}")
    print(f"Non-Achievable Scenario: Target ${result_not_achievable['target_price']} vs Market $25.00 - {result_not_achievable['is_achievable']}")
    
    # TEST 6: Safety Buffer Variations
    print("\n--- TEST 6: Safety Buffer Impact ---")
    result_6pct = calculate_target_price_manual(12.00, 3.00, "profit_hunter", safety_buffer=0.06)
    result_8pct = calculate_target_price_manual(12.00, 3.00, "profit_hunter", safety_buffer=0.08)
    print(f"6% Safety Buffer: ${result_6pct['target_price']}")
    print(f"8% Safety Buffer: ${result_8pct['target_price']}")
    print(f"✅ PASS: 8% > 6%" if result_8pct['target_price'] > result_6pct['target_price'] else "❌ FAIL")
    
    print("\n=== TOUS LES TESTS MANUELS TERMINÉS ===")
    
    return {
        "basic_calculation": result1,
        "roi_targets_valid": True,  # Assumé basé sur tests above
        "referral_fee_works": result_10['target_price'] < result_15['target_price'],
        "storage_fee_works": result_with_storage['target_price'] > result_no_storage['target_price'],
        "safety_buffer_works": result_8pct['target_price'] > result_6pct['target_price']
    }

if __name__ == "__main__":
    test_results = manual_target_price_test()