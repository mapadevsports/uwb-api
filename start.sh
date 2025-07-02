#!/bin/bash

# Script de inicialização para o Render
echo "Iniciando aplicação UWB API..."

# As tabelas do banco de dados serão criadas/gerenciadas manualmente via pgAdmin ou migrações
# python src/create_db.py  # Esta linha pode ser removida ou comentada
flask init-db
# Iniciar aplicação com Gunicorn
exec gunicorn --config gunicorn.conf.py src.main:app
