import logging
from typing import Dict, Any
from openai import AzureOpenAI
from app.core.config import settings
import instructor

logger = logging.getLogger(__name__)

# Initialize Azure OpenAI client with Instructor
base_client = AzureOpenAI(
    api_key=settings.AZURE_OPENAI_KEY,  
    api_version=settings.AZURE_OPENAI_API_VERSION,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
)

# Patch the client with Instructor
client = instructor.from_openai(base_client)

def validate_api_configuration() -> bool:
    """Validate Azure OpenAI configuration"""
    required_settings = [
        settings.AZURE_OPENAI_KEY,
        settings.AZURE_OPENAI_ENDPOINT,
        settings.AZURE_OPENAI_MODEL,
        settings.AZURE_OPENAI_API_VERSION
    ]
    return all(required_settings)

async def health_check() -> Dict[str, Any]:
    """Perform health check of Azure OpenAI integration"""
    try:
        response = client.chat.completions.create(
            model=settings.AZURE_OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Respond with 'ok' if you receive this message."},
                {"role": "user", "content": "Health check"}
            ],
            temperature=0.1
        )
        return {
            "status": "healthy",
            "message": "Azure OpenAI connection successful"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Azure OpenAI connection failed: {str(e)}"
        }