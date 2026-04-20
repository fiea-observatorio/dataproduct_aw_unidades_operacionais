import os
import threading
from datetime import datetime, timedelta

import requests

LOGIN_PATH = '/seguranca/tokens'
FONTE_DADOS_PREVISAO_SSI = 'CDS_RELORC_OFERTA_004'

# Meses retornados pela API como colunas ProducaoJaneiro..ProducaoDezembro
_PRODUCAO_MONTHLY_FIELDS = [
    'ProducaoJaneiro', 'ProducaoFevereiro', 'ProducaoMarco', 'ProducaoMarço',
    'ProducaoAbril', 'ProducaoMaio', 'ProducaoJunho', 'ProducaoJulho',
    'ProducaoAgosto', 'ProducaoSetembro', 'ProducaoOutubro', 'ProducaoNovembro',
    'ProducaoDezembro',
]

# Replica os filtros aplicados no Power Query sobre fato_previsaossi360
_NOME_PRODUTO_EXCLUIDOS = {
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
}

_PRODUTO_PREFIX = '103'


class Solucao360Client:
    """Cliente do Solução 360 com dois modos de autenticação:

    - API key estática (bearer pré-provisionado): usada em endpoints como
      `/tools/fontes-dados/.../executar`, que recusam tokens de usuário com
      "Token inválido." (HTTP 400).
    - Login de usuário (email+senha via /seguranca/tokens): para endpoints de
      negócio que esperam sessão de usuário.

    Se `api_key` for fornecida, ela é usada direto. Caso contrário, cai no
    fluxo de login e cacheia o token por `token_ttl_seconds`.
    """

    def __init__(self, api_host, email=None, password=None, api_key=None,
                 tenant='FIEA', token_ttl_seconds=3000):
        self._api_host = api_host.rstrip('/')
        self._email = email
        self._password = password
        self._api_key = api_key
        self._tenant = tenant
        self._token_ttl = timedelta(seconds=token_ttl_seconds)
        self._token = None
        self._token_expiry = None
        self._lock = threading.Lock()

    def _login(self):
        headers = {
            'Content-Type': 'application/json',
            'accept': 'application/json',
            'tenant': self._tenant,
        }
        response = requests.post(
            self._api_host + LOGIN_PATH,
            json={'email': self._email, 'password': self._password},
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        token = response.json().get('token')
        if not token:
            raise RuntimeError('Login no Solução 360 não retornou token')
        return token

    def _get_token(self):
        if self._api_key:
            return self._api_key
        if not self._email or not self._password:
            raise RuntimeError(
                'Solução 360 sem credencial: configure SOLUCAO360_API_KEY ou '
                'SOLUCAO360_EMAIL + SOLUCAO360_PASSWORD'
            )
        with self._lock:
            now = datetime.utcnow()
            if self._token and self._token_expiry and now < self._token_expiry:
                return self._token
            self._token = self._login()
            self._token_expiry = now + self._token_ttl
            return self._token

    def _headers(self):
        return {
            'Authorization': f'Bearer {self._get_token()}',
            'Content-Type': 'application/json',
            'accept': 'application/json',
            'tenant': self._tenant,
        }

    def _request(self, method, endpoint, params=None, json_body=None):
        url = self._api_host + endpoint
        response = requests.request(
            method, url, headers=self._headers(),
            params=params or None, json=json_body,
            timeout=30,
        )
        if response.status_code == 401:
            with self._lock:
                self._token = None
                self._token_expiry = None
            response = requests.request(
                method, url, headers=self._headers(),
                params=params or None, json=json_body,
                timeout=30,
            )
        if not response.ok:
            raise requests.HTTPError(
                f'{response.status_code} {response.reason} for {method} {url} '
                f'— body: {response.text[:1000]}',
                response=response,
            )
        return response.json()

    def get(self, endpoint, params=None):
        return self._request('GET', endpoint, params=params)

    def post(self, endpoint, json_body=None, params=None):
        return self._request('POST', endpoint, params=params, json_body=json_body)


_client = None
_client_lock = threading.Lock()


def _get_client():
    global _client
    if _client is not None:
        return _client
    with _client_lock:
        if _client is not None:
            return _client
        api_host = os.getenv('SOLUCAO360_URL', 'https://fiea.solucao360.com')
        email = os.getenv('SOLUCAO360_EMAIL')
        password = os.getenv('SOLUCAO360_PASSWORD')
        api_key = os.getenv('SOLUCAO360_API_KEY')
        tenant = os.getenv('SOLUCAO360_TENANT', 'FIEA')
        if not api_key and not (email and password):
            raise RuntimeError(
                'Configure SOLUCAO360_API_KEY (bearer estático) ou '
                'SOLUCAO360_EMAIL + SOLUCAO360_PASSWORD para o Solução 360'
            )
        _client = Solucao360Client(
            api_host, email=email, password=password, api_key=api_key, tenant=tenant,
        )
        return _client


def _extract_list(payload):
    """A API pode retornar lista direta, {data: [...]} ou {result: [...]}."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ('data', 'result'):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    raise ValueError('Formato inesperado da resposta Solução 360')


def fetch_previsao_ssi():
    """Busca previsão SSI do Solução 360, já filtrada conforme Power Query."""
    empresa_ano_fiscal_id = os.getenv('SOLUCAO360_EMPRESA_ANO_FISCAL_ID', '1020')
    endpoint = f'/tools/fontes-dados/{FONTE_DADOS_PREVISAO_SSI}/executar'

    raw = _extract_list(
        _get_client().get(endpoint, params={'EmpresaAnoFiscalId': empresa_ano_fiscal_id})
    )

    filtered = []
    for row in raw:
        produto = row.get('Produto') or ''
        if not str(produto).startswith(_PRODUTO_PREFIX):
            continue
        if row.get('NomeProduto') in _NOME_PRODUTO_EXCLUIDOS:
            continue
        filtered.append(row)
    return filtered


def _coerce_number(value):
    if value in (None, ''):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def sum_previsao_ssi_producao():
    """Soma anual de Producao (equivalente a SUM(fato_previsaossi360[Producao]))."""
    total = 0.0
    for row in fetch_previsao_ssi():
        for field in _PRODUCAO_MONTHLY_FIELDS:
            if field in row:
                total += _coerce_number(row[field])
    return total
