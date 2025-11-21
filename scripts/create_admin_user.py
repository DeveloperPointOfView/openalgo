#!/usr/bin/env python3
"""Create an admin user for OpenAlgo using the project's configured environment."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def bootstrap_paths():
    """
    Load environment variables before importing application modules and
    ensure the project src directory is on sys.path.
    """
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"

    if env_path.exists():
        load_dotenv(env_path)
    else:
        print(f"⚠️  .env not found at {env_path}. Using existing environment values.")

    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    return project_root


# Load env + paths before heavy imports
bootstrap_paths()

from openalgo.database.user_db import User, add_user  # noqa: E402
from openalgo.utils.logging import get_logger  # noqa: E402

logger = get_logger(__name__)


def get_admin_credentials():
    """
    Read admin credentials from environment with safe defaults so the script
    can be driven via env vars during container exec.
    """
    return (
        os.getenv("ADMIN_USERNAME", "admin"),
        os.getenv("ADMIN_EMAIL", "admin@openalgo.com"),
        os.getenv("ADMIN_PASSWORD", "admin123"),
    )


def create_admin_user():
    """Create an admin user for OpenAlgo"""

    username, email, password = get_admin_credentials()

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
        print("✅ Admin user created successfully!")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"   User ID: {admin_user.id}")
        print(f"   Is Admin: {admin_user.is_admin}")
        print("\nYou can now login at: http://127.0.0.1:5050/auth/login")
        return admin_user

    print("❌ Failed to create admin user")
    return None


if __name__ == "__main__":
    create_admin_user()
