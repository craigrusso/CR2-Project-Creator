
import sys
try:
    print(f"Python: {sys.version}")
    from PyQt6.QtWidgets import QApplication
    print("Successfully imported QApplication")
    app = QApplication([])
    print("Successfully created QApplication instance")
    from PyQt6.QtCore import QCoreApplication
    print(f"Qt version: {QCoreApplication.applicationVersion()}")
    from PyQt6.QtGui import QIcon
    print("Successfully imported QIcon")
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
