// Test case review script

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

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    // Get all review buttons
    const reviewButtons = document.querySelectorAll('.review-button');
    
    // Get CSRF Token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Add click event listener to each review button
    reviewButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault(); // Prevent default behavior
            
            // Get test case ID
            const testCaseId = this.getAttribute('data-id');
            
            // Validate test case ID exists
            if (!testCaseId) {
                alert('Error: Test case ID not found');
                return;
            }
            
            // Open detail review page in a new window
            window.open(`/test_case_reviewer/case-review-detail/?id=${testCaseId}`, 'TestCaseReview', 
                'width=800,height=600,scrollbars=yes,resizable=yes');
        });
    });
    
    // Get all status update buttons
    const statusButtons = document.querySelectorAll('.status-button');
    
    // Add click event to each status update button
    statusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const testCaseId = this.getAttribute('data-id');
            const status = this.getAttribute('data-status');
            const commentsElement = document.getElementById(`review-comments-${testCaseId}`);
            const comments = commentsElement ? commentsElement.value.trim() : '';
            
            if (status === 'rejected' && !comments) {
                showNotification('Review comments are required when rejecting a test case', 'error');
                return;
            }
            
            // Disable button
            this.disabled = true;
            
            // Send request to backend
            fetch('/api/update-status/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    test_case_id: testCaseId,
                    status: status,
                    comments: comments
                })
            })
            .then(response => response.json())
            .then(data => {
                this.disabled = false;
                
                if (data.success) {
                    showNotification('Test case status updated successfully', 'success');
                    
                    // Update UI
                    const testCaseItem = document.getElementById(`test-case-${testCaseId}`);
                    if (testCaseItem) {
                        // Remove old status class
                        testCaseItem.classList.remove('pending', 'approved', 'rejected');
                        
                        // Add new status class
                        testCaseItem.classList.add(status);
                        
                        // Update status badge
                        const statusBadge = testCaseItem.querySelector('.status-badge');
                        if (statusBadge) {
                            statusBadge.textContent = status === 'approved' ? 'Approved' : 'Rejected';
                            statusBadge.classList.remove('badge-warning', 'badge-success', 'badge-danger');
                            statusBadge.classList.add(
                                status === 'approved' ? 'badge-success' : 'badge-danger'
                            );
                        }
                        
                        // If on pending tab, remove from view and update tab counts
                        if (document.querySelector('#pending-tab.active')) {
                            setTimeout(() => {
                                testCaseItem.remove();
                                
                                // Check if any pending test cases remain
                                const pendingItems = document.querySelectorAll('#pending .test-case-item');
                                if (pendingItems.length === 0) {
                                    document.querySelector('#pending').innerHTML = 
                                        '<div class="alert alert-info">No test cases pending review</div>';
                                }
                                
                                // Update counts
                                updateTabCounts();
                            }, 500);
                        }
                    }
                } else {
                    showNotification(data.message || 'Failed to update test case status', 'error');
                }
            })
            .catch(error => {
                this.disabled = false;
                showNotification('Request failed: ' + error.message, 'error');
            });
        });
    });
    
    // Show notification
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
    
    // Update tab counts
    function updateTabCounts() {
        const pendingCount = document.querySelectorAll('#pending .test-case-item').length;
        const approvedCount = document.querySelectorAll('#approved .test-case-item').length;
        const rejectedCount = document.querySelectorAll('#rejected .test-case-item').length;
        
        document.querySelector('#pending-tab .badge').textContent = pendingCount;
        document.querySelector('#approved-tab .badge').textContent = approvedCount;
        document.querySelector('#rejected-tab .badge').textContent = rejectedCount;
    }

    // Pagination click event handler
    document.querySelectorAll('.pagination .page-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const pageType = this.getAttribute('data-page-type');
            const url = new URL(this.href);
            const page = url.searchParams.get(`${pageType}_page`);
            
            // Keep active tab state
            const currentTab = document.querySelector('.nav-tabs .nav-link.active');
            if (currentTab) {
                url.searchParams.set('active_tab', currentTab.getAttribute('href').substring(1));
            }
            
            // Navigate to new URL
            window.location.href = url.toString();
        });
    });
});