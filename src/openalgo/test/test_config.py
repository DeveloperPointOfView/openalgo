"""
Smoke tests for OpenAlgo configuration and core modules.
"""

import pytest
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from openalgo.config import settings


def test_config_loading():
    """Test that configuration loads without errors."""
    assert settings.app_name == "OpenAlgo"
    assert settings.version == "1.0.0"
    assert isinstance(settings.flask_port, int)
    assert isinstance(settings.websocket_port, int)


def test_paths_exist():
    """Test that configured paths are valid."""
    assert settings.base_dir.exists()
    assert settings.base_dir.is_absolute()  # Should be resolved to absolute path
    # var_dir is now in user-writable location, not under base_dir
    assert settings.var_dir.is_absolute()
    assert str(settings.var_dir).endswith("var")
    assert str(settings.db_dir).endswith("db")
    assert str(settings.log_dir).endswith("log")


def test_environment_variables():
    """Test that environment variables are handled correctly."""
    # DATABASE_URL should always have a default value
    assert settings.database_url is not None
    assert "sqlite" in settings.database_url  # Should default to SQLite

    # APP_KEY might be None in test environment, that's ok
    # The app should handle this gracefully


def test_env_bool_helper():
    """Test the _env_bool helper method with various inputs."""
    # Test with default values
    assert settings._env_bool("NONEXISTENT_VAR", True) is True
    assert settings._env_bool("NONEXISTENT_VAR", False) is False

    # Test with environment variables (using monkeypatch would be better, but this is a smoke test)
    # The method should handle various truthy/falsy string representations
    import os
    original_env = os.environ.copy()

    try:
        # Test truthy values
        os.environ["TEST_BOOL"] = "TRUE"
        assert settings._env_bool("TEST_BOOL", False) is True

        os.environ["TEST_BOOL"] = "1"
        assert settings._env_bool("TEST_BOOL", False) is True

        os.environ["TEST_BOOL"] = "YES"
        assert settings._env_bool("TEST_BOOL", False) is True

        # Test truthy values with whitespace
        os.environ["TEST_BOOL"] = "  true  "
        assert settings._env_bool("TEST_BOOL", False) is True

        os.environ["TEST_BOOL"] = "\tT\n"
        assert settings._env_bool("TEST_BOOL", False) is True

        # Test falsy values
        os.environ["TEST_BOOL"] = "FALSE"
        assert settings._env_bool("TEST_BOOL", True) is False

        os.environ["TEST_BOOL"] = "0"
        assert settings._env_bool("TEST_BOOL", True) is False

        # Test empty/None values fall back to default
        os.environ["TEST_BOOL"] = ""
        assert settings._env_bool("TEST_BOOL", True) is True
        assert settings._env_bool("TEST_BOOL", False) is False

        os.environ["TEST_BOOL"] = "   "
        assert settings._env_bool("TEST_BOOL", True) is True

        # Test unset variable falls back to default
        del os.environ["TEST_BOOL"]
        assert settings._env_bool("TEST_BOOL", True) is True
        assert settings._env_bool("TEST_BOOL", False) is False

    finally:
        # Restore environment
        os.environ.clear()
        os.environ.update(original_env)


def test_data_directory_logic():
    """Test the data directory selection logic."""
    import os
    from pathlib import Path
    original_env = os.environ.copy()

    try:
        # Clear relevant env vars
        for var in ["OPENALGO_DATA_DIR", "XDG_DATA_HOME"]:
            os.environ.pop(var, None)

        # Test default (should be ~/.openalgo)
        test_settings = type('TestSettings', (), {})()
        test_settings._get_data_dir = settings._get_data_dir.__get__(test_settings, type(test_settings))
        default_dir = test_settings._get_data_dir()
        assert str(default_dir).endswith(".openalgo")
        assert default_dir.is_absolute()

        # Test OPENALGO_DATA_DIR override
        os.environ["OPENALGO_DATA_DIR"] = "/tmp/custom_openalgo"
        custom_dir = test_settings._get_data_dir()
        assert str(custom_dir).endswith("custom_openalgo")  # Allow for /private/tmp resolution on macOS

        # Test XDG_DATA_HOME fallback
        del os.environ["OPENALGO_DATA_DIR"]
        os.environ["XDG_DATA_HOME"] = "/tmp/xdg_home"
        xdg_dir = test_settings._get_data_dir()
        assert str(xdg_dir).endswith("xdg_home/openalgo")  # Allow for /private/tmp resolution on macOS

    finally:
        # Restore environment
        os.environ.clear()
        os.environ.update(original_env)


if __name__ == "__main__":
    pytest.main([__file__])