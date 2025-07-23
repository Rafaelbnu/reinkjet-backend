from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    
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

    def set_password(self, password):
        """Hash e define a senha do usuário"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Verifica se a senha fornecida está correta"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

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

