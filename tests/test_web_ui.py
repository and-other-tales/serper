"""Unit tests for web UI functionality."""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from api.server import app, templates
from web.chat_handler import ChatHandler
from config.credentials_manager import CredentialsManager


@pytest.fixture
def test_client():
    """Create a test client for testing the API endpoints."""
    return TestClient(app)


@pytest.fixture
def mock_credentials_manager():
    """Mock the credentials manager."""
    with patch('config.credentials_manager.CredentialsManager') as mock:
        credentials_manager = mock.return_value
        credentials_manager.get_huggingface_credentials.return_value = ('test_user', 'test_token')
        credentials_manager.get_openai_key.return_value = 'test_key'
        credentials_manager.get_server_port.return_value = 8080
        credentials_manager.get_temp_dir.return_value = '/tmp/serper'
        yield credentials_manager


@pytest.fixture
def mock_task_tracker():
    """Mock the task tracker."""
    with patch('utils.task_tracker.TaskTracker') as mock:
        task_tracker = mock.return_value
        task_tracker.list_resumable_tasks.return_value = [
            {
                'id': 'test_task_1',
                'type': 'github_dataset',
                'status': 'completed',
                'progress': 100,
                'description': 'Test task 1',
                'updated_ago': '5 minutes ago'
            }
        ]
        task_tracker.get_cache_size.return_value = 50  # 50 MB
        yield task_tracker


class TestWebUIRoutes:
    """Test the web UI routes."""

    def test_dashboard_route(self, test_client, mock_credentials_manager, mock_task_tracker):
        """Test the dashboard route."""
        # Mock the necessary dependencies
        with patch('api.server.CredentialsManager', return_value=mock_credentials_manager), \
             patch('api.server.TaskTracker', return_value=mock_task_tracker), \
             patch('api.server.is_server_running', return_value=True), \
             patch('api.server.GitHubClient') as mock_github, \
             patch('api.server.GraphStore') as mock_graph_store:
            
            # Configure mocks
            mock_github_client = mock_github.return_value
            mock_github_client.verify_credentials.return_value = True
            
            mock_graph = mock_graph_store.return_value
            mock_graph.test_connection.return_value = True
            
            # Test the dashboard route
            response = test_client.get("/")
            
            # Check response
            assert response.status_code == 200
            assert b"Serper Dashboard" in response.content
            assert b"System Status" in response.content
            assert b"Storage Usage" in response.content
            assert b"Recent Tasks" in response.content

    def test_chat_route(self, test_client):
        """Test the chat route."""
        # Test the chat route
        response = test_client.get("/chat")
        
        # Check response
        assert response.status_code == 200
        assert b"Chat Interface" in response.content
        assert b"websocket_url" in response.content
        assert b"Example Commands" in response.content


class TestChatHandler:
    """Test the chat handler."""

    @pytest.fixture
    def chat_handler(self, mock_credentials_manager):
        """Create a chat handler for testing."""
        return ChatHandler(mock_credentials_manager)

    @pytest.mark.asyncio
    async def test_chat_handler_connect(self, chat_handler):
        """Test the connect method."""
        # Create a mock WebSocket
        mock_websocket = AsyncMock()
        
        # Call the connect method
        await chat_handler.connect(mock_websocket, 'test_client')
        
        # Check if the WebSocket accept method was called
        mock_websocket.accept.assert_called_once()
        
        # Check if the WebSocket send_text method was called with a welcome message
        assert any('Welcome to Serper' in call.args[0] 
                   for call in mock_websocket.send_text.call_args_list 
                   if isinstance(call.args[0], str) and 'type' in json.loads(call.args[0]) 
                   and json.loads(call.args[0])['type'] == 'system')
        
        # Check if the client ID was added to the active connections
        assert 'test_client' in chat_handler.active_connections
        assert chat_handler.active_connections['test_client'] == mock_websocket

    @pytest.mark.asyncio
    async def test_chat_handler_disconnect(self, chat_handler):
        """Test the disconnect method."""
        # Setup active connections
        mock_websocket = AsyncMock()
        chat_handler.active_connections['test_client'] = mock_websocket
        
        # Call the disconnect method
        await chat_handler.disconnect('test_client')
        
        # Check if the client ID was removed from the active connections
        assert 'test_client' not in chat_handler.active_connections

    @pytest.mark.asyncio
    async def test_chat_handler_send_message(self, chat_handler):
        """Test the send_message method."""
        # Create a mock WebSocket
        mock_websocket = AsyncMock()
        
        # Call the send_message method
        await chat_handler.send_message(mock_websocket, 'assistant', 'Test message', {'test': 'data'})
        
        # Check if the WebSocket send_text method was called with the correct message
        mock_websocket.send_text.assert_called_once()
        
        # Get the message sent to the WebSocket
        message_str = mock_websocket.send_text.call_args.args[0]
        message = json.loads(message_str)
        
        # Check the message content
        assert message['type'] == 'assistant'
        assert message['content'] == 'Test message'
        assert message['metadata'] == {'test': 'data'}
        assert 'timestamp' in message

    @pytest.mark.asyncio
    async def test_process_message_with_dataset_intent(self, chat_handler):
        """Test processing a message with dataset creation intent."""
        # Create a mock WebSocket
        mock_websocket = AsyncMock()
        
        # Mock the _classify_intent method to return a dataset creation intent
        chat_handler._classify_intent = AsyncMock(return_value={
            'type': 'dataset_creation',
            'parameters': {
                'source_type': 'github',
                'repository_url': 'https://github.com/langchain-ai/langchain',
                'dataset_name': 'langchain-sdk'
            }
        })
        
        # Mock the handle_github_dataset_creation method
        chat_handler.handle_github_dataset_creation = AsyncMock()
        
        # Process a message
        await chat_handler.process_message('Create a dataset from GitHub repository langchain-ai/langchain', mock_websocket)
        
        # Check if the handle_github_dataset_creation method was called with the correct parameters
        chat_handler.handle_github_dataset_creation.assert_called_once()
        call_args = chat_handler.handle_github_dataset_creation.call_args
        assert call_args[0][0] == 'https://github.com/langchain-ai/langchain'  # repo_url
        assert call_args[0][1] == 'langchain-sdk'  # dataset_name

    @pytest.mark.asyncio
    async def test_process_message_with_keyword_fallback(self, chat_handler):
        """Test processing a message with keyword matching fallback."""
        # Create a mock WebSocket
        mock_websocket = AsyncMock()
        
        # Set LLM client to None to trigger keyword matching
        chat_handler.llm_client = None
        
        # Mock the handle_list_datasets method
        chat_handler.handle_list_datasets = AsyncMock()
        
        # Process a message
        await chat_handler.process_message('What datasets do I have?', mock_websocket)
        
        # Check if the handle_list_datasets method was called
        chat_handler.handle_list_datasets.assert_called_once_with(mock_websocket)


class TestWebSocketEndpoint:
    """Test the WebSocket endpoint."""

    @pytest.mark.asyncio
    async def test_websocket_endpoint(self):
        """Test the WebSocket endpoint."""
        # This is more of an integration test but still useful
        # Create a test client with WebSocket support
        client = TestClient(app)
        
        # Mock the ChatHandler
        with patch('api.server.ChatHandler') as mock_handler_class:
            # Create a mock chat handler instance
            mock_handler = mock_handler_class.return_value
            mock_handler.connect = AsyncMock()
            mock_handler.process_message = AsyncMock()
            mock_handler.disconnect = AsyncMock()
            
            # Test the WebSocket endpoint
            with client.websocket_connect("/ws") as websocket:
                # Send a message
                websocket.send_text("Hello")
                
                # Check if the connect method was called
                mock_handler.connect.assert_called_once()
                
                # Check if the process_message method was called with the correct message
                mock_handler.process_message.assert_called_with("Hello", websocket._websocket)