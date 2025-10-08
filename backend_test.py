#!/usr/bin/env python3
"""
Backend API Testing for Sales Analytics Dashboard
Testing dynamic dashboard blocks functionality
"""

import requests
import json
import sys
from datetime import datetime

# Use the production URL from frontend/.env
BASE_URL = "https://salesmetrics-4.preview.emergentagent.com/api"

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

def validate_dashboard_blocks(data, expected_period):
    """Validate dashboard blocks structure and content"""
    print(f"\n📊 Validating dashboard blocks for period: {expected_period}")
    
    if 'dashboard_blocks' not in data:
        print("❌ dashboard_blocks not found in response")
        return False
    
    blocks = data['dashboard_blocks']
    success = True
    
    # Test Block 1: Meeting Generation
    if 'block_1_meetings' in blocks:
        block1 = blocks['block_1_meetings']
        print(f"✅ Block 1 found: {block1.get('title', 'No title')}")
        
        # Check required fields
        required_fields = ['period', 'total_actual', 'total_target', 'inbound_actual', 
                          'inbound_target', 'outbound_actual', 'outbound_target', 
                          'referral_actual', 'referral_target']
        
        for field in required_fields:
            if field not in block1:
                print(f"❌ Missing field in block_1_meetings: {field}")
                success = False
            else:
                print(f"  ✓ {field}: {block1[field]}")
        
        # Check fixed targets
        if block1.get('inbound_target') != 20:
            print(f"❌ Incorrect inbound_target: expected 20, got {block1.get('inbound_target')}")
            success = False
        if block1.get('outbound_target') != 15:
            print(f"❌ Incorrect outbound_target: expected 15, got {block1.get('outbound_target')}")
            success = False
        if block1.get('referral_target') != 10:
            print(f"❌ Incorrect referral_target: expected 10, got {block1.get('referral_target')}")
            success = False
            
        # Check period matches expected
        if block1.get('period') != expected_period:
            print(f"❌ Incorrect period in block_1_meetings: expected {expected_period}, got {block1.get('period')}")
            success = False
        else:
            print(f"✅ Period matches: {block1.get('period')}")
    else:
        print("❌ block_1_meetings not found")
        success = False
    
    # Test Block 2: Discovery & POA
    if 'block_2_discovery_poa' in blocks:
        block2 = blocks['block_2_discovery_poa']
        print(f"✅ Block 2 found: {block2.get('title', 'No title')}")
        
        # Check required fields
        required_fields = ['period', 'discovery_actual', 'discovery_target', 'poa_actual', 'poa_target']
        
        for field in required_fields:
            if field not in block2:
                print(f"❌ Missing field in block_2_discovery_poa: {field}")
                success = False
            else:
                print(f"  ✓ {field}: {block2[field]}")
        
        # Check fixed targets
        if block2.get('discovery_target') != 45:
            print(f"❌ Incorrect discovery_target: expected 45, got {block2.get('discovery_target')}")
            success = False
        if block2.get('poa_target') != 18:
            print(f"❌ Incorrect poa_target: expected 18, got {block2.get('poa_target')}")
            success = False
            
        # Check period matches expected
        if block2.get('period') != expected_period:
            print(f"❌ Incorrect period in block_2_discovery_poa: expected {expected_period}, got {block2.get('period')}")
            success = False
        else:
            print(f"✅ Period matches: {block2.get('period')}")
    else:
        print("❌ block_2_discovery_poa not found")
        success = False
    
    return success

def test_monthly_analytics_with_offset(month_offset, expected_period):
    """Test monthly analytics with specific month offset"""
    print(f"\n{'='*60}")
    print(f"🗓️  TESTING MONTH OFFSET {month_offset} (Expected: {expected_period})")
    print(f"{'='*60}")
    
    endpoint = f"/analytics/monthly?month_offset={month_offset}"
    data = test_api_endpoint(endpoint)
    
    if data is None:
        return False
    
    # Validate dashboard blocks
    blocks_valid = validate_dashboard_blocks(data, expected_period)
    
    # Additional validation for the response structure
    print(f"\n📋 Additional Response Validation:")
    
    # Check if response has expected top-level fields
    expected_fields = ['week_start', 'week_end', 'meeting_generation', 'meetings_attended', 
                      'attribution', 'deals_closed', 'pipe_metrics', 'old_pipe', 
                      'closing_projections', 'big_numbers_recap', 'dashboard_blocks']
    
    for field in expected_fields:
        if field in data:
            print(f"  ✅ {field}: present")
        else:
            print(f"  ❌ {field}: missing")
            blocks_valid = False
    
    return blocks_valid

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

def test_data_status():
    """Test if there's data available for testing"""
    print(f"\n{'='*60}")
    print(f"📊 CHECKING DATA AVAILABILITY")
    print(f"{'='*60}")
    
    data = test_api_endpoint("/data/status")
    if data and isinstance(data, dict):
        has_data = data.get('has_data', False)
        total_records = data.get('total_records', 0)
        
        print(f"Has data: {has_data}")
        print(f"Total records: {total_records}")
        
        if has_data and total_records > 0:
            print(f"✅ Data is available for testing")
            return True
        else:
            print(f"⚠️  No data available - tests may return empty results")
            return False
    else:
        print(f"❌ Could not check data status")
        return False

def test_projections_hot_deals():
    """Test the hot deals projections endpoint"""
    print(f"\n{'='*60}")
    print(f"🔥 TESTING HOT DEALS PROJECTIONS ENDPOINT")
    print(f"{'='*60}")
    
    data = test_api_endpoint("/projections/hot-deals")
    
    if data is None:
        return False
    
    # Should return a list (even if empty)
    if not isinstance(data, list):
        print(f"❌ Expected list response, got {type(data)}")
        return False
    
    print(f"✅ Received list with {len(data)} hot deals")
    
    # If we have data, validate structure
    if len(data) > 0:
        print(f"📋 Validating hot deals structure:")
        
        # Check first deal structure
        first_deal = data[0]
        required_fields = ['id', 'client', 'pipeline', 'expected_mrr', 'expected_arr', 'owner', 'stage', 'hubspot_link']
        
        success = True
        for field in required_fields:
            if field in first_deal:
                print(f"  ✅ {field}: {first_deal[field]}")
            else:
                print(f"  ❌ Missing field: {field}")
                success = False
        
        # Verify stage is "B Legals"
        if first_deal.get('stage') == 'B Legals':
            print(f"  ✅ Stage is correctly 'B Legals'")
        else:
            print(f"  ❌ Expected stage 'B Legals', got '{first_deal.get('stage')}'")
            success = False
        
        return success
    else:
        print(f"⚠️  No hot deals found (empty result is valid)")
        return True

def test_projections_hot_leads():
    """Test the hot leads projections endpoint"""
    print(f"\n{'='*60}")
    print(f"🎯 TESTING HOT LEADS PROJECTIONS ENDPOINT")
    print(f"{'='*60}")
    
    data = test_api_endpoint("/projections/hot-leads")
    
    if data is None:
        return False
    
    # Should return a list (even if empty)
    if not isinstance(data, list):
        print(f"❌ Expected list response, got {type(data)}")
        return False
    
    print(f"✅ Received list with {len(data)} hot leads")
    
    # If we have data, validate structure
    if len(data) > 0:
        print(f"📋 Validating hot leads structure:")
        
        # Check first lead structure
        first_lead = data[0]
        required_fields = ['id', 'client', 'pipeline', 'expected_mrr', 'expected_arr', 'owner', 'stage', 'hubspot_link', 'poa_date']
        
        success = True
        for field in required_fields:
            if field in first_lead:
                print(f"  ✅ {field}: {first_lead[field]}")
            else:
                print(f"  ❌ Missing field: {field}")
                success = False
        
        # Verify stage is one of the expected stages
        expected_stages = ['C Proposal sent', 'D POA Booked']
        if first_lead.get('stage') in expected_stages:
            print(f"  ✅ Stage is correctly '{first_lead.get('stage')}'")
        else:
            print(f"  ❌ Expected stage in {expected_stages}, got '{first_lead.get('stage')}'")
            success = False
        
        return success
    else:
        print(f"⚠️  No hot leads found (empty result is valid)")
        return True

def test_projections_performance_summary():
    """Test the performance summary projections endpoint"""
    print(f"\n{'='*60}")
    print(f"📊 TESTING PERFORMANCE SUMMARY PROJECTIONS ENDPOINT")
    print(f"{'='*60}")
    
    data = test_api_endpoint("/projections/performance-summary")
    
    if data is None:
        return False
    
    # Should return a dict
    if not isinstance(data, dict):
        print(f"❌ Expected dict response, got {type(data)}")
        return False
    
    print(f"✅ Received performance summary data")
    
    # Validate required fields
    required_fields = ['ytd_revenue', 'ytd_target', 'remaining_target', 'forecast_gap', 'dashboard_blocks']
    
    success = True
    for field in required_fields:
        if field in data:
            print(f"  ✅ {field}: {data[field]}")
        else:
            print(f"  ❌ Missing field: {field}")
            success = False
    
    # Validate dashboard_blocks structure
    if 'dashboard_blocks' in data and isinstance(data['dashboard_blocks'], dict):
        blocks = data['dashboard_blocks']
        print(f"  📋 Dashboard blocks validation:")
        
        if 'meetings' in blocks:
            meetings = blocks['meetings']
            meeting_fields = ['period', 'inbound_actual', 'inbound_target', 'outbound_actual', 'outbound_target', 'referral_actual', 'referral_target']
            
            for field in meeting_fields:
                if field in meetings:
                    print(f"    ✅ meetings.{field}: {meetings[field]}")
                else:
                    print(f"    ❌ Missing meetings.{field}")
                    success = False
        else:
            print(f"    ❌ Missing 'meetings' block in dashboard_blocks")
            success = False
    
    # Validate data types
    if isinstance(data.get('ytd_revenue'), (int, float)):
        print(f"  ✅ ytd_revenue is numeric: {data['ytd_revenue']}")
    else:
        print(f"  ❌ ytd_revenue should be numeric, got {type(data.get('ytd_revenue'))}")
        success = False
    
    if isinstance(data.get('ytd_target'), (int, float)):
        print(f"  ✅ ytd_target is numeric: {data['ytd_target']}")
    else:
        print(f"  ❌ ytd_target should be numeric, got {type(data.get('ytd_target'))}")
        success = False
    
    if isinstance(data.get('forecast_gap'), bool):
        print(f"  ✅ forecast_gap is boolean: {data['forecast_gap']}")
    else:
        print(f"  ❌ forecast_gap should be boolean, got {type(data.get('forecast_gap'))}")
        success = False
    
    return success

def main():
    """Main testing function"""
    print(f"🚀 Starting Backend API Tests for Sales Analytics Dashboard")
    print(f"Base URL: {BASE_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Track test results
    test_results = {
        'connectivity': False,
        'data_status': False,
        'projections_hot_deals': False,
        'projections_hot_leads': False,
        'projections_performance_summary': False,
        'month_offset_0': False,
        'month_offset_1': False,
        'month_offset_3': False
    }
    
    # Test 1: Basic connectivity
    test_results['connectivity'] = test_basic_connectivity()
    
    # Test 2: Data availability
    test_results['data_status'] = test_data_status()
    
    # Test 3: New Projections API endpoints
    test_results['projections_hot_deals'] = test_projections_hot_deals()
    test_results['projections_hot_leads'] = test_projections_hot_leads()
    test_results['projections_performance_summary'] = test_projections_performance_summary()
    
    # Test 4: Monthly analytics with different offsets
    # month_offset=0 should show "Oct 2025"
    test_results['month_offset_0'] = test_monthly_analytics_with_offset(0, "Oct 2025")
    
    # month_offset=1 should show "Sep 2025"
    test_results['month_offset_1'] = test_monthly_analytics_with_offset(1, "Sep 2025")
    
    # month_offset=3 should show "Jul 2025"
    test_results['month_offset_3'] = test_monthly_analytics_with_offset(3, "Jul 2025")
    
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
    
    if passed_tests == total_tests:
        print(f"🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)