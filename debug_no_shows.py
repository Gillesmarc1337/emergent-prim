#!/usr/bin/env python3
"""
Debug No Shows issue in /api/analytics/yearly?year=2025 endpoint
Specifically checking show_noshow column data and filtering
"""

import requests
import json
import sys
from datetime import datetime

# Use the production URL from frontend/.env
BASE_URL = "https://pipeline-insights-1.preview.emergentagent.com/api"

def debug_yearly_analytics_no_shows():
    """Debug the No Shows issue in yearly analytics endpoint"""
    print(f"\n{'='*80}")
    print(f"🔍 DEBUGGING NO SHOWS ISSUE IN /api/analytics/yearly?year=2025")
    print(f"{'='*80}")
    
    # Test the yearly analytics endpoint
    endpoint = "/analytics/yearly?year=2025"
    print(f"\n📡 Testing endpoint: {BASE_URL}{endpoint}")
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        data = response.json()
        print(f"✅ Response received successfully")
        
        # Check if dashboard_blocks exists
        if 'dashboard_blocks' not in data:
            print(f"❌ dashboard_blocks not found in response")
            return False
            
        dashboard_blocks = data['dashboard_blocks']
        print(f"✅ dashboard_blocks found")
        
        # Focus on block_1_meetings
        if 'block_1_meetings' not in dashboard_blocks:
            print(f"❌ block_1_meetings not found in dashboard_blocks")
            return False
            
        block_1 = dashboard_blocks['block_1_meetings']
        print(f"✅ block_1_meetings found")
        
        # Print all block_1_meetings data for analysis
        print(f"\n📊 BLOCK_1_MEETINGS COMPLETE DATA:")
        print(f"{'='*50}")
        for key, value in block_1.items():
            print(f"{key}: {value}")
        
        # Specifically check show/no-show data
        print(f"\n🎯 SHOW/NO-SHOW ANALYSIS:")
        print(f"{'='*40}")
        
        show_actual = block_1.get('show_actual', 'NOT FOUND')
        no_show_actual = block_1.get('no_show_actual', 'NOT FOUND')
        
        print(f"show_actual: {show_actual}")
        print(f"no_show_actual: {no_show_actual}")
        
        # Check debug_info if available
        if 'debug_info' in block_1:
            debug_info = block_1['debug_info']
            print(f"\n🔧 DEBUG_INFO:")
            print(f"{'='*30}")
            for key, value in debug_info.items():
                print(f"{key}: {value}")
        else:
            print(f"\n⚠️  No debug_info found in block_1_meetings")
        
        # Check if there are any issues with the data
        print(f"\n🔍 DATA VALIDATION:")
        print(f"{'='*30}")
        
        # Validate show/no-show numbers
        if isinstance(show_actual, (int, float)) and isinstance(no_show_actual, (int, float)):
            total_show_noshow = show_actual + no_show_actual
            total_meetings = block_1.get('total_actual', 0)
            
            print(f"Total meetings: {total_meetings}")
            print(f"Show + No Show: {total_show_noshow}")
            print(f"Difference: {total_meetings - total_show_noshow}")
            
            if total_show_noshow <= total_meetings:
                print(f"✅ Show/No-Show numbers are consistent with total meetings")
            else:
                print(f"❌ Show/No-Show numbers exceed total meetings - data issue!")
                
            # Check if no_show_actual is 0 (which might be the issue)
            if no_show_actual == 0:
                print(f"⚠️  WARNING: no_show_actual is 0 - this might be the issue!")
                print(f"   This could mean:")
                print(f"   1. There are genuinely no No Shows in July-Dec 2025")
                print(f"   2. The show_noshow column doesn't contain 'No Show' values")
                print(f"   3. The filtering logic is incorrect")
                print(f"   4. The column name is wrong (should be 'show_noshow' not 'show_nowshow')")
            else:
                print(f"✅ no_show_actual has a value: {no_show_actual}")
        else:
            print(f"❌ show_actual or no_show_actual are not numeric!")
            print(f"show_actual type: {type(show_actual)}")
            print(f"no_show_actual type: {type(no_show_actual)}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_data_status_for_show_noshow():
    """Test data status to understand the show_noshow column"""
    print(f"\n{'='*80}")
    print(f"📊 CHECKING DATA STATUS FOR SHOW_NOSHOW COLUMN")
    print(f"{'='*80}")
    
    endpoint = "/data/status"
    print(f"\n📡 Testing endpoint: {BASE_URL}{endpoint}")
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Data status response received")
            
            # Print all available data
            print(f"\n📋 DATA STATUS DETAILS:")
            print(f"{'='*40}")
            for key, value in data.items():
                print(f"{key}: {value}")
                
            return True
        else:
            print(f"❌ Data status request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking data status: {str(e)}")
        return False

def test_with_curl_command():
    """Show the curl command for manual testing"""
    print(f"\n{'='*80}")
    print(f"🔧 CURL COMMAND FOR MANUAL TESTING")
    print(f"{'='*80}")
    
    curl_command = f'curl -X GET "{BASE_URL}/analytics/yearly?year=2025" -H "Accept: application/json"'
    print(f"\nCopy and run this command to test manually:")
    print(f"{'='*50}")
    print(f"{curl_command}")
    print(f"{'='*50}")
    
    # Also provide a command to check just the dashboard blocks
    print(f"\nTo extract just the dashboard_blocks.block_1_meetings data:")
    print(f"{'='*60}")
    jq_command = f'{curl_command} | jq ".dashboard_blocks.block_1_meetings"'
    print(f"{jq_command}")
    print(f"{'='*60}")
    
    # Command to check debug_info specifically
    print(f"\nTo extract just the debug_info:")
    print(f"{'='*40}")
    debug_command = f'{curl_command} | jq ".dashboard_blocks.block_1_meetings.debug_info"'
    print(f"{debug_command}")
    print(f"{'='*40}")

def main():
    """Main debugging function"""
    print(f"🚀 Starting No Shows Debug for Sales Analytics Dashboard")
    print(f"Base URL: {BASE_URL}")
    print(f"Debug Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Check data status
    print(f"\n🔍 Step 1: Checking data availability...")
    data_status_ok = test_data_status_for_show_noshow()
    
    # Test 2: Debug the yearly analytics endpoint
    print(f"\n🔍 Step 2: Debugging yearly analytics endpoint...")
    yearly_debug_ok = debug_yearly_analytics_no_shows()
    
    # Test 3: Provide curl commands for manual testing
    print(f"\n🔍 Step 3: Providing manual testing commands...")
    test_with_curl_command()
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📋 DEBUG SUMMARY")
    print(f"{'='*80}")
    
    print(f"Data Status Check: {'✅ OK' if data_status_ok else '❌ FAILED'}")
    print(f"Yearly Analytics Debug: {'✅ OK' if yearly_debug_ok else '❌ FAILED'}")
    
    if yearly_debug_ok:
        print(f"\n🎯 KEY FINDINGS TO INVESTIGATE:")
        print(f"1. Check if show_noshow column contains 'No Show' or 'NoShow' or other format")
        print(f"2. Verify the filtering logic in the backend code")
        print(f"3. Confirm there are actually meetings with No Show status in July-Dec 2025")
        print(f"4. Check if the column name is correct (show_noshow vs show_nowshow)")
        
        print(f"\n🔧 NEXT STEPS:")
        print(f"1. Run the curl command above to see raw response")
        print(f"2. Check the backend logs for any errors")
        print(f"3. Examine the raw data in MongoDB to see actual show_noshow values")
        print(f"4. Verify the date range filtering for July-December 2025")
    
    return 0 if (data_status_ok and yearly_debug_ok) else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)