from flask import Blueprint, request, jsonify
from src.models.uwb_data import UWBData
from src.models.relatorio import Relatorio
from src.models.user import db
from datetime import datetime

adicional_uwb_bp = Blueprint("adicional_uwb_bp", __name__)

@adicional_uwb_bp.route("/uwb/data-batch", methods=["POST"])
def receber_dados_uwb_batch():
    dados_recebidos = request.get_json(force=True)
    if not isinstance(dados_recebidos, list):
        return jsonify({"erro": "Formato incorreto. Esperado um array de objetos JSON."}), 400

    relatorio_ativo = Relatorio.query.filter_by(fim=None).order_by(Relatorio.inicio.desc()).first()
    if not relatorio_ativo:
        return jsonify({"erro": "Nenhum relatório ativo encontrado."}), 404

    registros_salvos = []
    for item in dados_recebidos:
        try:
            novo_dado = UWBData(
                id_tag=item.get("id"),
                distancia_1=item.get("range", [None])[0],
                distancia_2=item.get("range", [None])[1],
                distancia_3=item.get("range", [None])[2],
                horario=datetime.utcnow(),
                relatorio_id=relatorio_ativo.id,
            )
            db.session.add(novo_dado)
            registros_salvos.append(item)
        except Exception as e:
            print(f"Erro ao processar item: {item} - Erro: {e}")

    db.session.commit()
    return jsonify({"status": "ok", "total_registros": len(registros_salvos)})