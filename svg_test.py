#!/usr/bin/env python3

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtSvg import QSvgRenderer

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller/py2app """
    
    base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("SVG Icon Test")
        self.setGeometry(100, 100, 400, 400)
        
        layout = QVBoxLayout()
        
        # Test loading with QIcon
        label1 = QLabel("QIcon SVG Test:")
        layout.addWidget(label1)
        
        icon_path = get_resource_path(os.path.join("app", "assets", "icons", "templates", "template_structure_icon.svg"))
        print(f"Loading SVG icon from: {icon_path}")
        print(f"File exists: {os.path.exists(icon_path)}")
        
        if os.path.exists(icon_path):
            # Method 1: QIcon
            icon = QIcon(icon_path)
            pixmap = icon.pixmap(QSize(64, 64))
            if pixmap.isNull():
                print("ERROR: QIcon created a null pixmap")
            else:
                print(f"SUCCESS: QIcon created a valid pixmap with size {pixmap.width()}x{pixmap.height()}")
            
            label2 = QLabel()
            label2.setPixmap(pixmap)
            layout.addWidget(label2)
            
            # Method 2: QSvgRenderer
            label3 = QLabel("QSvgRenderer Test:")
            layout.addWidget(label3)
            
            renderer = QSvgRenderer(icon_path)
            if renderer.isValid():
                print("SUCCESS: QSvgRenderer loaded SVG file successfully")
                svg_pixmap = QPixmap(64, 64)
                svg_pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(svg_pixmap)
                renderer.render(painter)
                painter.end()
                
                label4 = QLabel()
                label4.setPixmap(svg_pixmap)
                layout.addWidget(label4)
            else:
                print("ERROR: QSvgRenderer could not load SVG file")
        else:
            print(f"ERROR: File not found at {icon_path}")
        
        # Central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 