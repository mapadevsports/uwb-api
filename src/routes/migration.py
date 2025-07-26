from flask import Blueprint, jsonify
from src.models.user import db
from src.models.relatorio import Relatorio
import logging

migration_bp = Blueprint('migration', __name__)

@migration_bp.route('/migration/create-relatorio-table', methods=['POST'])
def create_relatorio_table():
    """
    Endpoint para criar a tabela relatorio no banco de dados
    Use este endpoint uma vez para criar a tabela no PostgreSQL do Render
    """
    try:
        # Verificar se a tabela já existe
        inspector = db.inspect(db.engine)
        if 'relatorio' in inspector.get_table_names():
            return jsonify({
                'success': True,
                'message': 'Tabela relatorio já existe',
                'action': 'nenhuma'
            }), 200
        
        # Criar a tabela
        db.create_all()
        
        logging.info("Tabela relatorio criada com sucesso")
        
        return jsonify({
            'success': True,
            'message': 'Tabela relatorio criada com sucesso',
            'action': 'tabela_criada',
            'schema': {
                'table_name': 'relatorio',
                'columns': [
                    'id (INTEGER, PRIMARY KEY)',
                    'inicio_do_relatorio (DATETIME)',
                    'fim_do_relatorio (DATETIME)', 
                    'status (VARCHAR(20), DEFAULT: inativo)',
                    'criado_em (DATETIME, DEFAULT: now)',
                    'atualizado_em (DATETIME, DEFAULT: now, ON UPDATE: now)'
                ]
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao criar tabela relatorio: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro ao criar tabela: {str(e)}',
            'action': 'erro'
        }), 500

@migration_bp.route('/migration/check-tables', methods=['GET'])
def check_tables():
    """
    Endpoint para verificar quais tabelas existem no banco
    """
    try:
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        table_details = {}
        for table in tables:
            columns = inspector.get_columns(table)
            table_details[table] = [col['name'] for col in columns]
        
        return jsonify({
            'success': True,
            'tables': tables,
            'table_details': table_details,
            'relatorio_exists': 'relatorio' in tables
        }), 200
        
    except Exception as e:
        logging.error(f"Erro ao verificar tabelas: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro ao verificar tabelas: {str(e)}'
        }), 500

@migration_bp.route('/migration/reset-relatorio-table', methods=['POST'])
def reset_relatorio_table():
    """
    Endpoint para recriar a tabela relatorio (CUIDADO: apaga dados existentes)
    """
    try:
        # Dropar tabela se existir
        inspector = db.inspect(db.engine)
        if 'relatorio' in inspector.get_table_names():
            Relatorio.__table__.drop(db.engine)
            logging.info("Tabela relatorio removida")
        
        # Recriar tabela
        db.create_all()
        logging.info("Tabela relatorio recriada")
        
        return jsonify({
            'success': True,
            'message': 'Tabela relatorio recriada com sucesso',
            'warning': 'Todos os dados anteriores foram perdidos',
            'action': 'tabela_recriada'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao recriar tabela relatorio: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro ao recriar tabela: {str(e)}',
            'action': 'erro'
        }), 500

@migration_bp.route('/migration/health', methods=['GET'])
def migration_health():
    """Health check para o módulo de migração"""
    return jsonify({
        'status': 'OK',
        'message': 'Módulo de migração ativo',
        'endpoints': [
            'POST /api/migration/create-relatorio-table - Criar tabela relatorio',
            'GET /api/migration/check-tables - Verificar tabelas existentes',
            'POST /api/migration/reset-relatorio-table - Recriar tabela relatorio (PERIGOSO)',
            'GET /api/migration/health - Health check'
        ],
        'warning': 'Use os endpoints de migração com cuidado em produção'
    }), 200

