# Gerenciador de Atualizações Dinâmicas com Oracle DB

Este é um projeto web robusto construído em Python (Flask) para servir como uma interface gráfica (GUI) para executar consultas e atualizações em um banco de dados Oracle. A ferramenta é 100% modular, permitindo que novas operações de banco de dados sejam adicionadas e editadas diretamente de um arquivo `queries.json`, sem a necessidade de alterar o código-fonte.

## 🚀 Funcionalidades

* **Interface Modular:** As queries não estão fixadas no código. Elas são carregadas dinamicamente a partir do `queries.json`.
* **Editor de Query:** Permite visualizar e editar a query SQL salva diretamente pela interface web (com um alerta de segurança).
* **Filtros Dinâmicos:** A interface gera os campos de filtro (parâmetros) automaticamente, com base no que está definido no JSON.
* **Resultados em Tabela:** Exibe os resultados da busca em uma tabela interativa com coluna de seleção "congelada" (sticky).
* **Formulário de Update Dinâmico:** Gera os campos de atualização com base nas colunas retornadas pela query.
* **Segurança:** As credenciais são gerenciadas por variáveis de ambiente (`.env`) e não são expostas no código.

## 🛠️ Stack Tecnológica

* **Backend:** Python 3, Flask, `oracledb`
* **Frontend:** HTML5, CSS3, JavaScript (Vanilla JS/Fetch API)
* **Configuração:** JSON

---

## ⚙️ Instalação e Execução

Siga estes passos para executar o projeto localmente.

### 1. Pré-requisitos

* Python 3.7+
* Acesso a um banco de dados Oracle (local ou remoto).
* [Oracle Instant Client](https://www.oracle.com/database/technologies/instant-client/downloads.html) (necessário para a biblioteca `oracledb` se conectar ao banco).

### 2. Clone o Repositório

```bash
git clone [https://github.com/SEU-USUARIO/NOME-DO-SEU-REPO.git](https://github.com/SEU-USUARIO/NOME-DO-SEU-REPO.git)
cd NOME-DO-SEU-REPO
```

### 3. Crie um Ambiente Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Instale as Dependências

```bash
pip install -r requirements.txt
```

### 5. Configure o Ambiente

Crie seu próprio arquivo de credenciais a partir do exemplo.

```bash
# Copie o arquivo de exemplo
cp .env.example .env
```

Agora, **edite o arquivo `.env`** com suas credenciais reais do Oracle.

```ini
# / .env
DB_USER="OPECIT"
DB_PASSWORD="sua-senha-real"
DB_HOST="172.32.1.254"
DB_PORT="1521"
DB_SERVICE="bhz.sub02102124181.bhzvcn.oraclevcn.com"
DB_ROLE_PASSWORD="Zp*/3i2~"
```

### 6. Configure as Queries

Edite o arquivo `queries.json` para refletir as tabelas, colunas e regras de negócio do *seu* banco de dados.

* `"id"`: Um identificador único.
* `"name"`: O nome que aparecerá no dropdown.
* `"sql"`: A query SQL (deve incluir `a.rowid` como primeira coluna para o update funcionar).
* `"target_table"`: A tabela que sofrerá o `UPDATE`.
* `"parameters"`: Os campos que se tornarão filtros (bind variables da query).
* `"update_rules"`: Mapeamento de colunas que podem ser atualizadas e suas regras de conversão (ex: `TO_TIMESTAMP`).

### 7. Execute a Aplicação

```bash
python run.py
```

Abra seu navegador e acesse `http://127.0.0.1:5000`.