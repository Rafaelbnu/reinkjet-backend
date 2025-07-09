from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from src.models.user import db, User, Equipment

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Registrar novo usuário/cliente"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['username', 'email', 'password', 'full_name', 'company_name']
        
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        # Verificar se usuário já existe
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Nome de usuário já existe'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'E-mail já cadastrado'}), 400
        
        # Criar novo usuário
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            full_name=data['full_name'],
            phone=data.get('phone'),
            company_name=data['company_name'],
            company_cnpj=data.get('company_cnpj'),
            company_address=data.get('company_address'),
            company_city=data.get('company_city'),
            company_state=data.get('company_state'),
            company_zip=data.get('company_zip'),
            contract_number=data.get('contract_number'),
            contract_type=data.get('contract_type', 'outsourcing')
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuário registrado com sucesso',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Fazer login"""
    try:
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username e password são obrigatórios'}), 400
        
        # Buscar usuário
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Conta desativada'}), 401
        
        # Atualizar último login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Criar sessão
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            'message': 'Login realizado com sucesso',
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Fazer logout"""
    try:
        session.clear()
        return jsonify({'message': 'Logout realizado com sucesso'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """Obter perfil do usuário logado"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        return jsonify({'user': user.to_dict()})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    """Atualizar perfil do usuário"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        data = request.get_json()
        
        # Campos que podem ser atualizados
        updatable_fields = ['full_name', 'phone', 'company_address', 
                           'company_city', 'company_state', 'company_zip']
        
        for field in updatable_fields:
            if field in data:
                setattr(user, field, data[field])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Perfil atualizado com sucesso',
            'user': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """Alterar senha"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Senha atual e nova senha são obrigatórias'}), 400
        
        if not check_password_hash(user.password_hash, current_password):
            return jsonify({'error': 'Senha atual incorreta'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'Nova senha deve ter pelo menos 6 caracteres'}), 400
        
        user.password_hash = generate_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Senha alterada com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Rota para criar usuários de demonstração
@auth_bp.route('/create-demo-user', methods=['POST'])
def create_demo_user():
    """Criar usuário de demonstração"""
    try:
        # Verificar se já existe
        demo_user = User.query.filter_by(username='demo').first()
        if demo_user:
            return jsonify({
                'message': 'Usuário demo já existe',
                'user': demo_user.to_dict()
            })
        
        # Criar usuário demo
        user = User(
            username='demo',
            email='demo@reinkjet.com.br',
            password_hash=generate_password_hash('demo123'),
            full_name='João Silva',
            phone='(47) 99999-9999',
            company_name='Empresa Demo Ltda',
            company_cnpj='12.345.678/0001-90',
            company_address='Rua das Flores, 123',
            company_city='Blumenau',
            company_state='SC',
            company_zip='89010-000',
            contract_number='CT-2024-001',
            contract_type='outsourcing'
        )
        
        db.session.add(user)
        db.session.flush()
        
        # Criar equipamentos demo
        equipment1 = Equipment(
            user_id=user.id,
            serial_number='HP123456789',
            model='LaserJet Pro M404dn',
            brand='HP',
            equipment_type='impressora',
            location='Recepção - Térreo',
            department='Administrativo',
            status='active',
            current_counter_bw=15420,
            current_counter_color=0
        )
        
        equipment2 = Equipment(
            user_id=user.id,
            serial_number='EP987654321',
            model='EcoTank L3150',
            brand='Epson',
            equipment_type='multifuncional',
            location='Sala de Reuniões - 2º Andar',
            department='Comercial',
            status='active',
            current_counter_bw=8750,
            current_counter_color=2340
        )
        
        db.session.add(equipment1)
        db.session.add(equipment2)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuário demo criado com sucesso',
            'user': user.to_dict(),
            'credentials': {
                'username': 'demo',
                'password': 'demo123'
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

