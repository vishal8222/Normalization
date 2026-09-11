const app = {
    state: {
        sessionId: null,
        columns: [],
        dependencies: [],
        primaryKey: [],
        result: null
    },

    init() {
        this.setupUploadHandlers();
        this.setupDependencyHandlers();
        this.loadHistory();
        this.setupSearch();
    },

    // ===== UI UTILITIES =====
    showSection(id) {
        document.querySelectorAll('.step-card').forEach(el => el.classList.add('hidden'));
        document.getElementById(id).classList.remove('hidden');
    },

    showLoading(show = true) {
        const overlay = document.getElementById('loading-overlay');
        if (show) overlay.classList.remove('hidden');
        else overlay.classList.add('hidden');
    },

    showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => { clearTimeout(timeout); func(...args); };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // ===== STEP 1: UPLOAD =====
    setupUploadHandlers() {
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                this.uploadFile(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                this.uploadFile(e.target.files[0]);
            }
        });

        document.getElementById('proceed-step-2').addEventListener('click', () => {
            this.showSection('dependency-section');
            this.renderPrimaryKeySelector();
        });
    },

    async uploadFile(file) {
        this.showLoading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            
            if (!res.ok) throw new Error(data.error || 'Upload failed');

            this.state.sessionId = data.session_id;
            this.state.columns = data.columns;
            this.state.suggestedDependencies = data.suggested_dependencies || [];
            this.state.suggestedPrimaryKey = data.suggested_primary_key || [];
            
            this.showPreview(data.sample_data, data.columns);
            this.showToast('File uploaded successfully!');
        } catch (err) {
            this.showToast(err.message, 'error');
        } finally {
            this.showLoading(false);
            // Reset input
            document.getElementById('file-input').value = '';
        }
    },

    showPreview(data, columns) {
        const container = document.getElementById('preview-table-container');
        if (!data || !data.length) {
            container.innerHTML = '<p>No data to preview.</p>';
        } else {
            let html = '<table><thead><tr>';
            columns.forEach(col => html += `<th>${col}</th>`);
            html += '</tr></thead><tbody>';
            
            data.forEach(row => {
                html += '<tr>';
                columns.forEach(col => {
                    html += `<td>${row[col] !== undefined ? row[col] : ''}</td>`;
                });
                html += '</tr>';
            });
            html += '</tbody></table>';
            container.innerHTML = html;
        }

        document.getElementById('upload-preview').classList.remove('hidden');
    },

    // ===== STEP 2: DEPENDENCIES =====
    setupDependencyHandlers() {
        document.getElementById('add-dep-btn').addEventListener('click', () => this.addDependencyRow());
        document.getElementById('back-step-1').addEventListener('click', () => this.showSection('upload-section'));
        document.getElementById('normalize-btn').addEventListener('click', () => this.submitAndNormalize());
        const autoBtn = document.getElementById('auto-detect-btn');
        if (autoBtn) {
            autoBtn.addEventListener('click', () => this.autoDetectDependencies());
        }
    },

    renderPrimaryKeySelector() {
        const container = document.getElementById('pk-selector');
        container.innerHTML = '';
        const suggestedPks = this.state.suggestedPrimaryKey || [];

        this.state.columns.forEach(col => {
            const isChecked = suggestedPks.includes(col);
            const div = document.createElement('div');
            div.className = 'checkbox-item';
            div.innerHTML = `
                <input type="checkbox" id="pk_${col}" value="${col}" ${isChecked ? 'checked' : ''}>
                <label for="pk_${col}">${col}</label>
            `;
            container.appendChild(div);
        });
        
        // Reset deps container
        document.getElementById('deps-container').innerHTML = '';
        
        // If we have auto-detected dependencies, auto-populate them right away!
        if (this.state.suggestedDependencies && this.state.suggestedDependencies.length) {
            this.state.suggestedDependencies.forEach(dep => {
                this.addDependencyRow(dep.determinant, dep.dependent);
            });
            this.showToast(`Auto-detected ${this.state.suggestedDependencies.length} functional dependencies!`);
        } else {
            this.addDependencyRow(); // add one empty row
        }
    },

    autoDetectDependencies() {
        if (!this.state.suggestedDependencies || !this.state.suggestedDependencies.length) {
            this.showToast('No functional dependencies discovered automatically. You can add them manually!', 'info');
            return;
        }
        const container = document.getElementById('deps-container');
        container.innerHTML = '';
        this.state.suggestedDependencies.forEach(dep => {
            this.addDependencyRow(dep.determinant, dep.dependent);
        });
        this.showToast(`Populated ${this.state.suggestedDependencies.length} functional dependencies.`);
    },

    addDependencyRow(selectedDets = [], selectedDeps = []) {
        const container = document.getElementById('deps-container');
        const rowId = 'dep_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);
        const row = document.createElement('div');
        row.className = 'dependency-row';
        row.id = rowId;

        const detOptions = this.state.columns.map(c => {
            const sel = selectedDets.includes(c) ? 'selected' : '';
            return `<option value="${c}" ${sel}>${c}</option>`;
        }).join('');

        const depOptions = this.state.columns.map(c => {
            const sel = selectedDeps.includes(c) ? 'selected' : '';
            return `<option value="${c}" ${sel}>${c}</option>`;
        }).join('');
        
        row.innerHTML = `
            <div style="flex:1;">
                <small style="font-weight:600; color:#1b4f72;">Determinant (LHS):</small>
                <select multiple class="det-select" size="3" title="Hold Ctrl/Cmd to select multiple">${detOptions}</select>
            </div>
            <span style="font-size:1.5rem; color:#1b4f72; align-self:center;"> ➡️ </span>
            <div style="flex:1;">
                <small style="font-weight:600; color:#1b4f72;">Dependent (RHS):</small>
                <select multiple class="dep-select" size="3" title="Hold Ctrl/Cmd to select multiple">${depOptions}</select>
            </div>
            <button class="delete-btn" style="align-self:center;" onclick="document.getElementById('${rowId}').remove()">✖</button>
        `;
        container.appendChild(row);
    },

    collectDependencies() {
        // Collect PKs
        this.state.primaryKey = Array.from(document.querySelectorAll('#pk-selector input:checked')).map(cb => cb.value);

        // Collect Deps
        this.state.dependencies = [];
        document.querySelectorAll('.dependency-row').forEach(row => {
            const det = Array.from(row.querySelector('.det-select').selectedOptions).map(o => o.value);
            const dep = Array.from(row.querySelector('.dep-select').selectedOptions).map(o => o.value);
            if (det.length && dep.length) {
                this.state.dependencies.push({ determinant: det, dependent: dep });
            }
        });
    },

    async submitAndNormalize() {
        this.collectDependencies();
        
        if (!this.state.primaryKey.length) {
            this.showToast('Please select at least one Primary Key column.', 'error');
            return;
        }

        this.showLoading(true);

        try {
            // 1. Submit deps
            let res = await fetch('/api/dependencies', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    session_id: this.state.sessionId,
                    primary_key: this.state.primaryKey,
                    dependencies: this.state.dependencies
                })
            });
            if (!res.ok) throw new Error('Failed to save dependencies');

            // 2. Normalize
            res = await fetch('/api/normalize', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ session_id: this.state.sessionId })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Normalization failed');

            this.state.result = data;
            this.renderResults();
            this.showSection('results-section');
            this.showToast('Normalization complete!');
            this.loadHistory();
        } catch (err) {
            this.showToast(err.message, 'error');
        } finally {
            this.showLoading(false);
        }
    },

    // ===== STEP 3: RESULTS =====
    renderResults() {
        const r = this.state.result;
        if (!r) return;

        this.renderStepper(r.steps);
        this.renderStepDetails(r.steps);
        this.renderSQL(r.generated_ddl);
        this.renderStats(r);
        
        if (r.er_diagram_data && window.renderERDiagram) {
            window.renderERDiagram('er-diagram-container', r.er_diagram_data);
        }
    },

    renderStepper(steps) {
        const forms = steps.map(s => s.normal_form.toLowerCase());
        document.querySelectorAll('.stepper .step[data-step]').forEach(el => {
            const step = el.getAttribute('data-step');
            el.classList.remove('active', 'completed');
            if (forms.includes(step)) {
                el.classList.add('completed');
            }
        });
        document.querySelectorAll('.stepper .line').forEach(el => el.classList.add('completed'));
    },

    renderStepDetails(steps) {
        const container = document.getElementById('step-details');
        container.innerHTML = '';

        steps.forEach(step => {
            const div = document.createElement('div');
            div.className = 'step-details-content';
            
            let html = `<h3>${step.normal_form} Normalization</h3>`;
            html += `<p>${step.explanation || ''}</p>`;
            
            if (step.violations_found && step.violations_found.length) {
                html += `<h4>Violations Found:</h4>`;
                step.violations_found.forEach(v => {
                    html += `
                        <div class="violation-card">
                            <h4>⚠️ ${v.violation_type}</h4>
                            <p>${v.description}</p>
                            <small>Affected columns: ${v.affected_columns.join(', ')}</small>
                        </div>
                    `;
                });
            }

            if (step.resulting_tables && step.resulting_tables.length) {
                html += `<h4>Resulting Tables:</h4>`;
                step.resulting_tables.forEach(table => {
                    html += `<h5>${table.name}</h5>`;
                    html += this.generateTableHTML(table);
                });
            }
            div.innerHTML = html;
            container.appendChild(div);
            // Just append a separator
            container.appendChild(document.createElement('hr'));
        });
    },

    generateTableHTML(tableInfo) {
        if (!tableInfo.data || !tableInfo.data.length) return '<p>No data</p>';
        
        const cols = tableInfo.columns;
        let html = '<div class="table-container"><table><thead><tr>';
        
        cols.forEach(c => {
            let cls = '';
            let icon = '';
            if (c.is_primary_key) { cls = 'pk-col'; icon = '🔑 '; }
            else if (c.is_foreign_key) { cls = 'fk-col'; icon = '🔗 '; }
            html += `<th class="${cls}">${icon}${c.name} <small>(${c.data_type})</small></th>`;
        });
        html += '</tr></thead><tbody>';
        
        // Show max 10 rows
        const rows = tableInfo.data.slice(0, 10);
        rows.forEach(row => {
            html += '<tr>';
            cols.forEach(c => {
                let cls = '';
                if (c.is_primary_key) cls = 'pk-col';
                else if (c.is_foreign_key) cls = 'fk-col';
                html += `<td class="${cls}">${row[c.name] !== undefined ? row[c.name] : ''}</td>`;
            });
            html += '</tr>';
        });
        html += '</tbody></table></div>';
        if (tableInfo.data.length > 10) html += `<p><small>Showing 10 of ${tableInfo.data.length} rows</small></p>`;
        return html;
    },

    renderSQL(ddl) {
        const codeEl = document.getElementById('ddl-code');
        if (!ddl) {
            codeEl.textContent = '-- No SQL generated';
            return;
        }
        
        // Basic syntax highlighting
        let highlighted = ddl
            .replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/\b(CREATE|TABLE|PRIMARY|KEY|FOREIGN|REFERENCES|INT|VARCHAR|TEXT|BOOLEAN|DATE|DATETIME|FLOAT|DOUBLE)\b/gi, '<span class="sql-keyword">$1</span>')
            .replace(/('.*?')/g, '<span class="sql-string">$1</span>')
            .replace(/\b(\d+)\b/g, '<span class="sql-number">$1</span>');
            
        codeEl.innerHTML = highlighted;
    },

    renderStats(result) {
        const ctx = document.getElementById('stats-chart');
        if (!ctx) return;
        
        // Destroy existing chart if it exists
        if (this.chart) this.chart.destroy();

        const beforeCols = result.original_table?.columns?.length || 0;
        const afterTables = result.final_tables || [];
        const afterCols = afterTables.reduce((sum, t) => sum + (t.columns?.length || 0), 0);

        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Before Normalization', 'After Normalization'],
                datasets: [
                    {
                        label: 'Number of Tables',
                        data: [1, afterTables.length],
                        backgroundColor: '#1B4F72'
                    },
                    {
                        label: 'Total Columns',
                        data: [beforeCols, afterCols],
                        backgroundColor: '#28B463'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    },

    // ===== EXPORTS =====
    exportExcel() {
        if (!this.state.sessionId) return;
        window.open(`/api/export/excel/${this.state.sessionId}`, '_blank');
    },
    exportPdf() {
        if (!this.state.sessionId) return;
        window.open(`/api/export/pdf/${this.state.sessionId}`, '_blank');
    },
    exportSQL() {
        if (!this.state.sessionId) return;
        window.open(`/api/export/sql/${this.state.sessionId}`, '_blank');
    },
    
    copySQL() {
        const text = document.getElementById('ddl-code').innerText;
        navigator.clipboard.writeText(text).then(() => {
            this.showToast('SQL copied to clipboard!');
        }).catch(err => {
            this.showToast('Failed to copy text', 'error');
        });
    },

    reset() {
        this.state = { sessionId: null, columns: [], dependencies: [], primaryKey: [], result: null };
        document.getElementById('file-input').value = '';
        document.getElementById('upload-preview').classList.add('hidden');
        this.showSection('upload-section');
    },

    // ===== HISTORY =====
    async loadHistory() {
        try {
            const res = await fetch('/api/history');
            const data = await res.json();
            this.renderHistory(data.results || []);
        } catch (err) {
            console.error('Failed to load history', err);
        }
    },

    setupSearch() {
        const searchInput = document.getElementById('search-input');
        const handleSearch = this.debounce(async (e) => {
            const query = e.target.value.trim();
            if (!query) {
                this.loadHistory();
                return;
            }
            try {
                const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const data = await res.json();
                this.renderHistory(data.results || []);
            } catch (err) {
                console.error('Search failed', err);
            }
        }, 300);
        searchInput.addEventListener('input', handleSearch);
    },

    renderHistory(items) {
        const container = document.getElementById('history-list');
        container.innerHTML = '';
        if (!items.length) {
            container.innerHTML = '<p class="text-muted">No history found.</p>';
            return;
        }

        items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item';
            div.innerHTML = `
                <h4>${item.filename || 'Session: ' + item.session_id.substring(0, 8) + '...'}</h4>
                <p>Type: ${item.file_type || 'unknown'} | Tables: ${item.table_count || '-'}</p>
                <p class="text-muted"><small>${item.created_at || ''}</small></p>
            `;
            // Clicking a history item could hypothetically load it, 
            // but the API doesn't specify a GET /api/session/{id} endpoint yet.
            div.addEventListener('click', () => {
                this.state.result = item;
                this.state.sessionId = item.session_id;
                this.renderResults();
                this.showSection('results-section');
            });
            container.appendChild(div);
        });
    }
};

document.addEventListener('DOMContentLoaded', () => app.init());
