"""
Shared MongoDB database connection module
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection - singleton pattern
_client: AsyncIOMotorClient = None
_db = None

def get_database():
    """Get or create the database connection"""
    global _client, _db
    
    if _client is None or _db is None:
        mongo_url = os.environ.get('MONGO_URL')
        if not mongo_url:
            raise ValueError("MONGO_URL environment variable is not set")
        
        # Create client with connection pool settings to prevent hanging
        _client = AsyncIOMotorClient(
            mongo_url,
            serverSelectionTimeoutMS=5000,  # 5 second timeout for server selection
            connectTimeoutMS=10000,  # 10 second timeout for connection
            socketTimeoutMS=30000,  # 30 second timeout for socket operations
            maxPoolSize=50,  # Maximum number of connections in the pool
            minPoolSize=10,  # Minimum number of connections in the pool
            maxIdleTimeMS=45000,  # Close connections after 45 seconds of inactivity
        )
        _db = _client[os.environ.get('DB_NAME', 'sales_analytics')]
    
    return _db

def get_client():
    """Get or create the MongoDB client"""
    global _client
    
    if _client is None:
        mongo_url = os.environ.get('MONGO_URL')
        if not mongo_url:
            raise ValueError("MONGO_URL environment variable is not set")
        
        # Create client with connection pool settings to prevent hanging
        _client = AsyncIOMotorClient(
            mongo_url,
            serverSelectionTimeoutMS=5000,  # 5 second timeout for server selection
            connectTimeoutMS=10000,  # 10 second timeout for connection
            socketTimeoutMS=30000,  # 30 second timeout for socket operations
            maxPoolSize=50,  # Maximum number of connections in the pool
            minPoolSize=10,  # Minimum number of connections in the pool
            maxIdleTimeMS=45000,  # Close connections after 45 seconds of inactivity
        )
    
    return _client

def close_connection():
    """Close the database connection"""
    global _client, _db
    
    if _client is not None:
        _client.close()
        _client = None
        _db = None

