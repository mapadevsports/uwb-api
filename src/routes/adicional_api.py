from flask import Blueprint, request, jsonify
from src.models.relatorio import Relatorio, db
from datetime import datetime
import json
import logging

relatorio_bp = Blueprint('relatorio', __name__)

@relatorio_bp.route('/relatorio/iniciar', methods=['POST'])
def iniciar_relatorio():
    """
    Inicia um novo relatório, recebendo dados como JSON (padrão) ou texto cru (ex: Kodular).
    """
    try:
        # Verificar se já existe um relatório ativo
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

        # Tentar carregar o corpo como JSON padrão ou texto cru
        try:
            # Primeiro tenta como JSON real
            data = request.get_json(force=True)
        except:
            # Se falhar, tenta como string crua vinda do Kodular
            raw_data = request.get_data(as_text=True)
            data = json.loads(raw_data)

        # Extrair kx e ky
        kx_value = data.get('kx')
        ky_value = data.get('ky')

        # Criar novo relatório
        novo_relatorio = Relatorio(
            inicio_do_relatorio=datetime.utcnow(),
            kx=str(kx_value) if kx_value is not None else None,
            ky=str(ky_value) if ky_value is not None else None
        )

        db.session.add(novo_relatorio)
        db.session.commit()

        logging.info(f"Novo relatório iniciado: ID {novo_relatorio.relatorio_number}, Kx={kx_value}, Ky={ky_value}")

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
