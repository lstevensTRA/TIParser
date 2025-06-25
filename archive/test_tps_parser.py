#!/usr/bin/env python3
"""
Test script for TP/S Parser functionality
This is a temporary test file to verify the implementation works correctly
"""

from utils.tp_s_parser import TPSParser

def test_tps_parser():
    """Test the TP/S parser functionality"""
    print("🧪 Testing TP/S Parser Functionality")
    print("=" * 50)
    
    # Test filename parsing
    test_cases = [
        ("WI 19 TP", "TP"),
        ("WI S 19", "S"),
        ("WI 19", "TP"),  # Default
        ("WI 19 COMBINED", None),  # Joint
        ("WI 19 JOINT", None),  # Joint
        ("WI 20 SPOUSE", "S"),  # Should detect S
        ("", "TP"),  # Empty filename
    ]
    
    print("📁 Testing filename parsing:")
    for filename, expected in test_cases:
        result = TPSParser.extract_owner_from_filename(filename)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{filename}' → {result} (expected: {expected})")
    
    # Test data enhancement
    print("\n📊 Testing data enhancement:")
    sample_wi_data = {
        "2019": [
            {"Form": "W-2", "Income": 50000, "Withholding": 5000},
            {"Form": "1099-MISC", "Income": 10000, "Withholding": 0}
        ],
        "2020": [
            {"Form": "W-2", "Income": 55000, "Withholding": 5500}
        ]
    }
    
    enhanced_data = TPSParser.enhance_wi_data_with_owner(sample_wi_data, "WI 19 TP")
    
    print("  ✅ Enhanced data structure:")
    for year, forms in enhanced_data.items():
        print(f"    {year}: {len(forms)} forms with Owner field")
        for form in forms:
            print(f"      - {form['Form']}: ${form['Income']:,.0f} (Owner: {form['Owner']})")
    
    # Test aggregation
    print("\n💰 Testing income aggregation:")
    totals = TPSParser.aggregate_income_by_owner(enhanced_data)
    
    for year, year_totals in totals.items():
        print(f"  {year}:")
        for owner_type, data in year_totals.items():
            if data['income'] > 0:
                print(f"    {owner_type}: ${data['income']:,.0f}")
    
    # Test missing data detection
    print("\n🔍 Testing missing data detection:")
    recommendations = TPSParser.detect_missing_spouse_data(totals, "Married Filing Jointly")
    
    if recommendations:
        for rec in recommendations:
            print(f"  ⚠️ {rec}")
    else:
        print("  ✅ No missing data issues detected")
    
    print("\n🎉 TP/S Parser test completed successfully!")

if __name__ == "__main__":
    test_tps_parser() 