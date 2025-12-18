"""
Script para testar as rotas da API
Execute: python test_routes.py
"""
import requests
import json

# Configuração
BASE_URL = 'http://localhost:5000'
TOKEN = None

def print_response(response):
    """Imprime resposta formatada"""
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)
    print("-" * 50)

def test_health():
    """Testa endpoint de health check"""
    print("\n🏥 Testando Health Check...")
    response = requests.get(f'{BASE_URL}/health')
    print_response(response)
    return response.status_code == 200

def test_register():
    """Testa registro de novo usuário"""
    print("\n📝 Testando Registro de Usuário...")
    data = {
        'username': 'novousuario',
        'password': 'senha123'
    }
    response = requests.post(f'{BASE_URL}/api/auth/register', json=data)
    print_response(response)
    return response.status_code == 201

def test_login(username='admin', password='admin123'):
    """Testa login e retorna o token"""
    print(f"\n🔐 Testando Login ({username})...")
    data = {
        'username': username,
        'password': password
    }
    response = requests.post(f'{BASE_URL}/api/auth/login', json=data)
    print_response(response)
    
    if response.status_code == 200:
        global TOKEN
        TOKEN = response.json()['access_token']
        print(f"✅ Token obtido: {TOKEN[:50]}...")
        return True
    return False

def test_me():
    """Testa endpoint de usuário atual"""
    print("\n👤 Testando GET /api/auth/me...")
    headers = {'Authorization': f'Bearer {TOKEN}'}
    response = requests.get(f'{BASE_URL}/api/auth/me', headers=headers)
    print_response(response)
    return response.status_code == 200

def test_get_units():
    """Testa listagem de unidades"""
    print("\n🏢 Testando GET /api/units...")
    headers = {'Authorization': f'Bearer {TOKEN}'}
    response = requests.get(f'{BASE_URL}/api/units', headers=headers)
    print_response(response)
    return response.status_code == 200

def test_create_unit():
    """Testa criação de unidade (apenas admin)"""
    print("\n➕ Testando POST /api/units (criar unidade)...")
    headers = {'Authorization': f'Bearer {TOKEN}'}
    data = {
        'name': 'Unidade Oeste',
        'description': 'Unidade da região oeste - criada via API'
    }
    response = requests.post(f'{BASE_URL}/api/units', headers=headers, json=data)
    print_response(response)
    return response.status_code == 201

def test_get_unit_users(unit_id=1):
    """Testa listagem de usuários de uma unidade"""
    print(f"\n👥 Testando GET /api/units/{unit_id}/users...")
    headers = {'Authorization': f'Bearer {TOKEN}'}
    response = requests.get(f'{BASE_URL}/api/units/{unit_id}/users', headers=headers)
    print_response(response)
    return response.status_code == 200

def test_add_user_to_unit(unit_id=1, user_id=3):
    """Testa adicionar usuário a uma unidade (apenas admin)"""
    print(f"\n🔗 Testando POST /api/units/{unit_id}/users (adicionar usuário)...")
    headers = {'Authorization': f'Bearer {TOKEN}'}
    data = {'user_id': user_id}
    response = requests.post(f'{BASE_URL}/api/units/{unit_id}/users', headers=headers, json=data)
    print_response(response)
    return response.status_code == 200

def test_admin_users():
    """Testa listagem de usuários (apenas admin)"""
    print("\n👨‍💼 Testando GET /api/admin/users...")
    headers = {'Authorization': f'Bearer {TOKEN}'}
    response = requests.get(f'{BASE_URL}/api/admin/users', headers=headers)
    print_response(response)
    return response.status_code == 200

def test_admin_stats():
    """Testa estatísticas do sistema (apenas admin)"""
    print("\n📊 Testando GET /api/admin/stats...")
    headers = {'Authorization': f'Bearer {TOKEN}'}
    response = requests.get(f'{BASE_URL}/api/admin/stats', headers=headers)
    print_response(response)
    return response.status_code == 200

def run_all_tests():
    """Executa todos os testes"""
    print("="*60)
    print("🚀 INICIANDO TESTES DA API")
    print("="*60)
    
    # Testes sem autenticação
    test_health()
    
    # Login como admin
    if not test_login('admin', 'admin123'):
        print("❌ Falha no login. Verifique se o banco foi populado.")
        return
    
    # Testes com autenticação
    test_me()
    test_get_units()
    test_get_unit_users(1)
    
    # Testes apenas para admin
    test_create_unit()
    test_add_user_to_unit(1, 3)
    test_admin_users()
    test_admin_stats()
    
    # Teste com usuário comum
    print("\n" + "="*60)
    print("🔄 Testando com usuário comum...")
    print("="*60)
    test_login('usuario1', 'senha123')
    test_me()
    test_get_units()
    
    print("\n" + "="*60)
    print("✅ TESTES CONCLUÍDOS!")
    print("="*60)

if __name__ == '__main__':
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ Erro: Não foi possível conectar ao servidor.")
        print("💡 Certifique-se de que a aplicação está rodando em http://localhost:5000")
        print("   Execute: flask run ou python run.py")
