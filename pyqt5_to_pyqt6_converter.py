import os
import re

# Directories to scan (add more if needed)
DIRECTORIES_TO_SCAN = [".", "app", "tests"]
# If your app directory is not at the root, adjust the path, e.g., "my_project/app"

# Basic replacements: PyQt5.Module -> PyQt6.Module
BASIC_REPLACEMENTS = {
    "PyQt6.QtWidgets": "PyQt6.QtWidgets",
    "PyQt6.QtGui": "PyQt6.QtGui",
    "PyQt6.QtCore": "PyQt6.QtCore",
    "PyQt6.QtPrintSupport": "PyQt6.QtPrintSupport",
    "PyQt6.QtMultimedia": "PyQt6.QtMultimedia",
    "PyQt6.QtMultimediaWidgets": "PyQt6.QtMultimediaWidgets",
    "PyQt6.QtNetwork": "PyQt6.QtNetwork",
    "PyQt6.QtOpenGL": "PyQt6.QtOpenGL", # Might need QtOpenGLWidgets depending on usage
    "PyQt6.QtSql": "PyQt6.QtSql",
    "PyQt6.QtSvg": "PyQt6.QtSvg",
    "PyQt6.QtTest": "PyQt6.QtTest",
    "PyQt6.QtWebEngineWidgets": "PyQt6.QtWebEngineWidgets",
    "PyQt6.QtWebChannel": "PyQt6.QtWebChannel",
    "PyQt6.QtWebSockets": "PyQt6.QtWebSockets",
    "PyQt6.Qsci": "PyQt6.Qsci", # If you use QScintilla
    "from PyQt6 import": "from PyQt6 import",
}

# Regex for more complex replacements, e.g., Qt.Foo -> Qt.Bar.Foo or specific method changes
# These are examples, you'll likely need to expand this list based on your code and errors
# Order matters if one pattern is a subset of another
REGEX_REPLACEMENTS = [
    # Dialog exec_() to exec()
    (r'\.exec_\(\s*\)', r'.exec()'), 
    
    # Common Enum Changes (examples - you'll need to be thorough)
    # Qt.AspectRatioMode.KeepAspectRatio -> Qt.AspectRatioMode.KeepAspectRatio
    (r'([^A-Za-z0-9_])Qt\.KeepAspectRatio\b', r'\1Qt.AspectRatioMode.KeepAspectRatio'),
    (r'([^A-Za-z0-9_])Qt\.IgnoreAspectRatio\b', r'\1Qt.AspectRatioMode.IgnoreAspectRatio'),
    (r'([^A-Za-z0-9_])Qt\.SmoothTransformation\b', r'\1Qt.TransformationMode.SmoothTransformation'),
    (r'([^A-Za-z0-9_])Qt\.FastTransformation\b', r'\1Qt.TransformationMode.FastTransformation'),
    
    # Alignment flags: Qt.AlignmentFlagFlagFlag.AlignLeft -> Qt.AlignmentFlagFlagFlag.AlignLeft
    (r'([^A-Za-z0-9_])Qt\.(AlignLeft|AlignRight|AlignHCenter|AlignJustify|AlignTop|AlignBottom|AlignVCenter|AlignCenter)([^A-Za-z0-9_])', r'\1Qt.AlignmentFlag.\2\3'),
    (r'([^A-Za-z0-9_])Qt\.Alignment', r'\1Qt.AlignmentFlag'), # If used as Qt.AlignmentFlagFlag, change to Qt.AlignmentFlagFlagFlag

    # Window states: Qt.WindowState.WindowMaximized -> Qt.WindowState.WindowMaximized
    (r'([^A-Za-z0-9_])Qt\.(WindowMaximized|WindowMinimized|WindowFullScreen|WindowActive)([^A-Za-z0-9_])', r'\1Qt.WindowState.\2\3'),

    # Modifiers: Qt.KeyboardModifier.NoModifier -> Qt.KeyboardModifier.NoModifier
    (r'([^A-Za-z0-9_])Qt\.(NoModifier|ShiftModifier|ControlModifier|AltModifier|MetaModifier|KeypadModifier|GroupSwitchModifier)([^A-Za-z0-9_])', r'\1Qt.KeyboardModifier.\2\3'),
    
    # Mouse buttons: Qt.MouseButton.LeftButton -> Qt.MouseButton.LeftButton
    (r'([^A-Za-z0-9_])Qt\.(LeftButton|RightButton|MiddleButton|XButton1|XButton2|NoButton)([^A-Za-z0-9_])', r'\1Qt.MouseButton.\2\3'),

    # Orientations: Qt.Orientation.Horizontal -> Qt.Orientation.Horizontal
    (r'([^A-Za-z0-9_])Qt\.(Horizontal|Vertical)([^A-Za-z0-9_])', r'\1Qt.Orientation.\2\3'),

    # Roles: Qt.ItemDataRole.DisplayRole -> Qt.ItemDataRole.DisplayRole
    (r'([^A-Za-z0-9_])Qt\.(DisplayRole|DecorationRole|EditRole|ToolTipRole|StatusTipRole|WhatsThisRole|FontRole|TextAlignmentRole|BackgroundRole|ForegroundRole|CheckStateRole|AccessibleTextRole|AccessibleDescriptionRole|SizeHintRole|UserRole)([^A-Za-z0-9_])', r'\1Qt.ItemDataRole.\2\3'),

    # QAction.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut) -> QAction.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
    (r'Qt\.ApplicationShortcut', r'Qt.ShortcutContext.ApplicationShortcut'),
    (r'Qt\.WindowShortcut', r'Qt.ShortcutContext.WindowShortcut'),
    (r'Qt\.WidgetShortcut', r'Qt.ShortcutContext.WidgetShortcut'),
    (r'Qt\.WidgetWithChildrenShortcut', r'Qt.ShortcutContext.WidgetWithChildrenShortcut'),

    # QHeaderView.setResizeMode -> QHeaderView.setSectionResizeMode (older Qt5 might use this)
    # This is a common one, check arguments carefully after script runs
    # (r'\.setResizeMode\((.*?),\s*QHeaderView\.Stretch\)', r'.setSectionResizeMode(\1, QHeaderView.ResizeMode.Stretch)'),
    # (r'\.setResizeMode\((.*?),\s*QHeaderView\.Interactive\)', r'.setSectionResizeMode(\1, QHeaderView.ResizeMode.Interactive)'),
    # (r'\.setResizeMode\((.*?),\s*QHeaderView\.Fixed\)', r'.setSectionResizeMode(\1, QHeaderView.ResizeMode.Fixed)'),
    # (r'\.setResizeMode\((.*?),\s*QHeaderView\.ResizeToContents\)', r'.setSectionResizeMode(\1, QHeaderView.ResizeMode.ResizeToContents)'),
    # More generally for QHeaderView ResizeMode enum:
    (r'QHeaderView\.Stretch', 'QHeaderView.ResizeMode.Stretch'),
    (r'QHeaderView\.Interactive', 'QHeaderView.ResizeMode.Interactive'),
    (r'QHeaderView\.Fixed', 'QHeaderView.ResizeMode.Fixed'),
    (r'QHeaderView\.ResizeToContents', 'QHeaderView.ResizeMode.ResizeToContents'),
    
    # QMouseEvent.pos() and globalPos() are still methods, but x() and y() can be replaced by position().x() and position().y()
    # QMouseEvent.x() -> QMouseEvent.position().x()
    # (r'\.x\(\)', '.position().x()'), # This is too broad, needs context of QMouseEvent
    # QMouseEvent.y() -> QMouseEvent.position().y()
    # (r'\.y\(\)', '.position().y()'), # Same here

    # PyQt6.QtCore.PYQT_VERSION_STR -> PyQt6.QtCore.PYQT_VERSION_STR (if not caught by basic import)
    (r'PyQt5\.QtCore\.PYQT_VERSION_STR', 'PyQt6.QtCore.PYQT_VERSION_STR'),
    (r'PyQt5\.QtCore\.QT_VERSION_STR', 'PyQt6.QtCore.QT_VERSION_STR'),
]


def update_file_content(filepath):
    """Reads a file, applies replacements, and writes back if changes were made."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False

    original_content = content

    # Apply basic string replacements
    for old, new in BASIC_REPLACEMENTS.items():
        content = content.replace(old, new)

    # Apply regex replacements
    for pattern, replacement in REGEX_REPLACEMENTS:
        try:
            content = re.sub(pattern, replacement, content)
        except Exception as e:
            print(f"Regex error in {filepath} with pattern '{pattern}': {e}")

    if content != original_content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {filepath}")
            return True
        except Exception as e:
            print(f"Error writing {filepath}: {e}")
            # Consider reverting or handling this (e.g., restore from original_content)
            return False
    return False

def main():
    updated_files_count = 0
    scanned_files_count = 0

    # Get the absolute path of the script's directory to resolve relative paths correctly
    script_dir = os.path.dirname(os.path.abspath(__file__))

    for directory_name in DIRECTORIES_TO_SCAN:
        scan_path = os.path.join(script_dir, directory_name)
        if not os.path.exists(scan_path):
            print(f"Warning: Directory '{scan_path}' not found. Skipping.")
            continue
        if not os.path.isdir(scan_path):
            print(f"Warning: Path '{scan_path}' is not a directory. Assuming it's a file to scan directly.")
            if directory_name.endswith(".py"):
                 scanned_files_count += 1
                 if update_file_content(scan_path):
                    updated_files_count +=1
            continue # Skip os.walk if it's not a directory

        for root, _, files in os.walk(scan_path):
            for filename in files:
                if filename.endswith(".py"):
                    filepath = os.path.join(root, filename)
                    scanned_files_count += 1
                    if update_file_content(filepath):
                        updated_files_count += 1
    
    print(f"\nScan complete. Scanned {scanned_files_count} Python files.")
    print(f"Updated {updated_files_count} files.")
    if updated_files_count > 0:
        print("Please review the changes and test your application thoroughly.")
        print("You may need to manually adjust more complex API changes (e.g., enums, method signatures).")

if __name__ == "__main__":
    main() 