from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from app import db, limiter
from app.models import User

bp = Blueprint('auth', __name__)

# @bp.route('/register', methods=['POST'])
# @limiter.limit("5 per hour")
# def register():
#     """
#     Registro de novo usuário
#     ---
#     tags:
#       - Authentication
#     parameters:
#       - in: body
#         name: body
#         required: true
#         schema:
#           type: object
#           required:
#             - username
#             - password
#           properties:
#             username:
#               type: string
#               example: "johndoe"
#             password:
#               type: string
#               example: "SecurePass123!"
#     responses:
#       201:
#         description: Usuário criado com sucesso
#       400:
#         description: Dados inválidos
#       409:
#         description: Username já existe
#     """
#     data = request.get_json()
    
#     if not data or not data.get('username') or not data.get('password'):
#         return jsonify({'error': 'Username and password are required'}), 400
    
#     username = data['username'].strip()
#     password = data['password']
    
#     # Validações
#     if len(username) < 3:
#         return jsonify({'error': 'Username must be at least 3 characters'}), 400
    
#     if len(password) < 6:
#         return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
#     # Verificar se username já existe
#     if User.query.filter_by(username=username).first():
#         return jsonify({'error': 'Username already exists'}), 409
    
#     # Criar usuário
#     user = User(username=username)
#     user.set_password(password)
    
#     db.session.add(user)
#     db.session.commit()
    
#     return jsonify({
#         'message': 'User created successfully',
#         'user': user.to_dict()
#     }), 201

@bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """
    Login de usuário
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
              example: "johndoe"
            password:
              type: string
              example: "SecurePass123!"
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
        description: Credenciais inválidas
    """
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Usuário e senha são obrigatórios'}), 400
    
    username = data['username']
    password = data['password']
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Usuário ou senha inválidos'}), 401
    
    # Criar tokens (identity deve ser string)
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
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
