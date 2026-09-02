from flask import Blueprint, current_app, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from app import db, limiter
from app.middleware.auth import require_role
from app.models import User, IdigitalUser
from app.services import idigital_service
from app.services.idigital_service import IdigitalAuthError

bp = Blueprint('auth', __name__)

# A autenticação oficial é via iDigital (/idigital/login). As linhas de
# `users` são perfis de acesso — carregam as unidades e o bi_filter_param que
# cada e-mail mapeado em `idigital_users` herda. O login por senha abaixo é um
# atalho de DESENVOLVIMENTO: só responde com ALLOW_PASSWORD_LOGIN=1 na .env e
# nunca deve ficar ligado em produção.

@bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute; 20 per hour")
def login():
    """
    Login de desenvolvimento (usuário/senha)
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      200:
        description: Login bem-sucedido
      401:
        description: Credenciais inválidas
      404:
        description: Login por senha desativado neste ambiente
    """
    if not current_app.config.get('ALLOW_PASSWORD_LOGIN'):
        return jsonify({'error': 'Login por senha desativado neste ambiente'}), 404

    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Usuário e senha são obrigatórios'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Usuário ou senha inválidos'}), 401

    return jsonify({
        'access_token': create_access_token(identity=str(user.id)),
        'refresh_token': create_refresh_token(identity=str(user.id)),
        'user': user.to_dict(include_units=True)
    }), 200

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Renovar access token
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Token renovado com sucesso
        schema:
          type: object
          properties:
            access_token:
              type: string
    """
    current_user_id = get_jwt_identity()  # Já é string
    new_access_token = create_access_token(identity=current_user_id)
    
    return jsonify({'access_token': new_access_token}), 200

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Obter dados do usuário autenticado
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Dados do usuário
      404:
        description: Usuário não encontrado
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    return jsonify(user.to_dict(include_units=True)), 200

@bp.route('/idigital/login', methods=['POST'])
@limiter.limit("10 per minute; 40 per hour")
def idigital_login():
    """
    Troca tokens do iDigital por tokens da aplicação
    ---
    tags:
      - Authentication
    parameters:
      - in: header
        name: Authorization
        required: true
        description: "Bearer {access token do iDigital}"
        type: string
      - in: header
        name: X-Id-Token
        required: true
        description: ID token do iDigital (fonte do e-mail)
        type: string
    responses:
      200:
        description: Login bem-sucedido
        schema:
          type: object
          properties:
            access_token:
              type: string
            refresh_token:
              type: string
            user:
              type: object
      401:
        description: Tokens do iDigital inválidos
      403:
        description: E-mail sem acesso cadastrado na plataforma
    """
    bearer = request.headers.get('Authorization', '')
    access_token = bearer.split(' ', 1)[1].strip() if bearer.lower().startswith('bearer ') else None
    id_token = request.headers.get('X-Id-Token')

    if not access_token or not id_token:
        return jsonify({'error': 'Tokens do iDigital não informados'}), 401

    try:
        idigital_service.verify_access_token(access_token)
        claims = idigital_service.verify_id_token(id_token)
    except IdigitalAuthError as error:
        return jsonify({'error': f'Autenticação iDigital recusada: {error}'}), 401
    except Exception:
        return jsonify({'error': 'Falha ao validar tokens no iDigital'}), 401

    email = idigital_service.get_email(claims)
    if not email:
        return jsonify({'error': 'O iDigital não informou o e-mail do usuário'}), 401

    mapping = IdigitalUser.query.filter(db.func.lower(IdigitalUser.email) == email).first()
    if not mapping or not mapping.user:
        return jsonify({'error': f'O e-mail {email} ainda não tem acesso à plataforma'}), 403

    user = mapping.user
    return jsonify({
        'access_token': create_access_token(identity=str(user.id)),
        'refresh_token': create_refresh_token(identity=str(user.id)),
        'user': user.to_dict(include_units=True)
    }), 200

@bp.route('/idigital/profiles', methods=['GET'])
@require_role('admin')
def list_idigital_profiles():
    """
    Lista os perfis de acesso disponíveis (com unidades)
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de perfis
    """
    users = User.query.order_by(User.username).all()
    return jsonify([u.to_dict(include_units=True) for u in users]), 200

@bp.route('/idigital/users', methods=['GET'])
@require_role('admin')
def list_idigital_users():
    """
    Lista os e-mails do iDigital e o usuário legado de cada um
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de mapeamentos
    """
    mappings = IdigitalUser.query.order_by(IdigitalUser.email).all()
    return jsonify([m.to_dict() for m in mappings]), 200

@bp.route('/idigital/users', methods=['POST'])
@require_role('admin')
def create_idigital_user():
    """
    Vincula um e-mail do iDigital a um usuário legado (define os acessos)
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
          properties:
            email:
              type: string
              example: "fulano@sistemafiea.com.br"
            username:
              type: string
              example: "senai.poco"
            user_id:
              type: integer
    responses:
      201:
        description: Mapeamento criado
      400:
        description: Dados inválidos
      404:
        description: Usuário legado não encontrado
      409:
        description: E-mail já cadastrado
    """
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()

    if not email or '@' not in email:
        return jsonify({'error': 'E-mail inválido'}), 400

    user = None
    if data.get('user_id'):
        user = User.query.get(data['user_id'])
    elif data.get('username'):
        user = User.query.filter_by(username=data['username']).first()

    if not user:
        return jsonify({'error': 'Informe um username ou user_id de usuário existente'}), 404

    if IdigitalUser.query.filter(db.func.lower(IdigitalUser.email) == email).first():
        return jsonify({'error': 'E-mail já cadastrado'}), 409

    mapping = IdigitalUser(email=email, user_id=user.id)
    db.session.add(mapping)
    db.session.commit()

    return jsonify(mapping.to_dict()), 201

@bp.route('/idigital/users/<int:id>', methods=['DELETE'])
@require_role('admin')
def delete_idigital_user(id):
    """
    Remove o vínculo de um e-mail do iDigital
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        required: true
        type: integer
    responses:
      200:
        description: Mapeamento removido
      404:
        description: Mapeamento não encontrado
    """
    mapping = IdigitalUser.query.get(id)
    if not mapping:
        return jsonify({'error': 'Mapeamento não encontrado'}), 404

    db.session.delete(mapping)
    db.session.commit()
    return jsonify({'message': 'Mapeamento removido'}), 200
