import json
import os
from threading import Lock

# Trava para evitar que duas requisições escrevam no JSON ao mesmo tempo
json_lock = Lock()

QUERY_FILE = "queries.json"

def get_queries_list():
    """Retorna apenas a lista de IDs e Nomes para o dropdown."""
    try:
        with open(QUERY_FILE, 'r', encoding='utf-8') as f:
            queries = json.load(f)
        
        # Retorna uma lista simplificada
        return [{"id": q.get("id"), "name": q.get("name")} for q in queries]
    
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Erro ao ler {QUERY_FILE}: {e}")
        return []

def get_query_by_id(query_id):
    """Retorna o objeto completo da query selecionada."""
    try:
        with open(QUERY_FILE, 'r', encoding='utf-8') as f:
            queries = json.load(f)
        
        for query in queries:
            if query.get("id") == query_id:
                return query
        
        return None # Query não encontrada
    except Exception as e:
        print(f"Erro ao buscar query {query_id}: {e}")
        return None

def save_query_sql(query_id, new_sql):
    """Salva a nova string SQL no arquivo JSON."""
    with json_lock:
        try:
            # 1. Ler o arquivo
            with open(QUERY_FILE, 'r', encoding='utf-8') as f:
                queries = json.load(f)
            
            # 2. Encontrar e modificar a query
            query_found = False
            for query in queries:
                if query.get("id") == query_id:
                    query["sql"] = new_sql
                    query_found = True
                    break
            
            if not query_found:
                raise ValueError(f"Query ID '{query_id}' não encontrada para salvar.")

            # 3. Escrever o arquivo de volta
            with open(QUERY_FILE, 'w', encoding='utf-8') as f:
                json.dump(queries, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"ERRO CRÍTICO ao salvar {QUERY_FILE}: {e}")
            return False