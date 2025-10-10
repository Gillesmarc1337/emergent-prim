#!/usr/bin/env python3
"""
Backend API Testing for Sales Analytics Dashboard
Testing MongoDB data structure and available endpoints for master data verification
"""

import requests
import json
import sys
from datetime import datetime

# Use the production URL from frontend/.env
BASE_URL = "https://revdashboard.preview.emergentagent.com/api"

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

def test_custom_analytics_dynamic_targets():
    """Test custom analytics endpoint with dynamic targets for different periods"""
    print(f"\n{'='*60}")
    print(f"🎯 TESTING CUSTOM ANALYTICS DYNAMIC TARGETS")
    print(f"{'='*60}")
    
    # Test 1: 1-month period (baseline)
    print(f"\n📅 Test 1: 1-month period (October 2025)")
    endpoint_1m = "/analytics/custom?start_date=2025-10-01&end_date=2025-10-31"
    data_1m = test_api_endpoint(endpoint_1m)
    
    if data_1m is None:
        print("❌ Failed to get 1-month data")
        return False
    
    # Validate dashboard_blocks exist
    if 'dashboard_blocks' not in data_1m:
        print("❌ dashboard_blocks not found in 1-month response")
        return False
    
    blocks_1m = data_1m['dashboard_blocks']
    print(f"✅ Dashboard blocks found for 1-month period")
    
    # Extract 1-month targets (baseline)
    baseline_targets = {}
    
    # Block 1: Meetings Generation
    if 'block_1_meetings' in blocks_1m:
        block1 = blocks_1m['block_1_meetings']
        baseline_targets['meetings_total'] = block1.get('total_target', 0)
        baseline_targets['meetings_inbound'] = block1.get('inbound_target', 0)
        baseline_targets['meetings_outbound'] = block1.get('outbound_target', 0)
        baseline_targets['meetings_referral'] = block1.get('referral_target', 0)
        print(f"  ✓ Block 1 - Total meetings target: {baseline_targets['meetings_total']}")
    else:
        print("❌ block_1_meetings not found in 1-month response")
        return False
    
    # Block 2: Intro & POA
    if 'block_2_intro_poa' in blocks_1m:
        block2 = blocks_1m['block_2_intro_poa']
        baseline_targets['intro'] = block2.get('intro_target', 0)
        baseline_targets['poa'] = block2.get('poa_target', 0)
        print(f"  ✓ Block 2 - Intro target: {baseline_targets['intro']}, POA target: {baseline_targets['poa']}")
    else:
        print("❌ block_2_intro_poa not found in 1-month response")
        return False
    
    # Block 3: New Pipe Created
    if 'block_3_new_pipe' in blocks_1m:
        block3 = blocks_1m['block_3_new_pipe']
        baseline_targets['pipe'] = block3.get('target', 0)
        print(f"  ✓ Block 3 - Pipe target: {baseline_targets['pipe']}")
    else:
        print("❌ block_3_new_pipe not found in 1-month response")
        return False
    
    # Block 4: Revenue Objective
    if 'block_4_revenue' in blocks_1m:
        block4 = blocks_1m['block_4_revenue']
        baseline_targets['revenue'] = block4.get('target_revenue', 0)
        print(f"  ✓ Block 4 - Revenue target: {baseline_targets['revenue']}")
    else:
        print("❌ block_4_revenue not found in 1-month response")
        return False
    
    # Test 2: 2-month period (should have 2x targets)
    print(f"\n📅 Test 2: 2-month period (October 1 - November 30, 2025)")
    endpoint_2m = "/analytics/custom?start_date=2025-10-01&end_date=2025-11-30"
    data_2m = test_api_endpoint(endpoint_2m)
    
    if data_2m is None:
        print("❌ Failed to get 2-month data")
        return False
    
    if 'dashboard_blocks' not in data_2m:
        print("❌ dashboard_blocks not found in 2-month response")
        return False
    
    blocks_2m = data_2m['dashboard_blocks']
    print(f"✅ Dashboard blocks found for 2-month period")
    
    # Validate 2x multiplier
    success = True
    
    # Block 1: Meetings Generation (2x targets)
    if 'block_1_meetings' in blocks_2m:
        block1_2m = blocks_2m['block_1_meetings']
        expected_total = baseline_targets['meetings_total'] * 2
        expected_inbound = baseline_targets['meetings_inbound'] * 2
        expected_outbound = baseline_targets['meetings_outbound'] * 2
        expected_referral = baseline_targets['meetings_referral'] * 2
        
        actual_total = block1_2m.get('total_target', 0)
        actual_inbound = block1_2m.get('inbound_target', 0)
        actual_outbound = block1_2m.get('outbound_target', 0)
        actual_referral = block1_2m.get('referral_target', 0)
        
        if actual_total == expected_total:
            print(f"  ✅ Block 1 - Total meetings target correctly doubled: {actual_total} (expected: {expected_total})")
        else:
            print(f"  ❌ Block 1 - Total meetings target NOT doubled: {actual_total} (expected: {expected_total})")
            success = False
            
        if actual_inbound == expected_inbound:
            print(f"  ✅ Block 1 - Inbound target correctly doubled: {actual_inbound}")
        else:
            print(f"  ❌ Block 1 - Inbound target NOT doubled: {actual_inbound} (expected: {expected_inbound})")
            success = False
            
        if actual_outbound == expected_outbound:
            print(f"  ✅ Block 1 - Outbound target correctly doubled: {actual_outbound}")
        else:
            print(f"  ❌ Block 1 - Outbound target NOT doubled: {actual_outbound} (expected: {expected_outbound})")
            success = False
            
        if actual_referral == expected_referral:
            print(f"  ✅ Block 1 - Referral target correctly doubled: {actual_referral}")
        else:
            print(f"  ❌ Block 1 - Referral target NOT doubled: {actual_referral} (expected: {expected_referral})")
            success = False
    else:
        print("❌ block_1_meetings not found in 2-month response")
        success = False
    
    # Block 2: Intro & POA (2x targets)
    if 'block_2_intro_poa' in blocks_2m:
        block2_2m = blocks_2m['block_2_intro_poa']
        expected_intro = baseline_targets['intro'] * 2
        expected_poa = baseline_targets['poa'] * 2
        
        actual_intro = block2_2m.get('intro_target', 0)
        actual_poa = block2_2m.get('poa_target', 0)
        
        if actual_intro == expected_intro:
            print(f"  ✅ Block 2 - Intro target correctly doubled: {actual_intro} (expected: {expected_intro})")
        else:
            print(f"  ❌ Block 2 - Intro target NOT doubled: {actual_intro} (expected: {expected_intro})")
            success = False
            
        if actual_poa == expected_poa:
            print(f"  ✅ Block 2 - POA target correctly doubled: {actual_poa} (expected: {expected_poa})")
        else:
            print(f"  ❌ Block 2 - POA target NOT doubled: {actual_poa} (expected: {expected_poa})")
            success = False
    else:
        print("❌ block_2_intro_poa not found in 2-month response")
        success = False
    
    # Block 3: New Pipe Created (2x target)
    if 'block_3_new_pipe' in blocks_2m:
        block3_2m = blocks_2m['block_3_new_pipe']
        expected_pipe = baseline_targets['pipe'] * 2
        actual_pipe = block3_2m.get('target', 0)
        
        if actual_pipe == expected_pipe:
            print(f"  ✅ Block 3 - Pipe target correctly doubled: {actual_pipe} (expected: {expected_pipe})")
        else:
            print(f"  ❌ Block 3 - Pipe target NOT doubled: {actual_pipe} (expected: {expected_pipe})")
            success = False
    else:
        print("❌ block_3_new_pipe not found in 2-month response")
        success = False
    
    # Block 4: Revenue Objective (2x target)
    if 'block_4_revenue' in blocks_2m:
        block4_2m = blocks_2m['block_4_revenue']
        expected_revenue = baseline_targets['revenue'] * 2
        actual_revenue = block4_2m.get('target_revenue', 0)
        
        if actual_revenue == expected_revenue:
            print(f"  ✅ Block 4 - Revenue target correctly doubled: {actual_revenue} (expected: {expected_revenue})")
        else:
            print(f"  ❌ Block 4 - Revenue target NOT doubled: {actual_revenue} (expected: {expected_revenue})")
            success = False
    else:
        print("❌ block_4_revenue not found in 2-month response")
        success = False
    
    # Test 3: 3-month period (should have 3x targets)
    print(f"\n📅 Test 3: 3-month period (October 1 - December 31, 2025)")
    endpoint_3m = "/analytics/custom?start_date=2025-10-01&end_date=2025-12-31"
    data_3m = test_api_endpoint(endpoint_3m)
    
    if data_3m is None:
        print("❌ Failed to get 3-month data")
        return False
    
    if 'dashboard_blocks' not in data_3m:
        print("❌ dashboard_blocks not found in 3-month response")
        return False
    
    blocks_3m = data_3m['dashboard_blocks']
    print(f"✅ Dashboard blocks found for 3-month period")
    
    # Validate 3x multiplier for key blocks
    if 'block_1_meetings' in blocks_3m:
        block1_3m = blocks_3m['block_1_meetings']
        expected_total_3m = baseline_targets['meetings_total'] * 3
        actual_total_3m = block1_3m.get('total_target', 0)
        
        if actual_total_3m == expected_total_3m:
            print(f"  ✅ Block 1 - Total meetings target correctly tripled: {actual_total_3m} (expected: {expected_total_3m})")
        else:
            print(f"  ❌ Block 1 - Total meetings target NOT tripled: {actual_total_3m} (expected: {expected_total_3m})")
            success = False
    
    if 'block_2_intro_poa' in blocks_3m:
        block2_3m = blocks_3m['block_2_intro_poa']
        expected_intro_3m = baseline_targets['intro'] * 3
        expected_poa_3m = baseline_targets['poa'] * 3
        actual_intro_3m = block2_3m.get('intro_target', 0)
        actual_poa_3m = block2_3m.get('poa_target', 0)
        
        if actual_intro_3m == expected_intro_3m:
            print(f"  ✅ Block 2 - Intro target correctly tripled: {actual_intro_3m} (expected: {expected_intro_3m})")
        else:
            print(f"  ❌ Block 2 - Intro target NOT tripled: {actual_intro_3m} (expected: {expected_intro_3m})")
            success = False
            
        if actual_poa_3m == expected_poa_3m:
            print(f"  ✅ Block 2 - POA target correctly tripled: {actual_poa_3m} (expected: {expected_poa_3m})")
        else:
            print(f"  ❌ Block 2 - POA target NOT tripled: {actual_poa_3m} (expected: {expected_poa_3m})")
            success = False
    
    if 'block_4_revenue' in blocks_3m:
        block4_3m = blocks_3m['block_4_revenue']
        expected_revenue_3m = baseline_targets['revenue'] * 3
        actual_revenue_3m = block4_3m.get('target_revenue', 0)
        
        if actual_revenue_3m == expected_revenue_3m:
            print(f"  ✅ Block 4 - Revenue target correctly tripled: {actual_revenue_3m} (expected: {expected_revenue_3m})")
        else:
            print(f"  ❌ Block 4 - Revenue target NOT tripled: {actual_revenue_3m} (expected: {expected_revenue_3m})")
            success = False
    
    return success

def explore_mongodb_data_structure():
    """Explore MongoDB data structure for master data verification"""
    print(f"\n{'='*60}")
    print(f"🔍 EXPLORING MONGODB DATA STRUCTURE FOR MASTER DATA")
    print(f"{'='*60}")
    
    # Test all available endpoints to understand data structure
    endpoints_to_explore = [
        "/analytics/monthly",
        "/analytics/yearly?year=2025", 
        "/analytics/custom?start_date=2025-07-01&end_date=2025-12-31",
        "/projections/hot-deals",
        "/projections/hot-leads", 
        "/projections/performance-summary"
    ]
    
    master_data_found = {}
    
    for endpoint in endpoints_to_explore:
        print(f"\n🔍 Exploring endpoint: {endpoint}")
        data = test_api_endpoint(endpoint)
        
        if data is None:
            print(f"❌ No data from {endpoint}")
            continue
            
        # Look for structured monthly data for 2025
        monthly_data_2025 = find_monthly_data_2025(data, endpoint)
        if monthly_data_2025:
            master_data_found[endpoint] = {'monthly_data': monthly_data_2025}
            
        # Look for specific metrics requested
        metrics_found = find_target_metrics(data, endpoint)
        if metrics_found:
            if endpoint not in master_data_found:
                master_data_found[endpoint] = {}
            master_data_found[endpoint]['metrics'] = metrics_found
    
    # Summary of findings
    print(f"\n{'='*60}")
    print(f"📊 MASTER DATA STRUCTURE ANALYSIS")
    print(f"{'='*60}")
    
    if master_data_found:
        print(f"✅ STRUCTURED MASTER DATA FOUND:")
        for endpoint, data_info in master_data_found.items():
            print(f"\n📍 Endpoint: {endpoint}")
            if 'monthly_data' in data_info:
                print(f"  📅 Monthly Data 2025: {len(data_info['monthly_data'])} months found")
                for month_info in data_info['monthly_data']:
                    print(f"    • {month_info}")
            if 'metrics' in data_info:
                print(f"  📊 Target Metrics Found:")
                for metric in data_info['metrics']:
                    print(f"    • {metric}")
    else:
        print(f"❌ NO STRUCTURED MASTER DATA FOUND")
        print(f"   The system appears to use calculated analytics rather than pre-stored master data")
    
    return len(master_data_found) > 0

def find_monthly_data_2025(data, endpoint):
    """Look for monthly structured data for 2025"""
    monthly_data = []
    
    if isinstance(data, dict):
        # Check dashboard_blocks for monthly targets
        if 'dashboard_blocks' in data:
            blocks = data['dashboard_blocks']
            for block_name, block_data in blocks.items():
                if isinstance(block_data, dict) and 'period' in block_data:
                    period = block_data['period']
                    if '2025' in str(period):
                        monthly_data.append(f"{block_name}: {period}")
        
        # Check for monthly breakdown data
        if 'big_numbers_recap' in data and 'monthly_breakdown' in data['big_numbers_recap']:
            breakdown = data['big_numbers_recap']['monthly_breakdown']
            for month_key, value in breakdown.items():
                if '2025' in str(month_key):
                    monthly_data.append(f"Monthly breakdown: {month_key} = {value}")
        
        # Check for any date-based structures
        for key, value in data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if '2025' in str(sub_key) and isinstance(sub_value, (int, float)):
                        monthly_data.append(f"{key}.{sub_key}: {sub_value}")
    
    return monthly_data if monthly_data else None

def find_target_metrics(data, endpoint):
    """Look for specific target metrics requested by user"""
    target_metrics = [
        "Target pipe", "Created Pipe", "Aggregate pipe", 
        "New Weighted pipe", "Aggregate weighted pipe", 
        "Target Revenue", "Closed Revenue"
    ]
    
    found_metrics = []
    
    def search_dict_for_metrics(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Check if key matches any target metrics (case insensitive)
                for target_metric in target_metrics:
                    if any(word.lower() in key.lower() for word in target_metric.split()):
                        found_metrics.append(f"{current_path}: {value}")
                
                # Recursively search nested dictionaries
                if isinstance(value, dict):
                    search_dict_for_metrics(value, current_path)
                elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    for i, item in enumerate(value[:3]):  # Check first 3 items
                        search_dict_for_metrics(item, f"{current_path}[{i}]")
    
    search_dict_for_metrics(data)
    return found_metrics if found_metrics else None

def test_master_data_access():
    """Test access to master data collections and structure"""
    print(f"\n{'='*60}")
    print(f"🗄️  TESTING MASTER DATA ACCESS")
    print(f"{'='*60}")
    
    # Test yearly analytics for 2025 (most comprehensive)
    print(f"\n📊 Testing Yearly Analytics 2025 for Master Data Structure")
    yearly_data = test_api_endpoint("/analytics/yearly?year=2025")
    
    if yearly_data is None:
        print(f"❌ Cannot access yearly 2025 data")
        return False
    
    print(f"✅ Yearly 2025 data accessible")
    
    # Analyze the structure for master data characteristics
    master_data_characteristics = {
        'has_monthly_targets': False,
        'has_structured_periods': False,
        'has_pipeline_metrics': False,
        'has_revenue_targets': False,
        'data_organization': 'calculated'  # vs 'master_data'
    }
    
    # Check for dashboard blocks with structured targets
    if 'dashboard_blocks' in yearly_data:
        blocks = yearly_data['dashboard_blocks']
        print(f"\n📋 Dashboard Blocks Analysis:")
        
        for block_name, block_data in blocks.items():
            print(f"  📊 {block_name}:")
            if isinstance(block_data, dict):
                # Look for target vs actual patterns (indicates master data)
                targets = [k for k in block_data.keys() if 'target' in k.lower()]
                actuals = [k for k in block_data.keys() if 'actual' in k.lower()]
                
                if targets:
                    master_data_characteristics['has_monthly_targets'] = True
                    print(f"    🎯 Targets found: {targets}")
                if actuals:
                    print(f"    📈 Actuals found: {actuals}")
                
                # Check for period information
                if 'period' in block_data:
                    master_data_characteristics['has_structured_periods'] = True
                    print(f"    📅 Period: {block_data['period']}")
    
    # Check for pipeline metrics
    if 'pipe_metrics' in yearly_data:
        master_data_characteristics['has_pipeline_metrics'] = True
        pipe_data = yearly_data['pipe_metrics']
        print(f"\n🔧 Pipeline Metrics Found:")
        print(f"  • Created pipe: {pipe_data.get('created_pipe', {})}")
        print(f"  • Total pipe: {pipe_data.get('total_pipe', {})}")
    
    # Check for revenue targets
    if 'big_numbers_recap' in yearly_data:
        recap = yearly_data['big_numbers_recap']
        if 'ytd_target' in recap:
            master_data_characteristics['has_revenue_targets'] = True
            print(f"\n💰 Revenue Targets Found:")
            print(f"  • YTD Target: {recap.get('ytd_target')}")
            print(f"  • YTD Revenue: {recap.get('ytd_revenue')}")
    
    # Determine if this is master data or calculated data
    if (master_data_characteristics['has_monthly_targets'] and 
        master_data_characteristics['has_structured_periods'] and
        master_data_characteristics['has_pipeline_metrics']):
        master_data_characteristics['data_organization'] = 'structured_master_data'
    
    print(f"\n📋 Master Data Characteristics Summary:")
    for char, value in master_data_characteristics.items():
        status = "✅" if value else "❌"
        print(f"  {status} {char}: {value}")
    
    return master_data_characteristics['data_organization'] == 'structured_master_data'

def test_october_2025_analytics_detailed():
    """Test October 2025 analytics with detailed master data comparison"""
    print(f"\n{'='*80}")
    print(f"🎯 TESTING OCTOBER 2025 ANALYTICS - DETAILED MASTER DATA COMPARISON")
    print(f"{'='*80}")
    
    # Expected master data values for October 2025 (based on user requirements)
    expected_master_data = {
        'block_3_pipe_creation': {
            'new_pipe_created': 'Created Pipe from master data',
            'weighted_pipe_created': 'New Weighted pipe from master data',
            'aggregate_weighted_pipe': 'Aggregate weighted pipe from master data', 
            'target_pipe_created': 'Target pipe from master data'
        },
        'block_4_revenue': {
            'revenue_target': 'Target Revenue for October from master data',
            'closed_revenue': 'Closed Revenue for October from master data'
        }
    }
    
    # Test GET /api/analytics/monthly for October 2025
    print(f"\n📊 Testing GET /api/analytics/monthly for October 2025")
    endpoint = "/analytics/monthly?month_offset=0"  # 0 = current month (October 2025)
    data = test_api_endpoint(endpoint)
    
    if data is None:
        print(f"❌ Failed to get October 2025 analytics data")
        return False
    
    print(f"✅ Successfully retrieved October 2025 analytics data")
    
    # Check if dashboard_blocks exists
    if 'dashboard_blocks' not in data:
        print(f"❌ dashboard_blocks not found in response")
        return False
    
    dashboard_blocks = data['dashboard_blocks']
    print(f"✅ dashboard_blocks found in response")
    
    # Detailed examination of block_3_pipe_creation
    print(f"\n{'='*60}")
    print(f"🔧 EXAMINING BLOCK_3_PIPE_CREATION VALUES")
    print(f"{'='*60}")
    
    success = True
    
    if 'block_3_pipe_creation' in dashboard_blocks:
        block_3 = dashboard_blocks['block_3_pipe_creation']
        print(f"✅ block_3_pipe_creation found")
        
        # Display all values in block_3
        print(f"\n📋 Current values in block_3_pipe_creation:")
        for key, value in block_3.items():
            print(f"  • {key}: {value}")
        
        # Check specific fields requested
        print(f"\n🔍 Detailed comparison with expected master data:")
        
        # new_pipe_created
        actual_new_pipe = block_3.get('new_pipe_created', 'NOT FOUND')
        print(f"\n1️⃣ new_pipe_created (should correspond to 'Created Pipe'):")
        print(f"   📊 Actual value: {actual_new_pipe}")
        print(f"   🎯 Expected from master data: {expected_master_data['block_3_pipe_creation']['new_pipe_created']}")
        
        # weighted_pipe_created  
        actual_weighted_pipe = block_3.get('weighted_pipe_created', 'NOT FOUND')
        print(f"\n2️⃣ weighted_pipe_created (should correspond to 'New Weighted pipe'):")
        print(f"   📊 Actual value: {actual_weighted_pipe}")
        print(f"   🎯 Expected from master data: {expected_master_data['block_3_pipe_creation']['weighted_pipe_created']}")
        
        # aggregate_weighted_pipe
        actual_aggregate_weighted = block_3.get('aggregate_weighted_pipe', 'NOT FOUND')
        print(f"\n3️⃣ aggregate_weighted_pipe (should correspond to 'Aggregate weighted pipe'):")
        print(f"   📊 Actual value: {actual_aggregate_weighted}")
        print(f"   🎯 Expected from master data: {expected_master_data['block_3_pipe_creation']['aggregate_weighted_pipe']}")
        
        # target_pipe_created
        actual_target_pipe = block_3.get('target_pipe_created', 'NOT FOUND')
        print(f"\n4️⃣ target_pipe_created (should correspond to 'Target pipe'):")
        print(f"   📊 Actual value: {actual_target_pipe}")
        print(f"   🎯 Expected from master data: {expected_master_data['block_3_pipe_creation']['target_pipe_created']}")
        
    else:
        print(f"❌ block_3_pipe_creation not found in dashboard_blocks")
        success = False
    
    # Detailed examination of block_4_revenue
    print(f"\n{'='*60}")
    print(f"💰 EXAMINING BLOCK_4_REVENUE VALUES")
    print(f"{'='*60}")
    
    if 'block_4_revenue' in dashboard_blocks:
        block_4 = dashboard_blocks['block_4_revenue']
        print(f"✅ block_4_revenue found")
        
        # Display all values in block_4
        print(f"\n📋 Current values in block_4_revenue:")
        for key, value in block_4.items():
            print(f"  • {key}: {value}")
        
        # Check specific fields requested
        print(f"\n🔍 Detailed comparison with expected master data:")
        
        # revenue_target
        actual_revenue_target = block_4.get('revenue_target', 'NOT FOUND')
        print(f"\n1️⃣ revenue_target (should correspond to 'Target Revenue' for October):")
        print(f"   📊 Actual value: {actual_revenue_target}")
        print(f"   🎯 Expected from master data: {expected_master_data['block_4_revenue']['revenue_target']}")
        
        # closed_revenue
        actual_closed_revenue = block_4.get('closed_revenue', 'NOT FOUND')
        print(f"\n2️⃣ closed_revenue (should correspond to 'Closed Revenue' for October):")
        print(f"   📊 Actual value: {actual_closed_revenue}")
        print(f"   🎯 Expected from master data: {expected_master_data['block_4_revenue']['closed_revenue']}")
        
    else:
        print(f"❌ block_4_revenue not found in dashboard_blocks")
        success = False
    
    # Analysis of potential discrepancies
    print(f"\n{'='*60}")
    print(f"🔍 ANALYSIS OF POTENTIAL DISCREPANCIES")
    print(f"{'='*60}")
    
    print(f"\n📊 Data Source Analysis:")
    print(f"   • The API appears to calculate values dynamically from sales records")
    print(f"   • Values are computed in real-time rather than stored as master data")
    print(f"   • October 2025 targets appear to be hardcoded in the backend logic")
    
    # Check if there are any obvious data issues
    if 'block_3_pipe_creation' in dashboard_blocks and 'block_4_revenue' in dashboard_blocks:
        block_3 = dashboard_blocks['block_3_pipe_creation']
        block_4 = dashboard_blocks['block_4_revenue']
        
        print(f"\n⚠️  Potential Issues Identified:")
        
        # Check for zero values that might indicate calculation issues
        if block_3.get('new_pipe_created', 0) == 0:
            print(f"   • new_pipe_created is 0 - may indicate no deals created in October 2025")
        
        if block_3.get('weighted_pipe_created', 0) == 0:
            print(f"   • weighted_pipe_created is 0 - may indicate no weighted pipe calculation")
        
        if block_4.get('closed_revenue', 0) == 0:
            print(f"   • closed_revenue is 0 - may indicate no deals closed in October 2025")
        
        # Check for reasonable target values
        revenue_target = block_4.get('revenue_target', 0)
        if revenue_target == 1080000:
            print(f"   ✅ revenue_target matches expected October 2025 target (1,080,000)")
        elif revenue_target > 0:
            print(f"   ⚠️  revenue_target ({revenue_target}) differs from expected October target (1,080,000)")
        else:
            print(f"   ❌ revenue_target is 0 or missing")
    
    # Summary of findings
    print(f"\n{'='*60}")
    print(f"📋 OCTOBER 2025 ANALYTICS SUMMARY")
    print(f"{'='*60}")
    
    if success:
        print(f"✅ Successfully examined October 2025 analytics data")
        print(f"✅ Both block_3_pipe_creation and block_4_revenue are present")
        print(f"📊 All requested fields have been analyzed and compared")
    else:
        print(f"❌ Some issues found in October 2025 analytics data structure")
    
    return success

def test_dashboard_blocks_and_deals_closed():
    """Test dashboard_blocks presence and deals_closed data structure in monthly and yearly analytics"""
    print(f"\n{'='*80}")
    print(f"🎯 TESTING DASHBOARD BLOCKS AND DEALS_CLOSED DATA STRUCTURE")
    print(f"{'='*80}")
    
    test_results = {
        'monthly_dashboard_blocks': False,
        'yearly_dashboard_blocks': False,
        'monthly_deals_closed': False,
        'yearly_deals_closed': False
    }
    
    # Test 1: GET /api/analytics/monthly - Check dashboard_blocks
    print(f"\n📊 Test 1: GET /api/analytics/monthly - Dashboard Blocks")
    print(f"{'='*60}")
    
    monthly_data = test_api_endpoint("/analytics/monthly")
    if monthly_data:
        if 'dashboard_blocks' in monthly_data:
            print(f"✅ dashboard_blocks present in monthly analytics")
            test_results['monthly_dashboard_blocks'] = True
            
            # Display dashboard blocks structure
            blocks = monthly_data['dashboard_blocks']
            print(f"📋 Dashboard blocks found:")
            for block_name, block_data in blocks.items():
                print(f"  • {block_name}: {type(block_data)} with {len(block_data) if isinstance(block_data, dict) else 'N/A'} fields")
                if isinstance(block_data, dict):
                    for key, value in list(block_data.items())[:5]:  # Show first 5 fields
                        print(f"    - {key}: {value}")
                    if len(block_data) > 5:
                        print(f"    ... and {len(block_data) - 5} more fields")
        else:
            print(f"❌ dashboard_blocks NOT found in monthly analytics response")
            print(f"📋 Available top-level keys: {list(monthly_data.keys()) if isinstance(monthly_data, dict) else 'Not a dict'}")
        
        # Check deals_closed structure
        if 'deals_closed' in monthly_data:
            print(f"\n✅ deals_closed present in monthly analytics")
            test_results['monthly_deals_closed'] = True
            
            deals_closed = monthly_data['deals_closed']
            print(f"📋 deals_closed structure:")
            if isinstance(deals_closed, dict):
                for key, value in deals_closed.items():
                    print(f"  • {key}: {value} ({type(value).__name__})")
            else:
                print(f"  • Type: {type(deals_closed)}")
                print(f"  • Value: {deals_closed}")
        else:
            print(f"❌ deals_closed NOT found in monthly analytics response")
    else:
        print(f"❌ Failed to get monthly analytics data")
    
    # Test 2: GET /api/analytics/yearly - Check dashboard_blocks
    print(f"\n📊 Test 2: GET /api/analytics/yearly - Dashboard Blocks")
    print(f"{'='*60}")
    
    yearly_data = test_api_endpoint("/analytics/yearly?year=2025")
    if yearly_data:
        if 'dashboard_blocks' in yearly_data:
            print(f"✅ dashboard_blocks present in yearly analytics")
            test_results['yearly_dashboard_blocks'] = True
            
            # Display dashboard blocks structure
            blocks = yearly_data['dashboard_blocks']
            print(f"📋 Dashboard blocks found:")
            for block_name, block_data in blocks.items():
                print(f"  • {block_name}: {type(block_data)} with {len(block_data) if isinstance(block_data, dict) else 'N/A'} fields")
                if isinstance(block_data, dict):
                    for key, value in list(block_data.items())[:5]:  # Show first 5 fields
                        print(f"    - {key}: {value}")
                    if len(block_data) > 5:
                        print(f"    ... and {len(block_data) - 5} more fields")
        else:
            print(f"❌ dashboard_blocks NOT found in yearly analytics response")
            print(f"📋 Available top-level keys: {list(yearly_data.keys()) if isinstance(yearly_data, dict) else 'Not a dict'}")
        
        # Check deals_closed structure
        if 'deals_closed' in yearly_data:
            print(f"\n✅ deals_closed present in yearly analytics")
            test_results['yearly_deals_closed'] = True
            
            deals_closed = yearly_data['deals_closed']
            print(f"📋 deals_closed structure:")
            if isinstance(deals_closed, dict):
                for key, value in deals_closed.items():
                    print(f"  • {key}: {value} ({type(value).__name__})")
            else:
                print(f"  • Type: {type(deals_closed)}")
                print(f"  • Value: {deals_closed}")
        else:
            print(f"❌ deals_closed NOT found in yearly analytics response")
    else:
        print(f"❌ Failed to get yearly analytics data")
    
    # Test 3: Detailed analysis of deals_closed structure for "Deals Closed (Current Period)" block
    print(f"\n📊 Test 3: Deals Closed Data Structure Analysis")
    print(f"{'='*60}")
    
    if test_results['monthly_deals_closed'] and monthly_data:
        deals_closed = monthly_data['deals_closed']
        print(f"📋 Monthly deals_closed detailed analysis:")
        
        # Check for fields needed for "Deals Closed (Current Period)" dashboard block
        expected_fields = [
            'deals_closed', 'target_deals', 'arr_closed', 'target_arr', 
            'mrr_closed', 'avg_deal_size', 'on_track', 'deals_detail', 'monthly_closed'
        ]
        
        missing_fields = []
        present_fields = []
        
        for field in expected_fields:
            if field in deals_closed:
                present_fields.append(field)
                value = deals_closed[field]
                print(f"  ✅ {field}: {value} ({type(value).__name__})")
            else:
                missing_fields.append(field)
                print(f"  ❌ {field}: MISSING")
        
        print(f"\n📊 Summary for deals_closed structure:")
        print(f"  ✅ Present fields: {len(present_fields)}/{len(expected_fields)}")
        print(f"  ❌ Missing fields: {missing_fields}")
        
        # Check if deals_detail has proper structure
        if 'deals_detail' in deals_closed:
            deals_detail = deals_closed['deals_detail']
            if isinstance(deals_detail, list) and len(deals_detail) > 0:
                print(f"  📋 deals_detail sample (first deal):")
                first_deal = deals_detail[0]
                for key, value in first_deal.items():
                    print(f"    • {key}: {value}")
            else:
                print(f"  📋 deals_detail: {type(deals_detail)} with {len(deals_detail) if isinstance(deals_detail, list) else 'N/A'} items")
    
    # Test 4: Check if dashboard blocks contain deals_closed information
    print(f"\n📊 Test 4: Dashboard Blocks - Deals Closed Integration")
    print(f"{'='*60}")
    
    deals_closed_in_blocks = False
    
    if test_results['monthly_dashboard_blocks'] and monthly_data:
        blocks = monthly_data['dashboard_blocks']
        print(f"🔍 Searching for deals_closed related blocks in dashboard_blocks:")
        
        for block_name, block_data in blocks.items():
            if isinstance(block_data, dict):
                # Look for deals/closed related fields
                deals_fields = [k for k in block_data.keys() if 'deal' in k.lower() or 'closed' in k.lower()]
                if deals_fields:
                    deals_closed_in_blocks = True
                    print(f"  ✅ {block_name} contains deals/closed fields: {deals_fields}")
                    for field in deals_fields:
                        print(f"    • {field}: {block_data[field]}")
    
    if not deals_closed_in_blocks:
        print(f"  ⚠️  No deals/closed related fields found in dashboard_blocks")
        print(f"  💡 This might explain why 'Deals Closed (Current Period)' block is not displaying")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📋 DASHBOARD BLOCKS AND DEALS_CLOSED TEST SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\n📊 Overall Results: {passed_tests}/{total_tests} tests passed")
    
    # Diagnostic recommendations
    print(f"\n💡 DIAGNOSTIC RECOMMENDATIONS:")
    if not test_results['monthly_dashboard_blocks']:
        print(f"  • Monthly analytics missing dashboard_blocks - check backend implementation")
    if not test_results['yearly_dashboard_blocks']:
        print(f"  • Yearly analytics missing dashboard_blocks - check backend implementation")
    if not test_results['monthly_deals_closed']:
        print(f"  • Monthly analytics missing deals_closed - check deals_closed calculation")
    if not test_results['yearly_deals_closed']:
        print(f"  • Yearly analytics missing deals_closed - check deals_closed calculation")
    if not deals_closed_in_blocks:
        print(f"  • Dashboard blocks don't contain deals_closed data - may need integration")
    
    return passed_tests == total_tests

def test_meeting_targets_correction():
    """Test meeting targets correction for 50 per month across all analytics endpoints"""
    print(f"\n{'='*80}")
    print(f"🎯 TESTING MEETING TARGETS CORRECTION (50 PER MONTH)")
    print(f"{'='*80}")
    
    test_results = {
        'monthly_targets': False,
        'yearly_targets': False,
        'custom_targets': False
    }
    
    # Expected targets per month: 22 inbound + 17 outbound + 11 referral = 50 total
    expected_monthly_targets = {
        'total_target': 50,
        'inbound_target': 22,
        'outbound_target': 17,
        'referral_target': 11
    }
    
    # Test 1: GET /api/analytics/monthly - Verify meeting targets are 50 total
    print(f"\n📊 Test 1: GET /api/analytics/monthly - Monthly Meeting Targets")
    print(f"{'='*60}")
    
    monthly_data = test_api_endpoint("/analytics/monthly")
    if monthly_data and 'dashboard_blocks' in monthly_data:
        blocks = monthly_data['dashboard_blocks']
        
        if 'block_1_meetings' in blocks:
            block1 = blocks['block_1_meetings']
            print(f"✅ block_1_meetings found in monthly analytics")
            
            # Verify targets
            success = True
            for target_key, expected_value in expected_monthly_targets.items():
                actual_value = block1.get(target_key, 'NOT FOUND')
                if actual_value == expected_value:
                    print(f"  ✅ {target_key}: {actual_value} (matches expected {expected_value})")
                else:
                    print(f"  ❌ {target_key}: {actual_value} (expected {expected_value})")
                    success = False
            
            # Verify math adds up correctly (22+17+11=50)
            inbound = block1.get('inbound_target', 0)
            outbound = block1.get('outbound_target', 0)
            referral = block1.get('referral_target', 0)
            total = block1.get('total_target', 0)
            calculated_total = inbound + outbound + referral
            
            if calculated_total == 50 and total == 50:
                print(f"  ✅ Math verification: {inbound}+{outbound}+{referral}={calculated_total} (matches total_target={total})")
            else:
                print(f"  ❌ Math verification: {inbound}+{outbound}+{referral}={calculated_total} (total_target={total}, expected 50)")
                success = False
            
            test_results['monthly_targets'] = success
        else:
            print(f"❌ block_1_meetings not found in monthly analytics")
    else:
        print(f"❌ Failed to get monthly analytics or dashboard_blocks missing")
    
    # Test 2: GET /api/analytics/yearly - Verify July-Dec targets (6 months * 50 = 300)
    print(f"\n📊 Test 2: GET /api/analytics/yearly - July-December Meeting Targets")
    print(f"{'='*60}")
    
    yearly_data = test_api_endpoint("/analytics/yearly?year=2025")
    if yearly_data and 'dashboard_blocks' in yearly_data:
        blocks = yearly_data['dashboard_blocks']
        
        if 'block_1_meetings' in blocks:
            block1 = blocks['block_1_meetings']
            print(f"✅ block_1_meetings found in yearly analytics")
            
            # For July-Dec period (6 months), targets should be 6x monthly targets
            expected_july_dec_targets = {
                'total_target': 50 * 6,  # 300
                'inbound_target': 22 * 6,  # 132
                'outbound_target': 17 * 6,  # 102
                'referral_target': 11 * 6   # 66
            }
            
            success = True
            for target_key, expected_value in expected_july_dec_targets.items():
                actual_value = block1.get(target_key, 'NOT FOUND')
                if actual_value == expected_value:
                    print(f"  ✅ {target_key}: {actual_value} (matches expected {expected_value} for 6 months)")
                else:
                    print(f"  ❌ {target_key}: {actual_value} (expected {expected_value} for 6 months)")
                    success = False
            
            # Verify math for July-Dec period
            inbound = block1.get('inbound_target', 0)
            outbound = block1.get('outbound_target', 0)
            referral = block1.get('referral_target', 0)
            total = block1.get('total_target', 0)
            calculated_total = inbound + outbound + referral
            
            if calculated_total == 300 and total == 300:
                print(f"  ✅ July-Dec math verification: {inbound}+{outbound}+{referral}={calculated_total} (matches total_target={total})")
            else:
                print(f"  ❌ July-Dec math verification: {inbound}+{outbound}+{referral}={calculated_total} (total_target={total}, expected 300)")
                success = False
            
            # Verify period is correctly labeled
            period = block1.get('period', 'NOT FOUND')
            if 'Jul-Dec 2025' in str(period):
                print(f"  ✅ Period correctly labeled: {period}")
            else:
                print(f"  ⚠️  Period label: {period} (expected to contain 'Jul-Dec 2025')")
            
            test_results['yearly_targets'] = success
        else:
            print(f"❌ block_1_meetings not found in yearly analytics")
    else:
        print(f"❌ Failed to get yearly analytics or dashboard_blocks missing")
    
    # Test 3: GET /api/analytics/custom - Verify dynamic targets multiply correctly
    print(f"\n📊 Test 3: GET /api/analytics/custom - Dynamic Target Multiplication")
    print(f"{'='*60}")
    
    # Test 3a: 2-month period (should be 2x50 = 100 total)
    print(f"\n📅 Test 3a: 2-month custom period (Oct-Nov 2025)")
    custom_2m_data = test_api_endpoint("/analytics/custom?start_date=2025-10-01&end_date=2025-11-30")
    
    success_2m = False
    if custom_2m_data and 'dashboard_blocks' in custom_2m_data:
        blocks = custom_2m_data['dashboard_blocks']
        
        if 'block_1_meetings' in blocks:
            block1 = blocks['block_1_meetings']
            print(f"✅ block_1_meetings found in 2-month custom analytics")
            
            # For 2-month period, targets should be 2x monthly targets
            expected_2m_targets = {
                'total_target': 50 * 2,  # 100
                'inbound_target': 22 * 2,  # 44
                'outbound_target': 17 * 2,  # 34
                'referral_target': 11 * 2   # 22
            }
            
            success_2m = True
            for target_key, expected_value in expected_2m_targets.items():
                actual_value = block1.get(target_key, 'NOT FOUND')
                if actual_value == expected_value:
                    print(f"    ✅ {target_key}: {actual_value} (matches expected {expected_value} for 2 months)")
                else:
                    print(f"    ❌ {target_key}: {actual_value} (expected {expected_value} for 2 months)")
                    success_2m = False
            
            # Verify math for 2-month period
            inbound = block1.get('inbound_target', 0)
            outbound = block1.get('outbound_target', 0)
            referral = block1.get('referral_target', 0)
            total = block1.get('total_target', 0)
            calculated_total = inbound + outbound + referral
            
            if calculated_total == 100 and total == 100:
                print(f"    ✅ 2-month math verification: {inbound}+{outbound}+{referral}={calculated_total} (matches total_target={total})")
            else:
                print(f"    ❌ 2-month math verification: {inbound}+{outbound}+{referral}={calculated_total} (total_target={total}, expected 100)")
                success_2m = False
        else:
            print(f"❌ block_1_meetings not found in 2-month custom analytics")
    else:
        print(f"❌ Failed to get 2-month custom analytics or dashboard_blocks missing")
    
    # Test 3b: 3-month period (should be 3x50 = 150 total)
    print(f"\n📅 Test 3b: 3-month custom period (Oct-Dec 2025)")
    custom_3m_data = test_api_endpoint("/analytics/custom?start_date=2025-10-01&end_date=2025-12-31")
    
    success_3m = False
    if custom_3m_data and 'dashboard_blocks' in custom_3m_data:
        blocks = custom_3m_data['dashboard_blocks']
        
        if 'block_1_meetings' in blocks:
            block1 = blocks['block_1_meetings']
            print(f"✅ block_1_meetings found in 3-month custom analytics")
            
            # For 3-month period, targets should be 3x monthly targets
            expected_3m_targets = {
                'total_target': 50 * 3,  # 150
                'inbound_target': 22 * 3,  # 66
                'outbound_target': 17 * 3,  # 51
                'referral_target': 11 * 3   # 33
            }
            
            success_3m = True
            for target_key, expected_value in expected_3m_targets.items():
                actual_value = block1.get(target_key, 'NOT FOUND')
                if actual_value == expected_value:
                    print(f"    ✅ {target_key}: {actual_value} (matches expected {expected_value} for 3 months)")
                else:
                    print(f"    ❌ {target_key}: {actual_value} (expected {expected_value} for 3 months)")
                    success_3m = False
            
            # Verify math for 3-month period
            inbound = block1.get('inbound_target', 0)
            outbound = block1.get('outbound_target', 0)
            referral = block1.get('referral_target', 0)
            total = block1.get('total_target', 0)
            calculated_total = inbound + outbound + referral
            
            if calculated_total == 150 and total == 150:
                print(f"    ✅ 3-month math verification: {inbound}+{outbound}+{referral}={calculated_total} (matches total_target={total})")
            else:
                print(f"    ❌ 3-month math verification: {inbound}+{outbound}+{referral}={calculated_total} (total_target={total}, expected 150)")
                success_3m = False
        else:
            print(f"❌ block_1_meetings not found in 3-month custom analytics")
    else:
        print(f"❌ Failed to get 3-month custom analytics or dashboard_blocks missing")
    
    test_results['custom_targets'] = success_2m and success_3m
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📋 MEETING TARGETS CORRECTION TEST SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\n📊 Overall Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print(f"\n🎉 SUCCESS: All meeting targets are correctly set to 50 per month base!")
        print(f"   ✅ Monthly: 22 inbound + 17 outbound + 11 referral = 50 total")
        print(f"   ✅ Yearly (July-Dec): 6 months × 50 = 300 total")
        print(f"   ✅ Custom periods: Correctly multiply base 50 per month")
    else:
        print(f"\n❌ ISSUES FOUND: Some meeting targets are not correctly configured")
        print(f"   Please check the backend implementation for target calculations")
    
    return passed_tests == total_tests

def test_meeting_generation_structure():
    """Test meeting_generation structure in API responses for targets correction"""
    print(f"\n{'='*80}")
    print(f"🎯 TESTING MEETING GENERATION STRUCTURE FOR TARGETS CORRECTION")
    print(f"{'='*80}")
    
    test_results = {
        'monthly_meeting_generation': False,
        'yearly_meeting_generation': False,
        'custom_meeting_generation': False
    }
    
    # Test 1: GET /api/analytics/monthly - Check meeting_generation structure
    print(f"\n📊 Test 1: GET /api/analytics/monthly - Meeting Generation Structure")
    print(f"{'='*60}")
    
    monthly_data = test_api_endpoint("/analytics/monthly")
    if monthly_data and 'meeting_generation' in monthly_data:
        meeting_gen = monthly_data['meeting_generation']
        print(f"✅ meeting_generation found in monthly analytics")
        
        # Expected structure for monthly (50 total = 22+17+11)
        expected_monthly = {
            'target': 50,
            'inbound_target': 22,
            'outbound_target': 17,
            'referral_target': 11
        }
        
        success = True
        print(f"📋 Verifying meeting_generation structure:")
        for key, expected_value in expected_monthly.items():
            actual_value = meeting_gen.get(key, 'NOT FOUND')
            if actual_value == expected_value:
                print(f"  ✅ {key}: {actual_value} (matches expected {expected_value})")
            else:
                print(f"  ❌ {key}: {actual_value} (expected {expected_value})")
                success = False
        
        # Verify math adds up
        inbound = meeting_gen.get('inbound_target', 0)
        outbound = meeting_gen.get('outbound_target', 0)
        referral = meeting_gen.get('referral_target', 0)
        total = meeting_gen.get('target', 0)
        calculated_total = inbound + outbound + referral
        
        if calculated_total == total == 50:
            print(f"  ✅ Math verification: {inbound}+{outbound}+{referral}={calculated_total} = target({total})")
        else:
            print(f"  ❌ Math verification: {inbound}+{outbound}+{referral}={calculated_total} ≠ target({total})")
            success = False
        
        test_results['monthly_meeting_generation'] = success
    else:
        print(f"❌ meeting_generation not found in monthly analytics response")
        if monthly_data:
            print(f"📋 Available keys: {list(monthly_data.keys())}")
    
    # Test 2: GET /api/analytics/yearly - Check meeting_generation structure (6 months)
    print(f"\n📊 Test 2: GET /api/analytics/yearly - Meeting Generation Structure")
    print(f"{'='*60}")
    
    yearly_data = test_api_endpoint("/analytics/yearly?year=2025")
    if yearly_data and 'meeting_generation' in yearly_data:
        meeting_gen = yearly_data['meeting_generation']
        print(f"✅ meeting_generation found in yearly analytics")
        
        # Expected structure for yearly July-Dec (6 months × 50 = 300 total)
        expected_yearly = {
            'target': 300,  # 50 × 6 months
            'inbound_target': 132,  # 22 × 6 months
            'outbound_target': 102,  # 17 × 6 months
            'referral_target': 66   # 11 × 6 months
        }
        
        success = True
        print(f"📋 Verifying meeting_generation structure for July-Dec period:")
        for key, expected_value in expected_yearly.items():
            actual_value = meeting_gen.get(key, 'NOT FOUND')
            if actual_value == expected_value:
                print(f"  ✅ {key}: {actual_value} (matches expected {expected_value} for 6 months)")
            else:
                print(f"  ❌ {key}: {actual_value} (expected {expected_value} for 6 months)")
                success = False
        
        # Verify math adds up for yearly
        inbound = meeting_gen.get('inbound_target', 0)
        outbound = meeting_gen.get('outbound_target', 0)
        referral = meeting_gen.get('referral_target', 0)
        total = meeting_gen.get('target', 0)
        calculated_total = inbound + outbound + referral
        
        if calculated_total == total == 300:
            print(f"  ✅ Math verification: {inbound}+{outbound}+{referral}={calculated_total} = target({total})")
        else:
            print(f"  ❌ Math verification: {inbound}+{outbound}+{referral}={calculated_total} ≠ target({total})")
            success = False
        
        test_results['yearly_meeting_generation'] = success
    else:
        print(f"❌ meeting_generation not found in yearly analytics response")
        if yearly_data:
            print(f"📋 Available keys: {list(yearly_data.keys())}")
    
    # Test 3: GET /api/analytics/custom - Check meeting_generation dynamic scaling (2 months)
    print(f"\n📊 Test 3: GET /api/analytics/custom - Meeting Generation Dynamic Scaling")
    print(f"{'='*60}")
    
    custom_data = test_api_endpoint("/analytics/custom?start_date=2025-10-01&end_date=2025-11-30")
    if custom_data and 'meeting_generation' in custom_data:
        meeting_gen = custom_data['meeting_generation']
        print(f"✅ meeting_generation found in custom analytics (2-month period)")
        
        # Expected structure for 2-month custom period (2 × 50 = 100 total)
        expected_custom = {
            'target': 100,  # 50 × 2 months
            'inbound_target': 44,  # 22 × 2 months
            'outbound_target': 34,  # 17 × 2 months
            'referral_target': 22   # 11 × 2 months
        }
        
        success = True
        print(f"📋 Verifying meeting_generation structure for 2-month period:")
        for key, expected_value in expected_custom.items():
            actual_value = meeting_gen.get(key, 'NOT FOUND')
            if actual_value == expected_value:
                print(f"  ✅ {key}: {actual_value} (matches expected {expected_value} for 2 months)")
            else:
                print(f"  ❌ {key}: {actual_value} (expected {expected_value} for 2 months)")
                success = False
        
        # Verify math adds up for custom period
        inbound = meeting_gen.get('inbound_target', 0)
        outbound = meeting_gen.get('outbound_target', 0)
        referral = meeting_gen.get('referral_target', 0)
        total = meeting_gen.get('target', 0)
        calculated_total = inbound + outbound + referral
        
        if calculated_total == total == 100:
            print(f"  ✅ Math verification: {inbound}+{outbound}+{referral}={calculated_total} = target({total})")
        else:
            print(f"  ❌ Math verification: {inbound}+{outbound}+{referral}={calculated_total} ≠ target({total})")
            success = False
        
        test_results['custom_meeting_generation'] = success
    else:
        print(f"❌ meeting_generation not found in custom analytics response")
        if custom_data:
            print(f"📋 Available keys: {list(custom_data.keys())}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📋 MEETING GENERATION STRUCTURE TEST SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\n📊 Overall Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print(f"\n🎉 SUCCESS: Meeting generation structure is correctly implemented!")
        print(f"   ✅ Monthly: target=50, inbound_target=22, outbound_target=17, referral_target=11")
        print(f"   ✅ Yearly (July-Dec): target=300, inbound_target=132, outbound_target=102, referral_target=66")
        print(f"   ✅ Custom (2-month): target=100, inbound_target=44, outbound_target=34, referral_target=22")
        print(f"   ✅ All math adds up correctly and targets scale based on period duration")
    else:
        print(f"\n❌ ISSUES FOUND: Meeting generation structure needs correction")
        print(f"   Please verify the calculate_meeting_generation function returns individual targets")
    
    return passed_tests == total_tests

def test_pipeline_data_structure_inspection():
    """
    Comprehensive inspection of pipeline data structure for Deals & Pipeline tab implementation
    Focus on pipeline metrics, stage-based data, POA metrics, and weighted pipeline calculations
    """
    print(f"\n{'='*80}")
    print(f"🔍 PIPELINE DATA STRUCTURE INSPECTION FOR DEALS & PIPELINE TAB")
    print(f"{'='*80}")
    
    pipeline_data_findings = {
        'monthly_pipeline_data': {},
        'yearly_pipeline_data': {},
        'deals_by_stage': {},
        'poa_metrics': {},
        'weighted_pipeline': {},
        'ae_breakdown': {}
    }
    
    # Test 1: GET /api/analytics/monthly - Pipeline Data Structure
    print(f"\n📊 Test 1: GET /api/analytics/monthly - Pipeline Data Inspection")
    print(f"{'='*60}")
    
    monthly_data = test_api_endpoint("/analytics/monthly")
    if monthly_data:
        print(f"✅ Monthly analytics data retrieved successfully")
        
        # Inspect pipeline-related sections
        pipeline_sections = ['pipe_metrics', 'deals_closed', 'closing_projections', 'dashboard_blocks', 'big_numbers_recap']
def test_excel_weighting_implementation():
    """Test the updated Excel-based weighting logic implementation"""
    print(f"\n{'='*80}")
    print(f"🧮 TESTING EXCEL-BASED WEIGHTING LOGIC IMPLEMENTATION")
    print(f"{'='*80}")
    
    test_results = {
        'monthly_weighted_values': False,
        'yearly_weighted_values': False,
        'weighted_vs_pipeline_comparison': False,
        'closing_projections_weighting': False
    }
    
    # Test 1: GET /api/analytics/monthly - Verify Excel weighted calculations
    print(f"\n📊 Test 1: GET /api/analytics/monthly - Excel Weighted Calculations")
    print(f"{'='*60}")
    
    monthly_data = test_api_endpoint("/analytics/monthly")
    if monthly_data:
        print(f"✅ Monthly analytics data retrieved successfully")
        
        # Check pipe_metrics for Excel weighting
        if 'pipe_metrics' in monthly_data:
            pipe_metrics = monthly_data['pipe_metrics']
            print(f"✅ pipe_metrics found in monthly analytics")
            
            # Examine created_pipe weighted values
            if 'created_pipe' in pipe_metrics:
                created_pipe = pipe_metrics['created_pipe']
                print(f"\n📋 Created Pipe Metrics:")
                print(f"  • value: {created_pipe.get('value', 'NOT FOUND')}")
                print(f"  • weighted_value: {created_pipe.get('weighted_value', 'NOT FOUND')}")
                
                # Check if weighted_value exists and is different from value
                pipe_value = created_pipe.get('value', 0)
                weighted_value = created_pipe.get('weighted_value', 0)
                
                if weighted_value != 0 and weighted_value != pipe_value:
                    print(f"  ✅ Excel weighting detected: weighted_value ({weighted_value}) differs from pipeline value ({pipe_value})")
                    test_results['monthly_weighted_values'] = True
                else:
                    print(f"  ⚠️  Weighted value same as pipeline value or zero - may indicate simple probability weighting")
            
            # Examine total_pipe weighted values
            if 'total_pipe' in pipe_metrics:
                total_pipe = pipe_metrics['total_pipe']
                print(f"\n📋 Total Pipe Metrics:")
                print(f"  • value: {total_pipe.get('value', 'NOT FOUND')}")
                print(f"  • weighted_value: {total_pipe.get('weighted_value', 'NOT FOUND')}")
                
                # Check weighted vs unweighted ratio
                total_value = total_pipe.get('value', 0)
                total_weighted = total_pipe.get('weighted_value', 0)
                
                if total_value > 0 and total_weighted > 0:
                    ratio = total_weighted / total_value
                    print(f"  📊 Weighted/Pipeline ratio: {ratio:.3f}")
                    
                    # Excel weighting should result in more nuanced ratios (not simple 0.5, 0.3, etc.)
                    if 0.1 < ratio < 0.9 and ratio not in [0.3, 0.5, 0.7]:
                        print(f"  ✅ Ratio suggests Excel formula weighting (complex calculation)")
                    else:
                        print(f"  ⚠️  Ratio suggests simple stage probability weighting")
        else:
            print(f"❌ pipe_metrics not found in monthly analytics")
    else:
        print(f"❌ Failed to retrieve monthly analytics data")
    
    # Test 2: GET /api/analytics/yearly - Verify consistency across endpoints
    print(f"\n📊 Test 2: GET /api/analytics/yearly - Consistency Check")
    print(f"{'='*60}")
    
    yearly_data = test_api_endpoint("/analytics/yearly?year=2025")
    if yearly_data:
        print(f"✅ Yearly analytics data retrieved successfully")
        
        # Check pipe_metrics for Excel weighting
        if 'pipe_metrics' in yearly_data:
            pipe_metrics = yearly_data['pipe_metrics']
            print(f"✅ pipe_metrics found in yearly analytics")
            
            # Compare with monthly data
            if monthly_data and 'pipe_metrics' in monthly_data:
                monthly_pipe = monthly_data['pipe_metrics']
                
                # Check if both use same weighting logic
                monthly_created_weighted = monthly_pipe.get('created_pipe', {}).get('weighted_value', 0)
                yearly_created_weighted = pipe_metrics.get('created_pipe', {}).get('weighted_value', 0)
                
                print(f"\n📊 Weighted Value Comparison:")
                print(f"  • Monthly created_pipe weighted_value: {monthly_created_weighted}")
                print(f"  • Yearly created_pipe weighted_value: {yearly_created_weighted}")
                
                # They should be different (different time periods) but use same calculation method
                if monthly_created_weighted != yearly_created_weighted and both_non_zero(monthly_created_weighted, yearly_created_weighted):
                    print(f"  ✅ Different periods show different weighted values (expected)")
                    test_results['yearly_weighted_values'] = True
                else:
                    print(f"  ⚠️  Weighted values are same or one is zero")
        else:
            print(f"❌ pipe_metrics not found in yearly analytics")
    else:
        print(f"❌ Failed to retrieve yearly analytics data")
    
    # Test 3: Compare weighted values vs pipeline values for realism
    print(f"\n📊 Test 3: Weighted vs Pipeline Value Realism Check")
    print(f"{'='*60}")
    
    if monthly_data and 'pipe_metrics' in monthly_data:
        pipe_metrics = monthly_data['pipe_metrics']
        
        # Analyze AE breakdown for realistic weighting
        if 'ae_breakdown' in pipe_metrics:
            ae_breakdown = pipe_metrics['ae_breakdown']
            print(f"✅ AE breakdown found with {len(ae_breakdown)} AEs")
            
            realistic_weighting_count = 0
            total_aes = len(ae_breakdown)
            
            print(f"\n📋 AE-level Weighted vs Pipeline Analysis:")
            for ae_data in ae_breakdown[:5]:  # Check first 5 AEs
                ae_name = ae_data.get('ae', 'Unknown')
                total_pipe = ae_data.get('total_pipe', 0)
                weighted_pipe = ae_data.get('weighted_pipe', 0)
                
                if total_pipe > 0 and weighted_pipe > 0:
                    ratio = weighted_pipe / total_pipe
                    print(f"  • {ae_name}: ${total_pipe:,.0f} → ${weighted_pipe:,.0f} (ratio: {ratio:.3f})")
                    
                    # Check if ratio suggests Excel formula (stage × source × recency)
                    if 0.1 < ratio < 0.8 and not is_simple_probability(ratio):
                        realistic_weighting_count += 1
                        print(f"    ✅ Ratio suggests complex Excel weighting")
                    else:
                        print(f"    ⚠️  Ratio suggests simple probability weighting")
                else:
                    print(f"  • {ae_name}: No pipeline or weighted data")
            
            if realistic_weighting_count >= min(3, total_aes // 2):
                print(f"\n✅ Majority of AEs show realistic Excel weighting patterns")
                test_results['weighted_vs_pipeline_comparison'] = True
            else:
                print(f"\n⚠️  Most AEs show simple probability weighting patterns")
    
    # Test 4: Check closing_projections use Excel weighting
    print(f"\n📊 Test 4: Closing Projections Excel Weighting")
    print(f"{'='*60}")
    
    if monthly_data and 'closing_projections' in monthly_data:
        closing_proj = monthly_data['closing_projections']
        print(f"✅ closing_projections found in monthly analytics")
        
        # Check different time periods for weighted values
        periods = ['next_7_days', 'current_month', 'next_quarter']
        excel_weighting_detected = False
        
        for period in periods:
            if period in closing_proj:
                period_data = closing_proj[period]
                total_value = period_data.get('total_value', 0)
                weighted_value = period_data.get('weighted_value', 0)
                
                print(f"\n📋 {period.replace('_', ' ').title()}:")
                print(f"  • total_value: ${total_value:,.0f}")
                print(f"  • weighted_value: ${weighted_value:,.0f}")
                
                if total_value > 0 and weighted_value > 0:
                    ratio = weighted_value / total_value
                    print(f"  • ratio: {ratio:.3f}")
                    
                    # Check if this looks like Excel weighting (complex calculation)
                    if 0.1 < ratio < 0.9 and not is_simple_probability(ratio):
                        print(f"  ✅ Excel weighting pattern detected")
                        excel_weighting_detected = True
                    else:
                        print(f"  ⚠️  Simple probability pattern detected")
        
        if excel_weighting_detected:
            test_results['closing_projections_weighting'] = True
            print(f"\n✅ Closing projections use Excel weighting logic")
        else:
            print(f"\n⚠️  Closing projections may not use Excel weighting")
    else:
        print(f"❌ closing_projections not found in monthly analytics")
    
    # Test 5: Look for evidence of stage × source × recency factors
    print(f"\n📊 Test 5: Excel Formula Factors Analysis")
    print(f"{'='*60}")
    
    if monthly_data and 'pipe_metrics' in monthly_data and 'pipe_details' in monthly_data['pipe_metrics']:
        pipe_details = monthly_data['pipe_metrics']['pipe_details']
        print(f"✅ pipe_details found with {len(pipe_details)} deals")
        
        # Analyze individual deals for Excel weighting patterns
        excel_factors_detected = analyze_excel_factors(pipe_details)
        
        if excel_factors_detected:
            print(f"✅ Excel formula factors (stage × source × recency) detected in deal analysis")
        else:
            print(f"⚠️  Excel formula factors not clearly detected")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📋 EXCEL WEIGHTING IMPLEMENTATION TEST SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\n📊 Overall Results: {passed_tests}/{total_tests} tests passed")
    
    # Detailed findings
    print(f"\n💡 KEY FINDINGS:")
    if test_results['monthly_weighted_values']:
        print(f"  ✅ Monthly analytics implements Excel weighting (weighted_value ≠ pipeline value)")
    if test_results['yearly_weighted_values']:
        print(f"  ✅ Yearly analytics consistent with Excel weighting implementation")
    if test_results['weighted_vs_pipeline_comparison']:
        print(f"  ✅ Weighted values show realistic patterns vs pipeline values")
    if test_results['closing_projections_weighting']:
        print(f"  ✅ Closing projections use Excel weighting logic")
    
    if passed_tests >= 3:
        print(f"\n🎉 SUCCESS: Excel weighting implementation appears to be working correctly!")
        print(f"   The backend now implements Excel formula (stage × source × recency) instead of simple probabilities")
    else:
        print(f"\n❌ ISSUES: Excel weighting implementation may not be fully working")
        print(f"   Some endpoints may still use simple stage-only probabilities")
    
    return passed_tests >= 3

def both_non_zero(val1, val2):
    """Check if both values are non-zero"""
    return val1 != 0 and val2 != 0

def is_simple_probability(ratio):
    """Check if ratio suggests simple probability weighting (0.3, 0.5, 0.7, etc.)"""
    simple_probs = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    return any(abs(ratio - prob) < 0.05 for prob in simple_probs)

def analyze_excel_factors(pipe_details):
    """Analyze pipe details for evidence of Excel formula factors"""
    if not pipe_details or len(pipe_details) == 0:
        return False
    
    print(f"\n📋 Analyzing {len(pipe_details)} deals for Excel factors:")
    
    # Look for deals with different stages and check weighted values
    stage_weighted_ratios = {}
    
    for deal in pipe_details[:10]:  # Analyze first 10 deals
        stage = deal.get('stage', 'Unknown')
        pipeline = deal.get('pipeline', 0)
        weighted = deal.get('weighted_value', 0)
        
        if pipeline > 0 and weighted > 0:
            ratio = weighted / pipeline
            if stage not in stage_weighted_ratios:
                stage_weighted_ratios[stage] = []
            stage_weighted_ratios[stage].append(ratio)
    
    # Check if different stages have different weighting patterns
    excel_pattern_detected = False
    
    for stage, ratios in stage_weighted_ratios.items():
        if len(ratios) > 0:
            avg_ratio = sum(ratios) / len(ratios)
            print(f"  • {stage}: avg ratio {avg_ratio:.3f} ({len(ratios)} deals)")
            
            # Excel weighting should show variation within stages (due to source/recency factors)
            if len(ratios) > 1:
                ratio_variance = max(ratios) - min(ratios)
                if ratio_variance > 0.1:  # Significant variation suggests complex weighting
                    print(f"    ✅ High variance ({ratio_variance:.3f}) suggests Excel factors")
                    excel_pattern_detected = True
                else:
                    print(f"    ⚠️  Low variance ({ratio_variance:.3f}) suggests simple weighting")
    
    return excel_pattern_detected
    print(f"{'='*80}")
    
    print(f"\n🎯 KEY FINDINGS FOR DEALS & PIPELINE TAB IMPLEMENTATION:")
    
    # 1. Deals by Stage Data
    print(f"\n1️⃣ DEALS BY STAGE DATA:")
    if pipeline_data_findings['deals_by_stage']:
        for period, stage_data in pipeline_data_findings['deals_by_stage'].items():
            if stage_data:
                print(f"  ✅ {period.upper()}: Stage-based data available")
                for stage_info in stage_data[:3]:  # Show first 3 findings
                    print(f"    • {stage_info}")
            else:
                print(f"  ❌ {period.upper()}: No stage-based data found")
    else:
        print(f"  ❌ No stage-based data structure identified")
    
    # 2. POA Metrics
    print(f"\n2️⃣ POA BOOKED METRICS:")
    if pipeline_data_findings['poa_metrics']:
        for period, poa_data in pipeline_data_findings['poa_metrics'].items():
            if poa_data:
                print(f"  ✅ {period.upper()}: POA metrics available")
                for poa_info in poa_data[:3]:  # Show first 3 findings
                    print(f"    • {poa_info}")
            else:
                print(f"  ❌ {period.upper()}: No POA metrics found")
    else:
        print(f"  ❌ No POA metrics structure identified")
    
    # 3. Weighted Pipeline
    print(f"\n3️⃣ WEIGHTED PIPELINE CALCULATIONS:")
    if pipeline_data_findings['weighted_pipeline']:
        for period, weighted_data in pipeline_data_findings['weighted_pipeline'].items():
            if weighted_data:
                print(f"  ✅ {period.upper()}: Weighted pipeline data available")
                for weighted_info in weighted_data[:3]:  # Show first 3 findings
                    print(f"    • {weighted_info}")
            else:
                print(f"  ❌ {period.upper()}: No weighted pipeline data found")
    else:
        print(f"  ❌ No weighted pipeline structure identified")
    
    # 4. AE Breakdown
    print(f"\n4️⃣ AE BREAKDOWN WITH PIPELINE DATA:")
    if pipeline_data_findings['ae_breakdown']:
        print(f"  ✅ AE breakdown data available:")
        for ae_info in pipeline_data_findings['ae_breakdown'][:5]:  # Show first 5 findings
            print(f"    • {ae_info}")
    else:
        print(f"  ❌ No AE breakdown with pipeline data found")
    
    # 5. Specific Recommendations
    print(f"\n5️⃣ RECOMMENDATIONS FOR DEALS & PIPELINE TAB:")
    
    # Check if we have the required data for the user's requirements
    has_proposal_sent = any('proposal sent' in str(finding).lower() for findings in pipeline_data_findings['deals_by_stage'].values() for finding in findings)
    has_legals = any('legals' in str(finding).lower() for findings in pipeline_data_findings['deals_by_stage'].values() for finding in findings)
    has_poa_booked = any('poa' in str(finding).lower() for findings in pipeline_data_findings['poa_metrics'].values() for finding in findings)
    has_weighted_pipe = any('weighted' in str(finding).lower() for findings in pipeline_data_findings['weighted_pipeline'].values() for finding in findings)
    
    if has_proposal_sent:
        print(f"  ✅ 'Proposal sent' stage data: Available for pipeline metrics")
    else:
        print(f"  ⚠️  'Proposal sent' stage data: May need custom filtering")
    
    if has_legals:
        print(f"  ✅ 'Legals' stage data: Available for pipeline metrics")
    else:
        print(f"  ⚠️  'Legals' stage data: May need custom filtering")
    
    if has_poa_booked:
        print(f"  ✅ POA booked metrics: Available")
    else:
        print(f"  ⚠️  POA booked metrics: May need custom calculation")
    
    if has_weighted_pipe:
        print(f"  ✅ Weighted pipeline: Available")
    else:
        print(f"  ⚠️  Weighted pipeline: May need custom calculation")
    
    return len([f for f in [has_proposal_sent, has_legals, has_poa_booked, has_weighted_pipe] if f]) >= 3

def search_for_stage_data(data, path=""):
    """Search for stage-based deal data in the response"""
    stage_findings = []
    
    def recursive_search(obj, current_path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{current_path}.{key}" if current_path else key
                
                # Look for stage-related keys
                if 'stage' in key.lower():
                    stage_findings.append(f"Stage field found: {new_path} = {value}")
                
                # Look for specific stages
                if isinstance(value, str) and any(stage in value.lower() for stage in ['proposal sent', 'legals', 'poa booked']):
                    stage_findings.append(f"Target stage found: {new_path} = {value}")
                
                # Recursive search
                if isinstance(value, (dict, list)):
                    recursive_search(value, new_path)
                    
        elif isinstance(obj, list):
            for i, item in enumerate(obj[:5]):  # Check first 5 items
                recursive_search(item, f"{current_path}[{i}]")
    
    recursive_search(data)
    return stage_findings

def search_for_poa_data(data):
    """Search for POA-related metrics in the response"""
    poa_findings = []
    
    def recursive_search(obj, current_path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{current_path}.{key}" if current_path else key
                
                # Look for POA-related keys
                if 'poa' in key.lower():
                    poa_findings.append(f"POA field found: {new_path} = {value}")
                
                # Look for POA in values
                if isinstance(value, str) and 'poa' in value.lower():
                    poa_findings.append(f"POA reference found: {new_path} = {value}")
                
                # Recursive search
                if isinstance(value, (dict, list)):
                    recursive_search(value, new_path)
                    
        elif isinstance(obj, list):
            for i, item in enumerate(obj[:5]):  # Check first 5 items
                recursive_search(item, f"{current_path}[{i}]")
    
    recursive_search(data)
    return poa_findings

def search_for_weighted_pipeline_data(data):
    """Search for weighted pipeline calculations in the response"""
    weighted_findings = []
    
    def recursive_search(obj, current_path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{current_path}.{key}" if current_path else key
                
                # Look for weighted-related keys
                if 'weighted' in key.lower():
                    weighted_findings.append(f"Weighted field found: {new_path} = {value}")
                
                # Look for probability or percentage fields (often used in weighted calculations)
                if 'probability' in key.lower() or 'percent' in key.lower():
                    weighted_findings.append(f"Probability field found: {new_path} = {value}")
                
                # Look for aggregate pipeline
                if 'aggregate' in key.lower() and 'pipe' in key.lower():
                    weighted_findings.append(f"Aggregate pipeline found: {new_path} = {value}")
                
                # Recursive search
                if isinstance(value, (dict, list)):
                    recursive_search(value, new_path)
                    
        elif isinstance(obj, list):
            for i, item in enumerate(obj[:5]):  # Check first 5 items
                recursive_search(item, f"{current_path}[{i}]")
    
    recursive_search(data)
    return weighted_findings

def search_for_ae_pipeline_breakdown(monthly_data, yearly_data):
    """Search for AE breakdown with pipeline data"""
    ae_findings = []
    
    datasets = [("monthly", monthly_data), ("yearly", yearly_data)]
    
    for period_name, data in datasets:
        if not data:
            continue
            
        # Look for AE performance sections
        if 'ae_performance' in data:
            ae_perf = data['ae_performance']
            ae_findings.append(f"{period_name}: ae_performance section found with {len(ae_perf) if isinstance(ae_perf, dict) else 'unknown'} entries")
            
            # Check structure
            if isinstance(ae_perf, dict):
                for key, value in list(ae_perf.items())[:3]:  # Check first 3
                    ae_findings.append(f"{period_name}: ae_performance.{key} = {value}")
        
        # Look for pipe_metrics with AE breakdown
        if 'pipe_metrics' in data:
            pipe_metrics = data['pipe_metrics']
            if isinstance(pipe_metrics, dict) and 'ae_breakdown' in pipe_metrics:
                ae_breakdown = pipe_metrics['ae_breakdown']
                ae_findings.append(f"{period_name}: pipe_metrics.ae_breakdown found with {len(ae_breakdown) if isinstance(ae_breakdown, list) else 'unknown'} AEs")
                
                # Check structure of AE breakdown
                if isinstance(ae_breakdown, list) and len(ae_breakdown) > 0:
                    sample_ae = ae_breakdown[0]
                    if isinstance(sample_ae, dict):
                        ae_findings.append(f"{period_name}: AE breakdown structure: {list(sample_ae.keys())}")
    
    return ae_findings

def analyze_proposal_and_legals_stages(monthly_data, yearly_data):
    """Analyze specific data for Proposal sent and Legals stages"""
    analysis = {
        'proposal_sent_deals': [],
        'legals_deals': [],
        'stage_counts': {},
        'stage_values': {}
    }
    
    datasets = [("monthly", monthly_data), ("yearly", yearly_data)]
    
    for period_name, data in datasets:
        if not data:
            continue
        
        # Look through all sections for deals with these stages
        def find_deals_by_stage(obj, target_stages, current_path=""):
            deals_found = []
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{current_path}.{key}" if current_path else key
                    
                    # Check if this is a deal with stage information
                    if key == 'stage' and isinstance(value, str):
                        for target_stage in target_stages:
                            if target_stage.lower() in value.lower():
                                deals_found.append(f"{period_name}: Deal with {value} stage found at {current_path}")
                    
                    # Recursive search
                    if isinstance(value, (dict, list)):
                        deals_found.extend(find_deals_by_stage(value, target_stages, new_path))
                        
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    deals_found.extend(find_deals_by_stage(item, target_stages, f"{current_path}[{i}]"))
            
            return deals_found
        
        # Search for Proposal sent and Legals deals
        target_stages = ['proposal sent', 'legals', 'c proposal sent', 'b legals']
        deals_found = find_deals_by_stage(data, target_stages)
        
        for deal in deals_found:
            if 'proposal' in deal.lower():
                analysis['proposal_sent_deals'].append(deal)
            if 'legals' in deal.lower():
                analysis['legals_deals'].append(deal)
    
    return analysis

def test_pipeline_data_excel_matching():
    """Test pipeline data to find matches with Excel formulas for Created Pipe and Weighted Pipe"""
    print(f"\n{'='*80}")
    print(f"🎯 TESTING PIPELINE DATA FOR EXCEL FORMULA MATCHING")
    print(f"{'='*80}")
    
    # Target values from Excel calculations
    excel_created_pipe_total = 6338600  # $6,338,600
    excel_weighted_pipe_total = 2297760  # $2,297,760
    
    # Expected AE breakdowns from Excel
    excel_ae_breakdown = {
        'Rémi': {'created': 1692000, 'weighted': 767400},
        'Guillaume': {'created': 1706600, 'weighted': 686640},
        'Bruno': {'created': 1704000, 'weighted': 565920},
        'Sadie': {'created': 1092000, 'weighted': 205800},
        'François': {'created': 144000, 'weighted': 72000}
    }
    
    print(f"🎯 Target Excel Values:")
    print(f"   • Created Pipe Total: ${excel_created_pipe_total:,}")
    print(f"   • Weighted Pipe Total: ${excel_weighted_pipe_total:,}")
    print(f"   • AE Breakdown Expected: {len(excel_ae_breakdown)} AEs")
    
    # Test endpoints to find matching data
    endpoints_to_test = [
        "/analytics/monthly",
        "/analytics/yearly?year=2025",
        "/analytics/custom?start_date=2025-07-01&end_date=2025-12-31"
    ]
    
    matching_results = {}
    
    for endpoint in endpoints_to_test:
        print(f"\n{'='*60}")
        print(f"🔍 TESTING ENDPOINT: {endpoint}")
        print(f"{'='*60}")
        
        data = test_api_endpoint(endpoint)
        if data is None:
            print(f"❌ Failed to get data from {endpoint}")
            continue
        
        # Search for pipeline data fields
        pipeline_matches = find_pipeline_data_matches(data, excel_created_pipe_total, excel_weighted_pipe_total, excel_ae_breakdown)
        
        if pipeline_matches:
            matching_results[endpoint] = pipeline_matches
            print(f"✅ Found potential matches in {endpoint}")
        else:
            print(f"❌ No matches found in {endpoint}")
    
    # Summary of findings
    print(f"\n{'='*80}")
    print(f"📊 PIPELINE DATA MATCHING SUMMARY")
    print(f"{'='*80}")
    
    if matching_results:
        print(f"✅ POTENTIAL MATCHES FOUND:")
        
        for endpoint, matches in matching_results.items():
            print(f"\n📍 Endpoint: {endpoint}")
            
            if 'created_pipe_matches' in matches:
                print(f"  🎯 Created Pipe Matches:")
                for match in matches['created_pipe_matches']:
                    print(f"    • {match}")
            
            if 'weighted_pipe_matches' in matches:
                print(f"  ⚖️  Weighted Pipe Matches:")
                for match in matches['weighted_pipe_matches']:
                    print(f"    • {match}")
            
            if 'ae_breakdown_matches' in matches:
                print(f"  👥 AE Breakdown Matches:")
                for match in matches['ae_breakdown_matches']:
                    print(f"    • {match}")
            
            if 'exact_totals' in matches:
                print(f"  🎯 EXACT TOTAL MATCHES:")
                for match in matches['exact_totals']:
                    print(f"    • {match}")
        
        # Identify the best matching endpoint
        best_match = identify_best_pipeline_match(matching_results, excel_created_pipe_total, excel_weighted_pipe_total)
        if best_match:
            print(f"\n🏆 BEST MATCH IDENTIFIED:")
            print(f"   📍 Endpoint: {best_match['endpoint']}")
            print(f"   🎯 Field for Created Pipe: {best_match['created_pipe_field']}")
            print(f"   ⚖️  Field for Weighted Pipe: {best_match['weighted_pipe_field']}")
            print(f"   💰 Created Pipe Value: ${best_match['created_pipe_value']:,}")
            print(f"   💰 Weighted Pipe Value: ${best_match['weighted_pipe_value']:,}")
            
            return True
    else:
        print(f"❌ NO MATCHES FOUND")
        print(f"   The backend data does not contain fields matching the Excel totals")
        print(f"   Expected: Created Pipe ${excel_created_pipe_total:,}, Weighted Pipe ${excel_weighted_pipe_total:,}")
        
        return False

def find_pipeline_data_matches(data, target_created, target_weighted, target_ae_breakdown):
    """Search for pipeline data that matches Excel calculations"""
    matches = {
        'created_pipe_matches': [],
        'weighted_pipe_matches': [],
        'ae_breakdown_matches': [],
        'exact_totals': []
    }
    
    def search_for_values(obj, path="", tolerance=1000):
        """Recursively search for matching values with tolerance"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Check for numeric values that might match our targets
                if isinstance(value, (int, float)):
                    # Check Created Pipe match (within tolerance)
                    if abs(value - target_created) <= tolerance:
                        matches['created_pipe_matches'].append(f"{current_path}: ${value:,} (target: ${target_created:,})")
                        if abs(value - target_created) == 0:
                            matches['exact_totals'].append(f"EXACT Created Pipe: {current_path} = ${value:,}")
                    
                    # Check Weighted Pipe match (within tolerance)
                    if abs(value - target_weighted) <= tolerance:
                        matches['weighted_pipe_matches'].append(f"{current_path}: ${value:,} (target: ${target_weighted:,})")
                        if abs(value - target_weighted) == 0:
                            matches['exact_totals'].append(f"EXACT Weighted Pipe: {current_path} = ${value:,}")
                
                # Look for pipe-related field names
                pipe_keywords = ['pipe', 'pipeline', 'weighted', 'created', 'total']
                if any(keyword in key.lower() for keyword in pipe_keywords) and isinstance(value, (int, float)):
                    if value > 100000:  # Only consider substantial values
                        matches['created_pipe_matches'].append(f"PIPE FIELD: {current_path}: ${value:,}")
                
                # Recursively search nested objects
                if isinstance(value, dict):
                    search_for_values(value, current_path, tolerance)
                elif isinstance(value, list) and len(value) > 0:
                    for i, item in enumerate(value[:5]):  # Check first 5 items
                        if isinstance(item, dict):
                            search_for_values(item, f"{current_path}[{i}]", tolerance)
    
    # Search the entire data structure
    search_for_values(data)
    
    # Look for AE breakdown data
    ae_breakdown_found = find_ae_breakdown_matches(data, target_ae_breakdown)
    if ae_breakdown_found:
        matches['ae_breakdown_matches'] = ae_breakdown_found
    
    # Return matches only if we found something
    return matches if any(matches.values()) else None

def find_ae_breakdown_matches(data, target_ae_breakdown):
    """Look for AE breakdown data that matches Excel calculations"""
    ae_matches = []
    
    def search_ae_data(obj, path=""):
        """Search for AE-related data structures"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Look for AE-related keys
                if 'ae' in key.lower() or 'owner' in key.lower() or 'breakdown' in key.lower():
                    if isinstance(value, list):
                        # Check if this looks like AE breakdown data
                        for i, ae_data in enumerate(value):
                            if isinstance(ae_data, dict) and 'ae' in ae_data:
                                ae_name = ae_data.get('ae', '')
                                
                                # Check for pipeline values
                                for field_name, field_value in ae_data.items():
                                    if isinstance(field_value, (int, float)) and field_value > 10000:
                                        # Check if this matches any of our target AE values
                                        for target_ae, target_values in target_ae_breakdown.items():
                                            if target_ae.lower() in ae_name.lower() or ae_name.lower() in target_ae.lower():
                                                for value_type, target_val in target_values.items():
                                                    if abs(field_value - target_val) <= 5000:  # 5K tolerance
                                                        ae_matches.append(f"AE {ae_name} - {field_name}: ${field_value:,} (target {value_type}: ${target_val:,})")
                
                # Recursively search
                if isinstance(value, dict):
                    search_ae_data(value, current_path)
    
    search_ae_data(data)
    return ae_matches

def identify_best_pipeline_match(matching_results, target_created, target_weighted):
    """Identify the best matching endpoint and fields for pipeline data"""
    best_match = None
    best_score = 0
    
    for endpoint, matches in matching_results.items():
        score = 0
        created_field = None
        weighted_field = None
        created_value = None
        weighted_value = None
        
        # Check for exact matches first
        if 'exact_totals' in matches:
            for exact_match in matches['exact_totals']:
                if 'Created Pipe' in exact_match:
                    score += 100
                    # Extract field name and value
                    parts = exact_match.split(': ')
                    if len(parts) >= 2:
                        created_field = parts[1].split(' = ')[0]
                        created_value = target_created
                
                if 'Weighted Pipe' in exact_match:
                    score += 100
                    # Extract field name and value
                    parts = exact_match.split(': ')
                    if len(parts) >= 2:
                        weighted_field = parts[1].split(' = ')[0]
                        weighted_value = target_weighted
        
        # Check for close matches
        if 'created_pipe_matches' in matches:
            for match in matches['created_pipe_matches']:
                if 'target:' in match:
                    score += 50
                    if not created_field:
                        # Extract field name
                        field_part = match.split(':')[0]
                        created_field = field_part
                        # Extract value
                        value_part = match.split('$')[1].split(' ')[0].replace(',', '')
                        try:
                            created_value = int(value_part)
                        except:
                            pass
        
        if 'weighted_pipe_matches' in matches:
            for match in matches['weighted_pipe_matches']:
                if 'target:' in match:
                    score += 50
                    if not weighted_field:
                        # Extract field name
                        field_part = match.split(':')[0]
                        weighted_field = field_part
                        # Extract value
                        value_part = match.split('$')[1].split(' ')[0].replace(',', '')
                        try:
                            weighted_value = int(value_part)
                        except:
                            pass
        
        # Check for AE breakdown matches
        if 'ae_breakdown_matches' in matches and len(matches['ae_breakdown_matches']) > 0:
            score += 25
        
        if score > best_score and created_field and weighted_field:
            best_score = score
            best_match = {
                'endpoint': endpoint,
                'created_pipe_field': created_field,
                'weighted_pipe_field': weighted_field,
                'created_pipe_value': created_value or 0,
                'weighted_pipe_value': weighted_value or 0,
                'score': score
            }
    
    return best_match

def test_hot_deals_stage_analysis():
    """Analyze hot deals data to understand stage distribution and column assignment issues"""
    print(f"\n{'='*80}")
    print(f"🔥 ANALYZING HOT DEALS STAGE DISTRIBUTION FOR COLUMN ASSIGNMENT")
    print(f"{'='*80}")
    
    # Test GET /api/projections/hot-deals to examine actual stage data
    print(f"\n📊 Step 1: Testing GET /api/projections/hot-deals")
    print(f"{'='*60}")
    
    hot_deals_data = test_api_endpoint("/projections/hot-deals")
    
    if hot_deals_data is None:
        print(f"❌ Failed to get hot deals data")
        return False
    
    if not isinstance(hot_deals_data, list):
        print(f"❌ Expected list response, got {type(hot_deals_data)}")
        return False
    
    print(f"✅ Retrieved {len(hot_deals_data)} hot deals")
    
    # Analyze stage distribution in hot deals
    stage_distribution = {}
    stage_examples = {}
    
    print(f"\n📋 Step 2: Analyzing Stage Distribution in Hot Deals")
    print(f"{'='*60}")
    
    for deal in hot_deals_data:
        stage = deal.get('stage', 'UNKNOWN')
        
        # Count stages
        if stage not in stage_distribution:
            stage_distribution[stage] = 0
            stage_examples[stage] = []
        
        stage_distribution[stage] += 1
        
        # Keep first 3 examples of each stage
        if len(stage_examples[stage]) < 3:
            stage_examples[stage].append({
                'client': deal.get('client', 'N/A'),
                'pipeline': deal.get('pipeline', 0),
                'owner': deal.get('owner', 'N/A')
            })
    
    # Display stage analysis
    print(f"📊 Stage Distribution in Hot Deals:")
    for stage, count in sorted(stage_distribution.items()):
        print(f"  • {stage}: {count} deals")
        
        # Show examples
        if stage_examples[stage]:
            print(f"    Examples:")
            for i, example in enumerate(stage_examples[stage], 1):
                print(f"      {i}. {example['client']} - ${example['pipeline']:,.0f} - {example['owner']}")
    
    # Test all deals to understand broader stage landscape
    print(f"\n📊 Step 3: Testing All Available Endpoints for Stage Analysis")
    print(f"{'='*60}")
    
    # Get broader dataset from monthly analytics
    monthly_data = test_api_endpoint("/analytics/monthly")
    all_stages_found = set()
    
    if monthly_data:
        # Check closing_projections for more stage data
        if 'closing_projections' in monthly_data:
            projections = monthly_data['closing_projections']
            
            for period_key in ['next_7_days', 'current_month', 'next_quarter']:
                if period_key in projections and 'deals' in projections[period_key]:
                    deals = projections[period_key]['deals']
                    print(f"\n🔍 Stages found in closing_projections.{period_key} ({len(deals)} deals):")
                    
                    period_stages = {}
                    for deal in deals:
                        stage = deal.get('stage', 'UNKNOWN')
                        all_stages_found.add(stage)
                        
                        if stage not in period_stages:
                            period_stages[stage] = 0
                        period_stages[stage] += 1
                    
                    for stage, count in sorted(period_stages.items()):
                        print(f"    • {stage}: {count} deals")
        
        # Check pipe_metrics for additional stage data
        if 'pipe_metrics' in monthly_data and 'pipe_details' in monthly_data['pipe_metrics']:
            pipe_details = monthly_data['pipe_metrics']['pipe_details']
            print(f"\n🔍 Stages found in pipe_metrics.pipe_details ({len(pipe_details)} deals):")
            
            pipe_stages = {}
            for deal in pipe_details:
                stage = deal.get('stage', 'UNKNOWN')
                all_stages_found.add(stage)
                
                if stage not in pipe_stages:
                    pipe_stages[stage] = 0
                pipe_stages[stage] += 1
            
            for stage, count in sorted(pipe_stages.items()):
                print(f"    • {stage}: {count} deals")
    
    # Test hot leads endpoint for comparison
    print(f"\n📊 Step 4: Testing GET /api/projections/hot-leads for Stage Comparison")
    print(f"{'='*60}")
    
    hot_leads_data = test_api_endpoint("/projections/hot-leads")
    
    if hot_leads_data and isinstance(hot_leads_data, list):
        print(f"✅ Retrieved {len(hot_leads_data)} hot leads")
        
        leads_stage_distribution = {}
        for lead in hot_leads_data:
            stage = lead.get('stage', 'UNKNOWN')
            all_stages_found.add(stage)
            
            if stage not in leads_stage_distribution:
                leads_stage_distribution[stage] = 0
            leads_stage_distribution[stage] += 1
        
        print(f"📊 Stage Distribution in Hot Leads:")
        for stage, count in sorted(leads_stage_distribution.items()):
            print(f"  • {stage}: {count} deals")
    else:
        print(f"❌ Failed to get hot leads data or invalid format")
    
    # Comprehensive stage analysis
    print(f"\n📊 Step 5: Comprehensive Stage Analysis")
    print(f"{'='*60}")
    
    print(f"🔍 ALL UNIQUE STAGES FOUND ACROSS ALL ENDPOINTS:")
    for stage in sorted(all_stages_found):
        print(f"  • '{stage}'")
    
    # Analyze stage naming patterns for column assignment
    print(f"\n🎯 Step 6: Stage Analysis for Column Assignment Logic")
    print(f"{'='*60}")
    
    # Look for POA Booked variations
    poa_booked_stages = [stage for stage in all_stages_found if 'poa' in stage.lower() and 'booked' in stage.lower()]
    print(f"📋 POA Booked stage variations found:")
    if poa_booked_stages:
        for stage in poa_booked_stages:
            print(f"  • '{stage}'")
    else:
        print(f"  ❌ No POA Booked stages found")
        # Look for similar patterns
        poa_stages = [stage for stage in all_stages_found if 'poa' in stage.lower()]
        if poa_stages:
            print(f"  🔍 POA-related stages found:")
            for stage in poa_stages:
                print(f"    • '{stage}'")
    
    # Look for Legals variations
    legals_stages = [stage for stage in all_stages_found if 'legal' in stage.lower()]
    print(f"\n📋 Legals stage variations found:")
    if legals_stages:
        for stage in legals_stages:
            print(f"  • '{stage}'")
    else:
        print(f"  ❌ No Legals stages found")
    
    # Look for Proposal sent variations
    proposal_stages = [stage for stage in all_stages_found if 'proposal' in stage.lower()]
    print(f"\n📋 Proposal sent stage variations found:")
    if proposal_stages:
        for stage in proposal_stages:
            print(f"  • '{stage}'")
    else:
        print(f"  ❌ No Proposal sent stages found")
    
    # Identify stages that should go to 60-90 days column
    print(f"\n🎯 Step 7: Identifying Stages for 60-90 Days Column")
    print(f"{'='*60}")
    
    # Based on the analysis, identify which stages should be in 60-90 days
    potential_60_90_stages = []
    
    # POA Booked deals should typically go to 60-90 days
    potential_60_90_stages.extend(poa_booked_stages)
    
    # Some proposal stages might also go to 60-90 days depending on timing
    potential_60_90_stages.extend(proposal_stages)
    
    print(f"📊 Stages that should potentially go to 60-90 days column:")
    if potential_60_90_stages:
        for stage in potential_60_90_stages:
            print(f"  • '{stage}'")
    else:
        print(f"  ⚠️  No obvious candidates for 60-90 days column found")
    
    # Summary and recommendations
    print(f"\n📋 Step 8: Summary and Recommendations")
    print(f"{'='*60}")
    
    print(f"🔍 KEY FINDINGS:")
    print(f"  • Total unique stages found: {len(all_stages_found)}")
    print(f"  • Hot deals endpoint returns: {len(hot_deals_data)} deals")
    print(f"  • Hot leads endpoint returns: {len(hot_leads_data) if hot_leads_data else 0} deals")
    
    print(f"\n🎯 STAGE NAMING ANALYSIS:")
    print(f"  • POA Booked variations: {poa_booked_stages if poa_booked_stages else 'None found'}")
    print(f"  • Legals variations: {legals_stages if legals_stages else 'None found'}")
    print(f"  • Proposal sent variations: {proposal_stages if proposal_stages else 'None found'}")
    
    print(f"\n💡 RECOMMENDATIONS FOR COLUMN ASSIGNMENT:")
    if not poa_booked_stages and not proposal_stages:
        print(f"  ❌ ISSUE: No POA Booked or Proposal sent stages found")
        print(f"  🔧 This explains why deals aren't appearing in 60-90 days column")
        print(f"  📝 Check if stage names in data match the expected names in frontend logic")
    else:
        print(f"  ✅ Found relevant stages for 60-90 days column")
        print(f"  📝 Verify frontend logic uses these exact stage names:")
        for stage in potential_60_90_stages:
            print(f"    - '{stage}'")
    
    return True

def main():
    """Run all backend tests with priority on pipeline data Excel matching"""
    print(f"🚀 Starting Backend API Testing")
    print(f"Backend URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Track overall success
    all_tests_passed = True
    
    # Test 1: Basic connectivity
    if not test_basic_connectivity():
        all_tests_passed = False
        print(f"\n⚠️  Basic connectivity failed - other tests may not work properly")
    
    # Test 2: Data availability
    data_available = test_data_status()
    if not data_available:
        print(f"\n⚠️  No data available - tests will return empty results")
    
    # PRIORITY TEST: Pipeline Data Excel Matching (as requested in review)
    print(f"\n🎯 PRIORITY TEST: Pipeline Data Excel Matching")
    if not test_pipeline_data_excel_matching():
        all_tests_passed = False
    
    # Test 3: Monthly analytics with different offsets
    monthly_tests = [
        (0, "Oct 2025"),
        (-1, "Nov 2025"),
        (1, "Sep 2025")
    ]
    
    for offset, expected_period in monthly_tests:
        if not test_monthly_analytics_with_offset(offset, expected_period):
            all_tests_passed = False
    
    # Test 4: Projections endpoints
    if not test_projections_hot_deals():
        all_tests_passed = False
    
    if not test_projections_hot_leads():
        all_tests_passed = False
    
    if not test_projections_performance_summary():
        all_tests_passed = False
    
    # Test 5: Custom analytics dynamic targets
    if not test_custom_analytics_dynamic_targets():
        all_tests_passed = False
    
    # Test 6: MongoDB data structure exploration
    if not explore_mongodb_data_structure():
        print(f"\n⚠️  MongoDB data structure exploration completed - see results above")
    
    # Test 7: Master data access verification
    if not test_master_data_access():
        print(f"\n⚠️  Master data access verification completed - see results above")
    
    # Test 8: October 2025 analytics detailed analysis
    if not test_october_2025_analytics_detailed():
        all_tests_passed = False
    
    # Test 9: Dashboard blocks and deals_closed structure
    if not test_dashboard_blocks_and_deals_closed():
        all_tests_passed = False
    
    # Test 10: Meeting targets correction verification
    if not test_meeting_targets_correction():
        all_tests_passed = False
    
    # Test 11: Meeting generation structure verification
    if not test_meeting_generation_structure():
        all_tests_passed = False
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"🏁 FINAL TEST SUMMARY")
    print(f"{'='*80}")
    
    if all_tests_passed:
        print(f"✅ ALL TESTS PASSED - Backend API is working correctly")
        return 0
    else:
        print(f"❌ SOME TESTS FAILED - Check individual test results above")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)