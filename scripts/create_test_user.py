#!/usr/bin/env python3
"""
Script to create a test user for OpenAlgo
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.user_db import add_user, User, db_session
from utils.logging import get_logger

logger = get_logger(__name__)

def create_test_user():
    """Create a test user for OpenAlgo"""
    
    # Test user credentials
    username = "testuser"
    email = "test@example.com"
    password = "testpass123"
    
    print(f"Creating test user: {username}")
    
    # Check if user already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        print(f"User '{username}' already exists!")
        print(f"   Username: {username}")
        print(f"   Email: {existing_user.email}")
        print(f"   Password: {password}")
        print(f"   User ID: {existing_user.id}")
        print(f"\nYou can login at: http://127.0.0.1:5050/auth/login")
        return existing_user
    
    # Create the user
    user = add_user(username, email, password, is_admin=False)
    
    if user:
        print(f"✅ Test user created successfully!")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"   User ID: {user.id}")
        print(f"\nYou can now login at: http://127.0.0.1:5050/auth/login")
        return user
    else:
        print("❌ Failed to create test user (username might already exist)")
        return None

if __name__ == "__main__":
    create_test_user()