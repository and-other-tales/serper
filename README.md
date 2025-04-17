# Serper - AI Dataset Generator

This is the main application directory containing both the backend Python services and the frontend Next.js application.

## Structure

```
├── backend/              # Python backend services
│   ├── api/              # FastAPI server implementation
│   ├── config/           # Configuration and credential management
│   ├── exceptions/       # Custom exception classes
│   ├── github/           # GitHub API integration
│   ├── huggingface/      # HuggingFace dataset tools
│   ├── knowledge_graph/  # Neo4j integration
│   ├── processors/       # Content processors and converters
│   ├── utils/            # Utility functions and helpers
│   ├── tests/            # Test suite
│   ├── Dockerfile        # Backend Docker configuration
│   ├── main.py           # Application entry point
│   └── requirements.txt  # Python dependencies
├── frontend/             # Next.js frontend application
│   ├── public/           # Static files
│   ├── src/              # React components and pages
│   ├── Dockerfile        # Frontend Docker configuration
│   └── ...               # Next.js configuration files
├── docker-compose.yml    # Docker Compose configuration
└── start.sh              # Start script for the application
```

## Quick Start

To run the application:

```bash
# Make sure the script is executable
chmod +x start.sh

# Start the application
./start.sh
```

This will:
1. Set up necessary environment variables
2. Build and start Docker containers for both frontend and backend
3. Provide URLs for accessing the web interface and API

## Access Points

- Dashboard: http://localhost:3000
- Chat Interface: http://localhost:3000/chat
- API: http://localhost:8080/api
- API Documentation: http://localhost:8080/docs

## Development Setup

### Backend (Python)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py web
```

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

## Configuration

Configure the application by editing the `.env` file in the root directory. This file is automatically created by the start script if it doesn't exist.

Important environment variables:
- `HUGGINGFACE_TOKEN`: Required for dataset creation
- `GITHUB_TOKEN`: Optional, provides higher API rate limits
- `OPENAI_API_KEY`: Optional, used for AI-powered features
- `NEO4J_*`: Optional, for knowledge graph functionality