import subprocess
import os
from typing import Optional
from fastapi import HTTPException
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class ConversionError(Exception):
    """Custom exception for conversion failures"""
    pass

def convert_to_text(docx_path: str) -> str:
    """
    Convert DOCX to plain text using Pandoc with Azure Document Intelligence fallback
    """
    try:
        return _convert_with_pandoc(docx_path)
    except ConversionError as e:
        logger.warning(f"Pandoc conversion failed: {e}. Falling back to Azure Document Intelligence.")
        return _convert_with_azure_di(docx_path)

def _convert_with_pandoc(docx_path: str) -> str:
    """
    Convert DOCX to plain text using Pandoc
    """
    try:
        cmd = [
            settings.PANDOC_PATH,
            docx_path,
            '-f', 'docx',
            '-t', 'plain',
            '--wrap=none'
        ]
        
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return process.stdout
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Pandoc conversion failed: {e.stderr}")
        raise ConversionError(f"Pandoc conversion failed: {e.stderr}")

def _convert_with_azure_di(docx_path: str) -> str:
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
        document_analysis_client = DocumentAnalysisClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )

        with open(docx_path, "rb") as f:
            poller = document_analysis_client.begin_analyze_document(
                "prebuilt-document", f
            )
        result = poller.result()

        # Extract text content
        text_content = []
        for page in result.pages:
            for line in page.lines:
                text_content.append(line.content)
        
        return '\n'.join(text_content)

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