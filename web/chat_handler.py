"""Chat interface handler for Serper web UI."""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, Callable

from fastapi import WebSocket
from config.credentials_manager import CredentialsManager
from utils.task_tracker import TaskTracker
from huggingface.dataset_manager import DatasetManager
from web.crawler import WebCrawler
from github.content_fetcher import ContentFetcher
from huggingface.dataset_creator import DatasetCreator
from utils.llm_client import LLMClient
from knowledge_graph.graph_store import GraphStore

logger = logging.getLogger(__name__)

class ChatHandler:
    """Handler for processing chat messages and managing chat sessions."""
    
    def __init__(self, credentials_manager: CredentialsManager):
        """Initialize the chat handler with required components.
        
        Args:
            credentials_manager: Credentials manager for accessing API keys
        """
        self.credentials_manager = credentials_manager
        self.task_tracker = TaskTracker()
        
        # Initialize LLM client if credentials are available
        try:
            openai_key = self.credentials_manager.get_openai_key()
            if openai_key:
                self.llm_client = LLMClient(openai_api_key=openai_key)
            else:
                self.llm_client = None
                logger.warning("OpenAI API key not found, LLM features will be limited")
        except Exception as e:
            logger.error(f"Error initializing LLM client: {e}")
            self.llm_client = None
            
        # Initialize active connections
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Handle new websocket connection.
        
        Args:
            websocket: The websocket connection
            client_id: Unique ID for the client
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        # Send welcome message
        await self.send_message(
            websocket, 
            "system", 
            "Welcome to Serper. I can help you create datasets from GitHub repositories and websites. "
            "You can ask things like 'Create a dataset from the React documentation website' or "
            "'What datasets do I have?'"
        )
        
        # Send system status
        await self.send_system_status(websocket)
    
    async def disconnect(self, client_id: str) -> None:
        """Handle websocket disconnection.
        
        Args:
            client_id: Unique ID for the client
        """
        self.active_connections.pop(client_id, None)
    
    async def send_message(self, websocket: WebSocket, type: str, content: str, 
                           metadata: Optional[Dict[str, Any]] = None) -> None:
        """Send a message to the client.
        
        Args:
            websocket: The websocket connection
            type: Message type ('system', 'assistant', or 'error')
            content: Message content
            metadata: Optional additional metadata
        """
        message = {
            "type": type,
            "content": content,
            "timestamp": self.task_tracker.get_current_timestamp()
        }
        
        if metadata:
            message["metadata"] = metadata
            
        await websocket.send_text(json.dumps(message))
    
    async def send_system_status(self, websocket: WebSocket) -> None:
        """Send system status information to the client.
        
        Args:
            websocket: The websocket connection
        """
        # Get credentials status
        huggingface_status = False
        github_status = False
        neo4j_status = False
        
        try:
            # Check Hugging Face credentials
            _, huggingface_token = self.credentials_manager.get_huggingface_credentials()
            huggingface_status = bool(huggingface_token)
            
            # Check GitHub integration
            from github.client import GitHubClient
            github_client = GitHubClient()
            github_status = github_client.verify_credentials()
            
            # Check Neo4j connection
            graph_store = GraphStore()
            neo4j_status = graph_store.test_connection()
        except Exception as e:
            logger.error(f"Error checking system status: {e}")
        
        # Send status message
        status_message = {
            "type": "status",
            "content": {
                "huggingface": huggingface_status,
                "github": github_status,
                "neo4j": neo4j_status,
                "recent_tasks": self.task_tracker.list_resumable_tasks(limit=5)
            }
        }
        
        await websocket.send_text(json.dumps(status_message))
    
    async def send_task_update(self, websocket: WebSocket, task_id: str, progress: float, 
                              status: str, task_type: Optional[str] = None) -> None:
        """Send a task progress update to the client.
        
        Args:
            websocket: The websocket connection
            task_id: ID of the task
            progress: Progress percentage (0-100)
            status: Status message
            task_type: Type of task
        """
        update = {
            "type": "task_update",
            "task_id": task_id,
            "progress": progress,
            "status": status
        }
        
        if task_type:
            update["task_type"] = task_type
            
        await websocket.send_text(json.dumps(update))
    
    async def process_message(self, message_text: str, websocket: WebSocket) -> None:
        """Process an incoming chat message.
        
        Args:
            message_text: The text message from the client
            websocket: The websocket connection
        """
        try:
            # Process intent based on message
            if self.llm_client:
                # If LLM client is available, use it to determine intent
                await self.send_message(websocket, "thinking", "Thinking...")
                intent = await self._classify_intent(message_text)
                logger.info(f"Classified intent: {intent}")
                
                # Handle intent
                if intent.get("type") == "dataset_creation":
                    await self.handle_dataset_creation(intent, message_text, websocket)
                elif intent.get("type") == "dataset_management":
                    await self.handle_dataset_management(intent, message_text, websocket)
                elif intent.get("type") == "credentials":
                    await self.handle_credentials(intent, message_text, websocket)
                elif intent.get("type") == "task_management":
                    await self.handle_task_management(intent, message_text, websocket)
                else:
                    # Default to information query
                    await self.handle_information_query(message_text, websocket)
            else:
                # Without LLM, use simple keyword matching
                await self._process_message_keywords(message_text, websocket)
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            await self.send_message(
                websocket, 
                "error", 
                f"I encountered an error while processing your request: {str(e)}"
            )
    
    async def _process_message_keywords(self, message_text: str, websocket: WebSocket) -> None:
        """Process a message using simple keyword matching when LLM is unavailable.
        
        Args:
            message_text: The text message from the client
            websocket: The websocket connection
        """
        message_lower = message_text.lower()
        
        # Check for dataset creation
        if any(keyword in message_lower for keyword in ["create dataset", "new dataset", "make dataset"]):
            if "github" in message_lower:
                # Extract GitHub repo URL with simple pattern matching
                import re
                repo_url_match = re.search(r'github\.com/[^\s\/]+/[^\s\/]+', message_lower)
                repo_url = f"https://{repo_url_match.group(0)}" if repo_url_match else None
                
                if repo_url:
                    # Extract dataset name (text after "called" or "named")
                    dataset_name_match = re.search(r'(?:called|named)\s+([a-zA-Z0-9_-]+)', message_lower)
                    dataset_name = dataset_name_match.group(1) if dataset_name_match else "github-dataset"
                    
                    await self.handle_github_dataset_creation(repo_url, dataset_name, message_text, websocket)
                else:
                    await self.send_message(
                        websocket, 
                        "assistant", 
                        "I need a GitHub repository URL to create a dataset. Please provide a URL like 'github.com/org/repo'."
                    )
            elif any(keyword in message_lower for keyword in ["website", "url", "web", "site"]):
                # Extract URL with simple pattern matching
                import re
                url_match = re.search(r'https?://[^\s]+', message_lower)
                url = url_match.group(0) if url_match else None
                
                if url:
                    # Extract dataset name
                    dataset_name_match = re.search(r'(?:called|named)\s+([a-zA-Z0-9_-]+)', message_lower)
                    dataset_name = dataset_name_match.group(1) if dataset_name_match else "web-dataset"
                    
                    await self.handle_web_dataset_creation(url, dataset_name, message_text, websocket)
                else:
                    await self.send_message(
                        websocket, 
                        "assistant", 
                        "I need a website URL to create a dataset. Please provide a URL like 'https://example.com'."
                    )
            else:
                await self.send_message(
                    websocket, 
                    "assistant", 
                    "I can create datasets from GitHub repositories or websites. Please specify a source."
                )
        # Check for dataset management
        elif any(keyword in message_lower for keyword in ["list dataset", "show dataset", "my dataset"]):
            await self.handle_list_datasets(websocket)
        # Check for credentials
        elif any(keyword in message_lower for keyword in ["credential", "token", "api key", "huggingface"]):
            await self.send_message(
                websocket, 
                "assistant", 
                "To set up your credentials, please go to the Configuration page or use the CLI interface."
            )
        # Check for tasks
        elif any(keyword in message_lower for keyword in ["task", "job", "progress"]):
            await self.handle_list_tasks(websocket)
        # Default response
        else:
            await self.send_message(
                websocket, 
                "assistant", 
                "I'm here to help you create and manage datasets from GitHub repositories and websites. "
                "You can ask me to create a dataset, list your datasets, check task status, or get information about the system."
            )
    
    async def _classify_intent(self, message_text: str) -> Dict[str, Any]:
        """Classify user intent using LLM.
        
        Args:
            message_text: The text message from the client
            
        Returns:
            Dict: Intent classification result
        """
        if not self.llm_client:
            # Default intent if LLM is unavailable
            return {"type": "general_query"}
        
        try:
            # Define the system prompt for intent classification
            system_prompt = """You are an expert intent classifier for a dataset creation system.
Your task is to analyze the user's message and identify their intent.
Return a JSON object with the following fields:
- type: The intent type (dataset_creation, dataset_management, credentials, task_management, information_query)
- parameters: Parameters extracted from the user's message"""
            
            # Call LLM to classify intent
            response = self.llm_client.direct_client.messages.create(
                model=self.llm_client.anthropic_model if self.llm_client.provider == "anthropic" else self.llm_client.openai_model,
                messages=[
                    {"role": "user", "content": message_text}
                ],
                system=system_prompt,
                max_tokens=1000,
                temperature=0.2
            )
            
            # Extract JSON from response
            response_text = response.content[0].text if self.llm_client.provider == "anthropic" else response.choices[0].message.content
            
            try:
                # Try to find JSON in the response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    return json.loads(json_str)
                else:
                    logger.warning("Couldn't find JSON in LLM response")
                    return {"type": "information_query"}
            except Exception as e:
                logger.error(f"Error parsing intent JSON: {e}")
                return {"type": "information_query"}
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return {"type": "information_query"}
    
    async def handle_dataset_creation(self, intent: Dict[str, Any], message_text: str, websocket: WebSocket) -> None:
        """Handle dataset creation intent.
        
        Args:
            intent: The classified intent
            message_text: The original message
            websocket: The websocket connection
        """
        parameters = intent.get("parameters", {})
        source_type = parameters.get("source_type")
        
        if source_type == "github":
            repo_url = parameters.get("repository_url")
            dataset_name = parameters.get("dataset_name", "github-dataset")
            
            if repo_url:
                await self.handle_github_dataset_creation(repo_url, dataset_name, message_text, websocket)
            else:
                await self.send_message(
                    websocket, 
                    "assistant", 
                    "I need a GitHub repository URL to create a dataset. Can you provide one?"
                )
        elif source_type == "website":
            url = parameters.get("website_url")
            dataset_name = parameters.get("dataset_name", "web-dataset")
            
            if url:
                await self.handle_web_dataset_creation(url, dataset_name, message_text, websocket)
            else:
                await self.send_message(
                    websocket, 
                    "assistant", 
                    "I need a website URL to create a dataset. Can you provide one?"
                )
        else:
            await self.send_message(
                websocket, 
                "assistant", 
                "I can create datasets from GitHub repositories or websites. What source would you like to use?"
            )
    
    async def handle_github_dataset_creation(self, repo_url: str, dataset_name: str, 
                                            message_text: str, websocket: WebSocket) -> None:
        """Handle GitHub dataset creation.
        
        Args:
            repo_url: GitHub repository URL
            dataset_name: Name for the dataset
            message_text: The original message
            websocket: The websocket connection
        """
        # Validate repository URL
        if not repo_url.startswith("https://github.com/"):
            repo_url = f"https://github.com/{repo_url}" if "github.com" in repo_url else None
            
        if not repo_url:
            await self.send_message(
                websocket, 
                "assistant", 
                "I need a valid GitHub repository URL. Please provide a URL in the format 'github.com/org/repo'."
            )
            return
            
        # Check for Hugging Face credentials
        _, huggingface_token = self.credentials_manager.get_huggingface_credentials()
        if not huggingface_token:
            await self.send_message(
                websocket, 
                "assistant", 
                "Hugging Face credentials are not configured. Please set them up in the Configuration page before creating datasets."
            )
            return
            
        # Create dataset creator
        dataset_creator = DatasetCreator(huggingface_token=huggingface_token)
        
        # Create content fetcher
        content_fetcher = ContentFetcher()
        
        # Create a progress callback that sends updates via websocket
        task_id = self.task_tracker.create_task(
            "github_dataset",
            {"url": repo_url, "dataset_name": dataset_name},
            f"Create dataset '{dataset_name}' from GitHub repository {repo_url}"
        )
        
        # Acknowledge the request
        await self.send_message(
            websocket, 
            "assistant", 
            f"I'm creating a dataset named '{dataset_name}' from the GitHub repository {repo_url}. "
            f"I'll keep you updated on the progress."
        )
        
        # Define progress callback
        async def progress_callback(percent: float, message: Optional[str] = None) -> None:
            status = message or "Processing"
            await self.send_task_update(websocket, task_id, percent, status, "github_dataset")
        
        # Start background task
        asyncio.create_task(self._create_github_dataset(
            content_fetcher, dataset_creator, repo_url, dataset_name, 
            progress_callback, task_id, message_text, websocket
        ))
        
    async def _create_github_dataset(
        self, content_fetcher: ContentFetcher, dataset_creator: DatasetCreator,
        repo_url: str, dataset_name: str, progress_callback: Callable, 
        task_id: str, user_instructions: str, websocket: WebSocket
    ) -> None:
        """Background task for GitHub dataset creation.
        
        Args:
            content_fetcher: GitHub content fetcher
            dataset_creator: Dataset creator
            repo_url: GitHub repository URL
            dataset_name: Name for the dataset
            progress_callback: Callback function for progress updates
            task_id: Task ID
            user_instructions: Original user message with instructions
            websocket: The websocket connection
        """
        try:
            # Use the LLM client to determine if we should use AI guidance
            use_ai_guidance = False
            ai_instructions = None
            
            if self.llm_client:
                # Check if the user message contains specific instructions
                intent_analysis = await self._classify_intent(user_instructions)
                if "parameters" in intent_analysis and "specific_filters" in intent_analysis["parameters"]:
                    use_ai_guidance = True
                    ai_instructions = user_instructions
            
            # Fetch the repository content
            await progress_callback(10, "Fetching repository metadata and files...")
            
            # Check if this is an organization URL
            import re
            is_org_url = bool(re.match(r"https?://github\.com/([^/]+)/?$", repo_url))
            
            if is_org_url:
                await progress_callback(15, "Detected GitHub organization - fetching all repositories...")
                if use_ai_guidance:
                    content_files = content_fetcher.fetch_multiple_repositories(
                        repo_url,
                        progress_callback=lambda p: asyncio.run(progress_callback(15 + p * 0.5, "Fetching repositories...")),
                        user_instructions=ai_instructions,
                        use_ai_guidance=True
                    )
                else:
                    content_files = content_fetcher.fetch_multiple_repositories(
                        repo_url,
                        progress_callback=lambda p: asyncio.run(progress_callback(15 + p * 0.5, "Fetching repositories..."))
                    )
            else:
                if use_ai_guidance:
                    content_files = content_fetcher.fetch_single_repository(
                        repo_url,
                        progress_callback=lambda p: asyncio.run(progress_callback(15 + p * 0.5, "Fetching repository...")),
                        user_instructions=ai_instructions,
                        use_ai_guidance=True
                    )
                else:
                    content_files = content_fetcher.fetch_single_repository(
                        repo_url,
                        progress_callback=lambda p: asyncio.run(progress_callback(15 + p * 0.5, "Fetching repository..."))
                    )
            
            if not content_files:
                await progress_callback(-1, "No content found in repository")
                await self.send_message(
                    websocket,
                    "assistant",
                    f"I couldn't find any content in the GitHub repository {repo_url}."
                )
                self.task_tracker.complete_task(task_id, success=False, result={"error": "No content found"})
                return
            
            # Create the dataset
            await progress_callback(70, f"Creating dataset from {len(content_files)} files...")
            result = dataset_creator.create_and_push_dataset(
                file_data_list=content_files,
                dataset_name=dataset_name,
                description=f"Dataset created from {repo_url}",
                source_info=repo_url,
                progress_callback=lambda p: asyncio.run(progress_callback(70 + p * 0.3, "Creating and uploading dataset"))
            )
            
            # Check result
            if result[0]:  # Success flag
                await progress_callback(100, "Completed")
                await self.send_message(
                    websocket,
                    "assistant",
                    f"Successfully created dataset '{dataset_name}' from GitHub repository {repo_url}. "
                    f"The dataset contains {len(content_files)} files and is now available on Hugging Face."
                )
                self.task_tracker.complete_task(task_id, success=True)
            else:
                await progress_callback(-1, f"Failed: {result[1]}")
                await self.send_message(
                    websocket,
                    "assistant",
                    f"I encountered an error while creating the dataset: {result[1]}"
                )
                self.task_tracker.complete_task(task_id, success=False, result={"error": result[1]})
        except Exception as e:
            logger.error(f"Error in GitHub dataset creation: {e}", exc_info=True)
            await progress_callback(-1, f"Error: {str(e)}")
            await self.send_message(
                websocket,
                "error",
                f"I encountered an error while creating the dataset: {str(e)}"
            )
            self.task_tracker.complete_task(task_id, success=False, result={"error": str(e)})
            
    async def handle_web_dataset_creation(self, url: str, dataset_name: str, 
                                        message_text: str, websocket: WebSocket) -> None:
        """Handle web dataset creation.
        
        Args:
            url: Website URL
            dataset_name: Name for the dataset
            message_text: The original message
            websocket: The websocket connection
        """
        # Validate URL
        if not url.startswith("http"):
            url = f"https://{url}"
            
        # Check for Hugging Face credentials
        _, huggingface_token = self.credentials_manager.get_huggingface_credentials()
        if not huggingface_token:
            await self.send_message(
                websocket, 
                "assistant", 
                "Hugging Face credentials are not configured. Please set them up in the Configuration page before creating datasets."
            )
            return
            
        # Create dataset creator
        dataset_creator = DatasetCreator(huggingface_token=huggingface_token)
        
        # Create a progress callback that sends updates via websocket
        task_id = self.task_tracker.create_task(
            "web_dataset",
            {"url": url, "dataset_name": dataset_name},
            f"Create dataset '{dataset_name}' from website {url}"
        )
        
        # Acknowledge the request
        await self.send_message(
            websocket, 
            "assistant", 
            f"I'm creating a dataset named '{dataset_name}' from the website {url}. "
            f"I'll keep you updated on the progress."
        )
        
        # Define progress callback
        async def progress_callback(percent: float, message: Optional[str] = None) -> None:
            status = message or "Processing"
            await self.send_task_update(websocket, task_id, percent, status, "web_dataset")
        
        # Start background task
        asyncio.create_task(self._create_web_dataset(
            dataset_creator, url, dataset_name, 
            progress_callback, task_id, message_text, websocket
        ))
        
    async def _create_web_dataset(
        self, dataset_creator: DatasetCreator, url: str, dataset_name: str, 
        progress_callback: Callable, task_id: str, user_instructions: str, websocket: WebSocket
    ) -> None:
        """Background task for web dataset creation.
        
        Args:
            dataset_creator: Dataset creator
            url: Website URL
            dataset_name: Name for the dataset
            progress_callback: Callback function for progress updates
            task_id: Task ID
            user_instructions: Original user message with instructions
            websocket: The websocket connection
        """
        try:
            # Use the LLM client to determine if we should use AI guidance
            use_ai_guidance = False
            recursive = True
            
            if self.llm_client:
                # Check if the user message contains specific instructions
                intent_analysis = await self._classify_intent(user_instructions)
                if "parameters" in intent_analysis and "specific_filters" in intent_analysis["parameters"]:
                    use_ai_guidance = True
                
                # Check if recursive crawling is explicitly mentioned
                if "parameters" in intent_analysis and "recursive" in intent_analysis["parameters"]:
                    recursive = intent_analysis["parameters"]["recursive"]
            
            # Create the dataset
            result = dataset_creator.create_dataset_from_url(
                url=url,
                dataset_name=dataset_name,
                description=f"Dataset created from {url}",
                recursive=recursive,
                progress_callback=lambda p, m=None: asyncio.run(progress_callback(p, m)),
                user_instructions=user_instructions if use_ai_guidance else None,
                use_ai_guidance=use_ai_guidance
            )
            
            # Check result
            if result.get("success"):
                await progress_callback(100, "Completed")
                pages_processed = result.get("pages_processed", 0)
                await self.send_message(
                    websocket,
                    "assistant",
                    f"Successfully created dataset '{dataset_name}' from website {url}. "
                    f"The dataset contains content from {pages_processed} pages and is now available on Hugging Face."
                )
                self.task_tracker.complete_task(task_id, success=True)
            else:
                await progress_callback(-1, f"Failed: {result.get('message')}")
                await self.send_message(
                    websocket,
                    "assistant",
                    f"I encountered an error while creating the dataset: {result.get('message')}"
                )
                self.task_tracker.complete_task(task_id, success=False, result={"error": result.get('message')})
        except Exception as e:
            logger.error(f"Error in web dataset creation: {e}", exc_info=True)
            await progress_callback(-1, f"Error: {str(e)}")
            await self.send_message(
                websocket,
                "error",
                f"I encountered an error while creating the dataset: {str(e)}"
            )
            self.task_tracker.complete_task(task_id, success=False, result={"error": str(e)})
    
    async def handle_dataset_management(self, intent: Dict[str, Any], message_text: str, websocket: WebSocket) -> None:
        """Handle dataset management intent.
        
        Args:
            intent: The classified intent
            message_text: The original message
            websocket: The websocket connection
        """
        parameters = intent.get("parameters", {})
        action = parameters.get("action")
        
        if action == "list":
            await self.handle_list_datasets(websocket)
        elif action == "view":
            dataset_id = parameters.get("dataset_id")
            await self.handle_view_dataset(dataset_id, websocket)
        elif action == "delete":
            dataset_id = parameters.get("dataset_id")
            await self.handle_delete_dataset(dataset_id, websocket)
        else:
            await self.send_message(
                websocket,
                "assistant",
                "I can list your datasets, view dataset details, or delete datasets. What would you like to do?"
            )
    
    async def handle_list_datasets(self, websocket: WebSocket) -> None:
        """Handle listing datasets.
        
        Args:
            websocket: The websocket connection
        """
        # Check for Hugging Face credentials
        _, huggingface_token = self.credentials_manager.get_huggingface_credentials()
        if not huggingface_token:
            await self.send_message(
                websocket, 
                "assistant", 
                "Hugging Face credentials are not configured. Please set them up in the Configuration page before managing datasets."
            )
            return
            
        # Initialize dataset manager
        dataset_manager = DatasetManager(
            huggingface_token=huggingface_token,
            credentials_manager=self.credentials_manager
        )
        
        try:
            # Fetch datasets
            await self.send_message(websocket, "thinking", "Fetching your datasets from Hugging Face...")
            datasets = dataset_manager.list_datasets()
            
            if not datasets:
                await self.send_message(
                    websocket,
                    "assistant",
                    "You don't have any datasets on Hugging Face yet. You can create one by asking me to create a dataset from a GitHub repository or website."
                )
                return
                
            # Format dataset information
            dataset_list = "\n\n".join([
                f"* **{dataset.get('id', 'Unknown')}**\n  - Last modified: {dataset.get('lastModified', 'Unknown date')}"
                for dataset in datasets[:10]  # Limit to 10 datasets to avoid overly long message
            ])
            
            # Add a note if there are more datasets
            more_note = f"\n\n...and {len(datasets) - 10} more" if len(datasets) > 10 else ""
            
            await self.send_message(
                websocket,
                "assistant",
                f"I found {len(datasets)} datasets in your Hugging Face account:\n\n{dataset_list}{more_note}"
            )
        except Exception as e:
            logger.error(f"Error listing datasets: {e}")
            await self.send_message(
                websocket,
                "error",
                f"I encountered an error while fetching your datasets: {str(e)}"
            )
    
    async def handle_view_dataset(self, dataset_id: Optional[str], websocket: WebSocket) -> None:
        """Handle viewing dataset details.
        
        Args:
            dataset_id: ID of the dataset to view
            websocket: The websocket connection
        """
        if not dataset_id:
            await self.send_message(
                websocket,
                "assistant",
                "I need a dataset ID to show you the details. You can ask me to list your datasets first."
            )
            return
            
        # Check for Hugging Face credentials
        _, huggingface_token = self.credentials_manager.get_huggingface_credentials()
        if not huggingface_token:
            await self.send_message(
                websocket, 
                "assistant", 
                "Hugging Face credentials are not configured. Please set them up in the Configuration page before managing datasets."
            )
            return
            
        # Initialize dataset manager
        dataset_manager = DatasetManager(
            huggingface_token=huggingface_token,
            credentials_manager=self.credentials_manager
        )
        
        try:
            # Fetch dataset details
            await self.send_message(websocket, "thinking", f"Fetching details for dataset '{dataset_id}'...")
            info = dataset_manager.get_dataset_info(dataset_id)
            
            if info:
                # Format dataset information
                dataset_info = (
                    f"**Dataset**: {info.id}\n\n"
                    f"**Description**: {info.description}\n\n"
                    f"**Created**: {info.created_at}\n\n"
                    f"**Last modified**: {info.last_modified}\n\n"
                    f"**Downloads**: {info.downloads}\n\n"
                    f"**Likes**: {info.likes}\n\n"
                    f"**Tags**: {', '.join(info.tags) if info.tags else 'None'}"
                )
                
                await self.send_message(
                    websocket,
                    "assistant",
                    dataset_info
                )
            else:
                await self.send_message(
                    websocket,
                    "assistant",
                    f"I couldn't find a dataset with the ID '{dataset_id}'. Please check the ID and try again."
                )
        except Exception as e:
            logger.error(f"Error viewing dataset: {e}")
            await self.send_message(
                websocket,
                "error",
                f"I encountered an error while fetching dataset details: {str(e)}"
            )
    
    async def handle_delete_dataset(self, dataset_id: Optional[str], websocket: WebSocket) -> None:
        """Handle deleting a dataset.
        
        Args:
            dataset_id: ID of the dataset to delete
            websocket: The websocket connection
        """
        if not dataset_id:
            await self.send_message(
                websocket,
                "assistant",
                "I need a dataset ID to delete. You can ask me to list your datasets first."
            )
            return
            
        # Check for Hugging Face credentials
        _, huggingface_token = self.credentials_manager.get_huggingface_credentials()
        if not huggingface_token:
            await self.send_message(
                websocket, 
                "assistant", 
                "Hugging Face credentials are not configured. Please set them up in the Configuration page before managing datasets."
            )
            return
            
        # Initialize dataset manager
        dataset_manager = DatasetManager(
            huggingface_token=huggingface_token,
            credentials_manager=self.credentials_manager
        )
        
        try:
            # Delete the dataset
            await self.send_message(websocket, "thinking", f"Deleting dataset '{dataset_id}'...")
            success = dataset_manager.delete_dataset(dataset_id)
            
            if success:
                await self.send_message(
                    websocket,
                    "assistant",
                    f"I've successfully deleted the dataset '{dataset_id}'."
                )
            else:
                await self.send_message(
                    websocket,
                    "assistant",
                    f"I couldn't delete the dataset '{dataset_id}'. Please check the ID and try again."
                )
        except Exception as e:
            logger.error(f"Error deleting dataset: {e}")
            await self.send_message(
                websocket,
                "error",
                f"I encountered an error while deleting the dataset: {str(e)}"
            )
    
    async def handle_credentials(self, intent: Dict[str, Any], message_text: str, websocket: WebSocket) -> None:
        """Handle credentials intent.
        
        Args:
            intent: The classified intent
            message_text: The original message
            websocket: The websocket connection
        """
        # For security reasons, credential management is only available through the web UI Configuration page
        await self.send_message(
            websocket,
            "assistant",
            "For security reasons, I can't set up credentials through this chat interface. "
            "Please use the Configuration page in the web UI to manage your credentials."
        )
    
    async def handle_task_management(self, intent: Dict[str, Any], message_text: str, websocket: WebSocket) -> None:
        """Handle task management intent.
        
        Args:
            intent: The classified intent
            message_text: The original message
            websocket: The websocket connection
        """
        parameters = intent.get("parameters", {})
        action = parameters.get("action")
        
        if action == "list":
            await self.handle_list_tasks(websocket)
        elif action == "resume":
            task_id = parameters.get("task_id")
            await self.handle_resume_task(task_id, websocket)
        elif action == "cancel":
            task_id = parameters.get("task_id")
            await self.handle_cancel_task(task_id, websocket)
        else:
            await self.send_message(
                websocket,
                "assistant",
                "I can list your tasks, resume interrupted tasks, or cancel running tasks. What would you like to do?"
            )
    
    async def handle_list_tasks(self, websocket: WebSocket) -> None:
        """Handle listing tasks.
        
        Args:
            websocket: The websocket connection
        """
        try:
            # List resumable tasks
            tasks = self.task_tracker.list_resumable_tasks()
            
            if not tasks:
                await self.send_message(
                    websocket,
                    "assistant",
                    "You don't have any active or resumable tasks right now."
                )
                return
                
            # Format task information
            task_list = "\n\n".join([
                f"* **Task ID**: {task.get('id')}\n  - **Type**: {task.get('type')}\n  - **Progress**: {task.get('progress', 0):.0f}%\n  - **Description**: {task.get('description')}\n  - **Last updated**: {task.get('updated_ago', 'unknown')}"
                for task in tasks
            ])
            
            await self.send_message(
                websocket,
                "assistant",
                f"Here are your active and resumable tasks:\n\n{task_list}"
            )
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            await self.send_message(
                websocket,
                "error",
                f"I encountered an error while fetching your tasks: {str(e)}"
            )
    
    async def handle_resume_task(self, task_id: Optional[str], websocket: WebSocket) -> None:
        """Handle resuming a task.
        
        Args:
            task_id: ID of the task to resume
            websocket: The websocket connection
        """
        if not task_id:
            await self.send_message(
                websocket,
                "assistant",
                "I need a task ID to resume. You can ask me to list your tasks first."
            )
            return
            
        try:
            # Get task details
            task = self.task_tracker.get_task(task_id)
            
            if not task:
                await self.send_message(
                    websocket,
                    "assistant",
                    f"I couldn't find a task with the ID '{task_id}'. Please check the ID and try again."
                )
                return
                
            # Check if task is resumable
            if task.get("status") != "interrupted":
                await self.send_message(
                    websocket,
                    "assistant",
                    f"The task with ID '{task_id}' cannot be resumed because it is not in an interrupted state."
                )
                return
                
            # Resume the task based on type
            task_type = task.get("type")
            
            await self.send_message(
                websocket,
                "assistant",
                f"I'm resuming the '{task_type}' task with ID '{task_id}'."
            )
            
            # TODO: Implement task resumption logic
            # This will depend on the specific task types and resumption mechanisms
            
            await self.send_message(
                websocket,
                "assistant",
                "I'm sorry, but task resumption is not yet implemented in the chat interface. "
                "Please use the CLI interface to resume this task."
            )
        except Exception as e:
            logger.error(f"Error resuming task: {e}")
            await self.send_message(
                websocket,
                "error",
                f"I encountered an error while resuming the task: {str(e)}"
            )
    
    async def handle_cancel_task(self, task_id: Optional[str], websocket: WebSocket) -> None:
        """Handle cancelling a task.
        
        Args:
            task_id: ID of the task to cancel
            websocket: The websocket connection
        """
        if not task_id:
            await self.send_message(
                websocket,
                "assistant",
                "I need a task ID to cancel. You can ask me to list your tasks first."
            )
            return
            
        try:
            # Cancel the task
            success = self.task_tracker.cancel_task(task_id)
            
            if success:
                await self.send_message(
                    websocket,
                    "assistant",
                    f"I've successfully cancelled the task with ID '{task_id}'."
                )
            else:
                await self.send_message(
                    websocket,
                    "assistant",
                    f"I couldn't cancel the task with ID '{task_id}'. Please check the ID and try again."
                )
        except Exception as e:
            logger.error(f"Error cancelling task: {e}")
            await self.send_message(
                websocket,
                "error",
                f"I encountered an error while cancelling the task: {str(e)}"
            )
    
    async def handle_information_query(self, message_text: str, websocket: WebSocket) -> None:
        """Handle general information queries.
        
        Args:
            message_text: The original message
            websocket: The websocket connection
        """
        # If LLM client is available, generate a contextual response
        if self.llm_client:
            try:
                # Define the system prompt
                system_prompt = """You are an assistant for Serper, a system that creates datasets from GitHub repositories and websites for use with AI models.
You provide helpful information about the system's features and capabilities.
Keep your responses concise, informative, and focused on the Serper system.
Information about Serper:
- It can create datasets from GitHub repositories and websites
- It can export data to Hugging Face datasets
- It can create knowledge graphs from content
- It supports scheduled dataset updates
- Users can manage their datasets, tasks, and credentials"""
                
                # Call LLM to generate response
                response = self.llm_client.direct_client.messages.create(
                    model=self.llm_client.anthropic_model if self.llm_client.provider == "anthropic" else self.llm_client.openai_model,
                    messages=[
                        {"role": "user", "content": message_text}
                    ],
                    system=system_prompt,
                    max_tokens=1000,
                    temperature=0.7
                )
                
                # Extract response text
                response_text = response.content[0].text if self.llm_client.provider == "anthropic" else response.choices[0].message.content
                
                await self.send_message(
                    websocket,
                    "assistant",
                    response_text
                )
            except Exception as e:
                logger.error(f"Error generating LLM response: {e}")
                # Fall back to default response
                await self.send_message(
                    websocket,
                    "assistant",
                    "I'm here to help you create and manage datasets from GitHub repositories and websites. "
                    "You can ask me to create a dataset, list your datasets, check task status, or get information about the system."
                )
        else:
            # Default response when LLM is unavailable
            await self.send_message(
                websocket,
                "assistant",
                "I'm here to help you create and manage datasets from GitHub repositories and websites. "
                "You can ask me to create a dataset, list your datasets, check task status, or get information about the system."
            )