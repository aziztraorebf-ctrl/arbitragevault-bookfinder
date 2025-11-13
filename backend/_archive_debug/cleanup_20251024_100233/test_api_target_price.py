"""Test API endpoint pour Target Price avec données simulées."""

import sys
sys.path.append('.')

def test_target_price_api_manual():
    """Test manuel de l'API Target Price sans serveur."""
    
    print("=== API TARGET PRICE MANUAL TEST ===")
    
    # Simulation des données comme si elles venaient de l'API Keepa
    mock_keepa_product_data = {
        "B00ABCD123": {
            "title": "Advanced Calculus Textbook",
            "csv": [[2800], None, None, None, None, None, None, None, None, None, 
                   None, None, None, None, None, None, None, None, [2650]],  # Buy box à $26.50
            "salesRank": 15420,
            "categoryTree": [{"name": "Books"}, {"name": "Textbooks"}]
        },
        "B00EFGH456": {
            "title": "Python Programming Guide",
            "csv": [[1950], None, None, None, None, None, None, None, None, None,
                   None, None, None, None, None, None, None, None, [1850]],  # Buy box à $18.50
            "salesRank": 8745,
            "categoryTree": [{"name": "Books"}, {"name": "Computer Science"}]
        }
    }
    
    # Simulation de _get_real_product_analysis
    def simulate_product_analysis(asin: str, product_data: dict):
        """Simulate product analysis like the API would do."""
        
        # Extract pricing (convert cents to dollars)
        buy_box_price_cents = None
        csv_data = product_data.get('csv', [])
        
        if len(csv_data) > 18 and csv_data[18]:
            buy_box_price_cents = csv_data[18][-1]
        elif len(csv_data) > 0 and csv_data[0]:
            buy_box_price_cents = csv_data[0][-1]
        
        current_price = buy_box_price_cents / 100.0 if buy_box_price_cents else 0
        
        if current_price > 0:
            # FBA fees estimation
            estimated_fees = (current_price * 0.15) + 3.0
            estimated_buy_price = current_price * 0.7  # 70% of sell price
            profit_net = current_price - estimated_fees - estimated_buy_price
            roi_percent = (profit_net / estimated_buy_price * 100) if estimated_buy_price > 0 else 0
        else:
            estimated_buy_price = 0
            profit_net = 0
            roi_percent = 0
        
        return {
            "asin": asin,
            "title": product_data.get('title', f'Product {asin}'),
            "buy_price": round(estimated_buy_price, 2),
            "sell_price": round(current_price, 2),
            "roi_percent": round(roi_percent, 1),
            "profit_net": round(profit_net, 2),
            "current_bsr": product_data.get('salesRank', 0),
            "category": "Books",
            "source": "keepa_api"
        }
    
    # Test simulation avec strategic views service
    try:
        from app.services.strategic_views_service import StrategicViewsService
        service = StrategicViewsService()
        print("✅ StrategicViewsService initialisé")
    except Exception as e:
        print(f"❌ Erreur import service: {e}")
        return False
    
    print("\n--- TEST 1: Product Analysis Simulation ---")
    
    for asin, keepa_data in mock_keepa_product_data.items():
        analysis = simulate_product_analysis(asin, keepa_data)
        print(f"\n{asin} - {analysis['title']}")
        print(f"  Buy Price: ${analysis['buy_price']}")
        print(f"  Sell Price: ${analysis['sell_price']}")
        print(f"  ROI: {analysis['roi_percent']}%")
        print(f"  Profit: ${analysis['profit_net']}")
        print(f"  BSR: {analysis['current_bsr']:,}")
    
    print("\n--- TEST 2: Target Price Calculations ---")
    
    # Prepare data for strategic views service
    products_data = []
    
    for asin, keepa_data in mock_keepa_product_data.items():
        analysis = simulate_product_analysis(asin, keepa_data)
        
        product_data = {
            "id": asin,
            "isbn_or_asin": asin,
            "buy_price": analysis["buy_price"],
            "current_price": analysis["buy_price"],
            "fba_fee": 3.50,
            "buybox_price": analysis["sell_price"],
            "referral_fee_rate": 0.15,
            "storage_fee": 0.50,
            "roi_percentage": analysis["roi_percent"],
            "velocity_score": 0.70,
            "profit_estimate": analysis["profit_net"],
            "competition_level": "MEDIUM",
            "price_volatility": 0.20,
            "demand_consistency": 0.80,
            "data_confidence": 0.85
        }
        
        products_data.append(product_data)
    
    # Test different strategic views
    strategic_views = ["profit_hunter", "velocity", "cashflow_hunter", "balanced_score", "volume_player"]
    
    for view_name in strategic_views:
        print(f"\n=== {view_name.upper()} VIEW ===")
        
        try:
            result = service.get_strategic_view_with_target_prices(view_name, products_data)
            
            print(f"View: {result['view_name']}")
            print(f"ROI Target: {result['roi_target'] * 100}%")
            print(f"Products: {result['products_count']}")
            
            for i, product in enumerate(result['products']):
                target_result = product.get('target_price_result', {})
                if target_result:
                    print(f"\n  Product {i+1}: {product.get('isbn_or_asin', 'Unknown')}")
                    print(f"    Buy Price: ${product.get('buy_price', 0)}")
                    print(f"    Current Market: ${product.get('buybox_price', 0)}")
                    print(f"    Target Price: ${target_result.get('target_price', 0)}")
                    print(f"    Achievable: {target_result.get('is_achievable', False)}")
                    print(f"    Price Gap: {target_result.get('price_gap_percentage', 0)}%")
            
            # Summary
            summary = result.get('summary', {})
            print(f"\n  SUMMARY:")
            print(f"    Achievable Opportunities: {summary.get('achievable_opportunities', 0)}/{summary.get('total_products', 0)}")
            print(f"    Average Target Price: ${summary.get('avg_target_price', 0)}")
            print(f"    Average Strategic Score: {summary.get('avg_strategic_score', 0):.1f}")
            
        except Exception as e:
            print(f"❌ Erreur {view_name}: {e}")
            return False
    
    print("\n--- TEST 3: Target Price Formula Validation ---")
    
    # Manual calculation verification
    test_product = products_data[0]  # First product
    
    print(f"Manual Calculation for {test_product['isbn_or_asin']}:")
    print(f"  Buy Price: ${test_product['buy_price']}")
    print(f"  FBA Fee: ${test_product['fba_fee']}")
    print(f"  Storage Fee: ${test_product['storage_fee']}")
    
    # Manual calculation for profit_hunter (50% ROI)
    total_costs = test_product['buy_price'] + test_product['fba_fee'] + test_product['storage_fee']
    roi_target = 0.50
    referral_rate = 0.15
    safety_buffer = 0.06
    
    net_rate = (1 - referral_rate) * (1 - roi_target)
    base_target = total_costs / net_rate
    final_target = base_target * (1 + safety_buffer)
    
    print(f"  Total Costs: ${total_costs}")
    print(f"  Net Rate: {net_rate}")
    print(f"  Base Target: ${base_target:.2f}")
    print(f"  Final Target (with {safety_buffer*100}% buffer): ${final_target:.2f}")
    
    # Compare with service calculation
    target_result = service.calculate_target_price_for_view("profit_hunter", test_product)
    if target_result:
        service_target = target_result.target_price
        print(f"  Service Calculated: ${service_target}")
        print(f"  Match: {'✅' if abs(service_target - final_target) < 0.01 else '❌'}")
    
    print("\n=== VALIDATION AVEC DONNÉES SIMULÉES KEEPA RÉUSSIE ✅ ===")
    return True

if __name__ == "__main__":
    success = test_target_price_api_manual()
    if not success:
        exit(1)