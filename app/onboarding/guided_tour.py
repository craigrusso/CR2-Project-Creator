#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Guided Tour Component

Provides an interactive guided tour with animated tooltips that highlight
specific UI elements and guide users through the app step by step.
"""

from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, 
                           QHBoxLayout, QFrame, QGraphicsOpacityEffect,
                           QApplication)
from PyQt6.QtCore import (Qt, QTimer, QPropertyAnimation, QEasingCurve, 
                        pyqtSignal, QRect, QPoint, QSize)
from PyQt6.QtGui import (QFont, QPalette, QColor, QPainter, QPen, QBrush,
                       QPixmap, QIcon, QRegion)
from app.ui.color_scheme_pyqt import get_color, colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE
import time


class TourTooltip(QWidget):
    """Animated tooltip for guided tour steps"""
    
    next_clicked = pyqtSignal()
    previous_clicked = pyqtSignal()
    skip_clicked = pyqtSignal()
    
    def __init__(self, title, content, step_number, total_steps, parent=None):
        super().__init__(parent)
        self.title = title
        self.content = content
        self.step_number = step_number
        self.total_steps = total_steps
        
        # Widget properties
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(320, 200)  # Smaller size
        
        self._setup_ui()
        self._setup_animations()
    
    def _setup_ui(self):
        """Setup the tooltip UI"""
        # Main frame - styled like a cute thought bubble
        self.main_frame = QFrame(self)
        self.main_frame.setGeometry(0, 0, 320, 200)
        self.main_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {get_color('card_bg')};
                border: 2px solid {get_color('accent')};
                border-radius: 12px;
                padding: 15px;
            }}
        """)
        
        # Main layout
        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header with title and close button
        header_layout = QHBoxLayout()
        
        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.title_label.setStyleSheet(f"color: {get_color('text')}; border: none;")
        self.title_label.setWordWrap(True)
        header_layout.addWidget(self.title_label, 1)
        
        # Close button
        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(20, 20)
        self.close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {get_color('secondary_text')};
                border: none;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {get_color('danger')};
                color: white;
                border-radius: 10px;
            }}
        """)
        self.close_button.clicked.connect(self.skip_clicked.emit)
        header_layout.addWidget(self.close_button)
        
        layout.addLayout(header_layout)
        
        # Content
        self.content_label = QLabel(self.content)
        self.content_label.setFont(QFont("Arial", 10))
        self.content_label.setStyleSheet(f"color: {get_color('secondary_text')}; border: none;")
        self.content_label.setWordWrap(True)
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.content_label, 1)
        
        # Progress indicator
        progress_text = f"Step {self.step_number} of {self.total_steps}"
        self.progress_label = QLabel(progress_text)
        self.progress_label.setFont(QFont("Arial", 9))
        self.progress_label.setStyleSheet(f"color: {get_color('accent')}; border: none;")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Skip button
        self.skip_button = QPushButton("Skip Tour")
        self.skip_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {get_color('secondary_text')};
                border: 1px solid {get_color('border')};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {get_color('bg')};
            }}
        """)
        self.skip_button.clicked.connect(self.skip_clicked.emit)
        button_layout.addWidget(self.skip_button)
        
        button_layout.addStretch()
        
        # Previous button
        self.prev_button = QPushButton("← Previous")
        self.prev_button.setVisible(self.step_number > 1)
        self.prev_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {get_color('border')};
                color: {get_color('text')};
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {get_color('accent')};
            }}
        """)
        self.prev_button.clicked.connect(self.previous_clicked.emit)
        button_layout.addWidget(self.prev_button)
        
        # Next button
        next_text = "Finish" if self.step_number == self.total_steps else "Next →"
        self.next_button = QPushButton(next_text)
        self.next_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {get_color('accent')};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {get_color('accent')};
            }}
        """)
        self.next_button.clicked.connect(self.next_clicked.emit)
        button_layout.addWidget(self.next_button)
        
        layout.addLayout(button_layout)
    
    def _setup_animations(self):
        """Setup entrance and exit animations"""
        # Opacity animation
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Scale animation (simulated with resize)
        self.original_size = self.size()
    
    def show_animated(self):
        """Show the tooltip with animation"""
        # Start with opacity 0
        self.opacity_effect.setOpacity(0.0)
        self.show()
        
        # Animate to full opacity
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
    
    def hide_animated(self):
        """Hide the tooltip with animation"""
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.start()
    
    def position_near_widget(self, target_widget, offset=QPoint(20, 20)):
        """Position the tooltip near a target widget"""
        if not target_widget:
            return
            
        # Get target widget's global position and size
        target_rect = target_widget.geometry()
        target_global_pos = target_widget.mapToGlobal(QPoint(0, 0))
        target_global_rect = QRect(target_global_pos, target_rect.size())
        
        # Calculate tooltip position
        tooltip_pos = QPoint(
            target_global_rect.right() + offset.x(),
            target_global_rect.top() + offset.y()
        )
        
        # Ensure tooltip stays on screen
        screen = QApplication.primaryScreen().geometry()
        if tooltip_pos.x() + self.width() > screen.width():
            # Position to the left of target
            tooltip_pos.setX(target_global_rect.left() - self.width() - offset.x())
        
        if tooltip_pos.y() + self.height() > screen.height():
            # Position above target
            tooltip_pos.setY(target_global_rect.bottom() - self.height() - offset.y())
        
        # Ensure minimum distance from screen edges
        tooltip_pos.setX(max(10, tooltip_pos.x()))
        tooltip_pos.setY(max(10, tooltip_pos.y()))
        
        self.move(tooltip_pos)


class HighlightOverlay(QWidget):
    """Overlay to highlight specific widgets during guided tour"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlight_rect = QRect()
        self.highlight_radius = 8
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # Don't block mouse events
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        
    def set_highlight_widget(self, widget):
        """Set the widget to highlight"""
        if widget and widget.isVisible():
            # Get the parent widget to position the overlay
            parent = self.parent() or widget.window()
            if parent:
                self.setParent(parent)
                self.resize(parent.size())
                
                # Get widget position relative to parent
                widget_pos = widget.mapTo(parent, QPoint(0, 0))
                self.highlight_rect = QRect(
                    widget_pos.x() - 5,
                    widget_pos.y() - 5,
                    widget.width() + 10,
                    widget.height() + 10
                )
                
                self.show()
                self.update()
            else:
                self.hide()
        else:
            self.hide()
    
    def paintEvent(self, event):
        """Paint the overlay with highlighted area"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Only draw highlight border - no overlay
        if not self.highlight_rect.isEmpty():
            # Draw highlight border - bright and animated
            painter.setPen(QPen(QColor(get_color('accent')), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(self.highlight_rect, self.highlight_radius, self.highlight_radius)
            
            # Add a subtle glow effect
            glow_pen = QPen(QColor(get_color('accent')))
            glow_pen.setWidth(1)
            painter.setPen(glow_pen)
            painter.drawRoundedRect(
                self.highlight_rect.adjusted(-2, -2, 2, 2), 
                self.highlight_radius + 2, 
                self.highlight_radius + 2
            )


class GuidedTour(QWidget):
    """Main guided tour controller"""
    
    # Signals
    completed = pyqtSignal()
    skipped = pyqtSignal()
    step_changed = pyqtSignal(int)  # step_index
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.current_step = 0
        self.current_tooltip = None
        self.overlay = HighlightOverlay()
        self._setup_tour_steps()
    
    def _setup_tour_steps(self):
        """Define the guided tour steps"""
        self.tour_steps = [
            {
                'title': '👋 Welcome to Echelon!',
                'content': 'Let me show you around Echelon\'s main interface. This is where all the magic happens!',
                'target_widget_name': None,
                'highlight': False
            },
            {
                'title': '📁 Template Gallery',
                'content': 'This is your template gallery where all your saved templates live. Any templates you create will appear here as cards.',
                'target_widget_name': 'template_gallery',
                'highlight': True
            },
            {
                'title': '📝 Project Names',
                'content': 'Here\'s where you\'ll enter project names when you\'re ready to create new projects. You can create single or multiple projects at once.',
                'target_widget_name': 'project_name_field',
                'highlight': True
            },
            {
                'title': '⚙️ Smart Options',
                'content': 'These controls let you customize how your projects are created - versioning, date sequences, and other powerful features.',
                'target_widget_name': 'structure_editor',
                'highlight': True
            },
            {
                'title': '🎯 Add Template',
                'content': 'Ready to create your first template? Click this button to start the template creation process!',
                'target_widget_name': 'add_template_button',
                'highlight': True
            },
            {
                'title': '🚀 You\'re Ready!',
                'content': 'That\'s the tour! You now know where everything is. Ready to create your first template?',
                'target_widget_name': None,
                'highlight': False
            }
        ]
    
    def start_tour(self):
        """Start the guided tour"""
        if not self.parent_widget:
            return
            
        self.current_step = 0
        self._show_current_step()
    
    def _show_current_step(self):
        """Show the current tour step"""
        if self.current_step >= len(self.tour_steps):
            self._complete_tour()
            return
        
        step = self.tour_steps[self.current_step]
        
        # Find the target widget
        target_widget = self._find_widget_by_name(step['target_widget_name'])
        
        # Show highlight overlay if needed
        if step.get('highlight', False) and target_widget:
            self.overlay.set_highlight_widget(target_widget)
        else:
            self.overlay.hide()
        
        # Create and show tooltip
        self.current_tooltip = TourTooltip(
            step['title'],
            step['content'],
            self.current_step + 1,
            len(self.tour_steps),
            self.parent_widget
        )
        
        # Connect signals
        self.current_tooltip.next_clicked.connect(self._next_step)
        self.current_tooltip.previous_clicked.connect(self._previous_step)
        self.current_tooltip.skip_clicked.connect(self._skip_tour)
        
        # Position tooltip
        if target_widget:
            self.current_tooltip.position_near_widget(target_widget)
        else:
            # Center on screen if no target widget
            self.current_tooltip.move(
                QApplication.primaryScreen().geometry().center() - 
                QPoint(self.current_tooltip.width() // 2, self.current_tooltip.height() // 2)
            )
        
        # Show with animation
        self.current_tooltip.show_animated()
        
        # Emit signal
        self.step_changed.emit(self.current_step)
    
    def _find_widget_by_name(self, widget_name):
        """Find a widget by its object name in the parent widget hierarchy"""
        if not self.parent_widget or not widget_name:
            return None
        
        print(f"DEBUG: Looking for widget '{widget_name}'")
        
        # First try direct object name search
        widget = self.parent_widget.findChild(QWidget, widget_name)
        if widget:
            print(f"DEBUG: Found widget '{widget_name}' by object name")
            return widget
        
        # If not found, try searching by attribute paths
        widget_search_paths = {
            'template_gallery': ['template_gallery'],
            'project_name_field': ['batch_text_edit'],
            'structure_editor': ['versioning_options', 'enable_versioning'],
            'add_template_button': ['template_gallery.add_template_button']
        }
        
        if widget_name in widget_search_paths:
            for path in widget_search_paths[widget_name]:
                try:
                    obj = self.parent_widget
                    for attr in path.split('.'):
                        obj = getattr(obj, attr)
                    if obj and hasattr(obj, 'isVisible'):
                        print(f"DEBUG: Found widget '{widget_name}' at path '{path}'")
                        return obj
                except AttributeError:
                    continue
        
        # If still not found, try comprehensive search by class name and properties
        print(f"DEBUG: Searching comprehensively for '{widget_name}'")
        
        # Search all QPushButton widgets for "Add Template" button
        if widget_name == 'add_template_button':
            buttons = self.parent_widget.findChildren(QPushButton)
            for button in buttons:
                if button.text() in ['Add Template', 'New Template']:
                    print(f"DEBUG: Found Add Template button by text: '{button.text()}'")
                    return button
        
        # Search for template gallery by class
        elif widget_name == 'template_gallery':
            # Try to find TemplateGallery widget
            from app.gallery.gallery_widget import TemplateGallery
            galleries = self.parent_widget.findChildren(TemplateGallery)
            if galleries:
                print(f"DEBUG: Found TemplateGallery widget")
                return galleries[0]
        
        # Search for text edit widgets
        elif widget_name == 'project_name_field':
            from PyQt6.QtWidgets import QTextEdit
            text_edits = self.parent_widget.findChildren(QTextEdit)
            for edit in text_edits:
                if hasattr(edit, 'placeholderText') and 'Project' in edit.placeholderText():
                    print(f"DEBUG: Found project text edit by placeholder")
                    return edit
            # If not found by placeholder, return first text edit
            if text_edits:
                print(f"DEBUG: Using first text edit widget")
                return text_edits[0]
        
        print(f"WARNING: Could not find widget '{widget_name}'")
        return None
    
    def _next_step(self):
        """Move to the next step"""
        if self.current_tooltip:
            self.current_tooltip.hide_animated()
            self.current_tooltip = None
        
        self.current_step += 1
        self._show_current_step()
    
    def _previous_step(self):
        """Move to the previous step"""
        if self.current_tooltip:
            self.current_tooltip.hide_animated()
            self.current_tooltip = None
        
        if self.current_step > 0:
            self.current_step -= 1
            self._show_current_step()
    
    def _skip_tour(self):
        """Skip the guided tour"""
        self._cleanup()
        self.skipped.emit()
    
    def _complete_tour(self):
        """Complete the guided tour"""
        self._cleanup()
        self.completed.emit()
    
    def _cleanup(self):
        """Clean up tour resources"""
        if self.current_tooltip:
            self.current_tooltip.hide()
            self.current_tooltip = None
        
        self.overlay.hide()
    
    def stop_tour(self):
        """Stop the tour (called externally)"""
        self._cleanup()
    
    def set_target_widget_by_name(self, step_index, widget_name):
        """Update the target widget name for a specific step"""
        if 0 <= step_index < len(self.tour_steps):
            self.tour_steps[step_index]['target_widget_name'] = widget_name 