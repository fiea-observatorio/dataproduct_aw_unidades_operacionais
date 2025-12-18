from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models import User, Unit, Link, Report, AccessLog
from app.middleware.auth import require_role
from sqlalchemy import func

bp = Blueprint('admin', __name__)

@bp.route('/users', methods=['GET'])
@jwt_required()
@require_role('admin')
def list_users():
    """
    Listar todos os usuários (apenas admin)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de usuários
    """
    users = User.query.all()
    return jsonify([user.to_dict(include_units=True) for user in users]), 200

@bp.route('/users/<int:id>', methods=['PUT'])
@jwt_required()
@require_role('admin')
def update_user(id):
    """
    Atualizar usuário (apenas admin)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            role:
              type: string
              enum: [admin, user]
            password:
              type: string
    responses:
      200:
        description: Usuário atualizado
      404:
        description: Usuário não encontrado
    """
    user = User.query.get_or_404(id)
    data = request.get_json()
    
    if data.get('role') and data['role'] in ['admin', 'user']:
        user.role = data['role']
    
    if data.get('password'):
        user.set_password(data['password'])
    
    db.session.commit()
    
    return jsonify(user.to_dict()), 200

@bp.route('/users/<int:id>', methods=['DELETE'])
@jwt_required()
@require_role('admin')
def delete_user(id):
    """
    Deletar usuário (apenas admin)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      204:
        description: Usuário deletado
      404:
        description: Usuário não encontrado
    """
    user = User.query.get_or_404(id)
    
    db.session.delete(user)
    db.session.commit()
    
    return '', 204

@bp.route('/stats', methods=['GET'])
@jwt_required()
@require_role('admin')
def get_stats():
    """
    Obter estatísticas gerais (apenas admin)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    responses:
      200:
        description: Estatísticas do sistema
    """
    stats = {
        'total_users': User.query.count(),
        'total_units': Unit.query.count(),
        'total_links': Link.query.count(),
        'total_reports': Report.query.count(),
        'total_accesses': AccessLog.query.count(),
        'users_by_role': dict(
            db.session.query(User.role, func.count(User.id))
            .group_by(User.role)
            .all()
        )
    }
    
    return jsonify(stats), 200

@bp.route('/access-logs', methods=['GET'])
@jwt_required()
@require_role('admin')
def get_access_logs():
    """
    Obter logs de acesso (apenas admin)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - in: query
        name: user_id
        type: integer
        required: false
      - in: query
        name: report_id
        type: integer
        required: false
      - in: query
        name: limit
        type: integer
        required: false
        default: 100
    responses:
      200:
        description: Logs de acesso
    """
    query = AccessLog.query
    
    user_id = request.args.get('user_id', type=int)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    report_id = request.args.get('report_id', type=int)
    if report_id:
        query = query.filter_by(report_id=report_id)
    
    limit = request.args.get('limit', type=int, default=100)
    
    logs = query.order_by(AccessLog.created_at.desc()).limit(limit).all()
    
    return jsonify([log.to_dict() for log in logs]), 200
