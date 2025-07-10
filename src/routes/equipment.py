from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User
from src.models.equipment import Equipment
from datetime import datetime

equipment_bp = Blueprint('equipment', __name__)

@equipment_bp.route('/equipment', methods=['GET'])
@jwt_required()
def get_equipment():
    """Obtém todos os equipamentos do usuário autenticado"""
    try:
        user_id = get_jwt_identity()
        
        # Parâmetros de filtro
        status = request.args.get('status')
        equipment_type = request.args.get('type')
        location = request.args.get('location')
        
        # Query base
        query = Equipment.query.filter_by(user_id=user_id)
        
        # Aplicar filtros
        if status:
            query = query.filter_by(status=status)
        if equipment_type:
            query = query.filter_by(equipment_type=equipment_type)
        if location:
            query = query.filter(Equipment.location.ilike(f'%{location}%'))
        
        # Ordenar por localização
        equipment_list = query.order_by(Equipment.location, Equipment.model).all()
        
        return jsonify({
            'equipment': [eq.to_dict() for eq in equipment_list],
            'total': len(equipment_list)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@equipment_bp.route('/equipment/<equipment_id>', methods=['GET'])
@jwt_required()
def get_equipment_detail(equipment_id):
    """Obtém detalhes de um equipamento específico"""
    try:
        user_id = get_jwt_identity()
        
        equipment = Equipment.query.filter_by(
            id=equipment_id,
            user_id=user_id
        ).first()
        
        if not equipment:
            return jsonify({'error': 'Equipamento não encontrado'}), 404
        
        return jsonify({'equipment': equipment.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@equipment_bp.route('/equipment/stats', methods=['GET'])
@jwt_required()
def get_equipment_stats():
    """Obtém estatísticas dos equipamentos do usuário"""
    try:
        user_id = get_jwt_identity()
        
        # Contar equipamentos por status
        stats = {
            'total': Equipment.query.filter_by(user_id=user_id).count(),
            'active': Equipment.query.filter_by(user_id=user_id, status='active').count(),
            'maintenance': Equipment.query.filter_by(user_id=user_id, status='maintenance').count(),
            'inactive': Equipment.query.filter_by(user_id=user_id, status='inactive').count()
        }
        
        # Equipamentos por tipo
        type_stats = {}
        equipment_types = db.session.query(Equipment.equipment_type).filter_by(user_id=user_id).distinct().all()
        for (eq_type,) in equipment_types:
            type_stats[eq_type] = Equipment.query.filter_by(
                user_id=user_id, 
                equipment_type=eq_type
            ).count()
        
        # Equipamentos por localização
        location_stats = {}
        locations = db.session.query(Equipment.location).filter_by(user_id=user_id).distinct().all()
        for (location,) in locations:
            location_stats[location] = Equipment.query.filter_by(
                user_id=user_id, 
                location=location
            ).count()
        
        # Contadores totais (impressões)
        total_bw = db.session.query(
            db.func.sum(Equipment.current_counter_bw - Equipment.initial_counter_bw)
        ).filter_by(user_id=user_id).scalar() or 0
        
        total_color = db.session.query(
            db.func.sum(Equipment.current_counter_color - Equipment.initial_counter_color)
        ).filter_by(user_id=user_id).scalar() or 0
        
        return jsonify({
            'status_stats': stats,
            'type_stats': type_stats,
            'location_stats': location_stats,
            'printing_stats': {
                'total_bw_prints': total_bw,
                'total_color_prints': total_color,
                'total_prints': total_bw + total_color
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@equipment_bp.route('/equipment/locations', methods=['GET'])
@jwt_required()
def get_equipment_locations():
    """Obtém lista de localizações dos equipamentos do usuário"""
    try:
        user_id = get_jwt_identity()
        
        locations = db.session.query(Equipment.location).filter_by(
            user_id=user_id
        ).distinct().all()
        
        location_list = [location[0] for location in locations if location[0]]
        
        return jsonify({'locations': sorted(location_list)}), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@equipment_bp.route('/equipment/types', methods=['GET'])
@jwt_required()
def get_equipment_types():
    """Obtém lista de tipos de equipamentos do usuário"""
    try:
        user_id = get_jwt_identity()
        
        types = db.session.query(Equipment.equipment_type).filter_by(
            user_id=user_id
        ).distinct().all()
        
        type_list = [eq_type[0] for eq_type in types if eq_type[0]]
        
        return jsonify({'types': sorted(type_list)}), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

