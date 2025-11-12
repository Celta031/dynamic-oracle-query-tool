import oracledb
from config import Config

# --- Bloco PL/SQL Genérico ---
plsql_set_role = """
declare 
    v_setrole varchar2(50);
    comando varchar2(200);
begin
    select cbd_use_role into v_setrole from CONTROLE_BD;
    comando := 'SET ROLE ' || v_setrole || ' IDENTIFIED BY "Zp*/3i2~"';
    EXECUTE IMMEDIATE comando;
end;
"""

def get_db_connection():
    """Cria, configura a ROLE e retorna uma conexão."""
    try:
        connection = oracledb.connect(
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            dsn=Config.DB_DSN
        )
        
        # Verifica se a senha da ROLE foi carregada
        if not Config.DB_ROLE_PASSWORD:
            raise ValueError("DB_ROLE_PASSWORD não está definida no .env")

        # 2. Constrói o bloco PL/SQL dinamicamente usando a senha do Config
        # A senha NUNCA fica visível no código-fonte
        # (Note o uso de f-string e as aspas duplas dentro da string de comando)
        plsql_set_role = f"""
        declare 
            v_setrole varchar2(50);
            comando varchar2(200);
        begin
            select cbd_use_role into v_setrole from CONTROLE_BD;
            comando := 'SET ROLE ' || v_setrole || ' IDENTIFIED BY "{Config.DB_ROLE_PASSWORD}"';
            EXECUTE IMMEDIATE comando;
        end;
        """

        # 3. Executa o bloco PL/SQL para definir a ROLE
        cursor = connection.cursor()
        cursor.execute(plsql_set_role)
        cursor.close()
        
        return connection
        
    except oracledb.Error as e:
        print(f"Erro ao conectar ou definir ROLE: {e}")
        raise

def execute_dynamic_query(sql, bind_params):
    """Executa uma query de SELECT dinâmica."""
    
    # Filtra parâmetros vazios (para campos opcionais)
    final_bind_params = {k: v for k, v in bind_params.items() if v}
    
    # Ajusta a query para campos opcionais (ex: :ccit_ext)
    # Se um parâmetro opcional não foi passado, a condição se torna "1=1"
    for param in bind_params:
        if param not in final_bind_params:
             # Ex: "AND e.equ_num_serie = :ccit_ext" vira "AND 1=1"
             sql = sql.replace(f"= :{param}", "= 1=1") 

    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute(sql, final_bind_params)
        
        col_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        results = [dict(zip(col_names, row)) for row in rows]
        
        # O frontend precisa dos nomes das colunas
        return {"headers": col_names, "rows": results}
        
    except oracledb.Error as e:
        print(f"Erro ao executar query dinâmica: {e}")
        raise
    finally:
        if connection:
            connection.close()

def execute_dynamic_update(target_table, target_rowids, updates_to_make, update_rules):
    """
    Executa o UPDATE validando contra as regras do JSON.
    Esta é a função mais crítica.
    """
    
    # 1. Validar e construir a query de UPDATE
    set_clauses = []
    update_bind_params = {}
    
    for i, (col_name, value) in enumerate(updates_to_make.items()):
        # Verifica se a coluna está nas regras daquela query
        if col_name in update_rules:
            bind_name = f"update_val_{i}"
            # Pega a regra de formatação (ex: "TO_TIMESTAMP(...)")
            sql_snippet = update_rules[col_name].replace(":val_name", f":{bind_name}")
            
            set_clauses.append(sql_snippet)
            update_bind_params[bind_name] = value
        else:
            # Ignora colunas que não estão nas regras
            print(f"AVISO: Tentativa de update da coluna '{col_name}' foi ignorada (não está nas 'update_rules' do JSON).")

    if not set_clauses:
        raise ValueError("Nenhuma alteração válida ou permitida foi fornecida.")
    if not target_rowids:
        raise ValueError("Nenhum ROWID foi selecionado para alteração.")

    # 2. Montar a query final
    set_sql_string = ", ".join(set_clauses)
    query_update_final = f"UPDATE {target_table} SET {set_sql_string} WHERE rowid = :p_rowid"

    # 3. Executar a Transação
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        updated_count = 0
        
        for row_id in target_rowids:
            loop_bind_params = update_bind_params.copy() 
            loop_bind_params["p_rowid"] = row_id
            
            cursor.execute(query_update_final, loop_bind_params)
            updated_count += 1
        
        connection.commit()
        return updated_count
        
    except oracledb.Error as e:
        print(f"Erro durante o UPDATE dinâmico: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()