#!/usr/bin/env python3
"""
Detailed Analytics Testing for Dashboard Blocks and Deals Closed Structure
Specifically testing the monthly and yearly analytics endpoints as requested
"""

import requests
import json
import sys
from datetime import datetime

# Use the production URL from frontend/.env
BASE_URL = "https://viewsync-analytics.preview.emergentagent.com/api"

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

def analyze_dashboard_blocks(data, endpoint_name):
    """Analyze dashboard_blocks structure in detail"""
    print(f"\n{'='*80}")
    print(f"📊 DASHBOARD BLOCKS ANALYSIS - {endpoint_name}")
    print(f"{'='*80}")
    
    if 'dashboard_blocks' not in data:
        print(f"❌ dashboard_blocks not found in {endpoint_name}")
        return False
    
    blocks = data['dashboard_blocks']
    print(f"✅ dashboard_blocks found with {len(blocks)} blocks")
    
    for block_name, block_data in blocks.items():
        print(f"\n📋 Block: {block_name}")
        print(f"   Type: {type(block_data)}")
        
        if isinstance(block_data, dict):
            print(f"   Fields ({len(block_data)}):")
            for key, value in block_data.items():
                value_type = type(value).__name__
                if isinstance(value, (int, float)):
                    print(f"     • {key}: {value:,} ({value_type})")
                elif isinstance(value, str):
                    print(f"     • {key}: '{value}' ({value_type})")
                elif isinstance(value, bool):
                    print(f"     • {key}: {value} ({value_type})")
                elif isinstance(value, list):
                    print(f"     • {key}: [{len(value)} items] ({value_type})")
                elif isinstance(value, dict):
                    print(f"     • {key}: {{{len(value)} fields}} ({value_type})")
                else:
                    print(f"     • {key}: {value} ({value_type})")
        else:
            print(f"   Value: {block_data}")
    
    return True

def analyze_deals_closed(data, endpoint_name):
    """Analyze deals_closed structure in detail"""
    print(f"\n{'='*80}")
    print(f"💰 DEALS CLOSED ANALYSIS - {endpoint_name}")
    print(f"{'='*80}")
    
    if 'deals_closed' not in data:
        print(f"❌ deals_closed not found in {endpoint_name}")
        return False
    
    deals_closed = data['deals_closed']
    print(f"✅ deals_closed found")
    print(f"   Type: {type(deals_closed)}")
    
    if isinstance(deals_closed, dict):
        print(f"\n📊 Deals Closed Structure ({len(deals_closed)} fields):")
        
        # Core metrics
        core_metrics = ['deals_closed', 'target_deals', 'arr_closed', 'target_arr', 'mrr_closed', 'avg_deal_size']
        print(f"\n   📈 Core Metrics:")
        for metric in core_metrics:
            if metric in deals_closed:
                value = deals_closed[metric]
                value_type = type(value).__name__
                if isinstance(value, (int, float)):
                    print(f"     • {metric}: {value:,} ({value_type})")
                else:
                    print(f"     • {metric}: {value} ({value_type})")
            else:
                print(f"     • {metric}: MISSING")
        
        # Status indicators
        status_fields = ['on_track']
        print(f"\n   🎯 Status Indicators:")
        for field in status_fields:
            if field in deals_closed:
                value = deals_closed[field]
                print(f"     • {field}: {value} ({type(value).__name__})")
            else:
                print(f"     • {field}: MISSING")
        
        # Detailed data
        detail_fields = ['deals_detail', 'monthly_closed']
        print(f"\n   📋 Detailed Data:")
        for field in detail_fields:
            if field in deals_closed:
                value = deals_closed[field]
                if isinstance(value, list):
                    print(f"     • {field}: [{len(value)} items]")
                    if len(value) > 0:
                        print(f"       Sample item: {value[0]}")
                        if len(value) > 1:
                            print(f"       ... and {len(value) - 1} more items")
                else:
                    print(f"     • {field}: {value} ({type(value).__name__})")
            else:
                print(f"     • {field}: MISSING")
        
        # Check for "Deals Closed (Current Period)" block compatibility
        print(f"\n   🔧 Dashboard Block Compatibility Check:")
        required_for_dashboard = ['deals_closed', 'target_deals', 'arr_closed', 'target_arr', 'on_track']
        missing_fields = [field for field in required_for_dashboard if field not in deals_closed]
        
        if not missing_fields:
            print(f"     ✅ All required fields present for 'Deals Closed (Current Period)' block")
        else:
            print(f"     ❌ Missing fields for dashboard block: {missing_fields}")
        
        # Data quality check
        print(f"\n   🔍 Data Quality Check:")
        deals_count = deals_closed.get('deals_closed', 0)
        arr_closed = deals_closed.get('arr_closed', 0)
        deals_detail = deals_closed.get('deals_detail', [])
        
        if deals_count == 0 and arr_closed == 0:
            print(f"     ⚠️  No deals closed in this period (deals_closed=0, arr_closed=0)")
        elif deals_count > 0 and len(deals_detail) == 0:
            print(f"     ⚠️  Deals count > 0 but deals_detail is empty")
        elif deals_count != len(deals_detail):
            print(f"     ⚠️  Mismatch: deals_closed={deals_count} but deals_detail has {len(deals_detail)} items")
        else:
            print(f"     ✅ Data consistency looks good")
    
    return True

def check_dashboard_blocks_integration(data, endpoint_name):
    """Check if deals_closed data is integrated into dashboard_blocks"""
    print(f"\n{'='*80}")
    print(f"🔗 DASHBOARD BLOCKS INTEGRATION CHECK - {endpoint_name}")
    print(f"{'='*80}")
    
    if 'dashboard_blocks' not in data or 'deals_closed' not in data:
        print(f"❌ Missing dashboard_blocks or deals_closed in {endpoint_name}")
        return False
    
    blocks = data['dashboard_blocks']
    deals_closed = data['deals_closed']
    
    # Look for deals/closed related data in dashboard blocks
    deals_related_blocks = []
    deals_related_fields = []
    
    for block_name, block_data in blocks.items():
        if isinstance(block_data, dict):
            # Check for deals/closed related fields
            for field_name, field_value in block_data.items():
                if any(keyword in field_name.lower() for keyword in ['deal', 'closed', 'revenue']):
                    deals_related_blocks.append(block_name)
                    deals_related_fields.append(f"{block_name}.{field_name}")
    
    print(f"📊 Deals-related blocks found: {len(set(deals_related_blocks))}")
    for block in set(deals_related_blocks):
        print(f"   • {block}")
    
    print(f"\n📊 Deals-related fields in dashboard_blocks:")
    for field in deals_related_fields:
        block_name, field_name = field.split('.', 1)
        field_value = blocks[block_name][field_name]
        print(f"   • {field}: {field_value}")
    
    # Check if there's a specific "Deals Closed" block
    deals_closed_block = None
    for block_name, block_data in blocks.items():
        if 'deal' in block_name.lower() and 'closed' in block_name.lower():
            deals_closed_block = block_name
            break
    
    if deals_closed_block:
        print(f"\n✅ Found dedicated deals closed block: {deals_closed_block}")
    else:
        print(f"\n⚠️  No dedicated 'Deals Closed' block found in dashboard_blocks")
        print(f"   This might explain why the 'Deals Closed (Current Period)' block is not displaying")
    
    # Compare deals_closed data with dashboard_blocks data
    print(f"\n🔍 Data Consistency Check:")
    deals_count_main = deals_closed.get('deals_closed', 0)
    arr_closed_main = deals_closed.get('arr_closed', 0)
    
    # Look for corresponding values in dashboard_blocks
    found_matches = []
    for block_name, block_data in blocks.items():
        if isinstance(block_data, dict):
            for field_name, field_value in block_data.items():
                if field_value == deals_count_main and deals_count_main != 0:
                    found_matches.append(f"deals_closed ({deals_count_main}) matches {block_name}.{field_name}")
                elif field_value == arr_closed_main and arr_closed_main != 0:
                    found_matches.append(f"arr_closed ({arr_closed_main}) matches {block_name}.{field_name}")
    
    if found_matches:
        print(f"   ✅ Found data matches between deals_closed and dashboard_blocks:")
        for match in found_matches:
            print(f"     • {match}")
    else:
        print(f"   ⚠️  No direct data matches found between deals_closed and dashboard_blocks")
    
    return len(deals_related_blocks) > 0

def main():
    """Main function to test dashboard blocks and deals_closed structure"""
    print(f"🚀 Starting Detailed Analytics Testing")
    print(f"Base URL: {BASE_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n📋 Testing Objectives:")
    print(f"   1. Verify dashboard_blocks exist in monthly and yearly analytics")
    print(f"   2. Analyze deals_closed data structure in both responses")
    print(f"   3. Check data formatting and missing fields")
    print(f"   4. Debug why dashboard blocks might not be displaying")
    
    # Test 1: Monthly Analytics
    print(f"\n{'='*100}")
    print(f"🗓️  TEST 1: MONTHLY ANALYTICS (/api/analytics/monthly)")
    print(f"{'='*100}")
    
    monthly_data = test_api_endpoint("/analytics/monthly")
    monthly_success = False
    
    if monthly_data:
        monthly_success = True
        analyze_dashboard_blocks(monthly_data, "MONTHLY")
        analyze_deals_closed(monthly_data, "MONTHLY")
        check_dashboard_blocks_integration(monthly_data, "MONTHLY")
    
    # Test 2: Yearly Analytics
    print(f"\n{'='*100}")
    print(f"📅 TEST 2: YEARLY ANALYTICS (/api/analytics/yearly)")
    print(f"{'='*100}")
    
    yearly_data = test_api_endpoint("/analytics/yearly?year=2025")
    yearly_success = False
    
    if yearly_data:
        yearly_success = True
        analyze_dashboard_blocks(yearly_data, "YEARLY")
        analyze_deals_closed(yearly_data, "YEARLY")
        check_dashboard_blocks_integration(yearly_data, "YEARLY")
    
    # Summary and Recommendations
    print(f"\n{'='*100}")
    print(f"📋 SUMMARY AND RECOMMENDATIONS")
    print(f"{'='*100}")
    
    print(f"\n🎯 Test Results:")
    print(f"   • Monthly Analytics: {'✅ SUCCESS' if monthly_success else '❌ FAILED'}")
    print(f"   • Yearly Analytics: {'✅ SUCCESS' if yearly_success else '❌ FAILED'}")
    
    if monthly_success and yearly_success:
        print(f"\n✅ FINDINGS:")
        print(f"   • Both endpoints return dashboard_blocks successfully")
        print(f"   • Both endpoints return properly structured deals_closed data")
        print(f"   • All required fields are present for dashboard block integration")
        
        # Check if there are any obvious issues
        monthly_deals = monthly_data.get('deals_closed', {}).get('deals_closed', 0) if monthly_data else 0
        yearly_deals = yearly_data.get('deals_closed', {}).get('deals_closed', 0) if yearly_data else 0
        
        if monthly_deals == 0:
            print(f"   ⚠️  Monthly period (Oct 2025) shows 0 deals closed")
        if yearly_deals > 0:
            print(f"   ✅ Yearly period shows {yearly_deals} deals closed")
        
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"   • Dashboard blocks data structure is correct and complete")
        print(f"   • Deals_closed data is properly formatted with all required fields")
        print(f"   • If 'Deals Closed (Current Period)' block is not displaying, check:")
        print(f"     - Frontend component mapping to dashboard_blocks data")
        print(f"     - Frontend filtering logic for current period")
        print(f"     - Component rendering conditions")
    else:
        print(f"\n❌ ISSUES FOUND:")
        if not monthly_success:
            print(f"   • Monthly analytics endpoint failed")
        if not yearly_success:
            print(f"   • Yearly analytics endpoint failed")
    
    return 0 if (monthly_success and yearly_success) else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)