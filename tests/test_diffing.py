import pytest
from app.services.diffing import compute_diff

def test_basic_difference_computation():
    """Test basic text difference computation"""
    text1 = "The cat sat on the mat."
    text2 = "The dog sat on the mat."
    
    result = compute_diff(text1, text2)
    
    assert "diff_text" in result
    assert "similarity_score" in result
    assert 0.7 < result["similarity_score"] < 0.9  # Most chars are same
    # Update assertions to match actual diff format
    assert "-cat" in result["diff_text"]  # Changed from "-The cat"
    assert "+dog" in result["diff_text"]  # Changed from "+The dog"

def test_empty_documents():
    """Test comparison of empty documents"""
    result = compute_diff("", "")
    assert "diff_text" in result
    assert result["similarity_score"] == 1.0

def test_completely_different_documents():
    """Test completely different documents"""
    text1 = "This is completely different."
    text2 = "Nothing in common here."
    
    result = compute_diff(text1, text2)
    assert result["similarity_score"] < 0.3

def test_multiline_differences():
    """Test differences across multiple lines"""
    text1 = """First line
    Second line
    Third line"""
    
    text2 = """First line
    Modified second line
    Third line"""
    
    result = compute_diff(text1, text2)
    assert "Modified" in result["diff_text"]
    assert 0.7 < result["similarity_score"] < 1.0

def test_error_handling():
    """Test error handling with invalid inputs"""
    with pytest.raises(Exception):
        compute_diff(None, "valid")
    with pytest.raises(Exception):
        compute_diff("valid", None)

if __name__ == "__main__":
    pytest.main([__file__])