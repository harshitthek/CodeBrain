// Knowledge base management page script

document.addEventListener('DOMContentLoaded', function() {
    const addKnowledgeForm = document.getElementById('add-knowledge-form');
    const knowledgeList = document.getElementById('knowledge-list');
    const searchInput = document.getElementById('knowledge-search');
    
    // Load knowledge base list
    loadKnowledgeList();
    
    // Add knowledge entry
    if (addKnowledgeForm) {
        addKnowledgeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const titleInput = document.getElementById('knowledge-title');
            const contentInput = document.getElementById('knowledge-content');
            
            const title = titleInput.value.trim();
            const content = contentInput.value.trim();
            
            if (!title) {
                showNotification('Please enter knowledge entry title', 'error');
                return;
            }
            
            if (!content) {
                showNotification('Please enter knowledge entry content', 'error');
                return;
            }
            
            // Disable submit button
            const submitButton = this.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.textContent = 'Adding...';
            
            // Send request to backend
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
                submitButton.disabled = false;
                submitButton.textContent = 'Add Knowledge Entry';
                
                if (data.success) {
                    showNotification('Knowledge entry added successfully', 'success');
                    
                    // Clear form
                    titleInput.value = '';
                    contentInput.value = '';
                    
                    // Reload knowledge base list
                    loadKnowledgeList();
                } else {
                    showNotification(data.message || 'Failed to add knowledge entry', 'error');
                }
            })
            .catch(error => {
                submitButton.disabled = false;
                submitButton.textContent = 'Add Knowledge Entry';
                showNotification('Request failed: ' + error.message, 'error');
            });
        });
    }
    
    // Search knowledge base
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const knowledgeItems = document.querySelectorAll('.list-group-item');
            
            knowledgeItems.forEach(item => {
                const title = item.querySelector('h5').textContent.toLowerCase();
                const content = item.querySelector('p').textContent.toLowerCase();
                
                if (title.includes(searchTerm) || content.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
    
    // Load knowledge base list
    function loadKnowledgeList() {
        if (!knowledgeList) return;
        
        knowledgeList.innerHTML = `
            <div class="text-center">
                <div class="spinner"></div>
                <p>Loading knowledge base...</p>
            </div>
        `;
        
        fetch('/api/knowledge-list/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayKnowledgeList(data.knowledge_items);
                } else {
                    knowledgeList.innerHTML = `<div class="alert alert-danger">${data.message || 'Failed to load knowledge base'}</div>`;
                }
            })
            .catch(error => {
                knowledgeList.innerHTML = `<div class="alert alert-danger">Request failed: ${error.message}</div>`;
            });
    }
    
    // Display knowledge base list
    function displayKnowledgeList(items) {
        if (!items || !items.length) {
            knowledgeList.innerHTML = '<div class="alert alert-info">Knowledge base is empty</div>';
            return;
        }
        
        let html = '<div class="list-group">';
        
        items.forEach(item => {
            const date = new Date(item.created_at);
            const formattedDate = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
            
            html += `
                <div class="list-group-item">
                    <div class="d-flex justify-content-between">
                        <h5>${item.title}</h5>
                        <small>${formattedDate}</small>
                    </div>
                    <p>${item.content}</p>
                </div>
            `;
        });
        
        html += '</div>';
        knowledgeList.innerHTML = html;
    }
    
    // Display notification
    function showNotification(message, type = 'info') {
        // Use container if present
        let container = document.getElementById('notification-container');
        
        // Create container if absent
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.style.position = 'fixed';
            container.style.top = '20px';
            container.style.right = '20px';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        `;
        
        // Append to container
        container.appendChild(notification);
        
        // Set auto close
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
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