// API test case generator script

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('single_file');
    const submitBtn = document.getElementById('submitBtn');
    const selectedFileDiv = document.getElementById('selected-file');
    const statusDiv = document.getElementById('uploadStatus');

    // File selection event handler
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            updateFileName(this);
        });
    }

    // Drag & drop upload area event handler
    const uploadArea = document.querySelector('.upload-area');
    if (uploadArea) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, preventDefaults, false);
        });

        // Visual feedback on drag enter/leave
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, unhighlight, false);
        });

        // File drop handler
        uploadArea.addEventListener('drop', handleDrop, false);
    }

    // Form submit handler
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleSubmit(e);
        });
    }

    // Update file name display
    function updateFileName(input) {
        if (input.files && input.files[0]) {
            selectedFileDiv.style.display = 'block';
            selectedFileDiv.textContent = 'Selected file: ' + input.files[0].name;
            
            // Validate file type
            const fileName = input.files[0].name;
            if (!fileName.toLowerCase().endsWith('.json')) {
                statusDiv.textContent = 'Please select a JSON format file';
                statusDiv.style.color = '#dc3545';
                submitBtn.disabled = true;
            } else {
                statusDiv.textContent = '';
                submitBtn.disabled = false;
            }
        } else {
            selectedFileDiv.style.display = 'none';
            selectedFileDiv.textContent = '';
            statusDiv.textContent = '';
            submitBtn.disabled = false;
        }
    }

    // Prevent default drag behaviors
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight on drag enter
    function highlight(e) {
        uploadArea.classList.add('highlight');
    }

    // Unhighlight on drag leave
    function unhighlight(e) {
        uploadArea.classList.remove('highlight');
    }

    // Handle file drop
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            updateFileName(fileInput);
        }
    }

    // Handle form submit
    async function handleSubmit(event) {
        const form = event.target;
        const fileInput = form.querySelector('input[type="file"]');
        
        if (!fileInput.files || !fileInput.files[0]) {
            statusDiv.textContent = 'Please select a file to upload first';
            statusDiv.style.color = '#dc3545';
            return false;
        }

        // Validate file type
        const fileName = fileInput.files[0].name;
        if (!fileName.toLowerCase().endsWith('.json')) {
            statusDiv.textContent = 'Please select a JSON format file';
            statusDiv.style.color = '#dc3545';
            return false;
        }

        submitBtn.disabled = true;
        statusDiv.textContent = 'Uploading file, please wait...';
        statusDiv.style.color = '#007bff';
        statusDiv.style.fontWeight = 'bold';

        try {
            const formData = new FormData(form);
            
            // Send POST request to iface_case_generator route
            const response = await fetch('/iface_case_generator/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });

            const result = await response.json();

            if (result.success) {
                statusDiv.textContent = `File uploaded successfully! Parsing API details...`;
                statusDiv.style.color = '#28a745';
                fileInput.value = '';
                selectedFileDiv.style.display = 'none';
                
                // Handle API list
                handleFileUploadSuccess(result);
            } else {
                statusDiv.textContent = result.error || 'Upload failed, please try again';
                statusDiv.style.color = '#dc3545';
            }
        } catch (error) {
            console.error('Upload error:', error);
            statusDiv.textContent = 'An error occurred during upload, please try again';
            statusDiv.style.color = '#dc3545';
        } finally {
            submitBtn.disabled = false;
        }

        return false;
    }

    // Handle API list display after successful upload
    function handleFileUploadSuccess(response) {
        if (response.success && response.api_list) {
            // Hide upload area, show API selection interface
            document.querySelector('.upload-container').style.display = 'none';
            document.getElementById('api-selection').style.display = 'block';
            
            // Generate API table rows
            generateApiTableRows(response.api_list);
            
            // Save file path
            window.uploadedFilePath = response.file_path;

            // Initialize rule editor: fetch template rules from backend
            fetch('/iface_case_generator/api/testcase-rule-template/')
                .then(r => r.json())
                .then(data => {
                    if (data && data.success) {
                        window.defaultRuleText = data.rule_text || '';
                        const editor = document.getElementById('rule-editor');
                        if (editor) {
                            editor.value = window.defaultRuleText;
                            updateCharCount();
                            setupRuleEditorValidation();
                        }
                    }
                })
                .catch(() => {});
        }
    }

    // Update character count display
    function updateCharCount() {
        const editor = document.getElementById('rule-editor');
        const charCount = document.getElementById('rule-char-count');
        if (editor && charCount) {
            const currentLength = editor.value.length;
            charCount.textContent = `${currentLength}/1000`;
            
            // Change color based on char count
            if (currentLength > 1000) {
                charCount.style.color = '#dc3545'; // Red
            } else if (currentLength > 800) {
                charCount.style.color = '#ffc107'; // Yellow
            } else {
                charCount.style.color = '#6c757d'; // Grey
            }
        }
    }

    // Setup rule editor validation
    function setupRuleEditorValidation() {
        const editor = document.getElementById('rule-editor');
        if (!editor) return;

        // Character type validation: allow alphanumeric, whitespace, and punctuation
        editor.addEventListener('input', function(e) {
            const value = e.target.value;
            const validValue = value.replace(/[^\u4e00-\u9fa5a-zA-Z0-9\s\n\r\t\u3000-\u303f\uff00-\uffef\u2000-\u206f\u0020-\u002f\u003a-\u0040\u005b-\u0060\u007b-\u007e]/g, '');
            
            if (value !== validValue) {
                e.target.value = validValue;
                showValidationMessage('Only alphanumeric characters and punctuation are allowed', 'error');
            } else {
                clearValidationMessage();
            }
            
            updateCharCount();
        });

        // Character length limit
        editor.addEventListener('input', function(e) {
            const value = e.target.value;
            if (value.length > 1000) {
                e.target.value = value.substring(0, 1000);
                showValidationMessage('Character count cannot exceed 1000', 'error');
            } else {
                clearValidationMessage();
            }
            updateCharCount();
        });

        // Paste event handler
        editor.addEventListener('paste', function(e) {
            setTimeout(() => {
                const value = e.target.value;
                const validValue = value.replace(/[^\u4e00-\u9fa5a-zA-Z0-9\s\n\r\t\u3000-\u303f\uff00-\uffef\u2000-\u206f\u0020-\u002f\u003a-\u0040\u005b-\u0060\u007b-\u007e]/g, '');
                
                if (value !== validValue) {
                    e.target.value = validValue;
                    showValidationMessage('Pasted content contains invalid characters; automatically filtered', 'warning');
                }
                
                if (value.length > 1000) {
                    e.target.value = value.substring(0, 1000);
                    showValidationMessage('Pasted content exceeds 1000 character limit; truncated', 'warning');
                }
                
                updateCharCount();
            }, 0);
        });
    }

    // Show validation message
    function showValidationMessage(message, type) {
        const msgEl = document.getElementById('rule-validate-msg');
        if (msgEl) {
            msgEl.textContent = message;
            msgEl.style.color = type === 'error' ? '#dc3545' : '#ffc107';
        }
    }

    // Clear validation message
    function clearValidationMessage() {
        const msgEl = document.getElementById('rule-validate-msg');
        if (msgEl) {
            msgEl.textContent = '';
            msgEl.style.color = '#6c757d';
        }
    }

    // Generate API table rows
    function generateApiTableRows(apiList) {
        const tbody = document.getElementById('api-table-body');
        tbody.innerHTML = '';
        
        apiList.forEach(api => {
            console.log('API data:', api);
            console.log('has_test_cases:', api.has_test_cases);
            console.log('test_case_count:', api.test_case_count, 'type:', typeof api.test_case_count);
            
            const row = document.createElement('tr');
            
            // Column 1: Checkbox
            const checkboxCell = document.createElement('td');
            checkboxCell.style.width = '80px';
            checkboxCell.style.textAlign = 'center';
            checkboxCell.style.padding = '8px';
            checkboxCell.style.border = '1px solid #dee2e6';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'api-checkbox';
            checkbox.value = api.path;
            checkbox.id = `api-${api.path.replace(/[^a-zA-Z0-9]/g, '-')}`;
            checkbox.style.margin = '0';
            checkbox.style.transform = 'scale(1.2)';
            
            checkboxCell.appendChild(checkbox);
            
            // Column 2: API Path
            const pathCell = document.createElement('td');
            pathCell.style.width = '40%';
            pathCell.style.padding = '8px';
            pathCell.style.border = '1px solid #dee2e6';
            pathCell.innerHTML = `<code>${api.method} ${api.path}</code>`;
            
            // Column 3: API Name
            const nameCell = document.createElement('td');
            nameCell.style.padding = '8px';
            nameCell.style.border = '1px solid #dee2e6';
            let nameContent = api.name;
            if (api.has_test_cases) {
                let cnt = null;
                if (api.test_case_count !== undefined && api.test_case_count !== null) {
                    const n = Number(api.test_case_count);
                    if (!Number.isNaN(n)) cnt = n;
                }
                console.log('Calculated cnt:', cnt);
                nameContent += ` <span class="badge badge-info">Already has (<span style="font-size: 2.0em; font-weight: bold; color: red;">${cnt}</span>) test cases</span>`;
            }
            nameCell.innerHTML = nameContent;
            
            // Assemble row
            row.appendChild(checkboxCell);
            row.appendChild(pathCell);
            row.appendChild(nameCell);
            
            tbody.appendChild(row);
        });
        
        // Bind select all functionality
        bindSelectAllFunctionality();
    }

    // Generate test cases button event
    document.getElementById('generateBtn').addEventListener('click', function() {
        const selectedApis = getSelectedApis();
        if (selectedApis.length === 0) {
            alert('Please select at least one API');
            return;
        }
        
        const countInput = document.getElementById('count-per-api');
        let countPerApi = parseInt(countInput.value || '0', 10);
        if (isNaN(countPerApi) || countPerApi <= 0) {
            alert('Generation count per API must be a positive integer');
            countInput.focus();
            return;
        }
        
        const totalCount = selectedApis.length * countPerApi;
        if (totalCount < 1 || totalCount > 100) {
            alert(`Total test cases generated per batch cannot exceed 100`);
            return;
        }
        
        const priority = document.getElementById('priority').value;
        const llmProvider = document.getElementById('llm-provider').value;
        
        // Show progress interface and logs area
        document.getElementById('api-selection').style.display = 'none';
        document.getElementById('generation-progress').style.display = 'block';
        document.getElementById('live-logs').style.display = 'block';
        
        // Send generation request
        generateTestCases(selectedApis, countPerApi, priority, llmProvider);
    });

    // Enforce digit-only input for count-per-api
    (function enforceDigitOnlyForCountInput() {
        const countInput = document.getElementById('count-per-api');
        if (!countInput) return;

        // Prompt numeric keypad on mobile devices
        try {
            countInput.setAttribute('inputmode', 'numeric');
            countInput.setAttribute('pattern', '\\d*');
        } catch (_) {}

        const sanitize = () => {
            const digits = (countInput.value || '').replace(/\D+/g, '');
            countInput.value = digits;
        };

        countInput.addEventListener('input', sanitize);
        countInput.addEventListener('paste', function() {
            setTimeout(sanitize, 0);
        });
        countInput.addEventListener('blur', function() {
            sanitize();
            if (countInput.value === '' || countInput.value === '0') {
                countInput.value = '1';
            }
        });
    })();

    // Bind select-all functionality
    function bindSelectAllFunctionality() {
        const selectAllCheckbox = document.getElementById('select-all');
        const apiCheckboxes = document.querySelectorAll('.api-checkbox');
        
        // Select all checkbox click event
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            
            // Update all API checkboxes state
            apiCheckboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
            });
        });
        
        // Individual API checkbox click event
        apiCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                updateSelectAllState();
            });
        });
    }
    
    // Update select-all state
    function updateSelectAllState() {
        const selectAllCheckbox = document.getElementById('select-all');
        const apiCheckboxes = document.querySelectorAll('.api-checkbox');
        const checkedCount = document.querySelectorAll('.api-checkbox:checked').length;
        const totalCount = apiCheckboxes.length;
        
        if (checkedCount === 0) {
            // None checked
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
        } else if (checkedCount === totalCount) {
            // All checked
            selectAllCheckbox.checked = true;
            selectAllCheckbox.indeterminate = false;
        } else {
            // Indeterminate
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = true;
        }
    }
    
    // Get selected APIs
    function getSelectedApis() {
        const checkboxes = document.querySelectorAll('#api-table-body input[type="checkbox"]:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    // Generate test cases
    async function generateTestCases(selectedApis, countPerApi, priority, llmProvider) {
        try {
            const formData = new FormData();
            formData.append('generate_test_cases', 'true');
            formData.append('file_path', window.uploadedFilePath);
            formData.append('selected_apis', JSON.stringify(selectedApis));
            formData.append('count_per_api', countPerApi);
            formData.append('priority', priority);
            formData.append('llm_provider', llmProvider);
            // Rule override
            const editor = document.getElementById('rule-editor');
            const msgEl = document.getElementById('rule-validate-msg');
            let rulesOverride = '';
            if (editor) {
                const current = (editor.value || '').trim();
                const defaultText = (window.defaultRuleText || '').trim();
                if (current && current !== defaultText) {
                    // Validate characters and length
                    const isValidChars = /^[\u4e00-\u9fa5a-zA-Z0-9\s\n\r\t\u3000-\u303f\uff00-\uffef\u2000-\u206f\u0020-\u002f\u003a-\u0040\u005b-\u0060\u007b-\u007e]*$/.test(current);
                    const isValidLength = current.length <= 1000;
                    
                    if (!isValidChars) {
                        if (msgEl) {
                            msgEl.textContent = 'Rules contain invalid characters. Custom rules ignored.';
                            msgEl.style.color = '#dc3545';
                        }
                    } else if (!isValidLength) {
                        if (msgEl) {
                            msgEl.textContent = 'Rule text exceeds 1000 characters. Custom rules ignored, using default template.';
                            msgEl.style.color = '#dc3545';
                        }
                    } else {
                        rulesOverride = current;
                        if (msgEl) {
                            msgEl.textContent = 'Using custom rules';
                            msgEl.style.color = '#28a745';
                        }
                    }
                }
            }
            if (rulesOverride) {
                formData.append('rules_override', rulesOverride);
            }
            
            const response = await fetch('/iface_case_generator/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Start polling progress
                if (result.task_id) {
                    window.currentTaskId = result.task_id;
                    // Try SSE first, fallback to polling
                    startSSE(result.task_id);
                }
            } else {
                alert('Generation failed: ' + result.error);
                // Return to selection interface
                document.getElementById('generation-progress').style.display = 'none';
                document.getElementById('api-selection').style.display = 'block';
            }
            
        } catch (error) {
            console.error('Failed to generate test cases:', error);
            alert('Generation failed: ' + error.message);
            // Return to selection interface
            document.getElementById('generation-progress').style.display = 'none';
            document.getElementById('api-selection').style.display = 'block';
        }
    }

    // Poll progress
    async function pollProgress(taskId) {
        try {
            const resp = await fetch(`/iface_case_generator/api/get-generation-progress/?task_id=${encodeURIComponent(taskId)}`);
            const data = await resp.json();
            if (!data.success) return;
            updateProgressUI(data.progress);
            if (data.progress && data.progress.percentage >= 100) {
                if (window.progressTimer) {
                    clearInterval(window.progressTimer);
                    window.progressTimer = null;
                }
            }
        } catch (e) {
            console.error('Failed to query progress:', e);
        }
    }

    // SSE first, fallback to polling
    function startSSE(taskId) {
        try {
            // Clean up old connection
            if (window.es) {
                try { window.es.close(); } catch (_) {}
                window.es = null;
            }

            // Poll once immediately
            pollProgress(taskId);

            const url = `/api/stream-logs/?task_id=${encodeURIComponent(taskId)}`;
            const es = new EventSource(url);
            window.es = es;

            es.onopen = () => {
                // Re-poll after connection established
                pollProgress(taskId);
            };
            // Poll progress on log event
            es.addEventListener('log', () => {
                pollProgress(taskId);
            });
            // Backend progress event
            es.addEventListener('progress', () => {
                pollProgress(taskId);
            });
            es.onerror = () => {
                // Connection error, fallback to polling
                try { es.close(); } catch (_) {}
                window.es = null;
                // Start fallback polling
                if (!window.progressTimer) {
                    window.progressTimer = setInterval(() => pollProgress(taskId), 2000);
                }
            };
            // Start fallback polling
            if (!window.progressTimer) {
                window.progressTimer = setInterval(() => pollProgress(taskId), 2000);
            }
        } catch (_) {
            // Fallback to polling
            pollProgress(taskId);
            if (!window.progressTimer) {
                window.progressTimer = setInterval(() => pollProgress(taskId), 2000);
            }
        }
    }

    function updateProgressUI(progress) {
        const bar = document.getElementById('progress-bar');
        const text = document.getElementById('progress-text');
        const currentApi = document.getElementById('current-api');
        const logsBox = document.getElementById('live-logs');
        
        if (bar && typeof progress.percentage === 'number') {
            bar.style.width = progress.percentage + '%';
        }
        if (text && progress.message) {
            text.textContent = progress.message;
        }
        if (currentApi) {
            currentApi.textContent = progress.current_api ? `Current API: ${progress.current_api}` : '';
        }
        if (logsBox && Array.isArray(progress.logs)) {
            logsBox.innerHTML = progress.logs.map(l => `<div>${formatLogEntry(l)}</div>`).join('');
            logsBox.scrollTop = logsBox.scrollHeight;
        }
        // Auto-display results upon completion
        if (progress.percentage >= 100) {
            // Hide progress bar elements
            document.getElementById('progress-bar').style.display = 'none';
            document.getElementById('progress-text').style.display = 'none';
            document.getElementById('current-api').style.display = 'none';
            
            // Hide progress title
            const progressTitle = document.querySelector('#generation-progress h3');
            if (progressTitle) {
                progressTitle.style.display = 'none';
            }
            
            // Switch to result section
            const progressContainer = document.getElementById('generation-progress');
            if (progressContainer) progressContainer.style.display = 'none';
            document.getElementById('generation-result').style.display = 'block';
            document.getElementById('live-logs').style.display = 'block';
            document.getElementById('result-message').textContent = progress.message || 'API test case generation completed';
            if (progress.file_path) {
                document.getElementById('download-link').href = `/iface_case_generator/download_file/?file_path=${encodeURIComponent(progress.file_path)}`;
                document.getElementById('download-link').classList.remove('disabled');
            }
            // Cleanup SSE and polling on completion
            if (window.es) {
                try { window.es.close(); } catch (_) {}
                window.es = null;
            }
            if (window.progressTimer) {
                clearInterval(window.progressTimer);
                window.progressTimer = null;
            }
        }
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatLogEntry(logEntry) {
        const escaped = escapeHtml(logEntry);
        
        // Add color according to log level
        if (escaped.includes(' - ERROR - ')) {
            return `<span style="color: #ff6b6b;">${escaped}</span>`; // Red - Error
        } else if (escaped.includes(' - WARNING - ')) {
            return `<span style="color: #ffa726;">${escaped}</span>`; // Orange - Warning
        } else {
            return `<span style="color: #ffffff;">${escaped}</span>`; // White - Other levels
        }
    }

    // Display generation result
    function showGenerationResult(result) {
        document.getElementById('generation-progress').style.display = 'none';
        document.getElementById('generation-result').style.display = 'block';
        
        document.getElementById('result-message').textContent = result.message;
        document.getElementById('download-link').href = `/iface_case_generator/download_file/?file_path=${encodeURIComponent(result.file_path)}`;
    }

    // Closed-Loop Runner & Exporter bindings
    const executeSuiteBtn = document.getElementById('executeSuiteBtn');
    const exportPytestBtn = document.getElementById('exportPytestBtn');
    const exportPostmanBtn = document.getElementById('exportPostmanBtn');

    if (executeSuiteBtn) {
        executeSuiteBtn.addEventListener('click', async function() {
            const baseUrlInput = document.getElementById('target-base-url');
            const baseUrl = baseUrlInput ? baseUrlInput.value.trim() : '';
            if (!baseUrl) {
                alert('Please enter a target base URL (e.g. http://127.0.0.1:8000)');
                return;
            }

            const spinner = document.getElementById('execution-spinner');
            const resultsCard = document.getElementById('execution-results-card');
            if (spinner) spinner.style.display = 'block';
            if (resultsCard) resultsCard.style.display = 'none';
            executeSuiteBtn.disabled = true;

            try {
                const response = await fetch('/iface_case_generator/api/execute/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                    },
                    body: JSON.stringify({
                        base_url: baseUrl,
                        file_path: window.uploadedFilePath
                    })
                });

                let data = {};
                try {
                    data = await response.json();
                } catch (_) {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText || 'Server error'}`);
                    }
                    throw new Error('Invalid JSON response from server');
                }
                if (response.ok && data.success && data.summary) {
                    renderExecutionSummary(data.summary);
                } else {
                    alert('Execution failed: ' + (data.message || response.statusText || 'Unknown error'));
                }
            } catch (err) {
                console.error('Test execution error:', err);
                alert('Failed to execute test suite: ' + err.message);
            } finally {
                if (spinner) spinner.style.display = 'none';
                executeSuiteBtn.disabled = false;
            }
        });
    }

    function renderExecutionSummary(summary) {
        const resultsCard = document.getElementById('execution-results-card');
        if (resultsCard) resultsCard.style.display = 'block';

        const statTotal = document.getElementById('stat-total');
        const statPassed = document.getElementById('stat-passed');
        const statFailed = document.getElementById('stat-failed');
        const statRate = document.getElementById('stat-rate');
        const statTime = document.getElementById('stat-time');

        if (statTotal) statTotal.textContent = summary.total_executed || 0;
        if (statPassed) statPassed.textContent = summary.passed || 0;
        if (statFailed) statFailed.textContent = summary.failed || 0;
        if (statRate) statRate.textContent = (summary.pass_rate || 0) + '%';
        if (statTime) statTime.textContent = (summary.total_duration_ms || 0) + ' ms';

        const tbody = document.getElementById('execution-results-body');
        if (!tbody) return;
        tbody.innerHTML = '';

        (summary.results || []).forEach((res, idx) => {
            const tr = document.createElement('tr');
            const statusClass = res.status === 'PASSED' ? 'badge-success' : 'badge-danger';
            const methodClass = res.method === 'GET' ? 'badge-info' : (res.method === 'POST' ? 'badge-primary' : 'badge-warning');

            const passedAssertions = (res.assertions || []).filter(a => a.passed).length;
            const totalAssertions = (res.assertions || []).length;

            tr.innerHTML = `
                <td><span class="badge ${statusClass}">${escapeHtml(res.status)}</span></td>
                <td><span class="badge ${methodClass}">${escapeHtml(res.method || 'GET')}</span></td>
                <td>
                    <strong>${escapeHtml(res.name || 'API Case')}</strong><br>
                    <small class="text-muted">${escapeHtml(res.url || '')}</small>
                </td>
                <td><code>${escapeHtml(String(res.status_code || '-'))}</code></td>
                <td>${res.latency_ms ? escapeHtml(String(res.latency_ms)) + ' ms' : '-'}</td>
                <td><span class="badge ${passedAssertions === totalAssertions ? 'badge-success' : 'badge-danger'}">${passedAssertions}/${totalAssertions}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline-info" type="button" data-toggle="collapse" data-target="#detail-${idx}">
                        Details
                    </button>
                </td>
            `;
            tbody.appendChild(tr);

            // Collapsible details row
            const detailTr = document.createElement('tr');
            detailTr.className = 'collapse';
            detailTr.id = `detail-${idx}`;
            
            let assertionsHtml = '';
            if (res.assertions && res.assertions.length > 0) {
                assertionsHtml = `
                    <h6>Assertions:</h6>
                    <ul class="list-group mb-2">
                        ${res.assertions.map(a => `
                            <li class="list-group-item d-flex justify-content-between align-items-center py-1">
                                <span><code>${escapeHtml(a.expression)}</code> ${escapeHtml(a.operator)} <code>${escapeHtml(JSON.stringify(a.expected))}</code></span>
                                <span>
                                    <span class="badge ${a.passed ? 'badge-success' : 'badge-danger'} mr-2">${a.passed ? 'PASS' : 'FAIL'}</span>
                                    <small class="text-muted">Actual: <code>${escapeHtml(JSON.stringify(a.actual))}</code></small>
                                </span>
                            </li>
                        `).join('')}
                    </ul>
                `;
            }

            const errorHtml = res.error ? `<div class="alert alert-danger py-1 mb-0"><small><strong>Error:</strong> ${escapeHtml(res.error)}</small></div>` : '';

            detailTr.innerHTML = `
                <td colspan="7" class="bg-light p-3">
                    ${assertionsHtml}
                    ${errorHtml}
                </td>
            `;
            tbody.appendChild(detailTr);
        });
    }

    if (exportPytestBtn) {
        exportPytestBtn.addEventListener('click', async function() {
            const baseUrlInput = document.getElementById('target-base-url');
            const baseUrl = baseUrlInput ? baseUrlInput.value.trim() : 'http://127.0.0.1:8000';

            try {
                const response = await fetch('/iface_case_generator/api/export-pytest/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                    },
                    body: JSON.stringify({
                        base_url: baseUrl,
                        file_path: window.uploadedFilePath
                    })
                });

                if (!response.ok) {
                    let errMsg = response.statusText || `HTTP ${response.status}`;
                    try {
                        const err = await response.json();
                        if (err && err.message) errMsg = err.message;
                    } catch (_) {}
                    alert('Pytest export failed: ' + errMsg);
                    return;
                }

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'test_api_generated.py';
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            } catch (err) {
                console.error('Export Pytest error:', err);
                alert('Export failed: ' + err.message);
            }
        });
    }

    if (exportPostmanBtn) {
        exportPostmanBtn.addEventListener('click', async function() {
            const baseUrlInput = document.getElementById('target-base-url');
            const baseUrl = baseUrlInput ? baseUrlInput.value.trim() : 'http://127.0.0.1:8000';

            try {
                const response = await fetch('/iface_case_generator/api/export-postman/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                    },
                    body: JSON.stringify({
                        base_url: baseUrl,
                        file_path: window.uploadedFilePath
                    })
                });

                if (!response.ok) {
                    let errMsg = response.statusText || `HTTP ${response.status}`;
                    try {
                        const err = await response.json();
                        if (err && err.message) errMsg = err.message;
                    } catch (_) {}
                    alert('Postman export failed: ' + errMsg);
                    return;
                }

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'codebrain_postman_collection.json';
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            } catch (err) {
                console.error('Export Postman error:', err);
                alert('Export failed: ' + err.message);
            }
        });
    }
});

