"""
Script para popular o banco de dados com dados iniciais
Execute: python seed_db.py
"""

from app import create_app, db
from app.models import User, Unit, Step, Report, UserUnit


def seed_database():
    app = create_app()

    with app.app_context():
        print("🌱 Populando banco de dados...")

        # Verificar se já existem dados
        if User.query.first():
            print("⚠️  Banco já possui dados. Deseja continuar? (s/n)")
            if input().lower() != "s":
                print("❌ Operação cancelada")
                return

        # Criar usuários
        print("\n👤 Criando usuários...")

        # Usuários normais
        senai_poco = User(
            username="senai.poco", name="SENAI Poço", role="user"
        )
        senai_poco.set_password("2468")
        db.session.add(senai_poco)

        sesi_saude_cambona = User(
            username="sesi.saude.cambona",
            name="SESI Saúde Cambona",
            role="user"
        )
        sesi_saude_cambona.set_password("9012")
        db.session.add(sesi_saude_cambona)

        sesi_centro = User(
            username="sesi.centro",
            name="Escola SESI Centro",
            role="user"
        )
        sesi_centro.set_password("1243")
        db.session.add(sesi_centro)

        sesi_senai_arapiraca = User(
            username="sesi.senai.arapiraca",
            name="SESI/SENAI Arapiraca",
            role="user"
        )
        sesi_senai_arapiraca.set_password("7890")
        db.session.add(sesi_senai_arapiraca)

        sesi_senai_benedito = User(
            username="sesi.senai.benedito",
            name="SESI/SENAI Benedito Bentes",
            role="user"
        )
        sesi_senai_benedito.set_password("5678")
        db.session.add(sesi_senai_benedito)

        sesi_saude_tabuleiro = User(
            username="sesi.saude.tabuleiro",
            name="SESI Saúde Tabuleiro",
            role="user"
        )
        sesi_saude_tabuleiro.set_password("3456")
        db.session.add(sesi_saude_tabuleiro)

        # Admin
        diretoria = User(
            username="diretoria", name="Diretoria", role="admin"
        )
        diretoria.set_password("1357")
        db.session.add(diretoria)

        db.session.commit()
        print("✅ Usuários criados!")

        # Criar unidades
        print("\n🏢 Criando unidades...")
        unit_sesi_educacao = Unit(
            name="SESI Educação Básica",
            description="Unidade de Educação Básica do SESI",
        )
        db.session.add(unit_sesi_educacao)

        unit_sesi_saude = Unit(
            name="SESI Saúde",
            description="Unidade de Saúde e Segurança do Trabalho do SESI",
        )
        db.session.add(unit_sesi_saude)

        unit_senai_educacao = Unit(
            name="SENAI Educação Profissional e STI",
            description="Unidade de Educação Profissional e Serviços Técnicos e Tecnológicos do SENAI",
        )
        db.session.add(unit_senai_educacao)

        db.session.commit()
        print("✅ Unidades criadas!")

        # Associar usuários às unidades
        print("\n🔗 Associando usuários às unidades...")

        # sesi.centro -> SESI Educação Básica
        uu1 = UserUnit(user_id=sesi_centro.id, unit_id=unit_sesi_educacao.id, bi_filter_param="3")
        db.session.add(uu1)

        # sesi.senai.benedito -> SESI Educação Básica, SENAI Educação Profissional e STI
        uu2 = UserUnit(user_id=sesi_senai_benedito.id, unit_id=unit_sesi_educacao.id, bi_filter_param="5")
        uu3 = UserUnit(user_id=sesi_senai_benedito.id, unit_id=unit_senai_educacao.id, bi_filter_param="6")
        db.session.add_all([uu2, uu3])

        # sesi.saude.cambona -> SESI Saúde
        uu4 = UserUnit(user_id=sesi_saude_cambona.id, unit_id=unit_sesi_saude.id, bi_filter_param="2")
        db.session.add(uu4)

        # sesi.saude.tabuleiro -> SESI Saúde
        uu5 = UserUnit(user_id=sesi_saude_tabuleiro.id, unit_id=unit_sesi_saude.id, bi_filter_param="7")
        db.session.add(uu5)

        # sesi.senai.arapiraca -> SESI Saúde, SENAI Educação Profissional e STI
        uu6 = UserUnit(user_id=sesi_senai_arapiraca.id, unit_id=unit_sesi_saude.id, bi_filter_param="8")
        uu7 = UserUnit(user_id=sesi_senai_arapiraca.id, unit_id=unit_senai_educacao.id, bi_filter_param="4")
        db.session.add_all([uu6, uu7])

        # senai.poco -> SENAI Educação Profissional e STI
        uu8 = UserUnit(user_id=senai_poco.id, unit_id=unit_senai_educacao.id, bi_filter_param="1")
        db.session.add(uu8)

        # diretoria -> SESI Educação Básica, SESI Saúde, SENAI Educação Profissional e STI
        uu9 = UserUnit(user_id=diretoria.id, unit_id=unit_sesi_educacao.id, bi_filter_param="0")
        uu10 = UserUnit(user_id=diretoria.id, unit_id=unit_sesi_saude.id, bi_filter_param="0")
        uu11 = UserUnit(user_id=diretoria.id, unit_id=unit_senai_educacao.id, bi_filter_param="0")
        db.session.add_all([uu9, uu10, uu11])

        db.session.commit()
        print("✅ Associações criadas!")

        # Criar Steps (blocos) globais - aplicam-se a todas as unidades
        print("\n📋 Criando blocos (steps) globais...")

        bloco1 = Step(step_number=1, name="Recursos Humanos")
        bloco2 = Step(step_number=2, name="Infraestrutura")
        bloco3 = Step(step_number=3, name="Comercial")
        bloco4 = Step(step_number=4, name="Operação")
        bloco5 = Step(step_number=5, name="Orçamento e Financeiro")
        bloco6 = Step(step_number=6, name="Estratégia")

        db.session.add_all([bloco1, bloco2, bloco3, bloco4, bloco5, bloco6])
        db.session.commit()
        print("✅ Blocos criados!")

        # Criar Reports (relatórios Power BI)
        print("\n📊 Criando relatórios Power BI...")

        # Workspace fixo para todos os reports
        WORKSPACE_ID = "92c6a839-193b-41b7-bde6-5a23eefe0182"

        # Mapear unidades (1=SESI Educação, 2=SESI Saúde, 3=SENAI)
        units_map = {1: unit_sesi_educacao, 2: unit_sesi_saude, 3: unit_senai_educacao}

        # Mapear blocos
        blocos_map = {1: bloco1, 2: bloco2, 3: bloco3, 4: bloco4, 5: bloco5, 6: bloco6}

        # Reports com dados reais
        reports_data = [
            {
                "id": "778f12e7-9eef-48db-b4b3-f235f43af9a0",
                "name": "Análise de Cargos e Salarios",
                "code": "BI232",
                "units": "1,2,3",
                "step_number": "1",
            },
            {
                "id": "357a92cd-ea49-46dc-8fda-f2f1fe466fd1",
                "name": "Treinamentos",
                "code": "BI026",
                "units": "1,2,3",
                "step_number": "1",
            },
            {
                "id": "4c71c885-0468-4f19-98b2-5d2b9168b681",
                "name": "Pessoal e Encargos",
                "code": "BI030",
                "units": "1,2,3",
                "step_number": "1",
            },
            {
                "id": "7697d368-73b8-4eae-8a9e-90818125c4ee",
                "name": "Simulador de Pessoal e Encargos",
                "code": "BI200",
                "units": "1,2,3",
                "step_number": "1",
            },
            {
                "id": "8171b998-4bd5-406d-b9b2-73efe6be1c37",
                "name": "Absenteismo",
                "code": "BI207",
                "units": "1,2,3",
                "step_number": "1",
            },
            {
                "id": "c9167405-1ea0-48a7-a794-5fd48748ebc9",
                "name": "Gestão de Ativos",
                "code": "BI081",
                "units": "1,2,3",
                "step_number": "2",
            },
            {
                "id": "464355dd-b688-4ceb-a709-58c30993fa4c",
                "name": "Consultas",
                "code": "BI009",
                "units": "1,2,3",
                "step_number": "2",
            },
            {
                "id": "7c56852b-0174-4b67-919b-57426e22fffb",
                "name": "Monitoramento de Propostas",
                "code": "BI111",
                "units": "1,2,3",
                "step_number": "3",
            },
            {
                "id": "151eccfc-7fbc-4cf8-99bc-be26894b570b",
                "name": "Metas de Vendas 2025",
                "code": "BI251",
                "units": "1,2,3",
                "step_number": "3",
            },
            {
                "id": "03a6f0fe-e8a9-44f0-a44c-727832ea3188",
                "name": "EB Produção",
                "code": "BI091",
                "units": "1",
                "step_number": "4",
            },
            {
                "id": "4e5c8d46-b201-4af1-82fe-85b1d0b36ee9",
                "name": "SAC e Ouvidoria Gerencial",
                "code": "BI086",
                "units": "1,2,3",
                "step_number": "4",
            },
            {
                "id": "c9598402-6184-4f0d-9187-60b92d0e6a13",
                "name": "Desempenho Educacional",
                "code": "BI039",
                "units": "1",
                "step_number": "4",
            },
            {
                "id": "fefc0ae1-7fc3-4f5e-b502-9e4c83b4fe18",
                "name": "Matrículas SESI 2026",
                "code": "BI268",
                "units": "1",
                "step_number": "4",
            },
            {
                "id": "6fbb7a8e-2868-4b25-8ef4-9e68c3b48cd3",
                "name": "Painel Gerencial EJA",
                "code": "BI141",
                "units": "1",
                "step_number": "4",
            },
            {
                "id": "e67670a2-11c3-4cb2-9985-9e5c2fd7ad79",
                "name": "Monitoramento de Demais Ações Educativas",
                "code": "BI156",
                "units": "1",
                "step_number": "4",
            },
            {
                "id": "566fcbb8-4ded-4d95-ade3-f490e1ece3d8",
                "name": "Monitoramento e Inteligência Curricular (Centro)",
                "code": "AW026",
                "units": "1",
                "step_number": "4",
            },
            {
                "id": "09080a98-65fd-4e6d-9835-0634f43e1b57",
                "name": "Monitoramento e Inteligência Curricular (Benedito)",
                "code": "AW026",
                "units": "1",
                "step_number": "4",
            },
            {
                "id": "47f3299a-319e-443c-8372-d528d2a15ff7",
                "name": "Tela 16 (Planejamento e Controle da Operação)",
                "code": "AW018",
                "units": "1, 3",
                "step_number": "4",
            },
            {
                "id": "a0a81630-279d-4834-a3f1-2c453e540264",
                "name": "Perfil Epidemiológico",
                "code": "BI190",
                "units": "2",
                "step_number": "4",
            },
            {
                "id": "b6f1cf12-f1ba-48f8-9838-4bd404d206fc",
                "name": "Relatórios Faturamento",
                "code": "BI238",
                "units": "2",
                "step_number": "4",
            },
            {
                "id": "1713f719-6dd0-42e4-abc6-ff66a5c2fddb",
                "name": "Monitoramento Saúde",
                "code": "BI242",
                "units": "2",
                "step_number": "4",
            },
            {
                "id": "f390f9c5-4d2c-4c7e-9c43-47a2f5e8b445",
                "name": "Saúde Ocupacional S+",
                "code": "BI256",
                "units": "2",
                "step_number": "4",
            },
            {
                "id": "fa4ef9b4-76d8-4ddf-9ee1-34a3249afa84",
                "name": "Saúde Insights",
                "code": "BI263",
                "units": "2",
                "step_number": "4",
            },
            {
                "id": "3c30914c-6350-4adc-9933-a79b43b952ab",
                "name": "Gestão Esocial",
                "code": "BI094",
                "units": "2",
                "step_number": "4",
            },
            {
                "id": "147ca2eb-287b-47f9-9523-2de20ac9529c",
                "name": "Serviços de Segurança",
                "code": "BI131",
                "units": "2",
                "step_number": "4",
            },
            {
                "id": "442b3be8-c840-422c-a8ae-c8af923df954",
                "name": "Educação Corporativa",
                "code": "BI222",
                "units": "2",
                "step_number": "4",
            },
            {
                "id": "38bbebf2-1cd4-454c-b04e-e622addb321a",
                "name": "Vigência Produtos de Segurança",
                "code": "BI235",
                "units": "2",
                "step_number": "4",
            },
            {
                "id": "bcdadca1-4ad8-4312-a3fc-ca0625d56efa",
                "name": "Cresce Indústria",
                "code": "BI278",
                "units": "2",
                "step_number": "4",
            },
            {
                "id": "dcea617d-910e-4f0b-8b51-b7b62ff50726",
                "name": "EP Produção",
                "code": "BI090",
                "units": "3",
                "step_number": "4",
            },
            {
                "id": "99137375-8a8e-4e43-ad35-f05a2fdf4f12",
                "name": "Turmas Abertas SENAI",
                "code": "BI101",
                "units": "3",
                "step_number": "4",
            },
            {
                "id": "ca622f4b-36d4-4567-b382-1c9f88eb1e50",
                "name": "Matrículas por Área SENAI",
                "code": "BI135",
                "units": "3",
                "step_number": "4",
            },
            {
                "id": "8e670570-e6e5-4fec-b5ca-b7dd20d5d158",
                "name": "Disponibilidade Docente",
                "code": "BI249",
                "units": "3",
                "step_number": "4",
            },
            {
                "id": "10891c59-638d-4d4c-982c-5153d072e507",
                "name": "Metrologia",
                "code": "BI070",
                "units": "3",
                "step_number": "4",
            },
            {
                "id": "6ed64b8a-e45e-4dbc-9f7c-d18a47a68949",
                "name": "Análise Orçamentária",
                "code": "BI181",
                "units": "1,2,3",
                "step_number": "5",
            },
            {
                "id": "f1575a47-f368-436e-b468-c42740c4abf5",
                "name": "Inadimplência PF",
                "code": "BI220",
                "units": "1,2,3",
                "step_number": "5",
            },
            {
                "id": "214d215a-cc63-4c50-9359-ffeef53b885f",
                "name": "Indicador Impacto Folha",
                "code": "BI271",
                "units": "1,2,3",
                "step_number": "5",
            },
            {
                "id": "e961a703-dcd5-472b-b166-20218fa8969f",
                "name": "Inadimplência PJ",
                "code": "BI068",
                "units": "2,3",
                "step_number": "5",
            },
            {
                "id": "0b594750-1f6b-4024-817f-6c35d0143b90",
                "name": "Tela 2 (Plano de Ação)",
                "code": "AW018",
                "units": "1,2,3",
                "step_number": "6",
            },
            {
                "id": "c18b7cd3-6acb-4002-8297-8aebeb0407da",
                "name": "Gestão de Projetos",
                "code": "BI265",
                "units": "1,2,3",
                "step_number": "6",
            },
        ]

        for report_data in reports_data:
            # Criar report
            report = Report(
                report_id=report_data["id"],
                workspace_id=WORKSPACE_ID,
                name=report_data["name"],
                code=report_data["code"],
                step_id=blocos_map[int(report_data["step_number"])].id,
                # embed_url=f'https://app.powerbi.com/reportEmbed?reportId={report_data["id"]}',
            )
            
            # Adicionar ao session primeiro
            db.session.add(report)

            # Associar unidades depois de adicionar à sessão
            unit_ids = [int(u) for u in report_data["units"].split(",")]
            for unit_id in unit_ids:
                report.units.append(units_map[unit_id])

        db.session.commit()
        print("✅ Relatórios criados!")

        # Resumo
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS DADOS CRIADOS")
        print("=" * 60)
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

        print("\n📋 Blocos (Steps) - Globais para todas as unidades:")
        print("   1. Recursos Humanos")
        print("   2. Infraestrutura")
        print("   3. Comercial")
        print("   4. Operação")
        print("   5. Orçamento e Financeiro")
        print("   6. Estratégia")

        print("\n📊 Relatórios Power BI:")
        print(f"   - Total: {len(reports_data)} relatórios")
        print(f"   - Todos os relatórios estão disponíveis para as 3 unidades")
        print(f"   - Workspace: {WORKSPACE_ID}")

        print("\n�🔗 Associações Usuário → Unidades:")
        print("   - sesi.centro → SESI Educação Básica")
        print(
            "   - sesi.senai.benedito → SESI Educação Básica, SENAI Educação Profissional e STI"
        )
        print("   - sesi.saude.cambona → SESI Saúde")
        print("   - sesi.saude.tabuleiro → SESI Saúde")
        print(
            "   - sesi.senai.arapiraca → SESI Saúde, SENAI Educação Profissional e STI"
        )
        print("   - senai.poco → SENAI Educação Profissional e STI")
        print(
            "   - diretoria → SESI Educação Básica, SESI Saúde, SENAI Educação Profissional e STI"
        )

        print("\n✅ Banco populado com sucesso!")


if __name__ == "__main__":
    seed_database()
