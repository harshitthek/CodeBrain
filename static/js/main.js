// Main JavaScript file

document.addEventListener('DOMContentLoaded', function() {
    // Initialize page
    initPage();
    
    // Bind event listeners
    bindEventListeners();
});

function initPage() {
    // Initialize features based on current page
    const currentPath = window.location.pathname;
    
    if (currentPath.includes('/generate')) {
        initGeneratePage();
    } else if (currentPath.includes('/review')) {
        initReviewPage();
    } else if (currentPath.includes('/knowledge')) {
        initKnowledgePage();
    }
}

function bindEventListeners() {
    // General event listeners
    
    // Validate before form submission
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
    
    // Show/hide elements
    const toggleButtons = document.querySelectorAll('[data-toggle]');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-toggle');
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                if (targetElement.style.display === 'none') {
                    targetElement.style.display = 'block';
                } else {
                    targetElement.style.display = 'none';
                }
            }
        });
    });
}

// Form validation
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            field.classList.add('is-invalid');
            
            // Add error message
            let errorMessage = field.getAttribute('data-error-message') || 'This field cannot be empty';
            let errorElement = document.createElement('div');
            errorElement.className = 'invalid-feedback';
            errorElement.textContent = errorMessage;
            
            // Remove existing error message
            const existingError = field.parentNode.querySelector('.invalid-feedback');
            if (existingError) {
                existingError.remove();
            }
            
            field.parentNode.appendChild(errorElement);
        } else {
            field.classList.remove('is-invalid');
            const existingError = field.parentNode.querySelector('.invalid-feedback');
            if (existingError) {
                existingError.remove();
            }
        }
    });
    
    return isValid;
}

// Test case generator page initialization
function initGeneratePage() {
    const generateForm = document.getElementById('generate-form');
    const generateButton = document.getElementById('generate-button');
    const saveButton = document.getElementById('save-button');
    const resultContainer = document.getElementById('result-container');
    const loadingIndicator = document.getElementById('loading-indicator');
    // TODO: Overlaps with generate.js
    if (generateForm) {
        generateForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading indicator
            if (loadingIndicator) {
                loadingIndicator.style.display = 'block';
            }
            
            // Disable generate button
            if (generateButton) {
                generateButton.disabled = true;
                generateButton.innerHTML = '<span class="spinner"></span> Generating...';
            }
            
            // Get form data
            const formData = new FormData(generateForm);
            const inputType = document.querySelector('input[name="input_type"]:checked').value;
            const inputText = document.getElementById('input-text').value;
            
            // Send AJAX request
            fetch('/api/generate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    input_type: inputType,
                    input: inputText
                })
            })
            .then(response => response.json())
            .then(data => {
                // Hide loading indicator
                if (loadingIndicator) {
                    loadingIndicator.style.display = 'none';
                }
                
                // Restore generate button
                if (generateButton) {
                    generateButton.disabled = false;
                    generateButton.textContent = 'Generate Test Cases';
                }
                
                // Display results
                if (resultContainer) {
                    displayTestCases(data.test_cases, resultContainer);
                    
                    // Enable save button
                    if (saveButton) {
                        saveButton.disabled = false;
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                
                // Hide loading indicator
                if (loadingIndicator) {
                    loadingIndicator.style.display = 'none';
                }
                
                // Restore generate button
                if (generateButton) {
                    generateButton.disabled = false;
                    generateButton.textContent = 'Generate Test Cases';
                }
                
                // Display error message
                if (resultContainer) {
                    resultContainer.innerHTML = `<div class="alert alert-danger">Error generating test cases: ${error.message}</div>`;
                }
            });
        });
    }
    
    // Save test cases
    if (saveButton) {
        saveButton.addEventListener('click', function() {
            const testCases = collectTestCasesFromUI();
            const inputType = document.querySelector('input[name="input_type"]:checked').value;
            const inputText = document.getElementById('input-text').value;
            
            fetch('/test_case_generator-drop/save-test-case/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    test_cases: testCases,
                    requirements: inputType === 'requirements' ? inputText : '',
                    code_snippet: inputType === 'code' ? inputText : ''
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Test cases saved successfully', 'success');
                } else {
                    showNotification('Failed to save test cases: ' + data.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Failed to save test cases: ' + error.message, 'danger');
            });
        });
    }
}

// Test case review page initialization
function initReviewPage() {
    const reviewButtons = document.querySelectorAll('.review-button');
    const statusButtons = document.querySelectorAll('.status-button');
    
    // Review button click event
    reviewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const testCaseId = this.getAttribute('data-id');
            
            // Show loading indicator
            this.innerHTML = '<span class="spinner"></span> Reviewing...';
            this.disabled = true;
            
            fetch('/api/review/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    test_case_id: [testCaseId]
                })
            })
            .then(response => response.json())
            .then(data => {
                // Restore button state
                this.textContent = 'Review';
                this.disabled = false;
                
                // Display review results
                if (data.success) {
                    displayReviewResults(data.review_results, testCaseId);
                } else {
                    showNotification('Review failed: ' + data.errors.join(', '), 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                
                // Restore button state
                this.textContent = 'Review';
                this.disabled = false;
                
                showNotification('Review failed: ' + error.message, 'danger');
            });
        });
    });
    
    // Status update button click event
    statusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const testCaseId = this.getAttribute('data-id');
            const status = this.getAttribute('data-status');
            const commentsElement = document.getElementById(`comments-${testCaseId}`);
            const comments = commentsElement ? commentsElement.value : '';
            
            fetch('/api/update-status/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    test_case_id: testCaseId,
                    status: status,
                    comments: comments
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Status updated successfully', 'success');
                    
                    // Update UI
                    updateTestCaseStatus(testCaseId, status);
                } else {
                    showNotification('Failed to update status: ' + data.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Failed to update status: ' + error.message, 'danger');
            });
        });
    });
}

// Knowledge base page initialization
function initKnowledgePage() {
    const addKnowledgeForm = document.getElementById('add-knowledge-form');
    
    if (addKnowledgeForm) {
        addKnowledgeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const title = document.getElementById('knowledge-title').value;
            const content = document.getElementById('knowledge-content').value;
            
            fetch('/api/add-knowledge/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    title: title,
                    content: content
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Knowledge entry added successfully', 'success');
                    
                    // Clear form
                    document.getElementById('knowledge-title').value = '';
                    document.getElementById('knowledge-content').value = '';
                    
                    // Refresh knowledge list
                    loadKnowledgeList();
                } else {
                    showNotification('Failed to add knowledge entry: ' + data.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Failed to add knowledge entry: ' + error.message, 'danger');
            });
        });
    }
    
    // Initial load of knowledge list
    loadKnowledgeList();
}

// Helper functions

// Display test cases
function displayTestCases(testCases, container) {
    if (!testCases || testCases.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No test cases generated</div>';
        return;
    }
    
    let html = '<div class="test-cases-container">';
    
    testCases.forEach((testCase, index) => {
        html += `
            <div class="test-case-item" data-index="${index}">
                <h3>${testCase.title}</h3>
                <p>${testCase.description}</p>
                <div class="form-group">
                    <label>Test Steps:</label>
                    <div class="test-steps">${testCase.test_steps}</div>
                </div>
                <div class="form-group">
                    <label>Expected Results:</label>
                    <div class="expected-results">${testCase.expected_results}</div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Collect test cases data from UI
function collectTestCasesFromUI() {
    const testCases = [];
    const testCaseItems = document.querySelectorAll('.test-case-item');
    
    testCaseItems.forEach(item => {
        const title = item.querySelector('h3').textContent;
        const description = item.querySelector('p').textContent;
        const testSteps = item.querySelector('.test-steps').innerHTML;
        const expectedResults = item.querySelector('.expected-results').innerHTML;
        
        testCases.push({
            title: title,
            description: description,
            test_steps: testSteps,
            expected_results: expectedResults
        });
    });
    
    return testCases;
}

// Display review results
function displayReviewResults(reviewResults, testCaseId) {
    const resultContainer = document.getElementById(`review-result-${testCaseId}`);
    if (!resultContainer) return;
    
    const review = reviewResults.find(r => r.test_case_index.toString() === testCaseId);
    if (!review) {
        resultContainer.innerHTML = '<div class="alert alert-warning">No review results found</div>';
        return;
    }
    
    let statusBadge = '';
    if (review.status === 'approved') {
        statusBadge = '<span class="badge badge-success">Approved</span>';
    } else {
        statusBadge = '<span class="badge badge-danger">Rejected</span>';
    }
    
    let html = `
        <div class="card mt-3">
            <div class="card-header">
                Review Result ${statusBadge}
            </div>
            <div class="card-body">
                <h5>Review Comments:</h5>
                <p>${review.comments}</p>
                
                <h5>Suggestions:</h5>
                <p>${review.suggestions}</p>
                
                <div class="form-group mt-3">
                    <label for="comments-${testCaseId}">Add Review Notes:</label>
                    <textarea id="comments-${testCaseId}" class="form-control" rows="3"></textarea>
                </div>
                
                <div class="text-right">
                    <button class="btn btn-success status-button" data-id="${testCaseId}" data-status="approved">
                        Mark as Approved
                    </button>
                    <button class="btn btn-danger status-button" data-id="${testCaseId}" data-status="rejected">
                        Mark as Rejected
                    </button>
                </div>
            </div>
        </div>
    `;
    
    resultContainer.innerHTML = html;
    
    // Rebind status button events
    const statusButtons = resultContainer.querySelectorAll('.status-button');
    statusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const testCaseId = this.getAttribute('data-id');
            const status = this.getAttribute('data-status');
            const commentsElement = document.getElementById(`comments-${testCaseId}`);
            const comments = commentsElement ? commentsElement.value : '';
            
            updateTestCaseStatus(testCaseId, status, comments);
        });
    });
}

// Update test case status
function updateTestCaseStatus(testCaseId, status, comments = '') {
    fetch('/api/update-status/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            test_case_id: testCaseId,
            status: status,
            comments: comments
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Status updated successfully', 'success');
            
            // Update UI
            const testCaseElement = document.getElementById(`test-case-${testCaseId}`);
            if (testCaseElement) {
                // Remove all status classes
                testCaseElement.classList.remove('pending', 'approved', 'rejected');
                
                // Add new status class
                if (status === 'approved') {
                    testCaseElement.classList.add('approved');
                } else if (status === 'rejected') {
                    testCaseElement.classList.add('rejected');
                } else {
                    testCaseElement.classList.add('pending');
                }
                
                // Update status badge
                const statusBadge = testCaseElement.querySelector('.status-badge');
                if (statusBadge) {
                    statusBadge.className = 'badge status-badge';
                    if (status === 'approved') {
                        statusBadge.classList.add('badge-success');
                        statusBadge.textContent = 'Approved';
                    } else if (status === 'rejected') {
                        statusBadge.classList.add('badge-danger');
                        statusBadge.textContent = 'Rejected';
                    } else {
                        statusBadge.classList.add('badge-warning');
                        statusBadge.textContent = 'Pending Review';
                    }
                }
            }
        } else {
            showNotification('Failed to update status: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Failed to update status: ' + error.message, 'danger');
    });
}

// Load knowledge base list
function loadKnowledgeList() {
    const knowledgeListContainer = document.getElementById('knowledge-list');
    if (!knowledgeListContainer) return;
    
    fetch('/api/knowledge-list/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayKnowledgeList(data.knowledge_items, knowledgeListContainer);
            } else {
                knowledgeListContainer.innerHTML = `<div class="alert alert-danger">Failed to load knowledge base: ${data.message}</div>`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            knowledgeListContainer.innerHTML = `<div class="alert alert-danger">Failed to load knowledge base: ${error.message}</div>`;
        });
}

// Display knowledge base list
function displayKnowledgeList(knowledgeItems, container) {
    if (!knowledgeItems || knowledgeItems.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No entries in knowledge base</div>';
        return;
    }
    
    let html = '<div class="list-group">';
    
    knowledgeItems.forEach(item => {
        html += `
            <div class="list-group-item">
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1">${item.title}</h5>
                    <small>ID: ${item.id}</small>
                </div>
                <p class="mb-1">${item.content.substring(0, 150)}${item.content.length > 150 ? '...' : ''}</p>
                <small>Created At: ${new Date(item.created_at).toLocaleString()}</small>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Display notification
function showNotification(message, type = 'info') {
    const notificationContainer = document.getElementById('notification-container');
    if (!notificationContainer) {
        // Create notification container
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '1000';
        document.body.appendChild(container);
    }
    
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.style.marginBottom = '10px';
    notification.innerHTML = message;
    
    // Add close button
    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = 'close';
    closeButton.innerHTML = '&times;';
    closeButton.addEventListener('click', function() {
        notification.remove();
    });
    
    notification.appendChild(closeButton);
    
    // Append to container
    document.getElementById('notification-container').appendChild(notification);
    
    // Auto close
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Get CSRF token
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

// Initialize tab switching
document.addEventListener('DOMContentLoaded', function() {
    const tabLinks = document.querySelectorAll('.nav-tabs .nav-link');
    
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove all active states
            tabLinks.forEach(l => l.classList.remove('active'));
            const tabContents = document.querySelectorAll('.tab-pane');
            tabContents.forEach(c => {
                c.classList.remove('show', 'active');
            });
            
            // Set current tab to active
            this.classList.add('active');
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.classList.add('show', 'active');
            }
        });
    });
}); 