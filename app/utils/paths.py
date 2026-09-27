import os
from pathlib import Path
from typing import Union

def validate_safe_lab_path(target_path: Union[str, Path], lab_root: Union[str, Path]) -> Path:
    r"""
    Rigorously validates and canonicalizes a target filesystem path, ensuring
    it strictly resides within the designated laboratory root directory.
    
    Protects against:
    - Path traversal attacks (e.g. '../../Windows')
    - Drive-letter hopping (e.g. 'C:\Windows' when lab is on D:)
    - Windows case-insensitivity discrepancies
    - Trailing dots, spaces, or alternate path separators
    - UNC network shares
    
    Raises:
        ValueError: If target_path is empty or invalid.
        PermissionError: If target_path resolves outside lab_root.
    """
    if not target_path or not str(target_path).strip():
        raise ValueError("Target path cannot be empty.")
        
    if not lab_root or not str(lab_root).strip():
        raise ValueError("Lab root path cannot be empty.")
        
    try:
        canonical_lab = Path(lab_root).resolve(strict=False)
        canonical_target = Path(target_path).resolve(strict=False)
    except Exception as e:
        raise PermissionError(f"Path canonicalization failure for '{target_path}': {e}")
        
    # Case-normalized string comparison for Windows filesystem safety
    norm_lab = os.path.normcase(str(canonical_lab))
    norm_target = os.path.normcase(str(canonical_target))
    
    # Must start with lab directory and not be equal to drive root
    # Ensure there is a trailing separator check so 'D:\lab_extra' doesn't match 'D:\lab'
    if not norm_lab.endswith(os.sep):
        norm_lab_prefix = norm_lab + os.sep
    else:
        norm_lab_prefix = norm_lab
        
    if norm_target != norm_lab and not norm_target.startswith(norm_lab_prefix):
        raise PermissionError(
            f"Path Traversal Violation: Target '{canonical_target}' resolves outside lab root '{canonical_lab}'."
        )
        
    return canonical_target
