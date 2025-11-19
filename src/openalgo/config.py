"""
Central configuration module for OpenAlgo.

This module provides a centralized way to manage application configuration.
"""

import os
from pathlib import Path


class OpenAlgoSettings:
    """Application settings with environment variable support."""

    def _get_data_dir(self) -> Path:
        """Get user-writable data directory for OpenAlgo."""
        # Priority: OPENALGO_DATA_DIR env var > XDG_DATA_HOME > ~/.openalgo
        if data_dir := os.getenv("OPENALGO_DATA_DIR"):
            path = Path(data_dir).expanduser().resolve()
            if path.is_absolute():
                return path

        # XDG Base Directory specification
        if xdg_data := os.getenv("XDG_DATA_HOME"):
            return Path(xdg_data).expanduser().resolve() / "openalgo"

        # Fallback to ~/.openalgo
        return Path.home() / ".openalgo"

    def __init__(self):
        # Paths (must be set first as they're used by other settings)
        self.base_dir = Path(__file__).parent.parent.parent.resolve()
        self.var_dir = self._get_data_dir() / "var"
        self.db_dir = self.var_dir / "db"
        self.log_dir = self.var_dir / "log"

        # Application
        self.app_key = os.getenv("APP_KEY")
        self.app_name = "OpenAlgo"
        self.version = "1.0.0"

        # Server
        self.host_server = os.getenv("HOST_SERVER", "http://127.0.0.1:5000")
        self.flask_host_ip = os.getenv("FLASK_HOST_IP", "127.0.0.1")
        self.flask_port = int(os.getenv("FLASK_PORT", 5000))
        self.flask_debug = self._env_bool("FLASK_DEBUG", False)
        self.flask_env = os.getenv("FLASK_ENV", "production")

        # Database
        self.database_url = os.getenv("DATABASE_URL") or f"sqlite:///{self.db_dir}/openalgo.db"

        # Session
        self.session_cookie_name = os.getenv("SESSION_COOKIE_NAME", "session")
        self.csrf_cookie_name = os.getenv("CSRF_COOKIE_NAME", "csrf_token")
        csrf_time_limit = os.getenv("CSRF_TIME_LIMIT", "").strip()
        self.csrf_time_limit = int(csrf_time_limit) if csrf_time_limit else None

        # Security
        self.csrf_enabled = self._env_bool("CSRF_ENABLED", True)

        # API
        self.api_rate_limit = os.getenv("API_RATE_LIMIT", "10 per second")

        # WebSocket
        self.websocket_port = int(os.getenv("WEBSOCKET_PORT", 8765))
        self.zmq_port = int(os.getenv("ZMQ_PORT", 5555))

        # Features
        self.analyzer_mode = self._env_bool("ANALYZER_MODE", False)
        self.ngrok_allow = self._env_bool("NGROK_ALLOW", False)

        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # Create directories (only if writable)
        self._create_directories_if_writable()

    def _env_bool(self, name: str, default: bool = False) -> bool:
        """Parse boolean environment variable with consistent semantics."""
        value = os.getenv(name)
        if value is None or not value.strip():
            return default
        return value.strip().upper() in ("TRUE", "1", "T", "YES", "Y")

    def _create_directories_if_writable(self):
        """Create data directories only if the data directory is writable."""
        try:
            # Check if we can write to the data directory
            data_dir = self.var_dir.parent
            data_dir.mkdir(parents=True, exist_ok=True)

            # Test writability by creating a temporary file
            test_file = data_dir / ".write_test"
            test_file.touch()
            test_file.unlink()

            # If we get here, the directory is writable
            self.var_dir.mkdir(parents=True, exist_ok=True)
            self.db_dir.mkdir(parents=True, exist_ok=True)
            self.log_dir.mkdir(parents=True, exist_ok=True)

        except (OSError, PermissionError):
            # Directory is not writable, skip creation
            # The app should handle missing directories gracefully
            pass


# Global settings instance
settings = OpenAlgoSettings()