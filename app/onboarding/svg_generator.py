#!/usr/bin/env python3
"""
SVG Tutorial Illustration Generator
Creates lightweight SVG illustrations for onboarding tutorials using the app's color scheme.
"""

from typing import Dict, List, Tuple, Optional
import xml.etree.ElementTree as ET
from xml.dom import minidom

class SVGGenerator:
    """Generates SVG illustrations for tutorial content"""
    
    def __init__(self, color_scheme: Dict[str, str]):
        """Initialize with app color scheme"""
        self.colors = color_scheme
        
        # Standard dimensions for consistency
        self.width = 400
        self.height = 300
        self.padding = 20
        
    def create_svg_element(self, width: int = None, height: int = None) -> ET.Element:
        """Create a base SVG element with proper namespace and dimensions"""
        w = width or self.width
        h = height or self.height
        
        svg = ET.Element('svg')
        svg.set('xmlns', 'http://www.w3.org/2000/svg')
        svg.set('viewBox', f'0 0 {w} {h}')
        svg.set('width', str(w))
        svg.set('height', str(h))
        
        # Add a subtle background
        bg_rect = ET.SubElement(svg, 'rect')
        bg_rect.set('width', str(w))
        bg_rect.set('height', str(h))
        bg_rect.set('fill', self.colors.get('card_bg', '#252526'))
        bg_rect.set('rx', '8')
        
        return svg
    
    def add_app_window_frame(self, svg: ET.Element, x: int = 40, y: int = 40, 
                            width: int = 320, height: int = 220) -> ET.Element:
        """Add a simplified app window frame"""
        # Window background
        window = ET.SubElement(svg, 'rect')
        window.set('x', str(x))
        window.set('y', str(y))
        window.set('width', str(width))
        window.set('height', str(height))
        window.set('fill', self.colors.get('bg', '#1E1E1E'))
        window.set('stroke', self.colors.get('border', '#3C3C3C'))
        window.set('stroke-width', '2')
        window.set('rx', '8')
        
        # Title bar
        title_bar = ET.SubElement(svg, 'rect')
        title_bar.set('x', str(x))
        title_bar.set('y', str(y))
        title_bar.set('width', str(width))
        title_bar.set('height', '30')
        title_bar.set('fill', self.colors.get('card_bg', '#252526'))
        title_bar.set('rx', '8')
        
        # Window controls (simplified)
        for i, color in enumerate(['#FF5F56', '#FFBD2E', '#27CA3F']):
            circle = ET.SubElement(svg, 'circle')
            circle.set('cx', str(x + 15 + i * 20))
            circle.set('cy', str(y + 15))
            circle.set('r', '6')
            circle.set('fill', color)
        
        return window
    
    def add_button(self, svg: ET.Element, x: int, y: int, width: int, height: int, 
                   text: str, highlight: bool = False) -> ET.Element:
        """Add a button with optional highlight"""
        button_color = self.colors.get('accent', '#2C4F76') if highlight else self.colors.get('card_bg', '#252526')
        text_color = 'white' if highlight else self.colors.get('text', '#CCCCCC')
        
        # Button background
        button = ET.SubElement(svg, 'rect')
        button.set('x', str(x))
        button.set('y', str(y))
        button.set('width', str(width))
        button.set('height', str(height))
        button.set('fill', button_color)
        button.set('stroke', self.colors.get('border', '#3C3C3C'))
        button.set('stroke-width', '1')
        button.set('rx', '4')
        
        # Button text
        text_elem = ET.SubElement(svg, 'text')
        text_elem.set('x', str(x + width // 2))
        text_elem.set('y', str(y + height // 2 + 4))
        text_elem.set('text-anchor', 'middle')
        text_elem.set('fill', text_color)
        text_elem.set('font-family', 'Arial, sans-serif')
        text_elem.set('font-size', '12')
        text_elem.text = text
        
        return button
    
    def add_text_input(self, svg: ET.Element, x: int, y: int, width: int, height: int, 
                       placeholder: str = '') -> ET.Element:
        """Add a text input field"""
        # Input background
        input_field = ET.SubElement(svg, 'rect')
        input_field.set('x', str(x))
        input_field.set('y', str(y))
        input_field.set('width', str(width))
        input_field.set('height', str(height))
        input_field.set('fill', self.colors.get('bg', '#1E1E1E'))
        input_field.set('stroke', self.colors.get('border', '#3C3C3C'))
        input_field.set('stroke-width', '1')
        input_field.set('rx', '3')
        
        # Placeholder text
        if placeholder:
            text_elem = ET.SubElement(svg, 'text')
            text_elem.set('x', str(x + 8))
            text_elem.set('y', str(y + height // 2 + 4))
            text_elem.set('fill', self.colors.get('secondary_text', '#858585'))
            text_elem.set('font-family', 'Arial, sans-serif')
            text_elem.set('font-size', '11')
            text_elem.text = placeholder
        
        return input_field
    
    def add_arrow(self, svg: ET.Element, start_x: int, start_y: int, 
                  end_x: int, end_y: int, color: str = None) -> None:
        """Add an arrow pointing from start to end"""
        arrow_color = color or self.colors.get('accent', '#2C4F76')
        
        # Arrow line
        line = ET.SubElement(svg, 'line')
        line.set('x1', str(start_x))
        line.set('y1', str(start_y))
        line.set('x2', str(end_x))
        line.set('y2', str(end_y))
        line.set('stroke', arrow_color)
        line.set('stroke-width', '3')
        line.set('marker-end', 'url(#arrowhead)')
        
        # Define arrowhead marker if not already defined
        defs = svg.find('.//defs')
        if defs is None:
            defs = ET.SubElement(svg, 'defs')
        
        if defs.find('.//marker[@id="arrowhead"]') is None:
            marker = ET.SubElement(defs, 'marker')
            marker.set('id', 'arrowhead')
            marker.set('markerWidth', '10')
            marker.set('markerHeight', '7')
            marker.set('refX', '9')
            marker.set('refY', '3.5')
            marker.set('orient', 'auto')
            
            polygon = ET.SubElement(marker, 'polygon')
            polygon.set('points', '0 0, 10 3.5, 0 7')
            polygon.set('fill', arrow_color)
    
    def add_highlight_bubble(self, svg: ET.Element, x: int, y: int, width: int, height: int,
                            text: str, pointer_x: int = None, pointer_y: int = None) -> ET.Element:
        """Add a thought bubble or callout with text"""
        bubble_color = self.colors.get('accent', '#2C4F76')
        
        # Main bubble
        bubble = ET.SubElement(svg, 'rect')
        bubble.set('x', str(x))
        bubble.set('y', str(y))
        bubble.set('width', str(width))
        bubble.set('height', str(height))
        bubble.set('fill', bubble_color)
        bubble.set('stroke', self.colors.get('border', '#3C3C3C'))
        bubble.set('stroke-width', '2')
        bubble.set('rx', '12')
        
        # Pointer tail if specified
        if pointer_x is not None and pointer_y is not None:
            # Simple triangular pointer
            points = f"{x + width//2 - 8},{y + height} {x + width//2 + 8},{y + height} {pointer_x},{pointer_y}"
            pointer = ET.SubElement(svg, 'polygon')
            pointer.set('points', points)
            pointer.set('fill', bubble_color)
            pointer.set('stroke', self.colors.get('border', '#3C3C3C'))
            pointer.set('stroke-width', '2')
        
        # Bubble text
        text_elem = ET.SubElement(svg, 'text')
        text_elem.set('x', str(x + width // 2))
        text_elem.set('y', str(y + height // 2 + 4))
        text_elem.set('text-anchor', 'middle')
        text_elem.set('fill', 'white')
        text_elem.set('font-family', 'Arial, sans-serif')
        text_elem.set('font-size', '12')
        text_elem.set('font-weight', 'bold')
        text_elem.text = text
        
        return bubble
    
    def add_file_icon(self, svg: ET.Element, x: int, y: int, size: int = 16, 
                      is_folder: bool = False) -> ET.Element:
        """Add a simple file or folder icon"""
        if is_folder:
            # Folder icon
            folder = ET.SubElement(svg, 'rect')
            folder.set('x', str(x))
            folder.set('y', str(y + size // 4))
            folder.set('width', str(size))
            folder.set('height', str(size * 3 // 4))
            folder.set('fill', self.colors.get('folder_icon', '#E8BA36'))
            folder.set('rx', '2')
            
            # Folder tab
            tab = ET.SubElement(svg, 'rect')
            tab.set('x', str(x))
            tab.set('y', str(y))
            tab.set('width', str(size // 2))
            tab.set('height', str(size // 4))
            tab.set('fill', self.colors.get('folder_icon', '#E8BA36'))
            tab.set('rx', '1')
        else:
            # File icon
            file_icon = ET.SubElement(svg, 'rect')
            file_icon.set('x', str(x))
            file_icon.set('y', str(y))
            file_icon.set('width', str(size))
            file_icon.set('height', str(size))
            file_icon.set('fill', self.colors.get('secondary_text', '#858585'))
            file_icon.set('rx', '2')
            
            # File corner fold
            fold = ET.SubElement(svg, 'polygon')
            fold_size = size // 4
            points = f"{x + size - fold_size},{y} {x + size},{y + fold_size} {x + size - fold_size},{y + fold_size}"
            fold.set('points', points)
            fold.set('fill', self.colors.get('bg', '#1E1E1E'))
        
        return folder if is_folder else file_icon
    
    def to_string(self, svg: ET.Element) -> str:
        """Convert SVG element to formatted string"""
        rough_string = ET.tostring(svg, 'unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ").split('\n', 1)[1]  # Remove XML declaration 