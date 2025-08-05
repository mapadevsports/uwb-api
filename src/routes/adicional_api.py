from flask import Blueprint, request, jsonify
from src.models.relatorio import Relatorio
from src.models.user import db
from datetime import datetime
import logging

relatorio_kodular_bp = Blueprint("relatorio_kodular_bp", __name__)

@relatorio_kodular_bp.route("/iniciar_kodular", methods=["POST"])
def iniciar_ou_finalizar_kodular():
    """
    🔹 Se o corpo for JSON com kx e ky → inicia um novo relatório.
    🔹 Se o corpo for texto "finalizar_relatorio" → finaliza o relatório ativo.
    """
    try:
        # Verifica se é texto puro (caso de finalização)
        if not request.is_json:
            raw_data = request.get_data(as_text=True).strip()
            logging.info(f"[Kodular] Texto recebido: {raw_data}")

            if raw_data.lower() == "finalizar_relatorio":
                # Tentar finalizar o relatório ativo
                relatorio_ativo = Relatorio.query.filter(
                    Relatorio.inicio_do_relatorio.isnot(None),
                    Relatorio.fim_do_relatorio.is_(None)
                ).first()

                if not relatorio_ativo:
                    return jsonify({
                        "success": False,
                        "message": "Nenhum relatório ativo encontrado"
                    }), 400

                relatorio_ativo.fim_do_relatorio = datetime.utcnow()
                db.session.commit()

                logging.info(f"[Kodular] Relatório finalizado: ID {relatorio_ativo.relatorio_number}")

                return jsonify({
                    "success": True,
                    "message": "Relatório finalizado com sucesso",
                    "relatorio": relatorio_ativo.to_dict(),
                    "leituras_habilitadas": False
                }), 200

            # Se não for "finalizar_relatorio", retorna erro
            return jsonify({"error": "Comando inválido no modo texto"}), 400

        # Se for JSON, deve conter kx e ky
        data = request.get_json()
        kx = data.get("kx")
        ky = data.get("ky")
        nome_relatorio = data.get("nome") # Novo campo extraído


        if not kx or not ky:
            return jsonify({
                "success": False,
                "message": "Parâmetros kx e ky são obrigatórios"
            }), 400

        # Verifica se já há um relatório ativo
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

        # Cria novo relatório
        novo_relatorio = Relatorio(
            inicio_do_relatorio=datetime.utcnow(),
            kx=str(kx),
            ky=str(ky),
            nome=str(nome_relatorio)
        )

        db.session.add(novo_relatorio)
        db.session.commit()

        logging.info(f"[Kodular] Novo relatório: ID {novo_relatorio.relatorio_number}, Kx={kx}, Ky={ky}")

        return jsonify({
            "success": True,
            "message": "Relatório iniciado via Kodular",
            "relatorio": novo_relatorio.to_dict(),
            "leituras_habilitadas": True
        }), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"[Kodular] Erro: {e}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500



