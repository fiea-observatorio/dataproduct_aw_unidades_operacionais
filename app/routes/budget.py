from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import and_, func, select

from app.dw_models import dw_engine, fato_orcamento_lancamentos
from app.middleware.auth import get_current_user
from app.models import Unit

bp = Blueprint('budget', __name__)

# cd_empresaid em dw.fato_orcamento_lancamentos. Conferido no DW
# (backup_tb.dim_orcamento_filial e filiais da saúde): 1 = SENAI, 2 = SESI.
_EMPRESA_SENAI = '1'
_EMPRESA_SESI = '2'

# Empresa dona de cada negócio (Unit.name). Unidades integradas SESI/SENAI
# lançam nas duas empresas com o mesmo código de unidade organizacional, então
# a empresa é o que separa os lançamentos de cada negócio.
UNIT_EMPRESA = {
    'SESI Educação Básica': _EMPRESA_SESI,
    'SESI Saúde': _EMPRESA_SESI,
    'SENAI Educação Profissional e STI': _EMPRESA_SENAI,
}

# username -> cd_unidadeorganizacional. Nomes conferidos em
# dw.dim_pessoas_funcionarios.
USER_UNIDADE_ORGANIZACIONAL = {
    'sesi.senai.arapiraca': '040401',  # UNID. INT. SESI/SENAI ARAPIRACA
    'senai.poco': '041001',  # UNIDADE SENAI POÇO
    'sesi.saude.cambona': '040201',  # UNIDADE SESI CAMBONA SAÚDE
    'sesi.centro': '040801',  # ESCOLA SESI CENTRO
    'sesi.senai.benedito': '040901',  # UNID. INT. SESI/SENAI BENEDITO BENTES
    'sesi.saude.tabuleiro': '040501',  # UNIDADE SESI TABULEIRO
}

# Contas contábeis de Receita de Serviço.
_RECEITA_SERVICO_CONTA_PREFIX = '410104'


def _calculate_receita_servico(cd_empresaid, cd_unidadeorganizacional, ano):
    """Meta e realizado da Receita de Serviço de uma empresa + unidade.

    Sobre dw.fato_orcamento_lancamentos, filtrando:
      - cd_contacontabil inicia com '410104' (todas as contas somadas)
      - tp_periodicidade = 'Receita'
      - nr_ano = ano
      - cd_empresaid e cd_unidadeorganizacional em conjunto
    Calcula:
      - meta = SUM(vl_revisado)
      - realizado = SUM(vl_real)
      - resultado = realizado / meta (0 quando meta vazia)
    """
    t = fato_orcamento_lancamentos

    with dw_engine.connect() as conn:
        row = conn.execute(
            select(
                func.sum(t.c.vl_revisado).label('meta'),
                func.sum(t.c.vl_real).label('realizado'),
            ).where(
                and_(
                    t.c.cd_contacontabil.like(f'{_RECEITA_SERVICO_CONTA_PREFIX}%'),
                    t.c.tp_periodicidade == 'Receita',
                    t.c.nr_ano == ano,
                    t.c.cd_empresaid == cd_empresaid,
                    t.c.cd_unidadeorganizacional == cd_unidadeorganizacional,
                )
            )
        ).one()

    meta = round(float(row.meta or 0), 2)
    realizado = round(float(row.realizado or 0), 2)
    resultado = round((realizado / meta) * 100, 2) if meta else 0

    return {
        'meta': meta,
        'realizado': realizado,
        'resultado': resultado,
        'year': ano,
    }


@bp.route('/service-revenue', methods=['GET'])
@jwt_required()
def get_service_revenue():
    """
    Obter meta e realizado da Receita de Serviço da unidade do usuário logado
    ---
    tags:
      - Budget
    security:
      - Bearer: []
    parameters:
      - in: query
        name: unit_id
        type: integer
        required: true
        description: ID do negócio (define a empresa SESI/SENAI dos lançamentos)
    responses:
      200:
        description: Meta, realizado e resultado da Receita de Serviço no ano vigente
        schema:
          type: object
          properties:
            unit_id:
              type: integer
            unit_name:
              type: string
            meta:
              type: number
              description: SUM(vl_revisado), em R$
            realizado:
              type: number
              description: SUM(vl_real), em R$
            resultado:
              type: number
              description: realizado / meta, em %
            year:
              type: integer
      400:
        description: unit_id ausente
      403:
        description: Usuário não tem acesso à unidade
      404:
        description: Unidade não encontrada ou sem mapeamento de orçamento
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

    if user not in unit.users:
        return jsonify({'error': 'Acesso negado a esta unidade'}), 403

    cd_empresaid = UNIT_EMPRESA.get(unit.name)
    if not cd_empresaid:
        return jsonify({'error': f'Empresa não mapeada para a unidade "{unit.name}"'}), 404

    cd_unidadeorganizacional = USER_UNIDADE_ORGANIZACIONAL.get(user.username)
    if not cd_unidadeorganizacional:
        return jsonify({'error': 'Unidade organizacional não mapeada para o usuário'}), 404

    result = _calculate_receita_servico(
        cd_empresaid, cd_unidadeorganizacional, datetime.now().year
    )

    return jsonify({
        'unit_id': unit.id,
        'unit_name': unit.name,
        **result,
    }), 200
