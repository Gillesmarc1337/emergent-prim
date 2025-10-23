#!/usr/bin/env python3
"""
Test Master view targets configuration specifically
"""

import requests
import json
import sys
from datetime import datetime

# Use the production URL from frontend/.env
BASE_URL = "https://multi-tenant-sales.preview.emergentagent.com/api"

def test_api_endpoint(endpoint, method="GET", data=None, cookies=None, expected_status=200):
    """Test an API endpoint and return response"""
    try:
        print(f"\n🔍 Testing: {method} {endpoint}")
        
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", cookies=cookies, timeout=30)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, cookies=cookies, timeout=30)
        elif method == "PUT":
            response = requests.put(f"{BASE_URL}{endpoint}", json=data, cookies=cookies, timeout=30)
        elif method == "DELETE":
            response = requests.delete(f"{BASE_URL}{endpoint}", cookies=cookies, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != expected_status:
            print(f"❌ Expected status {expected_status}, got {response.status_code}")
            print(f"Response: {response.text}")
            return None, response
            
        if response.status_code in [200, 201]:
            try:
                data = response.json()
                print(f"✅ Response received successfully")
                return data, response
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response")
                print(f"Response text: {response.text}")
                return None, response
        elif response.status_code == expected_status:
            # For expected non-200 status codes (like 401), return the response
            print(f"✅ Expected status {expected_status} received")
            return None, response
        else:
            return response.text, response
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
        return None, None

def test_demo_login():
    """Test POST /api/auth/demo-login endpoint"""
    print(f"\n🔐 Demo Login")
    
    # Test demo login
    result = test_api_endpoint("/auth/demo-login", method="POST", expected_status=200)
    
    if not result or len(result) != 2:
        print(f"❌ Demo login failed - no response")
        return None, None
    
    data, response = result
    if data is None or response is None:
        print(f"❌ Demo login failed")
        return None, None
    
    # Check for session cookie
    session_cookie = None
    if response.cookies:
        session_cookie = response.cookies.get('session_token')
        if session_cookie:
            print(f"✅ Session cookie set: {session_cookie[:20]}...")
        else:
            print(f"❌ Session cookie not found in response")
            return None, None
    else:
        print(f"❌ No cookies in response")
        return None, None
    
    print(f"✅ Demo login successful: {data.get('email')} ({data.get('role')})")
    return data, session_cookie

def main():
    """Test Master view targets configuration"""
    print(f"\n{'='*80}")
    print(f"🎯 TESTING MASTER VIEW TARGETS CONFIGURATION")
    print(f"{'='*80}")
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Demo login
    print(f"\n🔄 Step 1: Demo login")
    demo_data, session_token = test_demo_login()
    
    if not demo_data or not session_token:
        print(f"❌ Demo login failed - cannot continue testing")
        return False
    
    cookies = {'session_token': session_token}
    
    # Step 2: Find Master view ID from GET /api/views
    print(f"\n🔄 Step 2: Find Master view ID")
    result = test_api_endpoint("/views", cookies=cookies, expected_status=200)
    
    master_view_id = None
    if result and len(result) == 2:
        data, response = result
        if data and isinstance(data, list):
            print(f"✅ Found {len(data)} views")
            
            # Look for Master view
            for view in data:
                view_name = view.get('name', '').lower()
                is_master = view.get('is_master', False)
                
                print(f"  - {view.get('name')} (ID: {view.get('id')}, is_master: {is_master})")
                
                if 'master' in view_name or is_master:
                    master_view_id = view.get('id')
                    print(f"✅ Found Master view: {view.get('name')} (ID: {master_view_id})")
                    break
            
            if not master_view_id:
                print(f"❌ Master view not found in views list")
                return False
        else:
            print(f"❌ Invalid views response")
            return False
    else:
        print(f"❌ Failed to get views list")
        return False
    
    # Step 3: Get Master view config: GET /api/views/{master_view_id}/config
    print(f"\n🔄 Step 3: Get Master view configuration")
    config_endpoint = f"/views/{master_view_id}/config"
    result = test_api_endpoint(config_endpoint, cookies=cookies, expected_status=200)
    
    master_config = None
    if result and len(result) == 2:
        data, response = result
        if data and isinstance(data, dict):
            master_config = data
            print(f"✅ Master view config retrieved successfully")
            print(f"  View name: {data.get('name')}")
            print(f"  Is master: {data.get('is_master', False)}")
            print(f"  Has targets: {'targets' in data}")
            
            # Show the actual targets structure
            targets = data.get('targets', {})
            if targets:
                print(f"\n📊 Current targets structure:")
                print(json.dumps(targets, indent=2))
            else:
                print(f"❌ No targets found in Master view config")
                return False
        else:
            print(f"❌ Invalid master config response")
            return False
    else:
        print(f"❌ Failed to get master view config")
        return False
    
    # Step 4: Verify all targets should be 150
    print(f"\n🔄 Step 4: Verify Master targets are set to 150")
    
    targets = master_config.get('targets', {})
    
    # Check specific targets mentioned in the review request
    expected_targets = {
        'revenue_2025.jan': 150,
        'dashboard_bottom_cards.new_pipe_created': 150,
        'meeting_generation.total_target': 150,
        'meetings_attended.meetings_scheduled': 150,
        'deals_closed_yearly.deals_target': 150
    }
    
    targets_verification = {}
    all_targets_150 = True
    
    print(f"\n📊 Checking specific targets:")
    
    # Check revenue_2025.jan
    revenue_2025 = targets.get('revenue_2025', {})
    jan_target = revenue_2025.get('jan', 'NOT FOUND')
    targets_verification['revenue_2025.jan'] = jan_target
    if jan_target == 150:
        print(f"  ✅ revenue_2025.jan = {jan_target}")
    else:
        print(f"  ❌ revenue_2025.jan = {jan_target} (expected 150)")
        all_targets_150 = False
    
    # Check dashboard_bottom_cards.new_pipe_created
    dashboard_cards = targets.get('dashboard_bottom_cards', {})
    new_pipe_target = dashboard_cards.get('new_pipe_created', 'NOT FOUND')
    targets_verification['dashboard_bottom_cards.new_pipe_created'] = new_pipe_target
    if new_pipe_target == 150:
        print(f"  ✅ dashboard_bottom_cards.new_pipe_created = {new_pipe_target}")
    else:
        print(f"  ❌ dashboard_bottom_cards.new_pipe_created = {new_pipe_target} (expected 150)")
        all_targets_150 = False
    
    # Check meeting_generation.total_target
    meeting_gen = targets.get('meeting_generation', {})
    total_target = meeting_gen.get('total_target', 'NOT FOUND')
    targets_verification['meeting_generation.total_target'] = total_target
    if total_target == 150:
        print(f"  ✅ meeting_generation.total_target = {total_target}")
    else:
        print(f"  ❌ meeting_generation.total_target = {total_target} (expected 150)")
        all_targets_150 = False
    
    # Check meetings_attended.meetings_scheduled
    meetings_attended = targets.get('meetings_attended', {})
    meetings_scheduled = meetings_attended.get('meetings_scheduled', 'NOT FOUND')
    targets_verification['meetings_attended.meetings_scheduled'] = meetings_scheduled
    if meetings_scheduled == 150:
        print(f"  ✅ meetings_attended.meetings_scheduled = {meetings_scheduled}")
    else:
        print(f"  ❌ meetings_attended.meetings_scheduled = {meetings_scheduled} (expected 150)")
        all_targets_150 = False
    
    # Check deals_closed_yearly.deals_target
    deals_closed = targets.get('deals_closed_yearly', {})
    deals_target = deals_closed.get('deals_target', 'NOT FOUND')
    targets_verification['deals_closed_yearly.deals_target'] = deals_target
    if deals_target == 150:
        print(f"  ✅ deals_closed_yearly.deals_target = {deals_target}")
    else:
        print(f"  ❌ deals_closed_yearly.deals_target = {deals_target} (expected 150)")
        all_targets_150 = False
    
    # Step 5: Verify Analytics uses manual targets (150) for Master view
    print(f"\n🔄 Step 5: Verify Analytics uses manual targets for Master view")
    analytics_endpoint = f"/analytics/monthly?view_id={master_view_id}"
    result = test_api_endpoint(analytics_endpoint, cookies=cookies, expected_status=200)
    
    if result and len(result) == 2:
        data, response = result
        if data and isinstance(data, dict):
            print(f"✅ Master view analytics retrieved successfully")
            
            # Look for targets in the analytics response
            print(f"\n📊 Checking analytics targets:")
            
            # Check dashboard_blocks for targets
            if 'dashboard_blocks' in data:
                blocks = data['dashboard_blocks']
                
                # Look for any target values that should be 150
                target_fields_found = []
                for block_name, block_data in blocks.items():
                    if isinstance(block_data, dict):
                        for field_name, field_value in block_data.items():
                            if 'target' in field_name.lower() and isinstance(field_value, (int, float)):
                                target_fields_found.append(f"{block_name}.{field_name}: {field_value}")
                                
                                # Check if this target is using manual value (150) vs auto-aggregated
                                if field_value == 150:
                                    print(f"  ✅ {block_name}.{field_name} = {field_value} (manual target)")
                                else:
                                    print(f"  ⚠️  {block_name}.{field_name} = {field_value} (may be auto-aggregated)")
                
                if target_fields_found:
                    print(f"\n📋 Found {len(target_fields_found)} target fields in analytics")
                else:
                    print(f"❌ No target fields found in analytics dashboard_blocks")
            else:
                print(f"❌ No dashboard_blocks found in analytics response")
        else:
            print(f"❌ Invalid analytics response")
    else:
        print(f"❌ Failed to get Master view analytics")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📋 MASTER VIEW TARGETS CONFIGURATION TEST SUMMARY")
    print(f"{'='*80}")
    
    print(f"\n🔍 Key Findings:")
    print(f"  📍 Master view ID: {master_view_id}")
    print(f"  🎯 Manual targets set to 150: {'✅ YES' if all_targets_150 else '❌ NO'}")
    
    if all_targets_150:
        print(f"\n🎉 SUCCESS: All Master view targets are correctly set to 150!")
    else:
        print(f"\n❌ ISSUES: Some Master view targets are not set to 150")
        print(f"📋 Current target values:")
        for target_path, value in targets_verification.items():
            print(f"  {target_path}: {value}")
    
    print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return all_targets_150

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)