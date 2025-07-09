import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.tickets import tickets_bp
from src.routes.email import email_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configurações de produção
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'reinkjet_secret_key_2024_secure')
app.config['FLASK_ENV'] = os.environ.get('FLASK_ENV', 'production')

# Configurar CORS para permitir requisições do frontend Hostinger
frontend_url = os.environ.get('FRONTEND_URL', 'https://reinkjet.com.br')
CORS(app, 
     supports_credentials=True,
     origins=[frontend_url, 'https://www.reinkjet.com.br', 'http://localhost:5173'],
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(tickets_bp, url_prefix='/api')
app.register_blueprint(email_bp, url_prefix='/api/email')

# Configuração do banco de dados PostgreSQL (Render)
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Render fornece DATABASE_URL com postgres://, mas SQLAlchemy precisa de postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Fallback para desenvolvimento local
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Configurações para upload de arquivos
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db.init_app(app)

# Criar tabelas
with app.app_context():
    try:
        db.create_all()
        print("✅ Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Servir arquivos estáticos e SPA"""
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
    return {
        'status': 'ok', 
        'message': 'Reinkjet API is running',
        'environment': app.config['FLASK_ENV'],
        'database': 'PostgreSQL' if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI'] else 'SQLite'
    }

@app.errorhandler(404)
def not_found(error):
    return {'error': 'Endpoint não encontrado'}, 404

@app.errorhandler(500)
def internal_error(error):
    return {'error': 'Erro interno do servidor'}, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

