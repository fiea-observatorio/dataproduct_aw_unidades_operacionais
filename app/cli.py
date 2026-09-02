"""Comandos de terminal para gerenciar os acessos via iDigital.

Com o login por senha desativado, os vínculos e-mail -> perfil de acesso são
administrados por aqui (não há mais como obter um JWT de admin para usar os
endpoints HTTP):

    flask idigital list
    flask idigital add fulano@sistemafiea.com.br senai.poco
    flask idigital remove fulano@sistemafiea.com.br
    flask idigital profiles
"""
import click
from flask.cli import AppGroup

from app import db
from app.models import IdigitalUser, User

idigital_cli = AppGroup('idigital', help='Gerencia os acessos via iDigital.')


@idigital_cli.command('list')
def list_mappings():
    """Lista os e-mails cadastrados e o perfil de acesso de cada um."""
    mappings = IdigitalUser.query.order_by(IdigitalUser.email).all()
    if not mappings:
        click.echo('Nenhum e-mail cadastrado.')
        return
    for mapping in mappings:
        click.echo(f'{mapping.email} -> {mapping.user.username} (user_id {mapping.user_id})')


@idigital_cli.command('add')
@click.argument('email')
@click.argument('perfil')
def add_mapping(email, perfil):
    """Dá ao EMAIL o mesmo acesso do PERFIL (username legado, ex.: senai.poco)."""
    email = email.strip().lower()
    if '@' not in email:
        raise click.ClickException(f'E-mail inválido: {email}')

    user = User.query.filter_by(username=perfil).first()
    if not user:
        profiles = ', '.join(u.username for u in User.query.order_by(User.username))
        raise click.ClickException(f'Perfil "{perfil}" não existe. Perfis: {profiles}')

    existing = IdigitalUser.query.filter(db.func.lower(IdigitalUser.email) == email).first()
    if existing:
        raise click.ClickException(
            f'{email} já está cadastrado (perfil {existing.user.username}). '
            'Remova antes de recadastrar.'
        )

    db.session.add(IdigitalUser(email=email, user_id=user.id))
    db.session.commit()

    units = ', '.join(u.name for u in user.units) or 'nenhuma unidade'
    click.echo(f'{email} agora tem o acesso de {user.username}: {units}')


@idigital_cli.command('remove')
@click.argument('email')
def remove_mapping(email):
    """Remove o acesso do EMAIL."""
    email = email.strip().lower()
    mapping = IdigitalUser.query.filter(db.func.lower(IdigitalUser.email) == email).first()
    if not mapping:
        raise click.ClickException(f'{email} não está cadastrado.')

    db.session.delete(mapping)
    db.session.commit()
    click.echo(f'{email} removido.')


@idigital_cli.command('profiles')
def list_profiles():
    """Lista os perfis de acesso disponíveis e suas unidades."""
    for user in User.query.order_by(User.id).all():
        units = ', '.join(
            f'{u.name} (bi_filter_param {user.get_bi_filter_param(u.id)})' for u in user.units
        ) or 'nenhuma unidade'
        click.echo(f'{user.username} (id {user.id}, role {user.role}): {units}')
