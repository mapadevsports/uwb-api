from flask import Blueprint, jsonify, request
from src.models.uwb_data import UWBData, UWBDataProcessada, db
from datetime import datetime

uwb_bp = Blueprint('uwb', __name__)

@uwb_bp.route('/uwb/data', methods=['POST'])
def receive_uwb_data():
    """
    Endpoint para receber dados UWB do ESP32 com processamento automático
    Espera um JSON no formato:
    {
        "id": "4",
        "range": [6, 59, 126, 0, 0, 0, 0, 0]
    }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'Nenhum dado JSON fornecido'}), 400
        
        # Validar se os campos obrigatórios estão presentes
        if 'id' not in data or 'range' not in data:
            return jsonify({'error': 'Campos obrigatórios: id, range'}), 400
        
        tag_id = str(data['id'])
        range_values = data['range']
        
        # Validar se range tem exatamente 8 valores
        if not isinstance(range_values, list) or len(range_values) != 8:
            return jsonify({'error': 'Range deve ser uma lista com exatamente 8 valores'}), 400
        
        # Criar novo registro UWB (dados originais)
        uwb_data = UWBData(
            tag_number=tag_id,
            da0=float(range_values[0]),
            da1=float(range_values[1]),
            da2=float(range_values[2]),
            da3=float(range_values[3]),
            da4=float(range_values[4]),
            da5=float(range_values[5]),
            da6=float(range_values[6]),
            da7=float(range_values[7]),
            criado_em=datetime.utcnow()
        )
        
        # Salvar dados originais no banco
        db.session.add(uwb_data)
        
        # ===== PROCESSAMENTO AUTOMÁTICO =====
        # Criar registro processado automaticamente (+1 em cada valor)
        uwb_data_processada = UWBDataProcessada(
            tag_number=tag_id,
            da0=(float(range_values[0]) if range_values[0] is not None else 0) + 1,
            da1=(float(range_values[1]) if range_values[1] is not None else 0) + 1,
            da2=(float(range_values[2]) if range_values[2] is not None else 0) + 1,
            da3=(float(range_values[3]) if range_values[3] is not None else 0) + 1,
            da4=(float(range_values[4]) if range_values[4] is not None else 0) + 1,
            da5=(float(range_values[5]) if range_values[5] is not None else 0) + 1,
            da6=(float(range_values[6]) if range_values[6] is not None else 0) + 1,
            da7=(float(range_values[7]) if range_values[7] is not None else 0) + 1,
            criado_em=datetime.utcnow()
        )
        
        # Salvar dados processados no banco
        db.session.add(uwb_data_processada)
        
        # Commit de ambas as operações
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Dados UWB salvos e processados automaticamente',
            'data_original': uwb_data.to_dict(),
            'data_processada': uwb_data_processada.to_dict()
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Erro de conversão de dados: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@uwb_bp.route('/uwb/data', methods=['GET'])
def get_uwb_data():
    """
    Endpoint para recuperar dados UWB (para testes)
    """
    try:
        # Pegar os últimos 50 registros
        uwb_records = UWBData.query.order_by(UWBData.criado_em.desc()).limit(50).all()
        return jsonify([record.to_dict() for record in uwb_records])
    except Exception as e:
        return jsonify({'error': f'Erro ao recuperar dados: {str(e)}'}), 500

@uwb_bp.route('/uwb/data/<tag_number>', methods=['GET'])
def get_uwb_data_by_tag(tag_number):
    """
    Endpoint para recuperar dados UWB de uma tag específica
    """
    try:
        uwb_records = UWBData.query.filter_by(tag_number=tag_number).order_by(UWBData.criado_em.desc()).limit(50).all()
        return jsonify([record.to_dict() for record in uwb_records])
    except Exception as e:
        return jsonify({'error': f'Erro ao recuperar dados: {str(e)}'}), 500

@uwb_bp.route('/uwb/data-processada', methods=['GET'])
def get_uwb_data_processada():
    """
    Endpoint para recuperar dados processados
    """
    try:
        uwb_records = UWBDataProcessada.query.order_by(UWBDataProcessada.criado_em.desc()).limit(50).all()
        return jsonify([record.to_dict() for record in uwb_records])
    except Exception as e:
        return jsonify({'error': f'Erro ao recuperar dados processados: {str(e)}'}), 500

@uwb_bp.route('/uwb/health', methods=['GET'])
def health_check():
    """
    Endpoint simples para verificar se a API está funcionando
    """
    return jsonify({
        'status': 'OK',
        'message': 'API UWB está funcionando com processamento automático',
        'timestamp': datetime.utcnow().isoformat()
    })

# Manter o endpoint manual para compatibilidade (opcional)
@uwb_bp.route('/uwb/processar', methods=['POST'])
def processar_uwb():
    """
    Endpoint manual para processamento (mantido para compatibilidade)
    NOTA: Com processamento automático, este endpoint pode não ser mais necessário
    """
    try:
        dados = UWBData.query.all()

        for dado in dados:
            nova_linha = UWBDataProcessada(
                tag_number=dado.tag_number,
                da0=(dado.da0 or 0) + 1,
                da1=(dado.da1 or 0) + 1,
                da2=(dado.da2 or 0) + 1,
                da3=(dado.da3 or 0) + 1,
                da4=(dado.da4 or 0) + 1,
                da5=(dado.da5 or 0) + 1,
                da6=(dado.da6 or 0) + 1,
                da7=(dado.da7 or 0) + 1,
            )
            db.session.add(nova_linha)

        db.session.commit()
        return jsonify({'status': 'processamento manual concluído'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

