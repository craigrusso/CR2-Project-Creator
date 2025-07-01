#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Tutorial Slideshow Component

Provides an attractive slideshow-style tutorial with smooth transitions,
animations, and modern UI design.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame, QStackedWidget, QWidget,
                           QGraphicsOpacityEffect, QProgressBar, QSizePolicy)
from PyQt6.QtCore import (Qt, QTimer, QPropertyAnimation, QEasingCurve, 
                        pyqtSignal, QRect, QEvent, QByteArray, QPoint, QPointF, QLineF, QSizeF, QRectF)
from PyQt6.QtGui import (QFont, QPalette, QColor, QPainter, QPen, QBrush,
                       QPixmap, QIcon, QMovie, QPolygonF, QPainterPath)
from app.ui.color_scheme_pyqt import get_color, colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, APP_COLORS
from app.templates.components.utils import get_system_font, get_slideshow_title_font_size, get_slideshow_description_font_size, get_platform_css_font_size, get_dynamic_font_size
from app.constants import get_resource_path
try:
    from .tutorial_illustrations import TutorialIllustrations
except ImportError:
    TutorialIllustrations = None
from .config import CUSTOM_SLIDESHOW_CONTENT, TUTORIAL_CONTENT # Import configuration
import os
import math
import platform





class ImageWithArrow(QWidget):
    """A widget to display a pixmap with optional overlays and multi-step animations."""
    
    # Signal for step changes
    step_changed = pyqtSignal(int)  # current_step
    
    def __init__(self, pixmap=None, arrow_data=None, crop_rect=None, arrow_delay=None, arrow_image_path=None, multi_step_sequence=None, parent=None):
        super().__init__(parent)
        self.original_pixmap = pixmap if pixmap else QPixmap()
        self.arrow_data = arrow_data
        self.crop_rect = crop_rect
        self.arrow_svg = None
        self.arrow_delay = arrow_delay  # Always set this
        self.multi_step_sequence = multi_step_sequence or []
        self.current_step = 0
        self.total_steps = len(self.multi_step_sequence) if self.multi_step_sequence else (1 if (arrow_delay or arrow_image_path) else 0)
        
        # Set size policy to expand and fill the available space
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Animation states
        self.show_arrow = False
        self.arrow_opacity = 0.0
        self.show_overlay = False
        self.overlay_opacity = 0.0
        self.show_final_arrow = False
        self.final_arrow_opacity = 0.0
        self.show_advanced_arrow = False
        self.advanced_arrow_opacity = 0.0
        
        # Current images
        self.current_arrow_image = None
        self.overlay_image = None
        self.final_arrow_image = None
        self.advanced_arrow_image = None
        
        # Timer management
        self.active_timers = []
        
        # Setup fade animations
        self.arrow_opacity_effect = QGraphicsOpacityEffect()
        self.arrow_fade_animation = QPropertyAnimation(self.arrow_opacity_effect, b"opacity")
        self.arrow_fade_animation.setDuration(500)  # 500ms fade-in
        self.arrow_fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Load the initial arrow image (PNG or SVG)
        if arrow_image_path:
            resolved_arrow_path = get_resource_path(arrow_image_path)
            if os.path.exists(resolved_arrow_path):
                self.arrow_svg = QPixmap(resolved_arrow_path)
        # Note: Removed fallback curved arrow as file doesn't exist
        
        # Set initial state
        if self.arrow_data or arrow_image_path:  # Show arrow if we have either positioning data OR an arrow image
            if not arrow_delay and not multi_step_sequence:
                self.show_arrow = True
                self.arrow_opacity = 1.0

    def get_total_steps(self):
        """Get the total number of animation steps for this widget"""
        return self.total_steps

    def get_current_step(self):
        """Get the current animation step (0-based)"""
        return self.current_step

    def jump_to_step(self, step_index):
        """Jump directly to a specific animation step"""
        if step_index < 0 or step_index >= self.total_steps:
            return
        
        # Stop all current animations and timers
        self.stop_animations()
        
        # Reset state
        self.reset_animation_state()
        
        if self.multi_step_sequence:
            # Jump to specific step in multi-step sequence
            self.current_step = step_index
            self._jump_to_multi_step(step_index)
        else:
            # For simple arrow animations, step 0 = no arrow, step 1 = arrow shown
            self.current_step = step_index
            if step_index == 0:
                # No arrow state
                pass
            elif step_index == 1 and (self.arrow_data or self.arrow_svg):
                # Show arrow immediately
                self.show_arrow = True
                self.arrow_opacity = 1.0
                self.update()
        
        # Emit step change signal
        self.step_changed.emit(self.current_step)

    def _jump_to_multi_step(self, target_step):
        """Jump to a specific step in the multi-step sequence"""
        # Apply all effects up to and including the target step
        for i in range(target_step + 1):
            if i < len(self.multi_step_sequence):
                step_data = self.multi_step_sequence[i]
                self._apply_step_immediately(step_data, i)
        
        self.update()

    def _apply_step_immediately(self, step_data, step_index):
        """Apply a step's effects immediately without animation"""
        action = step_data.get('action', 'show_arrow')
        
        if action == 'show_arrow':
            # Load and show the arrow immediately
            arrow_image_path = step_data.get('arrow_image')
            if arrow_image_path:
                resolved_path = get_resource_path(arrow_image_path)
                if os.path.exists(resolved_path):
                    self.current_arrow_image = QPixmap(resolved_path)
                    self.show_arrow = True
                    self.arrow_opacity = 1.0
                
        elif action == 'fade_arrow_show_overlay':
            # Hide arrow and show overlay immediately
            if step_index > 0:  # Only hide arrow if we had one from previous step
                self.show_arrow = False
                self.arrow_opacity = 0.0
            
            overlay_image_path = step_data.get('overlay_image')
            if overlay_image_path:
                resolved_path = get_resource_path(overlay_image_path)
                if os.path.exists(resolved_path):
                    self.overlay_image = QPixmap(resolved_path)
                    self.show_overlay = True
                    self.overlay_opacity = 1.0
                
        elif action == 'show_final_arrow':
            # Show final arrow on top of overlay immediately
            arrow_image_path = step_data.get('arrow_image')
            if arrow_image_path:
                resolved_path = get_resource_path(arrow_image_path)
                if os.path.exists(resolved_path):
                    self.final_arrow_image = QPixmap(resolved_path)
                    self.show_final_arrow = True
                    self.final_arrow_opacity = 1.0
                
        elif action == 'show_advanced_arrow':
            # Show advanced arrow on top of everything immediately
            arrow_image_path = step_data.get('arrow_image')
            if arrow_image_path:
                resolved_path = get_resource_path(arrow_image_path)
                if os.path.exists(resolved_path):
                    self.advanced_arrow_image = QPixmap(resolved_path)
                    self.show_advanced_arrow = True
                    self.advanced_arrow_opacity = 1.0

    def start_arrow_animation(self):
        """Start the animation sequence when the slide becomes visible"""
        # Always reset the slide state first
        self.reset_animation_state()
        
        if self.multi_step_sequence:
            # Start multi-step sequence
            self.current_step = 0
            self._execute_next_step()
        elif (self.arrow_data or self.arrow_svg) and self.arrow_delay and not self.show_arrow:
            # Simple single arrow animation
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(self.trigger_arrow_display)
            self.active_timers.append(timer)
            timer.start(self.arrow_delay)

    def reset_animation_state(self):
        """Reset all animation states to initial values"""
        # Stop all active timers first
        for timer in getattr(self, 'active_timers', []):
            if timer and timer.isActive():
                timer.stop()
        self.active_timers = []
        
        # Reset all visibility flags
        self.show_arrow = False
        self.show_overlay = False
        self.show_final_arrow = False
        self.show_advanced_arrow = False
        
        # Reset all opacity values
        self.arrow_opacity = 0.0
        self.overlay_opacity = 0.0
        self.final_arrow_opacity = 0.0
        self.advanced_arrow_opacity = 0.0
        
        # Reset step counter
        self.current_step = 0
        
        # Clear current images (they'll be reloaded as needed)
        self.current_arrow_image = None
        self.overlay_image = None
        self.final_arrow_image = None
        self.advanced_arrow_image = None
        
        # Stop any running animations
        if hasattr(self, 'arrow_fade_animation'):
            self.arrow_fade_animation.stop()
        
        # Force a repaint to clear any visible elements
        self.update()

    def stop_animations(self):
        """Stop all running animations and timers"""
        # Stop the main animation
        if hasattr(self, 'arrow_fade_animation'):
            self.arrow_fade_animation.stop()
        
        # Reset state
        self.reset_animation_state()

    def _execute_next_step(self):
        """Execute the next step in the multi-step sequence"""
        if self.current_step >= len(self.multi_step_sequence):
            return
            
        step_data = self.multi_step_sequence[self.current_step]
        delay = step_data.get('delay', 1000)
        action = step_data.get('action', 'show_arrow')
        
        # Create timer and track it
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._perform_step_action(step_data))
        self.active_timers.append(timer)
        timer.start(delay)

    def _perform_step_action(self, step_data):
        """Perform the action for a specific step"""
        
        action = step_data.get('action', 'show_arrow')
        
        if action == 'show_arrow':
            # Load and show the arrow
            arrow_image_path = step_data.get('arrow_image')
            if arrow_image_path:
                resolved_path = get_resource_path(arrow_image_path)
                if os.path.exists(resolved_path):
                    self.current_arrow_image = QPixmap(resolved_path)
                    self.show_arrow = True
                    self._fade_in_arrow()
                
        elif action == 'fade_arrow_show_overlay':
            # Fade out arrow and fade in overlay
            self._fade_out_arrow()
            overlay_image_path = step_data.get('overlay_image')
            if overlay_image_path:
                resolved_path = get_resource_path(overlay_image_path)
                if os.path.exists(resolved_path):
                    self.overlay_image = QPixmap(resolved_path)
                    # Create timer and track it
                    timer = QTimer()
                    timer.setSingleShot(True)
                    timer.timeout.connect(self._fade_in_overlay)
                    self.active_timers.append(timer)
                    timer.start(300)  # Start overlay fade after arrow fade starts
                
        elif action == 'show_final_arrow':
            # Show final arrow on top of overlay
            arrow_image_path = step_data.get('arrow_image')
            if arrow_image_path:
                resolved_path = get_resource_path(arrow_image_path)
                if os.path.exists(resolved_path):
                    self.final_arrow_image = QPixmap(resolved_path)
                    self.show_final_arrow = True
                    self._fade_in_final_arrow()
                
        elif action == 'show_advanced_arrow':
            # Show advanced arrow on top of everything
            arrow_image_path = step_data.get('arrow_image')
            if arrow_image_path:
                resolved_path = get_resource_path(arrow_image_path)
                if os.path.exists(resolved_path):
                    self.advanced_arrow_image = QPixmap(resolved_path)
                    self.show_advanced_arrow = True
                    self._fade_in_advanced_arrow()
        
        # Emit step change signal
        self.step_changed.emit(self.current_step)
        
        self.current_step += 1
        # Schedule next step if there are more
        if self.current_step < len(self.multi_step_sequence):
            next_step = self.multi_step_sequence[self.current_step]
            next_delay = next_step.get('delay', 2000)
            
            # Create timer and track it
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self._perform_step_action(next_step))
            self.active_timers.append(timer)
            timer.start(next_delay)

    def _fade_in_arrow(self):
        """Fade in the current arrow"""
        self.arrow_fade_animation.setStartValue(0.0)
        self.arrow_fade_animation.setEndValue(1.0)
        self.arrow_fade_animation.valueChanged.connect(self._update_arrow_opacity)
        self.arrow_fade_animation.start()

    def _fade_out_arrow(self):
        """Fade out the current arrow"""
        self.arrow_fade_animation.setStartValue(self.arrow_opacity)
        self.arrow_fade_animation.setEndValue(0.0)
        self.arrow_fade_animation.valueChanged.connect(self._update_arrow_opacity)
        self.arrow_fade_animation.finished.connect(lambda: setattr(self, 'show_arrow', False))
        self.arrow_fade_animation.start()

    def _fade_in_overlay(self):
        """Fade in the overlay image"""
        self.show_overlay = True
        # Create a simple opacity animation for overlay
        self.overlay_opacity = 0.0
        self._animate_overlay_opacity(0.0, 1.0)

    def _fade_in_final_arrow(self):
        """Fade in the final arrow"""
        self.final_arrow_opacity = 0.0
        self._animate_final_arrow_opacity(0.0, 1.0)

    def _fade_in_advanced_arrow(self):
        """Fade in the advanced arrow"""
        self.advanced_arrow_opacity = 0.0
        self._animate_advanced_arrow_opacity(0.0, 1.0)

    def _animate_overlay_opacity(self, start_val, end_val):
        """Animate overlay opacity"""
        self.overlay_opacity = start_val
        # Simple timer-based animation
        steps = 20
        step_size = (end_val - start_val) / steps
        step_duration = 25  # 500ms total / 20 steps
        
        def animate_step(current_step):
            if current_step <= steps:
                self.overlay_opacity = start_val + (step_size * current_step)
                self.update()
                QTimer.singleShot(step_duration, lambda: animate_step(current_step + 1))
        
        animate_step(0)

    def _animate_final_arrow_opacity(self, start_val, end_val):
        """Animate final arrow opacity"""
        self.final_arrow_opacity = start_val
        # Simple timer-based animation
        steps = 20
        step_size = (end_val - start_val) / steps
        step_duration = 25  # 500ms total / 20 steps
        
        def animate_step(current_step):
            if current_step <= steps:
                self.final_arrow_opacity = start_val + (step_size * current_step)
                self.update()
                QTimer.singleShot(step_duration, lambda: animate_step(current_step + 1))
        
        animate_step(0)

    def _animate_advanced_arrow_opacity(self, start_val, end_val):
        """Animate advanced arrow opacity"""
        self.advanced_arrow_opacity = start_val
        # Simple timer-based animation
        steps = 20
        step_size = (end_val - start_val) / steps
        step_duration = 25  # 500ms total / 20 steps
        
        def animate_step(current_step):
            if current_step <= steps:
                self.advanced_arrow_opacity = start_val + (step_size * current_step)
                self.update()
                QTimer.singleShot(step_duration, lambda: animate_step(current_step + 1))
        
        animate_step(0)

    def trigger_arrow_display(self):
        """Legacy method for simple arrow display"""
        self.show_arrow = True
        self._fade_in_arrow()

    def _update_arrow_opacity(self, value):
        self.arrow_opacity = value
        self.update()  # Trigger repaint

    def set_pixmap(self, pixmap):
        self.original_pixmap = pixmap
        self.update() # Trigger a repaint

    def set_arrow(self, arrow_data):
        self.arrow_data = arrow_data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.original_pixmap.isNull():
            return

        # Get the original pixmap
        pixmap_to_draw = self.original_pixmap
        if self.crop_rect:
            pixmap_to_draw = self.original_pixmap.copy(self.crop_rect)

        # Scale image to fit the widget size while maintaining aspect ratio
        widget_width = self.width()
        widget_height = self.height()
        final_pixmap = pixmap_to_draw.scaled(widget_width, widget_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        # Draw at exact pixel size accounting for device pixel ratio
        draw_rect = QRect(0, 0, self.width(), self.height())
        painter.drawPixmap(draw_rect, final_pixmap, final_pixmap.rect())

        # Draw overlays and arrows with EXACT same positioning and scaling as background
        
        # Draw the main arrow (from multi-step or simple arrow)
        arrow_image_to_use = self.current_arrow_image if self.current_arrow_image else self.arrow_svg
        if self.show_arrow and arrow_image_to_use and not arrow_image_to_use.isNull():
            # Scale arrow using EXACT same parameters as the background image
            arrow_to_draw = arrow_image_to_use
            if self.crop_rect:
                arrow_to_draw = arrow_image_to_use.copy(self.crop_rect)
            
            # Scale arrow with EXACT same scaling as background image
            scaled_arrow = arrow_to_draw.scaled(widget_width, widget_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            if self.arrow_opacity < 1.0:
                painter.setOpacity(self.arrow_opacity)
            
            # Draw arrow at EXACT same position as background (using same draw_rect)
            painter.drawPixmap(draw_rect, scaled_arrow, scaled_arrow.rect())
            
            if self.arrow_opacity < 1.0:
                painter.setOpacity(1.0)
        
        # Draw the overlay image (menu, etc.)
        if self.show_overlay and self.overlay_image and not self.overlay_image.isNull():
            overlay_to_draw = self.overlay_image
            if self.crop_rect:
                overlay_to_draw = self.overlay_image.copy(self.crop_rect)
            
            scaled_overlay = overlay_to_draw.scaled(widget_width, widget_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            if self.overlay_opacity < 1.0:
                painter.setOpacity(self.overlay_opacity)
            
            painter.drawPixmap(draw_rect, scaled_overlay, scaled_overlay.rect())
            
            if self.overlay_opacity < 1.0:
                painter.setOpacity(1.0)
        
        # Draw the final arrow (on top of overlay)
        if self.show_final_arrow and self.final_arrow_image and not self.final_arrow_image.isNull():
            final_arrow_to_draw = self.final_arrow_image
            if self.crop_rect:
                final_arrow_to_draw = self.final_arrow_image.copy(self.crop_rect)
            
            scaled_final_arrow = final_arrow_to_draw.scaled(widget_width, widget_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            if self.final_arrow_opacity < 1.0:
                painter.setOpacity(self.final_arrow_opacity)
            
            painter.drawPixmap(draw_rect, scaled_final_arrow, scaled_final_arrow.rect())
            
            if self.final_arrow_opacity < 1.0:
                painter.setOpacity(1.0)
        
        # Draw the advanced arrow (on top of everything)
        if self.show_advanced_arrow and self.advanced_arrow_image and not self.advanced_arrow_image.isNull():
            advanced_arrow_to_draw = self.advanced_arrow_image
            if self.crop_rect:
                advanced_arrow_to_draw = self.advanced_arrow_image.copy(self.crop_rect)
            
            scaled_advanced_arrow = advanced_arrow_to_draw.scaled(widget_width, widget_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            if self.advanced_arrow_opacity < 1.0:
                painter.setOpacity(self.advanced_arrow_opacity)
            
            painter.drawPixmap(draw_rect, scaled_advanced_arrow, scaled_advanced_arrow.rect())
            
            if self.advanced_arrow_opacity < 1.0:
                painter.setOpacity(1.0)
        # Fallback to drawing a path if SVG is not available
        elif self.show_arrow and self.arrow_data:
            start_x = (self.width() - pixmap_to_draw.width()) // 2 + self.arrow_data['start'][0] * pixmap_to_draw.width()
            start_y = (self.height() - pixmap_to_draw.height()) // 2 + self.arrow_data['start'][1] * pixmap_to_draw.height()
            end_x = (self.width() - pixmap_to_draw.width()) // 2 + self.arrow_data['end'][0] * pixmap_to_draw.width()
            end_y = (self.height() - pixmap_to_draw.height()) // 2 + self.arrow_data['end'][1] * pixmap_to_draw.height()
            
            pen = QPen(QColor("#D94141"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)

            path = QPainterPath()
            path.moveTo(start_x, start_y)

            # Control points for the curve
            ctrl_x = (start_x + end_x) / 2 + 50
            ctrl_y = (start_y + end_y) / 2 - 50
            path.quadTo(ctrl_x, ctrl_y, end_x, end_y)

            painter.drawPath(path)

            # Draw arrowhead
            angle = math.atan2(ctrl_y - end_y, ctrl_x - end_x)
            arrow_size = 20
            
            arrow_p1 = QPointF(end_x, end_y) + QPointF(math.cos(angle + 0.5) * arrow_size, math.sin(angle + 0.5) * arrow_size)
            arrow_p2 = QPointF(end_x, end_y) + QPointF(math.cos(angle - 0.5) * arrow_size, math.sin(angle - 0.5) * arrow_size)

            arrow_head = QPolygonF([QPointF(end_x, end_y), arrow_p1, arrow_p2])
            
            painter.setBrush(QColor("#D94141"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(arrow_head)


class SlideshowSlide(QWidget):
    """A single slide in the tutorial slideshow"""
    
    # Signal for when user clicks on a sub-navigation dot
    sub_nav_requested = pyqtSignal(int)  # step_index
    
    def __init__(self, title, content, slide_index=0, image_path=None, animation_data=None, arrow_data=None, crop_rect=None, arrow_delay=None, arrow_image_path=None, multi_step_sequence=None):
        super().__init__()
        self.title = title
        self.content = content
        self.slide_index = slide_index
        self.image_path = image_path
        self.animation_data = animation_data
        self.arrow_data = arrow_data
        self.crop_rect = crop_rect
        self.arrow_delay = arrow_delay
        self.arrow_image_path = arrow_image_path
        self.multi_step_sequence = multi_step_sequence
        self.current_sub_step = 0
        try:
            self.illustrations = TutorialIllustrations(APP_COLORS) if TutorialIllustrations else None
        except Exception as e:
            print(f"Warning: Could not initialize TutorialIllustrations: {e}")
            self.illustrations = None
        
        # Setup the UI
        self._setup_ui()

    def _setup_ui(self):
        """Setup the slide UI with a two-panel layout"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 40, 20, 40)  # Reduced left/right margins to prevent cutoff
        main_layout.setSpacing(0)  # Minimal spacing between text and image panels

        # --- Left Panel (Text) ---
        text_panel = QFrame()
        text_layout = QVBoxLayout(text_panel)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(20)
        
        # Title with dynamic font size optimized for container and content
        self.title_label = QLabel(self.title)
        title_font_size = get_slideshow_title_font_size(self.title, 430)
        self.title_label.setFont(QFont(get_system_font(), title_font_size, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #FFFFFF; margin-bottom: 10px;")
        self.title_label.setWordWrap(True)
        text_layout.addWidget(self.title_label)
        
        # Description with dynamic font size optimized for container and content
        self.description_label = QLabel(self.content)
        desc_font_size = get_slideshow_description_font_size(self.content, 430)
        self.description_label.setFont(QFont(get_system_font(), desc_font_size))
        self.description_label.setStyleSheet(f"color: {get_color('text')}; line-height: 1.3;")
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        text_layout.addWidget(self.description_label)
        
        text_layout.addStretch()
        
        # Keep original text panel width
        text_panel.setFixedWidth(430)
        
        # --- Right Panel (Image + Sub-navigation) ---
        image_panel = QFrame()
        image_panel_layout = QVBoxLayout(image_panel)
        image_panel_layout.setContentsMargins(0, 0, 0, 0)
        image_panel_layout.setSpacing(10)  # Space between image and dots
        
        # Image display widget - make it responsive
        self.image_display_widget = ImageWithArrow(
            pixmap=None,  # Will be loaded from image_path
            arrow_data=self.arrow_data, 
            crop_rect=self.crop_rect, 
            arrow_delay=self.arrow_delay, 
            arrow_image_path=self.arrow_image_path,
            multi_step_sequence=getattr(self, 'multi_step_sequence', None)
        )
        
        # Load the image after creating the widget
        if self.image_path:
            # Use centralized resource path resolution
            resolved_image_path = get_resource_path(self.image_path)
            if os.path.exists(resolved_image_path):
                pixmap = QPixmap(resolved_image_path)
                if not pixmap.isNull():
                    self.image_display_widget.set_pixmap(pixmap)
        
        # Keep original image size for proper slideshow display
        self.image_display_widget.setFixedSize(730, 500)
        image_panel_layout.addWidget(self.image_display_widget, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Sub-navigation container (under the image)
        self.sub_nav_container = QWidget()
        self.sub_nav_container.setFixedHeight(25)  # Compact height for dots
        image_panel_layout.addWidget(self.sub_nav_container, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Add stretch to push everything up
        image_panel_layout.addStretch()
        
        # Keep original image panel width
        image_panel.setFixedWidth(770)
        
        # Add panels to main layout
        main_layout.addWidget(text_panel)
        main_layout.addWidget(image_panel)
        
        # Create and populate sub-navigation if needed
        if hasattr(self, 'image_display_widget') and self.image_display_widget.get_total_steps() > 1:
            self._create_and_populate_sub_nav()

    def _create_and_populate_sub_nav(self):
        """Create and populate the sub-navigation container"""
        # Clear existing sub-navigation
        if hasattr(self, 'sub_nav_container'):
            # Clear the container properly
            layout = self.sub_nav_container.layout()
            if layout:
                # Clear existing widgets
                while layout.count():
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                # Delete the layout
                layout.deleteLater()
            
            # Get current slide
            current_slide_widget = self
            
            # Check if current slide has multi-step navigation
            if (hasattr(current_slide_widget, 'image_display_widget') and 
                current_slide_widget.image_display_widget.get_total_steps() > 1):
                
                # Create sub-navigation for this slide
                sub_nav_widget = current_slide_widget._create_sub_navigation()
                if sub_nav_widget:
                    # Create new layout for the container
                    container_layout = QHBoxLayout(self.sub_nav_container)
                    container_layout.setContentsMargins(0, 0, 0, 0)
                    container_layout.addWidget(sub_nav_widget)
                    
                    # Connect step changes to update the sub-nav
                    current_slide_widget.image_display_widget.step_changed.connect(
                        current_slide_widget._update_sub_nav_state
                    )
                    
                    # Make container visible and store reference
                    self.sub_nav_container.setVisible(True)
                    self.current_sub_nav = sub_nav_widget
                    self.current_slide_widget = current_slide_widget
                else:
                    # No sub-navigation needed - hide the container
                    self.sub_nav_container.setVisible(False)
            else:
                # No sub-navigation needed - hide the container
                self.sub_nav_container.setVisible(False)

    def _create_sub_navigation(self):
        """Create a proper two-layer image-based sub-navigation for footer"""
        if not hasattr(self, 'image_display_widget'):
            return None
            
        total_steps = self.image_display_widget.get_total_steps()
        if total_steps <= 1:
            return None
        
        # Container for sub-navigation - optimized for footer
        sub_nav_container = QWidget()
        sub_nav_container.setFixedHeight(30)  # Match footer container height
        sub_nav_layout = QHBoxLayout(sub_nav_container)
        sub_nav_layout.setContentsMargins(0, 5, 0, 5)  # Small vertical margins
        sub_nav_layout.setSpacing(4)  # Tight spacing between dots
        
        # Center the dots
        sub_nav_layout.addStretch()
        
        # Create proper two-layer image-based dots
        self.sub_nav_dots = []
        for i in range(total_steps):
            dot_container = self._create_dot(i)
            self.sub_nav_dots.append(dot_container)
            sub_nav_layout.addWidget(dot_container)
        
        sub_nav_layout.addStretch()
        
        # Update initial state
        self._update_sub_nav_state(0)
        
        return sub_nav_container

    def _create_dot(self, step_index):
        """Create a proper two-layer navigation dot using outline + fill images"""
        # Create a container widget for the two-layer dot
        dot_container = QWidget()
        dot_container.setProperty("step_index", step_index)
        dot_container.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Load the dot images using centralized resource path resolution
        
        empty_dot_path = get_resource_path(os.path.join("slides", "DOT EMPTY.png"))
        filled_dot_path = get_resource_path(os.path.join("slides", "DOT FILL.png"))
        
        # Set fixed size for the container - half the original image size
        target_size = 15  # Half of 29px
        dot_container.setFixedSize(target_size, target_size)
        
        # Create the outline (always visible) - positioned absolutely
        outline_label = QLabel(dot_container)
        outline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outline_label.setFixedSize(target_size, target_size)
        outline_label.move(0, 0)
        
        # Create the fill (layered on top) - positioned absolutely
        fill_label = QLabel(dot_container)
        fill_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fill_label.setFixedSize(target_size, target_size)
        fill_label.move(0, 0)
        
        # Load and scale images
        if os.path.exists(empty_dot_path):
            outline_pixmap = QPixmap(empty_dot_path)
            scaled_outline = outline_pixmap.scaled(target_size, target_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            outline_label.setPixmap(scaled_outline)
        else:
            outline_label.setText("○")
            outline_label.setStyleSheet(f"color: #666666; font-size: {get_platform_css_font_size(10, 0.9)};")
        
        if os.path.exists(filled_dot_path):
            fill_pixmap = QPixmap(filled_dot_path)
            scaled_fill = fill_pixmap.scaled(target_size, target_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            fill_label.setPixmap(scaled_fill)
        else:
            fill_label.setText("●")
            fill_label.setStyleSheet(f"color: #FFFFFF; font-size: {get_platform_css_font_size(10, 0.9)};")
        
        # Ensure fill is on top by raising it
        fill_label.raise_()
        
        # Store references for easy access
        dot_container.outline_label = outline_label
        dot_container.fill_label = fill_label
        dot_container.empty_image_path = empty_dot_path
        dot_container.filled_image_path = filled_dot_path
        
        # Handle mouse clicks
        def on_dot_clicked(event):
            self._on_dot_clicked(step_index)
        
        dot_container.mousePressEvent = on_dot_clicked
        
        return dot_container

    def _update_sub_nav_state(self, current_step):
        """Update the visual state using proper two-layer dot images"""
        if not hasattr(self, 'sub_nav_dots') or not self.sub_nav_dots:
            return
        
        self.current_sub_step = current_step
        
        for i, dot_container in enumerate(self.sub_nav_dots):
            is_active = i == current_step
            is_completed = i < current_step
            
            # The outline is always visible (no changes needed)
            
            # Control the fill layer visibility and opacity
            fill_label = dot_container.fill_label
            
            if is_active:
                # Active step - show fill at full opacity
                fill_label.setVisible(True)
                effect = QGraphicsOpacityEffect()
                effect.setOpacity(1.0)
                fill_label.setGraphicsEffect(effect)
            elif is_completed:
                # Completed step - show fill at reduced opacity
                fill_label.setVisible(True)
                effect = QGraphicsOpacityEffect()
                effect.setOpacity(0.6)
                fill_label.setGraphicsEffect(effect)
            else:
                # Future step - hide fill (only outline visible)
                fill_label.setVisible(False)

    def _on_step_changed(self, step_index):
        """Handle step changes from the image widget"""
        self._update_sub_nav_state(step_index)

    def _on_dot_clicked(self, step_index):
        """Handle dot clicks for sub-navigation"""
        if hasattr(self, 'image_display_widget'):
            self.image_display_widget.jump_to_step(step_index)
        
        # Emit signal for external handlers
        self.sub_nav_requested.emit(step_index)

    def get_current_sub_step(self):
        """Get the current sub-step index"""
        return self.current_sub_step

    def get_total_sub_steps(self):
        """Get the total number of sub-steps"""
        if hasattr(self, 'image_display_widget'):
            return self.image_display_widget.get_total_steps()
        return 0


class TutorialSlideshow(QDialog):
    """Modern, animated tutorial slideshow"""
    
    # Signals
    completed = pyqtSignal()
    skipped = pyqtSignal()
    slide_changed = pyqtSignal(int)  # slide_index
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_slide = 0
        self.auto_advance_timer = QTimer()
        self.auto_advance_timer.timeout.connect(self.next_slide)
        self._setup_slides()
        self._setup_ui()
        self._setup_animations()
    
    def _setup_slides(self):
        """Setup slides from configuration data"""
        from .config import CUSTOM_SLIDESHOW_CONTENT
        self.slides_data = CUSTOM_SLIDESHOW_CONTENT
        self.slides = []
        
        # Create slide widgets
        for i, slide_data in enumerate(self.slides_data):
            slide = SlideshowSlide(
                title=slide_data['title'],
                content=slide_data['content'],
                slide_index=i,
                image_path=slide_data.get('image_path'),
                animation_data=slide_data.get('animation_data'),
                arrow_data=slide_data.get('arrow_data'),
                crop_rect=slide_data.get('crop_rect'),
                arrow_delay=slide_data.get('arrow_delay'),
                arrow_image_path=slide_data.get('arrow_image_path'),
                multi_step_sequence=slide_data.get('multi_step_sequence')
            )
            
            # Connect sub-navigation signals
            slide.sub_nav_requested.connect(self._on_sub_nav_requested)
            
            self.slides.append(slide)

    def _on_sub_nav_requested(self, step_index):
        """Handle sub-navigation requests from slides"""
        # This signal comes from individual slides when user clicks on sub-nav dots
        # The slide handles the animation jump internally, we just need to acknowledge
        pass

    def _setup_ui(self):
        """Setup the main slideshow UI"""
        self.setWindowTitle("Welcome to ForwardFlow - Quick Start Guide")
        
        # Keep original fixed size for slideshow images to display properly
        self.setFixedSize(1280, 760)
        
        self.setModal(True)
        
        # Center the dialog
        if self.parent():
            parent_rect = self.parent().geometry()
            self.move(
                parent_rect.center().x() - self.width() // 2,
                parent_rect.center().y() - self.height() // 2
            )
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Slide stack
        self.slide_stack = QStackedWidget()
        self.slide_stack.setStyleSheet(f"background-color: {get_color('bg')};")
        
        # Add slides to stack
        for slide in self.slides:
            self.slide_stack.addWidget(slide)
        
        main_layout.addWidget(self.slide_stack)
        
        # Footer
        footer = self._create_footer()
        main_layout.addWidget(footer)
        
        # Apply theme
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {get_color('bg')};
                border: 1px solid {get_color('border')};
                border-radius: 16px;
            }}
        """)
        
        # Setup animations
        self._setup_animations()
        
        # Set initial slide
        self.slide_stack.setCurrentIndex(0)
        self.progress_bar.setValue(1)

    def _create_header(self):
        """Create the header with progress bar"""
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {get_color('card_bg')};
                border-bottom: 1px solid {get_color('border')};
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                padding: 0 20px;
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(len(self.slides_data))
        self.progress_bar.setValue(1)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {get_color('bg')};
                border: 1px solid {get_color('border')};
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {get_color('accent')};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        return header

    def _create_footer(self):
        """Create the footer with navigation buttons"""
        footer = QFrame()
        footer.setFixedHeight(80)  # Reduced since no sub-nav
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {get_color('card_bg')};
                border-top: 1px solid {get_color('border')};
                border-bottom-left-radius: 16px;
                border-bottom-right-radius: 16px;
            }}
        """)
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(30, 15, 30, 15)
        
        # Skip button (left)
        self.skip_button = QPushButton("Skip Tutorial")
        self.skip_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.skip_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {get_color('secondary_text')};
                border: none;
                padding: 8px 16px;
                font-size: {get_platform_css_font_size(14, 1.0)};
            }}
            QPushButton:hover {{
                color: {get_color('text')};
            }}
        """)
        layout.addWidget(self.skip_button, 0, Qt.AlignmentFlag.AlignLeft)
        
        layout.addStretch()
        
        # Navigation buttons (center)
        nav_widget = QWidget()
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.setSpacing(10)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        
        self.prev_button = QPushButton("Previous")
        self.prev_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_button.setStyleSheet(BUTTON_STYLE)
        self.prev_button.setFixedWidth(120)
        
        # Add opacity effect for disabling
        self.prev_button_opacity = QGraphicsOpacityEffect(self.prev_button)
        self.prev_button.setGraphicsEffect(self.prev_button_opacity)
        
        self.next_button = QPushButton("Next")
        self.next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.next_button.setFixedWidth(120)
        
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        
        layout.addWidget(nav_widget, 0, Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()

        # Connect navigation buttons
        self.skip_button.clicked.connect(self._skip_tutorial)
        self.prev_button.clicked.connect(self.previous_slide)
        self.next_button.clicked.connect(self.next_slide)
        
        # Update button states
        self._update_button_states()
        
        return footer
    
    def _update_button_states(self):
        """Update navigation button states based on current slide"""
        is_first_slide = self.current_slide == 0
        is_last_slide = self.current_slide == len(self.slides_data) - 1
        
        self.prev_button.setEnabled(not is_first_slide)
        self.prev_button_opacity.setOpacity(1.0 if not is_first_slide else 0.5)

        if is_last_slide:
            self.next_button.setText("Get Started")
            # Disconnect all previous connections and connect to complete
            try: 
                self.next_button.clicked.disconnect() 
            except TypeError: 
                pass
            self.next_button.clicked.connect(self._complete_tutorial)
        else:
            self.next_button.setText("Next")
            # Disconnect all previous connections and connect to next_slide
            try: 
                self.next_button.clicked.disconnect()
            except TypeError: 
                pass
            self.next_button.clicked.connect(self.next_slide)
            
    def next_slide(self):
        """Advance to the next slide"""
        if self.current_slide < len(self.slides_data) - 1:
            self.current_slide += 1
            self._update_slide()

    def previous_slide(self):
        """Go back to the previous slide"""
        if self.current_slide > 0:
            self.current_slide -= 1
            self._update_slide()
    
    def _update_slide(self):
        """Update the current slide and UI elements"""
        # Animate transition
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self._switch_slide_content)
        self.fade_animation.start()
    
    def _switch_slide_content(self):
        """The actual logic to switch content after fade out"""
        self.fade_animation.finished.disconnect(self._switch_slide_content)
        
        # Stop animations on ALL slides first to prevent interference
        for slide_widget in self.slides:
            if hasattr(slide_widget, 'image_display_widget'):
                slide_widget.image_display_widget.stop_animations()
        
        self.slide_stack.setCurrentIndex(self.current_slide)
        self.progress_bar.setValue(self.current_slide + 1)
        self.slide_changed.emit(self.current_slide)
        self._update_button_states()
        
        # Start arrow animation for the current slide if it has one
        current_slide_widget = self.slides[self.current_slide]
        if hasattr(current_slide_widget, 'image_display_widget'):
            current_slide_widget.image_display_widget.start_arrow_animation()
        
        # Fade back in
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()

    def _skip_tutorial(self):
        self.skipped.emit()
        self.accept()

    def _complete_tutorial(self):
        self.completed.emit()
        self.accept()

    def start_auto_advance(self, interval_ms=4000):
        self.auto_advance_timer.start(interval_ms)

    def stop_auto_advance(self):
        self.auto_advance_timer.stop()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Right:
            self.next_slide()
        elif event.key() == Qt.Key.Key_Left:
            self.previous_slide()
        elif event.key() == Qt.Key.Key_Escape:
            self._skip_tutorial()
        else:
            super().keyPressEvent(event)
    
    def _setup_animations(self):
        """Setup entrance and exit animations"""
        self.opacity_effect = QGraphicsOpacityEffect(self.slide_stack)
        self.slide_stack.setGraphicsEffect(self.opacity_effect)
        
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(200) # Faster transition
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def showEvent(self, event):
        """Override showEvent to trigger entrance animation"""
        self.opacity_effect.setOpacity(0.0)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        
        super().showEvent(event) 