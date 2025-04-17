"""Tests for the frontend JavaScript functionality.

These tests are designed to be run with pytest-playwright to test the frontend
JavaScript functionality of the web UI.

To run these tests:
1. Install pytest-playwright: pip install pytest-playwright
2. Install browsers: playwright install
3. Run the tests: python -m pytest tests/test_web_frontend.py
"""

import pytest
import json
import asyncio
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from unittest.mock import patch, MagicMock

# Skip these tests if playwright is not installed
pytest.importorskip("playwright")


class MockWebSocketServer:
    """Mock WebSocket server for testing the frontend."""
    
    def __init__(self):
        self.clients = []
        self.messages = []
        self.server_running = False
    
    async def start(self, host='localhost', port=8081):
        """Start the mock WebSocket server."""
        import websockets
        self.server = await websockets.serve(self.handler, host, port)
        self.server_running = True
        return self.server
    
    async def stop(self):
        """Stop the mock WebSocket server."""
        if self.server_running:
            self.server.close()
            await self.server.wait_closed()
            self.server_running = False
    
    async def handler(self, websocket, path):
        """Handle WebSocket connections."""
        self.clients.append(websocket)
        
        # Send welcome message
        welcome_message = {
            "type": "system",
            "content": "Welcome to Serper. I can help you create datasets from GitHub repositories and websites.",
            "timestamp": "2023-04-17T12:00:00Z"
        }
        await websocket.send(json.dumps(welcome_message))
        
        # Handle messages
        try:
            async for message in websocket:
                self.messages.append(message)
                
                # Send a thinking message
                thinking_message = {
                    "type": "thinking",
                    "content": "Thinking...",
                    "timestamp": "2023-04-17T12:00:01Z"
                }
                await websocket.send(json.dumps(thinking_message))
                
                # Wait a bit to simulate processing
                await asyncio.sleep(0.5)
                
                # Send a response message
                if "dataset" in message.lower() and "github" in message.lower():
                    # Mock a GitHub dataset creation response
                    response_message = {
                        "type": "assistant",
                        "content": "I'm creating a dataset from GitHub. This may take a while.",
                        "timestamp": "2023-04-17T12:00:02Z"
                    }
                    await websocket.send(json.dumps(response_message))
                    
                    # Send a task update after a delay
                    await asyncio.sleep(0.5)
                    task_update = {
                        "type": "task_update",
                        "task_id": "test_task_1",
                        "progress": 0,
                        "status": "Starting task...",
                        "task_type": "github_dataset"
                    }
                    await websocket.send(json.dumps(task_update))
                    
                    # Send progress updates
                    for progress in [10, 30, 50, 70, 100]:
                        await asyncio.sleep(0.5)
                        task_update = {
                            "type": "task_update",
                            "task_id": "test_task_1",
                            "progress": progress,
                            "status": f"Progress: {progress}%",
                            "task_type": "github_dataset"
                        }
                        await websocket.send(json.dumps(task_update))
                        
                    # Send completion message
                    await asyncio.sleep(0.5)
                    completion_message = {
                        "type": "assistant",
                        "content": "Dataset created successfully!",
                        "timestamp": "2023-04-17T12:00:10Z"
                    }
                    await websocket.send(json.dumps(completion_message))
                else:
                    # Default response
                    response_message = {
                        "type": "assistant",
                        "content": f"You said: {message}",
                        "timestamp": "2023-04-17T12:00:02Z"
                    }
                    await websocket.send(json.dumps(response_message))
        except websockets.exceptions.ConnectionClosed:
            self.clients.remove(websocket)


@pytest.fixture
async def mock_ws_server():
    """Create and start a mock WebSocket server."""
    server = MockWebSocketServer()
    await server.start()
    yield server
    await server.stop()


@pytest.mark.asyncio
async def test_chat_interface_messaging(mock_ws_server):
    """Test the chat interface messaging functionality."""
    # This test starts a real browser and tests the chat interface
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        # Mock the WebSocket URL to point to our mock server
        await page.add_init_script("""
            window.WebSocket = class extends WebSocket {
                constructor(url, ...args) {
                    // Replace the WebSocket URL with our mock server
                    super('ws://localhost:8081', ...args);
                }
            };
        """)
        
        # Load the chat interface page
        # In a real test, this would be the actual page URL
        # For this test, we'll create a simple HTML page that includes the chat.js script
        await page.set_content("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Chat Test</title>
            <style>
                .chat-container {
                    height: 300px;
                    overflow-y: auto;
                    border: 1px solid #ccc;
                    padding: 1rem;
                    margin-bottom: 1rem;
                }
                .user-message { text-align: right; }
                .assistant-message, .system-message, .thinking-message { text-align: left; }
                .chat-bubble {
                    display: inline-block;
                    padding: 0.5rem 1rem;
                    border-radius: 1rem;
                    margin-bottom: 0.5rem;
                }
                .user-message .chat-bubble { background-color: #007bff; color: white; }
                .assistant-message .chat-bubble { background-color: #e9ecef; color: black; }
                .system-message .chat-bubble { background-color: #f8f9fa; color: #6c757d; }
                .thinking-message .chat-bubble { background-color: #e9ecef; color: #6c757d; }
                
                .task-progress-popup {
                    position: fixed;
                    right: 1rem;
                    bottom: 1rem;
                    width: 300px;
                    background-color: white;
                    border: 1px solid #ccc;
                    border-radius: 0.5rem;
                    padding: 1rem;
                    display: none;
                }
                .task-progress-popup.visible { display: block; }
                .task-progress-popup.minimized { height: 40px; overflow: hidden; }
            </style>
        </head>
        <body>
            <div id="chat-messages" class="chat-container"></div>
            <form id="chat-form">
                <div class="input-group">
                    <input type="text" id="message-input" class="form-control" 
                        placeholder="Ask a question or enter a command...">
                    <button type="submit">Send</button>
                </div>
            </form>
            
            <div id="task-progress-popup" class="task-progress-popup">
                <div class="task-progress-content">
                    <div class="task-header">
                        <h5>Task in Progress</h5>
                        <span class="task-info">Creating dataset...</span>
                    </div>
                    <div class="progress">
                        <div id="popup-progress-bar" style="width: 0%;">0%</div>
                    </div>
                    <div class="task-status">
                        <div id="popup-status-message">Initializing task...</div>
                    </div>
                    <div class="task-actions">
                        <button id="minimize-task">Minimize</button>
                        <button id="cancel-task">Cancel</button>
                    </div>
                </div>
            </div>
            
            <script>
                // Simplified version of chat.js for testing
                let socket = null;
                let taskProgressPopup = null;
                let activeTaskId = null;
                
                function initChatWebSocket(websocketUrl) {
                    console.log('Initializing WebSocket connection to:', websocketUrl);
                    
                    const chatMessages = document.getElementById('chat-messages');
                    const chatForm = document.getElementById('chat-form');
                    const messageInput = document.getElementById('message-input');
                    
                    taskProgressPopup = document.getElementById('task-progress-popup');
                    
                    socket = new WebSocket(websocketUrl);
                    
                    socket.addEventListener('open', (event) => {
                        console.log('Connected to WebSocket');
                    });
                    
                    socket.addEventListener('message', (event) => {
                        console.log('Message from server:', event.data);
                        const message = JSON.parse(event.data);
                        
                        if (message.type === 'system' || message.type === 'assistant' || 
                            message.type === 'error' || message.type === 'thinking') {
                            // Handle chat messages
                            appendMessage(message.type, message.content);
                            // Scroll to bottom
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        } else if (message.type === 'task_update') {
                            // Handle task updates
                            handleTaskUpdate(message);
                        }
                    });
                    
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
                
                function appendMessage(type, content) {
                    const chatMessages = document.getElementById('chat-messages');
                    
                    // Create message element
                    const messageElement = document.createElement('div');
                    messageElement.className = `chat-message ${type}-message`;
                    
                    // Create bubble element
                    const bubbleElement = document.createElement('div');
                    bubbleElement.className = 'chat-bubble';
                    
                    // Set content
                    bubbleElement.textContent = content;
                    
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
                
                function handleTaskUpdate(update) {
                    console.log('Task update:', update);
                    
                    // Extract task information
                    const taskId = update.task_id;
                    const progress = update.progress;
                    const status = update.status;
                    
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
                    }
                    
                    if (statusMessage) {
                        statusMessage.textContent = status;
                    }
                    
                    if (taskInfo) {
                        taskInfo.textContent = `${update.task_type || 'Task'} - ${taskId}`;
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
                
                function showTaskProgressPopup() {
                    if (taskProgressPopup) {
                        taskProgressPopup.classList.add('visible');
                        if (taskProgressPopup.classList.contains('minimized')) {
                            taskProgressPopup.classList.remove('minimized');
                        }
                    }
                }
                
                function hideTaskProgressPopup() {
                    if (taskProgressPopup) {
                        taskProgressPopup.classList.remove('visible');
                        activeTaskId = null;
                    }
                }
                
                // Initialize WebSocket connection on page load
                document.addEventListener('DOMContentLoaded', function() {
                    initChatWebSocket('ws://localhost:8081');
                });
            </script>
        </body>
        </html>
        """)
        
        # Wait for the WebSocket connection to be established
        await asyncio.sleep(1)
        
        # Check if the welcome message was received
        system_message = await page.locator(".system-message").first.text_content()
        assert "Welcome to Serper" in system_message
        
        # Send a message
        await page.fill("#message-input", "Create a dataset from GitHub repository langchain-ai/langchain")
        await page.click("button[type=submit]")
        
        # Wait for the response
        await asyncio.sleep(1)
        
        # Check if the user message was displayed
        user_message = await page.locator(".user-message").first.text_content()
        assert "Create a dataset from GitHub repository" in user_message
        
        # Wait for the thinking message
        await asyncio.sleep(1)
        
        # Check if the thinking message was displayed
        thinking_message = await page.locator(".thinking-message").first.text_content()
        assert "Thinking" in thinking_message
        
        # Wait for the assistant message
        await asyncio.sleep(1)
        
        # Check if the assistant message was displayed
        assistant_message = await page.locator(".assistant-message").first.text_content()
        assert "I'm creating a dataset from GitHub" in assistant_message
        
        # Wait for the task progress popup to appear
        await asyncio.sleep(1)
        
        # Check if the task progress popup is visible
        is_visible = await page.locator("#task-progress-popup").is_visible()
        assert is_visible
        
        # Wait for the task to complete
        await asyncio.sleep(3)
        
        # Check if the progress bar shows completion
        progress_bar = await page.locator("#popup-progress-bar").get_attribute("style")
        assert "width: 100%" in progress_bar
        
        # Check if the final message was displayed
        await asyncio.sleep(1)
        final_messages = await page.locator(".assistant-message").all()
        last_message = await final_messages[-1].text_content()
        assert "Dataset created successfully" in last_message
        
        # Clean up
        await browser.close()


# Integration test to be run with a real server
def test_real_web_ui_integration(xfail=True):
    """Integration test with a real server.
    
    This test requires a running server and should be run manually.
    It's marked as xfail by default.
    """
    # Skip this test unless explicitly enabled
    if xfail:
        pytest.xfail("Test requires a running server")
    
    import requests
    from requests.exceptions import ConnectionError
    
    # Try to connect to the server
    try:
        response = requests.get("http://localhost:8080")
        assert response.status_code == 200
        assert "Serper Dashboard" in response.text
        
        # Check the chat page
        chat_response = requests.get("http://localhost:8080/chat")
        assert chat_response.status_code == 200
        assert "Chat Interface" in chat_response.text
    except ConnectionError:
        pytest.fail("Failed to connect to server. Make sure it's running on port 8080.")