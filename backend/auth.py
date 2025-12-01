"""
Authentication helpers and utilities for Google OAuth
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, Request, Cookie, Depends
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import logging
from database import get_database

# MongoDB connection - use shared database instance
db = get_database()

# Role constants
ROLE_VIEWER = "viewer"
ROLE_SUPER_ADMIN = "super_admin"


# Get logger - server.py will configure logging, so we just get the logger here
# The logger will inherit the root logger's configuration once server.py configures it
logger = logging.getLogger(__name__)
# Ensure the logger level is set (will be overridden by server.py's basicConfig)
logger.setLevel(logging.INFO)


async def verify_google_token(token: str):
    """
    Verify Google OAuth ID token and return user information
    """
    try:
        # Get Google OAuth client ID from environment
        client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
        if not client_id:
            raise HTTPException(status_code=500, detail="Google OAuth client ID not configured")
        
        # Verify the token
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), client_id)
        
        # Verify the issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        
        # Extract user information
        return {
            "email": idinfo.get("email"),
            "name": idinfo.get("name", idinfo.get("email", "").split("@")[0]),
            "picture": idinfo.get("picture"),
            "sub": idinfo.get("sub")  # Google user ID
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying Google token: {str(e)}")

async def get_or_create_user(email: str, name: str, picture: Optional[str] = None):
    """
    Get existing user or create new one if authorized
    """
    try:
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
        # Create new user from hardcoded list (backward compatibility)
        user_data = {
            "id": f"user-{email.split('@')[0]}-{int(datetime.now(timezone.utc).timestamp())}",
            "email": email,
            "name": name,
            "picture": picture,
            "role": ROLE_VIEWER,  # All users are viewers by default
            "created_at": datetime.now(timezone.utc),
            "last_login": datetime.now(timezone.utc)
        }
        
        await db.users.insert_one(user_data)
        return user_data
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

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
