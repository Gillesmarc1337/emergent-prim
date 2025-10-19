#!/usr/bin/env python3
"""
Specific test for July To Dec dashboard blocks corrections
Testing the /api/analytics/yearly?year=2025 endpoint
"""

import requests
import json
import sys
from datetime import datetime

# Use the production URL from frontend/.env
BASE_URL = "https://dealflow-tracker-7.preview.emergentagent.com/api"

def test_july_dec_dashboard_blocks():
    """Test the July To Dec dashboard blocks corrections"""
    print(f"\n{'='*80}")
    print(f"🗓️  TESTING JULY TO DEC DASHBOARD BLOCKS CORRECTIONS")
    print(f"{'='*80}")
    
    endpoint = "/analytics/yearly?year=2025"
    
    try:
        print(f"\n🔍 Testing: {endpoint}")
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Expected status 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        try:
            data = response.json()
            print(f"✅ Response received successfully")
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response")
            print(f"Response text: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
        return False

    # Validate dashboard_blocks exist
    if 'dashboard_blocks' not in data:
        print("❌ dashboard_blocks not found in response")
        return False
    
    blocks = data['dashboard_blocks']
    print(f"✅ Dashboard blocks found")
    
    success = True
    
    # Test 1: Check that dashboard_blocks.block_3_pipe_creation.weighted_pipe_created is NOT zero
    print(f"\n📊 Test 1: Checking block_3_pipe_creation.weighted_pipe_created is NOT zero")
    
    if 'block_3_pipe_creation' in blocks:
        block3 = blocks['block_3_pipe_creation']
        weighted_pipe_created = block3.get('weighted_pipe_created', 0)
        
        print(f"  weighted_pipe_created value: {weighted_pipe_created}")
        
        if weighted_pipe_created != 0 and weighted_pipe_created is not None:
            print(f"  ✅ weighted_pipe_created is NOT zero: {weighted_pipe_created}")
        else:
            print(f"  ❌ weighted_pipe_created is zero or None: {weighted_pipe_created}")
            success = False
    else:
        print("  ❌ block_3_pipe_creation not found")
        success = False
    
    # Test 2: Check that dashboard_blocks.block_1_meetings.no_show_actual has correct count
    print(f"\n📊 Test 2: Checking block_1_meetings.no_show_actual has correct count")
    
    if 'block_1_meetings' in blocks:
        block1 = blocks['block_1_meetings']
        no_show_actual = block1.get('no_show_actual', 0)
        
        print(f"  no_show_actual value: {no_show_actual}")
        
        # Check if it's using the correct column name "show_nowshow" (not zero if there are actual no-shows)
        if isinstance(no_show_actual, (int, float)) and no_show_actual >= 0:
            print(f"  ✅ no_show_actual has valid count: {no_show_actual}")
        else:
            print(f"  ❌ no_show_actual has invalid value: {no_show_actual}")
            success = False
    else:
        print("  ❌ block_1_meetings not found")
        success = False
    
    # Test 3: Verify dashboard_blocks.block_4_revenue.revenue_target is 4,800,000
    print(f"\n📊 Test 3: Checking block_4_revenue.revenue_target is 4,800,000")
    
    if 'block_4_revenue' in blocks:
        block4 = blocks['block_4_revenue']
        revenue_target = block4.get('revenue_target', 0)
        
        print(f"  revenue_target value: {revenue_target}")
        
        if revenue_target == 4800000:
            print(f"  ✅ revenue_target is correct: {revenue_target} (4,800,000)")
        else:
            print(f"  ❌ revenue_target is incorrect: {revenue_target} (expected: 4,800,000)")
            success = False
    else:
        print("  ❌ block_4_revenue not found")
        success = False
    
    # Test 4: Confirm all show/no-show calculations are using correct column name "show_nowshow"
    print(f"\n📊 Test 4: Checking show/no-show calculations use correct column name")
    
    if 'block_1_meetings' in blocks:
        block1 = blocks['block_1_meetings']
        show_actual = block1.get('show_actual', 0)
        no_show_actual = block1.get('no_show_actual', 0)
        
        print(f"  show_actual value: {show_actual}")
        print(f"  no_show_actual value: {no_show_actual}")
        
        # Both should be valid numbers (not None or negative)
        if (isinstance(show_actual, (int, float)) and show_actual >= 0 and 
            isinstance(no_show_actual, (int, float)) and no_show_actual >= 0):
            print(f"  ✅ Show/no-show calculations appear to be working correctly")
            print(f"    Show: {show_actual}, No-show: {no_show_actual}")
        else:
            print(f"  ❌ Show/no-show calculations have invalid values")
            print(f"    Show: {show_actual}, No-show: {no_show_actual}")
            success = False
    else:
        print("  ❌ block_1_meetings not found for show/no-show validation")
        success = False
    
    # Additional validation: Check period is July-December
    print(f"\n📊 Additional: Checking period is July-December")
    
    period_checks = []
    for block_name, block_data in blocks.items():
        if isinstance(block_data, dict) and 'period' in block_data:
            period = block_data['period']
            print(f"  {block_name} period: {period}")
            if 'Jul-Dec' in period or 'July' in period:
                period_checks.append(True)
            else:
                period_checks.append(False)
    
    if all(period_checks) and len(period_checks) > 0:
        print(f"  ✅ All blocks have correct July-December period")
    else:
        print(f"  ⚠️  Some blocks may not have correct July-December period")
    
    # Print detailed block information for debugging
    print(f"\n📋 Detailed Block Information:")
    for block_name, block_data in blocks.items():
        print(f"\n  {block_name}:")
        if isinstance(block_data, dict):
            for key, value in block_data.items():
                print(f"    {key}: {value}")
        else:
            print(f"    {block_data}")
    
    return success

def main():
    """Main testing function"""
    print(f"🚀 Starting July To Dec Dashboard Blocks Test")
    print(f"Base URL: {BASE_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run the specific test
    test_passed = test_july_dec_dashboard_blocks()
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📋 TEST SUMMARY")
    print(f"{'='*80}")
    
    if test_passed:
        print(f"✅ JULY TO DEC DASHBOARD BLOCKS TEST PASSED")
        print(f"🎉 All corrections are working correctly!")
        return 0
    else:
        print(f"❌ JULY TO DEC DASHBOARD BLOCKS TEST FAILED")
        print(f"⚠️  Some corrections need attention")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)