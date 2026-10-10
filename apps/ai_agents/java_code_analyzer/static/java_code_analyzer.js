// Java code analyzer page script

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('javaCodeAnalysisForm');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorMessage = document.getElementById('errorMessage');
    const successMessage = document.getElementById('successMessage');
    
    // Hide all status messages
    function hideAllMessages() {
        loadingIndicator.style.display = 'none';
        errorMessage.style.display = 'none';
        successMessage.style.display = 'none';
    }
    
    // Show loading state
    function showLoading() {
        hideAllMessages();
        loadingIndicator.style.display = 'block';
    }
    
    // Show error message
    function showError(message) {
        hideAllMessages();
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }
    
    function clearSuccessMessage() {
        while (successMessage.firstChild) {
            successMessage.removeChild(successMessage.firstChild);
        }
    }

    function showSuccessWithDownload(message, downloadUrl, filename) {
        // Hide only loading/error, not resultContainer
        loadingIndicator.style.display = 'none';
        errorMessage.style.display = 'none';

        clearSuccessMessage();
        successMessage.appendChild(document.createTextNode(message));

        if (downloadUrl && filename) {
            successMessage.appendChild(document.createElement('br'));
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.textContent = filename;
            link.target = '_blank';
            link.rel = 'noopener';
            successMessage.appendChild(link);
        }

        successMessage.style.display = 'block';
    }
    
    // Form submit event handler
    form.addEventListener('submit', async function(e) {
        e.preventDefault(); // Prevent default form submit
        
        // Get form data
        const targetService = document.getElementById('targetService').value;
        const baseCommit = document.getElementById('baseCommit').value;
        const newCommit = document.getElementById('newCommit').value;
        const llmProvider = document.getElementById('llmProvider').value;
        
        // Validate inputs
        if (!targetService || !baseCommit || !newCommit) {
            showError('Please fill in all required fields');
            return;
        }
        
        // Disable button to prevent duplicate submissions
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Analyzing...';
        
        try {
            showLoading();
            
            // Send analysis request
            const response = await fetch('/java_code_analyzer/api/java-code-analyzer-service/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') // Get CSRF token
                },
                body: JSON.stringify({
                    project_id: targetService,
                    base_commit: baseCommit,
                    new_commit: newCommit,
                    llm_provider: llmProvider
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success) {
                    // Success: display success message and download link
                    loadingIndicator.style.display = 'none';
                    errorMessage.style.display = 'none';

                    showSuccessWithDownload(
                        'Java source code analysis report generated successfully. Click link below to download:',
                        data.report_download_url,
                        data.report_filename
                    );
                } else {
                    showError(data.error || 'Analysis failed');
                }
            } else {
                const errorData = await response.json();
                showError(errorData.error || 'Request failed');
            }
        } catch (error) {
            console.error('Analysis request failed:', error);
            showError('Network error or server unavailable: ' + error.message);
        } finally {
            // Restore button state
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Start Analysis';
        }
    });
    
    // Helper function to get CSRF token
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
    
    // Target service change event handler
    document.getElementById('targetService').addEventListener('change', function() {
        const selectedValue = this.value;
        if (selectedValue === 'custom') {
            console.log('User selected custom service');
        }
    });
    
    // Initialize page state
    hideAllMessages();
});