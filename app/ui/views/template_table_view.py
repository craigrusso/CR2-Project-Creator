#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
QTableView subclass for displaying templates with spreadsheet-like column behavior.
"""

import os
from PyQt5.QtWidgets import (QTableView, QHeaderView, QAbstractItemView, 
                             QStyledItemDelegate, QStyleOptionViewItem, QStyle,
                             QStyleOptionHeader)
from PyQt5.QtCore import Qt, QSettings, QModelIndex, QSize, QRect, QPoint, QSortFilterProxyModel, QByteArray, QMimeData
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QPalette, QIcon, QBrush, QPainter, QFontMetrics, QFont, QDrag

from app.constants import get_resource_path
try:
    from app.ui.color_scheme_pyqt import colors
except ImportError:
    # Define fallback colors if the import fails
    colors = {
        'header_bg': '#2A2A2A',
        'secondary_text': '#CCCCCC',
        'border_dark': '#3C3C3C',
        'bg_hover': '#3E3E3E',
        'selection_bg': '#2C4F76',
        'primary_text': '#FFFFFF',
        'bg_dark': '#1E1E1E',
        'bg_medium': '#2A2A2A'
    }

# Placeholder for future model if needed separately
# class TemplateTableModel(QStandardItemModel):
#     pass

# --- Custom Delegate for Icon + Name ---
# Define a custom role for the warning flag
WarningRole = Qt.UserRole + 1

class IconNameDelegate(QStyledItemDelegate):
    """ Delegate to draw icon or warning character and text in the Name column. """
    def __init__(self, icon_size=QSize(18, 18), padding=4, parent=None):
        super().__init__(parent)
        self.icon_size = icon_size
        self.padding = padding # Space between icon and text, and left margin

    def paint(self, painter, option, index):
        # Ensure we have style options
        self.initStyleOption(option, index)
        
        # Get data from the model 
        icon = index.data(Qt.DecorationRole) # Get icon set in populate_data
        text = index.data(Qt.DisplayRole)
        is_warning = index.data(WarningRole) # Get warning flag
        
        # Get the cell rectangle
        rect = option.rect
        
        # --- Draw Background (Handles selection, alternating rows) ---
        # Let the default delegate handle background drawing
        option.text = "" # Prevent default text drawing
        option.icon = QIcon() # Prevent default icon drawing by base class
        option.widget.style().drawControl(QStyle.CE_ItemViewItem, option, painter, option.widget)
        
        # --- Draw Icon or Warning Character --- 
        icon_offset = self.padding # Default to only left padding
        
        # Calculate vertical center for icon/warning
        v_center = rect.y() + (rect.height() - self.icon_size.height()) // 2
        h_pos = rect.x() + self.padding
        
        if is_warning:
            # Draw warning character "⚠"
            painter.save()
            warning_color = QColor(colors.get('error', '#FF5252'))
            painter.setPen(warning_color) 
            # Use a font size appropriate for the icon size
            font = painter.font()
            font.setPointSize(int(self.icon_size.height() * 0.8)) # Cast to int
            font.setBold(True)
            painter.setFont(font)
            # Ensure the character is centered vertically within the icon area
            fm = QFontMetrics(font)
            char_rect = QRect(h_pos, rect.y(), self.icon_size.width(), rect.height())
            painter.drawText(char_rect, Qt.AlignCenter, "⚠")
            painter.restore()
            icon_offset = self.icon_size.width() + self.padding * 2
            
        elif isinstance(icon, QIcon) and not icon.isNull(): # Draw default icon if not warning
            icon_rect = QRect(QPoint(h_pos, v_center), self.icon_size)
            pixmap = icon.pixmap(self.icon_size, 
                                 QIcon.Normal if (option.state & QStyle.State_Selected) == 0 else QIcon.Selected,
                                 QIcon.On if (option.state & QStyle.State_Selected) != 0 else QIcon.Off)
            painter.drawPixmap(icon_rect, pixmap)
            icon_offset = self.icon_size.width() + self.padding * 2 # Icon width + padding on both sides
        
        # --- Draw Text --- 
        if text:
            # Calculate text position (right of icon, vertically centered)
            # Start text after icon + padding
            text_x = rect.x() + icon_offset
            text_rect = QRect(text_x, rect.y(), rect.width() - icon_offset - self.padding, rect.height())
            
            # Set text color based on selection
            text_color = option.palette.highlightedText().color() if (option.state & QStyle.State_Selected) else option.palette.text().color()
            painter.setPen(text_color)
            
            # Use style options for font, alignment etc.
            # Elide text if it overflows
            elided_text = option.fontMetrics.elidedText(text, Qt.ElideRight, text_rect.width())
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, elided_text)

    def sizeHint(self, option, index):
        # Provide a size hint, potentially adding padding
        size = super().sizeHint(option, index)
        # Optionally increase height if needed
        # size.setHeight(max(size.height(), self.icon_size.height() + 2 * self.padding))
        return size
# ---------------------------------------

# --- Custom Header View for Sorting Highlight ---
class SortableHeaderView(QHeaderView):
    """ Custom header view that highlights the sorted section background. """
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setSectionsClickable(True)
        # Define colors needed for painting (could be passed in)
        self.header_bg = QColor(colors.get('header_bg', '#2A2A2A'))
        self.highlight_bg = QColor(colors.get('selection_bg', '#2C4F76'))
        self.text_color = QColor(colors.get('secondary_text', '#CCCCCC'))
        self.highlight_text_color = QColor(colors.get('primary_text', '#FFFFFF'))
        self.border_color = QColor(colors.get('border_dark', '#3C3C3C'))

    def paintSectionBackground(self, painter: QPainter, rect: QRect, logicalIndex: int):
        """Paints the background of the header section."""
        is_sorted = self.sortIndicatorSection() == logicalIndex

        painter.save()

        # Set background color based on sort state
        if is_sorted:
            bg_color = self.highlight_bg # Use pre-defined highlight color
        else:
            # Use the default header background color from the theme
            bg_color = self.header_bg 
        
        painter.fillRect(rect, bg_color)
        
        # Optionally, draw a bottom border (simpler approach)
        # pen = QPen(self.palette().color(QPalette.Midlight))
        # pen.setWidth(1)
        # painter.setPen(pen)
        # painter.drawLine(rect.bottomLeft(), rect.bottomRight())

        painter.restore()

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()

        # --- 1. Draw Custom Background --- 
        self.paintSectionBackground(painter, rect, logicalIndex)

        # Determine sort state
        is_sorted_section = (self.isSortIndicatorShown() and self.sortIndicatorSection() == logicalIndex)
        
        # --- 2. Calculate Rects for Text and Arrow --- 
        arrow_width = 0
        arrow_rect = QRect()
        padding = 8 # Padding around elements
        
        if is_sorted_section:
            # Calculate arrow rectangle (small square on the right)
            arrow_size = min(rect.height() // 2, 8) # Make arrow smaller, max 8px
            arrow_rect = QRect(rect.right() - arrow_size - padding, 
                               rect.center().y() - arrow_size // 2, 
                               arrow_size, arrow_size)
            arrow_width = arrow_size + padding # Space to reserve on the right
        
        # Text rect takes remaining space, considering left padding and arrow width on right
        text_rect = rect.adjusted(padding, 0, -arrow_width, 0)

        # --- 3. Draw Header Text Manually --- 
        text_color = self.highlight_text_color if is_sorted_section else self.text_color
        painter.setPen(text_color) # Set the text color directly
        
        # Get text and alignment flags
        text = self.model().headerData(logicalIndex, self.orientation(), Qt.DisplayRole)
        alignment = Qt.AlignLeft | Qt.AlignVCenter # Consistent alignment
        
        # Elide text if necessary
        elided_text = painter.fontMetrics().elidedText(text, Qt.ElideRight, text_rect.width())
        
        # Draw the text within the calculated text_rect
        painter.drawText(text_rect, alignment, elided_text)

        # --- 4. Draw Sort Indicator Arrow Manually (using Style Primitive) --- 
        if is_sorted_section:
            arrow_option = QStyleOptionHeader() # Use a separate option for the arrow
            # Initialize necessary fields for the primitive to work
            self.initStyleOption(arrow_option) # Initialize default state etc.
            arrow_option.rect = arrow_rect # Use the specific, smaller arrow rectangle
            # Set sort indicator state
            arrow_option.sortIndicator = QStyleOptionHeader.SortDown if self.sortIndicatorOrder() == Qt.DescendingOrder else QStyleOptionHeader.SortUp
            
            # Draw the primitive within the calculated arrow_rect
            self.style().drawPrimitive(QStyle.PE_IndicatorHeaderArrow, arrow_option, painter, self)
        
        painter.restore()

# ---------------------------------------------

# --- Proxy Model for Sorting ---
class TemplateSortFilterProxyModel(QSortFilterProxyModel):
    """ Custom proxy model to handle sorting based on specific data roles. """
    COLUMN_HEADERS = ["Name", "Category", "Created", "Modified"] # Keep headers consistent

    def lessThan(self, left, right):
        """ Compare items based on column type. """
        col = left.column()
        left_data = self.sourceModel().data(left, Qt.EditRole) # Prefer EditRole for sorting
        right_data = self.sourceModel().data(right, Qt.EditRole)
        
        # Fallback to DisplayRole if EditRole is None (e.g., for Name, Category)
        if left_data is None:
            left_data = self.sourceModel().data(left, Qt.DisplayRole)
        if right_data is None:
            right_data = self.sourceModel().data(right, Qt.DisplayRole)
            
        # Handle None values (e.g., put them at the end)
        if left_data is None and right_data is None: return False
        if left_data is None: return False # None is considered greater than valid data
        if right_data is None: return True # Valid data is considered less than None
        
        try:
            # Attempt numeric comparison first (for dates/timestamps)
            return float(left_data) < float(right_data)
        except (ValueError, TypeError):
            # Fallback to string comparison for non-numeric types
            return str(left_data).lower() < str(right_data).lower()

# ------------------------------

class TemplateTableView(QTableView):
    """
    A QTableView customized to behave like macOS Finder's list view 
    or a spreadsheet, with specific column resizing and persistent state.
    """
    SETTINGS_KEY_HEADER_STATE = "templateTableView/columnState"
    DEFAULT_MIN_COLUMN_WIDTH = 100
    COLUMN_HEADERS = ["Name", "Category", "Created", "Modified"] # Example columns
    # Define icon paths
    DEFAULT_ICON_PATH = "ICONS/templates/template_structure_icon.svg"
    WARNING_ICON_PATH = "ICONS/alert-triangle.svg" # Path for the warning icon
    DEFAULT_ICON_SIZE = QSize(18, 18) # Define a default icon size

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Load icons during initialization
        self._load_icons()
        
        self._configure_appearance()
        self._configure_header()
        self._setup_model()
        self._restore_state()
        
        # Set custom delegate for the Name column (index 0)
        self.icon_name_delegate = IconNameDelegate(icon_size=self.DEFAULT_ICON_SIZE, 
                                                   parent=self) # No need to pass default icon
        self.setItemDelegateForColumn(0, self.icon_name_delegate)
        
        # Hide the vertical header (row numbers)
        self.verticalHeader().hide()
        
        # Variable to store the current sort column index
        self._current_sort_column = -1 

    def _load_icons(self):
        """Load icons used in the table view."""
        try:
            self.default_icon = QIcon(get_resource_path(self.DEFAULT_ICON_PATH))
            if self.default_icon.isNull():
                 print(f"WARNING: Failed to load default icon: {self.DEFAULT_ICON_PATH}")
                 self.default_icon = QIcon() # Use empty icon as fallback
        except Exception as e:
             print(f"ERROR loading default icon: {e}")
             self.default_icon = QIcon()
             
        # Warning icon is now handled by the delegate using Unicode character
        self.warning_icon = None # No longer need to load the SVG

    def _configure_appearance(self):
        """Configure basic appearance and behavior of the table view."""
        self.setObjectName("TemplateTableView")
        self.setAlternatingRowColors(True) # Improves readability
        self.setShowGrid(False) # Cleaner look, like Finder
        self.setWordWrap(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection) # Allow multi-select
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers) # Read-only view
        
        # Enable sorting
        self.setSortingEnabled(True)
        
        # --- Enable Dragging --- 
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly) # We only drag *from* this table
        # ---------------------
        
        # Set default icon size for the view - No longer needed here, delegate handles size
        # self.setIconSize(self.DEFAULT_ICON_SIZE) 
        
        # Apply basic styling from color scheme
        # More specific styling might be needed via QSS
        palette = self.palette()
        palette.setColor(QPalette.Base, QColor(colors.get('bg_dark', '#1E1E1E')))
        palette.setColor(QPalette.AlternateBase, QColor(colors.get('bg_medium', '#2A2A2A')))
        palette.setColor(QPalette.Text, QColor(colors.get('primary_text', '#FFFFFF')))
        palette.setColor(QPalette.HighlightedText, QColor(colors.get('primary_text', '#FFFFFF')))
        palette.setColor(QPalette.Highlight, QColor(colors.get('selection_bg', '#2C4F76')))
        self.setPalette(palette)
        
        # Delegate for custom row padding/styling if needed
        # self.setItemDelegate(RowPaddingDelegate(self))

    def _configure_header(self):
        """Configure the horizontal header view for desired resize behavior."""
        # Use the custom SortableHeaderView
        header = SortableHeaderView(Qt.Horizontal, self)
        self.setHorizontalHeader(header)
        
        header.setObjectName("TemplateTableHeader")
        
        # Enable interactive resizing, disable auto-stretching
        header.setSectionResizeMode(QHeaderView.Interactive) 
        header.setStretchLastSection(False) 
        
        # Allow reordering columns
        header.setSectionsMovable(True)
        
        # Prevent sections from collapsing too small
        header.setMinimumSectionSize(self.DEFAULT_MIN_COLUMN_WIDTH)
        
        # Ensure header text is visible
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Apply some basic styling (can be enhanced with QSS)
        # --- Temporarily commented out to test palette conflict ---
        header.setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {colors.get('header_bg', '#2A2A2A')};
                color: {colors.get('secondary_text', '#CCCCCC')};
                padding: 4px 8px;
                border-top: 1px solid {colors.get('border_dark', '#3C3C3C')};
                border-bottom: 1px solid {colors.get('border_dark', '#3C3C3C')};
                border-right: 1px solid {colors.get('border_dark', '#3C3C3C')};
                border-left: none; /* Avoid double borders */
                height: 30px; /* Consistent header height */
            }}
            QHeaderView::section:first {{
                border-left: 1px solid {colors.get('border_dark', '#3C3C3C')}; 
            }}
            QHeaderView::section:hover {{
                background-color: {colors.get('bg_hover', '#3E3E3E')};
            }}
            /* Style for the sorted column header */
            /* Highlighting handled by SortableHeaderView.paintSection */
            /* Remove custom arrow styling to allow native arrows */
        """)
        # ------------------------------------------------------

    def _setup_model(self):
        """Initialize the data model for the table."""
        self.source_model_instance = QStandardItemModel(0, len(self.COLUMN_HEADERS), self)
        self.source_model_instance.setHorizontalHeaderLabels(self.COLUMN_HEADERS)
        
        # TODO: Populate with actual template data later
        
        # --- Setup Proxy Model ---
        self.proxy_model = TemplateSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.source_model_instance)
        self.setModel(self.proxy_model) # Set the PROXY model on the view
        # -------------------------

    def populate_data(self, templates_data):
        """
        Populates the table model with data.
        Expects templates_data to be a list of dictionaries,
        where each dictionary represents a template.
        """
        source_model = self.proxy_model.sourceModel()
        if not source_model:
             print("[ERROR] Populate data: Could not get source model from proxy.")
             return
             
        source_model.removeRows(0, source_model.rowCount()) # Clear existing data on source model
        
        if not templates_data:
            return
            
        # Example: Assumes template dicts have keys matching COLUMN_HEADERS (case-insensitive)
        col_map = {header.lower(): i for i, header in enumerate(self.COLUMN_HEADERS)}

        for template in templates_data:
            row_items = [QStandardItem() for _ in self.COLUMN_HEADERS] # Create items for all columns
            
            name = template.get('name', 'Unknown') # Ensure name exists
            name_item = QStandardItem(name)
            row_items[col_map.get('name', 0)] = name_item
            
            # --- Set Icon based on structure presence --- Corrected Logic ---
            has_structure = bool(template.get('structure'))
            if not has_structure:
                # name_item.setIcon(self.warning_icon) # Don't set icon, delegate handles warning char
                name_item.setData(True, WarningRole) # Set the warning flag
                name_item.setToolTip("This template has no folder structure defined.")
            else:
                name_item.setIcon(self.default_icon) # Explicitly set default icon here
                name_item.setData(False, WarningRole) # Explicitly clear warning flag
                name_item.setToolTip(f"Template: {name}") 
            # ---------------------------------------------------------------
            
            # --- Set Data for Other Columns ---
            # Iterate through expected columns and set data if available in template
            for header, col_index in col_map.items():
                if header == 'name': # Already handled
                    continue 
                    
                raw_value = template.get(header)
                item = QStandardItem() # Create item for this column

                if raw_value is not None:
                    if header in ['created', 'modified']:
                        try:
                            # Store raw timestamp for sorting
                            timestamp = float(raw_value)
                            item.setData(timestamp, Qt.EditRole) 
                            # Store formatted string for display
                            display_str = self._format_timestamp(timestamp)
                            item.setData(display_str, Qt.DisplayRole)
                        except (ValueError, TypeError):
                            item.setData(str(raw_value), Qt.DisplayRole) # Fallback to string
                            item.setData(str(raw_value), Qt.EditRole)
                    else:
                        # For other columns (like Category), store as string
                        item.setData(str(raw_value), Qt.DisplayRole)
                        item.setData(str(raw_value), Qt.EditRole)
                        
                row_items[col_index] = item # Assign the configured item to the row
            
            source_model.appendRow(row_items) # Append to source model directly
            
        # Re-apply the current sort after populating - Proxy model handles sorting
        # The view triggers the proxy model sort when headers are clicked or sorting is enabled.
        # If we want an initial sort after load, we can trigger it on the proxy:
        # sort_col = self.horizontalHeader().sortIndicatorSection()
        # sort_order = self.horizontalHeader().sortIndicatorOrder()
        # self.proxy_model.sort(sort_col, sort_order)
        # Let's rely on header clicks or restored state for now.
        
        # Update header styling
        # Header update needed to reflect sort arrow, done by _set_sort_indicator
        self._set_sort_indicator(self.horizontalHeader().sortIndicatorSection(), 
                                 self.horizontalHeader().sortIndicatorOrder())

    def _format_timestamp(self, timestamp):
        """Helper to format timestamp into a readable string."""
        import datetime
        try:
            dt_object = datetime.datetime.fromtimestamp(float(timestamp))
            return dt_object.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return "" # Handle invalid timestamps gracefully

    def save_state(self):
        """Save the current column widths and order to QSettings."""
        settings = QSettings()
        header_state = self.horizontalHeader().saveState()
        settings.setValue(self.SETTINGS_KEY_HEADER_STATE, header_state)
        print(f"DEBUG: Saved header state for {self.objectName()}")

    def _restore_state(self):
        """Restore column widths and order from QSettings."""
        settings = QSettings()
        header_state = settings.value(self.SETTINGS_KEY_HEADER_STATE)
        if header_state:
            restored = self.horizontalHeader().restoreState(header_state)
            if restored:
                print(f"DEBUG: Restored header state for {self.objectName()}")
            else:
                 print(f"WARNING: Failed to restore header state for {self.objectName()}")
        else:
            print(f"DEBUG: No saved header state found for {self.objectName()}")
            # Optional: Set default widths if no state saved
            # self.horizontalHeader().resizeSection(0, 300) # Example default for Name
            # self.horizontalHeader().resizeSection(1, 150) 
            # ... etc

    def _set_sort_indicator(self, column, order):
        """
        Sets the visual sort indicator on the header. Highlighting is now handled by SortableHeaderView.
        """
        header = self.horizontalHeader()
        header.setSortIndicator(column, order)
        
        # Just update the header to reflect the sort indicator arrow change and trigger repaint
        header.update()

    def startDrag(self, supportedActions):
        selected_indexes = self.selectionModel().selectedRows() # Get indexes for Name column (col 0)
        if not selected_indexes:
            return

        template_names = []
        model = self.model()
        if not model:
            print("[ERROR] startDrag: No model assigned to TableView via self.model()")
            return
        
        for index in selected_indexes:
            # Get data directly from the model's DisplayRole (proxy should handle this)
            name = model.data(index, Qt.DisplayRole)
            if name:
                template_names.append(name)
            else:
                 # Use the proxy index row for warning
                 print(f"[WARNING] startDrag: Could not get template name for proxy row {index.row()}")

        if not template_names:
            print("[WARNING] startDrag: No template names found for selected rows.")
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        
        # Encode template names, separated by newline
        encoded_data = "\n".join(template_names).encode('utf-8')
        mime_data.setData("application/x-echelon-template-names", QByteArray(encoded_data))
        
        print(f"[DEBUG] Starting drag for templates: {template_names}")
        drag.setMimeData(mime_data)
        
        # Default drag action
        drag.exec_(supportedActions, Qt.MoveAction)


# Optional: Delegate for adding padding (can be removed if not needed)
# class RowPaddingDelegate(QStyledItemDelegate):
#     def sizeHint(self, option, index):
#         size = super().sizeHint(option, index)
#         size.setHeight(size.height() + 6) # Add 3px padding top and bottom
#         return size
# 
#     def paint(self, painter, option, index):
#         # Adjust rect for padding before painting
#         option.rect = option.rect.adjusted(0, 3, 0, -3) 
#         super().paint(painter, option, index)


if __name__ == '__main__':
    # Example usage for testing
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    
    # Example data
    test_data = [
        {'name': 'Basic Project', 'category': 'General', 'created': 1678886400, 'modified': 1678886400},
        {'name': 'Web App Template', 'category': 'Web', 'created': 1678972800, 'modified': 1679059200},
        {'name': 'Data Science Setup', 'category': 'Data', 'created': 1679145600, 'modified': 1679145600},
    ]

    view = TemplateTableView()
    view.populate_data(test_data)
    view.setWindowTitle("Template Table View Test")
    view.resize(800, 400)
    view.show()

    # Test saving state on close
    app.aboutToQuit.connect(view.save_state)

    sys.exit(app.exec_()) 