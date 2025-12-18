from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

# Tabela de associação N:N entre usuários e unidades
user_units = db.Table('user_units',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('unit_id', db.Integer, db.ForeignKey('units.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    units = db.relationship('Unit', secondary=user_units, back_populates='users')
    access_logs = db.relationship('AccessLog', back_populates='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_units=False):
        data = {
            'id': self.id,
            'username': self.username,
            'role': self.role,
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
    links = db.relationship('Link', back_populates='unit', cascade='all, delete-orphan')
    reports = db.relationship('Report', back_populates='unit', cascade='all, delete-orphan')
    
    def to_dict(self, include_users=False, include_links=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if include_users:
            data['users'] = [{'id': u.id, 'username': u.username} for u in self.users]
        if include_links:
            data['links'] = [link.to_dict() for link in self.links]
        return data

class Link(db.Model):
    __tablename__ = 'links'
    
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    unit = db.relationship('Unit', back_populates='links')
    
    def to_dict(self):
        return {
            'id': self.id,
            'unit_id': self.unit_id,
            'name': self.name,
            'url': self.url,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    report_id = db.Column(db.String(120), nullable=False, unique=True)  # Power BI Report ID
    workspace_id = db.Column(db.String(120), nullable=False)  # Power BI Workspace ID
    dataset_id = db.Column(db.String(120))  # Power BI Dataset ID
    name = db.Column(db.String(200), nullable=False)
    embed_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    unit = db.relationship('Unit', back_populates='reports')
    access_logs = db.relationship('AccessLog', back_populates='report', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'unit_id': self.unit_id,
            'report_id': self.report_id,
            'workspace_id': self.workspace_id,
            'dataset_id': self.dataset_id,
            'name': self.name,
            'embed_url': self.embed_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class AccessLog(db.Model):
    __tablename__ = 'access_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'), nullable=False)
    action = db.Column(db.String(50), default='view')  # view, embed_token_generated
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = db.relationship('User', back_populates='access_logs')
    report = db.relationship('Report', back_populates='access_logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'report_id': self.report_id,
            'action': self.action,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat()
        }
