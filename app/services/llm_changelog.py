import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.core.config import settings
from app.services.llm_integration import client

logger = logging.getLogger(__name__)

class Change(BaseModel):
    description: str = Field(..., description="Description of the change")
    search_string: str = Field(..., description="Search term to search for in target document (typically 1-2 words)")
    context: str = Field(..., description="Richly formatted HTML context around the search string (For display to the user). Typically 3-5 sentences. Use various styles such as strikethrough and different colors. (Assume background is bright)")

class Changelog(BaseModel):
    summary: str = Field(..., description="Brief overview of all changes")
    changes: List[Change] = Field(..., description="List of significant changes with search contexts")

async def generate_changelog(diff_text: str) -> Dict[str, Any]:
    """Generate a structured changelog with searchable citations"""
    try:
        changelog = client.chat.completions.create(
            model=settings.AZURE_OPENAI_MODEL,
            response_model=Changelog,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise changelog generator that provides searchable citations. "
                        "For each change:\n"
                        "1. Describe the change clearly\n"
                        "2. Provide a search term / string (I can use to find the relevant part within the diff string) that is:\n"
                        "   - 1-2 words long\n"
                        "   - Continuous (not broken across paragraphs)\n"
                        "   - Unique enough to find the specific location\n"
                        "   - Present in the target document\n"
                        "3. Include surrounding context (Up to 5 sentences, but only include information that was provided) for display to the user, use HTML code for optimal presentation of the change. Users must be given enough context to understand the change.\n"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate a changelog with searchable citations.\n"
                        f"Diff:\n{diff_text}\n"
                    )
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
            "changes": []
        }