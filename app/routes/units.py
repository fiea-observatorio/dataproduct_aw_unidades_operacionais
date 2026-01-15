from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Unit, User
from app.middleware.auth import require_role, require_unit_access, get_current_user

bp = Blueprint('units', __name__)

@bp.route('', methods=['GET'])
@jwt_required()
def list_units():
    """
    Listar unidades
    ---
    tags:
      - Units
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de unidades
    """
    user = get_current_user()
    
    # Admin vê todas as unidades, usuário comum vê apenas as suas
    if user.role == 'admin':
        units = Unit.query.all()
    else:
        units = user.units
    
    return jsonify([unit.to_dict() for unit in units]), 200

@bp.route('', methods=['POST'])
@jwt_required()
@require_role('admin')
def create_unit():
    """
    Criar nova unidade (apenas admin)
    ---
    tags:
      - Units
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              example: "Unidade Centro"
            description:
              type: string
              example: "Unidade central da empresa"
    responses:
      201:
        description: Unidade criada com sucesso
      400:
        description: Dados inválidos
    """
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Nome é obrigatório'}), 400
    
    unit = Unit(
        name=data['name'],
        description=data.get('description')
    )
    
    db.session.add(unit)
    db.session.commit()
    
    return jsonify(unit.to_dict()), 201

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@require_unit_access
def get_unit(id):
    """
    Obter detalhes de uma unidade
    ---
    tags:
      - Units
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Detalhes da unidade
      404:
        description: Unidade não encontrada
    """
    unit = Unit.query.get_or_404(id)
    return jsonify(unit.to_dict(include_users=True)), 200

@bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@require_role('admin')
def update_unit(id):
    """
    Atualizar unidade (apenas admin)
    ---
    tags:
      - Units
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
            name:
              type: string
            description:
              type: string
    responses:
      200:
        description: Unidade atualizada
      404:
        description: Unidade não encontrada
    """
    unit = Unit.query.get_or_404(id)
    data = request.get_json()
    
    if data.get('name'):
        unit.name = data['name']
    if 'description' in data:
        unit.description = data['description']
    
    db.session.commit()
    
    return jsonify(unit.to_dict()), 200

@bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@require_role('admin')
def delete_unit(id):
    """
    Deletar unidade (apenas admin)
    ---
    tags:
      - Units
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      204:
        description: Unidade deletada
      404:
        description: Unidade não encontrada
    """
    unit = Unit.query.get_or_404(id)
    
    db.session.delete(unit)
    db.session.commit()
    
    return '', 204

@bp.route('/<int:id>/users', methods=['POST'])
@jwt_required()
@require_role('admin')
def add_user_to_unit(id):
    """
    Associar usuário a unidade (apenas admin)
    ---
    tags:
      - Units
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - user_id
          properties:
            user_id:
              type: integer
              example: 1
    responses:
      200:
        description: Usuário associado com sucesso
      404:
        description: Unidade ou usuário não encontrado
      409:
        description: Usuário já associado
    """
    unit = Unit.query.get_or_404(id)
    data = request.get_json()
    
    if not data or not data.get('user_id'):
        return jsonify({'error': 'user_id é obrigatório'}), 400
    
    user = User.query.get_or_404(data['user_id'])
    
    # Verificar se já está associado
    if user in unit.users:
        return jsonify({'error': 'Usuário já associado a esta unidade'}), 409
    
    unit.users.append(user)
    db.session.commit()
    
    return jsonify({'message': 'Usuário adicionado à unidade com sucesso'}), 200

@bp.route('/<int:id>/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@require_role('admin')
def remove_user_from_unit(id, user_id):
    """
    Remover usuário de unidade (apenas admin)
    ---
    tags:
      - Units
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
      - in: path
        name: user_id
        type: integer
        required: true
    responses:
      200:
        description: Usuário removido com sucesso
      404:
        description: Unidade ou usuário não encontrado
    """
    unit = Unit.query.get_or_404(id)
    user = User.query.get_or_404(user_id)
    
    if user in unit.users:
        unit.users.remove(user)
        db.session.commit()
        return jsonify({'message': 'Usuário removido da unidade com sucesso'}), 200
    
    return jsonify({'error': 'Usuário não associado a esta unidade'}), 404

@bp.route('/<int:id>/users', methods=['GET'])
@jwt_required()
@require_unit_access
def list_unit_users(id):
    """
    Listar usuários de uma unidade
    ---
    tags:
      - Units
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Lista de usuários
    """
    unit = Unit.query.get_or_404(id)
    
    users = [{'id': u.id, 'username': u.username, 'role': u.role} for u in unit.users]
    
    return jsonify(users), 200
