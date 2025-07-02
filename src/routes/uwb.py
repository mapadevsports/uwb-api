from flask import Blueprint, jsonify, request
from src.models.uwb_data import UWBData
from src.models.ancora_uwb import AncoraUWB
from src.models.user import db
from scipy.optimize import least_squares
import numpy as np
import traceback

uwb_bp = Blueprint("uwb", __name__)

# Função para calcular a posição da tag usando trilateração e mínimos quadrados
def calculate_tag_position(ranges, anchor_coords):
    if len(ranges) < 3 or len(anchor_coords) < 3:
        raise ValueError("São necessárias pelo menos 3 âncoras e 3 distâncias para trilateração.")

    # Função de erro para least_squares
    def error_function(position, anchor_coords, ranges):
        errors = []
        for i in range(len(anchor_coords)):
            dist_expected = np.sqrt((position[0] - anchor_coords[i][0])**2 + (position[1] - anchor_coords[i][1])**2)
            errors.append(dist_expected - ranges[i])
        return np.array(errors)

    # Estimativa inicial da posição (pode ser a média das âncoras ou (0,0))
    initial_position = np.mean(anchor_coords, axis=0) if anchor_coords else np.array([0.0, 0.0])

    # Executa a otimização de mínimos quadrados
    result = least_squares(error_function, initial_position, args=(anchor_coords, ranges))

    if result.success:
        return result.x[0], result.x[1] # Retorna X e Y calculados
    else:
        # Se a otimização não convergir, pode retornar None ou levantar um erro
        print(f"Otimização de mínimos quadrados não convergiu: {result.message}")
        return None, None

@uwb_bp.route("/uwb/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "UWB API is running!"}), 200

@uwb_bp.route("/uwb/data", methods=["POST"])
def receive_uwb_data():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Dados JSON não fornecidos."}), 400

        # Extração de dados
        tag_id = data.get("id")
        ranges = data.get("range")
        coordenadas_ancoras_raw = data.get("coordenadasanc")

        # Validação básica dos dados
        if not tag_id:
            return jsonify({"error": "ID da tag não fornecido."}), 400
        if not isinstance(ranges, list) or len(ranges) < 3:
            return jsonify({"error": "Distâncias (range) inválidas ou insuficientes."}), 400
        if not isinstance(coordenadas_ancoras_raw, list) or len(coordenadas_ancoras_raw) < 3:
            return jsonify({"error": "Coordenadas das âncoras inválidas ou insuficientes."}), 400

        # Converte coordenadas das âncoras para numpy array
        anchor_coords = np.array(coordenadas_ancoras_raw)

        # Calcula a posição da tag
        calculated_x, calculated_y = calculate_tag_position(ranges, anchor_coords)

        if calculated_x is None or calculated_y is None:
            return jsonify({"error": "Não foi possível calcular a posição da tag."}), 500

        # Atualiza/Insere coordenadas das âncoras no banco de dados
        for i, coord in enumerate(coordenadas_ancoras_raw):
            ancora_id_str = f"ANC{i}"
            ancora = AncoraUWB.query.filter_by(ancora_id=ancora_id_str).first()
            if ancora:
                ancora.x = coord[0]
                ancora.y = coord[1]
                ancora.ultima_atualizacao = datetime.utcnow()
            else:
                new_ancora = AncoraUWB(
                    ancora_id=ancora_id_str,
                    x=coord[0],
                    y=coord[1],
                    ultima_atualizacao=datetime.utcnow()
                )
                db.session.add(new_ancora)
        db.session.commit()

        # Salva os dados da tag no banco de dados
        new_uwb_data = UWBData(
            tag_number=tag_id,
            X=calculated_x,
            Y=calculated_y
        )
        db.session.add(new_uwb_data)
        db.session.commit()

        return jsonify({
            "message": "Dados recebidos e processados com sucesso!",
            "tag_id": tag_id,
            "X": calculated_x,
            "Y": calculated_y
        }), 201

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": f"Erro de conversão de dados: {str(e)}"}), 400

    except Exception as e:
        db.session.rollback()
        import traceback
        full_traceback = traceback.format_exc()
        print(f"Erro interno do servidor no receive_uwb_data: {e}\n{full_traceback}") # Imprime no log do Render
        
        # RETORNA O TRACEBACK COMO TEXTO SIMPLES
        return full_traceback, 500, {"Content-Type": "text/plain"}

@uwb_bp.route("/uwb/data", methods=["GET"])
def get_uwb_data():
    """Endpoint para recuperar dados UWB (para testes)"""
    try:
        all_uwb_data = UWBData.query.order_by(UWBData.criado_em.desc()).limit(100).all()
        return jsonify([data.to_dict() for data in all_uwb_data]), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar dados: {str(e)}"}), 500


@uwb_bp.route("/uwb/anchors", methods=["GET"])
def get_anchors():
    """Endpoint para recuperar coordenadas das âncoras (para testes)"""
    try:
        all_anchors = AncoraUWB.query.order_by(AncoraUWB.ancora_id).all()
        return jsonify([{"ancora_id": a.ancora_id, "x": a.x, "y": a.y} for a in all_anchors]), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar âncoras: {str(e)}"}), 500


