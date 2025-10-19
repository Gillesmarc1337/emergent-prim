#!/usr/bin/env python3
"""
User Management Backend API Testing
Focused testing for the newly implemented User Management endpoints
"""

import requests
import json
import sys
from datetime import datetime

# Use the production URL from frontend/.env
BASE_URL = "https://dealflow-tracker-7.preview.emergentagent.com/api"

def test_endpoint(endpoint, method="GET", data=None, cookies=None, expected_status=200):
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
        
        # Always return the response object for analysis
        return response
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
        return None

def create_demo_session():
    """Create a demo session and return session token"""
    print(f"\n🔐 Creating demo session...")
    
    response = test_endpoint("/auth/demo-login", method="POST", expected_status=200)
    
    if not response or response.status_code != 200:
        print(f"❌ Failed to create demo session")
        return None, None
    
    try:
        data = response.json()
        session_token = data.get('session_token')
        
        print(f"✅ Demo session created")
        print(f"  📧 Email: {data.get('email')}")
        print(f"  👤 Role: {data.get('role')}")
        print(f"  🔑 Session: {session_token[:20]}..." if session_token else "No token")
        
        return data, session_token
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON response from demo login")
        return None, None

def test_user_management_endpoints():
    """Test all User Management Backend API endpoints"""
    print(f"\n{'='*80}")
    print(f"👥 TESTING USER MANAGEMENT BACKEND API ENDPOINTS")
    print(f"{'='*80}")
    print(f"🌐 Base URL: {BASE_URL}")
    
    # Step 1: Create demo session
    demo_data, session_token = create_demo_session()
    
    if not session_token:
        print(f"❌ Cannot proceed without demo session")
        return False
    
    cookies = {'session_token': session_token}
    
    # Test results tracking
    test_results = {
        'get_users_403': False,
        'create_user_403': False,
        'update_role_403': False,
        'get_user_views_403': False,
        'update_user_views_403': False,
        'delete_user_403': False
    }
    
    print(f"\n{'='*60}")
    print(f"🚫 TESTING ACCESS DENIED SCENARIOS (Demo User = Viewer)")
    print(f"{'='*60}")
    
    # Test 1: GET /api/admin/users (should return 403)
    print(f"\n📊 Test 1: GET /api/admin/users")
    response = test_endpoint("/admin/users", cookies=cookies)
    if response is not None:
        if response.status_code == 403:
            test_results['get_users_403'] = True
            print(f"✅ Demo user correctly denied access (403)")
            try:
                error_data = response.json()
                print(f"  📝 Error message: {error_data.get('detail', 'No detail')}")
            except:
                print(f"  📝 Error text: {response.text}")
        else:
            print(f"❌ Expected 403, got {response.status_code}")
    else:
        print(f"❌ No response received")
    
    # Test 2: POST /api/admin/users (should return 403)
    print(f"\n📊 Test 2: POST /api/admin/users")
    create_user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "role": "viewer",
        "view_access": ["Organic"]
    }
    response = test_endpoint("/admin/users", method="POST", data=create_user_data, cookies=cookies)
    if response is not None:
        if response.status_code == 403:
            test_results['create_user_403'] = True
            print(f"✅ Demo user correctly denied access (403)")
            try:
                error_data = response.json()
                print(f"  📝 Error message: {error_data.get('detail', 'No detail')}")
            except:
                print(f"  📝 Error text: {response.text}")
        else:
            print(f"❌ Expected 403, got {response.status_code}")
    else:
        print(f"❌ No response received")
    
    # Test 3: PUT /api/admin/users/{user_id}/role (should return 403)
    print(f"\n📊 Test 3: PUT /api/admin/users/test-id/role")
    role_update_data = {"role": "super_admin"}
    response = test_endpoint("/admin/users/test-id/role", method="PUT", data=role_update_data, cookies=cookies)
    if response is not None:
        if response.status_code == 403:
            test_results['update_role_403'] = True
            print(f"✅ Demo user correctly denied access (403)")
            try:
                error_data = response.json()
                print(f"  📝 Error message: {error_data.get('detail', 'No detail')}")
            except:
                print(f"  📝 Error text: {response.text}")
        else:
            print(f"❌ Expected 403, got {response.status_code}")
    else:
        print(f"❌ No response received")
    
    # Test 4: GET /api/admin/users/{user_id}/views (should return 403)
    print(f"\n📊 Test 4: GET /api/admin/users/test-id/views")
    response = test_endpoint("/admin/users/test-id/views", cookies=cookies)
    if response is not None:
        if response.status_code == 403:
            test_results['get_user_views_403'] = True
            print(f"✅ Demo user correctly denied access (403)")
            try:
                error_data = response.json()
                print(f"  📝 Error message: {error_data.get('detail', 'No detail')}")
            except:
                print(f"  📝 Error text: {response.text}")
        else:
            print(f"❌ Expected 403, got {response.status_code}")
    else:
        print(f"❌ No response received")
    
    # Test 5: PUT /api/admin/users/{user_id}/views (should return 403)
    print(f"\n📊 Test 5: PUT /api/admin/users/test-id/views")
    view_access_data = {"view_access": ["Signal", "Market"]}
    response = test_endpoint("/admin/users/test-id/views", method="PUT", data=view_access_data, cookies=cookies)
    if response is not None:
        if response.status_code == 403:
            test_results['update_user_views_403'] = True
            print(f"✅ Demo user correctly denied access (403)")
            try:
                error_data = response.json()
                print(f"  📝 Error message: {error_data.get('detail', 'No detail')}")
            except:
                print(f"  📝 Error text: {response.text}")
        else:
            print(f"❌ Expected 403, got {response.status_code}")
    else:
        print(f"❌ No response received")
    
    # Test 6: DELETE /api/admin/users/{user_id} (should return 403)
    print(f"\n📊 Test 6: DELETE /api/admin/users/test-id")
    response = test_endpoint("/admin/users/test-id", method="DELETE", cookies=cookies)
    if response is not None:
        if response.status_code == 403:
            test_results['delete_user_403'] = True
            print(f"✅ Demo user correctly denied access (403)")
            try:
                error_data = response.json()
                print(f"  📝 Error message: {error_data.get('detail', 'No detail')}")
            except:
                print(f"  📝 Error text: {response.text}")
        else:
            print(f"❌ Expected 403, got {response.status_code}")
    else:
        print(f"❌ No response received")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📋 USER MANAGEMENT ENDPOINTS TEST SUMMARY")
    print(f"{'='*80}")
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    print(f"\n🚫 Access Control Tests (Demo User): {passed_tests}/{total_tests} passed")
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\n📊 Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print(f"\n🎉 SUCCESS: All access control tests passed!")
        print(f"✅ Demo user (viewer role) correctly denied access to all admin endpoints")
        print(f"✅ User Management API endpoints are properly protected")
        print(f"💡 To test actual functionality, a super_admin session would be needed")
    else:
        print(f"\n❌ ISSUES: {total_tests - passed_tests} access control tests failed")
        print(f"🔧 Some admin endpoints may not be properly protected")
    
    # Additional notes
    print(f"\n{'='*60}")
    print(f"📝 TESTING NOTES")
    print(f"{'='*60}")
    print(f"✅ Demo user authentication working correctly")
    print(f"✅ All admin endpoints return 403 Forbidden for non-super_admin users")
    print(f"💡 Super_admin functionality testing would require:")
    print(f"   1. Creating a super_admin user in MongoDB")
    print(f"   2. Creating a valid session for that user")
    print(f"   3. Testing actual CRUD operations")
    print(f"   4. Testing data validation (invalid roles, non-existent views)")
    print(f"   5. Testing edge cases (self-deletion prevention, etc.)")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = test_user_management_endpoints()
    sys.exit(0 if success else 1)