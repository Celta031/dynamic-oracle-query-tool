import oracledb
import sys
import argparse

# ---  CONFIGURE SEUS DADOS DE CONEXÃO AQUI ---
DB_USER = "OPECIT"
DB_PASSWORD = "OPECIT"
DB_HOST = "172.32.1.254"
DB_PORT = "1521"
DB_SERVICE = "bhz.sub02102124181.bhzvcn.oraclevcn.com"
DB_DSN = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"

# --- LISTA DE PERMISSÃO PARA UPDATES (SEGURANÇA) ---
ALLOWED_UPDATE_COLUMNS = {
    "VIA_QTD_INTEIRAS": "VIA_QTD_INTEIRAS = :val_name",
    "VIA_VALOR_INTEIRAS": "VIA_VALOR_INTEIRAS = :val_name",
    "VIA_CATRACA_INICIAL": "VIA_CATRACA_INICIAL = :val_name",
    "VIA_CATRACA_FINAL": "VIA_CATRACA_FINAL = :val_name",
    "VIA_DATAHORA_FINAL_OPERACAO": "VIA_DATAHORA_FINAL_OPERACAO = TO_TIMESTAMP(:val_name, 'DD/MM/YYYY HH24:MI:SS')"
    # Adicione outras colunas da tabela 'ro_viagens' aqui se necessário
}

# --- Bloco PL/SQL e Query de SELECT ---
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
# A query de SELECT precisa ter 'a.rowid' como a PRIMEIRA coluna
query_select = """
SELECT a.rowid, a.OPE_COD_OPERADORA, e.EQU_NUM_SERIE, v.VEI_COD_VEICULO_EXTERNO, 
       a.VIA_DATAHORA_INICIO_OPERACAO, a.VIA_DATAHORA_FINAL_OPERACAO, 
         a.VIA_CATRACA_INICIAL, a.VIA_CATRACA_FINAL,
       a.VIA_QTD_INTEIRAS, a.VIA_VALOR_INTEIRAS
FROM ro_viagens a, equipamentos e, veiculos v, linhas l
WHERE
    e.equ_cod_equipamento = a.equ_cod_equipamento AND
    v.vei_cod_veiculo = a.vei_cod_veiculo AND
    l.LIN_COD_LINHA = a.LIN_COD_LINHA AND
    a.rop_data_coleta = TO_DATE(:data_coleta, 'DD/MM/YYYY') AND
    v.vei_cod_veiculo_externo = :veic_externo
"""

def main():
    parser = argparse.ArgumentParser(description="Busca e atualiza registros na tabela ro_viagens de forma interativa.")
    
    parser.add_argument("-d", "--data", required=True, 
                        help="Data da coleta (filtro OBRIGATÓRIO, formato 'DD/MM/YYYY')")
    parser.add_argument("-v", "--veiculo", required=True, 
                        help="Código do veículo externo (filtro OBRIGATÓRIO)")
    parser.add_argument("-c", "--ccit", 
                        help="Código CCIT Externo (filtro opcional para e.equ_num_serie)")
    
    try:
        args = parser.parse_args()
    except SystemExit:
        sys.exit(1)

    print("--- Script de Atualização Interativa ---")
    print(f"Filtro Data: {args.data}")
    print(f"Filtro Veículo: {args.veiculo}")
    if args.ccit:
        print(f"Filtro CCIT: {args.ccit}")
    print("------------------------------------------")

    connection = None
    cursor = None
    try:
        print(f"Conectando ao banco de dados em {DB_DSN}...")
        connection = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
        cursor = connection.cursor()
        print("Conexão bem-sucedida!")

        print("Definindo a ROLE...")
        cursor.execute(plsql_set_role)
        print("ROLE definida com sucesso.")

        print("Buscando registros...")
        
        bind_params_select = {
            "data_coleta": args.data,
            "veic_externo": args.veiculo
        }

        query_select_final = query_select
        if args.ccit:
            query_select_final += " AND e.equ_num_serie = :ccit_ext"
            bind_params_select["ccit_ext"] = args.ccit
            
        query_select_final += " ORDER BY a.VIA_DATAHORA_INICIO_OPERACAO ASC"

        cursor.execute(query_select_final, bind_params_select)
        rows_to_update = cursor.fetchall()

        if not rows_to_update:
            print("Nenhum registro encontrado com os filtros fornecidos. Nenhuma alteração será feita.")
            sys.exit(0)

        # --- 4. EXIBIR RESULTADOS ---
        print(f"\n--- {len(rows_to_update)} REGISTROS ENCONTRADOS ---")
        col_names = [desc[0] for desc in cursor.description]
        headers = col_names[1:] # Não mostra ROWID
        
        print(f"{'INDEX':<5} | {' | '.join(headers)}")
        print("-" * (len(' | '.join(headers)) + 7))

        for i, row in enumerate(rows_to_update):
            row_data = [str(item) for item in row[1:]] 
            print(f"[{i+1:<3}] | {' | '.join(row_data)}")
        
        print("------------------------------------------")

        # --- 5. [NOVO] SELECIONAR LINHAS (INDEX) ---
        target_input = input("\nQuais linhas (INDEX) você deseja alterar? (Ex: 1, 3 / 'todas' / 'sair'): ")
        
        if target_input.lower() == 'sair':
            sys.exit("Operação cancelada.")
        
        target_rowids = []
        target_indexes_display = []

        if target_input.lower() == 'todas':
            # Pega o ROWID (coluna 0) de todas as linhas
            target_rowids = [row[0] for row in rows_to_update]
            target_indexes_display = [str(i+1) for i in range(len(rows_to_update))]
        else:
            try:
                # Converte a entrada (ex: "1, 3") em índices de lista (ex: 0, 2)
                target_indices = [int(idx.strip()) - 1 for idx in target_input.split(',')]
                
                # Validação
                for idx in target_indices:
                    if 0 <= idx < len(rows_to_update):
                        # Adiciona o ROWID (row[0]) da linha selecionada
                        target_rowids.append(rows_to_update[idx][0])
                        target_indexes_display.append(str(idx + 1))
                    else:
                        print(f"ERRO: Índice '{idx + 1}' está fora do range (1 a {len(rows_to_update)}).")
                        sys.exit(1)
                
                if not target_rowids:
                    print("Nenhum índice válido selecionado.")
                    sys.exit(1)

            except ValueError:
                print(f"ERRO: Entrada de índice inválida: '{target_input}'. Use números separados por vírgula.")
                sys.exit(1)

        print(f"Linhas selecionadas para alteração (INDEX): {', '.join(target_indexes_display)}")
        
        # --- 6. LOOP INTERATIVO PARA DEFINIR O UPDATE ---
        updates_to_make = {}
        
        while True:
            print("\nQuais alterações você quer fazer nas linhas selecionadas?")
            coluna = input("Nome da Coluna (ou 'sair' para cancelar): ")
            
            if coluna.lower() == 'sair':
                print("Operação cancelada.")
                sys.exit(0)
            
            coluna_norm = coluna.strip().upper()
            
            if coluna_norm not in ALLOWED_UPDATE_COLUMNS:
                print(f"ERRO: A coluna '{coluna}' não é permitida ou não existe na lista.")
                print(f"Permitidas: {list(ALLOWED_UPDATE_COLUMNS.keys())}")
                continue
                
            valor = input(f"Novo valor para {coluna_norm}: ")
            updates_to_make[coluna_norm] = valor.strip()
            
            continuar = input("Deseja alterar outra coluna? (s/n): ")
            if continuar.lower() != 's':
                break
        
        if not updates_to_make:
            print("Nenhuma alteração definida. Saindo.")
            sys.exit(0)

        # --- 7. CONFIRMAÇÃO FINAL ---
        print("\n--- RESUMO DA OPERAÇÃO ---")
        print(f"Alvo: {len(target_rowids)} linhas (INDEX: {', '.join(target_indexes_display)})")
        print("Alterações a serem aplicadas:")
        for col, val in updates_to_make.items():
            print(f"  - SET {col} = {val}")
        
        confirm = input("\nConfirmar e EXECUTAR estas alterações? (s/n): ")
        if confirm.lower() != 's':
            print("Operação cancelada pelo usuário.")
            sys.exit(0)

        # --- 8. EXECUTAR UPDATE ---
        print("Construindo query de UPDATE...")
        set_clauses = []
        update_bind_params = {}
        
        for i, (col_norm, valor) in enumerate(updates_to_make.items()):
            bind_name = f"update_val_{i}"
            sql_snippet = ALLOWED_UPDATE_COLUMNS[col_norm].replace(":val_name", f":{bind_name}")
            set_clauses.append(sql_snippet)
            update_bind_params[bind_name] = valor

        set_sql_string = ", ".join(set_clauses)
        query_update_final = f"UPDATE ro_viagens SET {set_sql_string} WHERE rowid = :p_rowid"
        
        print(f"Executando UPDATE em {len(target_rowids)} linhas...")
        updated_count = 0
        
        # Itera APENAS sobre os ROWIDs selecionados
        for row_id in target_rowids:
            loop_bind_params = update_bind_params.copy() 
            loop_bind_params["p_rowid"] = row_id # Alvo é o ROWID específico
            
            cursor.execute(query_update_final, loop_bind_params)
            updated_count += 1

        # --- Etapa D: Commit das alterações ---
        connection.commit()
        print(f"\nSucesso! {updated_count} linhas foram atualizadas e comitadas.")

    except oracledb.Error as e:
        print(f"\nERRO: {e}")
        if connection:
            print("Executando ROLLBACK... Nenhuma alteração foi salva.")
            connection.rollback()
    except KeyboardInterrupt:
        print("\nOperação interrompida pelo usuário (Ctrl+C). Executando ROLLBACK...")
        if connection:
            connection.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"\nErro inesperado no script: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            print("Conexão fechada.")

# --- Ponto de entrada do script ---
if __name__ == "__main__":
    main()