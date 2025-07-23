from src.models.user import db
from datetime import datetime
import uuid

class Equipment(db.Model):
    __tablename__ = 'equipment'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
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

