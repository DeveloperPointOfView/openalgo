from flask import Blueprint, jsonify, render_template, session
import os
import socket
from openalgo.utils.logging import get_logger

# Optional imports guarded inside functions to avoid import-time errors

logger = get_logger(__name__)

health_bp = Blueprint('health_bp', __name__)


def _check_db():
    try:
        # Reuse existing engine from user_db module to avoid creating new engines
        from openalgo.database.user_db import engine as user_engine
        from sqlalchemy import text
        with user_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "DB reachable"
    except Exception as e:
        logger.error(f"Health DB check failed: {e}")
        return False, str(e)


def _check_websocket():
    host = os.getenv('WEBSOCKET_HOST', '127.0.0.1')
    try:
        port = int(os.getenv('WEBSOCKET_PORT', '8765'))
    except Exception:
        port = 8765
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return True, f"ws://{host}:{port} reachable"
    except Exception as e:
        logger.warning(f"WebSocket health check failed: {e}")
        return False, str(e)


def _get_current_user():
    try:
        return session.get('user')
    except Exception:
        return None


def _check_broker_and_master_contract():
    """Return (broker_connected, broker_name, master_contract_ready, msg)"""
    user = _get_current_user()
    if not user:
        return False, None, False, "No user session"

    try:
        from openalgo.database.auth_db import get_auth_token_dbquery
        auth_obj = get_auth_token_dbquery(user)
        if not auth_obj:
            return False, None, False, "No broker token found"

        broker = getattr(auth_obj, 'broker', None)
        # If we have a broker set, check master contract readiness
        if broker:
            try:
                from openalgo.database.master_contract_status_db import check_if_ready
                ready = bool(check_if_ready(broker))
            except Exception as e:
                logger.warning(f"Master contract readiness check failed: {e}")
                ready = False
            return True, broker, ready, "Broker connected"
        else:
            return True, None, False, "Broker token found without broker name"
    except Exception as e:
        logger.error(f"Broker health check error: {e}")
        return False, None, False, str(e)


@health_bp.route('/api/health', methods=['GET'])
def api_health():
    # Basic app check
    checks = {}
    overall_ok = True

    # App/version
    try:
        from openalgo.utils.version import get_version
        checks['app'] = {'ok': True, 'version': get_version()}
    except Exception:
        checks['app'] = {'ok': True}

    # DB
    db_ok, db_msg = _check_db()
    checks['db'] = {'ok': db_ok, 'message': db_msg}
    overall_ok &= db_ok

    # WebSocket
    ws_ok, ws_msg = _check_websocket()
    checks['websocket'] = {'ok': ws_ok, 'message': ws_msg}
    overall_ok &= ws_ok

    # Broker + Master Contract (user-specific; ok to be false when not logged in)
    broker_connected, broker_name, mc_ready, broker_msg = _check_broker_and_master_contract()
    checks['broker'] = {
        'connected': broker_connected,
        'broker': broker_name,
        'message': broker_msg
    }
    checks['master_contract'] = {
        'ready': mc_ready
    }

    status = 'ok' if overall_ok else 'degraded'
    return jsonify({'status': status, 'checks': checks}), 200


@health_bp.route('/health', methods=['GET'])
def health_page():
    return render_template('health.html')
