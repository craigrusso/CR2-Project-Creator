#!/usr/bin/env python3
"""
PyQt6 Migration Checker
Identifies all PyQt5 to PyQt6 migration issues in the codebase
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict

# Common PyQt5 to PyQt6 migration patterns
MIGRATION_PATTERNS = {
    # QFont enum issues
    'QFont.Weight.Bold': 'QFont.Weight.Bold',
    'QFont.Weight.Normal': 'QFont.Weight.Normal',
    'QFont.Weight.DemiBold': 'QFont.Weight.DemiBold',
    'QFont.Weight.Light': 'QFont.Weight.Light',
    'QFont.Weight.Black': 'QFont.Weight.Black',
    
    # Qt Key enums
    'Qt.Key_': 'Qt.Key.Key_',
    
    # QSizePolicy enums
    'QSizePolicy.Policy.Expanding': 'QSizePolicy.Policy.Expanding',
    'QSizePolicy.Policy.Fixed': 'QSizePolicy.Policy.Fixed',
    'QSizePolicy.Policy.Minimum': 'QSizePolicy.Policy.Minimum',
    'QSizePolicy.Policy.Maximum': 'QSizePolicy.Policy.Maximum',
    'QSizePolicy.Policy.Preferred': 'QSizePolicy.Policy.Preferred',
    'QSizePolicy.Policy.MinimumExpanding': 'QSizePolicy.Policy.MinimumExpanding',
    'QSizePolicy.Policy.Ignored': 'QSizePolicy.Policy.Ignored',
    
    # QStyle standard icons
    'QStyle.SP_': 'QStyle.StandardPixmap.SP_',
    
    # Qt enums
    'Qt.AlignmentFlag.AlignLeft': 'Qt.AlignmentFlag.AlignLeft',
    'Qt.AlignmentFlag.AlignRight': 'Qt.AlignmentFlag.AlignRight',
    'Qt.AlignmentFlag.AlignCenter': 'Qt.AlignmentFlag.AlignCenter',
    'Qt.AlignmentFlag.AlignTop': 'Qt.AlignmentFlag.AlignTop',
    'Qt.AlignmentFlag.AlignBottom': 'Qt.AlignmentFlag.AlignBottom',
    'Qt.AlignmentFlag.AlignVCenter': 'Qt.AlignmentFlag.AlignVCenter',
    'Qt.AlignmentFlag.AlignHCenter': 'Qt.AlignmentFlag.AlignHCenter',
    
    'Qt.MouseButton.LeftButton': 'Qt.MouseButton.LeftButton',
    'Qt.MouseButton.RightButton': 'Qt.MouseButton.RightButton',
    'Qt.MouseButton.MiddleButton': 'Qt.MouseButton.MiddleButton',
    
    'Qt.KeyboardModifier.NoModifier': 'Qt.KeyboardModifier.NoModifier',
    'Qt.KeyboardModifier.ShiftModifier': 'Qt.KeyboardModifier.ShiftModifier',
    'Qt.KeyboardModifier.ControlModifier': 'Qt.KeyboardModifier.ControlModifier',
    'Qt.KeyboardModifier.AltModifier': 'Qt.KeyboardModifier.AltModifier',
    'Qt.KeyboardModifier.MetaModifier': 'Qt.KeyboardModifier.MetaModifier',
    
    'Qt.Orientation.Horizontal': 'Qt.Orientation.Horizontal',
    'Qt.Orientation.Vertical': 'Qt.Orientation.Vertical',
    
    'Qt.CheckState.Checked': 'Qt.CheckState.Checked',
    'Qt.CheckState.Unchecked': 'Qt.CheckState.Unchecked',
    'Qt.CheckState.PartiallyChecked': 'Qt.CheckState.PartiallyChecked',
    
    'Qt.PenStyle.NoPen': 'Qt.PenStyle.NoPen',
    'Qt.PenStyle.SolidLine': 'Qt.PenStyle.SolidLine',
    'Qt.PenStyle.DashLine': 'Qt.PenStyle.DashLine',
    
    'Qt.BrushStyle.NoBrush': 'Qt.BrushStyle.NoBrush',
    'Qt.BrushStyle.SolidPattern': 'Qt.BrushStyle.SolidPattern',
    
    'Qt.AspectRatioMode.KeepAspectRatio': 'Qt.AspectRatioMode.KeepAspectRatio',
    'Qt.AspectRatioMode.IgnoreAspectRatio': 'Qt.AspectRatioMode.IgnoreAspectRatio',
    
    'Qt.TransformationMode.SmoothTransformation': 'Qt.TransformationMode.SmoothTransformation',
    'Qt.TransformationMode.FastTransformation': 'Qt.TransformationMode.FastTransformation',
    
    'Qt.ContextMenuPolicy.CustomContextMenu': 'Qt.ContextMenuPolicy.CustomContextMenu',
    'Qt.ContextMenuPolicy.DefaultContextMenu': 'Qt.ContextMenuPolicy.DefaultContextMenu',
    'Qt.ContextMenuPolicy.NoContextMenu': 'Qt.ContextMenuPolicy.NoContextMenu',
    
    'Qt.WindowModality.WindowModal': 'Qt.WindowModality.WindowModal',
    'Qt.WindowModality.ApplicationModal': 'Qt.WindowModality.ApplicationModal',
    'Qt.WindowModality.NonModal': 'Qt.WindowModality.NonModal',
    
    'Qt.FocusPolicy.StrongFocus': 'Qt.FocusPolicy.StrongFocus',
    'Qt.FocusPolicy.NoFocus': 'Qt.FocusPolicy.NoFocus',
    'Qt.FocusPolicy.TabFocus': 'Qt.FocusPolicy.TabFocus',
    'Qt.FocusPolicy.ClickFocus': 'Qt.FocusPolicy.ClickFocus',
    'Qt.FocusPolicy.WheelFocus': 'Qt.FocusPolicy.WheelFocus',
    
    'Qt.ItemFlag.ItemIsEnabled': 'Qt.ItemFlag.ItemIsEnabled',
    'Qt.ItemFlag.ItemIsSelectable': 'Qt.ItemFlag.ItemIsSelectable',
    'Qt.ItemFlag.ItemIsEditable': 'Qt.ItemFlag.ItemIsEditable',
    'Qt.ItemFlag.ItemIsDragEnabled': 'Qt.ItemFlag.ItemIsDragEnabled',
    'Qt.ItemFlag.ItemIsDropEnabled': 'Qt.ItemFlag.ItemIsDropEnabled',
    
    'Qt.ItemDataRole.DisplayRole': 'Qt.ItemDataRole.DisplayRole',
    'Qt.ItemDataRole.UserRole': 'Qt.ItemDataRole.UserRole',
    'Qt.ItemDataRole.DecorationRole': 'Qt.ItemDataRole.DecorationRole',
    
    'Qt.CursorShape.PointingHandCursor': 'Qt.CursorShape.PointingHandCursor',
    'Qt.CursorShape.ArrowCursor': 'Qt.CursorShape.ArrowCursor',
    'Qt.CursorShape.WaitCursor': 'Qt.CursorShape.WaitCursor',
    
    'Qt.GlobalColor.transparent': 'Qt.GlobalColor.transparent',
    'Qt.GlobalColor.black': 'Qt.GlobalColor.black',
    'Qt.GlobalColor.white': 'Qt.GlobalColor.white',
    
    'Qt.MaskMode.MaskOutColor': 'Qt.MaskMode.MaskOutColor',
    'Qt.MaskMode.MaskInColor': 'Qt.MaskMode.MaskInColor',
    
    'Qt.DropAction.MoveAction': 'Qt.DropAction.MoveAction',
    'Qt.DropAction.CopyAction': 'Qt.DropAction.CopyAction',
    
    # Painter composition modes
    'QPainter.CompositionMode.CompositionMode_SourceIn': 'QPainter.CompositionMode.CompositionMode_SourceIn',
    'QPainter.CompositionMode.CompositionMode_SourceOver': 'QPainter.CompositionMode.CompositionMode_SourceOver',
}

def find_migration_issues(file_path: Path) -> List[Tuple[int, str, str, str]]:
    """Find PyQt6 migration issues in a file"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            for old_pattern, new_pattern in MIGRATION_PATTERNS.items():
                # Create regex pattern with word boundaries where appropriate
                if old_pattern.endswith('_'):
                    # For patterns like Qt.Key_, match the full enum
                    pattern = re.compile(rf'\b{re.escape(old_pattern)}[A-Za-z0-9_]+\b')
                else:
                    pattern = re.compile(rf'\b{re.escape(old_pattern)}\b')
                
                if pattern.search(line):
                    issues.append((line_num, line.strip(), old_pattern, new_pattern))
                    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return issues

def scan_directory(directory: Path) -> Dict[str, List[Tuple[int, str, str, str]]]:
    """Scan directory for PyQt6 migration issues"""
    all_issues = {}
    
    # Only scan Python files
    for py_file in directory.rglob('*.py'):
        # Skip venv, __pycache__, and other irrelevant directories
        if any(part in str(py_file) for part in ['venv', '__pycache__', '.git', 'build', 'dist']):
            continue
            
        issues = find_migration_issues(py_file)
        if issues:
            all_issues[str(py_file.relative_to(directory))] = issues
            
    return all_issues

def main():
    """Main function to scan and report issues"""
    # Get the V4 directory
    v4_dir = Path(__file__).parent
    
    print("PyQt6 Migration Checker")
    print("=" * 80)
    print(f"Scanning directory: {v4_dir}")
    print()
    
    # Scan for issues
    all_issues = scan_directory(v4_dir)
    
    if not all_issues:
        print("No PyQt6 migration issues found!")
        return
        
    # Report issues
    total_issues = 0
    for file_path, issues in sorted(all_issues.items()):
        print(f"\n{file_path}:")
        print("-" * len(file_path))
        
        for line_num, line_content, old_pattern, new_pattern in issues:
            print(f"  Line {line_num}: {old_pattern} -> {new_pattern}")
            print(f"    {line_content}")
            total_issues += 1
            
    print(f"\n\nTotal issues found: {total_issues}")
    print("\nSuggested fixes have been identified. Run fix_pyqt6_migration.py to apply them.")

if __name__ == "__main__":
    main() 