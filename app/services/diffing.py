from typing import Dict, Any, List, Tuple
import logging
from diff_match_patch import diff_match_patch
import datetime

logger = logging.getLogger(__name__)

def compute_diff(text1: str, text2: str) -> Dict[str, Any]:
    """Compute differences between two text documents and return a git-like unified diff format"""
    try:
        dmp = diff_match_patch()
        dmp.Diff_Timeout = 5.0
        
        # Split texts into lines
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()
        
        # Compute diffs
        diffs = dmp.diff_main(text1, text2)
        dmp.diff_cleanupSemantic(diffs)
        
        # Convert to unified diff format
        diff_text = _create_unified_diff(lines1, lines2, diffs)
        
        # Calculate similarity score
        similarity = _calculate_similarity(diffs)
        
        return {
            "diff_text": diff_text,
            "similarity_score": similarity
        }
        
    except Exception as e:
        logger.error(f"Error computing differences: {str(e)}")
        raise

def _create_unified_diff(lines1: List[str], lines2: List[str], diffs: List[Tuple[int, str]]) -> str:
    """Create a unified diff format similar to Git"""
    # Create diff header
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    header = [
        "--- source",
        "+++ target",
        f"@@ -1,{len(lines1)} +1,{len(lines2)} @@ {now}"
    ]
    
    # Process diffs into unified format
    unified_diff = []
    for op, text in diffs:
        # Split text into lines and process each line
        for line in text.splitlines():
            if not line:
                continue
            if op == -1:  # Deletion
                unified_diff.append(f"-{line}")
            elif op == 1:  # Addition
                unified_diff.append(f"+{line}")
            else:  # Context
                unified_diff.append(f" {line}")
    
    # Combine header and diff content
    return "\n".join(header + unified_diff)

def _calculate_similarity(diffs: List[Tuple[int, str]]) -> float:
    """Calculate similarity score based on diffs"""
    unchanged_chars = sum(len(text) for op, text in diffs if op == 0)
    total_chars = sum(len(text) for _, text in diffs)
    return unchanged_chars / total_chars if total_chars > 0 else 1.0