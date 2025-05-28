import sys
from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR

print(f"Python version: {sys.version}")
print(f"Qt version: {QT_VERSION_STR}")
print(f"PyQt6 version: {PYQT_VERSION_STR}")

# Try to import a QtWidgets module as a basic check
try:
    from PyQt6.QtWidgets import QApplication, QLabel
    print("PyQt6.QtWidgets imported successfully!")
    app = QApplication(sys.argv)
    label = QLabel("PyQt6 is working!")
    # label.show() # We don't need to show a window for this test
    print("Simple PyQt6 app instance created (no window shown).")
except Exception as e:
    print(f"Error importing or using PyQt6.QtWidgets: {e}") 