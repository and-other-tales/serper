#!/bin/bash

# Serper Application Startup Script
# This script starts the Serper application stack using Docker Compose

# Enable strict mode
set -e

# Print colored messages
print_message() {
  local color=$1
  local message=$2
  
  case $color in
    "green") echo -e "\033[0;32m$message\033[0m" ;;
    "yellow") echo -e "\033[0;33m$message\033[0m" ;;
    "red") echo -e "\033[0;31m$message\033[0m" ;;
    *) echo "$message" ;;
  esac
}

print_message "yellow" "=============================================="
print_message "yellow" "🚀 Starting Serper Application"
print_message "yellow" "=============================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
  print_message "red" "❌ Docker is not installed. Please install Docker first."
  exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
  print_message "red" "❌ Docker Compose is not installed. Please install Docker Compose first."
  exit 1
fi

# Check if .env file exists, create if not
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
  print_message "yellow" "📝 Creating .env file with default values..."
  cat > "$ENV_FILE" <<EOF
# Serper Environment Configuration
# Fill in your API keys below

# Required for Hugging Face dataset creation
HUGGINGFACE_TOKEN=

# Optional - Provides higher rate limits for GitHub API
GITHUB_TOKEN=

# Optional - Used for AI-powered features
OPENAI_API_KEY=

# Neo4j configuration (optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=
EOF
  print_message "green" "✅ Created .env file. Please edit it to add your API keys."
  print_message "yellow" "📝 File location: $ENV_FILE"
fi

# Run in the serper-app directory
cd "$(dirname "$0")"

# Build and start the containers
print_message "green" "🔨 Building and starting containers..."
docker-compose up -d --build

# Check if containers are running
if [ $? -eq 0 ]; then
  print_message "green" "✅ Serper application is now running!"
  print_message "green" "📊 Dashboard: http://localhost:3000"
  print_message "green" "💬 Chat Interface: http://localhost:3000/chat"
  print_message "green" "🔧 API: http://localhost:8080/api"

  # Check for missing API keys
  if ! grep -q "HUGGINGFACE_TOKEN=.*[^[:space:]]" "$ENV_FILE"; then
    print_message "yellow" "⚠️  Warning: HUGGINGFACE_TOKEN is not set in .env file."
    print_message "yellow" "   Some features might not work correctly."
  fi
else
  print_message "red" "❌ Failed to start Serper application."
  exit 1
fi

print_message "yellow" "=============================================="
print_message "yellow" "To stop the application, run: docker-compose down"
print_message "yellow" "=============================================="

exit 0