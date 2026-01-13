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
        
        # Criar usuários
        print("\n👤 Criando usuários...")
        
        # Admin
        admin = User(username='admin', name='Administrador', role='admin')
        admin.set_password('admin')
        db.session.add(admin)
        
        # Usuários normais
        sesi_centro = User(username='sesi.centro', name='Escola SESI Centro', role='user')
        sesi_centro.set_password('1234')
        db.session.add(sesi_centro)
        
        sesi_senai_benedito = User(username='sesi.senai.benedito', name='SESI/SENAI Benedito Bentes', role='user')
        sesi_senai_benedito.set_password('5678')
        db.session.add(sesi_senai_benedito)
        
        sesi_saude_cambona = User(username='sesi.saude.cambona', name='SESI Saúde Cambona', role='user')
        sesi_saude_cambona.set_password('9012')
        db.session.add(sesi_saude_cambona)
        
        sesi_saude_tabuleiro = User(username='sesi.saude.tabuleiro', name='SESI Saúde Tabuleriro', role='user')
        sesi_saude_tabuleiro.set_password('3456')
        db.session.add(sesi_saude_tabuleiro)
        
        sesi_senai_arapiraca = User(username='sesi.senai.arapiraca', name='SESI/SENAI Arapiraca', role='user')
        sesi_senai_arapiraca.set_password('7890')
        db.session.add(sesi_senai_arapiraca)
        
        senai_poco = User(username='senai.poco', name='SENAI Poço', role='user')
        senai_poco.set_password('2468')
        db.session.add(senai_poco)
        
        diretoria = User(username='diretoria', name='Diretoria', role='user')
        diretoria.set_password('1357')
        db.session.add(diretoria)
        
        db.session.commit()
        print("✅ Usuários criados!")
        
        # Criar unidades
        print("\n🏢 Criando unidades...")
        unit_sesi_educacao = Unit(
            name='SESI Educação Básica',
            description='Unidade de Educação Básica do SESI'
        )
        db.session.add(unit_sesi_educacao)
        
        unit_sesi_saude = Unit(
            name='SESI Saúde',
            description='Unidade de Saúde e Segurança do Trabalho do SESI'
        )
        db.session.add(unit_sesi_saude)
        
        unit_senai_educacao = Unit(
            name='SENAI Educação Profissional e STI',
            description='Unidade de Educação Profissional e Serviços Técnicos e Tecnológicos do SENAI'
        )
        db.session.add(unit_senai_educacao)
        
        db.session.commit()
        print("✅ Unidades criadas!")
        
        # Associar usuários às unidades
        print("\n🔗 Associando usuários às unidades...")
        
        # sesi.centro -> SESI Educação Básica
        sesi_centro.units.append(unit_sesi_educacao)
        
        # sesi.senai.benedito -> SESI Educação Básica, SENAI Educação Profissional e STI
        sesi_senai_benedito.units.append(unit_sesi_educacao)
        sesi_senai_benedito.units.append(unit_senai_educacao)
        
        # sesi.saude.cambona -> SESI Saúde
        sesi_saude_cambona.units.append(unit_sesi_saude)
        
        # sesi.saude.tabuleiro -> SESI Saúde
        sesi_saude_tabuleiro.units.append(unit_sesi_saude)
        
        # sesi.senai.arapiraca -> SESI Saúde, SENAI Educação Profissional e STI
        sesi_senai_arapiraca.units.append(unit_sesi_saude)
        sesi_senai_arapiraca.units.append(unit_senai_educacao)
        
        # senai.poco -> SENAI Educação Profissional e STI
        senai_poco.units.append(unit_senai_educacao)
        
        # diretoria -> SESI Educação Básica, SESI Saúde, SENAI Educação Profissional e STI
        diretoria.units.append(unit_sesi_educacao)
        diretoria.units.append(unit_sesi_saude)
        diretoria.units.append(unit_senai_educacao)
        
        db.session.commit()
        print("✅ Associações criadas!")
        
        # Resumo
        print("\n" + "="*60)
        print("📊 RESUMO DOS DADOS CRIADOS")
        print("="*60)
        print("\n👥 Usuários:")
        print("   - admin (senha: admin) - Role: admin")
        print("   - sesi.centro (senha: 1234)")
        print("   - sesi.senai.benedito (senha: 5678)")
        print("   - sesi.saude.cambona (senha: 9012)")
        print("   - sesi.saude.tabuleiro (senha: 3456)")
        print("   - sesi.senai.arapiraca (senha: 7890)")
        print("   - senai.poco (senha: 2468)")
        print("   - diretoria (senha: 1357)")
        
        print("\n🏢 Unidades:")
        print(f"   - {unit_sesi_educacao.name}")
        print(f"   - {unit_sesi_saude.name}")
        print(f"   - {unit_senai_educacao.name}")
        
        print("\n🔗 Associações Usuário → Unidades:")
        print("   - sesi.centro → SESI Educação Básica")
        print("   - sesi.senai.benedito → SESI Educação Básica, SENAI Educação Profissional e STI")
        print("   - sesi.saude.cambona → SESI Saúde")
        print("   - sesi.saude.tabuleiro → SESI Saúde")
        print("   - sesi.senai.arapiraca → SESI Saúde, SENAI Educação Profissional e STI")
        print("   - senai.poco → SENAI Educação Profissional e STI")
        print("   - diretoria → SESI Educação Básica, SESI Saúde, SENAI Educação Profissional e STI")
        
        print("\n✅ Banco populado com sucesso!")
        print("\n💡 Para testar as rotas, use o arquivo test_routes.py")

if __name__ == '__main__':
    seed_database()
