# Power BI Embedded API

API REST completa para gestão de usuários, unidades e integração com Power BI Embedded.

## Funcionalidades

- ✅ Sistema de autenticação com JWT (login, register, refresh token)
- ✅ Gestão de usuários com roles (admin/user)
- ✅ Gestão de unidades e associação de usuários
- ✅ Integração completa com Power BI Embed API
- ✅ Geração de embed tokens com suporte a RLS (Row Level Security)
- ✅ Sincronização automática de reports do Power BI
- ✅ Sistema de auditoria e logs de acesso
- ✅ Rate limiting
- ✅ Documentação Swagger/OpenAPI
- ✅ Validação de entrada e sanitização
- ✅ CORS configurável
- ✅ Health check endpoint

## Tecnologias

- Python 3.10+
- Flask 3.0
- SQLAlchemy (ORM)
- Flask-JWT-Extended
- MSAL (Microsoft Authentication Library)

## Instalação

### 1. Clone o repositório e instale dependências

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

### 3. Configurar Power BI (Azure AD)

Para integração com Power BI, você precisa:

1. Criar um App Registration no Azure AD
2. Configurar permissões API: `Power BI Service` > `Report.Read.All`, `Dataset.Read.All`
3. Criar um Client Secret
4. Adicionar as credenciais no `.env`

### 4. Inicializar banco de dados

```bash
# Criar migrations
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 5. Criar usuário admin inicial (opcional)

```python
flask shell

>>> from app import db
>>> from app.models import User
>>> admin = User(username='admin', role='admin')
>>> admin.set_password('admin123')
>>> db.session.add(admin)
>>> db.session.commit()
>>> exit()
```

### 6. Executar aplicação

```bash
# Desenvolvimento
flask run

# Produção (com gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## Documentação da API

Após iniciar a aplicação, acesse:

- **Swagger UI**: http://localhost:5000/api/docs/
- **Health Check**: http://localhost:5000/health

## Estrutura do Projeto

```
powerbi-app/
├── app/
│   ├── __init__.py              # Inicialização da aplicação
│   ├── models.py                # Modelos do banco de dados
│   ├── middleware/
│   │   └── auth.py             # Middlewares de autenticação
│   ├── routes/
│   │   ├── auth.py             # Rotas de autenticação
│   │   ├── units.py            # Rotas de unidades

│   │   ├── reports.py          # Rotas de reports Power BI
│   │   └── admin.py            # Rotas administrativas
│   ├── services/
│   │   └── powerbi_service.py  # Serviço de integração Power BI
│   └── utils/
│       └── error_handlers.py   # Handlers de erro
├── config/
│   └── config.py               # Configurações da aplicação
├── migrations/                  # Migrations do banco
├── .env.example                # Exemplo de variáveis de ambiente
├── requirements.txt            # Dependências Python
├── run.py                      # Arquivo principal
└── README.md                   # Este arquivo
```

## Endpoints Principais

### Autenticação
- `POST /api/auth/register` - Registrar novo usuário
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Renovar token
- `GET /api/auth/me` - Dados do usuário atual

### Unidades
- `GET /api/units` - Listar unidades
- `POST /api/units` - Criar unidade (admin)
- `GET /api/units/{id}` - Obter unidade
- `PUT /api/units/{id}` - Atualizar unidade (admin)
- `DELETE /api/units/{id}` - Deletar unidade (admin)
- `POST /api/units/{id}/users` - Adicionar usuário (admin)
- `GET /api/units/{id}/users` - Listar usuários da unidade

### Reports Power BI
- `GET /api/reports` - Listar reports
- `POST /api/reports` - Criar/registrar report (admin)
- `GET /api/reports/{id}` - Obter report
- `POST /api/reports/{id}/embed-token` - Gerar embed token
- `GET /api/reports/{id}/embed-config` - Obter config completa
- `POST /api/reports/sync/{workspace_id}` - Sincronizar reports (admin)

### Admin
- `GET /api/admin/users` - Listar usuários (admin)
- `PUT /api/admin/users/{id}` - Atualizar usuário (admin)
- `DELETE /api/admin/users/{id}` - Deletar usuário (admin)
- `GET /api/admin/stats` - Estatísticas do sistema (admin)
- `GET /api/admin/access-logs` - Logs de acesso (admin)

## Exemplos de Uso

### 1. Registrar e fazer login

```bash
# Registrar
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "joao", "password": "senha123"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "joao", "password": "senha123"}'
```

### 2. Criar unidade (como admin)

```bash
curl -X POST http://localhost:5000/api/units \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Unidade Sul", "description": "Unidade da região sul"}'
```

### 3. Obter embed config para report

```bash
curl -X GET "http://localhost:5000/api/reports/1/embed-config?roles=Manager" \
  -H "Authorization: Bearer SEU_TOKEN"
```

## Power BI Embedded - Integração Frontend

Exemplo de como usar a configuração no frontend:

```javascript
// 1. Obter config do backend
const response = await fetch('/api/reports/1/embed-config', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
const config = await response.json();

// 2. Embed no Power BI
const embedContainer = document.getElementById('reportContainer');
const report = powerbi.embed(embedContainer, {
  type: 'report',
  tokenType: models.TokenType.Embed,
  accessToken: config.accessToken,
  embedUrl: config.embedUrl,
  id: config.reportId,
  permissions: models.Permissions.Read,
  settings: {
    panes: {
      filters: { expanded: false, visible: true }
    }
  }
});
```

## Segurança

- Senhas hasheadas com bcrypt
- JWT tokens com expiração
- Rate limiting em endpoints sensíveis
- Validação de entrada em todos os endpoints
- CORS configurável
- Logs de auditoria para acesso a reports
- Suporte a RLS (Row Level Security) do Power BI

## Deploy em Produção

### Usando Docker (recomendado)

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
```

### Variáveis de ambiente importantes para produção

- Configure `FLASK_ENV=production`
- Use banco PostgreSQL
- Use secrets seguros para JWT
- Configure CORS adequadamente

## Troubleshooting

### Erro ao conectar com Power BI

Verifique:
- Credenciais do Azure AD estão corretas
- App tem permissões necessárias
- Service principal tem acesso ao workspace

### Erro de autenticação

Verifique:
- JWT_SECRET_KEY está configurado
- Token não expirou
- Header Authorization está no formato: `Bearer {token}`

## Licença

MIT
