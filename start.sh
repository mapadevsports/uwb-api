#!/bin/bash

# Script de inicialização para o Render
echo "Iniciando aplicação UWB API..."

# Executar migrações do banco de dados se necessário
python -c "
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.main import app, db
with app.app_context():
    db.create_all()
    print('Tabelas do banco de dados criadas/verificadas com sucesso')
"

# Iniciar aplicação com Gunicorn
exec gunicorn --config gunicorn.conf.py src.main:app

