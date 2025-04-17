"""Integration tests for the Web UI and WebSocket functionality."""

import pytest
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from api.server import app, start_server_with_ui
from config.credentials_manager import CredentialsManager
from web.chat_handler import ChatHandler


@pytest.fixture
def test_client():
    """Create a test client for testing the API endpoints."""
    return TestClient(app)


@pytest.fixture
def mock_websocket_server():
    """Mock the WebSocket server for testing."""
    with patch('api.server.chat_handler') as mock_chat_handler:
        mock_chat_handler.connect = AsyncMock()
        mock_chat_handler.process_message = AsyncMock()
        mock_chat_handler.disconnect = AsyncMock()
        yield mock_chat_handler


class TestWebUIIntegration:
    """Integration tests for the Web UI."""
    
    def test_start_server_with_ui(self):
        """Test starting the server with UI enabled."""
        with patch('api.server.threading.Thread') as mock_thread:
            # Mock the run_server function
            mock_thread.return_value.daemon = False
            
            # Call the start_server_with_ui function
            result = start_server_with_ui(api_key='test_key', port=8080)
            
            # Check if the Thread was started
            mock_thread.assert_called_once()
            
            # Check the result
            assert result is not None
            assert result['status'] == 'running'
            assert result['port'] == 8080
            assert result['web_ui'] is True
            assert 'web_ui_url' in result
            assert 'chat_url' in result
    
    def test_navigation_flow(self, test_client):
        """Test the navigation flow between different pages."""
        # Mock the necessary services
        with patch('api.server.CredentialsManager') as mock_creds, \
             patch('api.server.TaskTracker') as mock_tracker, \
             patch('api.server.is_server_running', return_value=True), \
             patch('api.server.GitHubClient') as mock_github, \
             patch('api.server.GraphStore') as mock_graph:
            
            # Configure mocks
            mock_creds.return_value.get_huggingface_credentials.return_value = ('test_user', 'test_token')
            mock_creds.return_value.get_server_port.return_value = 8080
            mock_creds.return_value.get_temp_dir.return_value = '/tmp/serper'
            
            mock_tracker.return_value.list_resumable_tasks.return_value = []
            mock_tracker.return_value.get_cache_size.return_value = 50
            
            mock_github.return_value.verify_credentials.return_value = True
            mock_graph.return_value.test_connection.return_value = True
            
            # Test dashboard page
            dashboard_response = test_client.get("/")
            assert dashboard_response.status_code == 200
            assert "Serper Dashboard" in dashboard_response.text
            
            # Test chat page
            chat_response = test_client.get("/chat")
            assert chat_response.status_code == 200
            assert "Chat Interface" in chat_response.text
            
            # Test configuration page
            config_response = test_client.get("/configuration")
            assert config_response.status_code == 200
            assert "Configuration" in config_response.text


@pytest.mark.asyncio
class TestWebSocketIntegration:
    """Integration tests for the WebSocket functionality."""
    
    async def test_websocket_message_flow(self, mock_websocket_server):
        """Test the flow of messages through the WebSocket."""
        # Create a test client with WebSocket support
        client = TestClient(app)
        
        # Initialize a real ChatHandler for this test
        with patch('api.server.ChatHandler', return_value=mock_websocket_server):
            # Connect to the WebSocket endpoint
            with client.websocket_connect("/ws") as websocket:
                # Test the connection
                assert mock_websocket_server.connect.called
                
                # Send a message
                websocket.send_text("Create a dataset from GitHub repository langchain-ai/langchain")
                
                # Check if the process_message method was called
                mock_websocket_server.process_message.assert_called_once()
                args = mock_websocket_server.process_message.call_args.args
                assert args[0] == "Create a dataset from GitHub repository langchain-ai/langchain"
    
    async def test_chat_handler_dataset_creation(self):
        """Test the dataset creation flow in the ChatHandler."""
        # Create a real ChatHandler instance
        with patch('config.credentials_manager.CredentialsManager') as mock_creds:
            # Mock the necessary components
            mock_creds.return_value.get_huggingface_credentials.return_value = ('test_user', 'test_token')
            mock_creds.return_value.get_openai_key.return_value = 'test_key'
            
            # Create the ChatHandler
            chat_handler = ChatHandler(mock_creds.return_value)
            
            # Mock the LLM client
            chat_handler.llm_client = MagicMock()
            chat_handler._classify_intent = AsyncMock(return_value={
                'type': 'dataset_creation',
                'parameters': {
                    'source_type': 'github',
                    'repository_url': 'https://github.com/langchain-ai/langchain',
                    'dataset_name': 'langchain-sdk'
                }
            })
            
            # Mock the necessary methods
            chat_handler.handle_github_dataset_creation = AsyncMock()
            
            # Create a mock WebSocket
            mock_websocket = AsyncMock()
            
            # Process a message
            await chat_handler.process_message("Create a dataset from GitHub repository langchain-ai/langchain", mock_websocket)
            
            # Check that the right methods were called
            chat_handler._classify_intent.assert_called_once()
            chat_handler.handle_github_dataset_creation.assert_called_once()
    
    async def test_github_dataset_creation_task_flow(self):
        """Test the full flow of creating a GitHub dataset via the chat interface."""
        # Create mocks for all the necessary components
        mock_creds = MagicMock()
        mock_creds.get_huggingface_credentials.return_value = ('test_user', 'test_token')
        
        mock_task_tracker = MagicMock()
        mock_task_tracker.create_task.return_value = 'test_task_id'
        
        mock_content_fetcher = MagicMock()
        mock_content_fetcher.fetch_single_repository.return_value = [{'path': 'file1.md', 'content': 'content'}]
        
        mock_dataset_creator = MagicMock()
        mock_dataset_creator.create_and_push_dataset.return_value = (True, 'Success')
        
        # Create the ChatHandler with mocked dependencies
        with patch('web.chat_handler.ContentFetcher', return_value=mock_content_fetcher), \
             patch('web.chat_handler.DatasetCreator', return_value=mock_dataset_creator), \
             patch('web.chat_handler.TaskTracker', return_value=mock_task_tracker):
            
            chat_handler = ChatHandler(mock_creds)
            
            # Mock WebSocket
            mock_websocket = AsyncMock()
            
            # Call the handler method directly
            await chat_handler._create_github_dataset(
                mock_content_fetcher,
                mock_dataset_creator,
                'https://github.com/langchain-ai/langchain',
                'langchain-sdk',
                AsyncMock(),  # progress_callback
                'test_task_id',
                'Create a dataset from GitHub repository langchain-ai/langchain',
                mock_websocket
            )
            
            # Check that the task was completed successfully
            mock_task_tracker.complete_task.assert_called_once_with('test_task_id', success=True)
            
            # Check that the dataset was created
            mock_dataset_creator.create_and_push_dataset.assert_called_once()
            
            # Check that a success message was sent to the WebSocket
            mock_websocket.send_text.assert_called()
            
            # Get the last message sent
            last_call = mock_websocket.send_text.call_args_list[-1]
            message = json.loads(last_call.args[0])
            
            # Check the message type and content
            assert message['type'] == 'assistant'
            assert 'Successfully created dataset' in message['content']