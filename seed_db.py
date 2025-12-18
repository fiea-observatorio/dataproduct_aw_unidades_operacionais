"""
Script para popular o banco de dados com dados iniciais
Execute: python seed_db.py
"""
from app import create_app, db
from app.models import User, Unit

def seed_database():
    app = create_app()
    
    with app.app_context():
        print("🌱 Populando banco de dados...")
        
        # Verificar se já existem dados
        if User.query.first():
            print("⚠️  Banco já possui dados. Deseja continuar? (s/n)")
            if input().lower() != 's':
                print("❌ Operação cancelada")
                return
        
        # Criar usuário admin
        print("\n👤 Criando usuário admin...")
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Criar usuário comum
        print("👤 Criando usuário teste...")
        user1 = User(username='usuario1', role='user')
        user1.set_password('senha123')
        db.session.add(user1)
        
        user2 = User(username='usuario2', role='user')
        user2.set_password('senha123')
        db.session.add(user2)
        
        db.session.commit()
        print("✅ Usuários criados!")
        
        # Criar unidades
        print("\n🏢 Criando unidades...")
        unit1 = Unit(
            name='Unidade Sul',
            description='Unidade da região sul'
        )
        db.session.add(unit1)
        
        unit2 = Unit(
            name='Unidade Norte',
            description='Unidade da região norte'
        )
        db.session.add(unit2)
        
        unit3 = Unit(
            name='Unidade Leste',
            description='Unidade da região leste'
        )
        db.session.add(unit3)
        
        db.session.commit()
        print("✅ Unidades criadas!")
        
        # Associar usuários às unidades
        print("\n🔗 Associando usuários às unidades...")
        user1.units.append(unit1)
        user1.units.append(unit2)
        user2.units.append(unit2)
        user2.units.append(unit3)
        
        db.session.commit()
        print("✅ Associações criadas!")
        
        # Resumo
        print("\n" + "="*50)
        print("📊 RESUMO DOS DADOS CRIADOS")
        print("="*50)
        print("\n👥 Usuários:")
        print(f"   - admin (senha: admin123) - Role: admin")
        print(f"   - usuario1 (senha: senha123) - Role: user")
        print(f"   - usuario2 (senha: senha123) - Role: user")
        
        print("\n🏢 Unidades:")
        print(f"   - {unit1.name}")
        print(f"   - {unit2.name}")
        print(f"   - {unit3.name}")
        
        print("\n🔗 Associações:")
        print(f"   - usuario1: Unidade Sul, Unidade Norte")
        print(f"   - usuario2: Unidade Norte, Unidade Leste")
        
        print("\n✅ Banco populado com sucesso!")
        print("\n💡 Para testar as rotas, use o arquivo test_routes.py")

if __name__ == '__main__':
    seed_database()
