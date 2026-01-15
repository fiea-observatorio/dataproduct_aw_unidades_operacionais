from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

# Modelo de associação N:N entre usuários e unidades com bi_filter_param
class UserUnit(db.Model):
    __tablename__ = 'user_units'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), primary_key=True)
    bi_filter_param = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='user_units')
    unit = db.relationship('Unit', back_populates='user_units')

# Tabela de associação N:N entre reports e unidades
report_units = db.Table('report_units',
    db.Column('report_id', db.Integer, db.ForeignKey('reports.id'), primary_key=True),
    db.Column('unit_id', db.Integer, db.ForeignKey('units.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_units = db.relationship('UserUnit', back_populates='user', cascade='all, delete-orphan')
    units = db.relationship('Unit', secondary='user_units', viewonly=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_units=False):
        data = {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'role': self.role,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if include_units:
            data['units'] = [
                {
                    **unit.to_dict(),
                    'bi_filter_param': next((uu.bi_filter_param for uu in self.user_units if uu.unit_id == unit.id), None)
                }
                for unit in self.units
            ]
        return data
    
    def get_bi_filter_param(self, unit_id):
        """Get bi_filter_param for a specific unit"""
        user_unit = next((uu for uu in self.user_units if uu.unit_id == unit_id), None)
        return user_unit.bi_filter_param if user_unit else None

class Unit(db.Model):
    __tablename__ = 'units'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_units = db.relationship('UserUnit', back_populates='unit', cascade='all, delete-orphan')
    users = db.relationship('User', secondary='user_units', viewonly=True)
    reports = db.relationship('Report', secondary=report_units, back_populates='units')
    
    def to_dict(self, include_users=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if include_users:
            data['users'] = [{'id': u.id, 'username': u.username} for u in self.users]
        return data

class Step(db.Model):
    __tablename__ = 'steps'
    
    id = db.Column(db.Integer, primary_key=True)
    step_number = db.Column(db.Integer, nullable=False, unique=True)
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reports = db.relationship('Report', back_populates='step')
    
    def to_dict(self, include_reports=False):
        data = {
            'id': self.id,
            'step_number': self.step_number,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if include_reports:
            data['reports'] = [report.to_dict() for report in self.reports]
        return data

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    step_id = db.Column(db.Integer, db.ForeignKey('steps.id'), nullable=True)
    report_id = db.Column(db.String(120), nullable=False, unique=True)  # Power BI Report ID
    workspace_id = db.Column(db.String(120), nullable=False)  # Power BI Workspace ID
    dataset_id = db.Column(db.String(120))  # Power BI Dataset ID
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(120), nullable=False)
    embed_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    units = db.relationship('Unit', secondary=report_units, back_populates='reports')
    step = db.relationship('Step', back_populates='reports')
    
    def to_dict(self, include_units=False):
        data = {
            'id': self.id,
            'step_id': self.step_id,
            'report_id': self.report_id,
            'workspace_id': self.workspace_id,
            'dataset_id': self.dataset_id,
            'name': self.name,
            'code': self.code,
            'embed_url': self.embed_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if include_units:
            data['units'] = [{'id': u.id, 'name': u.name} for u in self.units]
        else:
            data['unit_ids'] = [u.id for u in self.units]
        return data
