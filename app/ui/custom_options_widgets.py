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
        
        # Setup clean styling without blue outlines
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['border']};
                border-radius: 6px;
                margin: 2px 0px;
            }}
        """)
        
        # Create main layout with tighter spacing
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 10, 12, 10)
        self.layout.setSpacing(6)
        
        # Add simplified title
        self.title_label = QLabel("Custom Options Required")
        self.title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {colors['text']};
            margin: 0px;
            padding: 0px;
            border: none;
            background-color: transparent;
        """)
        self.layout.addWidget(self.title_label)
    
    def set_custom_options(self, custom_prompts):
        """Set the custom options and create UI controls"""
        self.custom_options = custom_prompts
        self.combo_widgets.clear()
        
        # Clear existing option widgets (keep title)
        self._clear_option_widgets()
        
        # Create dropdown widgets for each custom option
        option_count = 0
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
            
            option_count += 1
            # Use simple generic labels instead of showing file paths or complex names
            if len(custom_prompts) == 1:
                display_label = "Select option"
            else:
                display_label = f"Option {option_count}"
                
            self._create_option_widget(display_label, options, key)
    
    def _clear_option_widgets(self):
        """Clear existing option widgets while preserving title"""
        items_to_remove = []
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # Only remove option widgets, not title
                if (hasattr(widget, 'objectName') and 
                    widget.objectName() == 'custom_option_widget'):
                    items_to_remove.append(widget)
        
        for widget in items_to_remove:
            self.layout.removeWidget(widget)
            widget.setParent(None)
    
    def _create_option_widget(self, display_key, options, actual_key):
        """Create a single option widget with label and dropdown"""
        # Create container for this option
        option_container = QWidget()
        option_container.setObjectName('custom_option_widget')
        option_container.setStyleSheet("background-color: transparent; border: none;")
        option_layout = QVBoxLayout(option_container)
        option_layout.setContentsMargins(0, 2, 0, 2)
        option_layout.setSpacing(3)
        
        # Create clean label
        label = QLabel(f"{display_key}:")
        label.setStyleSheet(f"""
            color: {colors['text']};
            font-weight: normal;
            font-size: 12px;
            margin: 0px;
            padding: 0px;
            border: none;
            background-color: transparent;
        """)
        option_layout.addWidget(label)
        
        # Create dropdown with clean styling
        combo = QComboBox()
        combo.addItems(options)
        combo.setStyleSheet(COMBOBOX_STYLE)
        combo.setMinimumHeight(28)
        
        # Connect to update preview if method exists
        if hasattr(self, '_update_preview'):
            combo.currentTextChanged.connect(self._update_preview)
        
        option_layout.addWidget(combo)
        
        # Store the combo widget using the actual key
        self.combo_widgets[actual_key] = combo
        
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
    """Animated custom options widget with slide-up/down animation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set initial height to 0 for animation
        self.setFixedHeight(0)
        
        # Setup animation
        self.animation = QPropertyAnimation(self, b"maximumHeight")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Add stability timer to prevent rapid hide/show cycles
        from PyQt6.QtCore import QTimer
        self._stability_timer = QTimer()
        self._stability_timer.setSingleShot(True)
        self._stability_timer.timeout.connect(self._execute_pending_slide_down)
        self._pending_slide_down = False
    
    def _create_option_widget(self, display_key, options, actual_key):
        """Override to connect preview updates"""
        super()._create_option_widget(display_key, options, actual_key)
        # Connect the newly created combo to preview updates
        if actual_key in self.combo_widgets:
            self.combo_widgets[actual_key].currentTextChanged.connect(self._update_preview)
    
    def _update_preview(self):
        """Update the preview with current selections - simplified version"""
        # This method is called but we don't need to show preview in the widget itself
        # The preview is handled elsewhere in the UI
        pass
    
    def set_custom_options(self, custom_prompts):
        """Override to update preview after setting options"""
        super().set_custom_options(custom_prompts)
        # Update preview if we have a pattern
        if hasattr(self, 'preview_pattern') and self.preview_pattern:
            self._update_preview()
    
    def slide_up(self):
        """Animate the widget sliding up"""
        print(f"DEBUG: slide_up called, is_visible={self.is_visible}, isVisible()={self.isVisible()}")
        
        # Cancel any pending slide down
        self._pending_slide_down = False
        self._stability_timer.stop()
        
        # Check both our flag and Qt's actual visibility
        if self.is_visible and self.isVisible():
            print(f"DEBUG: Widget already visible, returning early")
            return
            
        print(f"DEBUG: Proceeding with slide up animation")
        self.is_visible = True
        self.show()
        
        # Calculate target height based on content
        self.adjustSize()
        target_height = self.sizeHint().height()
        
        # Start animation
        self.animation.setStartValue(0)
        self.animation.setEndValue(target_height)
        self.animation.start()
    
    def slide_down(self, delay_ms=500):
        """Animate the widget sliding down with optional delay for stability"""
        if not self.is_visible:
            return
        
        # If delay is requested, use stability timer
        if delay_ms > 0:
            self._pending_slide_down = True
            self._stability_timer.start(delay_ms)
            return
        
        # Execute immediate slide down
        self._pending_slide_down = True  # Set flag for immediate execution too
        self._execute_pending_slide_down()
    
    def _execute_pending_slide_down(self):
        """Execute the actual slide down animation"""
        print(f"DEBUG: _execute_pending_slide_down called, is_visible={self.is_visible}")
        
        # Reset pending flag
        self._pending_slide_down = False
        
        if not self.is_visible:
            print(f"DEBUG: Widget already hidden, returning early")
            return
            
        print(f"DEBUG: Proceeding with slide down animation")
        self.is_visible = False
        
        # Disconnect any previous connections to avoid multiple calls
        try:
            self.animation.finished.disconnect()
        except:
            pass
        
        # Animate to height 0, then hide
        self.animation.setStartValue(self.height())
        self.animation.setEndValue(0)
        self.animation.finished.connect(self._on_slide_down_finished)
        self.animation.start()
    
    def _on_slide_down_finished(self):
        """Called when slide down animation completes"""
        print(f"DEBUG: Slide down animation finished")
        self.hide()
        # Ensure is_visible flag is properly set
        self.is_visible = False
    
    def _update_unified_preview(self):
        """Update the unified preview (compatibility method)"""
        self._update_preview() 