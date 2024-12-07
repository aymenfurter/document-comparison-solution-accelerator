
import logging
from typing import Dict, Any, Optional
from openai import AzureOpenAI
from app.core.config import settings
import backoff
import json

logger = logging.getLogger(__name__)

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=settings.AZURE_OPENAI_KEY,  
    api_version=settings.AZURE_OPENAI_API_VERSION,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
)

@backoff.on_exception(
    backoff.expo,
    (Exception),
    max_tries=3,
    max_time=30
)
async def send_prompt(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 2000,
    temperature: float = 0.1,
    response_format: Optional[Any] = None
) -> str:
    """
    Send prompt to Azure OpenAI with backoff retry logic
    """
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Prepare completion parameters
        params = {
            "model": settings.AZURE_OPENAI_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Add response format if specified
        if response_format:
            params["response_format"] = {"type": "json_object"}
            
        # Send request to Azure OpenAI
        response = client.chat.completions.create(**params)
        
        # Extract and validate response
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from Azure OpenAI")
            
        # Validate JSON if response format is specified
        if response_format:
            try:
                json.loads(content)
            except json.JSONDecodeError:
                raise ValueError("Response is not valid JSON")
                
        return content

    except Exception as e:
        logger.error(f"Error in Azure OpenAI request: {str(e)}")
        raise

def validate_api_configuration() -> bool:
    """
    Validate Azure OpenAI configuration
    """
    required_settings = [
        settings.AZURE_OPENAI_KEY,
        settings.AZURE_OPENAI_ENDPOINT,
        settings.AZURE_OPENAI_MODEL,
        settings.AZURE_OPENAI_API_VERSION
    ]
    
    return all(required_settings)

async def health_check() -> Dict[str, Any]:
    """
    Perform health check of Azure OpenAI integration
    """
    try:
        response = await send_prompt(
            system_prompt="Respond with 'ok' if you receive this message.",
            user_prompt="Health check",
            max_tokens=10
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