"""Simplified configuration management for pgvector MCP server."""

import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Simplified application settings - only essential configuration required from MCP client environment."""

    def __init__(self):
        # Essential configuration - must be provided by MCP client environment
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError(
                "DATABASE_URL environment variable is required. "
                "Please configure it in your MCP client environment (e.g., Claude Desktop)."
            )
        self.database_url: str = database_url

        dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
        if not dashscope_api_key:
            raise ValueError(
                "DASHSCOPE_API_KEY environment variable is required. "
                "Please configure your DashScope API key in your MCP client environment."
            )
        self.dashscope_api_key: str = dashscope_api_key

        # Optional configuration with sensible defaults
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.dashscope_base_url: str = os.getenv(
            "DASHSCOPE_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # Technical constants - DashScope embedding dimensions
        self.default_dimension: int = 1024  # Fixed for DashScope text-embedding-v3
        self.max_chunk_size: int = 8192     # DashScope token limit
        self.default_chunk_overlap: int = 200  # Optimal overlap for context preservation

def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
