from datetime import datetime, timezone
from flask import Blueprint, jsonify, current_app
from app import db

bp = Blueprint('health', __name__)

HEALTHY = 'healthy'
UNHEALTHY = 'unhealthy'
# A API não roda jobs agendados; o check existe para manter o formato padrão.
NOT_CONFIGURED = 'not_configured'


def _check_database():
    try:
        db.session.execute(db.text('SELECT 1'))
        return HEALTHY
    except Exception as e:
        current_app.logger.error(f"Health check - banco indisponível: {str(e)}")
        db.session.rollback()
        return UNHEALTHY


@bp.route('/health', methods=['GET'])
@bp.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check da API (público)
    ---
    tags:
      - Health
    security: []
    responses:
      200:
        description: API saudável
      503:
        description: Algum check falhou
    """
    checks = {
        'database': _check_database(),
        'scheduler': NOT_CONFIGURED,
    }
    status = UNHEALTHY if UNHEALTHY in checks.values() else HEALTHY

    return jsonify({
        'application': {
            'environment': current_app.config['APP_ENVIRONMENT'],
            'version': current_app.config['APP_VERSION'],
        },
        'checks': checks,
        'status': status,
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
    }), 200 if status == HEALTHY else 503
