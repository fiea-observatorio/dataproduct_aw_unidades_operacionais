from app import create_app, db
from app.models import User, Unit, Report, Step
import os

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Adicionar variáveis ao shell do Flask"""
    return {
        'db': db,
        'User': User,
        'Unit': Unit,
        'Report': Report,
        'Step': Step
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
