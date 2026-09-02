"""Validação dos tokens emitidos pelo iDigital (SSO da FIEA).

O front faz o fluxo OIDC (authorization code + PKCE) e envia para a API o
access token (Authorization: Bearer) e o ID token (X-Id-Token). Aqui os dois
são verificados contra o JWKS publicado pelo iDigital — assinatura, emissor,
audience e expiração — antes de qualquer troca por tokens próprios da API.

Regras espelhadas da lib oficial @fiea-al/idigital-node-integration:
- access token: typ "at+jwt", aud = applicationHost (o "resource" do fluxo),
  claim client_id = clientId do cadastro.
- ID token: aud = clientId.
"""
import time

import jwt as pyjwt
import requests
from flask import current_app
from jwt import PyJWKClient

DISCOVERY_PATH = '/sso/oidc/.well-known/openid-configuration'

# Claims onde o iDigital publica o e-mail e o nome, em ordem de preferência.
EMAIL_CLAIMS = ['email', 'preferred_username', 'upn', 'unique_name']
NAME_CLAIMS = ['displayName', 'name', 'given_name', 'firstName']

_DISCOVERY_TTL_SECONDS = 60 * 60
_HTTP_TIMEOUT_SECONDS = 10

_cache = {'discovery': None, 'discovery_expires_at': 0, 'jwk_client': None, 'issuer': None}


class IdigitalAuthError(Exception):
    """Token do iDigital ausente, inválido ou expirado."""


def _issuer():
    issuer = (current_app.config.get('IDIGITAL_ISSUER') or '').rstrip('/')
    if not issuer:
        raise IdigitalAuthError('IDIGITAL_ISSUER não configurado')
    return issuer


def _get_discovery():
    issuer = _issuer()
    now = time.time()
    if _cache['discovery'] and _cache['issuer'] == issuer and _cache['discovery_expires_at'] > now:
        return _cache['discovery']

    response = requests.get(issuer + DISCOVERY_PATH, timeout=_HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    _cache['discovery'] = response.json()
    _cache['discovery_expires_at'] = now + _DISCOVERY_TTL_SECONDS
    _cache['issuer'] = issuer
    _cache['jwk_client'] = None
    return _cache['discovery']


def _get_jwk_client():
    if _cache['jwk_client'] is None or _cache['issuer'] != _issuer():
        discovery = _get_discovery()
        jwks_uri = discovery.get('jwks_uri')
        if not jwks_uri:
            raise IdigitalAuthError('O iDigital não publicou jwks_uri no documento de descoberta')
        _cache['jwk_client'] = PyJWKClient(jwks_uri, cache_keys=True)
    return _cache['jwk_client']


def _signing_key(token):
    try:
        return _get_jwk_client().get_signing_key_from_jwt(token).key
    except pyjwt.exceptions.PyJWKClientError as error:
        raise IdigitalAuthError(f'Chave de assinatura não encontrada no JWKS: {error}')


def verify_access_token(token):
    """Valida o access token e retorna suas claims."""
    if not token:
        raise IdigitalAuthError('Access token não informado')

    client_id = current_app.config.get('IDIGITAL_CLIENT_ID')
    application_host = current_app.config.get('IDIGITAL_APPLICATION_HOST')

    try:
        payload = pyjwt.decode(
            token,
            _signing_key(token),
            algorithms=['RS256'],
            audience=application_host,
            issuer=_issuer(),
            options={'require': ['exp', 'iss', 'aud']},
        )
    except pyjwt.InvalidTokenError as error:
        raise IdigitalAuthError(f'Access token recusado: {error}')

    if payload.get('client_id') != client_id:
        raise IdigitalAuthError('Access token emitido para outro cliente')

    return payload


def verify_id_token(token):
    """Valida o ID token (fonte da identidade) e retorna suas claims."""
    if not token:
        raise IdigitalAuthError('ID token não informado')

    client_id = current_app.config.get('IDIGITAL_CLIENT_ID')

    try:
        return pyjwt.decode(
            token,
            _signing_key(token),
            algorithms=['RS256'],
            audience=client_id,
            issuer=_issuer(),
            options={'require': ['exp', 'iss', 'aud']},
        )
    except pyjwt.InvalidTokenError as error:
        raise IdigitalAuthError(f'ID token recusado: {error}')


def _first_claim(claims, names, is_valid=None):
    for name in names:
        value = (claims or {}).get(name)
        if isinstance(value, str) and value.strip() and (is_valid is None or is_valid(value)):
            return value.strip()
    return ''


def get_email(claims):
    return _first_claim(claims, EMAIL_CLAIMS, lambda value: '@' in value).lower()


def get_name(claims):
    return _first_claim(claims, NAME_CLAIMS)
