from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
import os
import tempfile

class Settings(BaseSettings):
    # Environment flag
    ENV: str = "development"

    # Azure OpenAI Settings
    AZURE_OPENAI_ENDPOINT: str = "https://test-endpoint.openai.azure.com"  # Test default
    AZURE_OPENAI_KEY: str = "test-key-1234"  # Test default
    AZURE_OPENAI_MODEL: str = "gpt-4o"
    AZURE_OPENAI_API_VERSION: str = "2024-10-21"
    
    # Azure Document Intelligence Settings
    AZURE_DOC_INTELLIGENCE_ENDPOINT: Optional[str] = None
    AZURE_DOC_INTELLIGENCE_KEY: Optional[str] = None
    
    # Pandoc Settings
    PANDOC_PATH: str = "pandoc"  # Assumes pandoc is in PATH
    TEMP_DIR: str = "/tmp/doc-comparison"
    
    # Comparison Settings
    SIMILARITY_THRESHOLD: float = 0.3  # Below this, documents are considered unrelated
    MAX_DIFF_SIZE: int = 1000000  # Maximum size of diff to process
    
    # API Settings
    MAX_UPLOAD_SIZE: int = 40 * 1024 * 1024  # 40MB
    
    @field_validator('TEMP_DIR')
    @classmethod
    def create_temp_dir(cls, v):
        os.makedirs(v, exist_ok=True)
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        # Allow environment variables to override .env file
        env_prefix = ""
        # Allow missing .env file
        validate_default = True

# Create settings instance
settings = Settings()

# Override settings for testing
if os.getenv("PYTEST_CURRENT_TEST"):
    settings.ENV = "test"
    # Use in-memory temp directory for tests
    settings.TEMP_DIR = os.path.join(tempfile.gettempdir(), "doc-comparison-test")