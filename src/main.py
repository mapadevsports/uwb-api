print("Iniciando a aplicação Flask...")
import os
import sys
# DON\'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.models.uwb_data import UWBData
from src.models.ancora_uwb import AncoraUWB # Importação adicionada
from src.routes.user import user_bp
from src.routes.uwb import uwb_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))
app.config["SECRET_KEY"] = "asdf#FGSgvasgf$5$WGT"

# Habilitar CORS para permitir requisições do ESP32
CORS(app)

app.register_blueprint(user_bp, url_prefix="/api")
app.register_blueprint(uwb_bp, url_prefix="/api")

# Configuração do banco de dados
# Para desenvolvimento local, use SQLite
# Para produção no Render, use PostgreSQL
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    # Produção - PostgreSQL no Render
    # Render fornece DATABASE_URL automaticamente
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    # Desenvolvimento local - SQLite
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(os.path.dirname(__file__), "database", "app.db")}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Comando CLI para inicializar o banco de dados
@app.cli.command("init-db")
def init_db_command():
    """Cria as tabelas do banco de dados."""
    with app.app_context():
        try:
            db.drop_all() # Tenta apagar todas as tabelas (pode falhar se não existirem)
            print("Tabelas existentes apagadas (se houver).")
        except Exception as e:
            print(f"Erro ao apagar tabelas (pode ser normal se não existirem): {e}")
            db.session.rollback() # Garante que a sessão seja limpa após erro

        db.create_all()
        print("Banco de dados inicializado (tabelas criadas/recriadas).")


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, "index.html")
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, "index.html")
        else:
            return "index.html not found", 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
