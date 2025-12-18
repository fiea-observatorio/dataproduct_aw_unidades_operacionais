from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models import User, Unit

def require_role(required_role):
    """Decorator para verificar role do usuário"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            current_user_id = int(get_jwt_identity())
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if user.role != required_role and user.role != 'admin':
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def require_unit_access(fn):
    """Decorator para verificar se usuário tem acesso à unidade"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Admin tem acesso a todas as unidades
        if user.role == 'admin':
            return fn(*args, **kwargs)
        
        # Pegar unit_id dos kwargs ou args
        unit_id = kwargs.get('unit_id')
        if not unit_id and 'id' in kwargs:
            unit_id = kwargs.get('id')
        
        if not unit_id:
            return jsonify({'error': 'Unit ID not provided'}), 400
        
        # Verificar se usuário pertence à unidade
        unit = Unit.query.get(unit_id)
        if not unit:
            return jsonify({'error': 'Unit not found'}), 404
        
        if user not in unit.users:
            return jsonify({'error': 'Access denied to this unit'}), 403
        
        return fn(*args, **kwargs)
    return wrapper

def get_current_user():
    """Helper para obter usuário atual"""
    verify_jwt_in_request()
    current_user_id = int(get_jwt_identity())
    return User.query.get(current_user_id)
