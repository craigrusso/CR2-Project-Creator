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
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtSvg import QSvgRenderer
from app.ui.color_scheme_pyqt import get_color, colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, APP_COLORS
from app.templates.components.utils import get_system_font
from .tutorial_illustrations import TutorialIllustrations
from .config import CUSTOM_SLIDESHOW_CONTENT, TUTORIAL_CONTENT # Import configuration
import os
import math


class ImageWithArrow(QWidget):
    """A widget to display a pixmap and an optional arrow overlay."""
    def __init__(self, pixmap=None, arrow_data=None, crop_rect=None, arrow_delay=None, arrow_image_path=None, parent=None):
        super().__init__(parent)
        self.original_pixmap = pixmap if pixmap else QPixmap()
        self.arrow_data = arrow_data
        self.crop_rect = crop_rect
        self.arrow_svg = None
        self.arrow_delay = arrow_delay  # Always set this
        # Set size policy to expand and fill the available space
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.show_arrow = False
        self.arrow_opacity = 0.0  # Start with arrow invisible
        
        # Setup fade-in animation for arrow
        self.arrow_opacity_effect = QGraphicsOpacityEffect()
        self.arrow_fade_animation = QPropertyAnimation(self.arrow_opacity_effect, b"opacity")
        self.arrow_fade_animation.setDuration(500)  # 500ms fade-in
        self.arrow_fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Load the arrow image (PNG or SVG)
        if arrow_image_path and os.path.exists(arrow_image_path):
            self.arrow_svg = QPixmap(arrow_image_path)
        else:
            # Fallback to default curved arrow
            arrow_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sample_svgs", "curved arrow_CR.svg")
            if os.path.exists(arrow_path):
                self.arrow_svg = QPixmap(arrow_path)
        
        if self.arrow_data or arrow_image_path:  # Show arrow if we have either positioning data OR an arrow image
            # Don't start the timer immediately - wait for slide to be shown
            if not arrow_delay:
                self.show_arrow = True
                self.arrow_opacity = 1.0

    def start_arrow_animation(self):
        """Start the arrow animation timer when the slide becomes visible"""
        if (self.arrow_data or self.arrow_svg) and self.arrow_delay and not self.show_arrow:
            QTimer.singleShot(self.arrow_delay, self.trigger_arrow_display)

    def trigger_arrow_display(self):
        self.show_arrow = True
        # Start fade-in animation
        self.arrow_fade_animation.setStartValue(0.0)
        self.arrow_fade_animation.setEndValue(1.0)
        self.arrow_fade_animation.valueChanged.connect(self._update_arrow_opacity)
        self.arrow_fade_animation.start()

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

        # Draw the arrow overlay scaled to fit
        if self.show_arrow and self.arrow_svg and not self.arrow_svg.isNull():
            # Scale arrow to match the background image scaling
            scaled_arrow = self.arrow_svg.scaled(widget_width, widget_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            # Set device pixel ratio for arrow too
            scaled_arrow.setDevicePixelRatio(self.devicePixelRatioF())
            
            arrow_x = (self.width() - scaled_arrow.width()) // 2
            arrow_y = (self.height() - scaled_arrow.height()) // 2
            
            if self.arrow_opacity < 1.0:
                painter.setOpacity(self.arrow_opacity)
            
            painter.drawPixmap(int(arrow_x), int(arrow_y), scaled_arrow)
            
            if self.arrow_opacity < 1.0:
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
    """Individual slide in the tutorial slideshow"""
    
    def __init__(self, title, content, slide_index=0, image_path=None, animation_data=None, arrow_data=None, crop_rect=None, arrow_delay=None, arrow_image_path=None):
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
        self.illustrations = TutorialIllustrations(APP_COLORS)
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

        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont(get_system_font(), 28, QFont.Weight.Bold))
        self.title_label.setStyleSheet(f"color: {get_color('text')};")
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Description
        self.description_label = QLabel(self.content)
        self.description_label.setFont(QFont(get_system_font(), 16))
        self.description_label.setStyleSheet(f"color: {get_color('secondary_text')}; line-height: 1.5;")
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.description_label)
        text_layout.addStretch()

        # --- Right Panel (Image) ---
        image_panel = QFrame()
        image_panel.setMinimumWidth(770)  # Set minimum width only
        image_panel.setMaximumWidth(770)  # Set maximum width only - let height be flexible
        # Use app color scheme for consistent styling
        image_panel.setStyleSheet(f"background-color: {get_color('card_bg')};")
        image_layout = QVBoxLayout(image_panel)
        image_layout.setContentsMargins(0, 0, 0, 0)  # Remove all padding to let image fill container

        pixmap = QPixmap()
        screenshot_filename = self.image_path
        
        # First check if we have a direct image_path (for PNG/JPG images or SVGs)
        if screenshot_filename and os.path.exists(screenshot_filename):
            # Load as regular image (PNG, JPG, or SVG)
            pixmap.load(screenshot_filename)
            if not pixmap.isNull():
                self.image_display_widget = ImageWithArrow(pixmap, self.arrow_data, self.crop_rect, self.arrow_delay, self.arrow_image_path)
                # Make the image widget expand to fill the entire layout
                image_layout.addWidget(self.image_display_widget, 1)  # stretch factor of 1
            else:
                print(f"Error loading image {screenshot_filename}")
                # Fallback to generated SVG
                self.svg_widget = QSvgWidget()
                try:
                    svg_content = self.illustrations.get_illustration_for_slide(self.slide_index)
                    if svg_content:
                        self.svg_widget.load(QByteArray(svg_content.encode('utf-8')))
                    image_layout.addWidget(self.svg_widget)
                except Exception as e:
                    print(f"Error loading fallback SVG for slide {self.slide_index}: {e}")
        elif screenshot_filename:
            # Try the old path logic for backward compatibility
            screenshots_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sample_svgs", "app screen shots", screenshot_filename)
            if os.path.exists(screenshots_path):
                pixmap.load(screenshots_path)
                if not pixmap.isNull():
                    self.image_display_widget = ImageWithArrow(pixmap, self.arrow_data, self.crop_rect, self.arrow_delay, self.arrow_image_path)
                    # Removed height constraint to allow fuller use of available space
                    image_layout.addWidget(self.image_display_widget)
        
        # If no image was loaded above, use generated SVG
        if not hasattr(self, 'image_display_widget') and not hasattr(self, 'svg_widget'):
            self.svg_widget = QSvgWidget()
            try:
                svg_content = self.illustrations.get_illustration_for_slide(self.slide_index)
                if svg_content:
                    self.svg_widget.load(QByteArray(svg_content.encode('utf-8')))
                    print(f"DEBUG: Loaded generated SVG for slide {self.slide_index}")
            except Exception as e:
                print(f"Error loading generated SVG for slide {self.slide_index}: {e}")
            image_layout.addWidget(self.svg_widget)

        # Add panels to main layout with fixed proportions
        # Text panel: 800px, Image panel: 1600px (2:1 ratio for high DPI)
        # Set fixed width for text panel - reduced by another 20px
        text_panel.setMinimumWidth(430)
        text_panel.setMaximumWidth(430)
        
        # Add panels to main layout with no stretch factors (use fixed sizes)
        main_layout.addWidget(text_panel)  # Text panel: fixed 800px
        main_layout.addWidget(image_panel) # Image panel: fixed 1600px
        

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
        """Setup the tutorial slides using the central configuration."""
        app_name = TUTORIAL_CONTENT.get('app_name', 'Echelon')
        
        self.slides_data = []
        for slide_config in CUSTOM_SLIDESHOW_CONTENT:
            processed_slide = slide_config.copy()
            if 'title' in processed_slide and processed_slide['title']:
                processed_slide['title'] = processed_slide['title'].format(app_name=app_name)
            if 'content' in processed_slide and processed_slide['content']:
                processed_slide['content'] = processed_slide['content'].format(app_name=app_name)
            self.slides_data.append(processed_slide)
    
    def _setup_ui(self):
        """Setup the main slideshow UI"""
        self.setWindowTitle("Welcome to Echelon - Quick Start Guide")
        self.setFixedSize(1280, 760)  # Increased height to accommodate 580px image + margins
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
        
        # Create slides
        self.slides = []
        for index, slide_data in enumerate(self.slides_data):
            slide = SlideshowSlide(
                slide_data['title'],
                slide_data['content'],
                slide_index=index,
                image_path=slide_data.get('image_path'),
                animation_data=slide_data.get('animation_data'),
                arrow_data=slide_data.get('arrow_data'),
                crop_rect=slide_data.get('crop_rect'),
                arrow_delay=slide_data.get('arrow_delay'),
                arrow_image_path=slide_data.get('arrow_image_path')
            )
            self.slides.append(slide)
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
        footer.setFixedHeight(80)
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
                font-size: 14px;
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
        
        # Start arrow animation for the initial slide if it has one
        if self.slides and hasattr(self.slides[0], 'image_display_widget'):
            self.slides[0].image_display_widget.start_arrow_animation()
            
        super().showEvent(event) 