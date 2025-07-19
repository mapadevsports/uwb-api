from flask import Blueprint, request, jsonify
from src.models.relatorio import Relatorio
from src.models.user import db
from datetime import datetime
import logging

relatorio_kodular_bp = Blueprint("relatorio_kodular_bp", __name__)

@relatorio_kodular_bp.route("/iniciar_kodular", methods=["POST"])
def iniciar_kodular():
    """
    Rota alternativa que permite iniciar um relatório via dados simples (ex: Kodular),
    sem formato JSON — apenas texto bruto no corpo do POST, como: kx=123&ky=456
    """

    try:
        # 🔹 Receber os dados brutos (formato texto simples)
        raw_data = request.get_data(as_text=True)

        # 🔹 Tentar extrair kx e ky manualmente
        kx, ky = None, None
        for pair in raw_data.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                if key.strip().lower() == "kx":
                    kx = value.strip()
                elif key.strip().lower() == "ky":
                    ky = value.strip()

        # 🔹 Verifica se já existe relatório ativo
        relatorio_ativo = Relatorio.query.filter(
            Relatorio.inicio_do_relatorio.isnot(None),
            Relatorio.fim_do_relatorio.is_(None)
        ).first()

        if relatorio_ativo:
            return jsonify({
                "success": False,
                "message": "Já existe um relatório ativo",
                "relatorio_ativo": relatorio_ativo.to_dict()
            }), 400

        # 🔹 Criar novo relatório com Kx e Ky
        novo_relatorio = Relatorio(
            inicio_do_relatorio=datetime.utcnow(),
            kx=kx,
            ky=ky
        )

        db.session.add(novo_relatorio)
        db.session.commit()

        logging.info(f"[Kodular] Novo relatório iniciado: ID {novo_relatorio.relatorio_number}, Kx={kx}, Ky={ky}")

        return jsonify({
            "success": True,
            "message": "Relatório iniciado via Kodular",
            "relatorio": novo_relatorio.to_dict(),
            "leituras_habilitadas": True
        }), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"[Kodular] Erro ao iniciar relatório: {e}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500
