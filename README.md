# OtherTales Serper

A versatile web scraping and documentation processing tool for creating datasets and knowledge graphs.

## Features

- **Web Crawling**: Scrape websites with Playwright and BeautifulSoup for complete content extraction
- **Advanced HTML to Markdown**: Convert web content to clean markdown with jinaai/ReaderLM-v2
- **Knowledge Graph Generation**: Create Neo4j-based knowledge graphs from web content for advanced querying
- **Dataset Creation**: Generate Hugging Face datasets for AI model training
- **Multiple Knowledge Graphs**: Create and manage separate knowledge graphs for different domains
- **OpenAPI Integration**: Access all functionality through a RESTful API

## Requirements

- Python 3.9+
- Neo4j (optional, for knowledge graph functionality)
- CUDA-compatible GPU (optional, for faster processing)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/othertales/serper.git
cd serper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Install Playwright browsers:
```bash
playwright install
```

4. (Optional) Start Neo4j database:
```bash
# Docker example
docker run \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -d \
    -e NEO4J_AUTH=neo4j/password \
    neo4j:latest
```

## Usage

### Command Line Interface

Start the CLI with:
```bash
python main.py
```

The interactive CLI provides options for:
- Scraping & Crawling websites
- Managing existing datasets
- Configuring knowledge graphs
- Setting up scheduled scraping tasks
- Managing API credentials

### API Server

Start the API server with:
```bash
python main.py server start
```

Or through the CLI menu.

## Use Cases

1. **Documentation Knowledge Base**
   - Scrape documentation websites and convert to structured markdown
   - Create searchable knowledge graphs of technical concepts
   - Generate datasets for fine-tuning specialized LLMs

2. **Legal and Regulatory Content**
   - Create comprehensive knowledge graphs from legal and governmental websites
   - Generate structured datasets of laws, regulations, and procedures
   - Enable advanced querying of legal relationships and concepts

3. **Research and Academic Content**
   - Scrape and structure research papers and academic resources
   - Build knowledge graphs of academic concepts and relationships
   - Create specialized training datasets for research domains

## HTML to Markdown Conversion

The application uses a state-of-the-art ReaderLM-v2 model from Jina AI to convert HTML content to high-quality markdown:

- **Advanced Formatting**: Preserves complex elements like tables, code blocks, and lists
- **Content Extraction**: Intelligently focuses on the main content, removing distractions
- **Multilingual Support**: Works with content in multiple languages 
- **Fallback Methods**: Uses graceful degradation with alternative conversion methods if needed

## Knowledge Graph Features

- **Multiple Graphs**: Create separate knowledge graphs for different domains
- **Entity Extraction**: Automatically extract named entities and concepts
- **Relationship Mapping**: Build connections between documents and concepts
- **Neo4j Integration**: Leverage the power of Neo4j's graph database capabilities
- **Visual Exploration**: Explore relationships through Neo4j's visualization tools

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.