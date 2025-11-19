# websocket_proxy/__init__.py

import logging

from .server import WebSocketProxy, main as websocket_main
from .broker_factory import register_adapter, create_broker_adapter

# Set up logger
logger = logging.getLogger(__name__)

# websocket_proxy/__init__.py

import logging

from .server import WebSocketProxy, main as websocket_main
from .broker_factory import register_adapter, create_broker_adapter

# Set up logger
logger = logging.getLogger(__name__)

# websocket_proxy/__init__.py

import logging

from .server import WebSocketProxy, main as websocket_main
from .broker_factory import register_adapter, create_broker_adapter

# Set up logger
logger = logging.getLogger(__name__)

# Don't register adapters at import time to avoid circular imports
# Adapters will be registered dynamically when first requested

__all__ = [
    'WebSocketProxy',
    'websocket_main',
    'register_adapter',
    'create_broker_adapter'
]

__all__ = [
    'WebSocketProxy',
    'websocket_main',
    'register_adapter',
    'create_broker_adapter'
]
