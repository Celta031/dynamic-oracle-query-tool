document.addEventListener("DOMContentLoaded", () => {

    // --- Seletores Globais ---
    const querySelect = document.getElementById("query-select");
    const filterSection = document.getElementById("filter-section");
    const filterFormInputs = document.getElementById("filter-form-inputs");
    const searchForm = document.getElementById("search-form");
    const resultsSection = document.getElementById("results-section");
    const updateSection = document.getElementById("update-section");
    const tableContainer = document.getElementById("results-table");
    const noResultsDiv = document.getElementById("no-results");
    const updateForm = document.getElementById("update-form");
    const updateFormInputs = document.getElementById("update-form-inputs");
    const feedbackMessage = document.getElementById("feedback-message");
    const btnBuscar = document.getElementById("btn-buscar");
    const btnAtualizar = document.getElementById("btn-atualizar");
    
    // --- Seletores do Modal ---
    const queryModal = document.getElementById("query-modal");
    const btnShowQueryModal = document.getElementById("btn-show-query-modal");
    const btnCloseModal = document.getElementById("btn-close-modal");
    const modalQueryName = document.getElementById("modal-query-name");
    const modalQuerySql = document.getElementById("modal-query-sql");
    const btnSaveQuery = document.getElementById("btn-save-query");

    // --- Estado da Aplicação ---
    let currentQueryId = null;
    let currentQueryData = {}; // Armazena o objeto da query (sql, params, rules)
    let currentResultHeaders = []; // Armazena cabeçalhos da busca
    let tableSelectAllCheckbox = null;

    // --- 1. Evento: Seleção de Query ---
    querySelect.addEventListener("change", () => {
        currentQueryId = querySelect.value;
        if (!currentQueryId) {
            filterSection.style.display = "none";
            btnShowQueryModal.disabled = true;
            return;
        }
        
        // Reseta a interface
        hideResults();
        clearFeedback();
        
        // Busca os detalhes da query (parâmetros, sql)
        loadQueryDetails(currentQueryId);
    });

    async function loadQueryDetails(queryId) {
        try {
            const response = await fetch(`/api/query/${queryId}`);
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || "Falha ao carregar query");
            }
            
            currentQueryData = await response.json();
            
            // 1. Constrói o formulário de filtros
            buildFilterForm(currentQueryData.parameters);
            filterSection.style.display = "block";
            
            // 2. Prepara o modal de edição
            modalQueryName.textContent = currentQueryData.name;
            modalQuerySql.value = currentQueryData.sql;
            btnShowQueryModal.disabled = false;

        } catch (error) {
            showFeedback(`Erro: ${error.message}`, "error");
        }
    }

    function buildFilterForm(parameters) {
        filterFormInputs.innerHTML = ""; // Limpa filtros antigos
        
        parameters.forEach(param => {
            const formGroup = document.createElement("div");
            formGroup.className = "form-group";

            const label = document.createElement("label");
            label.setAttribute("for", `filter_${param.bind_name}`);
            label.textContent = param.label;

            const input = document.createElement("input");
            input.type = "text";
            input.id = `filter_${param.bind_name}`;
            input.name = param.bind_name;
            input.placeholder = param.placeholder || "";
            input.required = param.required;
            
            // Adiciona máscara de data
            if (param.label.includes('DD/MM/YYYY')) {
                addDateMask(input);
            }

            formGroup.appendChild(label);
            formGroup.appendChild(input);
            filterFormInputs.appendChild(formGroup);
        });
    }

    // --- 2. Evento: Buscar Dados (Submit do Filtro) ---
    searchForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        clearFeedback();
        hideResults();
        btnBuscar.disabled = true;
        btnBuscar.textContent = "Buscando...";

        // Coleta os filtros dinâmicos
        const formData = new FormData(searchForm);
        const params = {};
        for (let [key, value] of formData.entries()) {
            params[key] = value;
        }

        const data = {
            query_id: currentQueryId,
            params: params
        };

        try {
            const response = await fetch("/api/buscar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            });

            if (response.status === 404) {
                showNoResults();
            } else if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Erro ${response.status}`);
            } else {
                const resultData = await response.json();
                currentResultHeaders = resultData.headers;
                // Guarda as regras de update recebidas do servidor
                currentQueryData.update_rules = resultData.update_rules; 
                
                displayResults(resultData.headers, resultData.rows);
                buildUpdateForm(resultData.headers, resultData.update_rules);
            }

        } catch (error) {
            showFeedback(error.message, "error");
        } finally {
            btnBuscar.disabled = false;
            btnBuscar.textContent = "Buscar Registros";
        }
    });

    // --- 3. Evento: Atualizar Dados (Submit do Update) ---
    updateForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const selectedRowIDs = getSelectedRowIDs();
        if (selectedRowIDs.length === 0) {
            showFeedback("Erro: Nenhuma linha foi selecionada.", "error");
            return;
        }

        const formData = new FormData(updateForm);
        const updates = {};
        for (let [key, value] of formData.entries()) {
            if (value.trim() !== "") {
                updates[key] = value.trim();
            }
        }

        if (Object.keys(updates).length === 0) {
            showFeedback("Erro: Nenhum valor de alteração foi preenchido.", "error");
            return;
        }

        const confirmation = confirm(
            `--- RESUMO DA OPERAÇÃO ---\n\n` +
            `Alvo: ${selectedRowIDs.length} linhas\n` +
            `Alterações: \n${JSON.stringify(updates, null, 2)}\n\n` +
            `Confirmar e EXECUTAR?`
        );

        if (!confirmation) {
            showFeedback("Operação cancelada.", "error");
            return;
        }

        clearFeedback();
        btnAtualizar.disabled = true;
        btnAtualizar.textContent = "Atualizando...";

        try {
            const response = await fetch("/api/atualizar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query_id: currentQueryId,
                    rowids: selectedRowIDs,
                    updates: updates
                }),
            });

            const resultData = await response.json();
            if (!response.ok) {
                throw new Error(resultData.error || `Erro ${response.status}`);
            }

            showFeedback(resultData.message, "success");
            updateForm.reset();
            searchForm.requestSubmit(); // Recarrega os dados

        } catch (error) {
            showFeedback(error.message, "error");
        } finally {
            btnAtualizar.disabled = false;
            btnAtualizar.textContent = "Confirmar e Atualizar Linhas";
        }
    });

    // --- 4. Eventos do Modal ---
    btnShowQueryModal.addEventListener("click", () => {
        queryModal.classList.add("active");
    });
    btnCloseModal.addEventListener("click", () => {
        queryModal.classList.remove("active");
    });
    queryModal.addEventListener("click", (e) => {
        if (e.target === queryModal) queryModal.classList.remove("active");
    });
    
    btnSaveQuery.addEventListener("click", async () => {
        const newSql = modalQuerySql.value;
        if (!newSql) {
            alert("A query SQL não pode ser vazia.");
            return;
        }
        
        if (!confirm("Tem certeza que deseja salvar esta query? Esta ação é irreversível e afeta o servidor.")) {
            return;
        }

        try {
            const response = await fetch(`/api/query/${currentQueryId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ sql: newSql })
            });
            
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error);
            }
            
            // Atualiza a query em memória
            currentQueryData.sql = newSql;
            alert(result.message); // Sucesso
            queryModal.classList.remove("active");

        } catch (error) {
            alert(`Falha ao salvar: ${error.message}`);
        }
    });

    // --- Funções Auxiliares (DOM) ---

    function displayResults(headers, rows) {
        tableContainer.innerHTML = "";
        noResultsDiv.style.display = "none";
        const table = document.createElement("table");
        
        // Cabeçalho
        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");
        
        const thCheck = document.createElement("th");
        tableSelectAllCheckbox = document.createElement("input");
        tableSelectAllCheckbox.type = "checkbox";
        tableSelectAllCheckbox.title = "Selecionar Todos";
        tableSelectAllCheckbox.className = "row-selector";
        thCheck.appendChild(tableSelectAllCheckbox);
        headerRow.appendChild(thCheck);

        // Remove 'ROWID' dos cabeçalhos visuais
        const displayHeaders = headers.filter(h => h.toUpperCase() !== 'ROWID');
        displayHeaders.forEach(header => {
            const th = document.createElement("th");
            th.textContent = header;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Corpo
        const tbody = document.createElement("tbody");
        rows.forEach(row => {
            const tr = document.createElement("tr");
            const tdCheck = document.createElement("td");
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.className = "row-selector";
            checkbox.value = row.ROWID; // O valor é o ROWID
            tdCheck.appendChild(checkbox);
            tr.appendChild(tdCheck);

            displayHeaders.forEach(header => {
                const td = document.createElement("td");
                let value = row[header];
                if (header.includes('DATAHORA') && value) {
                    td.textContent = formatDateTime(value);
                } else {
                    td.textContent = (value === null || value === undefined) ? "" : value;
                }
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        tableContainer.appendChild(table);

        tableSelectAllCheckbox.addEventListener("change", () => {
            tableContainer.querySelectorAll('tbody .row-selector')
                .forEach(cb => cb.checked = tableSelectAllCheckbox.checked);
        });

        resultsSection.style.display = "block";
    }

    function buildUpdateForm(headers, updateRules) {
        updateFormInputs.innerHTML = ""; // Limpa inputs antigos
        
        // Constrói o form de update
        headers.forEach(header => {
            if (header.toUpperCase() === 'ROWID') return;

            const formGroup = document.createElement("div");
            formGroup.className = "form-group";

            const label = document.createElement("label");
            label.setAttribute("for", `update_${header}`);
            label.textContent = header;

            const input = document.createElement("input");
            input.type = "text";
            input.id = `update_${header}`;
            input.name = header;
            
            // Se a coluna não estiver nas regras, desabilita o campo
            if (!updateRules[header]) {
                input.disabled = true;
                input.title = "Esta coluna não está configurada para atualização no JSON.";
                label.style.color = "#999";
            } else if (header.includes('DATAHORA')) {
                input.placeholder = "DD/MM/YYYY HH24:MI:SS";
            }

            formGroup.appendChild(label);
            formGroup.appendChild(input);
            updateFormInputs.appendChild(formGroup);
        });
        updateSection.style.display = "block";
    }

    function getSelectedRowIDs() {
        const selected = tableContainer.querySelectorAll('tbody .row-selector:checked');
        return Array.from(selected).map(cb => cb.value);
    }

    function hideResults() {
        resultsSection.style.display = "none";
        updateSection.style.display = "none";
        tableContainer.innerHTML = "";
    }

    function showNoResults() {
        resultsSection.style.display = "block";
        updateSection.style.display = "none";
        tableContainer.innerHTML = "";
        noResultsDiv.style.display = "block";
    }

    function showFeedback(message, type = "success") {
        feedbackMessage.textContent = message;
        feedbackMessage.className = type;
    }

    function clearFeedback() {
        feedbackMessage.textContent = "";
        feedbackMessage.className = "";
    }

    function addDateMask(input) {
        input.setAttribute("maxlength", "10");
        input.addEventListener("input", (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 4) {
                value = value.substring(0, 2) + '/' + value.substring(2, 4) + '/' + value.substring(4, 8);
            } else if (value.length > 2) {
                value = value.substring(0, 2) + '/' + value.substring(2);
            }
            e.target.value = value;
        });
    }

    function formatDateTime(dateString) {
        if (!dateString) return "";
        try {
            const date = new Date(dateString);
            const pad = (num) => String(num).padStart(2, '0');
            const day = pad(date.getDate());
            const month = pad(date.getMonth() + 1);
            const year = date.getFullYear();
            const hours = pad(date.getHours());
            const minutes = pad(date.getMinutes());
            const seconds = pad(date.getSeconds());
            return `${day}/${month}/${year} ${hours}:${minutes}:${seconds}`;
        } catch (e) {
            return dateString;
        }
    }
});