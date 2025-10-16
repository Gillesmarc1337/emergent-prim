#!/usr/bin/env python3
"""
Backend API Testing for Corrected Targets and New Metrics
Testing the updated ytd_target (4.5M) and new metrics (pipe_created, active_deals_count)
"""

import requests
import json
import sys
from datetime import datetime

# Use the production URL from frontend/.env
BASE_URL = "https://sales-analytics-dash-3.preview.emergentagent.com/api"

def test_api_endpoint(endpoint, expected_status=200):
    """Test an API endpoint and return response"""
    try:
        print(f"\n🔍 Testing: {endpoint}")
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != expected_status:
            print(f"❌ Expected status {expected_status}, got {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Response received successfully")
                return data
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response")
                print(f"Response text: {response.text}")
                return None
        else:
            return response.text
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
        return None

def validate_big_numbers_recap(data, endpoint_name):
    """Validate big_numbers_recap section for corrected targets and new metrics"""
    print(f"\n📊 Validating big_numbers_recap for {endpoint_name}")
    
    if 'big_numbers_recap' not in data:
        print("❌ big_numbers_recap not found in response")
        return False
    
    recap = data['big_numbers_recap']
    success = True
    
    # Test 1: ytd_target should be 4,500,000 (not 3,600,000)
    ytd_target = recap.get('ytd_target')
    if ytd_target == 4500000.0:
        print(f"✅ ytd_target correctly updated to 4,500,000")
    elif ytd_target == 3600000.0:
        print(f"❌ ytd_target still shows old value 3,600,000 - should be 4,500,000")
        success = False
    else:
        print(f"❌ ytd_target has unexpected value: {ytd_target} - should be 4,500,000")
        success = False
    
    # Test 2: pipe_created should be included
    if 'pipe_created' in recap:
        pipe_created = recap['pipe_created']
        if isinstance(pipe_created, (int, float)):
            print(f"✅ pipe_created metric included: {pipe_created}")
        else:
            print(f"❌ pipe_created has invalid type: {type(pipe_created)} - should be numeric")
            success = False
    else:
        print(f"❌ pipe_created metric missing from big_numbers_recap")
        success = False
    
    # Test 3: active_deals_count should be included
    if 'active_deals_count' in recap:
        active_deals_count = recap['active_deals_count']
        if isinstance(active_deals_count, int):
            print(f"✅ active_deals_count metric included: {active_deals_count}")
        else:
            print(f"❌ active_deals_count has invalid type: {type(active_deals_count)} - should be integer")
            success = False
    else:
        print(f"❌ active_deals_count metric missing from big_numbers_recap")
        success = False
    
    # Additional validation: other expected fields
    expected_fields = ['ytd_revenue', 'remaining_target', 'forecast_gap']
    for field in expected_fields:
        if field in recap:
            print(f"  ✓ {field}: {recap[field]}")
        else:
            print(f"  ❌ Missing expected field: {field}")
            success = False
    
    return success

def test_monthly_analytics():
    """Test GET /api/analytics/monthly for corrected targets and new metrics"""
    print(f"\n{'='*60}")
    print(f"📅 TESTING MONTHLY ANALYTICS ENDPOINT")
    print(f"{'='*60}")
    
    data = test_api_endpoint("/analytics/monthly")
    
    if data is None:
        return False
    
    # Validate big_numbers_recap
    return validate_big_numbers_recap(data, "Monthly Analytics")

def test_yearly_analytics():
    """Test GET /api/analytics/yearly?year=2025 for corrected targets and new metrics"""
    print(f"\n{'='*60}")
    print(f"📅 TESTING YEARLY ANALYTICS ENDPOINT")
    print(f"{'='*60}")
    
    data = test_api_endpoint("/analytics/yearly?year=2025")
    
    if data is None:
        return False
    
    # Validate big_numbers_recap
    return validate_big_numbers_recap(data, "Yearly Analytics")

def test_performance_summary():
    """Test GET /api/projections/performance-summary for corrected targets and new metrics"""
    print(f"\n{'='*60}")
    print(f"📊 TESTING PERFORMANCE SUMMARY ENDPOINT")
    print(f"{'='*60}")
    
    data = test_api_endpoint("/projections/performance-summary")
    
    if data is None:
        return False
    
    # For performance summary, check if it has the corrected target and new metrics
    print(f"\n📊 Validating performance-summary for corrected targets and new metrics")
    
    success = True
    
    # Test 1: ytd_target should be 4,500,000
    ytd_target = data.get('ytd_target')
    if ytd_target == 4500000.0:
        print(f"✅ ytd_target correctly set to 4,500,000")
    elif ytd_target == 3600000.0:
        print(f"❌ ytd_target still shows old value 3,600,000 - should be 4,500,000")
        success = False
    else:
        print(f"❌ ytd_target has unexpected value: {ytd_target} - should be 4,500,000")
        success = False
    
    # Test 2: pipe_created should be included
    if 'pipe_created' in data:
        pipe_created = data['pipe_created']
        if isinstance(pipe_created, (int, float)):
            print(f"✅ pipe_created metric included: {pipe_created}")
        else:
            print(f"❌ pipe_created has invalid type: {type(pipe_created)} - should be numeric")
            success = False
    else:
        print(f"❌ pipe_created metric missing from performance-summary")
        success = False
    
    # Test 3: active_deals_count should be included
    if 'active_deals_count' in data:
        active_deals_count = data['active_deals_count']
        if isinstance(active_deals_count, int):
            print(f"✅ active_deals_count metric included: {active_deals_count}")
        else:
            print(f"❌ active_deals_count has invalid type: {type(active_deals_count)} - should be integer")
            success = False
    else:
        print(f"❌ active_deals_count metric missing from performance-summary")
        success = False
    
    # Additional validation: other expected fields
    expected_fields = ['ytd_revenue', 'remaining_target', 'forecast_gap']
    for field in expected_fields:
        if field in data:
            print(f"  ✓ {field}: {data[field]}")
        else:
            print(f"  ❌ Missing expected field: {field}")
            success = False
    
    return success

def test_basic_connectivity():
    """Test basic API connectivity"""
    print(f"\n{'='*60}")
    print(f"🔌 TESTING BASIC API CONNECTIVITY")
    print(f"{'='*60}")
    
    # Test root endpoint
    data = test_api_endpoint("/")
    if data and isinstance(data, dict) and 'message' in data:
        print(f"✅ API is accessible: {data['message']}")
        return True
    else:
        print(f"❌ API root endpoint failed")
        return False

def main():
    """Main testing function"""
    print(f"🚀 Starting Backend API Tests for Corrected Targets and New Metrics")
    print(f"Base URL: {BASE_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nTesting for:")
    print(f"  • ytd_target = 4,500,000 (corrected from 3,600,000)")
    print(f"  • pipe_created metric included")
    print(f"  • active_deals_count metric included")
    
    # Track test results
    test_results = {
        'connectivity': False,
        'monthly_analytics': False,
        'yearly_analytics': False,
        'performance_summary': False
    }
    
    # Test 1: Basic connectivity
    test_results['connectivity'] = test_basic_connectivity()
    
    if not test_results['connectivity']:
        print(f"\n❌ API connectivity failed - skipping other tests")
        return 1
    
    # Test 2: Monthly Analytics
    test_results['monthly_analytics'] = test_monthly_analytics()
    
    # Test 3: Yearly Analytics
    test_results['yearly_analytics'] = test_yearly_analytics()
    
    # Test 4: Performance Summary
    test_results['performance_summary'] = test_performance_summary()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📋 TEST SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    # Detailed results
    if test_results['monthly_analytics'] and test_results['yearly_analytics'] and test_results['performance_summary']:
        print(f"\n🎉 SUCCESS: All endpoints have corrected targets (4.5M) and new metrics!")
        print(f"  ✅ Monthly Analytics: ytd_target=4.5M, pipe_created, active_deals_count")
        print(f"  ✅ Yearly Analytics: ytd_target=4.5M, pipe_created, active_deals_count")
        print(f"  ✅ Performance Summary: ytd_target=4.5M, pipe_created, active_deals_count")
    else:
        print(f"\n❌ ISSUES FOUND:")
        if not test_results['monthly_analytics']:
            print(f"  • Monthly Analytics: Missing corrected targets or new metrics")
        if not test_results['yearly_analytics']:
            print(f"  • Yearly Analytics: Missing corrected targets or new metrics")
        if not test_results['performance_summary']:
            print(f"  • Performance Summary: Missing corrected targets or new metrics")
    
    if passed_tests == total_tests:
        print(f"\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)