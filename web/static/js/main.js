/**
 * Main JavaScript for Serper web UI
 */

// DOM elements
const serverStatusElement = document.getElementById('status-indicator');
const apiPortElement = document.getElementById('api-port');

// Task handling
function handleTaskClick(taskId) {
    // Show task details in modal
    const modal = new bootstrap.Modal(document.getElementById('taskProgressModal'));
    
    // Set task ID in modal
    document.getElementById('modal-task-id').textContent = taskId;
    
    // Fetch task details
    fetch(`/api/tasks/${taskId}`)
        .then(response => response.json())
        .then(data => {
            // Update modal content
            document.getElementById('modal-task-type').textContent = data.type;
            document.getElementById('modal-task-status').textContent = data.status;
            document.getElementById('modal-task-started').textContent = data.created_at;
            
            // Update progress bar
            const progressBar = document.getElementById('modal-task-progress-bar');
            progressBar.style.width = `${data.progress}%`;
            progressBar.textContent = `${data.progress}%`;
            progressBar.setAttribute('aria-valuenow', data.progress);
            
            // Set task log
            document.getElementById('modal-task-log').textContent = data.log || 'No log available';
            
            // Show modal
            modal.show();
        })
        .catch(error => {
            console.error('Error fetching task details:', error);
        });
}

// Cancel task
function cancelTask(taskId) {
    if (confirm('Are you sure you want to cancel this task?')) {
        fetch(`/api/tasks/${taskId}/cancel`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('taskProgressModal'));
                if (modal) {
                    modal.hide();
                }
                
                // Refresh task list if on tasks page
                if (window.location.pathname === '/tasks') {
                    window.location.reload();
                }
            } else {
                alert('Failed to cancel task: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error cancelling task:', error);
            alert('Error cancelling task');
        });
    }
}

// Initialize event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize server status updater
    if (serverStatusElement) {
        fetch('/status')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'running') {
                    serverStatusElement.textContent = 'Running';
                    serverStatusElement.classList.remove('bg-danger');
                    serverStatusElement.classList.add('bg-success');
                } else {
                    serverStatusElement.textContent = 'Stopped';
                    serverStatusElement.classList.remove('bg-success');
                    serverStatusElement.classList.add('bg-danger');
                }
                
                // Update port
                if (apiPortElement) {
                    apiPortElement.textContent = data.port;
                }
            })
            .catch(error => {
                console.error('Error fetching server status:', error);
                serverStatusElement.textContent = 'Unknown';
                serverStatusElement.classList.remove('bg-success');
                serverStatusElement.classList.add('bg-warning');
            });
    }
    
    // Task modal cancel button
    const modalCancelTaskButton = document.getElementById('modal-cancel-task');
    if (modalCancelTaskButton) {
        modalCancelTaskButton.addEventListener('click', function() {
            const taskId = document.getElementById('modal-task-id').textContent;
            cancelTask(taskId);
        });
    }
    
    // Task list items
    const taskItems = document.querySelectorAll('.task-item');
    if (taskItems) {
        taskItems.forEach(item => {
            item.addEventListener('click', function() {
                const taskId = this.getAttribute('data-task-id');
                handleTaskClick(taskId);
            });
        });
    }
});