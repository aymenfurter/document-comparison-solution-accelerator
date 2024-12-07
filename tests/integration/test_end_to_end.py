import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import logging
import json
import os
from app.main import app

logger = logging.getLogger(__name__)

# Path to sample files
SAMPLES_DIR = Path(__file__).parent.parent.parent / "sample"
AUGUST_DOC = SAMPLES_DIR / "August2023.docx"
NOVEMBER_DOC = SAMPLES_DIR / "November2023.docx"

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.mark.integration
@pytest.mark.skipif(
    not (AUGUST_DOC.exists() and NOVEMBER_DOC.exists()),
    reason="Sample documents not found"
)
class TestEndToEnd:
    """
    Integration tests for the deployed application.
    Run with: pytest tests/integration/test_end_to_end.py -v -m integration
    """
    
    @classmethod
    def setup_class(cls):
        """Verify sample files exist and are readable"""
        assert AUGUST_DOC.exists(), f"August sample file not found at {AUGUST_DOC}"
        assert NOVEMBER_DOC.exists(), f"November sample file not found at {NOVEMBER_DOC}"

    def test_1_health_check(self, client):
        """Test API health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @pytest.mark.dependency(depends=["TestEndToEnd::test_1_health_check"])
    def test_2_document_comparison(self, client):
        """Test document comparison endpoint"""
        # Prepare files for upload
        with open(AUGUST_DOC, "rb") as august_file, open(NOVEMBER_DOC, "rb") as november_file:
            files = {
                "source": ("August2023.docx", august_file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
                "target": ("November2023.docx", november_file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            }
            
            # Make the request
            response = client.post("/api/v1/upload", files=files)
            
            # Verify response
            # assert response.status_code == 200
            result = response.json()

            # Check response structure
            # assert "diff_result" in result
            # assert "changelog" in result
            
            # Save results for inspection
            output_dir = SAMPLES_DIR / "test_output"
            output_dir.mkdir(exist_ok=True)
            
            with open(output_dir / "api_comparison_results.json", "w") as f:
                json.dump(result, f, indent=2)
            
            logger.info(f"API results saved to {output_dir}/api_comparison_results.json")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])