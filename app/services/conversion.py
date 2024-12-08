import os
from typing import Optional
from fastapi import HTTPException
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult
from azure.core.credentials import AzureKeyCredential
from app.core.config import settings
import logging
import base64

logger = logging.getLogger(__name__)

def convert_to_text(docx_path: str) -> str:
    """
    Convert DOCX to plain text using Azure Document Intelligence
    """
    # Check credentials
    endpoint = settings.AZURE_DOC_INTELLIGENCE_ENDPOINT
    key = settings.AZURE_DOC_INTELLIGENCE_KEY
    
    if not endpoint or not key:
        raise HTTPException(
            status_code=500,
            detail="Azure Document Intelligence credentials not configured"
        )

    try:
        document_intelligence_client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )

        # Read file as bytes
        with open(docx_path, "rb") as f:
            file_bytes = f.read()

        # Create analyze request with bytes source
        analyze_request = AnalyzeDocumentRequest(
            bytes_source=file_bytes  # Changed from base64_source to bytes_source
        )

        # Start analysis
        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-layout",
            analyze_request
        )
        
        result: AnalyzeResult = poller.result()

        return result.content

    except Exception as e:
        logger.error(f"Azure Document Intelligence conversion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def cleanup_temp_files():
    """Clean up temporary files in the TEMP_DIR"""
    try:
        dir_path = settings.TEMP_DIR
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logger.debug(f"Removed file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete {file_path}: {str(e)}")
            os.sync()  # Ensure file system is synced
    except Exception as e:
        logger.error(f"Failed to cleanup temp files: {str(e)}")

class ConversionError(Exception):
    """Custom exception for conversion failures"""
    pass