# app.py
from flask import Flask
from src.routes.main_routes import main_bp
from src.db.database import init_db
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'docusuite_secret_key_pro'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'attachments')

# Asegurar que el directorio de adjuntos exista
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Registrar Controladores (Blueprints)
app.register_blueprint(main_bp)

if __name__ == '__main__':
    init_db() # Inicializa SQLite si no existe
    app.run(host='0.0.0.0', port=5000)