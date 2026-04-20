import os
from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, create_engine

load_dotenv()

dw_engine = create_engine(os.getenv("DATABASE_URL_DW"))

dw_metadata = MetaData(schema="dw")

# Colunas: cd_filial, cd_unidade, dt_matricula, dt_inicial, dt_final, nr_matricula,
#   cd_turma, nr_matricula_tuma, cd_centro, cd_curso, nm_curso, cd_modalidade_curso,
#   nm_modalidade, nm_mediacao, nm_situacao_matricula, nm_financiamento, nr_carga_horaria,
#   nm_periodo_letivo, nm_industria, dt_aula, nm_aluno, nm_fonte, dt_carga
fato_producao_ebdr = Table(
    'fato_producao_ebdr',
    dw_metadata,
    autoload_with=dw_engine
)

# Colunas conhecidas: cd_ofertaid, nm_programaestrategico, dt_calendario,
#   nm_modalidade, qt_alunos
fato_producao_metaofertaeb = Table(
    'fato_producao_metaofertaeb',
    dw_metadata,
    autoload_with=dw_engine
)

# Colunas: cd_producaoid, nm_unidade, nm_area, nm_curso, nm_modalidade, nm_turma,
#   nm_municipio, cd_turma, tp_matricula, nm_programaestrategico, dt_inicio, dt_termino,
#   nr_horaalunototal, dt_mesreferencia, nr_horaalunomensalalocada, dt_carga
fato_producao_metaproducaoep = Table(
    'fato_producao_metaproducaoep',
    dw_metadata,
    autoload_with=dw_engine
)

# Colunas: cd_filial, nm_unidade, dt_matricula, dt_inicial, dt_final, nr_matricula,
#   cd_turma, cd_centro, cd_curso, nm_curso, cd_modalidadecurso, nm_modalidade,
#   nm_financiamento, nr_cargahoraria, nr_periodoletivo, nm_industria, nm_aluno, nm_fonte,
#   cd_area, nm_area, nm_mediacaoturma, nm_mediacaosolucaointegradora, st_matricula,
#   st_resultado, cd_financiamento, nr_cargahorariacurso, cd_matriculaturma, dt_data,
#   ds_aplicacaooferta, cd_cnpjempatendida, dt_carga
fato_producao_epdr = Table(
    'fato_producao_epdr',
    dw_metadata,
    autoload_with=dw_engine
)

# Colunas: cd_ofertaid, nm_unidade, cd_produto, nm_produto, nm_origemoferta, fl_avender,
#   fl_producao, nr_producaototal, dt_inicialano, dt_finalano, dt_iniciogeral, dt_finalgeral,
#   tp_mediacao, nm_situacaooferta, tp_financiamento, nm_programaestrategico, nm_municipio,
#   vl_oferta, vl_custotoalano, vl_receitatotalano, vl_custototal, vl_receitatotal,
#   pc_margemcontribuicao, vl_resultado, dt_calendario, vl_receita, nr_producao, dt_carga
fato_producao_metaofertassi = Table(
    'fato_producao_metaofertassi',
    dw_metadata,
    autoload_with=dw_engine
)

# Colunas: sk_saudecomplementar, nk_idlanc, cd_cnpj, nm_razaosocial, nr_telefone, nm_email,
#   cd_convenio, cd_api, nm_item, cd_filial, cd_unidadeorg, cd_centro, cd_contabil,
#   nm_convenio, nm_paciente, cd_cpf, dt_nasc, nm_postocoleta, qt_qtde, vl_valor,
#   nr_honorarioexecutante, nr_honorariosolicitante, nm_responsavel, nr_atend, dt_data,
#   nr_medicoexecutante, nm_medicoexecutante, nr_medicosolicitante, nm_medico_solicitante,
#   tp_type, cd_unidade, cd_vendaid, fl_pendente, st_status, tp_convenio, nm_obsatend,
#   nr_graurisco, ds_portesistemafiea, nr_porteestabelecimento, nr_portereceita,
#   fl_contribuinte, fl_industria, qt_empregados, dt_carga, nm_sindicato, nm_entidade,
#   cd_entidade, nm_classe, nm_produto, nm_plano, nm_naturezaproduto
fato_producao_saudecomplementar = Table(
    'fato_producao_saudecomplementar',
    dw_metadata,
    autoload_with=dw_engine
)

# Colunas: sk_saudeocupacional, nk_idlanc, cd_cnpj, nm_razaosocial, nr_telefone, nm_email,
#   cd_convenio, cd_api, nm_item, cd_filial, cd_unidadeorg, cd_centro, cd_contabil,
#   nm_convenio, nm_paciente, cd_cpf, dt_nasc, nm_postocoleta, qt_qtde, vl_valor,
#   nr_honorarioexecutante, nr_honorariosolicitante, nm_responsavel, nr_atend, dt_data,
#   nr_medicoexecutante, nm_medicoexecutante, nr_medicosolicitante, nm_medico_solicitante,
#   tp_type, cd_unidade, cd_vendaid, fl_pendente, st_status, tp_convenio, nm_obsatend,
#   nr_graurisco, ds_portesistemafiea, nr_porteestabelecimento, nr_portereceita,
#   fl_contribuinte, fl_industria, qt_empregados, dt_carga, cd_sindicato,
#   nm_razaosocialsindicato, nm_entidade, cd_entidade, nm_classe, nm_produto, nm_plano,
#   nm_naturezaproduto
fato_producao_saudeocupacional = Table(
    'fato_producao_saudeocupacional',
    dw_metadata,
    autoload_with=dw_engine
)

# Colunas: cd_ofertaid, nm_unidade, cd_produto, nm_produto, nm_origemoferta, fl_avender,
#   fl_producao, fl_atendimento, nr_producaototal, dt_inicialano, dt_finalano, dt_iniciogeral,
#   dt_finalgeral, tp_mediacao, nm_situacaooferta, tp_financiamento, nm_programaestrategico,
#   nm_municipio, vl_oferta, vl_custotoalano, vl_receitatotalano, vl_custototal,
#   vl_receitatotal, pc_margemcontribuicao, vl_resultado, cd_naturezaproduto,
#   nm_naturezaproduto, cd_naturezaprodutosuperior, nm_naturezaprodutosuperior,
#   dt_calendario, vl_receita, nr_producao, nr_atendimento, dt_carga
fato_producao_metaofertasti = Table(
    'fato_producao_metaofertasti',
    dw_metadata,
    autoload_with=dw_engine
)

# Colunas: cd_idatendimento, cd_idproposta, cd_cpfcnpj, nm_tituloatendimento,
#   vl_totalfaturamento, nm_fontepagadora, ds_produtocategoria, ds_produtolinha, nm_produto,
#   dt_apropriacao, qt_dehorasensaioscalibracoes, nm_unidadeoperacional,
#   st_statusatendimento, nm_titulo, dt_emissao, dt_conclusao, vl_producaoestimada,
#   vl_receitaestimada, nm_agenciafomento, nm_fantasia, nm_razao_social, qt_funcionarios,
#   ds_porte_cliente, dt_carga
fato_producao_stisgt = Table(
    'fato_producao_stisgt',
    dw_metadata,
    autoload_with=dw_engine
)
