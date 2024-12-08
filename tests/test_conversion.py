from typing import Generator
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from azure.core.exceptions import ServiceRequestError
from app.services.conversion import (
    convert_to_text,
    cleanup_temp_files,
    ConversionError
)
from pathlib import Path
import tempfile

@pytest.fixture
def sample_docx() -> Generator[str, None, None]:
    """Create a temporary DOCX file for testing"""
    tmp_path = Path(tempfile.mkdtemp()) / "test.docx"
    tmp_path.write_bytes(b"Sample DOCX content")
    yield str(tmp_path)
    tmp_path.unlink(missing_ok=True)

@pytest.fixture
def mock_document_intelligence_client() -> Mock:
    """Mock Azure Document Intelligence client"""
    mock_result = Mock()
    mock_result.content = "Test content line 1\nTest content line 2"
    
    mock_poller = Mock()
    mock_poller.result.return_value = mock_result
    
    mock_client = Mock()
    mock_client.begin_analyze_document.return_value = mock_poller
    return mock_client

def test_convert_to_text_success(sample_docx: str, mock_document_intelligence_client: Mock) -> None:
    """Test successful document conversion"""
    with patch('app.services.conversion.DocumentIntelligenceClient') as mock_client_class:
        mock_client_class.return_value = mock_document_intelligence_client
        
        result = convert_to_text(sample_docx)
        assert "Test content line 1" in result
        assert "Test content line 2" in result
        mock_document_intelligence_client.begin_analyze_document.assert_called_once()

@pytest.mark.parametrize("error,expected_message", [
    (ServiceRequestError("Connection error"), "Connection error"),
    (ValueError("Invalid input"), "Invalid input"),
    (Exception("Unexpected error"), "Unexpected error"),
])
def test_convert_to_text_errors(
    sample_docx: str,
    error: Exception,
    expected_message: str
) -> None:
    """Test various conversion error scenarios"""
    with patch('app.services.conversion.DocumentIntelligenceClient') as mock_client_class:
        mock_client_class.side_effect = error
        with pytest.raises(HTTPException) as exc_info:
            convert_to_text(sample_docx)
        assert expected_message in str(exc_info.value.detail)
        assert exc_info.value.status_code == 500

def test_convert_to_text_missing_credentials(sample_docx: str) -> None:
    """Test conversion with missing Azure credentials"""
    with patch('app.services.conversion.settings') as mock_settings:
        mock_settings.AZURE_DOC_INTELLIGENCE_ENDPOINT = None
        mock_settings.AZURE_DOC_INTELLIGENCE_KEY = None
        
        with pytest.raises(HTTPException) as exc_info:
            convert_to_text(sample_docx)
        assert "credentials not configured" in str(exc_info.value.detail).lower()
        assert exc_info.value.status_code == 500

def test_cleanup_temp_files(tmp_path: Path) -> None:
    """Test temporary file cleanup"""
    test_files = ['test1.tmp', 'test2.tmp']
    
    # Create test files
    for file in test_files:
        (tmp_path / file).write_text('test')
    
    with patch('app.services.conversion.settings') as mock_settings:
        mock_settings.TEMP_DIR = str(tmp_path)
        cleanup_temp_files()
        
        # Verify cleanup
        remaining_files = list(tmp_path.glob('*.tmp'))
        assert len(remaining_files) == 0

@pytest.mark.parametrize("file_content,expected_contains", [
    (b"Simple text", "Simple text"),
    (b"<h1>HTML content</h1>", "HTML content"),
    (b"Complex\nMultiline\nContent", "Complex"),
])
def test_convert_with_different_contents(
    tmp_path: Path,
    file_content: bytes,
    expected_contains: str
) -> None:
    """Test conversion with different content types"""
    test_file = tmp_path / "test.docx"
    test_file.write_bytes(file_content)
    
    with patch('app.services.conversion.DocumentIntelligenceClient') as mock_client_class:
        mock_result = Mock()
        mock_result.content = expected_contains
        mock_poller = Mock()
        mock_poller.result.return_value = mock_result
        mock_client = Mock()
        mock_client.begin_analyze_document.return_value = mock_poller
        mock_client_class.return_value = mock_client
        
        result = convert_to_text(str(test_file))
        assert expected_contains in result

def test_cleanup_temp_files_with_errors(tmp_path: Path) -> None:
    """Test cleanup with file deletion errors"""
    with patch('app.services.conversion.settings') as mock_settings, \
         patch('os.remove') as mock_remove:
        
        mock_settings.TEMP_DIR = str(tmp_path)
        mock_remove.side_effect = OSError("Permission denied")
        
        # Should not raise exception
        cleanup_temp_files()