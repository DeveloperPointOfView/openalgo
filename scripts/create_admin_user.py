#!/usr/bin/env python3
"""
Script to create an admin user for OpenAlgo
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.user_db import add_user, User, db_session
from utils.logging import get_logger

logger = get_logger(__name__)

def create_admin_user():
    """Create an admin user for OpenAlgo"""
    
    # Admin user credentials
    username = "admin"
    email = "admin@openalgo.com"
    password = "admin123"
    
    print(f"Creating admin user: {username}")
    
    # Check if admin user already exists
    existing_admin = User.query.filter_by(username=username).first()
    if existing_admin:
        print(f"Admin user '{username}' already exists!")
        print(f"   Username: {username}")
        print(f"   Email: {existing_admin.email}")
        print(f"   Password: {password}")
        print(f"   User ID: {existing_admin.id}")
        print(f"   Is Admin: {existing_admin.is_admin}")
        return existing_admin
    
    # Create the admin user
    admin_user = add_user(username, email, password, is_admin=True)
    
    if admin_user:
        print(f"✅ Admin user created successfully!")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"   User ID: {admin_user.id}")
        print(f"   Is Admin: {admin_user.is_admin}")
        print(f"\nYou can now login at: http://127.0.0.1:5050/auth/login")
        return admin_user
    else:
        print("❌ Failed to create admin user")
        return None

if __name__ == "__main__":
    create_admin_user()