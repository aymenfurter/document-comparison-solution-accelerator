import pytest
from unittest.mock import Mock, patch, mock_open
from fastapi import HTTPException
from app.services.conversion import (
    convert_to_text,  # Changed from convert_to_html
    _convert_with_pandoc,
    _convert_with_azure_di,
    cleanup_temp_files,
    ConversionError
)
from app.core.config import settings  # Add settings import
import subprocess
import os
import tempfile
import shutil  # Add shutil for robust file operations

@pytest.fixture
def sample_docx():
    """Create a temporary DOCX file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
        tmp.write(b"Sample DOCX content")
        return tmp.name

@pytest.fixture
def mock_document_analysis_client():
    """Mock Azure Document Intelligence client"""
    class MockResult:
        class MockPage:
            class MockLine:
                def __init__(self, content):
                    self.content = content
            lines = [MockLine("Test content line 1"), MockLine("Test content line 2")]
        pages = [MockPage()]

    class MockPoller:
        def result(self):
            return MockResult()

    mock_client = Mock()
    mock_client.begin_analyze_document.return_value = MockPoller()
    return mock_client

def test_convert_with_pandoc_success(sample_docx):
    """Test successful Pandoc conversion"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = "Converted text"  # Changed from HTML
        result = _convert_with_pandoc(sample_docx)
        assert "Converted text" in result  # Changed assertion
        mock_run.assert_called_once()

def test_convert_with_pandoc_failure(sample_docx):
    """Test Pandoc conversion failure"""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, 'pandoc', stderr=b'Conversion failed')
        with pytest.raises(ConversionError) as exc_info:
            _convert_with_pandoc(sample_docx)
        assert 'Pandoc conversion failed' in str(exc_info.value)

def test_convert_with_azure_di_success(sample_docx, mock_document_analysis_client):
    """Test successful Azure Document Intelligence conversion"""
    with patch('app.services.conversion.settings') as mock_settings, \
         patch('app.services.conversion.DocumentAnalysisClient') as mock_client_class:
        mock_settings.AZURE_DOC_INTELLIGENCE_ENDPOINT = 'https://test.azure.com'
        mock_settings.AZURE_DOC_INTELLIGENCE_KEY = 'test-key'
        mock_client_class.return_value = mock_document_analysis_client
        
        result = _convert_with_azure_di(sample_docx)
        # Remove HTML assertions, check for plain text
        assert 'Test content line 1' in result
        assert 'Test content line 2' in result

def test_convert_with_azure_di_missing_credentials(sample_docx):
    """Test Azure DI conversion with missing credentials"""
    with patch('app.services.conversion.settings', autospec=True) as mock_settings:
        # Explicitly set credentials to None
        mock_settings.AZURE_DOC_INTELLIGENCE_ENDPOINT = None
        mock_settings.AZURE_DOC_INTELLIGENCE_KEY = None
        
        with pytest.raises(HTTPException) as exc_info:
            _convert_with_azure_di(sample_docx)
        
        assert exc_info.value.status_code == 500
        assert "credentials not configured" in str(exc_info.value.detail).lower()

def test_convert_with_azure_di_failure(sample_docx):
    """Test Azure DI conversion failure"""
    error_message = "Azure DI failed"
    with patch('app.services.conversion.settings') as mock_settings, \
         patch('app.services.conversion.DocumentAnalysisClient') as mock_client:
        # Configure mock settings
        mock_settings.AZURE_DOC_INTELLIGENCE_ENDPOINT = 'https://test.azure.com'
        mock_settings.AZURE_DOC_INTELLIGENCE_KEY = 'test-key'
        mock_client.side_effect = Exception(error_message)
        
        with pytest.raises(HTTPException) as exc_info:
            _convert_with_azure_di(sample_docx)
        assert exc_info.value.status_code == 500
        assert error_message in str(exc_info.value.detail)

def test_convert_to_text_pandoc_success(sample_docx):  # Changed from test_convert_to_html_pandoc_success
    """Test successful conversion using Pandoc"""
    with patch('app.services.conversion._convert_with_pandoc') as mock_pandoc:
        mock_pandoc.return_value = "Converted text"  # Changed from HTML
        result = convert_to_text(sample_docx)  # Changed from convert_to_html
        assert result == "Converted text"
        mock_pandoc.assert_called_once_with(sample_docx)

def test_convert_to_text_fallback_to_azure(sample_docx):  # Renamed function
    """Test fallback to Azure DI when Pandoc fails"""
    with patch('app.services.conversion._convert_with_pandoc') as mock_pandoc:
        with patch('app.services.conversion._convert_with_azure_di') as mock_azure:
            mock_pandoc.side_effect = ConversionError("Pandoc failed")
            mock_azure.return_value = "Azure Success Text"  # Changed from HTML
            
            result = convert_to_text(sample_docx)
            assert result == "Azure Success Text"
            mock_pandoc.assert_called_once()
            mock_azure.assert_called_once()

def test_cleanup_temp_files():
    """Test temporary file cleanup"""
    test_dir = tempfile.mkdtemp()
    test_files = ['test1.tmp', 'test2.tmp']
    
    # Create test files
    for file in test_files:
        file_path = os.path.join(test_dir, file)
        with open(file_path, 'w') as f:
            f.write('test')
    
    try:
        with patch('app.services.conversion.settings') as mock_settings:
            mock_settings.TEMP_DIR = test_dir
            cleanup_temp_files()
            # Verify files were deleted
            remaining_files = os.listdir(test_dir)
            assert len(remaining_files) == 0
    finally:
        # Ensure cleanup
        shutil.rmtree(test_dir, ignore_errors=True)

def test_cleanup_temp_files_handling_errors():
    """Test cleanup error handling"""
    with patch('os.listdir') as mock_listdir, \
         patch('os.path.isfile') as mock_isfile, \
         patch('os.unlink') as mock_unlink:
        
        mock_listdir.return_value = ['test.tmp']
        mock_isfile.return_value = True
        mock_unlink.side_effect = OSError("Permission denied")
        
        # Should not raise exception
        cleanup_temp_files()

def test_convert_to_html_both_methods_fail(sample_docx):
    """Test handling when both conversion methods fail"""
    with patch('app.services.conversion._convert_with_pandoc') as mock_pandoc:
        with patch('app.services.conversion._convert_with_azure_di') as mock_azure:
            mock_pandoc.side_effect = ConversionError("Pandoc failed")
            mock_azure.side_effect = HTTPException(status_code=500, detail="Azure failed")
            
            with pytest.raises(HTTPException) as exc_info:
                convert_to_text(sample_docx)  # Changed from convert_to_html
            assert exc_info.value.status_code == 500

@pytest.mark.parametrize("file_content", [
    b"Simple text",
    b"<h1>HTML content</h1>",
    b"Complex\nMultiline\nContent",
    b""  # Empty file
])
def test_convert_with_different_content_types(file_content):
    """Test conversion with different types of content"""
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
        tmp.write(file_content)
        tmp.flush()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = "Converted HTML"
            with patch('builtins.open', mock_open(read_data='<html>Converted</html>')):
                result = convert_to_text(tmp.name)  # Changed from convert_to_html
                assert result is not None
                assert isinstance(result, str)

if __name__ == "__main__":
    pytest.main([__file__])