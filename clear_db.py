"""
Script para limpar todos os dados do banco de dados
Execute: python clear_db.py
"""

from app import create_app, db
from app.models import User, Unit, Step, Report, UserUnit


def clear_database():
    app = create_app()

    with app.app_context():
        print("🗑️  Limpando banco de dados...")
        
        # Confirmar ação
        print("⚠️  ATENÇÃO: Todos os dados serão apagados!")
        print("Deseja continuar? (s/n)")
        if input().lower() != "s":
            print("❌ Operação cancelada")
            return

        try:
            # Deletar na ordem correta (respeitando foreign keys)
            print("\n🔄 Deletando dados...")
            
            # Primeiro, deletar relações many-to-many
            print("   - Deletando relações report-unit...")
            db.session.execute(db.text("DELETE FROM report_units"))
            
            print("   - Deletando relações user-unit...")
            UserUnit.query.delete()
            
            # Depois, deletar as entidades principais
            print("   - Deletando reports...")
            Report.query.delete()
            
            print("   - Deletando steps...")
            Step.query.delete()
            
            print("   - Deletando units...")
            Unit.query.delete()
            
            print("   - Deletando users...")
            User.query.delete()
            
            # Commit das mudanças
            db.session.commit()
            
            print("\n✅ Banco de dados limpo com sucesso!")
            print("\n💡 Agora você pode executar:")
            print("   - flask db downgrade base")
            print("   - flask db upgrade head")
            print("   - python seed_db.py")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro ao limpar banco: {e}")


if __name__ == "__main__":
    clear_database()
