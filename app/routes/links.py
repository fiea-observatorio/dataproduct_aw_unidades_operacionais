from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models import Link, Unit
from app.middleware.auth import require_unit_access, get_current_user, require_role

bp = Blueprint('links', __name__)

@bp.route('/units/<int:unit_id>/links', methods=['GET'])
@jwt_required()
@require_unit_access
def list_links(unit_id):
    """
    Listar links de uma unidade
    ---
    tags:
      - Links
    security:
      - Bearer: []
    parameters:
      - in: path
        name: unit_id
        type: integer
        required: true
    responses:
      200:
        description: Lista de links
    """
    unit = Unit.query.get_or_404(unit_id)
    links = Link.query.filter_by(unit_id=unit_id).all()
    
    return jsonify([link.to_dict() for link in links]), 200

@bp.route('/units/<int:unit_id>/links', methods=['POST'])
@jwt_required()
@require_role('admin')
def create_link(unit_id):
    """
    Criar novo link em uma unidade (apenas admin)
    ---
    tags:
      - Links
    security:
      - Bearer: []
    parameters:
      - in: path
        name: unit_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - url
          properties:
            name:
              type: string
              example: "Dashboard Vendas"
            url:
              type: string
              example: "https://app.powerbi.com/..."
            description:
              type: string
              example: "Dashboard de vendas mensais"
    responses:
      201:
        description: Link criado com sucesso
      400:
        description: Dados inválidos
      404:
        description: Unidade não encontrada
    """
    unit = Unit.query.get_or_404(unit_id)
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('url'):
        return jsonify({'error': 'Name and URL are required'}), 400
    
    # Validação básica de URL
    url = data['url'].strip()
    if not url.startswith('http://') and not url.startswith('https://'):
        return jsonify({'error': 'Invalid URL format'}), 400
    
    link = Link(
        unit_id=unit_id,
        name=data['name'],
        url=url,
        description=data.get('description')
    )
    
    db.session.add(link)
    db.session.commit()
    
    return jsonify(link.to_dict()), 201

@bp.route('/links/<int:id>', methods=['GET'])
@jwt_required()
def get_link(id):
    """
    Obter detalhes de um link
    ---
    tags:
      - Links
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Detalhes do link
      403:
        description: Acesso negado
      404:
        description: Link não encontrado
    """
    link = Link.query.get_or_404(id)
    user = get_current_user()
    
    # Verificar acesso
    if user.role != 'admin' and link.unit not in user.units:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(link.to_dict()), 200

@bp.route('/links/<int:id>', methods=['PUT'])
@jwt_required()
@require_role('admin')
def update_link(id):
    """
    Atualizar link (apenas admin)
    ---
    tags:
      - Links
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
            url:
              type: string
            description:
              type: string
    responses:
      200:
        description: Link atualizado
      404:
        description: Link não encontrado
    """
    link = Link.query.get_or_404(id)
    data = request.get_json()
    
    if data.get('name'):
        link.name = data['name']
    if data.get('url'):
        url = data['url'].strip()
        if not url.startswith('http://') and not url.startswith('https://'):
            return jsonify({'error': 'Invalid URL format'}), 400
        link.url = url
    if 'description' in data:
        link.description = data['description']
    
    db.session.commit()
    
    return jsonify(link.to_dict()), 200

@bp.route('/links/<int:id>', methods=['DELETE'])
@jwt_required()
@require_role('admin')
def delete_link(id):
    """
    Deletar link (apenas admin)
    ---
    tags:
      - Links
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      204:
        description: Link deletado
      404:
        description: Link não encontrado
    """
    link = Link.query.get_or_404(id)
    
    db.session.delete(link)
    db.session.commit()
    
    return '', 204

@bp.route('/me/links', methods=['GET'])
@jwt_required()
def get_my_links():
    """
    Obter todos os links do usuário autenticado
    ---
    tags:
      - Links
    security:
      - Bearer: []
    parameters:
      - in: query
        name: unit_id
        type: integer
        required: false
        description: Filtrar por unidade específica
    responses:
      200:
        description: Lista de links
    """
    user = get_current_user()
    unit_id = request.args.get('unit_id', type=int)
    
    if user.role == 'admin':
        # Admin vê todos os links
        query = Link.query
        if unit_id:
            query = query.filter_by(unit_id=unit_id)
        links = query.all()
    else:
        # Usuário comum vê apenas links das suas unidades
        unit_ids = [u.id for u in user.units]
        query = Link.query.filter(Link.unit_id.in_(unit_ids))
        if unit_id:
            if unit_id not in unit_ids:
                return jsonify({'error': 'Access denied to this unit'}), 403
            query = query.filter_by(unit_id=unit_id)
        links = query.all()
    
    return jsonify([link.to_dict() for link in links]), 200
