import requests
import msal
from datetime import datetime, timedelta
from flask import current_app
import json

class PowerBIService:
    def __init__(self):
        self.client_id = current_app.config['POWERBI_CLIENT_ID']
        self.client_secret = current_app.config['POWERBI_CLIENT_SECRET']
        self.tenant_id = current_app.config['POWERBI_TENANT_ID']
        self.authority = current_app.config['POWERBI_AUTHORITY_URL']
        self.scope = [current_app.config['POWERBI_SCOPE']]
        self.base_url = 'https://api.powerbi.com/v1.0/myorg'
        
        self._token_cache = {}
    
    def get_access_token(self):
        """Obtém access token do Azure AD com cache"""
        cache_key = 'powerbi_token'
        
        # Verificar se existe token em cache e se ainda é válido
        if cache_key in self._token_cache:
            token_data = self._token_cache[cache_key]
            expiry = token_data.get('expiry')
            if expiry and datetime.utcnow() < expiry:
                return token_data['token']
        
        # Obter novo token
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )
        
        result = app.acquire_token_for_client(scopes=self.scope)
        
        if "access_token" in result:
            # Cachear token (expira em 1 hora, renovar 5 minutos antes)
            expiry = datetime.utcnow() + timedelta(seconds=result.get('expires_in', 3600) - 300)
            self._token_cache[cache_key] = {
                'token': result['access_token'],
                'expiry': expiry
            }
            return result['access_token']
        else:
            raise Exception(f"Failed to acquire token: {result.get('error_description')}")
    
    def get_headers(self):
        """Retorna headers com authorization"""
        token = self.get_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def get_workspaces(self):
        """Lista todos os workspaces"""
        url = f'{self.base_url}/groups'
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        return response.json().get('value', [])
    
    def get_reports(self, workspace_id):
        """Lista reports de um workspace"""
        url = f'{self.base_url}/groups/{workspace_id}/reports'
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        return response.json().get('value', [])
    
    def get_report(self, workspace_id, report_id):
        """Obtém detalhes de um report específico"""
        url = f'{self.base_url}/groups/{workspace_id}/reports/{report_id}'
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        return response.json()
    
    def generate_embed_token(self, workspace_id, report_id, dataset_ids=None, username=None, roles=None):
        """
        Gera embed token para um report com suporte a RLS
        
        Args:
            workspace_id: ID do workspace
            report_id: ID do report
            dataset_ids: Lista de dataset IDs (opcional)
            username: Username para RLS (opcional)
            roles: Lista de roles para RLS (opcional)
        """
        url = f'{self.base_url}/GenerateToken'
        
        payload = {
            "reports": [
                {
                    "id": report_id,
                    "allowEdit": False
                }
            ],
            "targetWorkspaces": [
                {
                    "id": workspace_id
                }
            ]
        }
        
        # Adicionar datasets se fornecidos
        if dataset_ids:
            payload["datasets"] = [{"id": ds_id} for ds_id in dataset_ids]
        
        # Adicionar identidade para RLS se fornecida
        if username and roles:
            payload["identities"] = [
                {
                    "username": username,
                    "roles": roles,
                    "datasets": dataset_ids if dataset_ids else []
                }
            ]
        
        response = requests.post(url, headers=self.get_headers(), json=payload)
        response.raise_for_status()
        
        result = response.json()
        return {
            'token': result.get('token'),
            'token_id': result.get('tokenId'),
            'expiration': result.get('expiration')
        }
    
    def get_embed_config(self, workspace_id, report_id, username=None, roles=None):
        """
        Retorna configuração completa para embed do report
        """
        # Obter informações do report
        report = self.get_report(workspace_id, report_id)
        
        # Obter dataset IDs
        dataset_id = report.get('datasetId')
        dataset_ids = [dataset_id] if dataset_id else []
        
        # Gerar embed token
        token_data = self.generate_embed_token(
            workspace_id=workspace_id,
            report_id=report_id,
            dataset_ids=dataset_ids,
            username=username,
            roles=roles
        )
        
        return {
            'reportId': report_id,
            'embedUrl': report.get('embedUrl'),
            'accessToken': token_data['token'],
            'tokenExpiration': token_data['expiration'],
            'tokenId': token_data['token_id'],
            'datasetId': dataset_id
        }
    
    def sync_reports_from_workspace(self, workspace_id):
        """
        Sincroniza reports de um workspace
        Retorna lista de reports
        """
        reports = self.get_reports(workspace_id)
        return [
            {
                'report_id': r['id'],
                'workspace_id': workspace_id,
                'dataset_id': r.get('datasetId'),
                'name': r['name'],
                'embed_url': r.get('embedUrl')
            }
            for r in reports
        ]
