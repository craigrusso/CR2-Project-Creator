#!/usr/bin/env python3

import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtSvg import QSvgRenderer

def convert_svg_to_png(svg_path, output_path, size=64):
    """Convert an SVG file to PNG format"""
    print(f"Converting {svg_path} to {output_path}")
    
    if not os.path.exists(svg_path):
        print(f"Error: SVG file not found at {svg_path}")
        return False
    
    try:
        # Create renderer
        renderer = QSvgRenderer(svg_path)
        
        if not renderer.isValid():
            print(f"Error: Invalid SVG file at {svg_path}")
            return False
        
        # Create pixmap with transparent background
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # Paint SVG onto pixmap
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        # Save as PNG
        result = pixmap.save(output_path, "PNG")
        if result:
            print(f"Successfully saved {output_path}")
        else:
            print(f"Error: Failed to save PNG at {output_path}")
        
        return result
    except Exception as e:
        print(f"Error converting SVG to PNG: {e}")
        return False

def convert_all_icons_in_directory(directory):
    """Convert all SVG icons in a directory to PNG format"""
    if not os.path.exists(directory):
        print(f"Error: Directory not found at {directory}")
        return
    
    # Count for stats
    total = 0
    success = 0
    
    # Process all SVG files in the directory
    for filename in os.listdir(directory):
        if filename.lower().endswith('.svg'):
            total += 1
            svg_path = os.path.join(directory, filename)
            png_path = os.path.join(directory, os.path.splitext(filename)[0] + '.png')
            
            if convert_svg_to_png(svg_path, png_path, 128):
                success += 1
    
    print(f"Conversion complete: {success} of {total} files converted successfully")

if __name__ == "__main__":
    # Need QApplication instance for Qt functionality
    app = QApplication(sys.argv)
    
    # Convert icons in templates directory
    templates_dir = os.path.join(os.path.dirname(__file__), "app", "assets", "icons", "templates")
    convert_all_icons_in_directory(templates_dir)
    
    # Also convert icons in the main icons directory
    icons_dir = os.path.join(os.path.dirname(__file__), "app", "assets", "icons")
    convert_all_icons_in_directory(icons_dir) 