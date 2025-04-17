# Serper Web UI

This is the Next.js frontend for the Serper application, a system that creates datasets from GitHub repositories and websites for use with AI models.

## Features

- Modern responsive UI built with Next.js, React, TypeScript, and Tailwind CSS
- Task management with human-in-the-loop capabilities
- Chat interface for interacting with the Serper AI
- Dashboard for system monitoring and task tracking
- GitHub repository and web crawling dataset creation
- Integration with the Serper backend API

## Getting Started

### Prerequisites

- Node.js 18.x or higher
- Serper backend running (default on port 8080)

### Installation

1. Install dependencies:

```bash
npm install
# or
yarn install
# or
pnpm install
```

2. Run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

3. Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Project Structure

- `/src/app`: Next.js app router and page components
- `/src/components`: React components organized by feature
- `/src/hooks`: Custom React hooks
- `/src/lib`: Utility functions and shared code
- `/src/providers`: React context providers
- `/public`: Static assets

## Key Components

- Dashboard: System monitoring and quick actions
- Task Management: Managing dataset creation tasks
- Chat Interface: AI-powered assistant for interacting with Serper
- Configuration: Managing API keys and system settings
- Human-in-the-Loop: Task review and approval interface

## API Integration

The web UI communicates with the Serper backend API through:

1. RESTful API calls for data operations
2. WebSocket connection for real-time chat and task updates

## Development Notes

- The application uses WebSockets for real-time communication with the Serper AI assistant
- Task management includes a human-in-the-loop system for tasks that require human intervention
- Configuration settings are stored in browser localStorage for persistence
- The UI is fully responsive and works on mobile devices