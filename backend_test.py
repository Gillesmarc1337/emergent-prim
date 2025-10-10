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
BASE_URL = "https://pipeline-metrics-1.preview.emergentagent.com/api"

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

def main():
    """Main testing function for master data verification"""
    print(f"🚀 Starting MongoDB Master Data Structure Verification")
    print(f"Base URL: {BASE_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Track test results
    test_results = {
        'connectivity': False,
        'master_data_access': False,
        'data_structure_exploration': False,
        'monthly_data_2025': False,
        'target_metrics_found': False
    }
    
    # Test 1: Basic connectivity
    test_results['connectivity'] = test_basic_connectivity()
    
    if not test_results['connectivity']:
        print(f"❌ Cannot proceed without API connectivity")
        return 1
    
    # Test 2: Master data access
    test_results['master_data_access'] = test_master_data_access()
    
    # Test 3: Explore data structure
    test_results['data_structure_exploration'] = explore_mongodb_data_structure()
    
    # Test 4: Specific search for 2025 monthly data
    print(f"\n{'='*60}")
    print(f"📅 SEARCHING FOR 2025 MONTHLY STRUCTURED DATA")
    print(f"{'='*60}")
    
    # Test July to December 2025 data specifically
    july_dec_data = test_api_endpoint("/analytics/yearly?year=2025")
    if july_dec_data and 'dashboard_blocks' in july_dec_data:
        blocks = july_dec_data['dashboard_blocks']
        monthly_2025_found = False
        
        for block_name, block_data in blocks.items():
            if isinstance(block_data, dict) and 'period' in block_data:
                period = block_data['period']
                if 'Jul-Dec 2025' in str(period) or '2025' in str(period):
                    monthly_2025_found = True
                    print(f"✅ Found 2025 monthly data in {block_name}: {period}")
                    
                    # Show the structure
                    print(f"   📊 Structure:")
                    for key, value in block_data.items():
                        if isinstance(value, (int, float, str)):
                            print(f"     • {key}: {value}")
        
        test_results['monthly_data_2025'] = monthly_2025_found
    
    # Test 5: Search for specific metrics
    print(f"\n{'='*60}")
    print(f"🎯 SEARCHING FOR SPECIFIC TARGET METRICS")
    print(f"{'='*60}")
    
    target_metrics_found = False
    
    # Check multiple endpoints for the requested metrics
    endpoints_to_check = [
        "/analytics/yearly?year=2025",
        "/analytics/monthly",
        "/projections/performance-summary"
    ]
    
    for endpoint in endpoints_to_check:
        print(f"\n🔍 Checking {endpoint} for target metrics...")
        data = test_api_endpoint(endpoint)
        
        if data:
            metrics = find_target_metrics(data, endpoint)
            if metrics:
                target_metrics_found = True
                print(f"✅ Target metrics found in {endpoint}:")
                for metric in metrics:
                    print(f"  • {metric}")
    
    test_results['target_metrics_found'] = target_metrics_found
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📋 MASTER DATA VERIFICATION SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, result in test_results.items():
        status = "✅ FOUND" if result else "❌ NOT FOUND"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} components verified")
    
    # Final assessment
    if test_results['master_data_access'] and test_results['monthly_data_2025']:
        print(f"\n🎉 MASTER DATA STRUCTURE CONFIRMED!")
        print(f"   ✅ Structured monthly data for 2025 exists")
        print(f"   ✅ Target vs Actual metrics available")
        print(f"   ✅ Pipeline and revenue metrics accessible")
    else:
        print(f"\n⚠️  MASTER DATA STRUCTURE ANALYSIS:")
        print(f"   • System uses calculated analytics rather than pre-stored master data")
        print(f"   • Data is dynamically generated from sales records")
        print(f"   • Monthly targets are configured in code, not stored as master data")
    
    return 0 if passed_tests >= 3 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)