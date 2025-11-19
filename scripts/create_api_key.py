#!/usr/bin/env python3
"""
Script to create an API key for a user in OpenAlgo
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.auth_db import upsert_api_key, get_api_key_for_tradingview
from database.user_db import User, db_session
from blueprints.apikey import generate_api_key
from utils.logging import get_logger

logger = get_logger(__name__)

def create_api_key_for_user(username):
    """Create an API key for a specific user"""
    
    print(f"Creating API key for user: {username}")
    
    # Find the user
    user = User.query.filter_by(username=username).first()
    if not user:
        print(f"❌ User '{username}' not found!")
        return None
    
    print(f"   User ID: {user.id}")
    print(f"   Email: {user.email}")
    
    # Check if user already has an API key
    existing_key = get_api_key_for_tradingview(username)
    if existing_key:
        print(f"✅ User already has an API key: {existing_key}")
        return existing_key
    
    # Generate new API key
    api_key = generate_api_key()
    
    # Store the API key
    key_id = upsert_api_key(username, api_key)
    
    if key_id is not None:
        print(f"✅ API key created successfully!")
        print(f"   API Key: {api_key}")
        print(f"   Key ID: {key_id}")
        print(f"\nUse this API key in your bot's .env file:")
        print(f"OPENALGO_API_KEY={api_key}")
        return api_key
    else:
        print("❌ Failed to create API key")
        return None

if __name__ == "__main__":
    # Create API key for admin user
    api_key = create_api_key_for_user("admin")
    
    if api_key:
        print(f"\n🎯 SUCCESS: API key ready for use!")
        print(f"Update your bot's .env file with:")
        print(f"OPENALGO_API_KEY={api_key}")
