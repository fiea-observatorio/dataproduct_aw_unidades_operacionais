from flask import jsonify
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError

def register_error_handlers(app):
    """Registrar handlers de erro globais"""
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Handler para exceções HTTP"""
        response = {
            'error': e.name,
            'message': e.description,
            'status': e.code
        }
        return jsonify(response), e.code
    
    @app.errorhandler(404)
    def handle_not_found(e):
        """Handler para 404"""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(400)
    def handle_bad_request(e):
        """Handler para 400"""
        return jsonify({
            'error': 'Bad Request',
            'message': str(e)
        }), 400
    
    @app.errorhandler(401)
    def handle_unauthorized(e):
        """Handler para 401"""
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def handle_forbidden(e):
        """Handler para 403"""
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        """Handler para 405"""
        return jsonify({
            'error': 'Method Not Allowed',
            'message': 'The method is not allowed for the requested URL'
        }), 405
    
    @app.errorhandler(429)
    def handle_rate_limit_exceeded(e):
        """Handler para rate limit"""
        return jsonify({
            'error': 'Too Many Requests',
            'message': 'Rate limit exceeded. Please try again later.'
        }), 429
    
    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(e):
        """Handler para erros de banco de dados"""
        app.logger.error(f"Database error: {str(e)}")
        return jsonify({
            'error': 'Database Error',
            'message': 'An error occurred while processing your request'
        }), 500
    
    @app.errorhandler(Exception)
    def handle_generic_error(e):
        """Handler genérico para qualquer erro não tratado"""
        app.logger.error(f"Unhandled error: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
