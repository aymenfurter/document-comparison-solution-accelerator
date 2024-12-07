import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.services.llm_integration import client

logger = logging.getLogger(__name__)

class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    REFORMATTED = "reformatted"
    MOVED = "moved"

class ContentType(str, Enum):
    TEXT = "text"
    HEADING = "heading"
    LIST = "list"
    TABLE = "table"

class DiffContext(BaseModel):
    section_heading: Optional[str] = Field(None, description="The heading under which this change occurs")
    paragraph_before: Optional[str] = Field(None, description="Content immediately before the change")
    paragraph_after: Optional[str] = Field(None, description="Content immediately after the change")
    content_type: ContentType = Field(..., description="Type of content being changed")

class ChangeDetails(BaseModel):
    id: str = Field(..., description="Unique identifier for the change")
    description: str = Field(..., description="Clear, concise description of what changed")
    change_type: ChangeType
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for this change")
    context: DiffContext
    impact: str = Field(..., description="The semantic impact of this change")

class ChangeGroup(BaseModel):
    title: str = Field(..., description="Short title describing this group of changes")
    changes: List[ChangeDetails]
    section: Optional[str] = Field(None, description="Document section this group belongs to")

class Changelog(BaseModel):
    groups: List[ChangeGroup] = Field(..., description="Grouped changes for better organization")
    summary: str = Field(..., description="Brief overview of all changes")
    total_changes: int = Field(..., description="Total number of changes")
    verification_status: bool = Field(..., description="Whether changes have been verified")

async def generate_changelog(differences: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a structured changelog using Azure OpenAI"""
    try:
        # Initial analysis with structured output
        completion = client.chat.completions.parse(
            model=settings.AZURE_OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Analyze document changes and generate a structured changelog."
                },
                {
                    "role": "user",
                    "content": f"Generate a changelog from these differences: {differences}"
                }
            ],
            response_format=Changelog,
            temperature=0.1
        )
        
        # Parse and validate the response
        changelog = Changelog.model_validate(completion.choices[0].message.parsed)
        
        # Verify citations and accuracy
        verified = await _verify_changelog(changelog, differences)
        
        return verified.model_dump()
        
    except Exception as e:
        logger.error(f"Error generating changelog: {str(e)}")
        return {"error": "Failed to generate changelog", "details": str(e)}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def _verify_changelog(changelog: Changelog, original_diffs: List[Dict[str, Any]]) -> Changelog:
    """Verify changelog accuracy and citations"""
    try:
        completion = client.chat.completions.parse(
            model=settings.AZURE_OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Verify changelog accuracy and citations."
                },
                {
                    "role": "user",
                    "content": f"Verify this changelog against the original differences:\n\n"
                              f"Changelog: {changelog.model_dump_json()}\n\n"
                              f"Original differences: {original_diffs}"
                }
            ],
            response_format=Changelog,
            temperature=0.1
        )
        
        return Changelog.model_validate(completion.choices[0].message.parsed)
        
    except Exception as e:
        logger.error(f"Changelog verification failed: {str(e)}")
        raise