"""
Authentication helpers and utilities for Emergent OAuth
"""
import os
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, Request, Cookie, Depends
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'sales_analytics')]

# Role constants
ROLE_VIEWER = "viewer"
ROLE_SUPER_ADMIN = "super_admin"

# Authorized users
AUTHORIZED_USERS = {
    "asher@primelis.com": ROLE_SUPER_ADMIN,  # Super admin
    "remi@primelis.com": ROLE_SUPER_ADMIN,
    "francois@primelis.com": ROLE_SUPER_ADMIN,  # Super admin
    "demo@primelis.com": ROLE_VIEWER,  # Demo mode user
    # New multi-view users
    "oren@primelis.com": ROLE_VIEWER,  # Signal view
    "maxime.toubia@primelis.com": ROLE_VIEWER,  # Full Funnel view
    "coralie.truffy@primelis.com": ROLE_VIEWER,  # Market view
    "philippe@primelis.com": ROLE_SUPER_ADMIN  # Master view + all views access
}

async def get_session_data_from_emergent(session_id: str):
    """
    Call Emergent API to get session data
    """
    try:
        response = requests.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            raise HTTPException(status_code=401, detail="Invalid session ID")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error contacting auth service: {str(e)}")

async def get_or_create_user(email: str, name: str, picture: Optional[str] = None):
    """
    Get existing user or create new one if authorized
    """
    # First, check if user exists in database
    existing_user = await db.users.find_one({"email": email})
    
    if existing_user:
        # User exists in database - they are authorized
        # Update last_login
        await db.users.update_one(
            {"email": email},
            {"$set": {"last_login": datetime.now(timezone.utc)}}
        )
        return existing_user
    
    # User doesn't exist in database, check hardcoded list for backward compatibility
    if email not in AUTHORIZED_USERS:
        raise HTTPException(status_code=403, detail="User not authorized. Please contact your administrator to get access.")
    
    # Create new user from hardcoded list (backward compatibility)
    user_data = {
        "id": f"user-{email.split('@')[0]}-{int(datetime.now(timezone.utc).timestamp())}",
        "email": email,
        "name": name,
        "picture": picture,
        "role": AUTHORIZED_USERS[email],
        "created_at": datetime.now(timezone.utc),
        "last_login": datetime.now(timezone.utc)
    }
    
    await db.users.insert_one(user_data)
    return user_data

async def create_session(user_id: str, session_token: str, expires_hours: int = None):
    """
    Create a new session in database
    expires_hours: Custom expiration in hours (default: 7 days for normal, 24 hours for demo)
    """
    if expires_hours is None:
        expires_hours = 7 * 24  # 7 days default
    
    session_data = {
        "id": f"session-{int(datetime.now(timezone.utc).timestamp())}",
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=expires_hours),
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.user_sessions.insert_one(session_data)
    return session_data

async def create_demo_user():
    """
    Create or get demo user for development/testing
    """
    demo_email = "demo@primelis.com"
    
    # Check if demo user exists
    existing_user = await db.users.find_one({"email": demo_email})
    
    if existing_user:
        return existing_user
    
    # Create demo user
    user_data = {
        "id": f"user-demo-{int(datetime.now(timezone.utc).timestamp())}",
        "email": demo_email,
        "name": "Demo User",
        "picture": None,
        "role": ROLE_VIEWER,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.users.insert_one(user_data)
    return user_data

async def get_user_from_session(session_token: str):
    """
    Get user from session token
    """
    if not session_token:
        return None
    
    # Find session
    session = await db.user_sessions.find_one({"session_token": session_token})
    
    if not session:
        return None
    
    # Check if expired
    expires_at = session.get("expires_at")
    if expires_at:
        # Handle both timezone-aware and naive datetimes
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            await db.user_sessions.delete_one({"session_token": session_token})
            return None
    
    # Get user
    user = await db.users.find_one({"id": session["user_id"]})
    return user

async def get_current_user(
    request: Request,
    session_token: Optional[str] = Cookie(None)
):
    """
    Dependency to get current authenticated user
    Checks cookie first, then Authorization header
    """
    # Try cookie first
    token = session_token
    
    # If no cookie, try Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = await get_user_from_session(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return user

async def require_super_admin(user: dict = Depends(get_current_user)):
    """
    Dependency to require super admin role
    """
    if user.get("role") != ROLE_SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin access required")
    return user

async def delete_session(session_token: str):
    """
    Delete a session (logout)
    """
    await db.user_sessions.delete_one({"session_token": session_token})
