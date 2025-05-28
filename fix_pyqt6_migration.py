#!/usr/bin/env python3
"""
PyQt6 Migration Fixer
Fixes all PyQt5 to PyQt6 migration issues in the codebase
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple
import shutil
import sys

# Import the migration patterns from the checker
from check_pyqt6_migration import MIGRATION_PATTERNS

def backup_file(file_path: Path) -> bool:
    """Create a backup of the file before modifying it"""
    backup_path = file_path.with_suffix(file_path.suffix + '.bak')
    try:
        shutil.copy2(file_path, backup_path)
        return True
    except Exception as e:
        print(f"Warning: Failed to create backup of {file_path}: {e}")
        return False

def fix_file(file_path: Path) -> Tuple[int, List[str]]:
    """Fix PyQt6 migration issues in a file"""
    fixes_applied = 0
    applied_patterns = []
    
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Apply fixes for each pattern
        original_content = content
        
        for old_pattern, new_pattern in MIGRATION_PATTERNS.items():
            # Skip patterns in the dictionary that are for the checker only
            if old_pattern in applied_patterns:
                continue
                
            # For patterns that end with underscore (like Qt.Key_), we need special handling
            if old_pattern.endswith('_'):
                # Create a regex that captures the full enum name
                pattern = re.compile(rf'\b{re.escape(old_pattern)}([A-Za-z0-9_]+)\b')
                # Replace with the new namespace pattern but keep the enum value
                modified_content = pattern.sub(rf'{new_pattern}\1', content)
                
                if modified_content != content:
                    fixes_applied += len(re.findall(pattern, content))
                    content = modified_content
                    applied_patterns.append(old_pattern)
            else:
                # For regular patterns, do a direct word boundary replacement
                pattern = re.compile(rf'\b{re.escape(old_pattern)}\b')
                modified_content = pattern.sub(new_pattern, content)
                
                if modified_content != content:
                    fixes_applied += len(re.findall(pattern, content))
                    content = modified_content
                    applied_patterns.append(old_pattern)
                    
        # Apply special case fixes for ObjCInstance property access
        objc_pattern = re.compile(r'(\w+)\.TIFFRepresentation\(\)')
        modified_content = objc_pattern.sub(r'\1.TIFFRepresentation', content)
        if modified_content != content:
            fixes_applied += len(re.findall(objc_pattern, content))
            content = modified_content
            applied_patterns.append('ObjCInstance property access')
            
        # Write the file only if changes were made
        if content != original_content:
            # Create a backup first
            backup_file(file_path)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        
    return fixes_applied, applied_patterns

def fix_directory(directory: Path, dry_run: bool = False) -> Dict[str, Tuple[int, List[str]]]:
    """Fix PyQt6 migration issues in all files in a directory"""
    all_fixes = {}
    
    # Only scan Python files
    for py_file in directory.rglob('*.py'):
        # Skip venv, __pycache__, and other irrelevant directories
        if any(part in str(py_file) for part in ['venv', '__pycache__', '.git', 'build', 'dist']):
            continue
            
        if dry_run:
            # In dry run mode, just report the files that would be fixed
            print(f"Would fix: {py_file.relative_to(directory)}")
        else:
            # Apply fixes
            fixes_count, patterns = fix_file(py_file)
            
            if fixes_count > 0:
                all_fixes[str(py_file.relative_to(directory))] = (fixes_count, patterns)
                
    return all_fixes

def main():
    """Main function to fix PyQt6 migration issues"""
    # Get the V4 directory
    v4_dir = Path(__file__).parent
    
    # Check for dry run mode
    dry_run = '--dry-run' in sys.argv
    
    print("PyQt6 Migration Fixer")
    print("=" * 80)
    print(f"Scanning directory: {v4_dir}")
    if dry_run:
        print("DRY RUN MODE: No files will be modified")
    print()
    
    # Apply fixes
    all_fixes = fix_directory(v4_dir, dry_run)
    
    if not all_fixes:
        print("No PyQt6 migration issues fixed!")
        return
        
    # Report fixes
    total_fixes = 0
    for file_path, (fixes_count, patterns) in sorted(all_fixes.items()):
        print(f"\n{file_path}:")
        print("-" * len(file_path))
        
        print(f"  Fixed {fixes_count} issues with patterns: {', '.join(patterns)}")
        total_fixes += fixes_count
            
    print(f"\n\nTotal fixes applied: {total_fixes}")
    if not dry_run:
        print("\nBackup files (.py.bak) were created for all modified files.")
        print("If everything works correctly, you can delete them.")

if __name__ == "__main__":
    main() 