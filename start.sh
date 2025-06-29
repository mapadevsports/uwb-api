#!/bin/bash

# Script de inicialização para o Render
echo "Iniciando aplicação UWB API..."

# Executar migrações do banco de dados
# Usamos um script Python separado para garantir que __file__ esteja definido
python -c "from src.main import app, db; with app.app_context(): db.create_all(); print(\'Tabelas do banco de dados criadas/verificadas com sucesso\')"

# Iniciar aplicação com Gunicorn
exec gunicorn --config gunicorn.conf.py src.main:app
