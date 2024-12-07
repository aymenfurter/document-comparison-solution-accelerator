import pytest
from app.services.diffing import DiffEngine, compute_diff, ChangeType, Difference
import numpy as np

@pytest.fixture
def diff_engine():
    return DiffEngine()

def test_basic_difference_computation(diff_engine):
    original = ["The cat sat on the mat."]
    revised = ["The dog sat on the mat."]
    
    differences, similarity = diff_engine.compute_differences(original, revised)
    
    assert len(differences) == 1
    assert differences[0].change_type == ChangeType.MODIFIED
    assert differences[0].original == original[0]
    assert differences[0].revised == revised[0]
    assert 0.7 < similarity < 0.9  # Most chars are same

def test_empty_documents():
    result = compute_diff("", "")
    assert result["differences"] == []
    assert result["similarity_score"] == 1.0

def test_completely_different_documents(diff_engine):
    original = ["This is completely different."]
    revised = ["Nothing in common here."]
    
    differences, similarity = diff_engine.compute_differences(original, revised)
    
    assert len(differences) == 1
    assert differences[0].change_type == ChangeType.MODIFIED
    assert similarity < 0.5 

def test_multiple_paragraph_alignment(diff_engine):
    original = [
        "First paragraph.",
        "Second paragraph.",
        "Third paragraph."
    ]
    revised = [
        "First paragraph.",
        "New middle paragraph.",
        "Third paragraph."
    ]
    
    differences, similarity = diff_engine.compute_differences(original, revised)
    
    assert len(differences) == 1  # Only middle paragraph changed
    assert differences[0].original == "Second paragraph."
    assert differences[0].revised == "New middle paragraph."
    assert differences[0].paragraph_index == 1

def test_added_paragraph(diff_engine):
    original = ["First.", "Last."]
    revised = ["First.", "Middle.", "Last."]
    
    differences, similarity = diff_engine.compute_differences(original, revised)
    
    added = [d for d in differences if d.change_type == ChangeType.ADDED]
    assert len(added) == 1
    assert added[0].revised == "Middle."
    assert added[0].original == ""

def test_removed_paragraph(diff_engine):
    original = ["First.", "Middle.", "Last."]
    revised = ["First.", "Last."]
    
    differences, similarity = diff_engine.compute_differences(original, revised)
    
    removed = [d for d in differences if d.change_type == ChangeType.REMOVED]
    assert len(removed) == 1
    assert removed[0].original == "Middle."
    assert removed[0].revised == ""

def test_similarity_calculation(diff_engine):
    text1 = "The quick brown fox"
    text2 = "The quick brown fox"
    assert diff_engine._calculate_similarity(text1, text2) == 1.0
    
    text2 = "The slow brown fox"
    assert 0.7 < diff_engine._calculate_similarity(text1, text2) < 0.9
    
    text2 = "Completely different text"
    assert diff_engine._calculate_similarity(text1, text2) < 0.3

def test_optimal_alignment(diff_engine):
    # Test with known similarity matrix
    matrix = np.array([
        [0.9, 0.1, 0.1],
        [0.1, 0.8, 0.1],
        [0.1, 0.1, 0.9]
    ])
    
    original = ["A", "B", "C"]
    revised = ["A", "B", "C"]
    
    aligned = diff_engine._get_optimal_alignment(matrix, original, revised)
    assert len(aligned) == 3
    assert all(orig == rev for orig, rev in aligned)

def test_diff_id_generation(diff_engine):
    # Test that IDs are deterministic and unique
    id1 = diff_engine._generate_diff_id("test", 1)
    id2 = diff_engine._generate_diff_id("test", 1)
    id3 = diff_engine._generate_diff_id("test", 2)
    
    assert id1 == id2  # Same input should give same ID
    assert id1 != id3  # Different index should give different ID
    assert id1.startswith("diff-")  # Should follow format

def test_large_document_handling(diff_engine):
    # Test with larger documents to ensure performance
    original = ["Paragraph " + str(i) for i in range(100)]
    revised = ["Paragraph " + str(i) for i in range(100)]
    revised[50] = "Modified paragraph"
    
    differences, similarity = diff_engine.compute_differences(original, revised)
    
    assert len(differences) == 1  # Only one paragraph changed
    assert differences[0].paragraph_index == 50
    assert differences[0].change_type == ChangeType.MODIFIED
    assert 0.95 < similarity < 1.0  # High similarity due to single change

def test_error_handling():
    with pytest.raises(Exception):
        compute_diff(None, "valid")
    with pytest.raises(Exception):
        compute_diff("valid", None)

if __name__ == "__main__":
    pytest.main([__file__])