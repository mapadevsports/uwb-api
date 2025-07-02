from flask import Blueprint, jsonify, request
from src.models.uwb_data import UWBData, db
from src.models.ancora_uwb import AncoraUWB
from datetime import datetime
import math

uwb_bp = Blueprint("uwb", __name__)

# --- Lógica de Trilateração ---
def calculate_tag_position(anchor_data, tag_ranges):
    """
    Calcula a posição da tag usando trilateração e mínimos quadrados.
    :param anchor_data: Dicionário de âncoras com 'ancora_id', 'x', 'y'.
                        Ex: {'ANC0': {'x': 0, 'y': 0}, 'ANC1': {'x': 140, 'y': 0}, ...}
    :param tag_ranges: Lista de distâncias da tag para as âncoras, indexada pelo ID da âncora.
                       Ex: [dist_anc0, dist_anc1, dist_anc2, dist_anc3, ...]
    :return: Tupla (x, y) da posição da tag, ou (None, None) se não houver dados suficientes.
    """
    
    valid_anchors_with_ranges = []
    for i, dist in enumerate(tag_ranges):
        anc_id_str = f"ANC{i}"
        if anc_id_str in anchor_data and dist > 0:
            valid_anchors_with_ranges.append({
                'id': anc_id_str,
                'x': anchor_data[anc_id_str]['x'],
                'y': anchor_data[anc_id_str]['y'],
                'r': dist
            })

    if len(valid_anchors_with_ranges) < 3:
        print("Não há âncoras suficientes com dados válidos para trilateração.") # Usando print para logs simples no Flask
        return None, None

    def three_point_intersection(x1, y1, r1, x2, y2, r2):
        d = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

        if d == 0:
            return None, None

        if d > r1 + r2 or d < abs(r1 - r2):
            temp_x = x1 + (x2 - x1) * r1 / (r1 + r2) if (r1 + r2) != 0 else x1
            temp_y = y1 + (y2 - y1) * r1 / (r1 + r2) if (r1 + r2) != 0 else y1
            return temp_x, temp_y
        
        dr = d / 2 + (r1 * r1 - r2 * r2) / (2 * d)
        temp_x = x1 + (x2 - x1) * dr / d
        temp_y = y1 + (y2 - y1) * dr / d
        
        return temp_x, temp_y

    sum_x = 0.0
    sum_y = 0.0
    count_intersections = 0

    num_anchors = len(valid_anchors_with_ranges)
    for i in range(num_anchors):
        for j in range(i + 1, num_anchors):
            anc1 = valid_anchors_with_ranges[i]
            anc2 = valid_anchors_with_ranges[j]

            x, y = three_point_intersection(anc1['x'], anc1['y'], anc1['r'],
                                             anc2['x'], anc2['y'], anc2['r'])
            if x is not None and y is not None:
                sum_x += x
                sum_y += y
                count_intersections += 1

    if count_intersections > 0:
        final_x = sum_x / count_intersections
        final_y = sum_y / count_intersections
        return final_x, final_y
    else:
        return None, None

@uwb_bp.route('/uwb/data', methods=['POST'])
def receive_uwb_data():
    """
    Endpoint para receber dados UWB do ESP32
    Espera um JSON no formato:
    {
        "id": "4",
        "range": [6, 59, 126, 0, 0, 0, 0, 0],
        "coordenadasanc": [[0,0], [140,0], [140,140], [0,140]]
    }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'Nenhum dado JSON fornecido'}), 400
        
        if 'id' not in data or 'range' not in data or 'coordenadasanc' not in data:
            return jsonify({'error': 'Campos obrigatórios: id, range, coordenadasanc'}), 400
        
        tag_id = str(data['id'])
        range_values = data['range']
        anc_coords_list = data['coordenadasanc']
        
        if not isinstance(range_values, list) or len(range_values) < 3:
            return jsonify({'error': 'Range deve ser uma lista com pelo menos 3 valores'}), 400
        
        if not isinstance(anc_coords_list, list) or len(anc_coords_list) < 3:
            return jsonify({'error': 'coordenadasanc deve ser uma lista com pelo menos 3 conjuntos de coordenadas'}), 400

        # 1. Atualizar/Inserir coordenadas das âncoras no banco de dados
        current_anchors_data = {} # Para passar para a função de cálculo
        for i, coords in enumerate(anc_coords_list):
            if not isinstance(coords, list) or len(coords) != 2:
                print(f"Coordenadas de âncora inválidas no índice {i}: {coords}")
                continue

            anc_id_str = f"ANC{i}"
            x_anc, y_anc = float(coords[0]), float(coords[1])

            ancora = AncoraUWB.query.filter_by(ancora_id=anc_id_str).first()
            if ancora:
                ancora.x = x_anc
                ancora.y = y_anc
            else:
                ancora = AncoraUWB(ancora_id=anc_id_str, x=x_anc, y=y_anc)
                db.session.add(ancora)
            
            current_anchors_data[anc_id_str] = {'x': x_anc, 'y': y_anc}
        
        db.session.commit()

        # 2. Calcular a posição da tag
        calculated_x, calculated_y = calculate_tag_position(current_anchors_data, range_values)

        # 3. Salvar a posição da tag no banco de dados
        uwb_data = UWBData(
            tag_number=tag_id,
            X=calculated_x,
            Y=calculated_y,
            criado_em=datetime.utcnow()
        )
        
        db.session.add(uwb_data)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Dados UWB processados e salvos com sucesso',
            'data': {
                'tag_number': tag_id,
                'X': calculated_x,
                'Y': calculated_y
            }
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Erro de conversão de dados: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        import traceback # Importa traceback aqui para garantir que esteja disponível
        full_traceback = traceback.format_exc()
        print(f"Erro interno do servidor no receive_uwb_data: {e}\n{full_traceback}") # Imprime no log do Render
        return jsonify({
            'error': 'Erro interno do servidor',
            'details': str(e),
            'traceback': full_traceback # Adiciona o traceback completo na resposta JSON
        }), 500
@uwb_bp.route('/uwb/data', methods=['GET'])
def get_uwb_data():
    """
    Endpoint para recuperar dados UWB (para testes)
    """
    try:
        uwb_records = UWBData.query.order_by(UWBData.criado_em.desc()).limit(50).all()
        # Adicionar as coordenadas das âncoras para a resposta GET
        anchors = AncoraUWB.query.all()
        anchors_data = {anc.ancora_id: {'x': anc.x, 'y': anc.y} for anc in anchors}

        return jsonify({
            'uwb_records': [record.to_dict() for record in uwb_records],
            'anchors': anchors_data
        })
    except Exception as e:
        return jsonify({'error': f'Erro ao recuperar dados: {str(e)}'}), 500

@uwb_bp.route('/uwb/data/<tag_number>', methods=['GET'])
def get_uwb_data_by_tag(tag_number):
    """
    Endpoint para recuperar dados UWB de uma tag específica
    """
    try:
        uwb_records = UWBData.query.filter_by(tag_number=tag_number).order_by(UWBData.criado_em.desc()).limit(50).all()
        # Adicionar as coordenadas das âncoras para a resposta GET
        anchors = AncoraUWB.query.all()
        anchors_data = {anc.ancora_id: {'x': anc.x, 'y': anc.y} for anc in anchors}

        return jsonify({
            'uwb_records': [record.to_dict() for record in uwb_records],
            'anchors': anchors_data
        })
    except Exception as e:
        return jsonify({'error': f'Erro ao recuperar dados: {str(e)}'}), 500

@uwb_bp.route('/uwb/health', methods=['GET'])
def health_check():
    """
    Endpoint simples para verificar se a API está funcionando
    """
    return jsonify({
        'status': 'OK',
        'message': 'API UWB está funcionando',
        'timestamp': datetime.utcnow().isoformat()
    })

