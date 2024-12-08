from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import aiohttp
from urllib.parse import urlparse
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.services.conversion import convert_to_text
from app.services.diffing import compute_diff
from app.services.llm_changelog import generate_changelog
import tempfile
import os
from typing import List

router = APIRouter()

async def validate_microsoft_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc.endswith('microsoft.com')

async def download_file(url: str) -> bytes:
    if not await validate_microsoft_url(url):
        raise HTTPException(status_code=400, detail="Only Microsoft URLs are allowed")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise HTTPException(status_code=400, detail="Failed to download file")
            return await response.read()

@router.post("/upload")
async def upload_documents(
    source: UploadFile | None = None,
    target: UploadFile | None = None,
    source_url: str | None = Form(None),
    target_url: str | None = Form(None)
):
    """Upload or provide URLs for two documents to compare"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as source_tmp, \
             tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as target_tmp:
            
            # Handle source document
            if source:
                source_content = await source.read()
            elif source_url:
                source_content = await download_file(source_url)
            else:
                raise HTTPException(status_code=400, detail="No source document provided")

            # Handle target document
            if target:
                target_content = await target.read()
            elif target_url:
                target_content = await download_file(target_url)
            else:
                raise HTTPException(status_code=400, detail="No target document provided")

            # Write content to temp files
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}")
async def get_comparison_status(job_id: str):
    """Get the status of an ongoing comparison"""
    # For future implementation of async processing
    return {"status": "not_implemented"}