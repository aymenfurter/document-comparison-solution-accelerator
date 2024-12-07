from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.services.conversion import convert_to_text
from app.services.diffing import compute_diff
from app.services.llm_changelog import generate_changelog
import tempfile
import os
from typing import List

router = APIRouter()

@router.post("/upload")
async def upload_documents(
    source: UploadFile = File(...),
    target: UploadFile = File(...)
):
    """Upload two documents for comparison"""
    # Validate file sizes
    for doc in [source, target]:
        if doc.size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        
        if not doc.filename.endswith('.docx'):
            raise HTTPException(status_code=400, detail="Only .docx files are supported")

    # Create temporary files
    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as source_tmp, \
         tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as target_tmp:
        
        # Save uploaded files
        source_content = await source.read()
        target_content = await target.read()
        source_tmp.write(source_content)
        target_tmp.write(target_content)
        
        try:
            # Convert to text
            source_text = convert_to_text(source_tmp.name)
            target_text = convert_to_text(target_tmp.name)
            
            # Compute diff
            diff_result = compute_diff(source_text, target_text)
            
            # Generate changelog using LLM
            if diff_result["similarity_score"] >= settings.SIMILARITY_THRESHOLD:
                changelog = await generate_changelog(diff_result["diff_text"])
            else:
                changelog = {"warning": "Documents appear to be unrelated"}

            return {
                "diff_text": diff_result["diff_text"],
                "similarity_score": diff_result["similarity_score"],
                "changelog": changelog,
                "warning": diff_result["similarity_score"] < settings.SIMILARITY_THRESHOLD
            }
            
        finally:
            # Cleanup temporary files
            os.unlink(source_tmp.name)
            os.unlink(target_tmp.name)

@router.get("/status/{job_id}")
async def get_comparison_status(job_id: str):
    """Get the status of an ongoing comparison"""
    # For future implementation of async processing
    return {"status": "not_implemented"}