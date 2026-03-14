"""
Configuration Management for SBN ChatAgent
Centralized configuration using pydantic-settings
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings with validation.
    Loads from environment variables and .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application Settings
    app_host: str = Field(default="0.0.0.0", description="Host to bind the application")
    app_port: int = Field(default=3030, ge=1, le=65535, description="Port to bind the application")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Ollama Settings
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama server URL")
    ollama_model: str = Field(default="qwen2.5:0.5b", description="Ollama model to use")
    ollama_timeout: float = Field(default=30.0, ge=1, description="Ollama request timeout")

    # Internal API Settings
    internal_api_url: str = Field(default="http://localhost:8000/api/products", description="Internal API base URL")
    internal_api_timeout: float = Field(default=10.0, ge=1, description="Internal API request timeout")

    # ChromaDB Settings
    chroma_persist_dir: str = Field(default="./data/chroma", description="ChromaDB persistence directory")

    # Rate Limiting Settings
    rate_limit_requests: int = Field(default=10, ge=1, description="Rate limit: requests per window")
    rate_limit_window: int = Field(default=60, ge=1, description="Rate limit: window in seconds")

    # Conversation Settings
    max_conversation_history: int = Field(default=10, ge=1, le=50, description="Max messages per conversation")
    max_message_length: int = Field(default=2000, ge=100, description="Max message length")

    @field_validator('ollama_host')
    @classmethod
    def validate_ollama_host(cls, v: str) -> str:
        """Validate Ollama host URL format"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("OLLAMA_HOST must start with http:// or https://")
        return v.rstrip('/')

    @field_validator('internal_api_url')
    @classmethod
    def validate_internal_api_url(cls, v: str) -> str:
        """Validate internal API URL format"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("INTERNAL_API_URL must start with http:// or https://")
        return v.rstrip('/')

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(valid_levels)}")
        return v_upper

    @property
    def ollama_base_url(self) -> str:
        """Get Ollama base URL without trailing slash"""
        return self.ollama_host.rstrip('/')

    def get_ollama_embeddings_url(self) -> str:
        """Get full URL for Ollama embeddings endpoint"""
        return f"{self.ollama_base_url}/api/embeddings"

    def get_ollama_generate_url(self) -> str:
        """Get full URL for Ollama generate endpoint"""
        return f"{self.ollama_base_url}/api/generate"

    def get_ollama_tags_url(self) -> str:
        """Get full URL for Ollama tags endpoint"""
        return f"{self.ollama_base_url}/api/tags"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment"""
    global settings
    settings = Settings()
    return settings
