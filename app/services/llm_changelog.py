import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.core.config import settings
from app.services.llm_integration import client

logger = logging.getLogger(__name__)

class Changelog(BaseModel):
    summary: str = Field(..., description="Brief overview of all changes")
    changes: List[str] = Field(..., description="List of significant changes")
    verification_status: bool = Field(default=True, description="Whether changes have been verified")

async def generate_changelog(diff_text: str) -> Dict[str, Any]:
    """Generate a structured changelog from unified diff format using Instructor"""
    try:
        # Use Instructor's direct model response capability
        changelog = client.chat.completions.create(
            model=settings.AZURE_OPENAI_MODEL,
            response_model=Changelog,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise changelog generator. "
                        "Analyze the unified diff format and create a clear, "
                        "concise changelog focusing on meaningful changes."
                    )
                },
                {
                    "role": "user",
                    "content": f"Generate a changelog from this diff:\n\n{diff_text}"
                }
            ],
            temperature=0.1
        )
        
        return changelog.model_dump()
        
    except Exception as e:
        logger.error(f"Error generating changelog: {str(e)}")
        return {
            "error": "Failed to generate changelog",
            "details": str(e),
            "summary": "Error generating changelog",
            "changes": [],
            "verification_status": False
        }