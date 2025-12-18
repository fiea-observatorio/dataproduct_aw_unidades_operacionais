#!/usr/bin/env python3
"""
Script para configuração inicial da aplicação
"""
import sys
from app import create_app, db
from app.models import User, Unit

def setup_database():
    """Inicializar banco de dados"""
    print("Criando tabelas do banco de dados...")
    db.create_all()
    print("✓ Tabelas criadas com sucesso!")

def create_admin_user():
    """Criar usuário admin padrão"""
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print("! Usuário admin já existe")
        return
    
    print("\nCriando usuário admin padrão...")
    admin = User(username='admin', role='admin')
    admin.set_password('admin123')
    
    db.session.add(admin)
    db.session.commit()
    
    print("✓ Usuário admin criado!")
    print("  Username: admin")
    print("  Password: admin123")
    print("  ⚠️  IMPORTANTE: Altere a senha em produção!")

def create_sample_data():
    """Criar dados de exemplo"""
    response = input("\nDeseja criar dados de exemplo? (s/n): ")
    
    if response.lower() != 's':
        return
    
    print("\nCriando dados de exemplo...")
    
    # Criar usuário comum
    user = User(username='usuario', role='user')
    user.set_password('senha123')
    db.session.add(user)
    
    # Criar unidades
    unit1 = Unit(name='Unidade Centro', description='Unidade central da empresa')
    unit2 = Unit(name='Unidade Sul', description='Unidade da região sul')
    
    db.session.add(unit1)
    db.session.add(unit2)
    db.session.commit()
    
    # Associar usuário às unidades
    admin = User.query.filter_by(username='admin').first()
    user = User.query.filter_by(username='usuario').first()
    
    unit1.users.append(admin)
    unit1.users.append(user)
    unit2.users.append(admin)
    
    db.session.commit()
    
    print("✓ Dados de exemplo criados!")
    print("  - Usuário: usuario / senha123")
    print("  - 2 unidades criadas")

def main():
    """Função principal"""
    print("=" * 50)
    print("  Setup Power BI Embedded API")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            setup_database()
            create_admin_user()
            create_sample_data()
            
            print("\n" + "=" * 50)
            print("  ✓ Setup concluído com sucesso!")
            print("=" * 50)
            print("\nPróximos passos:")
            print("1. Configure as variáveis de ambiente (.env)")
            print("2. Execute: flask run")
            print("3. Acesse: http://localhost:5000/api/docs/")
            print("4. Faça login com admin/admin123")
            
        except Exception as e:
            print(f"\n✗ Erro durante setup: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    main()
