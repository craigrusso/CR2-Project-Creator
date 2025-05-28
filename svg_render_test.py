#!/usr/bin/env python3

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtSvg import QSvgRenderer

class SVGRenderTest(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("SVG Rendering Test")
        self.setGeometry(100, 100, 400, 400)
        
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # Get SVG path
        icon_path = os.path.join(os.path.dirname(__file__), "app", "assets", "icons", "templates", "template_structure_icon.svg")
        print(f"Testing SVG path: {icon_path}")
        print(f"Path exists: {os.path.exists(icon_path)}")
        
        # Method 1: QIcon
        icon_label = QLabel("QIcon Method:")
        layout.addWidget(icon_label)
        
        icon_display = QLabel()
        icon = QIcon(icon_path)
        pixmap1 = icon.pixmap(QSize(64, 64))
        print(f"QIcon pixmap null: {pixmap1.isNull()}")
        print(f"QIcon pixmap size: {pixmap1.width()}x{pixmap1.height()}")
        icon_display.setPixmap(pixmap1)
        layout.addWidget(icon_display)
        
        # Method 2: Direct SVG rendering
        svg_label = QLabel("Direct SVG Rendering:")
        layout.addWidget(svg_label)
        
        svg_display = QLabel()
        svg_display.setMinimumSize(64, 64)
        
        try:
            renderer = QSvgRenderer(icon_path)
            pixmap2 = QPixmap(64, 64)
            pixmap2.fill(Qt.GlobalColor.transparent)
            
            if renderer.isValid():
                painter = QPainter(pixmap2)
                renderer.render(painter)
                painter.end()
                print(f"SVG renderer valid: True")
                print(f"Direct pixmap null: {pixmap2.isNull()}")
                print(f"Direct pixmap size: {pixmap2.width()}x{pixmap2.height()}")
                svg_display.setPixmap(pixmap2)
            else:
                print(f"SVG renderer valid: False")
        except Exception as e:
            print(f"SVG rendering error: {e}")
        
        layout.addWidget(svg_display)
        
        # Add file content info
        try:
            with open(icon_path, 'r') as f:
                content = f.read(200)  # Read first 200 chars
                file_info = QLabel(f"SVG file content (first 200 chars):\n{content}...")
                layout.addWidget(file_info)
        except Exception as e:
            print(f"Error reading SVG file: {e}")
        
        self.setCentralWidget(central_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SVGRenderTest()
    window.show()
    sys.exit(app.exec()) 