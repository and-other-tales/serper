/**
 * Chat Interface JavaScript
 * Handles WebSocket communication and UI interactions for the chat interface
 */

// Global variables
let socket = null;
let reconnectAttempts = 0;
let maxReconnectAttempts = 5;
let reconnectInterval = 2000; // ms
let taskProgressPopup = null;
let activeTaskId = null;

/**
 * Initialize WebSocket connection
 * @param {string} websocketUrl - The WebSocket URL to connect to
 */
function initChatWebSocket(websocketUrl) {
    console.log('Initializing WebSocket connection to:', websocketUrl);
    
    // Get DOM elements
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const connectionStatus = document.getElementById('connection-status');
    const clearChatButton = document.getElementById('clear-chat-button');
    
    // Initialize task progress popup
    taskProgressPopup = document.getElementById('task-progress-popup');
    
    // Create WebSocket connection
    socket = new WebSocket(websocketUrl);
    
    // Connection opened
    socket.addEventListener('open', (event) => {
        console.log('Connected to WebSocket');
        connectionStatus.textContent = 'Connected';
        connectionStatus.classList.remove('bg-danger');
        connectionStatus.classList.add('bg-success');
        reconnectAttempts = 0;
    });
    
    // Connection closed
    socket.addEventListener('close', (event) => {
        console.log('Disconnected from WebSocket');
        connectionStatus.textContent = 'Disconnected';
        connectionStatus.classList.remove('bg-success');
        connectionStatus.classList.add('bg-danger');
        
        // Attempt to reconnect
        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            connectionStatus.textContent = `Reconnecting (${reconnectAttempts}/${maxReconnectAttempts})...`;
            setTimeout(() => {
                initChatWebSocket(websocketUrl);
            }, reconnectInterval);
        }
    });
    
    // Connection error
    socket.addEventListener('error', (event) => {
        console.error('WebSocket error:', event);
        connectionStatus.textContent = 'Error';
        connectionStatus.classList.remove('bg-success');
        connectionStatus.classList.add('bg-danger');
    });
    
    // Listen for messages
    socket.addEventListener('message', (event) => {
        console.log('Message from server:', event.data);
        const message = JSON.parse(event.data);
        
        if (message.type === 'system' || message.type === 'assistant' || 
            message.type === 'error' || message.type === 'thinking') {
            // Handle chat messages
            appendMessage(message.type, message.content);
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } else if (message.type === 'status') {
            // Handle status updates
            handleStatusUpdate(message.content);
        } else if (message.type === 'task_update') {
            // Handle task updates
            handleTaskUpdate(message);
        }
    });
    
    // Handle form submission
    chatForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const message = messageInput.value.trim();
        
        if (message && socket.readyState === WebSocket.OPEN) {
            // Send message to server
            socket.send(message);
            
            // Add message to chat
            appendMessage('user', message);
            
            // Clear input
            messageInput.value = '';
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    });
    
    // Handle example commands
    const exampleCommands = document.querySelectorAll('.example-command');
    exampleCommands.forEach(command => {
        command.addEventListener('click', (event) => {
            event.preventDefault();
            const commandText = command.textContent;
            
            // Set input value
            messageInput.value = commandText;
            
            // Focus input
            messageInput.focus();
        });
    });
    
    // Handle clear chat button
    if (clearChatButton) {
        clearChatButton.addEventListener('click', () => {
            // Keep only system welcome message
            const welcomeMessage = chatMessages.querySelector('.system-message');
            chatMessages.innerHTML = '';
            if (welcomeMessage) {
                chatMessages.appendChild(welcomeMessage);
            }
        });
    }
    
    // Handle task progress popup
    if (taskProgressPopup) {
        const minimizeButton = document.getElementById('minimize-task');
        const cancelButton = document.getElementById('cancel-task');
        
        if (minimizeButton) {
            minimizeButton.addEventListener('click', () => {
                taskProgressPopup.classList.toggle('minimized');
            });
        }
        
        if (cancelButton) {
            cancelButton.addEventListener('click', () => {
                if (activeTaskId && socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({
                        type: 'cancel_task',
                        task_id: activeTaskId
                    }));
                }
                hideTaskProgressPopup();
            });
        }
    }
}

/**
 * Append a message to the chat container
 * @param {string} type - The message type (system, user, assistant, error, thinking)
 * @param {string} content - The message content
 */
function appendMessage(type, content) {
    const chatMessages = document.getElementById('chat-messages');
    
    // Create message element
    const messageElement = document.createElement('div');
    messageElement.className = `chat-message ${type}-message`;
    
    // Create bubble element
    const bubbleElement = document.createElement('div');
    bubbleElement.className = 'chat-bubble';
    
    // Format markdown content for non-user messages
    if (type !== 'user') {
        // Simple markdown-like formatting
        // In a real app, use a proper markdown parser like Marked.js
        const formattedContent = content
            // Replace ** with <strong> for bold
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Replace * with <em> for italic
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Replace backticks `` with <code> for inline code
            .replace(/`(.*?)`/g, '<code>$1</code>')
            // Replace newlines with <br>
            .replace(/\n/g, '<br>');
        
        bubbleElement.innerHTML = formattedContent;
    } else {
        // For user messages, just set text content
        bubbleElement.textContent = content;
    }
    
    // Remove previous thinking message if present and this is an assistant message
    if (type === 'assistant') {
        const thinkingMessages = chatMessages.querySelectorAll('.thinking-message');
        thinkingMessages.forEach(message => {
            message.remove();
        });
    }
    
    // Add bubble to message
    messageElement.appendChild(bubbleElement);
    
    // Add message to chat
    chatMessages.appendChild(messageElement);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Handle status update
 * @param {Object} status - The status object
 */
function handleStatusUpdate(status) {
    console.log('Status update:', status);
    
    // Update UI with status information
    // This can be customized based on the status data structure
}

/**
 * Handle task update
 * @param {Object} update - The task update object
 */
function handleTaskUpdate(update) {
    console.log('Task update:', update);
    
    // Extract task information
    const taskId = update.task_id;
    const progress = update.progress;
    const status = update.status;
    const taskType = update.task_type || 'Task';
    
    // Set active task ID
    activeTaskId = taskId;
    
    // Get task progress popup elements
    const progressBar = document.getElementById('popup-progress-bar');
    const statusMessage = document.getElementById('popup-status-message');
    const taskInfo = document.querySelector('.task-info');
    
    // Update task progress popup
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
        progressBar.textContent = `${Math.round(progress)}%`;
        progressBar.setAttribute('aria-valuenow', progress);
        
        // Change progress bar color based on progress
        if (progress < 0) {
            // Error state
            progressBar.classList.remove('bg-primary', 'bg-success');
            progressBar.classList.add('bg-danger');
        } else if (progress === 100) {
            // Complete state
            progressBar.classList.remove('bg-primary', 'bg-danger');
            progressBar.classList.add('bg-success');
        } else {
            // In progress state
            progressBar.classList.remove('bg-success', 'bg-danger');
            progressBar.classList.add('bg-primary');
        }
    }
    
    if (statusMessage) {
        statusMessage.textContent = status;
    }
    
    if (taskInfo) {
        taskInfo.textContent = `${taskType} - ${taskId}`;
    }
    
    // Show task progress popup if not already visible
    showTaskProgressPopup();
    
    // If task completed or failed, auto-hide after a delay
    if (progress === 100 || progress < 0) {
        setTimeout(() => {
            hideTaskProgressPopup();
        }, 5000);
    }
}

/**
 * Show task progress popup
 */
function showTaskProgressPopup() {
    if (taskProgressPopup) {
        taskProgressPopup.classList.add('visible');
        if (taskProgressPopup.classList.contains('minimized')) {
            taskProgressPopup.classList.remove('minimized');
        }
    }
}

/**
 * Hide task progress popup
 */
function hideTaskProgressPopup() {
    if (taskProgressPopup) {
        taskProgressPopup.classList.remove('visible');
        activeTaskId = null;
    }
}

// Prevent displaying WebSocket errors in production
window.addEventListener('error', (event) => {
    if (event.message.includes('WebSocket')) {
        console.warn('WebSocket error:', event.message);
        event.preventDefault();
    }
});