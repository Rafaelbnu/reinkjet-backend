from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Informações básicas
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Informações pessoais
    full_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    
    # Informações da empresa
    company_name = db.Column(db.String(200), nullable=False)
    company_cnpj = db.Column(db.String(18))
    company_address = db.Column(db.Text)
    company_city = db.Column(db.String(100))
    company_state = db.Column(db.String(2))
    company_zip = db.Column(db.String(10))
    
    # Informações do contrato
    contract_number = db.Column(db.String(50))
    contract_type = db.Column(db.String(50))  # outsourcing, suprimentos, ambos
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'company_name': self.company_name,
            'company_cnpj': self.company_cnpj,
            'company_address': self.company_address,
            'company_city': self.company_city,
            'company_state': self.company_state,
            'company_zip': self.company_zip,
            'contract_number': self.contract_number,
            'contract_type': self.contract_type,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Equipment(db.Model):
    __tablename__ = 'equipment'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Informações do equipamento
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    model = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    equipment_type = db.Column(db.String(50), nullable=False)  # impressora, multifuncional, etc
    
    # Localização
    location = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100))
    
    # Status e contrato
    status = db.Column(db.String(20), nullable=False, default='active')  # active, maintenance, inactive
    contract_start = db.Column(db.Date)
    contract_end = db.Column(db.Date)
    
    # Contadores
    initial_counter_bw = db.Column(db.Integer, default=0)
    initial_counter_color = db.Column(db.Integer, default=0)
    current_counter_bw = db.Column(db.Integer, default=0)
    current_counter_color = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User', backref=db.backref('equipment', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'serial_number': self.serial_number,
            'model': self.model,
            'brand': self.brand,
            'equipment_type': self.equipment_type,
            'location': self.location,
            'department': self.department,
            'status': self.status,
            'contract_start': self.contract_start.isoformat() if self.contract_start else None,
            'contract_end': self.contract_end.isoformat() if self.contract_end else None,
            'initial_counter_bw': self.initial_counter_bw,
            'initial_counter_color': self.initial_counter_color,
            'current_counter_bw': self.current_counter_bw,
            'current_counter_color': self.current_counter_color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

