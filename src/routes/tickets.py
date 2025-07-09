from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import uuid
import requests
from datetime import datetime
from src.models.user import db, User, Equipment
from src.models.ticket import Ticket, Attachment, TicketHistory

tickets_bp = Blueprint('tickets', __name__)

# Configurações para upload de arquivos
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_upload_folder():
    upload_path = os.path.join(current_app.static_folder, UPLOAD_FOLDER)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    return upload_path

@tickets_bp.route('/tickets', methods=['GET'])
def get_tickets():
    """Listar chamados do usuário"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id é obrigatório'}), 400
        
        # Verificar se o usuário existe
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Filtros opcionais
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
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/tickets', methods=['POST'])
def create_ticket():
    """Criar novo chamado técnico"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['user_id', 'equipment_serial', 'equipment_model', 
                          'equipment_location', 'problem_type', 'description']
        
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        # Verificar se o usuário existe
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Criar novo chamado
        ticket = Ticket(
            user_id=data['user_id'],
            equipment_serial=data['equipment_serial'],
            equipment_model=data['equipment_model'],
            equipment_location=data['equipment_location'],
            problem_type=data['problem_type'],
            description=data['description'],
            priority=data.get('priority', 'medium')
        )
        
        db.session.add(ticket)
        db.session.flush()  # Para obter o ID do ticket
        
        # Adicionar entrada no histórico
        history = TicketHistory(
            ticket_id=ticket.id,
            action='created',
            description=f'Chamado criado pelo usuário {user.full_name}',
            user_id=data['user_id']
        )
        db.session.add(history)
        
        db.session.commit()
        
        # Enviar email de notificação
        try:
            email_data = {
                'ticket_id': ticket.ticket_number,
                'customer_name': user.full_name,
                'equipment': f"{data['equipment_model']} - {data['equipment_serial']}",
                'issue_type': data['problem_type'],
                'description': data['description'],
                'priority': data.get('priority', 'medium')
            }
            
            # Fazer requisição para enviar email
            requests.post(
                f"{request.host_url}api/email/send-ticket-notification",
                json=email_data,
                timeout=5
            )
        except Exception as email_error:
            # Log do erro mas não falha a criação do chamado
            print(f"Erro ao enviar email: {email_error}")
        
        return jsonify({
            'message': 'Chamado criado com sucesso',
            'ticket': ticket.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/tickets/<ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """Obter detalhes de um chamado específico"""
    try:
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Chamado não encontrado'}), 404
        
        return jsonify({'ticket': ticket.to_dict()})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/tickets/<ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    """Atualizar chamado (usado principalmente pela equipe técnica)"""
    try:
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Chamado não encontrado'}), 404
        
        data = request.get_json()
        
        # Campos que podem ser atualizados
        updatable_fields = ['status', 'assigned_to', 'resolution', 'priority']
        
        old_status = ticket.status
        
        for field in updatable_fields:
            if field in data:
                setattr(ticket, field, data[field])
        
        # Se o status mudou para resolved, definir data de resolução
        if data.get('status') == 'resolved' and old_status != 'resolved':
            ticket.resolved_at = datetime.utcnow()
        
        ticket.updated_at = datetime.utcnow()
        
        # Adicionar entrada no histórico
        if 'status' in data and data['status'] != old_status:
            history = TicketHistory(
                ticket_id=ticket.id,
                action='status_changed',
                description=f'Status alterado de {old_status} para {data["status"]}',
                user_id=data.get('updated_by')
            )
            db.session.add(history)
        
        if 'resolution' in data and data['resolution']:
            history = TicketHistory(
                ticket_id=ticket.id,
                action='resolution_added',
                description='Resolução adicionada ao chamado',
                user_id=data.get('updated_by')
            )
            db.session.add(history)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Chamado atualizado com sucesso',
            'ticket': ticket.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/tickets/<ticket_id>/attachments', methods=['POST'])
def upload_attachment(ticket_id):
    """Upload de anexos para um chamado"""
    try:
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Chamado não encontrado'}), 404
        
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de arquivo não permitido'}), 400
        
        # Criar pasta de upload se não existir
        upload_path = create_upload_folder()
        
        # Gerar nome único para o arquivo
        filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
        file_path = os.path.join(upload_path, filename)
        
        # Salvar arquivo
        file.save(file_path)
        
        # Obter informações do arquivo
        file_size = os.path.getsize(file_path)
        
        # Criar registro no banco
        attachment = Attachment(
            ticket_id=ticket_id,
            filename=filename,
            original_name=file.filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type or 'application/octet-stream'
        )
        
        db.session.add(attachment)
        
        # Adicionar entrada no histórico
        history = TicketHistory(
            ticket_id=ticket_id,
            action='attachment_added',
            description=f'Anexo adicionado: {file.filename}',
            user_id=request.form.get('user_id')
        )
        db.session.add(history)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Anexo enviado com sucesso',
            'attachment': attachment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/tickets/<ticket_id>/rating', methods=['POST'])
def rate_ticket(ticket_id):
    """Avaliar atendimento do chamado"""
    try:
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'error': 'Chamado não encontrado'}), 404
        
        if ticket.status != 'resolved':
            return jsonify({'error': 'Só é possível avaliar chamados resolvidos'}), 400
        
        data = request.get_json()
        rating = data.get('rating')
        
        if not rating or rating < 1 or rating > 5:
            return jsonify({'error': 'Avaliação deve ser entre 1 e 5'}), 400
        
        ticket.satisfaction_rating = rating
        ticket.updated_at = datetime.utcnow()
        
        # Adicionar entrada no histórico
        history = TicketHistory(
            ticket_id=ticket_id,
            action='rated',
            description=f'Chamado avaliado com {rating} estrelas',
            user_id=data.get('user_id')
        )
        db.session.add(history)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Avaliação registrada com sucesso',
            'ticket': ticket.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/equipment', methods=['GET'])
def get_user_equipment():
    """Listar equipamentos do usuário"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id é obrigatório'}), 400
        
        equipment = Equipment.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'equipment': [eq.to_dict() for eq in equipment]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Estatísticas para o dashboard do cliente"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id é obrigatório'}), 400
        
        # Contar chamados por status
        open_tickets = Ticket.query.filter_by(user_id=user_id, status='open').count()
        in_progress_tickets = Ticket.query.filter_by(user_id=user_id, status='in_progress').count()
        resolved_tickets = Ticket.query.filter_by(user_id=user_id, status='resolved').count()
        total_tickets = Ticket.query.filter_by(user_id=user_id).count()
        
        # Contar equipamentos
        total_equipment = Equipment.query.filter_by(user_id=user_id).count()
        active_equipment = Equipment.query.filter_by(user_id=user_id, status='active').count()
        
        # Avaliação média
        avg_rating = db.session.query(db.func.avg(Ticket.satisfaction_rating)).filter(
            Ticket.user_id == user_id,
            Ticket.satisfaction_rating.isnot(None)
        ).scalar()
        
        return jsonify({
            'tickets': {
                'open': open_tickets,
                'in_progress': in_progress_tickets,
                'resolved': resolved_tickets,
                'total': total_tickets
            },
            'equipment': {
                'total': total_equipment,
                'active': active_equipment
            },
            'avg_rating': round(avg_rating, 1) if avg_rating else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

