from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from app import db
from app.models import Report, Unit
from app.services.powerbi_service import PowerBIService
from app.middleware.auth import get_current_user, require_role

bp = Blueprint('reports', __name__)

@bp.route('', methods=['GET'])
@jwt_required()
def list_reports():
    """
    Listar reports disponíveis para o usuário
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    parameters:
      - in: query
        name: unit_id
        type: integer
        required: false
        description: Filtrar por unidade
    responses:
      200:
        description: Lista de reports
    """
    user = get_current_user()
    unit_id = request.args.get('unit_id', type=int)
    
    if user.role == 'admin':
        if unit_id:
            # Filtrar reports que pertencem à unidade específica
            unit = Unit.query.get_or_404(unit_id)
            reports = unit.reports
        else:
            # Todos os reports
            reports = Report.query.all()
    else:
        # Usuários normais veem apenas reports de suas unidades
        user_units = user.units
        if unit_id:
            # Verificar se o usuário tem acesso à unidade
            unit = Unit.query.get_or_404(unit_id)
            if unit not in user_units:
                return jsonify({'error': 'Acesso negado a esta unidade'}), 403
            reports = unit.reports
        else:
            # Buscar reports de todas as unidades do usuário
            reports = []
            seen_report_ids = set()
            for unit in user_units:
                for report in unit.reports:
                    if report.id not in seen_report_ids:
                        reports.append(report)
                        seen_report_ids.add(report.id)
    
    return jsonify([report.to_dict() for report in reports]), 200

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_report(id):
    """
    Obter detalhes de um report
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: Detalhes do report
      403:
        description: Acesso negado
      404:
        description: Report não encontrado
    """
    report = Report.query.get_or_404(id)
    user = get_current_user()
    
    # Verificar acesso - usuário precisa ter acesso a pelo menos uma das unidades do report
    if user.role != 'admin':
        user_unit_ids = {u.id for u in user.units}
        report_unit_ids = {u.id for u in report.units}
        if not user_unit_ids.intersection(report_unit_ids):
            return jsonify({'error': 'Acesso negado'}), 403
    
    return jsonify(report.to_dict(include_units=True)), 200

@bp.route('', methods=['POST'])
@jwt_required()
@require_role('admin')
def create_report():
    """
    Criar/registrar novo report (apenas admin)
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - unit_ids
            - report_id
            - workspace_id
            - name
          properties:
            unit_ids:
              type: array
              items:
                type: integer
              description: IDs das unidades associadas ao report
            report_id:
              type: string
              example: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            workspace_id:
              type: string
              example: "1a2b3c4d-5e6f-7890-abcd-ef0987654321"
            dataset_id:
              type: string
            name:
              type: string
            embed_url:
              type: string
            step_id:
              type: integer
              description: ID do bloco/step (opcional)
    responses:
      201:
        description: Report criado com sucesso
      400:
        description: Dados inválidos
    """
    data = request.get_json()
    
    required_fields = ['unit_ids', 'report_id', 'workspace_id', 'name']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Campos obrigatórios ausentes'}), 400
    
    # Verificar se unit_ids é uma lista
    if not isinstance(data['unit_ids'], list) or len(data['unit_ids']) == 0:
        return jsonify({'error': 'unit_ids deve ser um array não vazio'}), 400
    
    # Verificar se todas as unidades existem
    units = []
    for unit_id in data['unit_ids']:
        unit = Unit.query.get(unit_id)
        if not unit:
            return jsonify({'error': f'Unidade ID {unit_id} não encontrada'}), 404
        units.append(unit)
    
    # Verificar se report_id já existe
    if Report.query.filter_by(report_id=data['report_id']).first():
        return jsonify({'error': 'Report ID já existe'}), 409
    
    report = Report(
        report_id=data['report_id'],
        workspace_id=data['workspace_id'],
        dataset_id=data.get('dataset_id'),
        name=data['name'],
        embed_url=data.get('embed_url'),
        step_id=data.get('step_id')
    )
    
    # Associar unidades
    report.units.extend(units)
    
    db.session.add(report)
    db.session.commit()
    
    return jsonify(report.to_dict(include_units=True)), 201

@bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@require_role('admin')
def update_report(id):
    """
    Atualizar report (apenas admin)
    ---
    tags:
      - Reports
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
            embed_url:
              type: string
            dataset_id:
              type: string
    responses:
      200:
        description: Report atualizado
      404:
        description: Report não encontrado
    """
    report = Report.query.get_or_404(id)
    data = request.get_json()
    
    if data.get('name'):
        report.name = data['name']
    if 'embed_url' in data:
        report.embed_url = data['embed_url']
    if 'dataset_id' in data:
        report.dataset_id = data['dataset_id']
    
    db.session.commit()
    
    return jsonify(report.to_dict()), 200

@bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@require_role('admin')
def delete_report(id):
    """
    Deletar report (apenas admin)
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      204:
        description: Report deletado
      404:
        description: Report não encontrado
    """
    report = Report.query.get_or_404(id)
    
    db.session.delete(report)
    db.session.commit()
    
    return '', 204

@bp.route('/<int:id>/embed-config', methods=['GET'])
@jwt_required()
def get_embed_config(id):
    """
    Obter configuração completa para embed
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id
        type: integer
        required: true
      - in: query
        name: unit_id
        type: integer
        required: true
        description: ID da unidade selecionada
    responses:
      200:
        description: Configuração de embed
      400:
        description: Parâmetros inválidos
      403:
        description: Acesso negado
      404:
        description: Report não encontrado
    """
    report = Report.query.get_or_404(id)
    user = get_current_user()
    
    # Obter unit_id do query parameter
    unit_id = request.args.get('unit_id', type=int)
    if not unit_id:
        return jsonify({'error': 'Id da unidade é obrigatório'}), 400

    # Verificar acesso - checar se o usuário tem acesso à unidade especificada
    user_unit_ids = [u.id for u in user.units]
    if user.role != 'admin' and unit_id not in user_unit_ids:
        return jsonify({'error': 'Acesso negado a esta unidade'}), 403
    
    # Verificar se o report está disponível para a unidade
    report_unit_ids = [u.id for u in report.units]
    if unit_id not in report_unit_ids:
        return jsonify({'error': 'Report não disponível para esta unidade'}), 403

    try:
        pbi_service = PowerBIService()

        # Obter bi_filter_param da associação user-unit
        username = user.get_bi_filter_param(unit_id)
        if not username:
            return jsonify({'error': 'Nenhum filtro encontrado para esta combinação de usuário-unidade'}), 400

        # Roles fixo
        roles = ["rls_unidades"]

        # Obter configuração completa
        config = pbi_service.get_embed_config(
            workspace_id=report.workspace_id,
            report_id=report.report_id,
            username=username,
            roles=roles
        )

        return jsonify(config), 200

    except Exception as e:
        current_app.logger.error(f"Error getting embed config: {str(e)}")
        return jsonify({'error': 'Falha ao obter configuração de embed', 'details': str(e)}), 500


@bp.route('/workspace/<workspace_id>/list', methods=['GET'])
@jwt_required()
@require_role('admin')
def list_workspace_reports(workspace_id):
    """
    Listar todos os reports de um workspace do Power BI (apenas admin)
    Retorna apenas ID e nome de cada report
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    parameters:
      - in: path
        name: workspace_id
        type: string
        required: true
        description: ID do workspace do Power BI
    responses:
      200:
        description: Lista de reports com ID e nome
        schema:
          type: object
          properties:
            workspace_id:
              type: string
            reports:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                  name:
                    type: string
      500:
        description: Erro ao buscar reports
    """
    try:
        pbi_service = PowerBIService()
        reports_data = pbi_service.get_reports(workspace_id)
        
        # Retornar apenas ID e nome
        simplified_reports = [
            {
                'id': report['id'],
                'name': report['name']
            }
            for report in reports_data
        ]
        
        return jsonify({
            'workspace_id': workspace_id,
            'count': len(simplified_reports),
            'reports': simplified_reports
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error fetching workspace reports: {str(e)}")
        return jsonify({'error': 'Falha ao buscar reports do workspace', 'details': str(e)}), 500
