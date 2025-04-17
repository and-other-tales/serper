"""LLM client module supporting both Anthropic Claude and OpenAI models."""

import json
import os
import logging
from enum import Enum
from typing import Dict, Any, Optional, List, Union

import requests
from pydantic import BaseModel, Field

# Try to import langchain-related modules
# Fail gracefully if not available
LANGCHAIN_AVAILABLE = False
try:
    from langchain_anthropic import ChatAnthropic
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.pydantic_v1 import BaseModel as LCBaseModel
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# Try to import direct API clients
# Fail gracefully if not available
ANTHROPIC_AVAILABLE = False
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

OPENAI_AVAILABLE = False
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class CrawlInstructionsSchema(BaseModel):
    """Schema for web crawler instructions."""
    
    should_crawl_recursively: bool = Field(
        default=True,
        description="Whether to recursively crawl linked pages"
    )
    max_pages: int = Field(
        default=100,
        description="Maximum number of pages to crawl"
    )
    same_domain_only: bool = Field(
        default=True,
        description="Whether to only crawl pages on the same domain"
    )
    content_selectors: List[str] = Field(
        default_factory=list,
        description="CSS selectors to focus on for extracting content"
    )
    extraction_goal: str = Field(
        default="general",
        description="Goal of extraction: 'general', 'specific_content', or 'full_text'"
    )
    filters: List[str] = Field(
        default_factory=list,
        description="Criteria to filter content"
    )
    priority_content: List[str] = Field(
        default_factory=list,
        description="Keywords or patterns to prioritize when crawling"
    )


class GitHubInstructionsSchema(BaseModel):
    """Schema for GitHub repository fetching instructions."""
    
    file_patterns: List[str] = Field(
        default_factory=list,
        description="File patterns to prioritize (e.g. '*.md', '*.py')"
    )
    exclude_patterns: List[str] = Field(
        default_factory=list,
        description="File patterns to exclude (e.g. 'test_*', '*.log')"
    )
    max_files: int = Field(
        default=1000,
        description="Maximum number of files to fetch"
    )
    include_directories: List[str] = Field(
        default_factory=list,
        description="Directories to prioritize for inclusion"
    )
    exclude_directories: List[str] = Field(
        default_factory=list,
        description="Directories to exclude completely"
    )
    extraction_goal: str = Field(
        default="general",
        description="Goal of extraction: 'documentation', 'code', 'data', or 'general'"
    )
    priority_content: List[str] = Field(
        default_factory=list,
        description="Keywords or patterns to prioritize when fetching repository content"
    )


class LLMClient:
    """LLM client for generating instructions for web crawling and GitHub repository fetching."""

    def __init__(
        self, 
        provider: str = None,
        anthropic_api_key: str = None,
        openai_api_key: str = None,
        anthropic_model: str = "claude-3-sonnet-20240229",
        openai_model: str = "gpt-3.5-turbo"
    ):
        """
        Initialize the LLM client.
        
        Args:
            provider: The LLM provider to use ("anthropic" or "openai")
            anthropic_api_key: The Anthropic API key
            openai_api_key: The OpenAI API key
            anthropic_model: The Anthropic model to use
            openai_model: The OpenAI model to use
        """
        self.provider = provider or os.environ.get("LLM_PROVIDER", "anthropic")
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.anthropic_model = anthropic_model
        self.openai_model = openai_model
        
        # Check API keys
        if self.provider == LLMProvider.ANTHROPIC and not self.anthropic_api_key:
            logger.warning("Anthropic API key not found. Will fall back to OpenAI if available.")
            if self.openai_api_key:
                logger.info("Falling back to OpenAI")
                self.provider = LLMProvider.OPENAI
        
        if self.provider == LLMProvider.OPENAI and not self.openai_api_key:
            logger.warning("OpenAI API key not found. Will fall back to Anthropic if available.")
            if self.anthropic_api_key:
                logger.info("Falling back to Anthropic")
                self.provider = LLMProvider.ANTHROPIC
        
        # Initialize clients based on available dependencies
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize API clients based on available dependencies."""
        self.langchain_client = None
        self.direct_client = None
        
        if self.provider == LLMProvider.ANTHROPIC:
            if LANGCHAIN_AVAILABLE:
                try:
                    self.langchain_client = ChatAnthropic(
                        model=self.anthropic_model,
                        anthropic_api_key=self.anthropic_api_key,
                        default_headers={"anthropic-beta": "tools-2024-04-04"},
                    )
                    logger.info(f"Initialized langchain Anthropic client with model {self.anthropic_model}")
                except Exception as e:
                    logger.error(f"Failed to initialize langchain Anthropic client: {e}")
            
            if ANTHROPIC_AVAILABLE:
                try:
                    self.direct_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
                    logger.info(f"Initialized direct Anthropic client with model {self.anthropic_model}")
                except Exception as e:
                    logger.error(f"Failed to initialize direct Anthropic client: {e}")
        
        elif self.provider == LLMProvider.OPENAI:
            if OPENAI_AVAILABLE:
                try:
                    self.direct_client = openai.OpenAI(api_key=self.openai_api_key)
                    logger.info(f"Initialized direct OpenAI client with model {self.openai_model}")
                except Exception as e:
                    logger.error(f"Failed to initialize direct OpenAI client: {e}")
                    
    def _generate_structured_crawler_instructions_langchain(self, user_input: str, url: str) -> Dict[str, Any]:
        """
        Generate structured crawler instructions using langchain.
        
        Args:
            user_input: The user's description of what they want to extract
            url: The URL to crawl
            
        Returns:
            Dict: Structured crawler instructions
        """
        if not self.langchain_client:
            logger.error("Langchain client not available")
            return {}
        
        # Define structured output schema
        if self.provider == LLMProvider.ANTHROPIC:
            class CrawlInstructions(LCBaseModel):
                """Schema for crawler instructions."""
                should_crawl_recursively: bool = Field(description="Whether to recursively crawl linked pages")
                max_pages: int = Field(description="Maximum number of pages to crawl")
                same_domain_only: bool = Field(description="Whether to only crawl pages on the same domain")
                content_selectors: List[str] = Field(description="CSS selectors to focus on for extracting content")
                extraction_goal: str = Field(description="Goal of extraction: 'general', 'specific_content', or 'full_text'")
                filters: List[str] = Field(description="Criteria to filter content")
                priority_content: List[str] = Field(description="Keywords or patterns to prioritize when crawling")
            
            # Create structured output client
            structured_llm = self.langchain_client.with_structured_output(CrawlInstructions, include_raw=True)
            
            # Create the prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert web crawler instruction generator. 
                 Your task is to analyze the user's intent for web scraping and provide specific instructions for the web crawler."""),
                ("user", f"""I want to crawl this URL: {url}

I need: {user_input}

Please provide detailed instructions for the web crawler.""")
            ])
            
            # Generate and parse response
            try:
                result = (prompt | structured_llm).invoke({})
                if "parsed" in result and result["parsed"]:
                    return result["parsed"].dict()
                else:
                    logger.warning("Failed to get structured output from Anthropic")
                    if "raw" in result:
                        logger.debug(f"Raw output: {result['raw']}")
                    return {}
            except Exception as e:
                logger.error(f"Error generating structured output with langchain: {e}")
                return {}
        else:
            logger.warning("Langchain structured output only supported for Anthropic")
            return {}
            
    def _generate_crawler_instructions_anthropic(self, user_input: str, url: str) -> Dict[str, Any]:
        """
        Generate crawler instructions using Anthropic API directly.
        
        Args:
            user_input: The user's description of what they want to extract
            url: The URL to crawl
            
        Returns:
            Dict: Structured crawler instructions
        """
        if not self.direct_client:
            logger.error("Anthropic client not available")
            return {}
        
        system_prompt = """You are an expert web crawler instruction generator. 
Your task is to analyze the user's intent for web scraping and provide specific instructions for the web crawler.
Return your response as a JSON object with the following fields:
- should_crawl_recursively (boolean): Whether to recursively crawl linked pages
- max_pages (integer): Maximum number of pages to crawl
- same_domain_only (boolean): Whether to only crawl pages on the same domain
- content_selectors (array of strings): CSS selectors to focus on for extracting content
- extraction_goal (string: 'general', 'specific_content', 'full_text'): The goal of extraction
- filters (array of strings): Criteria to filter content
- priority_content (array of strings): Keywords or patterns to prioritize when crawling"""
        
        user_message = f"""I want to crawl this URL: {url}

I need: {user_input}

Please provide detailed instructions for my web crawler in JSON format."""
        
        try:
            # Use tool calling for Claude
            response = self.direct_client.messages.create(
                model=self.anthropic_model,
                messages=[
                    {"role": "user", "content": user_message}
                ],
                system=system_prompt,
                tools=[{
                    "name": "crawler_instructions",
                    "description": "Generate instructions for a web crawler",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "should_crawl_recursively": {
                                "type": "boolean",
                                "description": "Whether to recursively crawl linked pages"
                            },
                            "max_pages": {
                                "type": "integer",
                                "description": "Maximum number of pages to crawl"
                            },
                            "same_domain_only": {
                                "type": "boolean",
                                "description": "Whether to only crawl pages on the same domain"
                            },
                            "content_selectors": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "CSS selectors to focus on for extracting content"
                            },
                            "extraction_goal": {
                                "type": "string",
                                "description": "Goal of extraction: 'general', 'specific_content', or 'full_text'"
                            },
                            "filters": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Criteria to filter content"
                            },
                            "priority_content": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Keywords or patterns to prioritize when crawling"
                            }
                        },
                        "required": ["should_crawl_recursively", "max_pages", "same_domain_only"]
                    }
                }],
                max_tokens=4096,
                temperature=0.2
            )
            
            # Check if tool call was used
            for content_block in response.content:
                if content_block.type == "tool_use":
                    return content_block.input
            
            # If no tool call, try to extract JSON from text
            text_content = response.content[0].text
            try:
                # Try to find JSON in the response
                json_start = text_content.find('{')
                json_end = text_content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = text_content[json_start:json_end]
                    return json.loads(json_str)
                else:
                    logger.warning("Couldn't find JSON in Anthropic response")
                    return {}
            except Exception as e:
                logger.error(f"Error parsing JSON from Anthropic response: {e}")
                return {}
                
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {e}")
            return {}
            
    def _generate_crawler_instructions_openai(self, user_input: str, url: str) -> Dict[str, Any]:
        """
        Generate crawler instructions using OpenAI API.
        
        Args:
            user_input: The user's description of what they want to extract
            url: The URL to crawl
            
        Returns:
            Dict: Structured crawler instructions
        """
        if not self.direct_client:
            logger.error("OpenAI client not available")
            return {}
        
        system_prompt = """You are an expert web crawler instruction generator. 
Your task is to analyze the user's intent for web scraping and provide specific instructions for the web crawler."""
        
        user_message = f"""I want to crawl this URL: {url}

I need: {user_input}

Please provide detailed instructions for my web crawler in JSON format. Include the following fields:
- should_crawl_recursively (boolean): Whether to recursively crawl linked pages
- max_pages (integer): Maximum number of pages to crawl
- same_domain_only (boolean): Whether to only crawl pages on the same domain
- content_selectors (array of strings): CSS selectors to focus on for extracting content
- extraction_goal (string: 'general', 'specific_content', 'full_text'): The goal of extraction
- filters (array of strings): Criteria to filter content
- priority_content (array of strings): Keywords or patterns to prioritize when crawling"""
        
        try:
            # Call OpenAI with function calling
            response = self.direct_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                functions=[{
                    "name": "crawler_instructions",
                    "description": "Generate instructions for a web crawler",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "should_crawl_recursively": {
                                "type": "boolean",
                                "description": "Whether to recursively crawl linked pages"
                            },
                            "max_pages": {
                                "type": "integer",
                                "description": "Maximum number of pages to crawl"
                            },
                            "same_domain_only": {
                                "type": "boolean",
                                "description": "Whether to only crawl pages on the same domain"
                            },
                            "content_selectors": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "CSS selectors to focus on for extracting content"
                            },
                            "extraction_goal": {
                                "type": "string",
                                "description": "Goal of extraction: 'general', 'specific_content', or 'full_text'"
                            },
                            "filters": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Criteria to filter content"
                            },
                            "priority_content": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Keywords or patterns to prioritize when crawling"
                            }
                        },
                        "required": ["should_crawl_recursively", "max_pages", "same_domain_only"]
                    }
                }],
                function_call={"name": "crawler_instructions"},
                temperature=0.2
            )
            
            # Extract and parse the function call
            function_call = response.choices[0].message.function_call
            if function_call and function_call.name == "crawler_instructions":
                return json.loads(function_call.arguments)
            
            # If for some reason function calling didn't work, try to parse from message
            message_content = response.choices[0].message.content
            if message_content:
                try:
                    # Try to find JSON in the response
                    json_start = message_content.find('{')
                    json_end = message_content.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = message_content[json_start:json_end]
                        return json.loads(json_str)
                except Exception as e:
                    logger.error(f"Error parsing JSON from OpenAI response: {e}")
            
            return {}
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return {}
            
    def _generate_crawler_instructions_rest_api(self, user_input: str, url: str) -> Dict[str, Any]:
        """
        Generate crawler instructions using a basic REST API approach with either provider.
        This is a fallback method if the specific API integrations fail.
        
        Args:
            user_input: The user's description of what they want to extract
            url: The URL to crawl
            
        Returns:
            Dict: Structured crawler instructions
        """
        # Default instructions if API call fails
        default_instructions = {
            "should_crawl_recursively": True,
            "max_pages": 100,
            "same_domain_only": True,
            "content_selectors": [],
            "extraction_goal": "general",
            "filters": [],
            "priority_content": []
        }
        
        try:
            if self.provider == LLMProvider.ANTHROPIC:
                endpoint = "https://api.anthropic.com/v1/messages"
                headers = {
                    "Content-Type": "application/json",
                    "X-API-Key": self.anthropic_api_key,
                    "anthropic-version": "2023-06-01"
                }
                
                system_prompt = """You are an expert web crawler instruction generator. 
Your task is to analyze the user's intent for web scraping and provide specific instructions for the web crawler.
Return your response as a JSON object with the following fields:
- should_crawl_recursively (boolean): Whether to recursively crawl linked pages
- max_pages (integer): Maximum number of pages to crawl
- same_domain_only (boolean): Whether to only crawl pages on the same domain
- content_selectors (array of strings): CSS selectors to focus on for extracting content
- extraction_goal (string: 'general', 'specific_content', 'full_text'): The goal of extraction
- filters (array of strings): Criteria to filter content
- priority_content (array of strings): Keywords or patterns to prioritize when crawling"""
                
                payload = {
                    "model": self.anthropic_model,
                    "messages": [
                        {
                            "role": "user", 
                            "content": f"I want to crawl this URL: {url}\n\nI need: {user_input}\n\nPlease provide detailed instructions for my web crawler in JSON format."
                        }
                    ],
                    "system": system_prompt,
                    "max_tokens": 1024,
                    "temperature": 0.2
                }
                
            elif self.provider == LLMProvider.OPENAI:
                endpoint = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_api_key}"
                }
                
                payload = {
                    "model": self.openai_model,
                    "messages": [
                        {
                            "role": "system", 
                            "content": """You are an expert web crawler instruction generator. 
Your task is to analyze the user's intent for web scraping and provide specific instructions for the web crawler."""
                        },
                        {
                            "role": "user", 
                            "content": f"""I want to crawl this URL: {url}

I need: {user_input}

Please provide detailed instructions for my web crawler in JSON format. Include the following fields:
- should_crawl_recursively (boolean): Whether to recursively crawl linked pages
- max_pages (integer): Maximum number of pages to crawl
- same_domain_only (boolean): Whether to only crawl pages on the same domain
- content_selectors (array of strings): CSS selectors to focus on for extracting content
- extraction_goal (string: 'general', 'specific_content', 'full_text'): The goal of extraction
- filters (array of strings): Criteria to filter content
- priority_content (array of strings): Keywords or patterns to prioritize when crawling"""
                        }
                    ],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"}
                }
                
            else:
                logger.error(f"Unsupported provider: {self.provider}")
                return default_instructions
            
            # Make API call
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Parse based on provider
                if self.provider == LLMProvider.ANTHROPIC:
                    content = result.get("content", [{}])[0].get("text", "")
                elif self.provider == LLMProvider.OPENAI:
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Try to parse JSON from text
                try:
                    # Extract JSON part if it's in a markdown code block
                    if "```json" in content:
                        json_start = content.find("```json") + 7
                        json_end = content.find("```", json_start)
                        json_str = content[json_start:json_end].strip()
                    else:
                        # Try to find JSON in the response
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = content[json_start:json_end]
                        else:
                            logger.warning(f"Couldn't find JSON in response from {self.provider}")
                            return default_instructions
                    
                    # Parse the JSON
                    instructions = json.loads(json_str)
                    
                    # Validate and set defaults for missing fields
                    if "should_crawl_recursively" not in instructions:
                        instructions["should_crawl_recursively"] = default_instructions["should_crawl_recursively"]
                    if "max_pages" not in instructions:
                        instructions["max_pages"] = default_instructions["max_pages"]
                    if "same_domain_only" not in instructions:
                        instructions["same_domain_only"] = default_instructions["same_domain_only"]
                    if "content_selectors" not in instructions:
                        instructions["content_selectors"] = default_instructions["content_selectors"]
                    if "extraction_goal" not in instructions:
                        instructions["extraction_goal"] = default_instructions["extraction_goal"]
                    if "filters" not in instructions:
                        instructions["filters"] = default_instructions["filters"]
                    if "priority_content" not in instructions:
                        instructions["priority_content"] = default_instructions["priority_content"]
                        
                    return instructions
                        
                except Exception as e:
                    logger.error(f"Error parsing JSON from response: {e}")
                    return default_instructions
            
            logger.warning(f"Failed to get response from {self.provider}: {response.status_code}")
            return default_instructions
            
        except Exception as e:
            logger.error(f"Error making API call to {self.provider}: {e}")
            return default_instructions
    
    def _generate_github_instructions_anthropic(self, user_input: str, repo_url: str) -> Dict[str, Any]:
        """
        Generate GitHub repository instructions using Anthropic API directly.
        
        Args:
            user_input: The user's description of what they want to extract
            repo_url: The GitHub repository URL
            
        Returns:
            Dict: Structured GitHub instructions
        """
        if not self.direct_client:
            logger.error("Anthropic client not available")
            return {}
        
        system_prompt = """You are an expert GitHub repository analyzer. 
Your task is to analyze the user's intent for extracting data from a GitHub repository and provide specific instructions.
Return your response as a JSON object with the following fields:
- file_patterns (array of strings): File patterns to prioritize (e.g. '*.md', '*.py')
- exclude_patterns (array of strings): File patterns to exclude (e.g. 'test_*', '*.log')
- max_files (integer): Maximum number of files to fetch
- include_directories (array of strings): Directories to prioritize for inclusion
- exclude_directories (array of strings): Directories to exclude completely
- extraction_goal (string: 'documentation', 'code', 'data', 'general'): The goal of extraction
- priority_content (array of strings): Keywords or patterns to prioritize when fetching repository content"""
        
        user_message = f"""I want to extract data from this GitHub repository: {repo_url}

I need: {user_input}

Please provide detailed instructions for repository content extraction in JSON format."""
        
        try:
            # Use tool calling for Claude
            response = self.direct_client.messages.create(
                model=self.anthropic_model,
                messages=[
                    {"role": "user", "content": user_message}
                ],
                system=system_prompt,
                tools=[{
                    "name": "github_instructions",
                    "description": "Generate instructions for GitHub repository extraction",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "file_patterns": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "File patterns to prioritize (e.g. '*.md', '*.py')"
                            },
                            "exclude_patterns": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "File patterns to exclude (e.g. 'test_*', '*.log')"
                            },
                            "max_files": {
                                "type": "integer",
                                "description": "Maximum number of files to fetch"
                            },
                            "include_directories": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Directories to prioritize for inclusion"
                            },
                            "exclude_directories": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Directories to exclude completely"
                            },
                            "extraction_goal": {
                                "type": "string",
                                "description": "Goal of extraction: 'documentation', 'code', 'data', or 'general'"
                            },
                            "priority_content": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Keywords or patterns to prioritize when fetching repository content"
                            }
                        },
                        "required": ["file_patterns", "extraction_goal"]
                    }
                }],
                max_tokens=4096,
                temperature=0.2
            )
            
            # Check if tool call was used
            for content_block in response.content:
                if content_block.type == "tool_use":
                    return content_block.input
            
            # If no tool call, try to extract JSON from text
            text_content = response.content[0].text
            try:
                # Try to find JSON in the response
                json_start = text_content.find('{')
                json_end = text_content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = text_content[json_start:json_end]
                    return json.loads(json_str)
                else:
                    logger.warning("Couldn't find JSON in Anthropic response")
                    return {}
            except Exception as e:
                logger.error(f"Error parsing JSON from Anthropic response: {e}")
                return {}
                
        except Exception as e:
            logger.error(f"Error calling Anthropic API for GitHub instructions: {e}")
            return {}
            
    def _generate_github_instructions_openai(self, user_input: str, repo_url: str) -> Dict[str, Any]:
        """
        Generate GitHub repository instructions using OpenAI API.
        
        Args:
            user_input: The user's description of what they want to extract
            repo_url: The GitHub repository URL
            
        Returns:
            Dict: Structured GitHub instructions
        """
        if not self.direct_client:
            logger.error("OpenAI client not available")
            return {}
        
        system_prompt = """You are an expert GitHub repository analyzer. 
Your task is to analyze the user's intent for extracting data from a GitHub repository and provide specific instructions."""
        
        user_message = f"""I want to extract data from this GitHub repository: {repo_url}

I need: {user_input}

Please provide detailed instructions for repository content extraction in JSON format. Include the following fields:
- file_patterns (array of strings): File patterns to prioritize (e.g. '*.md', '*.py')
- exclude_patterns (array of strings): File patterns to exclude (e.g. 'test_*', '*.log')
- max_files (integer): Maximum number of files to fetch
- include_directories (array of strings): Directories to prioritize for inclusion
- exclude_directories (array of strings): Directories to exclude completely
- extraction_goal (string: 'documentation', 'code', 'data', 'general'): The goal of extraction
- priority_content (array of strings): Keywords or patterns to prioritize when fetching repository content"""
        
        try:
            # Call OpenAI with function calling
            response = self.direct_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                functions=[{
                    "name": "github_instructions",
                    "description": "Generate instructions for GitHub repository extraction",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_patterns": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "File patterns to prioritize (e.g. '*.md', '*.py')"
                            },
                            "exclude_patterns": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "File patterns to exclude (e.g. 'test_*', '*.log')"
                            },
                            "max_files": {
                                "type": "integer",
                                "description": "Maximum number of files to fetch"
                            },
                            "include_directories": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Directories to prioritize for inclusion"
                            },
                            "exclude_directories": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Directories to exclude completely"
                            },
                            "extraction_goal": {
                                "type": "string",
                                "description": "Goal of extraction: 'documentation', 'code', 'data', or 'general'"
                            },
                            "priority_content": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Keywords or patterns to prioritize when fetching repository content"
                            }
                        },
                        "required": ["file_patterns", "extraction_goal"]
                    }
                }],
                function_call={"name": "github_instructions"},
                temperature=0.2
            )
            
            # Extract and parse the function call
            function_call = response.choices[0].message.function_call
            if function_call and function_call.name == "github_instructions":
                return json.loads(function_call.arguments)
            
            # If for some reason function calling didn't work, try to parse from message
            message_content = response.choices[0].message.content
            if message_content:
                try:
                    # Try to find JSON in the response
                    json_start = message_content.find('{')
                    json_end = message_content.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = message_content[json_start:json_end]
                        return json.loads(json_str)
                except Exception as e:
                    logger.error(f"Error parsing JSON from OpenAI response: {e}")
            
            return {}
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API for GitHub instructions: {e}")
            return {}
    
    def generate_github_instructions(self, user_input: str, repo_url: str) -> Dict[str, Any]:
        """
        Generate GitHub repository instructions using the configured LLM provider.
        
        Args:
            user_input: The user's description of what they want to extract
            repo_url: The GitHub repository URL
            
        Returns:
            Dict: Structured GitHub repository instructions
        """
        logger.info(f"Generating GitHub repository instructions using {self.provider}")
        
        # Default instructions if all methods fail
        default_instructions = {
            "file_patterns": ["*.md", "*.txt", "*.py", "*.js", "*.html", "*.css"],
            "exclude_patterns": ["node_modules/*", "*.min.js", "*.min.css", "vendor/*"],
            "max_files": 1000,
            "include_directories": [],
            "exclude_directories": [".git", "node_modules", "vendor", "dist", "build"],
            "extraction_goal": "general",
            "priority_content": []
        }
        
        # Try different methods in order of preference
        if self.provider == LLMProvider.ANTHROPIC:
            # Try with direct Anthropic API
            if ANTHROPIC_AVAILABLE and self.direct_client:
                try:
                    logger.debug("Trying direct Anthropic API for GitHub instructions")
                    result = self._generate_github_instructions_anthropic(user_input, repo_url)
                    if result:
                        return result
                except Exception as e:
                    logger.warning(f"Error using direct Anthropic API for GitHub instructions: {e}")
                
        elif self.provider == LLMProvider.OPENAI:
            # Try with direct OpenAI API
            if OPENAI_AVAILABLE and self.direct_client:
                try:
                    logger.debug("Trying direct OpenAI API for GitHub instructions")
                    result = self._generate_github_instructions_openai(user_input, repo_url)
                    if result:
                        return result
                except Exception as e:
                    logger.warning(f"Error using direct OpenAI API for GitHub instructions: {e}")
        
        logger.warning("Failed to generate GitHub instructions, using default")
        return default_instructions
        
    def generate_crawler_instructions(self, user_input: str, url: str) -> Dict[str, Any]:
        """
        Generate crawler instructions using the configured LLM provider.
        
        Args:
            user_input: The user's description of what they want to extract
            url: The URL to crawl
            
        Returns:
            Dict: Structured crawler instructions
        """
        logger.info(f"Generating crawler instructions using {self.provider}")
        
        # Default instructions if all methods fail
        default_instructions = {
            "should_crawl_recursively": True,
            "max_pages": 100,
            "same_domain_only": True,
            "content_selectors": [],
            "extraction_goal": "general",
            "filters": [],
            "priority_content": []
        }
        
        # Try different methods in order of preference
        if self.provider == LLMProvider.ANTHROPIC:
            # Try with langchain structured output first
            if LANGCHAIN_AVAILABLE and self.langchain_client:
                try:
                    logger.debug("Trying langchain Anthropic structured output")
                    result = self._generate_structured_crawler_instructions_langchain(user_input, url)
                    if result:
                        return result
                except Exception as e:
                    logger.warning(f"Error using langchain Anthropic structured output: {e}")
            
            # Try with direct Anthropic API next
            if ANTHROPIC_AVAILABLE and self.direct_client:
                try:
                    logger.debug("Trying direct Anthropic API")
                    result = self._generate_crawler_instructions_anthropic(user_input, url)
                    if result:
                        return result
                except Exception as e:
                    logger.warning(f"Error using direct Anthropic API: {e}")
            
            # Fall back to REST API
            try:
                logger.debug("Trying REST API with Anthropic")
                result = self._generate_crawler_instructions_rest_api(user_input, url)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Error using REST API with Anthropic: {e}")
                
        elif self.provider == LLMProvider.OPENAI:
            # Try with direct OpenAI API first
            if OPENAI_AVAILABLE and self.direct_client:
                try:
                    logger.debug("Trying direct OpenAI API")
                    result = self._generate_crawler_instructions_openai(user_input, url)
                    if result:
                        return result
                except Exception as e:
                    logger.warning(f"Error using direct OpenAI API: {e}")
            
            # Fall back to REST API
            try:
                logger.debug("Trying REST API with OpenAI")
                result = self._generate_crawler_instructions_rest_api(user_input, url)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Error using REST API with OpenAI: {e}")
        
        logger.warning("All methods failed, using default instructions")
        return default_instructions