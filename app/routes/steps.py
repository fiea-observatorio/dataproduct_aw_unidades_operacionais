from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models import Step, Report, Unit
from app.middleware.auth import get_current_user

bp = Blueprint('steps', __name__)

@bp.route('', methods=['GET'])
@jwt_required()
def list_steps():
    """
    Listar todos os steps
    ---
    tags:
      - Steps
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de steps
    """
    steps = Step.query.order_by(Step.step_number).all()
    return jsonify([step.to_dict() for step in steps]), 200

@bp.route('/<int:step_number>/units/<int:unit_id>/reports', methods=['GET'])
@jwt_required()
def get_reports_by_step_and_unit(step_number, unit_id):
    """
    Obter reports de um step específico para uma unidade específica
    ---
    tags:
      - Steps
    security:
      - Bearer: []
    parameters:
      - in: path
        name: step_number
        required: true
        schema:
          type: integer
        description: Número do step (1-6)
      - in: path
        name: unit_id
        required: true
        schema:
          type: integer
        description: ID da unidade
    responses:
      200:
        description: Lista de reports do step para a unidade
      404:
        description: Step ou unidade não encontrado
      403:
        description: Usuário não tem acesso à unidade
    """
    user = get_current_user()
    
    # Verificar se o step existe usando step_number
    step = Step.query.filter_by(step_number=step_number).first()
    if not step:
        return jsonify({'error': 'Step não encontrado'}), 404
    
    # Verificar se a unidade existe
    unit = Unit.query.get(unit_id)
    if not unit:
        return jsonify({'error': 'Unidade não encontrada'}), 404
    
    # Verificar se o usuário tem acesso à unidade (admin tem acesso a todas)
    if user.role != 'admin' and unit not in user.units:
        return jsonify({'error': 'Acesso negado a esta unidade'}), 403
    
    # Buscar reports que pertencem ao step E à unidade
    reports = Report.query.filter(
        Report.step_id == step.id,
        Report.units.any(Unit.id == unit_id)
    ).all()
    
    return jsonify({
        'step': step.to_dict(),
        'unit': unit.to_dict(),
        'reports': [report.to_dict(include_units=True) for report in reports]
    }), 200
