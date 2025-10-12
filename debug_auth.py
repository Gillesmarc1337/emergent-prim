#!/usr/bin/env python3
"""
Debug authentication issue
"""

import requests
import json

BASE_URL = "https://pipeline-view.preview.emergentagent.com/api"

def debug_auth_flow():
    print("🔍 Debugging authentication flow...")
    
    # Step 1: Demo login
    print("\n1. Demo login")
    response = requests.post(f"{BASE_URL}/auth/demo-login")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        session_token = data.get('session_token')
        print(f"Session token: {session_token}")
        
        # Get cookies from response
        cookies = response.cookies
        print(f"Cookies from response: {dict(cookies)}")
        
        # Step 2: Test auth/me with session token
        print("\n2. Test auth/me with session token")
        cookies_dict = {'session_token': session_token}
        response2 = requests.get(f"{BASE_URL}/auth/me", cookies=cookies_dict)
        print(f"Status: {response2.status_code}")
        print(f"Response: {response2.text}")
        
        # Step 3: Logout
        print("\n3. Logout")
        response3 = requests.post(f"{BASE_URL}/auth/logout", cookies=cookies_dict)
        print(f"Status: {response3.status_code}")
        print(f"Response: {response3.text}")
        print(f"Cookies after logout: {dict(response3.cookies)}")
        
        # Step 4: Test auth/me after logout
        print("\n4. Test auth/me after logout")
        response4 = requests.get(f"{BASE_URL}/auth/me", cookies=cookies_dict)
        print(f"Status: {response4.status_code}")
        print(f"Response: {response4.text}")
        
        # Step 5: Test auth/me with no cookies
        print("\n5. Test auth/me with no cookies")
        response5 = requests.get(f"{BASE_URL}/auth/me")
        print(f"Status: {response5.status_code}")
        print(f"Response: {response5.text}")
        
    else:
        print(f"Demo login failed: {response.text}")

if __name__ == "__main__":
    debug_auth_flow()