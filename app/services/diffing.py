from diff_match_patch import diff_match_patch
from typing import List, Dict, Tuple, Any
import hashlib
import logging
from app.core.config import settings
import numpy as np
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ChangeType(Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"

@dataclass
class Difference:
    id: str
    original: str
    revised: str
    change_type: ChangeType
    paragraph_index: int
    
class DiffEngine:
    def __init__(self):
        self.dmp = diff_match_patch()
        self.dmp.Diff_Timeout = 5.0  # 5 second timeout for diff computation
        
    def compute_differences(self, original_blocks: List[str], revised_blocks: List[str]) -> Tuple[List[Difference], float]:
        """Compute differences between text blocks"""
        try:
            # Handle empty/None cases
            if original_blocks is None or revised_blocks is None:
                raise ValueError("Input blocks cannot be None")

            if not original_blocks and not revised_blocks:
                return [], 1.0

            # Simple cases
            if not original_blocks or not revised_blocks:
                return self._handle_empty_blocks(original_blocks, revised_blocks)

            # Build similarity matrix and find best alignments
            matrix = np.zeros((len(original_blocks), len(revised_blocks)))
            for i, orig in enumerate(original_blocks):
                for j, rev in enumerate(revised_blocks):
                    matrix[i, j] = self._calculate_similarity(orig, rev)

            differences = []
            total_chars = 0
            matched_chars = 0

            # Find matching blocks first
            matched_orig = set()
            matched_rev = set()

            # Match highly similar blocks first
            for i in range(len(original_blocks)):
                for j in range(len(revised_blocks)):
                    if i not in matched_orig and j not in matched_rev:
                        sim = matrix[i, j]
                        if sim > settings.SIMILARITY_THRESHOLD:
                            if not self._has_exact_match(original_blocks[i], revised_blocks[j]):
                                differences.append(Difference(
                                    id=self._generate_diff_id(original_blocks[i] + revised_blocks[j], i),
                                    original=original_blocks[i],
                                    revised=revised_blocks[j],
                                    change_type=ChangeType.MODIFIED,
                                    paragraph_index=i
                                ))
                            matched_orig.add(i)
                            matched_rev.add(j)
                            total_chars += len(original_blocks[i]) + len(revised_blocks[j])
                            matched_chars += 2 * sim * max(len(original_blocks[i]), len(revised_blocks[j]))

            # Handle unmatched blocks
            for i in range(len(original_blocks)):
                if i not in matched_orig:
                    differences.append(Difference(
                        id=self._generate_diff_id(original_blocks[i], i),
                        original=original_blocks[i],
                        revised="",
                        change_type=ChangeType.REMOVED,
                        paragraph_index=i
                    ))
                    total_chars += len(original_blocks[i])

            for j in range(len(revised_blocks)):
                if j not in matched_rev:
                    differences.append(Difference(
                        id=self._generate_diff_id(revised_blocks[j], j),
                        original="",
                        revised=revised_blocks[j],
                        change_type=ChangeType.ADDED,
                        paragraph_index=j
                    ))
                    total_chars += len(revised_blocks[j])

            similarity = matched_chars / total_chars if total_chars > 0 else 1.0
            return differences, similarity

        except Exception as e:
            logger.error(f"Error computing differences: {str(e)}")
            raise ValueError(f"Failed to compute differences: {str(e)}")

    def _align_paragraphs(self, original_blocks: List[str], revised_blocks: List[str]) -> List[Tuple[str, str]]:
        """
        Align paragraphs using similarity matching
        """
        if not original_blocks and not revised_blocks:
            return []
            
        # Create similarity matrix
        matrix = np.zeros((len(original_blocks), len(revised_blocks)))
        for i, orig in enumerate(original_blocks):
            for j, rev in enumerate(revised_blocks):
                matrix[i, j] = self._calculate_similarity(orig, rev)
        
        # Use dynamic programming to find optimal alignment
        aligned_pairs = self._get_optimal_alignment(matrix, original_blocks, revised_blocks)
        return aligned_pairs
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text blocks"""
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0

        diffs = self.dmp.diff_main(text1, text2)
        self.dmp.diff_cleanupSemantic(diffs)

        common_chars = sum(len(text) for op, text in diffs if op == 0)
        total_chars = len(text1) + len(text2)

        # Calculate Levenshtein-based similarity
        return (2.0 * common_chars) / total_chars if total_chars > 0 else 1.0

    def _get_optimal_alignment(self, matrix: np.ndarray, original_blocks: List[str], 
                             revised_blocks: List[str]) -> List[Tuple[str, str]]:
        """Find optimal alignment between blocks"""
        m, n = matrix.shape
        aligned_pairs: List[Tuple[str, str]] = []
        used_orig = set()
        used_rev = set()

        # Find best matches first
        pairs = [(i, j, matrix[i, j]) for i in range(m) for j in range(n)]
        pairs.sort(key=lambda x: x[2], reverse=True)

        for i, j, sim in pairs:
            if i not in used_orig and j not in used_rev and sim > settings.SIMILARITY_THRESHOLD:
                aligned_pairs.append((original_blocks[i], revised_blocks[j]))
                used_orig.add(i)
                used_rev.add(j)

        # Handle unmatched blocks
        for i in range(m):
            if i not in used_orig:
                aligned_pairs.append((original_blocks[i], ""))
        for j in range(n):
            if j not in used_rev:
                aligned_pairs.append(("", revised_blocks[j]))

        # Sort by original order
        aligned_pairs.sort(key=lambda x: (
            next((i for i, b in enumerate(original_blocks) if b == x[0]), float('inf')),
            next((j for j, b in enumerate(revised_blocks) if b == x[1]), float('inf'))
        ))

        return aligned_pairs
    
    def _generate_diff_id(self, text: str, index: int) -> str:
        """
        Generate a unique ID for a difference
        """
        hash_input = f"{text}{index}{hash(text)}"
        return f"diff-{hashlib.md5(hash_input.encode()).hexdigest()[:8]}"
    
    def _has_changes(self, diffs: List[Tuple[int, str]]) -> bool:
        """
        Check if diffs contain any changes
        """
        return any(op != 0 for op, _ in diffs)
    
    def _count_changed_chars(self, diffs: List[Tuple[int, str]]) -> int:
        """
        Count total characters changed in diffs
        """
        return sum(len(text) for op, text in diffs if op != 0)

    def _has_exact_match(self, text1: str, text2: str) -> bool:
        """Check if two texts match exactly after normalization"""
        return text1.strip() == text2.strip()

    def _handle_empty_blocks(self, original_blocks: List[str], revised_blocks: List[str]) -> Tuple[List[Difference], float]:
        """Handle cases where one or both block lists are empty"""
        if not original_blocks:
            return ([Difference(
                id=self._generate_diff_id("", idx),
                original="",
                revised=block,
                change_type=ChangeType.ADDED,
                paragraph_index=idx
            ) for idx, block in enumerate(revised_blocks)], 0.0)
        else:
            return ([Difference(
                id=self._generate_diff_id(block, idx),
                original=block,
                revised="",
                change_type=ChangeType.REMOVED,
                paragraph_index=idx
            ) for idx, block in enumerate(original_blocks)], 0.0)

def compute_diff(original_html: str, revised_html: str) -> Dict[str, Any]:
    """
    Public interface for computing differences between two HTML documents
    """
    if original_html is None or revised_html is None:
        raise ValueError("Input HTML cannot be None")
        
    from app.services.normalization import extract_text_blocks
    
    try:
        # Extract text blocks from HTML
        original_blocks = extract_text_blocks(original_html)
        revised_blocks = extract_text_blocks(revised_html)
        
        # Compute differences
        diff_engine = DiffEngine()
        differences, similarity_score = diff_engine.compute_differences(original_blocks, revised_blocks)
        
        # Convert to serializable format
        diff_result = {
            "differences": [
                {
                    "id": diff.id,
                    "original": diff.original,
                    "revised": diff.revised,
                    "change_type": diff.change_type.value,
                    "paragraph_index": diff.paragraph_index
                }
                for diff in differences
            ],
            "similarity_score": similarity_score
        }
        
        return diff_result
        
    except Exception as e:
        logger.error(f"Error in diff computation: {str(e)}")
        raise