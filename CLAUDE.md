# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run tests: `pytest`
- Run specific test file: `pytest tests/test_markdown_converter.py`
- Run specific test: `pytest tests/test_markdown_converter.py::test_clean_html`
- Run the application: `python main.py`
- Generate test coverage report: `pytest --cov=./ --cov-report=html`

## Code Style
- **Imports**: Standard library imports first, third-party imports second, local imports third, alphabetically sorted within each group
- **Type Hints**: Use Python type hints for function parameters and return values
- **Naming**: snake_case for variables/functions, CamelCase for classes, UPPER_CASE for constants
- **Error Handling**: Use try/except with specific exception types, log errors with proper context
- **Logging**: Use the logger from logging_config.py with appropriate log levels (debug, info, warning, error)
- **Documentation**: Use docstrings for modules, classes, and functions (Google style)
- **Testing**: Write unit tests with pytest, use fixtures for shared test data, mock external dependencies

## Best Practices
- Follow PEP 8 guidelines
- Use contextlib for resource management
- Implement proper exception handling and propagation
- Support graceful termination with signal handlers
- Use threading.Lock for thread safety when needed

## Project Structure
- `web/`: Web crawler and HTML processing
- `processors/`: Content processors including HTML to markdown conversion
- `knowledge_graph/`: Neo4j integration for knowledge graph creation
- `huggingface/`: Dataset creation and management
- `api/`: FastAPI server implementation
- `config/`: Configuration and credential management
- `utils/`: Utility functions and helpers
- `tests/`: Test suite