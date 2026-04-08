from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.middleware.auth import get_current_user
from app.models import Unit

bp = Blueprint('production', __name__)

# Configuração dos filtros disponíveis por unidade.
# A chave é o nome da unidade (Unit.name) exatamente como cadastrado no banco.
UNIT_FILTERS_CONFIG = {
    "SESI Educação Básica": {
        "has_business_filters": False,
        "business_filters": [],
        "measure_filters": {
            "default": [
                {"value": "matriculas", "label": "Matrículas"},
                {"value": "hora_aluno", "label": "Hora-aluno"},
            ]
        },
    },
    "SESI Saúde": {
        "has_business_filters": False,
        "business_filters": [],
        "measure_filters": {
            "default": [
                {"value": "consultas_exames", "label": "Consultas e exames"},
            ]
        },
    },
    "SENAI Educação Profissional e STI": {
        "has_business_filters": True,
        "business_filters": [
            {"value": "EP", "label": "Educação Profissional"},
            {"value": "STI", "label": "Serviços Técnicos e Tecnológicos"},
        ],
        "measure_filters": {
            "EP": [
                {"value": "matriculas", "label": "Matrículas"},
                {"value": "hora_aluno", "label": "Hora-aluno"},
            ],
            "STI": [
                {"value": "horas", "label": "Horas"},
                {"value": "servicos_metrologia", "label": "Serviços em Metrologia"},
            ],
        },
    },
}


@bp.route('/filters', methods=['GET'])
@jwt_required()
def get_filters():
    """
    Obter configuração de filtros disponíveis para a unidade do usuário logado
    ---
    tags:
      - Production
    security:
      - Bearer: []
    parameters:
      - in: query
        name: unit_id
        type: integer
        required: true
        description: ID da unidade para a qual os filtros serão retornados
    responses:
      200:
        description: Configuração de filtros da unidade
        schema:
          type: object
          properties:
            unit_id:
              type: integer
            unit_name:
              type: string
            has_business_filters:
              type: boolean
            business_filters:
              type: array
              items:
                type: object
                properties:
                  value:
                    type: string
                  label:
                    type: string
            measure_filters:
              type: object
              description: "Mapa de medidas disponíveis. Quando has_business_filters=true, é indexado pelo valor do filtro de negócio (ex.: EP, STI). Quando false, usa a chave 'default'."
      400:
        description: unit_id ausente ou inválido
      403:
        description: Usuário não tem acesso à unidade
      404:
        description: Unidade não encontrada ou sem configuração de filtros
    """
    unit_id = request.args.get('unit_id', type=int)
    if not unit_id:
        return jsonify({'error': 'unit_id é obrigatório'}), 400

    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    unit = Unit.query.get(unit_id)
    if not unit:
        return jsonify({'error': 'Unidade não encontrada'}), 404

    # Verificar se o usuário tem acesso a esta unidade (admin tem acesso a todas)
    if user.role != 'admin' and unit_id not in [u.id for u in user.units]:
        return jsonify({'error': 'Acesso negado a esta unidade'}), 403

    config = UNIT_FILTERS_CONFIG.get(unit.name)
    if not config:
        return jsonify({'error': f'Configuração de filtros não encontrada para a unidade "{unit.name}"'}), 404

    return jsonify({
        'unit_id': unit.id,
        'unit_name': unit.name,
        **config,
    }), 200
