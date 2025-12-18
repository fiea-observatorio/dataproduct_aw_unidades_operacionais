from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from app import db
from app.models import Report, Unit, AccessLog
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
        query = Report.query
        if unit_id:
            query = query.filter_by(unit_id=unit_id)
        reports = query.all()
    else:
        unit_ids = [u.id for u in user.units]
        query = Report.query.filter(Report.unit_id.in_(unit_ids))
        if unit_id:
            if unit_id not in unit_ids:
                return jsonify({'error': 'Access denied to this unit'}), 403
            query = query.filter_by(unit_id=unit_id)
        reports = query.all()
    
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
    
    # Verificar acesso
    if user.role != 'admin' and report.unit not in user.units:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(report.to_dict()), 200

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
            - unit_id
            - report_id
            - workspace_id
            - name
          properties:
            unit_id:
              type: integer
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
    responses:
      201:
        description: Report criado com sucesso
      400:
        description: Dados inválidos
    """
    data = request.get_json()
    
    required_fields = ['unit_id', 'report_id', 'workspace_id', 'name']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verificar se unidade existe
    unit = Unit.query.get_or_404(data['unit_id'])
    
    # Verificar se report_id já existe
    if Report.query.filter_by(report_id=data['report_id']).first():
        return jsonify({'error': 'Report ID already exists'}), 409
    
    report = Report(
        unit_id=data['unit_id'],
        report_id=data['report_id'],
        workspace_id=data['workspace_id'],
        dataset_id=data.get('dataset_id'),
        name=data['name'],
        embed_url=data.get('embed_url')
    )
    
    db.session.add(report)
    db.session.commit()
    
    return jsonify(report.to_dict()), 201

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

@bp.route('/<int:id>/embed-token', methods=['POST'])
@jwt_required()
def generate_embed_token(id):
    """
    Gerar embed token para um report
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
            roles:
              type: array
              items:
                type: string
              example: ["SalesManager"]
    responses:
      200:
        description: Token gerado com sucesso
      403:
        description: Acesso negado
      404:
        description: Report não encontrado
    """
    report = Report.query.get_or_404(id)
    user = get_current_user()
    
    # Verificar acesso
    if user.role != 'admin' and report.unit not in user.units:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        pbi_service = PowerBIService()
        
        # Obter roles do body (para RLS)
        data = request.get_json() or {}
        roles = data.get('roles', [])
        
        # Gerar token com RLS baseado no username
        token_data = pbi_service.generate_embed_token(
            workspace_id=report.workspace_id,
            report_id=report.report_id,
            dataset_ids=[report.dataset_id] if report.dataset_id else None,
            username=user.username if roles else None,
            roles=roles if roles else None
        )
        
        # Registrar acesso
        access_log = AccessLog(
            user_id=user.id,
            report_id=report.id,
            action='embed_token_generated',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(access_log)
        db.session.commit()
        
        return jsonify(token_data), 200
    
    except Exception as e:
        current_app.logger.error(f"Error generating embed token: {str(e)}")
        return jsonify({'error': 'Failed to generate embed token', 'details': str(e)}), 500

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
        name: roles
        type: string
        required: false
        description: Roles para RLS (separados por vírgula)
    responses:
      200:
        description: Configuração de embed
      403:
        description: Acesso negado
      404:
        description: Report não encontrado
    """
    report = Report.query.get_or_404(id)
    user = get_current_user()
    
    # Verificar acesso
    if user.role != 'admin' and report.unit not in user.units:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        pbi_service = PowerBIService()
        
        # Obter roles da query string
        roles_str = request.args.get('roles', '')
        roles = [r.strip() for r in roles_str.split(',') if r.strip()] if roles_str else []
        
        # Obter configuração completa
        config = pbi_service.get_embed_config(
            workspace_id=report.workspace_id,
            report_id=report.report_id,
            username=user.username if roles else None,
            roles=roles if roles else None
        )
        
        # Registrar acesso
        access_log = AccessLog(
            user_id=user.id,
            report_id=report.id,
            action='view',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(access_log)
        db.session.commit()
        
        return jsonify(config), 200
    
    except Exception as e:
        current_app.logger.error(f"Error getting embed config: {str(e)}")
        return jsonify({'error': 'Failed to get embed configuration', 'details': str(e)}), 500

@bp.route('/sync/<workspace_id>', methods=['POST'])
@jwt_required()
@require_role('admin')
def sync_reports(workspace_id):
    """
    Sincronizar reports de um workspace (apenas admin)
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
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - unit_id
          properties:
            unit_id:
              type: integer
              description: ID da unidade para associar os reports
    responses:
      200:
        description: Reports sincronizados
      404:
        description: Unidade não encontrada
    """
    data = request.get_json()
    
    if not data or not data.get('unit_id'):
        return jsonify({'error': 'unit_id is required'}), 400
    
    unit = Unit.query.get_or_404(data['unit_id'])
    
    try:
        pbi_service = PowerBIService()
        reports_data = pbi_service.sync_reports_from_workspace(workspace_id)
        
        created = 0
        updated = 0
        
        for report_data in reports_data:
            existing_report = Report.query.filter_by(report_id=report_data['report_id']).first()
            
            if existing_report:
                # Atualizar
                existing_report.name = report_data['name']
                existing_report.embed_url = report_data['embed_url']
                existing_report.dataset_id = report_data['dataset_id']
                updated += 1
            else:
                # Criar novo
                new_report = Report(
                    unit_id=unit.id,
                    **report_data
                )
                db.session.add(new_report)
                created += 1
        
        db.session.commit()
        
        return jsonify({
            'message': 'Reports synchronized successfully',
            'created': created,
            'updated': updated
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Error syncing reports: {str(e)}")
        return jsonify({'error': 'Failed to sync reports', 'details': str(e)}), 500
