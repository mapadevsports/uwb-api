#!/bin/bash

# Script de inicialização para o Render
echo "Iniciando aplicação UWB API..."

# Adiciona o diretório 'src' ao PYTHONPATH para que os módulos sejam encontrados
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# Executa o comando para inicializar/atualizar o banco de dados usando python -m flask
python -m flask init-db

# Iniciar aplicação com Gunicorn
exec gunicorn --config gunicorn.conf.py src.main:app
