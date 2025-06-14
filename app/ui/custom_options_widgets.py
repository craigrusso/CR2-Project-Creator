#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Custom Options Widgets for Template Customization
Provides both simple and animated versions of custom options widgets
"""

import datetime
import re
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont

from app.ui.color_scheme_pyqt import colors, COMBOBOX_STYLE


class BaseCustomOptionsWidget(QWidget):
    """Base class for custom options widgets with common functionality"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.custom_options = {}
        self.combo_widgets = {}
        self.is_visible = False
        self.preview_pattern = ''
        
        # Setup basic styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['card_bg']};
                border: 2px solid {colors['accent']};
                border-radius: 8px;
                margin: 5px 0px;
            }}
        """)
        
        # Create main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)
        
        # Add title
        self.title_label = QLabel("Custom Options Required")
        self.title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {colors['text']};
            margin: 10px 0px;
        """)
        self.layout.addWidget(self.title_label)
        
        # Add description
        self.desc_label = QLabel("This template requires custom options. Please select values below:")
        self.desc_label.setStyleSheet(f"""
            font-size: 12px;
            color: {colors['secondary_text']};
            margin-bottom: 15px;
        """)
        self.layout.addWidget(self.desc_label)
    
    def set_custom_options(self, custom_prompts):
        """Set the custom options and create UI controls"""
        self.custom_options = custom_prompts
        self.combo_widgets.clear()
        
        # Clear existing option widgets (keep title and description)
        self._clear_option_widgets()
        
        # Create dropdown widgets for each custom option
        for key, prompt_data in custom_prompts.items():
            # Handle both old format (direct list) and new format (dict with 'options' key)
            if isinstance(prompt_data, dict):
                options = prompt_data.get('options', [])
            elif isinstance(prompt_data, list):
                options = prompt_data
            else:
                continue
                
            if not options:
                continue
                
            self._create_option_widget(key, options)
    
    def _clear_option_widgets(self):
        """Clear existing option widgets while preserving title and description"""
        items_to_remove = []
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # Only remove option widgets, not title/description
                if (hasattr(widget, 'objectName') and 
                    widget.objectName() == 'custom_option_widget'):
                    items_to_remove.append(widget)
        
        for widget in items_to_remove:
            self.layout.removeWidget(widget)
            widget.setParent(None)
    
    def _create_option_widget(self, key, options):
        """Create a single option widget with label and dropdown"""
        # Create container for this option
        option_container = QWidget()
        option_container.setObjectName('custom_option_widget')
        option_layout = QVBoxLayout(option_container)
        option_layout.setContentsMargins(0, 5, 0, 5)
        option_layout.setSpacing(5)
        
        # Create label
        label = QLabel(f"{key}:")
        label.setStyleSheet(f"""
            color: {colors['text']};
            font-weight: bold;
            margin-bottom: 5px;
        """)
        option_layout.addWidget(label)
        
        # Create dropdown
        combo = QComboBox()
        combo.addItems(options)
        combo.setStyleSheet(COMBOBOX_STYLE)
        combo.setMinimumHeight(32)
        
        # Connect to update preview if method exists
        if hasattr(self, '_update_preview'):
            combo.currentTextChanged.connect(self._update_preview)
        
        option_layout.addWidget(combo)
        
        # Store the combo widget
        self.combo_widgets[key] = combo
        
        # Add to main layout
        self.layout.addWidget(option_container)
    
    def get_selected_values(self):
        """Get the selected values from all dropdowns"""
        return {key: combo.currentText() for key, combo in self.combo_widgets.items()}
    
    def slide_up(self):
        """Show the widget (base implementation)"""
        self.is_visible = True
        self.show()
        
    def slide_down(self):
        """Hide the widget (base implementation)"""
        self.is_visible = False
        self.hide()


class SimpleCustomOptionsWidget(BaseCustomOptionsWidget):
    """Simple custom options widget without animation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def _update_unified_preview(self):
        """Update the preview (dummy method for compatibility)"""
        pass


class AnimatedCustomOptionsWidget(BaseCustomOptionsWidget):
    """Animated custom options widget with slide-up/down animation and preview"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set initial height to 0 for animation
        self.setFixedHeight(0)
        
        # Add preview area after description
        self.preview_label = QLabel("Preview: ")
        self.preview_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: {colors['card_bg_alt']};
            border: 2px solid {colors['border']};
            border-radius: 6px;
            padding: 12px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 15px;
            min-height: 20px;
        """)
        # Insert preview after description (index 2)
        self.layout.insertWidget(2, self.preview_label)
        
        # Setup animation
        self.animation = QPropertyAnimation(self, b"maximumHeight")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def _create_option_widget(self, key, options):
        """Override to connect preview updates"""
        super()._create_option_widget(key, options)
        # Connect the newly created combo to preview updates
        if key in self.combo_widgets:
            self.combo_widgets[key].currentTextChanged.connect(self._update_preview)
    
    def _update_preview(self):
        """Update the preview with current selections"""
        if not hasattr(self, 'preview_pattern') or not self.preview_pattern:
            return
             
        preview = self.preview_pattern
        selections = self.get_selected_values()
        
        # Replace basic placeholders with sample values
        preview = preview.replace('${PROJECT_NAME}', 'MyProject')
        
        # Handle date/time placeholders
        now = datetime.datetime.now()
        preview = preview.replace('${DATE}', now.strftime('%Y%m%d'))
        preview = preview.replace('${TIME}', now.strftime('%H%M%S'))
        
        # Handle base name for files
        if '${BASE}' in preview:
            preview = preview.replace('${BASE}', 'example')
        
        # Handle custom placeholders with actual selections
        custom_matches = re.findall(r'\$\{(CUSTOM\d*)\}', preview)
        if custom_matches:
            for match in custom_matches:
                placeholder = f"${{{match}}}"
                # Find the corresponding selection
                for key, value in selections.items():
                    if key.endswith(f"_{match}"):
                        preview = preview.replace(placeholder, value)
                        break
                else:
                    # If no selection found, replace with placeholder name
                    preview = preview.replace(placeholder, f"[{match}]")
        
        # Handle file extension
        if '${EXT}' in preview:
            preview = preview.replace('${EXT}', '.prproj')
        
        self.preview_label.setText(f"Preview: {preview}")
    
    def set_custom_options(self, custom_prompts):
        """Override to update preview after setting options"""
        super().set_custom_options(custom_prompts)
        # Update preview if we have a pattern
        if hasattr(self, 'preview_pattern') and self.preview_pattern:
            self._update_preview()
    
    def slide_up(self):
        """Animate the widget sliding up"""
        if self.is_visible:
            return
            
        self.is_visible = True
        self.show()
        
        # Calculate target height based on content
        self.adjustSize()
        target_height = self.sizeHint().height()
        
        # Add extra height for multiple dropdowns
        if len(self.combo_widgets) > 1:
            extra_height = (len(self.combo_widgets) - 1) * 80
            target_height += extra_height
        
        # Ensure minimum height for readability
        target_height = max(target_height, 200)
        
        self.animation.setStartValue(0)
        self.animation.setEndValue(target_height)
        self.animation.start()
    
    def slide_down(self):
        """Animate the widget sliding down"""
        if not self.is_visible:
            return
            
        self.is_visible = False
        
        self.animation.setStartValue(self.height())
        self.animation.setEndValue(0)
        self.animation.finished.connect(self.hide)
        self.animation.start()
    
    def _update_unified_preview(self):
        """Alias for _update_preview for compatibility"""
        self._update_preview() 