import logging
import subprocess
import threading
import time
import os
import ssl
import uuid
from fastapi import FastAPI, HTTPException, Depends, Header, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union, Callable

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

# Security headers middleware class
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Server"] = "Serper API"
        
        return response

# Rate limiting middleware class
class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Middleware to implement basic rate limiting."""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_tracker = {}  # Store IP address -> list of request timestamps
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if client is in tracker
        current_time = time.time()
        if client_ip not in self.request_tracker:
            self.request_tracker[client_ip] = []
        
        # Clean up old requests
        self.request_tracker[client_ip] = [
            timestamp for timestamp in self.request_tracker[client_ip]
            if current_time - timestamp < self.window_seconds
        ]
        
        # Check if client exceeded rate limit
        if len(self.request_tracker[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for client {client_ip}")
            return Response(
                content="Rate limit exceeded. Please try again later.",
                status_code=429,
                media_type="text/plain"
            )
        
        # Add current request to tracker
        self.request_tracker[client_ip].append(current_time)
        
        # Add rate limiting headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(self.max_requests - len(self.request_tracker[client_ip]))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_seconds))
        
        return response

# Initialize FastAPI app
app = FastAPI(
    title="othertales Serper API",
    description="Scrape websites to create datasets and knowledge graphs for machine learning and data analysis",
    version="1.0.0",
)

# Initialize templates
templates = Jinja2Templates(directory="web/templates")

# Add security middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitingMiddleware, max_requests=100, window_seconds=60)
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses over 1KB
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # Can be restricted in production

# Add CORS middleware for LLM tool compatibility
origins = ["*"]  # In production, restrict to specific domains

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

@app.get("/health", response_model=dict, summary="Health Check", tags=["Monitoring"])
async def health_check():
    """
    Health check endpoint for container orchestration and monitoring.
    
    This endpoint checks the health of all critical system components and dependencies:
    - API server status
    - Database connections (Neo4j)
    - External API access (GitHub, HuggingFace)
    - File system access
    
    Returns:
        dict: Health status information including component status and system metrics
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": app.version,
        "components": {
            "api_server": {"status": "up"},
            "file_system": {"status": "unknown"},
            "neo4j": {"status": "unknown"},
            "huggingface_api": {"status": "unknown"},
            "github_api": {"status": "unknown"},
        },
        "system": {
            "memory_usage": 0,
            "cpu_load": 0,
            "uptime_seconds": 0
        }
    }
    
    # Check file system access
    try:
        # Test file system by writing and reading a temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tmp.write(b"test")
            tmp.flush()
            with open(tmp.name, 'rb') as f:
                if f.read() == b"test":
                    health_status["components"]["file_system"]["status"] = "up"
                else:
                    health_status["components"]["file_system"]["status"] = "degraded"
    except Exception as e:
        health_status["components"]["file_system"] = {
            "status": "down",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Neo4j connection if available
    try:
        from knowledge_graph.graph_store import GraphStore
        graph_store = GraphStore()
        if graph_store.test_connection():
            health_status["components"]["neo4j"]["status"] = "up"
        else:
            health_status["components"]["neo4j"]["status"] = "down"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["neo4j"] = {
            "status": "down",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Hugging Face API access
    try:
        from config.credentials_manager import CredentialsManager
        credentials_manager = CredentialsManager()
        _, huggingface_token = credentials_manager.get_huggingface_credentials()
        
        if huggingface_token:
            from huggingface_hub import HfApi
            api = HfApi(token=huggingface_token)
            # Just make a simple API call to test access
            _ = api.whoami()
            health_status["components"]["huggingface_api"]["status"] = "up"
        else:
            health_status["components"]["huggingface_api"]["status"] = "unconfigured"
    except Exception as e:
        health_status["components"]["huggingface_api"] = {
            "status": "down",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check GitHub API access
    try:
        from github.client import GitHubClient
        client = GitHubClient()
        # Just make a simple API call to test access
        client.verify_credentials()
        health_status["components"]["github_api"]["status"] = "up"
    except Exception as e:
        health_status["components"]["github_api"] = {
            "status": "down",
            "error": str(e)
        }
        # This is not critical for most operations, so we don't degrade overall status
    
    # Get system metrics if psutil is available
    try:
        import psutil
        import datetime
        
        # Memory usage
        memory = psutil.virtual_memory()
        health_status["system"]["memory_usage"] = {
            "total_mb": memory.total / (1024 * 1024),
            "used_mb": memory.used / (1024 * 1024),
            "percent": memory.percent
        }
        
        # CPU load
        health_status["system"]["cpu_load"] = {
            "percent": psutil.cpu_percent(interval=0.1),
            "cores": psutil.cpu_count()
        }
        
        # Uptime
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time
        health_status["system"]["uptime_seconds"] = uptime.total_seconds()
        
    except ImportError:
        # psutil not available, skip system metrics
        pass
    
    # Return 503 Service Unavailable if status is not healthy
    if health_status["status"] != "healthy":
        from fastapi import status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is degraded or unhealthy"
        )
    
    return health_status


@app.post("/generate", response_model=ApiResponse, summary="Generate Dataset")
async def generate_dataset(
    request: GenerateDatasetRequest, api_key: str = Depends(verify_api_key)
):
    """
    Create and publish a new dataset on Hugging Face from  repository or organization content.
    
    This endpoint fetches code files from the specified  source, processes them,
    and publishes a structured dataset to Hugging Face with appropriate metadata.
    """
    try:
        # Import necessary components
        from .content_fetcher import ContentFetcher
        from huggingface.dataset_creator import DatasetCreator
        from config.credentials_manager import CredentialsManager

        credentials_manager = CredentialsManager()

        # Get credentials
        _username, _token = credentials_manager.get__credentials()
        if not _token:
            return ApiResponse(
                success=False,
                message=" token not found. Please configure credentials first.",
                data=None,
            )

        hf_username, huggingface_token = credentials_manager.get_huggingface_credentials()
        if not huggingface_token:
            return ApiResponse(
                success=False,
                message="Hugging Face token not found. Please configure credentials first.",
                data=None,
            )

        content_fetcher = ContentFetcher(_token=_token)
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


def start_server(api_key, host="0.0.0.0", port=8080, use_https=False, cert_file=None, key_file=None, with_ui=False):
    """
    Start the FastAPI server using Uvicorn with optional HTTPS support.
    
    Args:
        api_key: API key for authentication
        host: Host to bind the server to
        port: Port to bind the server to
        use_https: Whether to use HTTPS
        cert_file: Path to SSL certificate file (required if use_https is True)
        key_file: Path to SSL key file (required if use_https is True)
        with_ui: Whether to enable the web UI
        
    Returns:
        dict: Server status information or False if server couldn't be started
    """
    set_api_key(api_key)
    
    # Check if HTTPS parameters are valid
    if use_https and (not cert_file or not key_file):
        logger.error("HTTPS requested but certificate or key file not provided")
        return False
    
    # If HTTPS is requested, check that certificate and key files exist
    if use_https:
        if not os.path.exists(cert_file):
            logger.error(f"SSL certificate file not found: {cert_file}")
            return False
        if not os.path.exists(key_file):
            logger.error(f"SSL key file not found: {key_file}")
            return False
    
    # Mount static files and routes if UI is enabled
    if with_ui:
        # Mount static files
        app.mount("/static", StaticFiles(directory="web/static"), name="static")
        
        # Add UI routes
        @app.get("/", response_class=HTMLResponse)
        async def get_dashboard(request: Request):
            """Render the dashboard page"""
            # Get system status data
            from utils.task_tracker import TaskTracker
            task_tracker = TaskTracker()
            recent_tasks = task_tracker.list_resumable_tasks()[:5]
            cache_size = task_tracker.get_cache_size()
            
            # Get credentials status
            from config.credentials_manager import CredentialsManager
            credentials_manager = CredentialsManager()
            
            # Initialize status variables
            github_status = False
            huggingface_status = False
            neo4j_status = False
            
            # Check credentials
            try:
                # GitHub check
                from github.client import GitHubClient
                github_client = GitHubClient()
                github_status = github_client.verify_credentials()
            except:
                pass
                
            try:
                # Hugging Face check
                _, huggingface_token = credentials_manager.get_huggingface_credentials()
                huggingface_status = bool(huggingface_token)
            except:
                pass
                
            try:
                # Neo4j check
                from knowledge_graph.graph_store import GraphStore
                graph_store = GraphStore()
                neo4j_status = graph_store.test_connection()
            except:
                pass
                
            # Get server status
            server_running = is_server_running()
            
            # Render dashboard
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "server_status": server_running,
                "github_status": github_status,
                "huggingface_status": huggingface_status,
                "neo4j_status": neo4j_status,
                "recent_tasks": recent_tasks,
                "cache_size": cache_size,
                "dataset_count": 0,  # Would need to fetch actual count
                "server_port": port,
                "temp_dir": credentials_manager.get_temp_dir(),
                "active_page": "dashboard"
            })
        
        @app.get("/chat", response_class=HTMLResponse)
        async def get_chat(request: Request):
            """Render the chat interface page"""
            # Determine WebSocket URL
            protocol = "wss" if use_https else "ws"
            websocket_url = f"{protocol}://{request.headers.get('host', f'{host}:{port}')}/ws"
            
            return templates.TemplateResponse("chat.html", {
                "request": request,
                "active_page": "chat",
                "websocket_url": websocket_url
            })
        
        # Additional UI routes can be added here
        @app.get("/tasks", response_class=HTMLResponse)
        async def get_tasks(request: Request):
            """Render the tasks page"""
            # Get task data
            from utils.task_tracker import TaskTracker
            task_tracker = TaskTracker()
            tasks = task_tracker.list_resumable_tasks()
            
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "tasks": tasks,
                "active_page": "tasks"
            })
        
        @app.get("/configuration", response_class=HTMLResponse)
        async def get_configuration(request: Request):
            """Render the configuration page"""
            # Get configuration data
            from config.credentials_manager import CredentialsManager
            credentials_manager = CredentialsManager()
            
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "server_port": credentials_manager.get_server_port(),
                "temp_dir": credentials_manager.get_temp_dir(),
                "active_page": "configuration"
            })

    def run_server():
        import uvicorn
        
        server_status.running = True
        server_status.host = host
        server_status.port = port
        
        if use_https:
            # Configure SSL context
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(cert_file, key_file)
            
            # Log HTTPS server details
            logger.info(f"Starting HTTPS FastAPI server on {host}:{port}")
            logger.info(f"OpenAPI Schema available at: https://{host}:{port}/openapi.json")
            logger.info(f"API Documentation available at: https://{host}:{port}/docs")
            
            if with_ui:
                logger.info(f"Web UI available at: https://{host}:{port}/")
                logger.info(f"Chat Interface available at: https://{host}:{port}/chat")
            
            # Run with SSL context
            uvicorn.run(
                app, 
                host=host, 
                port=port, 
                log_level="info",
                ssl_certfile=cert_file,
                ssl_keyfile=key_file
            )
        else:
            # Log HTTP server details
            logger.info(f"Starting HTTP FastAPI server on {host}:{port}")
            logger.info(f"OpenAPI Schema available at: http://{host}:{port}/openapi.json")
            logger.info(f"API Documentation available at: http://{host}:{port}/docs")
            
            if with_ui:
                logger.info(f"Web UI available at: http://{host}:{port}/")
                logger.info(f"Chat Interface available at: http://{host}:{port}/chat")
                
            logger.warning("Running in HTTP mode. Consider using HTTPS for production deployments.")
            
            # Run without SSL
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
    
    # Protocol for URLs depends on whether we're using HTTPS
    protocol = "https" if use_https else "http"
    
    return {
        "status": "running",
        "host": host,
        "port": port,
        "protocol": protocol,
        "api_docs_url": f"{protocol}://{host}:{port}/docs",
        "openapi_url": f"{protocol}://{host}:{port}/openapi.json",
        "using_https": use_https,
        "web_ui": with_ui,
        "web_ui_url": f"{protocol}://{host}:{port}/" if with_ui else None,
        "chat_url": f"{protocol}://{host}:{port}/chat" if with_ui else None
    }

def start_server_with_ui(api_key=None, host="0.0.0.0", port=8080, use_https=False, cert_file=None, key_file=None):
    """
    Start the server with web UI enabled
    
    Args:
        api_key: API key for authentication
        host: Host to bind the server to
        port: Port to bind the server to
        use_https: Whether to use HTTPS
        cert_file: Path to SSL certificate file (required if use_https is True)
        key_file: Path to SSL key file (required if use_https is True)
        
    Returns:
        dict: Server status information or False if server couldn't be started
    """
    return start_server(api_key, host=host, port=port, use_https=use_https, 
                        cert_file=cert_file, key_file=key_file, with_ui=True)


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
    
    # Detect whether we're using HTTPS by checking for SSL context in Uvicorn
    using_https = False
    try:
        import inspect
        import uvicorn
        if server_status.server_thread and server_status.running:
            frames = inspect.stack()
            for frame in frames:
                if 'ssl_certfile' in frame.frame.f_locals:
                    using_https = True
                    break
    except Exception:
        pass
    
    # Use appropriate protocol
    protocol = "https" if using_https else "http"
    
    return {
        "status": "running" if server_status.running else "stopped",
        "host": host,
        "port": port,
        "protocol": protocol,
        "using_https": using_https,
        "api_docs_url": f"{protocol}://{host}:{port}/docs" if server_status.running else None,
        "openapi_url": f"{protocol}://{host}:{port}/openapi.json" if server_status.running else None
    }

# Chat WebSocket connection manager and handler
chat_handler = None

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for chat interface"""
    global chat_handler
    
    # Initialize chat handler if needed
    if chat_handler is None:
        from config.credentials_manager import CredentialsManager
        from web.chat_handler import ChatHandler
        credentials_manager = CredentialsManager()
        chat_handler = ChatHandler(credentials_manager)
    
    # Generate a unique client ID
    client_id = str(uuid.uuid4())
    
    try:
        # Accept connection
        await chat_handler.connect(websocket, client_id)
        
        # Process messages
        while True:
            message = await websocket.receive_text()
            await chat_handler.process_message(message, websocket)
    except WebSocketDisconnect:
        # Handle client disconnect
        await chat_handler.disconnect(client_id)
        logger.info(f"Client #{client_id} disconnected")
    except Exception as e:
        # Handle errors
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason=f"Error: {str(e)}")
        except:
            pass
        
        # Clean up connection
        await chat_handler.disconnect(client_id)


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