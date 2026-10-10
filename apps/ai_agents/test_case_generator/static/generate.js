// Test case generator script

document.addEventListener('DOMContentLoaded', function() {
    const generateForm = document.getElementById('generate-form');
    const inputTypeRadios = document.querySelectorAll('input[name="input_type"]');
    const inputTextLabel = document.getElementById('input-text-label');
    const inputText = document.getElementById('input-text');
    const generateButton = document.getElementById('generate-button');
    const loadingIndicator = document.getElementById('loading-indicator');
    const resultContainer = document.getElementById('result-container');
    const saveButton = document.getElementById('save-button');
    
    // Change label text based on input type
    if (inputTypeRadios && inputTypeRadios.length > 0) {
        inputTypeRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'requirement') {
                    inputTextLabel.textContent = 'Requirements Description:';
                    inputText.placeholder = 'Please enter requirements description...';
                } else {
                    inputTextLabel.textContent = 'Code Snippet:';
                    inputText.placeholder = 'Please enter code snippet...';
                }
            });
        });
    }
    
    // Save preferred LLM provider to localStorage
    const llmProviderSelect = document.getElementById('llm-provider');
    if (llmProviderSelect) {
        llmProviderSelect.addEventListener('change', function() {
            localStorage.setItem('preferred-llm-provider', this.value);
        });
        
        // Restore user's previous selection on page load
        if (!llmProviderSelect.options[llmProviderSelect.selectedIndex].hasAttribute('selected')) {
            const savedProvider = localStorage.getItem('preferred-llm-provider');
            if (savedProvider) {
                // Ensure saved value exists in options
                for (let i = 0; i < llmProviderSelect.options.length; i++) {
                    if (llmProviderSelect.options[i].value === savedProvider) {
                        llmProviderSelect.value = savedProvider;
                        break;
                    }
                }
            }
        }
    }
    
    // Show loading indicator on form submit
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function() {
            if (loadingIndicator) {
                loadingIndicator.style.display = 'block';
            }
            if (generateButton) {
                generateButton.disabled = true;
            }
        });
    }
    
    // Submit form to generate test cases
    if (generateForm) {
        generateForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Form submit event triggered');
            
            // Get necessary DOM elements
            const loadingIndicator = document.getElementById('loading-indicator');
            const generateButton = document.getElementById('generate-button');
            const resultContainer = document.getElementById('result-container');
            const inputText = document.getElementById('input-text');
            
            // Get input text
            const inputTextValue = inputText?.value?.trim();
            
            // Get select elements
            const designMethodsSelect = document.getElementById('case_design_methods');
            const caseCategoriesSelect = document.getElementById('case_categories');
            
            if (!designMethodsSelect || !caseCategoriesSelect) {
                console.error('Cannot find select elements');
                return;
            }
            
            // Get selected values
            const selectedDesignMethods = Array.from(designMethodsSelect.selectedOptions || []).map(option => option.textContent);
            const selectedCaseCategories = Array.from(caseCategoriesSelect.selectedOptions || []).map(option => option.textContent);
            
            if (!inputTextValue) {
                showNotification('Please enter requirements description', 'error');
                return;
            }
            
            // Show loading indicator and clear result container
            if (loadingIndicator) {
                loadingIndicator.style.display = 'block';
            }
            if (resultContainer) {
                resultContainer.innerHTML = '';
            }
            if (generateButton) {
                generateButton.disabled = true;
            }
            
            // Construct request data
            const requestData = {
                requirements: inputTextValue,
                llm_provider: document.getElementById('llm-provider')?.value || 'deepseek',
                case_design_methods: selectedDesignMethods,
                case_categories: selectedCaseCategories,
                case_count: document.getElementById('case_count')?.value || '10'
            };
            
            console.log('Sent data:', requestData);
            
            // Send request
            fetch('/test_case_generator/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(requestData)
            })
            .then(response => {
                console.log('Received response:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Parsed response data:', data);
                
                // Hide loading indicator
                if (loadingIndicator) {
                    loadingIndicator.style.display = 'none';
                }
                if (generateButton) {
                    generateButton.disabled = false;
                }
                
                if (data.success) {
                    // Create or get result-container
                    let resultContainer = document.getElementById('result-container');
                    if (!resultContainer) {
                        resultContainer = document.createElement('div');
                        resultContainer.id = 'result-container';
                        resultContainer.className = 'mt-4';
                        generateForm.parentNode.insertBefore(resultContainer, generateForm.nextSibling);
                    }
                    
                    // Display test cases
                    displayTestCases(data.test_cases);
                    
                    // Save generated test cases to sessionStorage
                    sessionStorage.setItem('generatedTestCases', JSON.stringify(data.test_cases));
                    sessionStorage.setItem('inputText', inputTextValue);
                    
                    // Rebind save button event
                    const saveButton = document.getElementById('save-button');
                    if (saveButton) {
                        saveButton.disabled = false;
                    }
                } else {
                    console.error('Server error:', data.message);
                    if (resultContainer) {
                        resultContainer.innerHTML = `<div class="alert alert-danger">${data.message || 'Error generating test cases'}</div>`;
                    }
                }
            })
            .catch(error => {
                console.error('Request error:', error);
                if (loadingIndicator) {
                    loadingIndicator.style.display = 'none';
                }
                if (resultContainer) {
                    resultContainer.innerHTML = `<div class="alert alert-danger">Request failed: ${error.message}</div>`;
                }
            });
        });
    }
    
    // Display test cases
    function displayTestCases(testCases) {
        // Get or create resultContainer
        let resultContainer = document.getElementById('result-container');
        if (!resultContainer) {
            resultContainer = document.createElement('div');
            resultContainer.id = 'result-container';
            resultContainer.className = 'mt-4';
            const generateForm = document.getElementById('generate-form');
            if (generateForm) {
                generateForm.parentNode.insertBefore(resultContainer, generateForm.nextSibling);
            } else {
                document.body.appendChild(resultContainer);
            }
        }

        if (!testCases || !testCases.length) {
            resultContainer.innerHTML = '<div class="alert alert-info">No test cases generated</div>';
            return;
        }
        
        let html = `
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Generated Test Cases</h5>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-bordered table-hover">
                            <thead class="thead-light">
                                <tr>
                                    <th width="5%">#</th>
                                    <th width="25%">Description</th>
                                    <th width="35%">Test Steps</th>
                                    <th width="35%">Expected Results</th>
                                </tr>
                            </thead>
                            <tbody>
        `;

        testCases.forEach((testCase, index) => {
            // Ensure test_steps and expected_results are arrays
            const testSteps = Array.isArray(testCase.test_steps) 
                ? testCase.test_steps 
                : testCase.test_steps.split('\n').filter(step => step.trim());
            
            const expectedResults = Array.isArray(testCase.expected_results)
                ? testCase.expected_results
                : testCase.expected_results.split('\n').filter(result => result.trim());

            html += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${testCase.description || ''}</td>
                    <td>
                        ${testSteps.map(step => `<div class="mb-2">${step}</div>`).join('')}
                    </td>
                    <td>
                        ${expectedResults.map(result => `<div class="mb-2">${result}</div>`).join('')}
                    </td>
                </tr>
            `;
        });

        html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            <div class="text-right mt-3">
                <button id="save-button" class="btn btn-success">Save Test Cases</button>
            </div>
        `;

        resultContainer.innerHTML = html;

        // Rebind save button click event
        const saveButton = document.getElementById('save-button');
        if (saveButton) {
            saveButton.disabled = false;
            
            saveButton.addEventListener('click', function() {
                console.log('Save button clicked');
                
                // Try to get data from sessionStorage
                let testCases = null;
                try {
                    testCases = JSON.parse(sessionStorage.getItem('generatedTestCases') || '[]');
                } catch (error) {
                    console.error('Failed to parse test case data:', error);
                    alert('Failed to parse test case data. See console for details.');
                    return;
                }
                
                if (!testCases || testCases.length === 0) {
                    alert('No test cases to save.');
                    return;
                }
                
                // Get other required data
                const requirementElement = document.getElementById('input-text');
                const llmProviderElement = document.getElementById('llm-provider');
                
                if (!requirementElement || !llmProviderElement) {
                    console.error('Missing required page elements');
                    alert('Missing page elements, cannot save data.');
                    return;
                }
                
                // Prepare request data
                const requestData = {
                    test_cases: testCases,
                    requirement: requirementElement.value,
                    llm_provider: llmProviderElement.value
                };
                
                // Disable button to prevent duplicate submissions
                saveButton.disabled = true;
                saveButton.textContent = 'Saving...';
                
                // Send save request
                fetch('/test_case_generator/save-test-case/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                })
                .then(response => response.json())
                .then(data => {
                    saveButton.textContent = 'Save Test Cases';
                    
                    if (data.success) {
                        alert('Test cases saved successfully!');
                        // Clear sessionStorage
                        sessionStorage.removeItem('generatedTestCases');
                        sessionStorage.removeItem('inputText');
                    } else {
                        saveButton.disabled = false;
                        alert('Save failed: ' + (data.message || 'Unknown error'));
                    }
                })
                .catch(error => {
                    saveButton.disabled = false;
                    saveButton.textContent = 'Save Test Cases';
                    console.error('Save failed:', error);
                    alert('Save failed. See console for details.');
                });
            });
        }
    }
    
    // Helper function to get CSRF Token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}); 