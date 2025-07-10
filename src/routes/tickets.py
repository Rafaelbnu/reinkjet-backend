from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User
from src.models.ticket import Ticket, TicketHistory
from src.models.equipment import Equipment
from datetime import datetime

tickets_bp = Blueprint('tickets', __name__)

@tickets_bp.route('/tickets', methods=['GET'])
@jwt_required()
def get_tickets():
    """Obtém todos os chamados do usuário autenticado"""
    try:
        user_id = get_jwt_identity()
        
        # Parâmetros de filtro
        status = request.args.get('status')
        priority = request.args.get('priority')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Query base
        query = Ticket.query.filter_by(user_id=user_id)
        
        # Aplicar filtros
        if status:
            query = query.filter_by(status=status)
        if priority:
            query = query.filter_by(priority=priority)
        
        # Ordenar por data de criação (mais recentes primeiro)
        query = query.order_by(Ticket.created_at.desc())
        
        # Paginação
        tickets = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'tickets': [ticket.to_dict() for ticket in tickets.items],
            'total': tickets.total,
            'pages': tickets.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@tickets_bp.route('/tickets/<ticket_id>', methods=['GET'])
@jwt_required()
def get_ticket(ticket_id):
    """Obtém um chamado específico"""
    try:
        user_id = get_jwt_identity()
        
        ticket = Ticket.query.filter_by(
            id=ticket_id,
            user_id=user_id
        ).first()
        
        if not ticket:
            return jsonify({'error': 'Chamado não encontrado'}), 404
        
        return jsonify({'ticket': ticket.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@tickets_bp.route('/tickets', methods=['POST'])
@jwt_required()
def create_ticket():
    """Cria um novo chamado"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar campos obrigatórios
        required_fields = ['equipment_serial', 'problem_type', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        # Verificar se o equipamento pertence ao usuário
        equipment = Equipment.query.filter_by(
            serial_number=data['equipment_serial'],
            user_id=user_id
        ).first()
        
        if not equipment:
            return jsonify({'error': 'Equipamento não encontrado ou não pertence ao usuário'}), 400
        
        # Criar novo chamado
        ticket = Ticket(
            user_id=user_id,
            equipment_serial=data['equipment_serial'],
            equipment_model=equipment.model,
            equipment_location=equipment.location,
            problem_type=data['problem_type'],
            description=data['description'],
            priority=data.get('priority', 'medium')
        )
        
        db.session.add(ticket)
        db.session.flush()  # Para obter o ID do ticket
        
        # Criar entrada no histórico
        history = TicketHistory(
            ticket_id=ticket.id,
            action='created',
            description='Chamado criado pelo cliente',
            user_id=user_id
        )
        
        db.session.add(history)
        db.session.commit()
        
        return jsonify({
            'message': 'Chamado criado com sucesso',
            'ticket': ticket.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@tickets_bp.route('/tickets/<ticket_id>/close', methods=['POST'])
@jwt_required()
def close_ticket(ticket_id):
    """Fecha um chamado (apenas o cliente pode fechar seus próprios chamados)"""
    try:
        user_id = get_jwt_identity()
        
        ticket = Ticket.query.filter_by(
            id=ticket_id,
            user_id=user_id
        ).first()
        
        if not ticket:
            return jsonify({'error': 'Chamado não encontrado'}), 404
        
        if ticket.status == 'closed':
            return jsonify({'error': 'Chamado já está fechado'}), 400
        
        data = request.get_json()
        satisfaction_rating = data.get('satisfaction_rating')
        
        # Validar avaliação se fornecida
        if satisfaction_rating is not None:
            if not isinstance(satisfaction_rating, int) or satisfaction_rating < 1 or satisfaction_rating > 5:
                return jsonify({'error': 'Avaliação deve ser um número entre 1 e 5'}), 400
            ticket.satisfaction_rating = satisfaction_rating
        
        # Atualizar status
        ticket.status = 'closed'
        ticket.updated_at = datetime.utcnow()
        
        # Criar entrada no histórico
        history = TicketHistory(
            ticket_id=ticket.id,
            action='closed',
            description=f'Chamado fechado pelo cliente{f" com avaliação {satisfaction_rating}" if satisfaction_rating else ""}',
            user_id=user_id
        )
        
        db.session.add(history)
        db.session.commit()
        
        return jsonify({
            'message': 'Chamado fechado com sucesso',
            'ticket': ticket.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@tickets_bp.route('/tickets/stats', methods=['GET'])
@jwt_required()
def get_ticket_stats():
    """Obtém estatísticas dos chamados do usuário"""
    try:
        user_id = get_jwt_identity()
        
        # Contar chamados por status
        stats = {
            'total': Ticket.query.filter_by(user_id=user_id).count(),
            'open': Ticket.query.filter_by(user_id=user_id, status='open').count(),
            'in_progress': Ticket.query.filter_by(user_id=user_id, status='in_progress').count(),
            'resolved': Ticket.query.filter_by(user_id=user_id, status='resolved').count(),
            'closed': Ticket.query.filter_by(user_id=user_id, status='closed').count()
        }
        
        # Chamados por prioridade
        priority_stats = {
            'low': Ticket.query.filter_by(user_id=user_id, priority='low').count(),
            'medium': Ticket.query.filter_by(user_id=user_id, priority='medium').count(),
            'high': Ticket.query.filter_by(user_id=user_id, priority='high').count(),
            'critical': Ticket.query.filter_by(user_id=user_id, priority='critical').count()
        }
        
        # Chamados recentes (últimos 30 dias)
        thirty_days_ago = datetime.utcnow().replace(day=1)  # Simplificado para o mês atual
        recent_tickets = Ticket.query.filter(
            Ticket.user_id == user_id,
            Ticket.created_at >= thirty_days_ago
        ).count()
        
        return jsonify({
            'status_stats': stats,
            'priority_stats': priority_stats,
            'recent_tickets': recent_tickets
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

