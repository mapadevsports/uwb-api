from flask import Blueprint, jsonify, request
from src.models.relatorio import Relatorio, db
from datetime import datetime
import logging

relatorio_bp = Blueprint('relatorio', __name__)

@relatorio_bp.route('/relatorio/iniciar', methods=['POST'])
def iniciar_relatorio():
    """
    Endpoint para iniciar um novo relatório
    Chamado quando o botão flash é pressionado pela primeira vez
    """
    try:
        # Verificar se já existe um relatório ativo (que tem inicio mas não tem fim)
        relatorio_ativo = Relatorio.query.filter(
            Relatorio.inicio_do_relatorio.isnot(None),
            Relatorio.fim_do_relatorio.is_(None)
        ).first()
        
        if relatorio_ativo:
            return jsonify({
                'success': False,
                'message': 'Já existe um relatório ativo',
                'relatorio_ativo': relatorio_ativo.to_dict()
            }), 400
        
        # Criar novo relatório
        novo_relatorio = Relatorio(
            inicio_do_relatorio=datetime.utcnow()
        )
        
        db.session.add(novo_relatorio)
        db.session.commit()
        
        logging.info(f"Novo relatório iniciado: ID {novo_relatorio.relatorio_number}")
        
        return jsonify({
            'success': True,
            'message': 'Relatório iniciado com sucesso',
            'relatorio': novo_relatorio.to_dict(),
            'leituras_habilitadas': True
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao iniciar relatório: {e}")
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@relatorio_bp.route('/relatorio/finalizar', methods=['POST'])
def finalizar_relatorio():
    """
    Endpoint para finalizar o relatório ativo
    Chamado quando o botão flash é pressionado novamente
    """
    try:
        # Buscar relatório ativo (que tem inicio mas não tem fim)
        relatorio_ativo = Relatorio.query.filter(
            Relatorio.inicio_do_relatorio.isnot(None),
            Relatorio.fim_do_relatorio.is_(None)
        ).first()
        
        if not relatorio_ativo:
            return jsonify({
                'success': False,
                'message': 'Nenhum relatório ativo encontrado'
            }), 400
        
        # Finalizar relatório
        relatorio_ativo.fim_do_relatorio = datetime.utcnow()
        
        db.session.commit()
        
        logging.info(f"Relatório finalizado: ID {relatorio_ativo.relatorio_number}")
        
        return jsonify({
            'success': True,
            'message': 'Relatório finalizado com sucesso',
            'relatorio': relatorio_ativo.to_dict(),
            'leituras_habilitadas': False
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao finalizar relatório: {e}")
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@relatorio_bp.route('/relatorio/status', methods=['GET'])
def status_relatorio():
    """
    Endpoint para verificar o status atual do relatório
    Usado pelo ESP32 para saber se deve fazer leituras
    """
    try:
        # Buscar relatório ativo (que tem inicio mas não tem fim)
        relatorio_ativo = Relatorio.query.filter(
            Relatorio.inicio_do_relatorio.isnot(None),
            Relatorio.fim_do_relatorio.is_(None)
        ).first()
        
        if relatorio_ativo:
            return jsonify({
                'relatorio_ativo': True,
                'leituras_habilitadas': True,
                'relatorio': relatorio_ativo.to_dict()
            }), 200
        else:
            return jsonify({
                'relatorio_ativo': False,
                'leituras_habilitadas': False,
                'message': 'Nenhum relatório ativo'
            }), 200
            
    except Exception as e:
        logging.error(f"Erro ao verificar status do relatório: {e}")
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@relatorio_bp.route('/relatorio/historico', methods=['GET'])
def historico_relatorios():
    """
    Endpoint para recuperar histórico de relatórios
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        relatorios = Relatorio.query.order_by(Relatorio.relatorio_number.desc()).limit(limit).all()
        
        return jsonify({
            'relatorios': [relatorio.to_dict() for relatorio in relatorios],
            'total': len(relatorios)
        }), 200
        
    except Exception as e:
        logging.error(f"Erro ao recuperar histórico: {e}")
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@relatorio_bp.route('/relatorio/<int:relatorio_number>', methods=['GET'])
def obter_relatorio(relatorio_number):
    """
    Endpoint para obter detalhes de um relatório específico
    """
    try:
        relatorio = Relatorio.query.get(relatorio_number)
        
        if not relatorio:
            return jsonify({'error': 'Relatório não encontrado'}), 404
        
        return jsonify({
            'relatorio': relatorio.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Erro ao obter relatório: {e}")
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@relatorio_bp.route('/relatorio/health', methods=['GET'])
def health_check_relatorio():
    """Health check específico para o módulo de relatórios"""
    try:
        # Contar relatórios por status
        total_relatorios = Relatorio.query.count()
        relatorios_ativos = Relatorio.query.filter(
            Relatorio.inicio_do_relatorio.isnot(None),
            Relatorio.fim_do_relatorio.is_(None)
        ).count()
        relatorios_finalizados = Relatorio.query.filter(
            Relatorio.inicio_do_relatorio.isnot(None),
            Relatorio.fim_do_relatorio.isnot(None)
        ).count()
        
        return jsonify({
            'status': 'OK',
            'message': 'Módulo de relatórios funcionando',
            'estatisticas': {
                'total_relatorios': total_relatorios,
                'relatorios_ativos': relatorios_ativos,
                'relatorios_finalizados': relatorios_finalizados
            },
            'endpoints_disponiveis': [
                '/api/relatorio/iniciar',
                '/api/relatorio/finalizar', 
                '/api/relatorio/status',
                '/api/relatorio/historico',
                '/api/relatorio/<relatorio_number>'
            ],
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logging.error(f"Erro no health check: {e}")
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

