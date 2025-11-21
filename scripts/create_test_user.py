#!/usr/bin/env python3
"""Create a non-admin test user using the project's configured environment."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def bootstrap_paths():
    """Load env variables and ensure src is importable."""
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"

    if env_path.exists():
        load_dotenv(env_path)
    else:
        print(f"⚠️  .env not found at {env_path}. Using existing environment values.")

    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


bootstrap_paths()

from openalgo.database.user_db import User, add_user  # noqa: E402
from openalgo.utils.logging import get_logger  # noqa: E402

logger = get_logger(__name__)


def get_test_user_credentials():
    """Allow test user credentials to be overridden via environment variables."""
    return (
        os.getenv("TEST_USERNAME", "testuser"),
        os.getenv("TEST_EMAIL", "test@example.com"),
        os.getenv("TEST_PASSWORD", "testpass123"),
    )


def create_test_user():
    """Create a test user for OpenAlgo"""

    username, email, password = get_test_user_credentials()
    print(f"Creating test user: {username}")

    # Check if user already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        print(f"User '{username}' already exists!")
        print(f"   Username: {username}")
        print(f"   Email: {existing_user.email}")
        print(f"   Password: {password}")
        print(f"   User ID: {existing_user.id}")
        print("\nYou can login at: http://127.0.0.1:5050/auth/login")
        return existing_user

    # Create the user
    user = add_user(username, email, password, is_admin=False)

    if user:
        print("✅ Test user created successfully!")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"   User ID: {user.id}")
        print("\nYou can now login at: http://127.0.0.1:5050/auth/login")
        return user

    print("❌ Failed to create test user (username might already exist)")
    return None


if __name__ == "__main__":
    create_test_user()
