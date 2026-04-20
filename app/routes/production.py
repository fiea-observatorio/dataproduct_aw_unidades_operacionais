from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import and_, func, or_, select

from app.dw_models import (
    dw_engine,
    fato_producao_ebdr,
    fato_producao_epdr,
    fato_producao_metaofertaeb,
    fato_producao_metaofertasti,
    fato_producao_metaproducaoep,
    fato_producao_saudecomplementar,
    fato_producao_saudeocupacional,
)
from app.middleware.auth import get_current_user
from app.models import Unit
from app.services.solucao360_service import sum_previsao_ssi_producao

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
                {"value": "consultoria", "label": "Consultoria"},
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


def _calculate_eb_matriculas():
    """Meta, realizado e resultado para SESI Educação Básica — Matrículas.

    Replica o cálculo em DAX:
      - eb_meta = SUM(metaofertaeb.qt_alunos) / 12
      - eb_realizado2 = DISTINCTCOUNT(ebdr.nr_matricula) onde
          YEAR(dt_inicial) = ano atual
      - eb_resultado = realizado / meta

    Aplica os filtros do Power Query sobre metaofertaeb:
      - cd_ofertaid ∉ ('9340', '9341')
      - nm_modalidade ∈ ('Ensino Fundamental', 'Ensino Médio')
    """
    with dw_engine.connect() as conn:
        meta_stmt = select(
            func.sum(fato_producao_metaofertaeb.c.qt_alunos)
        ).where(
            and_(
                fato_producao_metaofertaeb.c.cd_ofertaid.notin_(['9340', '9341']),
                fato_producao_metaofertaeb.c.nm_modalidade.in_(
                    ['Ensino Fundamental', 'Ensino Médio']
                ),
            )
        )
        total_alunos = conn.execute(meta_stmt).scalar() or 0
        meta = int(total_alunos / 12)

        current_year = datetime.now().year

        cursos_ensino_medio = [
            "Ensino Médio - Linguagens+Humanas - Design e Cultura Maker",
            "Ensino Médio - Matemática+Humanas+Linguagens - Análise de Dados e Programação",
            "Novo Ensino Médio - Formação Geral Básica",
            "Novo Ensino Médio - Matemática",
            "Novo Ensino Médio - Ciências da Natureza",
            "Ensino Médio - Matemática+Natureza - Biotecnologia e Saúde",
            "Novo Ensino Médio - Formação Técnica e Profissional",
        ]

        cursos_ensino_fundamental = [
            "Ensino Fundamental - Anos Finais",
            "Ensino Fundamental - Anos Iniciais",
        ]

        realizado_stmt = select(
            func.count(func.distinct(fato_producao_ebdr.c.nr_matricula))
        ).where(
            and_(
                func.extract("year", fato_producao_ebdr.c.dt_inicial) == current_year,
                fato_producao_ebdr.c.nm_curso.in_(cursos_ensino_medio + cursos_ensino_fundamental),
            )
        )

        realizado = conn.execute(realizado_stmt).scalar() or 0

    resultado = (realizado / meta) if meta else 0

    return {
        'meta': meta,
        'realizado': realizado,
        'resultado': resultado,
        'year': current_year,
    }


def _calculate_eb_hora_aluno():
    """Meta, realizado e resultado para SESI Educação Básica — Hora-aluno.

    Replica o cálculo em DAX:
      - eb_metahoras = SUM(metaofertaeb.nr_producao)
      - eb_realizadohora = SUM(ebdr.nr_carga_horaria) onde
          YEAR(dt_inicial) = ano atual
      - eb_realizado_x_metahoras = realizado / meta

    Aplica os mesmos filtros de matrículas:
      - metaofertaeb: cd_ofertaid ∉ ('9340','9341'), nm_modalidade ∈ ('Ensino Fundamental','Ensino Médio')
      - ebdr: nm_curso ∈ lista fixa de cursos EB
    """
    with dw_engine.connect() as conn:
        meta_stmt = select(
            func.sum(fato_producao_metaofertaeb.c.nr_producao)
        ).where(
            and_(
                fato_producao_metaofertaeb.c.cd_ofertaid.notin_(['9340', '9341']),
                fato_producao_metaofertaeb.c.nm_modalidade.in_(
                    ['Ensino Fundamental', 'Ensino Médio']
                ),
            )
        )
        meta = conn.execute(meta_stmt).scalar() or 0

        current_year = datetime.now().year

        cursos_ensino_medio = [
            "Ensino Médio - Linguagens+Humanas - Design e Cultura Maker",
            "Ensino Médio - Matemática+Humanas+Linguagens - Análise de Dados e Programação",
            "Novo Ensino Médio - Formação Geral Básica",
            "Novo Ensino Médio - Matemática",
            "Novo Ensino Médio - Ciências da Natureza",
            "Ensino Médio - Matemática+Natureza - Biotecnologia e Saúde",
            "Novo Ensino Médio - Formação Técnica e Profissional",
        ]

        cursos_ensino_fundamental = [
            "Ensino Fundamental - Anos Finais",
            "Ensino Fundamental - Anos Iniciais",
        ]

        realizado_stmt = select(
            func.sum(fato_producao_ebdr.c.nr_carga_horaria)
        ).where(
            and_(
                func.extract("year", fato_producao_ebdr.c.dt_inicial) == current_year,
                fato_producao_ebdr.c.nm_curso.in_(cursos_ensino_medio + cursos_ensino_fundamental),
            )
        )

        realizado = conn.execute(realizado_stmt).scalar() or 0

    resultado = (realizado / meta) if meta else 0

    return {
        'meta': meta,
        'realizado': realizado,
        'resultado': resultado,
        'year': current_year,
    }


def _calculate_ep_hora_aluno():
    """Meta, realizado e resultado para SENAI Educação Profissional (EP) — Hora-aluno.

    Replica o cálculo em DAX:
      - ep_meta = SUM(metaproducaoep.nr_horaalunomensalalocada)
      - ep_realizado = SUM(epdr.nr_cargahoraria) onde YEAR(dt_data) = ano vigente
      - ep_realizado_x_meta = realizado / meta

    Aplica os filtros do Power Query sobre epdr:
      - nm_unidade ∉ ('Cep - Jackson Monteiro Ferreira', 'Cep - Napoleão Barbosa')
      - dt_inicial > 2022-12-31
    """
    with dw_engine.connect() as conn:
        meta_stmt = select(
            func.sum(fato_producao_metaproducaoep.c.nr_horaalunomensalalocada)
        )
        meta = conn.execute(meta_stmt).scalar() or 0

        current_year = datetime.now().year
        realizado_stmt = select(
            func.sum(fato_producao_epdr.c.nr_cargahoraria)
        ).where(
            and_(
                func.extract('year', fato_producao_epdr.c.dt_data) == current_year,
                fato_producao_epdr.c.nm_unidade.notin_([
                    'Cep - Jackson Monteiro Ferreira',
                    'Cep - Napoleão Barbosa',
                ]),
                fato_producao_epdr.c.dt_inicial > datetime(2022, 12, 31).date(),
            )
        )
        realizado = conn.execute(realizado_stmt).scalar() or 0

    resultado = (realizado / meta) if meta else 0

    return {
        'meta': meta,
        'realizado': realizado,
        'resultado': resultado,
        'year': current_year,
    }


def _calculate_ssi_consultas_exames():
    """Meta, realizado e resultado para SESI Saúde — Consultas e exames (SSI).

    Replica os cálculos em DAX:
      - ssi_meta = SUM(fato_previsaossi360[Producao])
          A tabela fato_previsaossi360 vem da API Solução 360 (fonte de dados
          CDS_RELORC_OFERTA_004). Aplica-se o filtro do Power Query:
            - Produto inicia com "103"
            - NomeProduto ∉ (lista de exclusões do PQ)
          Soma todas as colunas Producao{Mês} já com os filtros aplicados.
      - ssi_realizado = SUM(producao_ssi_real[qt_qtde]) onde
          producao_ssi_real = UNION(saudecomplementar, saudeocupacional)
          Filtros replicados do Power Query:
            saudecomplementar: st_status='LANCADO',
              nm_item ∉ ('PRE-CONSULTA', 'VACINA H1N1 MONODOSE - 2023'/2024/2025),
              nk_idlanc IS NOT NULL
            saudeocupacional: st_status='LANCADO',
              nm_item != 'PRE-CONSULTA', nk_idlanc IS NOT NULL
          Recorte pelo ano vigente via YEAR(dt_data) — replica o contexto do
          dashboard, que exibe sempre o ano corrente.
      - resultado = realizado / meta (0 quando meta vazia)
    """
    meta = sum_previsao_ssi_producao() or 0
    current_year = datetime.now().year

    with dw_engine.connect() as conn:
        complementar_stmt = select(
            func.sum(fato_producao_saudecomplementar.c.qt_qtde)
        ).where(
            and_(
                fato_producao_saudecomplementar.c.st_status == 'LANCADO',
                fato_producao_saudecomplementar.c.nm_item.notin_([
                    'PRE-CONSULTA',
                    'VACINA H1N1 MONODOSE - 2023',
                    'VACINA H1N1 MONODOSE - 2024',
                    'VACINA H1N1 MONODOSE - 2025',
                ]),
                fato_producao_saudecomplementar.c.nk_idlanc.isnot(None),
                func.extract('year', fato_producao_saudecomplementar.c.dt_data) == current_year,
            )
        )
        ocupacional_stmt = select(
            func.sum(fato_producao_saudeocupacional.c.qt_qtde)
        ).where(
            and_(
                fato_producao_saudeocupacional.c.st_status == 'LANCADO',
                fato_producao_saudeocupacional.c.nm_item != 'PRE-CONSULTA',
                fato_producao_saudeocupacional.c.nk_idlanc.isnot(None),
                func.extract('year', fato_producao_saudeocupacional.c.dt_data) == current_year,
            )
        )
        realizado_comp = conn.execute(complementar_stmt).scalar() or 0
        realizado_ocup = conn.execute(ocupacional_stmt).scalar() or 0

    realizado = realizado_comp + realizado_ocup
    resultado = (realizado / meta) if meta else 0

    return {
        'meta': meta,
        'realizado': realizado,
        'resultado': resultado,
        'year': current_year,
    }


def _sti_meta(natureza):
    """Soma da meta STI por natureza (Consultoria / Metrologia).

    sti_meta = SUM(fato_producao_metaofertasti[nr_producao]) onde
    nm_naturezaprodutosuperior = natureza.
    """
    with dw_engine.connect() as conn:
        stmt = select(
            func.sum(fato_producao_metaofertasti.c.nr_producao)
        ).where(
            fato_producao_metaofertasti.c.nm_naturezaprodutosuperior == natureza
        )
        return conn.execute(stmt).scalar() or 0


# Realizado e resultado do STI dependem da planilha SharePoint
# (relatorio_produção.xlsx em sistemafiea.sharepoint.com/sites/observatorioregional),
# que ainda não está integrada — devolvemos placeholder até a fonte estar disponível.
_STI_REALIZADO_PLACEHOLDER = 'Em construção'


def _calculate_sti_consultoria():
    """STI Consultoria — apenas meta; realizado pendente de integração SharePoint."""
    return {
        'meta': _sti_meta('Consultoria'),
        'realizado': _STI_REALIZADO_PLACEHOLDER,
        'resultado': _STI_REALIZADO_PLACEHOLDER,
        'year': datetime.now().year,
    }


def _calculate_sti_servicos_metrologia():
    """STI Metrologia — apenas meta; realizado pendente de integração SharePoint."""
    return {
        'meta': _sti_meta('Metrologia'),
        'realizado': _STI_REALIZADO_PLACEHOLDER,
        'resultado': _STI_REALIZADO_PLACEHOLDER,
        'year': datetime.now().year,
    }


# Mapa de calculadoras por (unit_name, business_filter, measure).
# business_filter é None quando a unidade não tem filtro de negócio.
_SUMMARY_CALCULATORS = {
    ('SESI Educação Básica', None, 'matriculas'): _calculate_eb_matriculas,
    ('SESI Educação Básica', None, 'hora_aluno'): _calculate_eb_hora_aluno,
    ('SESI Saúde', None, 'consultas_exames'): _calculate_ssi_consultas_exames,
    ('SENAI Educação Profissional e STI', 'EP', 'hora_aluno'): _calculate_ep_hora_aluno,
    ('SENAI Educação Profissional e STI', 'STI', 'consultoria'): _calculate_sti_consultoria,
    ('SENAI Educação Profissional e STI', 'STI', 'servicos_metrologia'): _calculate_sti_servicos_metrologia,
}


@bp.route('/summary', methods=['GET'])
@jwt_required()
def get_production_summary():
    """
    Obter resumo de produção (meta, realizado, resultado) por unidade e medida
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
      - in: query
        name: measure
        type: string
        required: true
        description: "Valor do filtro de medida (ex.: matriculas, hora_aluno)"
      - in: query
        name: business_filter
        type: string
        required: false
        description: "Valor do filtro de negócio quando a unidade exigir (ex.: EP, STI)"
    responses:
      200:
        description: Meta, realizado e resultado calculados
        schema:
          type: object
          properties:
            unit_id:
              type: integer
            unit_name:
              type: string
            business_filter:
              type: string
            measure:
              type: string
            meta:
              type: number
            realizado:
              type: number
            resultado:
              type: number
            year:
              type: integer
      400:
        description: Parâmetros inválidos
      403:
        description: Usuário não tem acesso à unidade
      404:
        description: Unidade não encontrada
      501:
        description: Combinação de unidade/medida ainda não implementada
    """
    unit_id = request.args.get('unit_id', type=int)
    measure = request.args.get('measure')
    business_filter = request.args.get('business_filter')

    if not unit_id:
        return jsonify({'error': 'unit_id é obrigatório'}), 400
    if not measure:
        return jsonify({'error': 'measure é obrigatório'}), 400

    user = get_current_user()
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    unit = Unit.query.get(unit_id)
    if not unit:
        return jsonify({'error': 'Unidade não encontrada'}), 404

    if user.role != 'admin' and unit_id not in [u.id for u in user.units]:
        return jsonify({'error': 'Acesso negado a esta unidade'}), 403

    config = UNIT_FILTERS_CONFIG.get(unit.name)
    if not config:
        return jsonify({'error': f'Configuração de filtros não encontrada para a unidade "{unit.name}"'}), 404

    if config['has_business_filters']:
        if not business_filter:
            return jsonify({'error': 'business_filter é obrigatório para esta unidade'}), 400
        valid_values = {f['value'] for f in config['business_filters']}
        if business_filter not in valid_values:
            return jsonify({'error': f'business_filter inválido para esta unidade: {business_filter}'}), 400
        available_measures = config['measure_filters'].get(business_filter, [])
    else:
        business_filter = None
        available_measures = config['measure_filters'].get('default', [])

    if measure not in {m['value'] for m in available_measures}:
        return jsonify({'error': f'measure inválido para esta unidade/filtro: {measure}'}), 400

    calculator = _SUMMARY_CALCULATORS.get((unit.name, business_filter, measure))
    if not calculator:
        return jsonify({
            'error': 'Cálculo ainda não implementado para esta combinação',
            'unit_name': unit.name,
            'business_filter': business_filter,
            'measure': measure,
        }), 501

    result = calculator()

    return jsonify({
        'unit_id': unit.id,
        'unit_name': unit.name,
        'business_filter': business_filter,
        'measure': measure,
        **result,
    }), 200
