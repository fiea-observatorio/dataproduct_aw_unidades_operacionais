from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import and_, bindparam, case, func, or_, select, text

from app.dw_models import (
    dw_engine,
    fato_producao_ebdr,
    fato_producao_epdr,
    fato_producao_metaofertaeb,
    fato_producao_metaofertassi,
    fato_producao_metaofertasti,
    fato_producao_metaproducaoep,
    fato_producao_saudecomplementar,
    fato_producao_saudeocupacional,
)
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
                # {"value": "matriculas", "label": "Matrículas"},
                {"value": "hora_aluno", "label": "Hora-aluno"},
            ],
            "STI": [
                {"value": "horas", "label": "Horas"},
                {"value": "servico", "label": "Serviço"},
            ],
        },
    },
}


# Mapeamento username -> nomes reais em nm_unidade nas tabelas do DW.
# Os nomes variam entre tabelas (ex.: "Unidade Senai Poço" vs
# "Unidade Senai Poco Gustavo Paiva"), então listamos todas as variantes
# que devem bater via IN (...). Ainda não aplicado nos cálculos.
USER_UNIT_ALIASES = {
    "senai.poco": [
        "Unidade Senai Poço",
        "Unidade Senai Poco Gustavo Paiva",
        "Soluções Digitais Unidade Senai Poço",
    ],
    "sesi.senai.benedito": [
        "Unidade Sesi/senai Benedito Bentes",
        "Unidade Senai Benedito Bentes Carlos Guido Ferrario Lobo",
        "ESCOLA SESI BENEDITO BENTES CARLOS GUIDO FERRARIO LOBO",
    ],
    "sesi.senai.arapiraca": [
        "Unidade Sesi/senai Arapiraca",
        "Unidade Senai Arapiraca Jose Gomes Barbosa",
        2784,
    ],
    "sesi.centro": [
        "ESCOLA SESI CENTRO INDUSTRIAL ABELARDO LOPES",
        "Escola Sesi Cambona",
    ],
    "sesi.saude.cambona": [
        2781,
    ],
    "sesi.saude.tabuleiro": [2782],
}


# Mapeamento username -> nomes em `nm_unidade` na tabela
# dw.fato_producao_metaofertassi. Replica o passo "Coluna Condicional
# Adicionada" do Power Query (cod_unidade) — só que filtra direto pelo nome
# em vez de mapear pra código.
SSI_METAOFERTASSI_UNIDADES_BY_USER = {
    "sesi.senai.arapiraca": ["Unidade Sesi/senai Arapiraca"],
    "sesi.saude.cambona": ["Unidade Cambona Saúde"],
    "sesi.saude.tabuleiro": ["Unidade Sesi Tabuleiro"],
}

# Filtros do Power Query sobre a previsão SSI em dw.fato_producao_metaofertassi.
_SSI_PRODUTO_PREFIX = '103'
_SSI_NOME_PRODUTO_EXCLUIDOS = [
    'AULA DE RELAXAMENTO',
    'AULÃO DE DANÇA',
    'BLITZ POSTURAL',
    'CAFÉ DA MANHÃ COM NUTRICIONISTA',
    'GINCANAS CORPORATIVAS',
    'GINÁSTICA FUNCIONAL',
    'GINÁSTICA LABORAL',
    'PCMSO - PROGRAMA DE CONTROLE MÉDICO DE SAÚDE OCUPACIONAL',
    'PILATES SOLO',
    'PROFISSIONAL DE NÍVEL SUPERIOR/TÉCNICO',
    'QUICK MASSAGE',
    'YOGA E MEDITAÇÃO',
]


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

    if user not in unit.users:
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
    user = get_current_user()
    unit_aliases = USER_UNIT_ALIASES.get(user.username, []) if user else []
    print(f"Calculando EB Matrículas para usuário {user.username} com aliases de unidade: {unit_aliases}")

    with dw_engine.connect() as conn:
        meta_stmt = select(
            func.sum(fato_producao_metaofertaeb.c.qt_alunos)
        ).where(
            and_(
                fato_producao_metaofertaeb.c.cd_ofertaid.notin_(['9340', '9341']),
                fato_producao_metaofertaeb.c.nm_modalidade.in_(
                    ['Ensino Fundamental', 'Ensino Médio']
                ),
                fato_producao_metaofertaeb.c.nm_unidade.in_(unit_aliases),
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
                fato_producao_ebdr.c.cd_unidade.in_(unit_aliases),
            )
        )

        realizado = int(conn.execute(realizado_stmt).scalar() or 0)

    resultado = round((realizado / meta) * 100, 2) if meta else 0

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
      - eb_realizadohora = SUM(ebdr.nr_cargahoraria) onde
          YEAR(dt_inicial) = ano atual
      - eb_realizado_x_metahoras = realizado / meta

    Aplica os mesmos filtros de matrículas:
      - metaofertaeb: cd_ofertaid ∉ ('9340','9341'), nm_modalidade ∈ ('Ensino Fundamental','Ensino Médio')
      - ebdr: nm_curso ∈ lista fixa de cursos EB
    """
    user = get_current_user()
    unit_aliases = USER_UNIT_ALIASES.get(user.username, []) if user else []

    with dw_engine.connect() as conn:
        meta_stmt = select(
            func.sum(fato_producao_metaofertaeb.c.nr_producao)
        ).where(
            and_(
                fato_producao_metaofertaeb.c.cd_ofertaid.notin_(['9340', '9341']),
                fato_producao_metaofertaeb.c.nm_modalidade.in_(
                    ['Ensino Fundamental', 'Ensino Médio']
                ),
                fato_producao_metaofertaeb.c.nm_unidade.in_(unit_aliases),
            )
        )
        meta = int(conn.execute(meta_stmt).scalar() or 0)

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
            func.sum(fato_producao_ebdr.c.nr_cargahoraria)
        ).where(
            and_(
                func.extract("year", fato_producao_ebdr.c.dt_inicial) == current_year,
                fato_producao_ebdr.c.nm_curso.in_(cursos_ensino_medio + cursos_ensino_fundamental),
                fato_producao_ebdr.c.cd_unidade.in_(unit_aliases),
            )
        )

        realizado = int(conn.execute(realizado_stmt).scalar() or 0)

    resultado = round((realizado / meta) * 100, 2) if meta else 0

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
    user = get_current_user()
    unit_aliases = USER_UNIT_ALIASES.get(user.username, []) if user else []

    with dw_engine.connect() as conn:
        meta_stmt = select(
            func.sum(fato_producao_metaproducaoep.c.nr_horaalunomensalalocada)
        ).where(
            fato_producao_metaproducaoep.c.nm_unidade.in_(unit_aliases)
        )
        meta = int(conn.execute(meta_stmt).scalar() or 0)

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
                fato_producao_epdr.c.nm_unidade.in_(unit_aliases),
            )
        )
        realizado = int(conn.execute(realizado_stmt).scalar() or 0)

    resultado = round((realizado / meta) * 100, 2) if meta else 0

    return {
        'meta': meta,
        'realizado': realizado,
        'resultado': resultado,
        'year': current_year,
    }


def _calculate_ssi_consultas_exames():
    """Meta, realizado e resultado para SESI Saúde — Consultas e exames (SSI).

    Replica os cálculos em DAX:
      - ssi_meta = SUM(fato_producao_metaofertassi[nr_producao])
          Filtros replicados do Power Query:
            - cd_produto inicia com "103"
            - nm_produto ∉ (lista de exclusões do PQ)
            - nm_unidade ∈ (lista por usuário)
            - YEAR(dt_calendario) = ano vigente
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
    current_year = datetime.now().year

    user = get_current_user()
    unit_aliases = USER_UNIT_ALIASES.get(user.username, []) if user else []
    cd_filiais = [a for a in unit_aliases if isinstance(a, int)]
    unidades_metaofertassi = (
        SSI_METAOFERTASSI_UNIDADES_BY_USER.get(user.username, []) if user else []
    )

    print(f"Calculando SSI Consultas e Exames para usuário {user.username} com aliases de unidade: {unit_aliases}, cd_filiais: {cd_filiais}, unidades metaofertassi: {unidades_metaofertassi}")

    with dw_engine.connect() as conn:
        meta_stmt = select(
            func.sum(fato_producao_metaofertassi.c.nr_producao)
        ).where(
            and_(
                fato_producao_metaofertassi.c.cd_produto.like(f'{_SSI_PRODUTO_PREFIX}%'),
                fato_producao_metaofertassi.c.nm_produto.notin_(_SSI_NOME_PRODUTO_EXCLUIDOS),
                fato_producao_metaofertassi.c.nm_unidade.in_(unidades_metaofertassi),
                func.extract('year', fato_producao_metaofertassi.c.dt_calendario) == current_year,
            )
        )
        meta = int(conn.execute(meta_stmt).scalar() or 0)

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
                fato_producao_saudecomplementar.c.cd_filial.in_(cd_filiais),
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
                fato_producao_saudeocupacional.c.cd_filial.in_(cd_filiais),
            )
        )
        realizado_comp = conn.execute(complementar_stmt).scalar() or 0
        realizado_ocup = conn.execute(ocupacional_stmt).scalar() or 0

    realizado = int(realizado_comp + realizado_ocup)
    resultado = round((realizado / meta) * 100, 2) if meta else 0

    return {
        'meta': meta,
        'realizado': realizado,
        'resultado': resultado,
        'year': current_year,
    }


# Ofertas excluídas da meta STI conforme Power Query.
_STI_OFERTAID_EXCLUIDOS = ['9221', '9319', '9485']

# Cada medida agrupa um conjunto fixo de modalidades. As strings precisam
# bater em nm_naturezaprodutosuperior (meta) e nm_modalidade (realizado,
# derivado via CASE) — se algum vier 0, conferir os rótulos no DW.
_STI_MEDIDA_CONFIG = {
    'horas': {
        'un_medida': 'Horas',
        'modalidades': ['Consultoria', 'Soluções Digitais', 'Inovação e Empreendedorismo', 'Pesquisa'],
    },
    'servico': {
        'un_medida': 'Serviço',
        'modalidades': ['Metrologia'],
    },
}

# Realizado STI a partir de dw.fato_producao_stisgt. Replica o Power Query
# que normaliza casing das unidades (ds_unidade / nm_unidadecarteira) e
# deriva nm_modalidade / un_medida / nm_unidadeajustada. Soma
# qt_apropriadas (horas para não-Metrologia; nº de serviços para Metrologia).
# Recorte por YEAR(dt_apropriacao) para o ano vigente.
_STI_REALIZADO_SQL = text("""
WITH base AS (
    SELECT
        TRY_CAST(qt_apropriadas AS INT) AS qt_apropriadas,
        dt_apropriacao,
        CASE
            WHEN UPPER(nm_produtoregional) LIKE N'%HUB%'
                THEN N'Inovação e Empreendedorismo'
            WHEN UPPER(LTRIM(RTRIM(ds_produtolinha))) = N'METROLOGIA'
                THEN N'Metrologia'
            WHEN UPPER(LTRIM(RTRIM(ds_produtolinha))) = N'CONSULTORIA EM TECNOLOGIA'
                THEN N'Consultoria'
            WHEN UPPER(LTRIM(RTRIM(ds_produtolinha))) = N'SERVIÇOS COMPLEMENTARES'
                THEN N'Serviços Complementares'
            WHEN UPPER(LTRIM(RTRIM(ds_produtolinha))) = N'SERVIÇOS TÉCNICOS ESPECIALIZADOS'
                THEN N'Serviços Técnicos Especializados'
            WHEN UPPER(LTRIM(RTRIM(ds_produtolinha))) = N'PESQUISA'
                THEN N'Pesquisa'
            WHEN UPPER(LTRIM(RTRIM(nm_produtoregional))) IN (
                N'DESENVOLVIMENTO DE SISTEMAS COMPUTACIONAIS',
                N'DESENVOLVIMENTO DE SOFTWARES',
                N'IMPLANTAÇÃO DE FERRAMENTA DATA WAREHOUSE',
                N'MELHORIAS E DESENVOLVIMENTO SISTEMAS COMPUTACIONAIS',
                N'SOLUÇÕES DIGITAIS - CIÊNCIA DE DADOS',
                N'SOLUÇÕES DIGITAIS - LICENÇA DE USO DE SOFTWARE',
                N'SUPORTE TÉCNICO A SISTEMAS COMPUTACIONAIS'
            ) THEN N'Soluções Digitais'
            ELSE ds_produtolinha
        END AS nm_modalidade,
        ds_unidade,
        nm_unidadecarteira
    FROM dw.fato_producao_stisgt
),
ajustado AS (
    SELECT
        qt_apropriadas,
        dt_apropriacao,
        nm_modalidade,
        CASE WHEN nm_modalidade = N'Metrologia' THEN N'Serviço' ELSE N'Horas' END AS un_medida,
        CASE
            WHEN nm_modalidade = N'Metrologia' THEN
                CASE
                    WHEN nm_unidadecarteira IS NULL
                         OR LTRIM(RTRIM(nm_unidadecarteira)) = N''
                        THEN ds_unidade
                    ELSE nm_unidadecarteira
                END
            ELSE ds_unidade
        END AS nm_unidadeajustada
    FROM base
)
SELECT MONTH(dt_apropriacao) AS mes,
       nm_modalidade AS modalidade,
       COALESCE(SUM(qt_apropriadas), 0) AS soma
FROM ajustado
WHERE un_medida = :un_medida
  AND nm_modalidade IN :modalidades
  AND nm_unidadeajustada IN :unidades
  AND YEAR(dt_apropriacao) = :ano
GROUP BY MONTH(dt_apropriacao), nm_modalidade
ORDER BY MONTH(dt_apropriacao), nm_modalidade
""").bindparams(
    bindparam('modalidades', expanding=True),
    bindparam('unidades', expanding=True),
)


def _sti_meta_por_mes(un_medida, modalidades_db, unit_aliases_str, current_year):
    """Retorna {mes: soma} de nr_producao do meta STI agrupado por mês."""
    if not modalidades_db or not unit_aliases_str:
        return {}
    un_medida_expr = case(
        (fato_producao_metaofertasti.c.nm_naturezaprodutosuperior == 'Metrologia', 'Serviço'),
        else_='Horas',
    )
    mes_expr = func.extract('month', fato_producao_metaofertasti.c.dt_calendario)
    with dw_engine.connect() as conn:
        stmt = select(
            mes_expr.label('mes'),
            func.sum(fato_producao_metaofertasti.c.nr_producao).label('soma'),
        ).where(
            and_(
                fato_producao_metaofertasti.c.cd_ofertaid.notin_(_STI_OFERTAID_EXCLUIDOS),
                un_medida_expr == un_medida,
                fato_producao_metaofertasti.c.nm_naturezaprodutosuperior.in_(modalidades_db),
                fato_producao_metaofertasti.c.nm_unidade.in_(unit_aliases_str),
                func.extract('year', fato_producao_metaofertasti.c.dt_calendario) == current_year,
            )
        ).group_by(mes_expr).order_by(mes_expr)
        return {int(row.mes): float(row.soma or 0) for row in conn.execute(stmt)}


def _sti_realizado_por_mes_modalidade(un_medida, modalidades_db, unit_aliases_str, current_year):
    """Retorna {mes: {modalidade: soma}} de qt_apropriadas do realizado STI."""
    if not modalidades_db or not unit_aliases_str:
        return {}
    with dw_engine.connect() as conn:
        rows = conn.execute(_STI_REALIZADO_SQL, {
            'un_medida': un_medida,
            'modalidades': modalidades_db,
            'unidades': unit_aliases_str,
            'ano': current_year,
        }).fetchall()
        por_mes = {}
        for r in rows:
            por_mes.setdefault(int(r.mes), {})[r.modalidade] = float(r.soma or 0)
        return por_mes


def _calculate_sti(medida_key):
    """Meta, realizado e resultado STI por medida, com breakdown por mês.

    Medida Horas engloba Consultoria + Soluções Digitais + Inovação e
    Empreendedorismo. Medida Serviço engloba apenas Metrologia.
    """
    current_year = datetime.now().year

    user = get_current_user()
    unit_aliases = USER_UNIT_ALIASES.get(user.username, []) if user else []
    unit_aliases_str = [a for a in unit_aliases if isinstance(a, str)]

    cfg = _STI_MEDIDA_CONFIG[medida_key]
    un_medida = cfg['un_medida']
    modalidades_db = cfg['modalidades']

    meta_por_mes = _sti_meta_por_mes(un_medida, modalidades_db, unit_aliases_str, current_year)
    realizado_por_mes_mod = _sti_realizado_por_mes_modalidade(
        un_medida, modalidades_db, unit_aliases_str, current_year
    )

    meta_total = sum(meta_por_mes.values())
    realizado_total = sum(
        soma for por_mod in realizado_por_mes_mod.values() for soma in por_mod.values()
    )
    resultado = round((realizado_total / meta_total) * 100, 2) if meta_total else 0

    meses = []
    for mes in range(1, 13):
        por_mod = realizado_por_mes_mod.get(mes, {})
        meses.append({
            'mes': mes,
            'meta': int(round(meta_por_mes.get(mes, 0))),
            'realizado': int(round(sum(por_mod.values()))),
            'realizado_modalidades': {
                modalidade: int(round(por_mod.get(modalidade, 0)))
                for modalidade in modalidades_db
            },
        })

    return {
        'meta': int(round(meta_total)),
        'realizado': int(round(realizado_total)),
        'resultado': resultado,
        'year': current_year,
        'meses': meses,
    }


def _calculate_sti_horas():
    return _calculate_sti('horas')


def _calculate_sti_servico():
    return _calculate_sti('servico')


# Mapa de calculadoras por (unit_name, business_filter, measure).
# business_filter é None quando a unidade não tem filtro de negócio.
_SUMMARY_CALCULATORS = {
    ('SESI Educação Básica', None, 'matriculas'): _calculate_eb_matriculas,
    ('SESI Educação Básica', None, 'hora_aluno'): _calculate_eb_hora_aluno,
    ('SESI Saúde', None, 'consultas_exames'): _calculate_ssi_consultas_exames,
    ('SENAI Educação Profissional e STI', 'EP', 'hora_aluno'): _calculate_ep_hora_aluno,
    ('SENAI Educação Profissional e STI', 'STI', 'horas'): _calculate_sti_horas,
    ('SENAI Educação Profissional e STI', 'STI', 'servico'): _calculate_sti_servico,
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

    if user not in unit.users:
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
