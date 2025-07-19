from flask import Blueprint, request, jsonify
from src.models.relatorio import Relatorio
from src.models.user import db
import json

relatorio_kodular_bp = Blueprint("relatorio_kodular", __name__)

@relatorio_bp.route("/iniciar_kodular", methods=["POST"])
def iniciar_kodular():
    try:
        # Lê mesmo que o content-type esteja incorreto
        raw_data = request.get_data(as_text=True)
        data = json.loads(raw_data)

        kx = data.get("kx")
        ky = data.get("ky")

        relatorio_ativo = Relatorio.query.filter(
            Relatorio.inicio_do_relatorio.isnot(None),
            Relatorio.fim_do_relatorio.is_(None)
        ).first()

        if relatorio_ativo:
            return jsonify({"erro": "Já existe um relatório ativo"}), 400

        novo_relatorio = Relatorio(kx=kx, ky=ky)
        db.session.add(novo_relatorio)
        db.session.commit()

        return jsonify({
            "mensagem": "Relatório iniciado via Kodular",
            "relatorio_id": novo_relatorio.relatorio_number,
            "kx": novo_relatorio.kx,
            "ky": novo_relatorio.ky
        }), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao iniciar relatório: {str(e)}"}), 400
