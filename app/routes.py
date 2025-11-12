from flask import current_app, render_template, request, jsonify
from . import db
from .core import query_manager

app = current_app

@app.route("/")
def index():
    """Renderiza a página HTML principal (o gerenciador)."""
    # Carrega a lista inicial de queries para o dropdown
    queries_list = query_manager.get_queries_list()
    return render_template("manager.html", queries_list=queries_list)

# --- API ENDPOINTS ---

@app.route("/api/query/<query_id>", methods=['GET'])
def api_get_query(query_id):
    """Retorna os detalhes de uma query específica (parâmetros, sql, etc)."""
    try:
        query_obj = query_manager.get_query_by_id(query_id)
        if query_obj:
            return jsonify(query_obj), 200
        else:
            return jsonify({"error": "Query não encontrada."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/query/<query_id>", methods=['POST'])
def api_save_query(query_id):
    """
    SALVA a string SQL editada de volta no queries.json.
    ALERTA: Esta rota permite a alteração do arquivo de queries.
    """
    try:
        data = request.json
        new_sql = data.get('sql')
        
        if not new_sql:
            return jsonify({"error": "SQL não pode ser vazio."}), 400

        if query_manager.save_query_sql(query_id, new_sql):
            return jsonify({"success": True, "message": "Query salva com sucesso!"}), 200
        else:
            return jsonify({"error": "Falha ao salvar a query no servidor."}), 500
            
    except Exception as e:
        print(f"Erro ao salvar query: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/buscar", methods=['POST'])
def api_buscar():
    """Executa a busca dinâmica."""
    try:
        data = request.json
        query_id = data.get('query_id')
        params = data.get('params') # Dicionário de bind_name: value

        if not query_id or not params:
            return jsonify({"error": "Query ID e Parâmetros são obrigatórios."}), 400

        query_obj = query_manager.get_query_by_id(query_id)
        if not query_obj:
            return jsonify({"error": "Query não encontrada."}), 404

        results = db.execute_dynamic_query(query_obj['sql'], params)
        
        if not results.get("rows"):
             return jsonify({"message": "Nenhum registro encontrado."}), 404

        # Anexa as regras de update na resposta, pois o form de update precisa saber
        results["update_rules"] = query_obj.get("update_rules", {})
        return jsonify(results), 200

    except Exception as e:
        print(e)
        return jsonify({"error": f"Erro interno no servidor: {e}"}), 500

@app.route("/api/atualizar", methods=['POST'])
def api_atualizar():
    """Executa o update dinâmico."""
    try:
        data = request.json
        query_id = data.get('query_id')
        target_rowids = data.get('rowids')
        updates = data.get('updates')

        if not query_id or not target_rowids or not updates:
            return jsonify({"error": "Dados insuficientes para atualização."}), 400

        # Pega as regras e a tabela-alvo do JSON
        query_obj = query_manager.get_query_by_id(query_id)
        if not query_obj:
            return jsonify({"error": "Query não encontrada."}), 404
            
        target_table = query_obj.get("target_table")
        update_rules = query_obj.get("update_rules", {})
        
        if not target_table:
             return jsonify({"error": "'target_table' não definida no JSON para esta query."}), 500

        updated_count = db.execute_dynamic_update(target_table, target_rowids, updates, update_rules)
        
        return jsonify({
            "success": True, 
            "message": f"Sucesso! {updated_count} linhas foram atualizadas e comitadas."
        }), 200

    except Exception as e:
        print(e)
        return jsonify({"error": f"Erro ao atualizar: {e}"}), 500