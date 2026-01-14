from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

# Tabela de associação N:N entre usuários e unidades
user_units = db.Table('user_units',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('unit_id', db.Integer, db.ForeignKey('units.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

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
    bi_filter_param = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    units = db.relationship('Unit', secondary=user_units, back_populates='users')
    
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
            'bi_filter_param': self.bi_filter_param,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if include_units:
            data['units'] = [unit.to_dict() for unit in self.units]
        return data

class Unit(db.Model):
    __tablename__ = 'units'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', secondary=user_units, back_populates='units')
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
            'embed_url': self.embed_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if include_units:
            data['units'] = [{'id': u.id, 'name': u.name} for u in self.units]
        else:
            data['unit_ids'] = [u.id for u in self.units]
        return data


