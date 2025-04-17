import logging
import subprocess
import threading
import time
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union

# Configure logging
logger = logging.getLogger(__name__)

class ServerStatus:
    """Class to track server status"""
    def __init__(self):
        self.running = False
        self.process = None
        self.server_thread = None
        self.host = "0.0.0.0"
        self.port = 8080

# Create a global status object
server_status = ServerStatus()

# Initialize FastAPI app
app = FastAPI(
    title="othertales Serper API",
    description="Scrape websites to create datasets and knowledge graphs for machine learning and data analysis",
    version="1.0.0",
)

# Add CORS middleware for LLM tool compatibility
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(
    scheme_name="API Key",
    description="Bearer token authentication with API key",
    auto_error=True
)
API_KEY = None


# Models for request and response
class GenerateDatasetRequest(BaseModel):
    source_type: str = Field(
        ...,
        description="Type of source: 'repository' or 'organization'"
    )
    source_name: str = Field(
        ...,
        description="Repository URL or organization name"
    )
    dataset_name: str = Field(
        ...,
        description="Name for the generated dataset on Hugging Face"
    )
    description: str = Field(
        ...,
        description="Description of the dataset content and purpose"
    )


class WebCrawlRequest(BaseModel):
    url: str = Field(
        ..., 
        description="URL to crawl for content"
    )
    recursive: bool = Field(
        False, 
        description="Whether to recursively crawl linked pages"
    )
    dataset_name: str = Field(
        ..., 
        description="Name for the generated dataset on Hugging Face"
    )
    description: str = Field(
        ..., 
        description="Description of the dataset content and purpose"
    )
    export_to_graph: bool = Field(
        True,
        description="Whether to export content to a knowledge graph"
    )
    graph_name: Optional[str] = Field(
        None,
        description="Name of the knowledge graph to export to (creates new if not exists)"
    )


class ModifyDatasetRequest(BaseModel):
    action: str = Field(
        ..., 
        description="Action to perform on the dataset: 'view', 'download', or 'delete'"
    )
    dataset_id: str = Field(
        ..., 
        description="Identifier for the dataset on Hugging Face"
    )


class KnowledgeGraphRequest(BaseModel):
    action: str = Field(
        ...,
        description="Action to perform on knowledge graph: 'create', 'list', 'view', 'delete'"
    )
    graph_name: Optional[str] = Field(
        None,
        description="Name of the knowledge graph (required for create, view, delete actions)"
    )
    description: Optional[str] = Field(
        None,
        description="Description of the knowledge graph (for create action)"
    )


class ApiResponse(BaseModel):
    success: bool = Field(
        ..., 
        description="Whether the operation was successful"
    )
    message: str = Field(
        ..., 
        description="Explanatory message about the operation result"
    )
    data: Optional[Any] = Field(
        None, 
        description="Optional data returned from the operation"
    )


# Authentication dependency
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify that the provided API key is valid.
    
    This dependency checks if the Bearer token matches the configured API key.
    """
    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="API key not configured on server",
        )
    
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key",
        )
    return credentials.credentials


@app.get("/", include_in_schema=True, summary="API Root")
async def root():
    """
    Root endpoint providing basic information about the API.
    
    Returns a simple message indicating the API is operational.
    """
    return {"message": "SDK Dataset Generator API. See /docs for API documentation."}

@app.get("/status", response_model=dict, summary="Server Status")
async def status():
    """
    Check server status and configuration.
    
    Returns information about the server's running state, host address, and port.
    """
    return {
        "status": "running" if server_status.running else "stopped",
        "host": server_status.host,
        "port": server_status.port,
        "version": app.version
    }


@app.post("/generate", response_model=ApiResponse, summary="Generate Dataset")
async def generate_dataset(
    request: GenerateDatasetRequest, api_key: str = Depends(verify_api_key)
):
    """
    Create and publish a new dataset on Hugging Face from GitHub repository or organization content.
    
    This endpoint fetches code files from the specified GitHub source, processes them,
    and publishes a structured dataset to Hugging Face with appropriate metadata.
    """
    try:
        # Import necessary components
        from github.content_fetcher import ContentFetcher
        from huggingface.dataset_creator import DatasetCreator
        from config.credentials_manager import CredentialsManager

        credentials_manager = CredentialsManager()

        # Get credentials
        github_username, github_token = credentials_manager.get_github_credentials()
        if not github_token:
            return ApiResponse(
                success=False,
                message="GitHub token not found. Please configure credentials first.",
                data=None,
            )

        hf_username, huggingface_token = credentials_manager.get_huggingface_credentials()
        if not huggingface_token:
            return ApiResponse(
                success=False,
                message="Hugging Face token not found. Please configure credentials first.",
                data=None,
            )

        content_fetcher = ContentFetcher(github_token=github_token)
        dataset_creator = DatasetCreator(huggingface_token=huggingface_token)

        # Process by source type
        if request.source_type.lower() == "organization":
            # Silent progress callback for API mode
            def progress_callback(percent, message=None):
                logger.info(f"Progress: {percent:.0f}% - {message if message else ''}")

            logger.info(f"Fetching repositories from organization: {request.source_name}")
            repos = content_fetcher.fetch_org_repositories(
                request.source_name, progress_callback=lambda p: progress_callback(p)
            )

            if not repos:
                return ApiResponse(
                    success=False,
                    message=f"No repositories found for organization: {request.source_name}",
                    data=None,
                )

            logger.info(f"Found {len(repos)} repositories")
            content = content_fetcher.fetch_multiple_repositories(
                request.source_name, progress_callback=lambda p: progress_callback(p)
            )

            if not content:
                return ApiResponse(
                    success=False, 
                    message="No content found in repositories",
                    data=None,
                )

            logger.info(f"Processing {len(content)} files...")
            success, dataset = dataset_creator.create_and_push_dataset(
                file_data_list=content,
                dataset_name=request.dataset_name,
                description=request.description,
                source_info=request.source_name,
            )

            if success:
                return ApiResponse(
                    success=True,
                    message=f"Dataset '{request.dataset_name}' created successfully",
                    data={"dataset_name": request.dataset_name},
                )
            else:
                return ApiResponse(
                    success=False, 
                    message="Failed to create dataset",
                    data=None,
                )

        elif request.source_type.lower() == "repository":
            # Silent progress callback for API mode
            def progress_callback(percent, message=None):
                logger.info(f"Progress: {percent:.0f}% - {message if message else ''}")

            logger.info(f"Creating dataset from repository: {request.source_name}")
            result = dataset_creator.create_dataset_from_repository(
                repo_url=request.source_name,
                dataset_name=request.dataset_name,
                description=request.description,
                progress_callback=progress_callback,
            )

            if result.get("success"):
                return ApiResponse(
                    success=True,
                    message=f"Dataset '{request.dataset_name}' created successfully",
                    data={"dataset_name": request.dataset_name},
                )
            else:
                return ApiResponse(
                    success=False,
                    message=f"Failed to create dataset: {result.get('message', 'Unknown error')}",
                    data=None,
                )
        else:
            return ApiResponse(
                success=False,
                message=f"Invalid source_type: {request.source_type}. Must be 'organization' or 'repository'",
                data=None,
            )

    except Exception as e:
        logger.error(f"Error generating dataset: {str(e)}")
        return ApiResponse(success=False, message=f"Error: {str(e)}", data=None)


@app.post("/modify", response_model=ApiResponse, summary="Modify Dataset")
async def modify_dataset(
    request: ModifyDatasetRequest, api_key: str = Depends(verify_api_key)
):
    """
    Perform operations on an existing dataset: view details, download metadata, or delete.
    
    This endpoint allows retrieving dataset information, downloading dataset metadata files,
    or completely removing a dataset from Hugging Face based on the specified action.
    """
    try:
        # Import necessary components
        from huggingface.dataset_manager import DatasetManager
        from config.credentials_manager import CredentialsManager

        credentials_manager = CredentialsManager()
        _, huggingface_token = credentials_manager.get_huggingface_credentials()

        if not huggingface_token:
            return ApiResponse(
                success=False,
                message="Hugging Face token not found. Please configure credentials first.",
                data=None,
            )

        dataset_manager = DatasetManager(
            huggingface_token=huggingface_token,
            credentials_manager=credentials_manager,
        )

        if request.action.lower() == "view":
            info = dataset_manager.get_dataset_info(request.dataset_id)
            if info:
                dataset_info = {
                    "id": info.id,
                    "description": info.description,
                    "created_at": str(info.created_at),
                    "last_modified": str(info.last_modified),
                    "downloads": info.downloads,
                    "likes": info.likes,
                    "tags": info.tags,
                }
                return ApiResponse(
                    success=True,
                    message=f"Retrieved information for dataset '{request.dataset_id}'",
                    data=dataset_info,
                )
            else:
                return ApiResponse(
                    success=False,
                    message=f"Error retrieving details for dataset {request.dataset_id}",
                    data=None,
                )

        elif request.action.lower() == "download":
            success = dataset_manager.download_dataset_metadata(request.dataset_id)
            if success:
                return ApiResponse(
                    success=True,
                    message=f"Metadata for dataset '{request.dataset_id}' downloaded successfully",
                    data={"path": f"./dataset_metadata/{request.dataset_id}/"},
                )
            else:
                return ApiResponse(
                    success=False,
                    message=f"Error downloading metadata for dataset {request.dataset_id}",
                    data=None,
                )

        elif request.action.lower() == "delete":
            success = dataset_manager.delete_dataset(request.dataset_id)
            if success:
                return ApiResponse(
                    success=True,
                    message=f"Dataset '{request.dataset_id}' deleted successfully",
                    data=None,
                )
            else:
                return ApiResponse(
                    success=False,
                    message=f"Error deleting dataset {request.dataset_id}",
                    data=None,
                )
        else:
            return ApiResponse(
                success=False,
                message=f"Invalid action: {request.action}. Must be 'view', 'download', or 'delete'",
                data=None,
            )

    except Exception as e:
        logger.error(f"Error modifying dataset: {str(e)}")
        return ApiResponse(success=False, message=f"Error: {str(e)}", data=None)


def set_api_key(key):
    """Set the API key for authentication"""
    global API_KEY
    API_KEY = key


def start_server(api_key, host="0.0.0.0", port=8080):
    """Start the FastAPI server using Uvicorn"""
    set_api_key(api_key)

    def run_server():
        import uvicorn
        server_status.running = True
        server_status.host = host
        server_status.port = port
        logger.info(f"Starting OpenAPI FastAPI server on {host}:{port}")
        logger.info(f"OpenAPI Schema available at: http://{host}:{port}/openapi.json")
        logger.info(f"API Documentation available at: http://{host}:{port}/docs")
        uvicorn.run(
            app, 
            host=host, 
            port=port, 
            log_level="info"
        )
    
    if server_status.running:
        logger.warning("Server is already running")
        return False
    
    server_status.server_thread = threading.Thread(target=run_server)
    server_status.server_thread.daemon = True
    server_status.server_thread.start()
    
    # Give the server a moment to start
    time.sleep(1)
    logger.info("FastAPI server started successfully")
    
    return {
        "status": "running",
        "host": host,
        "port": port,
        "api_docs_url": f"http://{host}:{port}/docs",
        "openapi_url": f"http://{host}:{port}/openapi.json"
    }


def stop_server():
    """Stop the FastAPI server"""
    server_status.running = False
    logger.info("Stopping OpenAPI FastAPI server")
    return True


def is_server_running():
    """Check if the server is running"""
    return server_status.running

def get_server_info():
    """Get server info including OpenAPI schema URL"""
    host = server_status.host
    port = server_status.port
    
    return {
        "status": "running" if server_status.running else "stopped",
        "host": host,
        "port": port,
        "api_docs_url": f"http://{host}:{port}/docs" if server_status.running else None,
        "openapi_url": f"http://{host}:{port}/openapi.json" if server_status.running else None
    }


@app.post("/crawl", response_model=ApiResponse, summary="Crawl Website")
async def crawl_website(
    request: WebCrawlRequest, api_key: str = Depends(verify_api_key)
):
    """
    Crawl a website and create a dataset from the content.
    
    This endpoint crawls the specified URL, optionally following links recursively,
    processes the content into markdown, creates a HuggingFace dataset,
    and optionally exports the content to a knowledge graph.
    """
    try:
        # Import necessary components
        from huggingface.dataset_creator import DatasetCreator
        from config.credentials_manager import CredentialsManager
        
        credentials_manager = CredentialsManager()
        
        # Get Hugging Face credentials
        hf_username, huggingface_token = credentials_manager.get_huggingface_credentials()
        if not huggingface_token:
            return ApiResponse(
                success=False,
                message="Hugging Face token not found. Please configure credentials first.",
                data=None,
            )
        
        # Initialize dataset creator
        dataset_creator = DatasetCreator(huggingface_token=huggingface_token)
        
        # Progress callback for logging
        def progress_callback(percent, message=None):
            logger.info(f"Progress: {percent:.0f}% - {message if message else ''}")
        
        # Create dataset from URL
        result = dataset_creator.create_dataset_from_url(
            url=request.url,
            dataset_name=request.dataset_name,
            description=request.description,
            recursive=request.recursive,
            progress_callback=progress_callback,
            export_to_knowledge_graph=request.export_to_graph,
            graph_name=request.graph_name
        )
        
        if result.get("success"):
            return ApiResponse(
                success=True,
                message=f"Dataset '{request.dataset_name}' created successfully",
                data={
                    "dataset_name": request.dataset_name,
                    "pages_processed": result.get("pages_processed", 0),
                    "task_id": result.get("task_id")
                },
            )
        else:
            return ApiResponse(
                success=False,
                message=f"Failed to create dataset: {result.get('message', 'Unknown error')}",
                data=None,
            )
        
    except Exception as e:
        logger.error(f"Error crawling website: {str(e)}")
        return ApiResponse(success=False, message=f"Error: {str(e)}", data=None)


@app.post("/knowledge_graph", response_model=ApiResponse, summary="Manage Knowledge Graphs")
async def manage_knowledge_graph(
    request: KnowledgeGraphRequest, api_key: str = Depends(verify_api_key)
):
    """
    Create, view, list, or delete knowledge graphs in Neo4j.
    
    This endpoint provides operations for managing knowledge graphs:
    - `create`: Create a new knowledge graph with the given name
    - `list`: List all available knowledge graphs
    - `view`: View statistics for a specific knowledge graph
    - `delete`: Delete a knowledge graph and all its contents
    """
    try:
        # Import knowledge graph store
        from knowledge_graph.graph_store import GraphStore
        
        action = request.action.lower()
        
        # Basic graph store for initial operations
        graph_store = GraphStore()
        
        # Check connection
        if not graph_store.test_connection():
            return ApiResponse(
                success=False,
                message="Failed to connect to Neo4j database. Check database configuration.",
                data=None
            )
        
        # List knowledge graphs
        if action == "list":
            graphs = graph_store.list_graphs()
            return ApiResponse(
                success=True,
                message=f"Found {len(graphs)} knowledge graphs",
                data={"graphs": graphs}
            )
        
        # Create knowledge graph
        elif action == "create":
            if not request.graph_name:
                return ApiResponse(
                    success=False,
                    message="Graph name is required for create action",
                    data=None
                )
            
            # Create the graph
            success = graph_store.create_graph(request.graph_name, request.description)
            
            if success:
                # Initialize schema on the new graph
                graph_store = GraphStore(graph_name=request.graph_name)
                graph_store.initialize_schema()
                
                return ApiResponse(
                    success=True,
                    message=f"Knowledge graph '{request.graph_name}' created successfully",
                    data={"graph_name": request.graph_name}
                )
            else:
                return ApiResponse(
                    success=False,
                    message=f"Failed to create knowledge graph '{request.graph_name}'",
                    data=None
                )
        
        # View knowledge graph statistics
        elif action == "view":
            if not request.graph_name:
                return ApiResponse(
                    success=False,
                    message="Graph name is required for view action",
                    data=None
                )
            
            # Get statistics for the specified graph
            graph_store = GraphStore(graph_name=request.graph_name)
            stats = graph_store.get_statistics()
            
            if stats:
                return ApiResponse(
                    success=True,
                    message=f"Retrieved statistics for knowledge graph '{request.graph_name}'",
                    data={"statistics": stats}
                )
            else:
                return ApiResponse(
                    success=False,
                    message=f"Failed to retrieve statistics for graph '{request.graph_name}'",
                    data=None
                )
        
        # Delete knowledge graph
        elif action == "delete":
            if not request.graph_name:
                return ApiResponse(
                    success=False,
                    message="Graph name is required for delete action",
                    data=None
                )
            
            # Delete the graph
            success = graph_store.delete_graph(request.graph_name)
            
            if success:
                return ApiResponse(
                    success=True,
                    message=f"Knowledge graph '{request.graph_name}' deleted successfully",
                    data=None
                )
            else:
                return ApiResponse(
                    success=False,
                    message=f"Failed to delete knowledge graph '{request.graph_name}'",
                    data=None
                )
        
        else:
            return ApiResponse(
                success=False,
                message=f"Invalid action: {action}. Must be 'create', 'list', 'view', or 'delete'",
                data=None
            )
        
    except Exception as e:
        logger.error(f"Error managing knowledge graph: {str(e)}")
        return ApiResponse(success=False, message=f"Error: {str(e)}", data=None)