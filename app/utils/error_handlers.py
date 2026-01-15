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
            'error': 'Não Encontrado',
            'message': 'O recurso solicitado não foi encontrado'
        }), 404
    
    @app.errorhandler(400)
    def handle_bad_request(e):
        """Handler para 400"""
        return jsonify({
            'error': 'Requisição Inválida',
            'message': str(e)
        }), 400
    
    @app.errorhandler(401)
    def handle_unauthorized(e):
        """Handler para 401"""
        return jsonify({
            'error': 'Não Autorizado',
            'message': 'Autenticação necessária'
        }), 401
    
    @app.errorhandler(403)
    def handle_forbidden(e):
        """Handler para 403"""
        return jsonify({
            'error': 'Proibido',
            'message': 'Você não tem permissão para acessar este recurso'
        }), 403
    
    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        """Handler para 405"""
        return jsonify({
            'error': 'Método Não Permitido',
            'message': 'O método não é permitido para a URL solicitada'
        }), 405
    
    @app.errorhandler(429)
    def handle_rate_limit_exceeded(e):
        """Handler para rate limit"""
        return jsonify({
            'error': 'Muitas Requisições',
            'message': 'Limite de taxa excedido. Por favor, tente novamente mais tarde.'
        }), 429
    
    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(e):
        """Handler para erros de banco de dados"""
        app.logger.error(f"Database error: {str(e)}")
        return jsonify({
            'error': 'Erro de Banco de Dados',
            'message': 'Ocorreu um erro ao processar sua solicitação'
        }), 500
    
    @app.errorhandler(Exception)
    def handle_generic_error(e):
        """Handler genérico para qualquer erro não tratado"""
        app.logger.error(f"Unhandled error: {str(e)}")
        return jsonify({
            'error': 'Erro Interno do Servidor',
            'message': 'Ocorreu um erro inesperado'
        }), 500
