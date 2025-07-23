from src.models.user import db
from datetime import datetime
import uuid

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)    
    # Informações do equipamento
    equipment_serial = db.Column(db.String(100), nullable=False)
    equipment_model = db.Column(db.String(100), nullable=False)
    equipment_location = db.Column(db.String(200), nullable=False)
    
    # Informações do problema
    problem_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), nullable=False, default='medium')  # low, medium, high, critical
    
    # Status e resolução
    status = db.Column(db.String(20), nullable=False, default='open')  # open, in_progress, resolved, closed
    assigned_to = db.Column(db.String(100))
    resolution = db.Column(db.Text)
    satisfaction_rating = db.Column(db.Integer)  # 1-5
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    # Relacionamentos
    user = db.relationship('User', backref=db.backref('tickets', lazy=True))
    attachments = db.relationship('Attachment', backref='ticket', lazy=True, cascade='all, delete-orphan')
    history = db.relationship('TicketHistory', backref='ticket', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Ticket, self).__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'equipment_serial': self.equipment_serial,
            'equipment_model': self.equipment_model,
            'equipment_location': self.equipment_location,
            'problem_type': self.problem_type,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'resolution': self.resolution,
            'satisfaction_rating': self.satisfaction_rating,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'user': self.user.to_dict() if self.user else None,
            'attachments': [att.to_dict() for att in self.attachments],
            'history': [hist.to_dict() for hist in self.history]
        }

class Attachment(db.Model):
    __tablename__ = 'attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'filename': self.filename,
            'original_name': self.original_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class TicketHistory(db.Model):
    __tablename__ = 'ticket_history'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer)  # Quem fez a ação
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'action': self.action,
            'description': self.description,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

