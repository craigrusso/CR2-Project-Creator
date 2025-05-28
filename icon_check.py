#!/usr/bin/env python3

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QFrame, QHBoxLayout
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import QSize, Qt, QRect
from PyQt6.QtSvg import QSvgRenderer

# Get resource path (similar to app.constants.get_resource_path)
def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller/py2app """
    # Base path is the script directory (for development testing)
    base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

class IconTest(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("SVG Icon Test (Comprehensive)")
        self.setGeometry(100, 100, 800, 600)
        
        # Main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header_label = QLabel("SVG Icon Loading Test")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)
        
        # Icons to test
        icons_to_test = [
            ("template_structure_icon.svg", "Template Structure"),
            ("folder_icon.svg", "Folder"),
            ("file_icon.svg", "File")
        ]
        
        # Test methods
        methods = [
            ("QIcon direct", self.load_with_qicon),
            ("QSvgRenderer", self.load_with_svg_renderer),
            ("QIcon from QPixmap", self.load_with_qicon_from_pixmap),
            ("Manual Fallback", self.create_fallback_icon)
        ]
        
        # Create grid layout
        grid_layout = QVBoxLayout()
        
        # Create header row
        header_row = QHBoxLayout()
        method_label = QLabel("Method")
        method_label.setFont(header_font)
        header_row.addWidget(method_label, 1)
        
        for icon_file, icon_name in icons_to_test:
            icon_header = QLabel(icon_name)
            icon_header.setFont(header_font)
            header_row.addWidget(icon_header, 1)
        
        grid_layout.addLayout(header_row)
        
        # Test each method with each icon
        for method_name, method_func in methods:
            row_layout = QHBoxLayout()
            
            # Method name
            method_label = QLabel(method_name)
            method_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            row_layout.addWidget(method_label, 1)
            
            # Try each icon with this method
            for icon_file, icon_name in icons_to_test:
                icon_path = get_resource_path(os.path.join("app", "assets", "icons", "templates", icon_file))
                icon_frame = QFrame()
                icon_frame.setFrameShape(QFrame.Shape.Box)
                icon_frame.setMinimumSize(100, 100)
                
                icon_layout = QVBoxLayout(icon_frame)
                
                # Create label for pixmap
                icon_label = QLabel()
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Create pixmap using the method
                pixmap = method_func(icon_path)
                if pixmap and not pixmap.isNull():
                    icon_label.setPixmap(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio))
                    result_label = QLabel("Success")
                    result_label.setStyleSheet("color: green;")
                else:
                    result_label = QLabel("Failed")
                    result_label.setStyleSheet("color: red;")
                
                # Add to layout
                icon_layout.addWidget(icon_label)
                icon_layout.addWidget(result_label)
                
                row_layout.addWidget(icon_frame, 1)
            
            grid_layout.addLayout(row_layout)
        
        main_layout.addLayout(grid_layout)
        
        # Path info
        path_info = QLabel(f"Current working directory: {os.getcwd()}")
        main_layout.addWidget(path_info)
        
        # Set central widget
        self.setCentralWidget(central_widget)
    
    def load_with_qicon(self, path):
        """Load icon using QIcon directly"""
        try:
            print(f"QIcon method: Loading {path}")
            if not os.path.exists(path):
                print(f"  File not found: {path}")
                return None
                
            icon = QIcon(path)
            pixmap = icon.pixmap(QSize(64, 64))
            if pixmap.isNull():
                print(f"  Created null pixmap for: {path}")
            else:
                print(f"  Success with size: {pixmap.width()}x{pixmap.height()}")
            return pixmap
        except Exception as e:
            print(f"  Exception in QIcon: {str(e)}")
            return None
    
    def load_with_svg_renderer(self, path):
        """Load icon using QSvgRenderer"""
        try:
            print(f"QSvgRenderer method: Loading {path}")
            if not os.path.exists(path):
                print(f"  File not found: {path}")
                return None
                
            renderer = QSvgRenderer(path)
            if not renderer.isValid():
                print(f"  Invalid SVG: {path}")
                return None
                
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            print(f"  Success with size: {pixmap.width()}x{pixmap.height()}")
            return pixmap
        except Exception as e:
            print(f"  Exception in QSvgRenderer: {str(e)}")
            return None
    
    def load_with_qicon_from_pixmap(self, path):
        """Load SVG with QSvgRenderer first, then create QIcon from that pixmap"""
        try:
            print(f"QIcon from QPixmap method: Loading {path}")
            if not os.path.exists(path):
                print(f"  File not found: {path}")
                return None
                
            # First render to pixmap
            renderer = QSvgRenderer(path)
            if not renderer.isValid():
                print(f"  Invalid SVG: {path}")
                return None
                
            temp_pixmap = QPixmap(64, 64)
            temp_pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(temp_pixmap)
            renderer.render(painter)
            painter.end()
            
            # Then create icon from pixmap
            icon = QIcon(temp_pixmap)
            pixmap = icon.pixmap(QSize(64, 64))
            
            print(f"  Success with size: {pixmap.width()}x{pixmap.height()}")
            return pixmap
        except Exception as e:
            print(f"  Exception in QIcon from QPixmap: {str(e)}")
            return None
    
    def create_fallback_icon(self, path):
        """Create a fallback icon regardless of input path"""
        try:
            print(f"Fallback method: Creating fallback for {path}")
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setPen(QColor(0, 0, 0))
            painter.setBrush(QColor(240, 240, 240))
            painter.drawRect(1, 1, 62, 62)
            painter.drawText(QRect(0, 0, 64, 64), Qt.AlignmentFlag.AlignCenter, "F")
            painter.end()
            print(f"  Created fallback with size: {pixmap.width()}x{pixmap.height()}")
            return pixmap
        except Exception as e:
            print(f"  Exception in Fallback: {str(e)}")
            return None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IconTest()
    window.show()
    sys.exit(app.exec()) 