from flask import Blueprint, jsonify, current_app, request
from flask_jwt_extended import jwt_required
from app.services.powerbi_service import PowerBIService

bp = Blueprint('external', __name__)

@bp.route('/sedics', methods=['GET'])
@jwt_required()
def get_sedics_report():
    """
    Obter configuração de embed para o relatório SEDICS
    ---
    tags:
      - External
    security:
      - Bearer: []
    responses:
      200:
        description: Configuração de embed do relatório SEDICS
      500:
        description: Erro ao obter configuração
    """
    workspace_id = "13bcf71a-8662-4a3c-af49-390ad878a554"
    report_id = "e58e4f9c-e153-4c24-a8a8-8b59aabe75d5"

    try:
        pbi_service = PowerBIService()

        config = pbi_service.get_embed_config(
            workspace_id=workspace_id,
            report_id=report_id,
        )

        return jsonify(config), 200

    except Exception as e:
        current_app.logger.error(f"Error getting SEDICS report config: {str(e)}")
        return jsonify({'error': 'Falha ao obter configuração do relatório SEDICS', 'details': str(e)}), 500


@bp.route('/embed', methods=['GET'])
@jwt_required()
def get_embed_report():
    """
    Obter configuração de embed para um relatório específico
    ---
    tags:
      - External
    security:
      - Bearer: []
    parameters:
      - in: query
        name: workspace_id
        type: string
        required: true
        description: ID do workspace do Power BI
      - in: query
        name: report_id
        type: string
        required: true
        description: ID do relatório do Power BI
      - in: query
        name: username
        type: string
        required: true
        description: Username para RLS
    responses:
      200:
        description: Configuração de embed do relatório
      400:
        description: Parâmetros obrigatórios ausentes
      500:
        description: Erro ao obter configuração
    """
    workspace_id = request.args.get('workspace_id')
    report_id = request.args.get('report_id')
    username = request.args.get('username')

    if not workspace_id or not report_id or not username:
        return jsonify({'error': 'workspace_id, report_id e username são obrigatórios'}), 400

    try:
        pbi_service = PowerBIService()

        config = pbi_service.get_embed_config(
            workspace_id=workspace_id,
            report_id=report_id,
            roles=['rls_unidades'],
            username=username
        )

        return jsonify(config), 200

    except Exception as e:
        current_app.logger.error(f"Error getting embed config: {str(e)}")
        return jsonify({'error': 'Falha ao obter configuração de embed', 'details': str(e)}), 500
