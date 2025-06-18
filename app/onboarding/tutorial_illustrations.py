#!/usr/bin/env python3
"""
Tutorial Illustrations Generator
Creates specific SVG illustrations for each onboarding tutorial step.
"""

from typing import Dict, Optional
import xml.etree.ElementTree as ET
from .svg_generator import SVGGenerator
import os

class TutorialIllustrations:
    """Creates tutorial illustrations for onboarding steps"""
    
    def __init__(self, color_scheme: Dict[str, str]):
        """Initialize with app color scheme"""
        self.generator = SVGGenerator(color_scheme)
        
    def create_welcome_illustration(self) -> str:
        """Create welcome screen illustration that matches the actual app"""
        svg = self.generator.create_svg_element()
        
        # App window with actual layout
        window = self.generator.add_app_window_frame(svg, x=10, y=10, width=380, height=260)
        
        # Left panel (project settings)
        left_panel = ET.SubElement(svg, 'rect')
        left_panel.set('x', '20')
        left_panel.set('y', '40')
        left_panel.set('width', '160')
        left_panel.set('height', '220')
        left_panel.set('fill', self.generator.colors.get('card_bg', '#252526'))
        left_panel.set('stroke', self.generator.colors.get('border', '#3C3C3C'))
        left_panel.set('stroke-width', '1')
        left_panel.set('rx', '4')
        
        # Left panel title
        title_text = ET.SubElement(svg, 'text')
        title_text.set('x', '30')
        title_text.set('y', '60')
        title_text.set('fill', self.generator.colors.get('text', '#CCCCCC'))
        title_text.set('font-family', 'Arial, sans-serif')
        title_text.set('font-size', '11')
        title_text.set('font-weight', 'bold')
        title_text.text = 'Project Settings'
        
        # Text area simulation
        text_area = ET.SubElement(svg, 'rect')
        text_area.set('x', '30')
        text_area.set('y', '75')
        text_area.set('width', '140')
        text_area.set('height', '80')
        text_area.set('fill', self.generator.colors.get('bg', '#1E1E1E'))
        text_area.set('stroke', self.generator.colors.get('border', '#3C3C3C'))
        text_area.set('stroke-width', '1')
        text_area.set('rx', '2')
        
        # Sample project names
        sample_names = ['Project 1', 'Project 2', 'Project 3']
        for i, name in enumerate(sample_names):
            name_text = ET.SubElement(svg, 'text')
            name_text.set('x', '35')
            name_text.set('y', str(95 + i * 15))
            name_text.set('fill', self.generator.colors.get('secondary_text', '#858585'))
            name_text.set('font-family', 'Arial, sans-serif')
            name_text.set('font-size', '10')
            name_text.text = name
        
        # Right panel (template gallery)
        right_panel = ET.SubElement(svg, 'rect')
        right_panel.set('x', '190')
        right_panel.set('y', '40')
        right_panel.set('width', '190')
        right_panel.set('height', '220')
        right_panel.set('fill', self.generator.colors.get('card_bg', '#252526'))
        right_panel.set('stroke', self.generator.colors.get('border', '#3C3C3C'))
        right_panel.set('stroke-width', '1')
        right_panel.set('rx', '4')
        
        # Gallery title
        gallery_title = ET.SubElement(svg, 'text')
        gallery_title.set('x', '200')
        gallery_title.set('y', '60')
        gallery_title.set('fill', self.generator.colors.get('text', '#CCCCCC'))
        gallery_title.set('font-family', 'Arial, sans-serif')
        gallery_title.set('font-size', '11')
        gallery_title.set('font-weight', 'bold')
        gallery_title.text = 'Template Gallery'
        
        # Add Template button
        self.generator.add_button(
            svg, x=290, y=45, width=80, height=20,
            text="Add Template", highlight=False
        )
        
        # Template cards
        for i in range(2):
            card_x = 200 + (i * 85)
            card = ET.SubElement(svg, 'rect')
            card.set('x', str(card_x))
            card.set('y', '80')
            card.set('width', '70')
            card.set('height', '60')
            card.set('fill', self.generator.colors.get('bg', '#1E1E1E'))
            card.set('stroke', self.generator.colors.get('border', '#3C3C3C'))
            card.set('stroke-width', '1')
            card.set('rx', '4')
            
            # Template icon
            icon = ET.SubElement(svg, 'rect')
            icon.set('x', str(card_x + 20))
            icon.set('y', '90')
            icon.set('width', '30')
            icon.set('height', '20')
            icon.set('fill', self.generator.colors.get('accent', '#2C4F76'))
            icon.set('rx', '2')
            
            # Template name
            template_text = ET.SubElement(svg, 'text')
            template_text.set('x', str(card_x + 35))
            template_text.set('y', '125')
            template_text.set('text-anchor', 'middle')
            template_text.set('fill', self.generator.colors.get('secondary_text', '#858585'))
            template_text.set('font-family', 'Arial, sans-serif')
            template_text.set('font-size', '9')
            template_text.text = f'Template {i+1}'
        
        return self.generator.to_string(svg)
    
    def create_template_creation_illustration(self) -> str:
        """Create template creation step illustration matching actual app"""
        svg = self.generator.create_svg_element()
        
        # Template creation dialog
        dialog = ET.SubElement(svg, 'rect')
        dialog.set('x', '20')
        dialog.set('y', '20')
        dialog.set('width', '360')
        dialog.set('height', '240')
        dialog.set('fill', self.generator.colors.get('card_bg', '#252526'))
        dialog.set('stroke', self.generator.colors.get('border', '#3C3C3C'))
        dialog.set('stroke-width', '2')
        dialog.set('rx', '8')
        
        # Dialog title
        title_text = ET.SubElement(svg, 'text')
        title_text.set('x', '200')
        title_text.set('y', '45')
        title_text.set('text-anchor', 'middle')
        title_text.set('fill', self.generator.colors.get('text', '#CCCCCC'))
        title_text.set('font-family', 'Arial, sans-serif')
        title_text.set('font-size', '14')
        title_text.set('font-weight', 'bold')
        title_text.text = 'Add New Template'
        
        # Template name field
        name_label = ET.SubElement(svg, 'text')
        name_label.set('x', '35')
        name_label.set('y', '75')
        name_label.set('fill', self.generator.colors.get('text', '#CCCCCC'))
        name_label.set('font-family', 'Arial, sans-serif')
        name_label.set('font-size', '11')
        name_label.text = 'Template Name:'
        
        name_input = self.generator.add_text_input(
            svg, x=35, y=80, width=310, height=25,
            placeholder="Enter template name..."
        )
        
        # Project structure area
        structure_label = ET.SubElement(svg, 'text')
        structure_label.set('x', '35')
        structure_label.set('y', '125')
        structure_label.set('fill', self.generator.colors.get('text', '#CCCCCC'))
        structure_label.set('font-family', 'Arial, sans-serif')
        structure_label.set('font-size', '11')
        structure_label.text = 'Project Structure'
        
        structure_area = ET.SubElement(svg, 'rect')
        structure_area.set('x', '35')
        structure_area.set('y', '135')
        structure_area.set('width', '310')
        structure_area.set('height', '80')
        structure_area.set('fill', self.generator.colors.get('bg', '#1E1E1E'))
        structure_area.set('stroke', self.generator.colors.get('border', '#3C3C3C'))
        structure_area.set('stroke-width', '1')
        structure_area.set('rx', '4')
        
        # Drop hint
        drop_hint = ET.SubElement(svg, 'text')
        drop_hint.set('x', '190')
        drop_hint.set('y', '180')
        drop_hint.set('text-anchor', 'middle')
        drop_hint.set('fill', self.generator.colors.get('secondary_text', '#858585'))
        drop_hint.set('font-family', 'Arial, sans-serif')
        drop_hint.set('font-size', '12')
        drop_hint.text = 'Drop Files and Folders Here'
        
        # Save and Cancel buttons
        self.generator.add_button(
            svg, x=250, y=225, width=60, height=25,
            text="Cancel", highlight=False
        )
        
        self.generator.add_button(
            svg, x=320, y=225, width=60, height=25,
            text="Save", highlight=True
        )
        
        return self.generator.to_string(svg)
    
    def create_drag_drop_illustration(self) -> str:
        """Create drag and drop files/folders illustration"""
        svg = self.generator.create_svg_element()
        
        # App window with larger drag area
        window = self.generator.add_app_window_frame(svg, x=30, y=20, width=340, height=200)
        
        # Template name input
        self.generator.add_text_input(
            svg, x=50, y=50, width=200, height=25,
            placeholder="My Template Name"
        )
        
        # Drag and drop area
        drop_area = ET.SubElement(svg, 'rect')
        drop_area.set('x', '50')
        drop_area.set('y', '85')
        drop_area.set('width', '300')
        drop_area.set('height', '120')
        drop_area.set('fill', 'none')
        drop_area.set('stroke', self.generator.colors.get('accent', '#2C4F76'))
        drop_area.set('stroke-width', '2')
        drop_area.set('stroke-dasharray', '5,5')
        drop_area.set('rx', '8')
        
        # Drop area text
        drop_text = ET.SubElement(svg, 'text')
        drop_text.set('x', '200')
        drop_text.set('y', '140')
        drop_text.set('text-anchor', 'middle')
        drop_text.set('fill', self.generator.colors.get('secondary_text', '#858585'))
        drop_text.set('font-family', 'Arial, sans-serif')
        drop_text.set('font-size', '12')
        drop_text.text = 'Drag files and folders here'
        
        # Sample files being dragged
        self.generator.add_file_icon(svg, x=80, y=230, size=20, is_folder=True)
        self.generator.add_file_icon(svg, x=120, y=240, size=16, is_folder=False)
        self.generator.add_file_icon(svg, x=150, y=235, size=16, is_folder=False)
        
        # Drag arrows
        self.generator.add_arrow(svg, 100, 250, 140, 180)
        self.generator.add_arrow(svg, 130, 255, 160, 185)
        
        # Instruction bubble
        self.generator.add_highlight_bubble(
            svg, x=200, y=260, width=180, height=40,
            text="Drag your project files here"
        )
        
        return self.generator.to_string(svg)
    
    def create_smart_patterns_illustration(self) -> str:
        """Create smart patterns/right-click illustration"""
        svg = self.generator.create_svg_element()
        
        # App window
        window = self.generator.add_app_window_frame(svg, x=30, y=20, width=340, height=180)
        
        # File structure area
        structure_area = ET.SubElement(svg, 'rect')
        structure_area.set('x', '50')
        structure_area.set('y', '85')
        structure_area.set('width', '150')
        structure_area.set('height', '100')
        structure_area.set('fill', self.generator.colors.get('bg', '#1E1E1E'))
        structure_area.set('stroke', self.generator.colors.get('border', '#3C3C3C'))
        structure_area.set('stroke-width', '1')
        structure_area.set('rx', '4')
        
        # Sample file structure
        files = [
            ('src/', True, 60, 100),
            ('main.py', False, 75, 115),
            ('config.txt', False, 75, 130),
            ('README.md', False, 60, 145)
        ]
        
        for filename, is_folder, x, y in files:
            self.generator.add_file_icon(svg, x=x, y=y, size=12, is_folder=is_folder)
            
            file_text = ET.SubElement(svg, 'text')
            file_text.set('x', str(x + 18))
            file_text.set('y', str(y + 9))
            file_text.set('fill', self.generator.colors.get('text', '#CCCCCC'))
            file_text.set('font-family', 'Arial, sans-serif')
            file_text.set('font-size', '10')
            file_text.text = filename
        
        # Context menu
        menu = ET.SubElement(svg, 'rect')
        menu.set('x', '220')
        menu.set('y', '100')
        menu.set('width', '120')
        menu.set('height', '80')
        menu.set('fill', self.generator.colors.get('card_bg', '#252526'))
        menu.set('stroke', self.generator.colors.get('border', '#3C3C3C'))
        menu.set('stroke-width', '1')
        menu.set('rx', '4')
        
        # Menu items
        menu_items = ['Smart Rename', 'Add Variables', 'Set Patterns']
        for i, item in enumerate(menu_items):
            item_text = ET.SubElement(svg, 'text')
            item_text.set('x', '230')
            item_text.set('y', str(120 + i * 18))
            item_text.set('fill', self.generator.colors.get('text', '#CCCCCC'))
            item_text.set('font-family', 'Arial, sans-serif')
            item_text.set('font-size', '10')
            item_text.text = item
        
        # Right-click cursor representation
        cursor = ET.SubElement(svg, 'circle')
        cursor.set('cx', '180')
        cursor.set('cy', '140')
        cursor.set('r', '3')
        cursor.set('fill', self.generator.colors.get('accent', '#2C4F76'))
        
        # Instruction bubble
        self.generator.add_highlight_bubble(
            svg, x=50, y=230, width=280, height=40,
            text="Right-click files to set up smart naming patterns"
        )
        
        return self.generator.to_string(svg)
    
    def create_project_creation_illustration(self) -> str:
        """Create final project creation step illustration"""
        svg = self.generator.create_svg_element()
        
        # App window
        window = self.generator.add_app_window_frame(svg, x=30, y=20, width=340, height=180)
        
        # Project name input (highlighted)
        name_input = self.generator.add_text_input(
            svg, x=50, y=50, width=200, height=25,
            placeholder="My Awesome Project"
        )
        # Highlight the input
        highlight = ET.SubElement(svg, 'rect')
        highlight.set('x', '48')
        highlight.set('y', '48')
        highlight.set('width', '204')
        highlight.set('height', '29')
        highlight.set('fill', 'none')
        highlight.set('stroke', self.generator.colors.get('accent', '#2C4F76'))
        highlight.set('stroke-width', '3')
        highlight.set('rx', '5')
        
        # Create project button (highlighted)
        self.generator.add_button(
            svg, x=270, y=50, width=80, height=25,
            text="Create", highlight=True
        )
        
        # Template preview area
        preview_area = ET.SubElement(svg, 'rect')
        preview_area.set('x', '50')
        preview_area.set('y', '85')
        preview_area.set('width', '300')
        preview_area.set('height', '100')
        preview_area.set('fill', self.generator.colors.get('bg', '#1E1E1E'))
        preview_area.set('stroke', self.generator.colors.get('border', '#3C3C3C'))
        preview_area.set('stroke-width', '1')
        preview_area.set('rx', '4')
        
        # Preview text
        preview_text = ET.SubElement(svg, 'text')
        preview_text.set('x', '200')
        preview_text.set('y', '140')
        preview_text.set('text-anchor', 'middle')
        preview_text.set('fill', self.generator.colors.get('secondary_text', '#858585'))
        preview_text.set('font-family', 'Arial, sans-serif')
        preview_text.set('font-size', '11')
        preview_text.text = 'Template ready! Enter project name and create.'
        
        # Instruction bubble
        self.generator.add_highlight_bubble(
            svg, x=80, y=230, width=240, height=40,
            text="Name your project and click Create!"
        )
        
        return self.generator.to_string(svg)
    
    def create_completion_illustration(self) -> str:
        """Create completion/success illustration"""
        svg = self.generator.create_svg_element()
        
        # App window
        window = self.generator.add_app_window_frame(svg, x=30, y=20, width=340, height=180)
        
        # Success checkmark
        checkmark = ET.SubElement(svg, 'circle')
        checkmark.set('cx', '200')
        checkmark.set('cy', '130')
        checkmark.set('r', '30')
        checkmark.set('fill', self.generator.colors.get('success', '#4CAF50'))
        checkmark.set('stroke', self.generator.colors.get('border', '#3C3C3C'))
        checkmark.set('stroke-width', '2')
        
        # Checkmark symbol
        check_path = ET.SubElement(svg, 'path')
        check_path.set('d', 'M 185 130 L 195 140 L 215 120')
        check_path.set('stroke', 'white')
        check_path.set('stroke-width', '4')
        check_path.set('stroke-linecap', 'round')
        check_path.set('stroke-linejoin', 'round')
        check_path.set('fill', 'none')
        
        # Success message
        success_text = ET.SubElement(svg, 'text')
        success_text.set('x', '200')
        success_text.set('y', '170')
        success_text.set('text-anchor', 'middle')
        success_text.set('fill', self.generator.colors.get('text', '#CCCCCC'))
        success_text.set('font-family', 'Arial, sans-serif')
        success_text.set('font-size', '12')
        success_text.set('font-weight', 'bold')
        success_text.text = 'Project Created Successfully!'
        
        # Completion bubble
        self.generator.add_highlight_bubble(
            svg, x=60, y=230, width=280, height=40,
            text="Great! You've created your first project template"
        )
        
        return self.generator.to_string(svg)
    
    def get_illustration_for_slide(self, slide_index: int) -> str:
        """Get the SVG illustration for a specific slide index.
        If a matching file exists in sample_svgs directory, use that instead."""
        
        # Check if we have a direct file in sample_svgs directory
        sample_svg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                        "sample_svgs", f"slide_{slide_index}.svg")
                        
        if os.path.exists(sample_svg_path):
            # Read the SVG file content directly
            try:
                with open(sample_svg_path, 'r') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading SVG file {sample_svg_path}: {e}")
        
        # Fall back to generated SVGs
        if slide_index == 0:
            return self.create_welcome_illustration()
        elif slide_index == 1:
            return self.create_template_creation_illustration()
        elif slide_index == 2:
            return self.create_drag_drop_illustration()
        elif slide_index == 3:
            return self.create_smart_patterns_illustration()
        elif slide_index == 4:
            return self.create_project_creation_illustration()
        elif slide_index == 5:
            return self.create_completion_illustration()
        else:
            # Fallback to generic illustration
            return self.create_welcome_illustration() 