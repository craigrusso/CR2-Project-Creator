#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QComboBox, QFrame, QListView, QAbstractItemView, QStyledItemDelegate, QApplication, QProxyStyle, QStyle
from PyQt6.QtCore import Qt, QEvent, QObject, QRect, QSize
from PyQt6.QtGui import QPalette, QColor, QPainter, QBrush, QPen, QFont, QPixmap, QPainterPath
import sys, time
from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, COMBOBOX_STYLE, LINEEDIT_STYLE, LABEL_STYLE, LISTVIEW_POPUP_STYLE, MESSAGE_BOX_BUTTON_STYLE, DIALOG_BUTTON_STYLE
import platform

# Add the force_app_palette function
def force_app_palette(app):
    """Force the application to use our dark theme palette regardless of system settings"""
    dark_palette = QPalette()
    
    # Set up the dark palette
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(colors['bg']))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(colors['text']))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(colors['card_bg']))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors['bg']))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors['card_bg']))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors['text']))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(colors['text']))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(colors['card_bg']))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors['text']))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(colors['highlight_text']))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(colors['accent']))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(colors['highlight_bg']))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors['highlight_text']))
    
    # Add additional macOS specific palette settings
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(colors['secondary_text']))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(colors['secondary_text']))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(colors['secondary_text']))
    dark_palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Highlight, QColor(colors['highlight_bg']))
    dark_palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.HighlightedText, QColor(colors['highlight_text']))
    
    # Apply the palette
    app.setPalette(dark_palette)
    
    # Force the application to use this palette with more comprehensive styling
    app.setStyleSheet(f"""
        QToolTip {{ 
            color: {colors['text']}; 
            background-color: {colors['card_bg']}; 
            border: 1px solid {colors['border']}; 
        }}
        
        /* Force all basic widgets to use our palette colors */
        QWidget {{ 
            background-color: {colors['bg']};
            color: {colors['text']};
        }}
        
        /* Ensure dialog backgrounds are correct */
        QDialog, QMessageBox, QInputDialog {{ 
            background-color: {colors['bg']}; 
            color: {colors['text']}; 
        }}
        
        /* Force macOS menu bar and menu items to use dark theme */
        QMenuBar, QMenuBar::item {{ 
            background-color: {colors['card_bg']}; 
            color: {colors['text']}; 
        }}
        
        QMenu {{ 
            background-color: {colors['card_bg']}; 
            color: {colors['text']}; 
        }}
    """)

# Remove the problematic global patch and classes

class ComboBoxItemDelegate(QStyledItemDelegate):
    """Custom delegate for rendering combo box items with enhanced hover effects"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def paint(self, painter, option, index):
        """Custom painting for combo box items"""
        # Get the rect where we'll draw
        rect = option.rect
        
        # Determine if this item is selected or hovered
        is_selected = option.state & QStyle.State_Selected
        is_hovered = bool(option.state & QStyle.State_MouseOver)
        
        # Setup the painter
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Define colors based on state
        bg_color = QColor(colors['card_bg'])
        text_color = QColor(colors['text'])
        border_color = QColor(colors['card_bg'])  # Same as bg by default
        
        # Draw different backgrounds based on state
        if is_hovered:
            # Hover state takes precedence
            bg_color = QColor(colors['accent'])
            text_color = QColor("white")
            border_color = QColor("white")
            
            # Draw the background
            painter.fillRect(rect, bg_color)
            
            # Draw left border
            border_rect = QRect(rect.left(), rect.top(), 5, rect.height())
            painter.fillRect(border_rect, border_color)
            
        elif is_selected:
            # Selected state
            bg_color = QColor(colors['highlight_bg'])
            text_color = QColor(colors['highlight_text'])
            border_color = QColor(colors['accent'])
            
            # Draw the background
            painter.fillRect(rect, bg_color)
            
            # Draw left border
            border_rect = QRect(rect.left(), rect.top(), 3, rect.height())
            painter.fillRect(border_rect, border_color)
        else:
            # Normal state
            painter.fillRect(rect, bg_color)
        
        # Draw the text
        text = index.data(Qt.ItemDataRole.DisplayRole)
        painter.setPen(QPen(text_color))
        
        # Use bold font for hovered items
        if is_hovered:
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
        
        # Text padding - leave space for left border
        text_rect = rect.adjusted(5, 0, -5, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
        
        painter.restore()

class ComboBoxPopupFilter(QObject):
    """Global event filter specifically for combo box popups"""
    
    def eventFilter(self, obj, event):
        """Filter events to catch and style combo box popups"""
        if event.type() == QEvent.Show: # Log ALL Show events
            obj_name = obj.objectName() if hasattr(obj, 'objectName') else 'N/A'
            parent_obj_name = obj.parent().objectName() if obj.parent() and hasattr(obj.parent(), 'objectName') else 'N/A'
            print(f"DEBUG POPUP FILTER (BROAD): Show event for obj: {obj_name}, type: {type(obj)}, parent: {parent_obj_name}")

            # Original logic for QListView remains
            if isinstance(obj, QListView) or (hasattr(obj, 'objectName') and obj.objectName() == "QComboBoxListView"):
                print(f"DEBUG POPUP FILTER (TARGETED): QListView detected: {obj.objectName() if hasattr(obj, 'objectName') else 'N/A'}, Parent: {obj.parent().objectName() if obj.parent() and hasattr(obj.parent(), 'objectName') else 'N/A'}")
                obj.setStyleSheet(LISTVIEW_POPUP_STYLE)
                
                if hasattr(obj, 'viewport'):
                    obj.viewport().setMouseTracking(True)
                    print(f"DEBUG POPUP FILTER (TARGETED): Viewport mouseTracking for {obj.objectName()}: {obj.viewport().hasMouseTracking()}")
                obj.setMouseTracking(True)
                print(f"DEBUG POPUP FILTER (TARGETED): QListView mouseTracking for {obj.objectName()}: {obj.hasMouseTracking()}")
                
                obj.setSelectionMode(QAbstractItemView.SingleSelection)
                obj.setSelectionBehavior(QAbstractItemView.SelectRows)
                
                # Create and set our custom delegate for advanced control
                delegate = ComboBoxItemDelegate(obj)
                obj.setItemDelegate(delegate)
                
                # Force the viewport to update now
                obj.viewport().update()
        
        # Always pass the event to the standard handler
        return False

def configure_styles(app):
    """Configure the application styles"""
    # Set application stylesheet with comprehensive style rules
    app.setStyleSheet(f"""
        /* Base application styling */
        QMainWindow, QDialog, QWidget {{
            background-color: {colors['bg']};
            color: {colors['text']};
        }}
        
        /* Apply QLineEdit styling */
        {LINEEDIT_STYLE}
        
        /* Force macOS menu bar to use dark theme */
        QMenuBar {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border-bottom: 1px solid {colors['border']};
        }}
        
        /* Apply dialog button styling to ensure consistent appearance in all themes */
        {MESSAGE_BOX_BUTTON_STYLE}
        
        /* Apply styling to buttons in input dialogs and other standard dialogs */
        {DIALOG_BUTTON_STYLE}
        
        QMenuBar::item {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors['highlight_bg']};
            color: {colors['highlight_text']};
        }}
        
        QMenu {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
        }}
        
        QMenu::item {{
            padding: 5px 10px 5px 10px; /* Added padding: top/bottom 5px, right/left 10px */
            border: none; /* Ensure no default border */
        }}
        
        QMenu::item:selected {{  /* Adjusted for consistent padding */
            background-color: {colors['accent']};
            color: white;
            font-weight: bold;
            padding-left: 5px; /* Keep 5px padding inside the border */
            border-left: 5px solid {colors['accent']}; /* Keep the 5px border */
            /* Total left space = 5px padding + 5px border = 10px, matching QMenu::item */
        }}
        
        /* Style for disabled items (used as headers) in ComboBox dropdowns */
        QComboBox QAbstractItemView::item:disabled {{
            color: {colors['secondary_text']}; /* Muted grey color */
            background-color: {colors['card_bg']}; /* Match dropdown background */
            font-weight: bold; /* Make headers stand out slightly */
            padding-top: 3px; /* Add slight padding */
            padding-bottom: 3px;
            /* Prevent selection styling on disabled items */
            selection-background-color: transparent;
            selection-color: {colors['secondary_text']};
        }}
        
        QStatusBar {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border-top: 1px solid {colors['border']};
        }}
        
        /* Scroll bars - critical for macOS */
        QScrollArea, QScrollBar {{
            background-color: {colors['bg']};
            color: {colors['text']};
        }}
        
        QScrollBar:vertical {{
            border: none;
            background: {colors['card_bg']};
            width: 10px;
            margin: 0px;
        }}
        
        QScrollBar::handle:vertical {{
            background: {colors['border']};
            min-height: 20px;
            border-radius: 5px;
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            border: none;
            background: {colors['card_bg']};
            height: 10px;
            margin: 0px;
        }}
        
        QScrollBar::handle:horizontal {{
            background: {colors['border']};
            min-width: 20px;
            border-radius: 5px;
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        
        /* Tab widget styling */
        QTabWidget::pane {{
            border: 1px solid {colors['border']};
            background-color: {colors['bg']};
        }}
        
        QTabBar::tab {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-bottom: none;
            padding: 5px 10px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors['bg']};
            border-bottom: none;
            border-left: 1px solid {colors['border']};
            border-top: 2px solid {colors['accent']};
            border-right: 1px solid {colors['border']};
        }}
        
        QTabBar::tab:!selected {{
            margin-top: 2px;
        }}
        
        /* Direct and focused styling for combo box popup items */
        QComboBox QAbstractItemView::item:hover {{
            background-color: {colors['accent']};
            color: white;
            font-weight: bold;
            border-left: 5px solid white;
        }}
        
        QComboBox QAbstractItemView::item:selected {{
            background-color: {colors['highlight_bg']};
            color: {colors['highlight_text']};
            border-left: 3px solid {colors['accent']};
        }}
        
        /* Add specific macOS overrides */
        QToolButton {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 3px;
        }}
        
        QToolButton:hover {{
            background-color: {colors['hover_bg']};
            border: 1px solid {colors['accent']};
        }}
        
        QToolButton:pressed {{
            background-color: {colors['accent']};
            color: white;
        }}
        
        /* Group box styling */
        QGroupBox {{
            border: 1px solid {colors['border']};
            margin-top: 6px;
            padding-top: 10px;
            background-color: {colors['bg']};
            color: {colors['text']};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            padding: 0 3px;
            background-color: {colors['bg']};
            color: {colors['text']};
        }}
        
        /* Style for Accent Buttons (e.g., Close button in dialogs) */
        QPushButton#closeButtonAccent {{
            {ACCENT_BUTTON_STYLE}
        }}
    """)

    # Define CheckBox QSS separately
    checkbox_qss = f"""
        QCheckBox {{ 
            spacing: 5px; /* Space between indicator and text */
            color: {colors['text']}; /* Ensure text color matches theme */
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {colors['border']};
            border-radius: 3px;
            background-color: {colors['card_bg']}; /* Slightly different background */
        }}
        QCheckBox::indicator:hover {{
            border: 1px solid {colors['accent']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {colors['accent']};
            border: 1px solid {colors['accent']};
            image: url("/Users/craigrusso/SynologyDrive/SCRIPTS/CLAUSE PROJECT CREATOR/V4/app/assets/css/check.svg");
        }}
        QCheckBox::indicator:disabled {{
            border: 1px solid {colors['secondary_text']};
            background-color: {colors['bg']};
        }}
        QCheckBox::indicator:checked:disabled {{
            background-color: {colors['secondary_text']};
            image: url("/Users/craigrusso/SynologyDrive/SCRIPTS/CLAUSE PROJECT CREATOR/V4/app/assets/css/check.svg");
        }}
    """

    # Append checkbox QSS to the main stylesheet
    app.setStyleSheet(app.styleSheet() + checkbox_qss)
    
    # Create programmatic checkmark icon for checkboxes
    def create_checkmark_icon():
        size = 14  # Size of the checkmark icon
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)  # Start with transparent background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # Draw checkmark path
        path = QPainterPath()
        path.moveTo(3, 7)
        path.lineTo(6, 10)
        path.lineTo(11, 4)
        
        # Set up painter
        pen = QPen(QColor("white"))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Draw the path
        painter.drawPath(path)
        painter.end()
        
        return pixmap
    
    # Create a custom checkbox style that adds the checkmark directly
    class CheckboxStyle(QProxyStyle):
        def __init__(self):
            super().__init__()
            self.checkmark = create_checkmark_icon()
        
        def drawControl(self, element, option, painter, widget=None):
            # First draw the checkbox normally
            super().drawControl(element, option, painter, widget)
            
            # If this is a checkbox indicator and it's checked, draw our checkmark
            if element == QStyle.ControlElement.CE_CheckBox or element == QStyle.ControlElement.CE_CheckBoxLabel:
                if option.state & QStyle.State.State_On:  # If checked
                    # Get the indicator rect
                    rect = self.subElementRect(QStyle.SubElement.SE_CheckBoxIndicator, option, widget)
                    
                    # Calculate position to center the checkmark in the indicator
                    x = rect.x() + (rect.width() - self.checkmark.width()) // 2
                    y = rect.y() + (rect.height() - self.checkmark.height()) // 2
                    
                    # Draw the checkmark
                    painter.drawPixmap(x, y, self.checkmark)
            
        def drawPrimitive(self, element, option, painter, widget=None):
            # If this is a checkbox indicator and it's checked, handle custom drawing
            if element == QStyle.PrimitiveElement.PE_IndicatorCheckBox and option.state & QStyle.State.State_On:
                # Draw the blue background and border (already done by stylesheet)
                super().drawPrimitive(element, option, painter, widget)
                
                # Draw our checkmark on top
                rect = option.rect
                x = rect.x() + (rect.width() - self.checkmark.width()) // 2
                y = rect.y() + (rect.height() - self.checkmark.height()) // 2
                painter.drawPixmap(x, y, self.checkmark)
            else:
                # For all other elements, use default drawing
                super().drawPrimitive(element, option, painter, widget)
    
    # Install custom style for all checkboxes
    app.setStyle(CheckboxStyle())
    
    # Install a global event filter to catch combo box popups
    # popup_filter = ComboBoxPopupFilter() # TEMPORARILY COMMENTED OUT
    # QApplication.instance().installEventFilter(popup_filter) # TEMPORARILY COMMENTED OUT
    # print("DEBUG THEME: ComboBoxPopupFilter installation commented out for testing.") # TEMPORARILY COMMENTED OUT

def apply_theme_to_widgets(widget_or_app):
    """Apply theme to all widgets in the application"""
    # Determine if we're dealing with an app object or a widget
    if hasattr(widget_or_app, 'setStyleSheet'):
        # It's a QApplication
        app = widget_or_app
        configure_styles(app)
    elif hasattr(widget_or_app, 'centralWidget'):
        # It's a main window
        main_window = widget_or_app
        update_widget_colors(main_window.centralWidget())
    else:
        # It's a widget
        update_widget_colors(widget_or_app)

def update_widget_colors(widget):
    """Recursively update colors for a widget and its children"""
    try:
        # Handle different widget types
        if isinstance(widget, QFrame):
            widget.setStyleSheet(f"background-color: {colors['card_bg']}; color: {colors['text']};")
        
        elif isinstance(widget, QLabel):
            # Check if this is a title label or regular label
            font = widget.font()
            if font.bold():
                widget.setStyleSheet(f"color: {colors['text']}; font-weight: bold;")
            else:
                widget.setStyleSheet(f"color: {colors['text']};")
        
        elif isinstance(widget, QLineEdit):
            widget.setStyleSheet(LINEEDIT_STYLE)
        
        elif isinstance(widget, QPushButton):
            # Check if this is an accent button
            if hasattr(widget, 'objectName') and "accent" in widget.objectName().lower():
                widget.setStyleSheet(ACCENT_BUTTON_STYLE)
            else:
                widget.setStyleSheet(BUTTON_STYLE)
        
        elif isinstance(widget, QComboBox):
            widget.setStyleSheet(COMBOBOX_STYLE)
        
    except Exception as e:
        # Skip widgets we can't configure or that don't have these properties
        print(f"Error updating widget {widget}: {e}")
    
    # Process children of this widget
    try:
        for child in widget.findChildren(QWidget):
            update_widget_colors(child)
    except Exception as e:
        # Some widgets might cause issues
        print(f"Error processing children of {widget}: {e}")

def apply_dark_theme_to_template_gallery(widget):
    """Apply dark theme styling to template gallery components"""
    if not widget:
        return
    
    # Apply dark theme to template cards and gallery components
    widget.setStyleSheet(f"""
        QWidget {{
            background-color: {colors['bg']};
            color: {colors['text']};
        }}
        
        QFrame {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border-radius: 5px;
            border: 1px solid {colors['border']};
        }}
        
        QLabel {{
            color: {colors['text']};
        }}
        
        QPushButton {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 5px 10px;
        }}
        
        QPushButton:hover {{
            background-color: {colors['hover_bg']};
        }}
        
        QPushButton:pressed {{
            background-color: {colors['accent']};
        }}
        
        QPushButton:checked {{
            background-color: {colors['highlight_bg']};
            color: white;
        }}
        
        QLineEdit {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 5px;
        }}
        
        QScrollArea {{
            border: none;
            background-color: {colors['bg']};
        }}
        
        QScrollArea > QWidget > QWidget {{
            background-color: {colors['bg']};
        }}
        
        QTreeWidget {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
        }}
        
        QTreeWidget::item:selected {{
            background-color: {colors['highlight_bg']};
            color: white;
        }}
    """)
    
    # Explicitly set background color for the gallery widget and scroll area if they exist
    if hasattr(widget, 'gallery_widget'):
        widget.gallery_widget.setStyleSheet(f"background-color: {colors['bg']};")
    
    if hasattr(widget, 'gallery_scroll'):
        widget.gallery_scroll.setStyleSheet(f"background-color: {colors['bg']};")

class ThemeEventFilter(QObject):
    """Event filter to apply theme to newly created widgets"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def eventFilter(self, obj, event):
        """Filter events to catch widget creation"""
        # If a QInputDialog is created or a QComboBox is created in any dialog
        if event.type() == QEvent.ChildAdded and isinstance(obj, QWidget):
            # Look for QComboBox in the added child widget's hierarchy
            self.apply_style_to_combos_recursively(event.child())
        
        # When a popup is shown, check if it's a combobox popup and style it
        if event.type() == QEvent.Show and obj.objectName() == "QComboBoxListView":
            # This is a combobox popup, style it directly
            from app.ui.color_scheme_pyqt import COMBOBOX_STYLE
            obj.setStyleSheet(COMBOBOX_STYLE)
            
        return super().eventFilter(obj, event)
    
    def apply_style_to_combos_recursively(self, widget):
        """Recursively find and style QComboBox widgets"""
        # Apply style if this is a QComboBox
        if isinstance(widget, QComboBox):
            widget.setStyleSheet(COMBOBOX_STYLE)
            
            # Ensure the popup is styled when shown
            widget.installEventFilter(self)
        
        # Check children recursively
        for child in widget.findChildren(QWidget):
            self.apply_style_to_combos_recursively(child)

def apply_dark_theme_to_template_section(app):
    """Apply dark grey theme to template file section"""
    # Find the template file frame in PyQt version
    template_frame = None
    
    if hasattr(app, 'template_file_frame'):
        template_frame = app.template_file_frame
    elif hasattr(app, 'template_section'):
        template_frame = app.template_section
    
    if template_frame:
        # Apply darker background to the template section
        template_frame.setStyleSheet(f"""
            background-color: #282828;
            color: {colors['text']};
            border: none;
            border-radius: 0px;
        """)
        
        # Update all child widgets
        for child in template_frame.findChildren(QWidget):
            if isinstance(child, QLabel) or isinstance(child, QFrame):
                child.setStyleSheet(f"background-color: #282828; color: {colors['text']};")
            elif isinstance(child, QPushButton):
                child.setStyleSheet(BUTTON_STYLE)
            elif isinstance(child, QComboBox):
                child.setStyleSheet(COMBOBOX_STYLE)
                # Apply hover delegate to comboboxes for better hover effects
                from app.ui.custom_delegates import apply_hover_delegate
                apply_hover_delegate(child)
            elif isinstance(child, QLineEdit):
                child.setStyleSheet(LINEEDIT_STYLE)
    
    # Update other template container elements if they exist
    for widget_name in ['template_file_container', 'recent_templates_frame']:
        if hasattr(app, widget_name):
            widget = getattr(app, widget_name)
            widget.setStyleSheet(f"""
                background-color: #282828; 
                color: {colors['text']};
                border: none;
                border-radius: 0px;
            """)
            
            # Also update all child widgets
            for child in widget.findChildren(QWidget):
                if isinstance(child, QLabel) or isinstance(child, QFrame):
                    child.setStyleSheet(f"background-color: #282828; color: {colors['text']};")
                elif isinstance(child, QPushButton):
                    child.setStyleSheet(BUTTON_STYLE)
                elif isinstance(child, QComboBox):
                    child.setStyleSheet(COMBOBOX_STYLE)
                    # Apply hover delegate to comboboxes for better hover effects
                    from app.ui.custom_delegates import apply_hover_delegate
                    apply_hover_delegate(child)
                elif isinstance(child, QLineEdit):
                    child.setStyleSheet(LINEEDIT_STYLE)
    
    # Force a repaint to ensure changes take effect
    if template_frame:
        template_frame.update()

def apply_theme_recursively(widget):
    """Apply theme to widget and its children recursively"""
    apply_theme_to_widget(widget)
    
    # Process child widgets
    for child in widget.findChildren(QWidget):
        apply_theme_to_widget(child)

def apply_theme_to_widget(widget):
    """Apply appropriate theme to widget based on its type"""
    if widget is None:
        return
        
    # Apply appropriate styling based on widget type
    if isinstance(widget, QPushButton):
        if widget.property("accent"):
            widget.setStyleSheet(ACCENT_BUTTON_STYLE)
        else:
            widget.setStyleSheet(BUTTON_STYLE)
    elif isinstance(widget, QLineEdit):
        widget.setStyleSheet(LINEEDIT_STYLE)
    elif isinstance(widget, QLabel):
        # Don't style labels with custom styling
        if not widget.styleSheet():
            widget.setStyleSheet(LABEL_STYLE)
    elif isinstance(widget, QComboBox):
        widget.setStyleSheet(COMBOBOX_STYLE)
    elif isinstance(widget, QFrame):
        # Prevent overriding custom frame styling
        pass

class GlobalMouseEventFilter(QObject):
    """Global filter to debug mouse events on the entire application"""
    
    def eventFilter(self, obj, event):
        # Only log dropdown-related events to avoid console spam
        if isinstance(obj, QListView) or (hasattr(obj, 'objectName') and "combo" in obj.objectName().lower()):
            if event.type() == QEvent.MouseMove:
                print(f"DEBUG: GLOBAL - Mouse move on {obj} at {time.time()}")
            elif event.type() == QEvent.MouseButtonPress:
                print(f"DEBUG: GLOBAL - Mouse press on {obj} at {time.time()}")
        
        # Important: always return False to allow event propagation
        return False

# ComboBoxItemHoverFilter class removed as part of hover simplification.

def apply_dark_theme_to_template_section(app):
    """Apply dark grey theme to template file section"""
    # Find the template file frame in PyQt version
    template_frame = None
    
    if hasattr(app, 'template_file_frame'):
        template_frame = app.template_file_frame
    elif hasattr(app, 'template_section'):
        template_frame = app.template_section
    
    if template_frame:
        # Apply darker background to the template section
        template_frame.setStyleSheet(f"""
            background-color: #282828;
            color: {colors['text']};
            border: none;
            border-radius: 0px;
        """)
        
        # Update all child widgets
        for child in template_frame.findChildren(QWidget):
            if isinstance(child, QLabel) or isinstance(child, QFrame):
                child.setStyleSheet(f"background-color: #282828; color: {colors['text']};")
            elif isinstance(child, QPushButton):
                child.setStyleSheet(BUTTON_STYLE)
            elif isinstance(child, QComboBox):
                child.setStyleSheet(COMBOBOX_STYLE)
                # Apply hover delegate to comboboxes for better hover effects
                from app.ui.custom_delegates import apply_hover_delegate
                apply_hover_delegate(child)
            elif isinstance(child, QLineEdit):
                child.setStyleSheet(LINEEDIT_STYLE)
    
    # Update other template container elements if they exist
    for widget_name in ['template_file_container', 'recent_templates_frame']:
        if hasattr(app, widget_name):
            widget = getattr(app, widget_name)
            widget.setStyleSheet(f"""
                background-color: #282828; 
                color: {colors['text']};
                border: none;
                border-radius: 0px;
            """)
            
            # Also update all child widgets
            for child in widget.findChildren(QWidget):
                if isinstance(child, QLabel) or isinstance(child, QFrame):
                    child.setStyleSheet(f"background-color: #282828; color: {colors['text']};")
                elif isinstance(child, QPushButton):
                    child.setStyleSheet(BUTTON_STYLE)
                elif isinstance(child, QComboBox):
                    child.setStyleSheet(COMBOBOX_STYLE)
                    # Apply hover delegate to comboboxes for better hover effects
                    from app.ui.custom_delegates import apply_hover_delegate
                    apply_hover_delegate(child)
                elif isinstance(child, QLineEdit):
                    child.setStyleSheet(LINEEDIT_STYLE)
    
    # Force a repaint to ensure changes take effect
    if template_frame:
        template_frame.update() 