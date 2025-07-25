from flask import Blueprint, request, jsonify
from src.models.uwb_data import UWBData
from src.models.relatorio import Relatorio
from src.models.user import db
from datetime import datetime
import traceback  # Para logs mais completos de erro

adicional_uwb_bp = Blueprint("adicional_uwb_bp", __name__)

@adicional_uwb_bp.route("/uwb/data-batch", methods=["POST"])
def receber_dados_uwb_batch():
    print("📥 Requisição recebida em /uwb/data-batch")
    
    try:
        dados_recebidos = request.get_json(force=True)
        print(f"📦 JSON recebido: {dados_recebidos}")
    except Exception as e:
        print("❌ Erro ao ler JSON:", str(e))
        traceback.print_exc()
        return jsonify({"erro": "JSON inválido"}), 400

    if not isinstance(dados_recebidos, list):
        print("⚠️ JSON não é uma lista.")
        return jsonify({"erro": "Formato incorreto. Esperado um array de objetos JSON."}), 400

    # Buscar relatório ativo
    relatorio_ativo = Relatorio.query.filter_by(fim_do_relatorio=None).order_by(Relatorio.inicio.desc()).first()
    if not relatorio_ativo:
        print("❌ Nenhum relatório ativo encontrado.")
        return jsonify({"erro": "Nenhum relatório ativo encontrado."}), 404
    else:
        print(f"📝 Relatório ativo encontrado: id={relatorio_ativo.id}, inicio={relatorio_ativo.inicio}")

    registros_salvos = []

    for item in dados_recebidos:
        print(f"🔄 Processando item: {item}")
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
            print("✅ Registro adicionado com sucesso.")
        except Exception as e:
            print("❌ Erro ao adicionar item:", item)
            print("Detalhe do erro:", str(e))
            traceback.print_exc()

    try:
        db.session.commit()
        print(f"💾 {len(registros_salvos)} registros salvos com sucesso no banco.")
    except Exception as e:
        print("❌ Erro ao commitar no banco de dados:", str(e))
        traceback.print_exc()
        return jsonify({"erro": "Erro ao salvar no banco de dados."}), 500

    return jsonify({"status": "ok", "total_registros": len(registros_salvos)})
