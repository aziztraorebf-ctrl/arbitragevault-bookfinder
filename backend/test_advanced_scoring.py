#!/usr/bin/env python3
"""
Quick test script for advanced scoring system
"""
import sys
import json
from decimal import Decimal
from datetime import datetime

# Test imports
def test_imports():
    print("🔍 Testing imports...")
    try:
        from app.core.calculations import (
            compute_advanced_velocity_score,
            compute_advanced_stability_score, 
            compute_advanced_confidence_score,
            compute_overall_rating,
            generate_readable_summary
        )
        print("✅ Advanced scoring functions imported")
        
        from app.api.v1.routers.keepa import ScoreBreakdown, AnalysisResult
        print("✅ API schemas imported")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

# Test business config loading
def test_config():
    print("\n🔍 Testing configuration...")
    try:
        import json
        with open('config/business_rules.json', 'r') as f:
            config = json.load(f)
        
        # Check for our new sections
        if 'advanced_scoring' in config:
            print("✅ advanced_scoring config found")
            velocity_config = config['advanced_scoring']['velocity']
            print(f"   - Velocity fallback: {velocity_config['fallback_score']}")
            print(f"   - Min data points: {velocity_config['min_data_points']}")
        else:
            print("❌ advanced_scoring config missing")
            
        if 'summary_templates' in config:
            print("✅ summary_templates config found")
            excellent_template = config['summary_templates']['EXCELLENT']
            print(f"   - EXCELLENT template: {excellent_template[:50]}...")
        else:
            print("❌ summary_templates config missing")
            
        return config
    except Exception as e:
        print(f"❌ Config error: {e}")
        return None

# Test individual scoring functions
def test_scoring_functions():
    print("\n🔍 Testing scoring functions...")
    try:
        from app.core.calculations import (
            compute_advanced_velocity_score,
            compute_advanced_stability_score,
            compute_advanced_confidence_score
        )
        
        # Load config
        config = test_config()
        if not config:
            return False
            
        # Test velocity scoring with mock data
        mock_bsr_history = [
            (datetime.now(), 60000),
            (datetime.now(), 55000), 
            (datetime.now(), 50000),
            (datetime.now(), 45000)  # Improving trend
        ]
        
        velocity_raw, velocity_score, velocity_level, velocity_notes = compute_advanced_velocity_score(
            mock_bsr_history, config
        )
        
        print(f"✅ Velocity Score: {velocity_score}/100 ({velocity_level})")
        print(f"   Raw: {velocity_raw:.3f}, Notes: {velocity_notes}")
        
        # Test stability scoring with mock data
        mock_price_history = [
            (datetime.now(), 24.99),
            (datetime.now(), 25.99),
            (datetime.now(), 24.49),
            (datetime.now(), 25.49)
        ]
        
        stability_raw, stability_score, stability_level, stability_notes = compute_advanced_stability_score(
            mock_price_history, config
        )
        
        print(f"✅ Stability Score: {stability_score}/100 ({stability_level})")
        print(f"   Raw: {stability_raw:.3f}, Notes: {stability_notes}")
        
        # Test confidence scoring
        confidence_raw, confidence_score, confidence_level, confidence_notes = compute_advanced_confidence_score(
            mock_price_history, mock_bsr_history, 2, config  # 2 days old data
        )
        
        print(f"✅ Confidence Score: {confidence_score}/100 ({confidence_level})")
        print(f"   Raw: {confidence_raw:.3f}, Notes: {confidence_notes}")
        
        return True
        
    except Exception as e:
        print(f"❌ Scoring functions error: {e}")
        import traceback
        traceback.print_exc()
        return False

# Test overall rating and summary
def test_overall_system():
    print("\n🔍 Testing overall rating system...")
    try:
        from app.core.calculations import compute_overall_rating, generate_readable_summary
        
        # Load config
        with open('config/business_rules.json', 'r') as f:
            config = json.load(f)
            
        # Test with good scores
        roi = 45.0
        velocity_score = 78
        stability_score = 85
        confidence_score = 92
        
        overall_rating = compute_overall_rating(roi, velocity_score, stability_score, confidence_score, config)
        print(f"✅ Overall Rating: {overall_rating}")
        
        scores_dict = {
            "velocity": velocity_score,
            "stability": stability_score, 
            "confidence": confidence_score
        }
        
        readable_summary = generate_readable_summary(roi, overall_rating, scores_dict, config)
        print(f"✅ Readable Summary: {readable_summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ Overall system error: {e}")
        import traceback
        traceback.print_exc()
        return False

# Main test runner
def main():
    print("🚀 ArbitrageVault Advanced Scoring System Test\n")
    
    all_passed = True
    
    # Run all tests
    if not test_imports():
        all_passed = False
        
    if not test_scoring_functions():
        all_passed = False
        
    if not test_overall_system():
        all_passed = False
    
    # Final result
    print("\n" + "="*50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Advanced Scoring Ready!")
        print("✅ Velocity, Stability, Confidence scoring functional")
        print("✅ Overall rating and readable summary working") 
        print("✅ Configuration system operational")
    else:
        print("❌ SOME TESTS FAILED - Review errors above")
    
    print("="*50)

if __name__ == "__main__":
    main()