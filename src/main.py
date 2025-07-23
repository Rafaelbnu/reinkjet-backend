import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.tickets import tickets_bp
from src.routes.equipment import equipment_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'reinkjet_client_area_secret_key_2024'
app.config['JWT_SECRET_KEY'] = 'reinkjet_jwt_secret_key_2024'

# Configurar CORS
CORS(app, supports_credentials=True)

# Configurar JWT
jwt = JWTManager(app)

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(tickets_bp, url_prefix='/api')
app.register_blueprint(equipment_bp, url_prefix='/api')

# Configuração do banco de dados
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://reinkjet_user:uawaTmmU5x6gH6MPNBlzMrGXGsKspZVm@dpg-d1na4c63jp1c7382rv30-a.oregon-postgres.render.com/reinkjet"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Criar tabelas
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {'status': 'ok', 'message': 'Reinkjet Client Area API is running'}

@app.errorhandler(404)
def not_found(error):
    return {'error': 'Endpoint não encontrado'}, 404

@app.errorhandler(500)
def internal_error(error):
    return {'error': 'Erro interno do servidor'}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
