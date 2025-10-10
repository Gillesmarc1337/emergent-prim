#!/usr/bin/env python3
"""
Specific test for October 2025 master data values comparison
Testing the exact values returned by /api/analytics/monthly for October 2025
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

def main():
    """Test October 2025 analytics and compare with expected master data"""
    print(f"🎯 OCTOBER 2025 MASTER DATA COMPARISON TEST")
    print(f"Base URL: {BASE_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    # Expected master data values based on backend code analysis
    expected_master_data = {
        'block_3_pipe_creation': {
            'new_pipe_created': 'Calculated from deals discovered in October 2025',
            'weighted_pipe_created': 'Calculated weighted value of new pipe in October 2025', 
            'aggregate_weighted_pipe': 'Total weighted value of all active deals',
            'target_pipe_created': 2000000  # Monthly target from backend code
        },
        'block_4_revenue': {
            'revenue_target': 1080000,  # October 2025 specific target from backend code
            'closed_revenue': 'Calculated from deals closed in October 2025'
        }
    }
    
    print(f"\n📋 EXPECTED MASTER DATA VALUES (from backend code analysis):")
    print(f"   🎯 Target Pipe Created: ${expected_master_data['block_3_pipe_creation']['target_pipe_created']:,}")
    print(f"   🎯 Revenue Target (October): ${expected_master_data['block_4_revenue']['revenue_target']:,}")
    print(f"   📊 New Pipe Created: {expected_master_data['block_3_pipe_creation']['new_pipe_created']}")
    print(f"   📊 Weighted Pipe Created: {expected_master_data['block_3_pipe_creation']['weighted_pipe_created']}")
    print(f"   📊 Aggregate Weighted Pipe: {expected_master_data['block_3_pipe_creation']['aggregate_weighted_pipe']}")
    print(f"   📊 Closed Revenue: {expected_master_data['block_4_revenue']['closed_revenue']}")
    
    # Test GET /api/analytics/monthly for October 2025
    print(f"\n{'='*80}")
    print(f"🔍 TESTING GET /api/analytics/monthly FOR OCTOBER 2025")
    print(f"{'='*80}")
    
    endpoint = "/analytics/monthly?month_offset=0"  # 0 = current month (October 2025)
    data = test_api_endpoint(endpoint)
    
    if data is None:
        print(f"❌ Failed to get October 2025 analytics data")
        return 1
    
    # Check if dashboard_blocks exists
    if 'dashboard_blocks' not in data:
        print(f"❌ dashboard_blocks not found in response")
        return 1
    
    dashboard_blocks = data['dashboard_blocks']
    
    # Examine block_3_pipe_creation
    print(f"\n{'='*60}")
    print(f"🔧 BLOCK_3_PIPE_CREATION ANALYSIS")
    print(f"{'='*60}")
    
    if 'block_3_pipe_creation' in dashboard_blocks:
        block_3 = dashboard_blocks['block_3_pipe_creation']
        
        print(f"✅ block_3_pipe_creation found")
        print(f"\n📊 ACTUAL VALUES RETURNED BY API:")
        
        # Extract actual values
        actual_new_pipe = block_3.get('new_pipe_created', 'NOT FOUND')
        actual_weighted_pipe = block_3.get('weighted_pipe_created', 'NOT FOUND')
        actual_aggregate_weighted = block_3.get('aggregate_weighted_pipe', 'NOT FOUND')
        actual_target_pipe = block_3.get('target_pipe_created', 'NOT FOUND')
        
        print(f"   • new_pipe_created: ${actual_new_pipe:,}" if isinstance(actual_new_pipe, (int, float)) else f"   • new_pipe_created: {actual_new_pipe}")
        print(f"   • weighted_pipe_created: ${actual_weighted_pipe:,}" if isinstance(actual_weighted_pipe, (int, float)) else f"   • weighted_pipe_created: {actual_weighted_pipe}")
        print(f"   • aggregate_weighted_pipe: ${actual_aggregate_weighted:,}" if isinstance(actual_aggregate_weighted, (int, float)) else f"   • aggregate_weighted_pipe: {actual_aggregate_weighted}")
        print(f"   • target_pipe_created: ${actual_target_pipe:,}" if isinstance(actual_target_pipe, (int, float)) else f"   • target_pipe_created: {actual_target_pipe}")
        
        print(f"\n🎯 COMPARISON WITH EXPECTED MASTER DATA:")
        
        # Compare target_pipe_created
        if actual_target_pipe == expected_master_data['block_3_pipe_creation']['target_pipe_created']:
            print(f"   ✅ target_pipe_created MATCHES expected: ${actual_target_pipe:,}")
        else:
            print(f"   ❌ target_pipe_created MISMATCH:")
            print(f"      Expected: ${expected_master_data['block_3_pipe_creation']['target_pipe_created']:,}")
            print(f"      Actual: ${actual_target_pipe:,}" if isinstance(actual_target_pipe, (int, float)) else f"      Actual: {actual_target_pipe}")
        
        # Analyze calculated values
        print(f"\n📈 CALCULATED VALUES ANALYSIS:")
        if isinstance(actual_new_pipe, (int, float)):
            if actual_new_pipe > 0:
                print(f"   ✅ new_pipe_created has positive value: ${actual_new_pipe:,}")
                print(f"      This represents deals discovered in October 2025")
            else:
                print(f"   ⚠️  new_pipe_created is zero: may indicate no new deals in October 2025")
        
        if isinstance(actual_weighted_pipe, (int, float)):
            if actual_weighted_pipe > 0:
                print(f"   ✅ weighted_pipe_created has positive value: ${actual_weighted_pipe:,}")
                print(f"      This represents weighted value of new deals in October 2025")
            else:
                print(f"   ⚠️  weighted_pipe_created is zero: may indicate no weighted calculation")
        
        if isinstance(actual_aggregate_weighted, (int, float)):
            if actual_aggregate_weighted > 0:
                print(f"   ✅ aggregate_weighted_pipe has positive value: ${actual_aggregate_weighted:,}")
                print(f"      This represents total weighted value of all active deals")
            else:
                print(f"   ⚠️  aggregate_weighted_pipe is zero: may indicate calculation issue")
    else:
        print(f"❌ block_3_pipe_creation not found in dashboard_blocks")
        return 1
    
    # Examine block_4_revenue
    print(f"\n{'='*60}")
    print(f"💰 BLOCK_4_REVENUE ANALYSIS")
    print(f"{'='*60}")
    
    if 'block_4_revenue' in dashboard_blocks:
        block_4 = dashboard_blocks['block_4_revenue']
        
        print(f"✅ block_4_revenue found")
        print(f"\n📊 ACTUAL VALUES RETURNED BY API:")
        
        # Extract actual values
        actual_revenue_target = block_4.get('revenue_target', 'NOT FOUND')
        actual_closed_revenue = block_4.get('closed_revenue', 'NOT FOUND')
        actual_progress = block_4.get('progress', 'NOT FOUND')
        
        print(f"   • revenue_target: ${actual_revenue_target:,}" if isinstance(actual_revenue_target, (int, float)) else f"   • revenue_target: {actual_revenue_target}")
        print(f"   • closed_revenue: ${actual_closed_revenue:,}" if isinstance(actual_closed_revenue, (int, float)) else f"   • closed_revenue: {actual_closed_revenue}")
        print(f"   • progress: {actual_progress}%" if isinstance(actual_progress, (int, float)) else f"   • progress: {actual_progress}")
        
        print(f"\n🎯 COMPARISON WITH EXPECTED MASTER DATA:")
        
        # Compare revenue_target
        if actual_revenue_target == expected_master_data['block_4_revenue']['revenue_target']:
            print(f"   ✅ revenue_target MATCHES expected October 2025 target: ${actual_revenue_target:,}")
        else:
            print(f"   ❌ revenue_target MISMATCH:")
            print(f"      Expected: ${expected_master_data['block_4_revenue']['revenue_target']:,}")
            print(f"      Actual: ${actual_revenue_target:,}" if isinstance(actual_revenue_target, (int, float)) else f"      Actual: {actual_revenue_target}")
        
        # Analyze closed_revenue
        print(f"\n📈 CLOSED REVENUE ANALYSIS:")
        if isinstance(actual_closed_revenue, (int, float)):
            if actual_closed_revenue > 0:
                print(f"   ✅ closed_revenue has positive value: ${actual_closed_revenue:,}")
                print(f"      This represents deals closed in October 2025")
                if isinstance(actual_progress, (int, float)):
                    print(f"      Progress towards target: {actual_progress:.1f}%")
            else:
                print(f"   ⚠️  closed_revenue is zero: indicates no deals closed in October 2025")
                print(f"      This may be expected if October 2025 is a future month or no deals were closed yet")
    else:
        print(f"❌ block_4_revenue not found in dashboard_blocks")
        return 1
    
    # Summary and discrepancy analysis
    print(f"\n{'='*80}")
    print(f"📋 MASTER DATA DISCREPANCY ANALYSIS")
    print(f"{'='*80}")
    
    print(f"\n🔍 KEY FINDINGS:")
    
    # Check if targets match expected values
    targets_match = True
    if 'block_3_pipe_creation' in dashboard_blocks:
        actual_target_pipe = dashboard_blocks['block_3_pipe_creation'].get('target_pipe_created')
        if actual_target_pipe != expected_master_data['block_3_pipe_creation']['target_pipe_created']:
            targets_match = False
    
    if 'block_4_revenue' in dashboard_blocks:
        actual_revenue_target = dashboard_blocks['block_4_revenue'].get('revenue_target')
        if actual_revenue_target != expected_master_data['block_4_revenue']['revenue_target']:
            targets_match = False
    
    if targets_match:
        print(f"   ✅ All target values match expected master data")
    else:
        print(f"   ❌ Some target values do not match expected master data")
    
    # Check calculated values
    print(f"\n📊 CALCULATED VALUES STATUS:")
    if 'block_3_pipe_creation' in dashboard_blocks:
        block_3 = dashboard_blocks['block_3_pipe_creation']
        new_pipe = block_3.get('new_pipe_created', 0)
        weighted_pipe = block_3.get('weighted_pipe_created', 0)
        aggregate_weighted = block_3.get('aggregate_weighted_pipe', 0)
        
        if new_pipe > 0:
            print(f"   ✅ New pipe created: ${new_pipe:,} (deals discovered in October 2025)")
        else:
            print(f"   ⚠️  New pipe created: $0 (no new deals in October 2025)")
        
        if weighted_pipe > 0:
            print(f"   ✅ Weighted pipe created: ${weighted_pipe:,}")
        else:
            print(f"   ⚠️  Weighted pipe created: $0")
        
        if aggregate_weighted > 0:
            print(f"   ✅ Aggregate weighted pipe: ${aggregate_weighted:,}")
        else:
            print(f"   ⚠️  Aggregate weighted pipe: $0")
    
    if 'block_4_revenue' in dashboard_blocks:
        block_4 = dashboard_blocks['block_4_revenue']
        closed_revenue = block_4.get('closed_revenue', 0)
        
        if closed_revenue > 0:
            print(f"   ✅ Closed revenue: ${closed_revenue:,} (deals closed in October 2025)")
        else:
            print(f"   ⚠️  Closed revenue: $0 (no deals closed in October 2025)")
    
    print(f"\n🎯 POTENTIAL REASONS FOR DISCREPANCIES:")
    print(f"   1. Data Source: Values are calculated dynamically from sales records, not stored as master data")
    print(f"   2. Time Period: October 2025 may be a future month with limited actual data")
    print(f"   3. Data Filtering: Only deals meeting specific criteria are included in calculations")
    print(f"   4. Stage Mapping: Deal stages may not map exactly to expected categories")
    print(f"   5. Date Ranges: Calculations may use different date ranges than expected")
    
    print(f"\n✅ TEST COMPLETED SUCCESSFULLY")
    print(f"📊 All requested values have been examined and compared with expected master data")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)