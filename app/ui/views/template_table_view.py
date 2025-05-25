#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
QTableView subclass for displaying templates with spreadsheet-like column behavior.
"""

import os
from PyQt5.QtWidgets import (QTableView, QHeaderView, QAbstractItemView, 
                             QStyledItemDelegate, QStyleOptionViewItem, QStyle,
                             QStyleOptionHeader, QApplication, QMenu, QAction, QMessageBox)
from PyQt5.QtCore import Qt, QSettings, QModelIndex, QSize, QRect, QPoint, QSortFilterProxyModel, QByteArray, QMimeData, QItemSelectionModel, pyqtSignal, QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QPalette, QIcon, QBrush, QPainter, QFontMetrics, QFont, QDrag, QPixmap, QCursor

from app.constants import get_resource_path
# from app.utils.data_management import DataManager # Removed unused import
try:
    from app.ui.color_scheme_pyqt import colors
    from app.templates.drag_helpers import setup_drag_mime_data, create_drag_pixmap
    from app.templates.mime_types import TEMPLATE_NAMES_MIME_TYPE
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
    # For import failures, define the MIME type constant here as fallback
    TEMPLATE_NAMES_MIME_TYPE = "application/x-echelon-template-names"

# Placeholder for future model if needed separately
# class TemplateTableModel(QStandardItemModel):
#     pass

# Define a custom role for the warning flag
WarningRole = Qt.UserRole + 1
# Define custom roles for filtering
IsFolderRole = Qt.UserRole + 2
ParentPathRole = Qt.UserRole + 3

# --- Custom Delegate for Icon + Name ---
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
        
        # Save painter state to restore later
        painter.save()
        
        # --- Check Selection Status (Multiple Ways) ---
        # 1. First check the selection model directly (most reliable)
        is_selected = False
        if option.widget:
            view = option.widget
            if hasattr(view, 'selectionModel'):
                selection_model = view.selectionModel()
                if selection_model:
                    # Check if this row is selected in the model
                    is_selected = selection_model.isSelected(index)
                    
        # 2. Also check the option state as fallback
        if not is_selected:
            is_selected = bool(option.state & QStyle.State_Selected)
        
        # --- Draw Background ---
        if is_selected:
            # Use the standard highlight color for selected items
            highlight_brush = option.palette.highlight()
            painter.fillRect(rect, highlight_brush)
        else:
            # For non-selected items, use the default style
            option.text = "" # Prevent default text drawing
            option.icon = QIcon() # Prevent default icon drawing
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
            icon_mode = QIcon.Selected if is_selected else QIcon.Normal
            icon_state = QIcon.On if is_selected else QIcon.Off
            pixmap = icon.pixmap(self.icon_size, icon_mode, icon_state)
            painter.drawPixmap(icon_rect, pixmap)
            icon_offset = self.icon_size.width() + self.padding * 2 # Icon width + padding on both sides
        
        # --- Draw Text --- 
        if text:
            # Calculate text position (right of icon, vertically centered)
            # Start text after icon + padding
            text_x = rect.x() + icon_offset
            text_rect = QRect(text_x, rect.y(), rect.width() - icon_offset - self.padding, rect.height())
            
            # Set text color based on selection
            text_color = option.palette.highlightedText().color() if is_selected else option.palette.text().color()
            painter.setPen(text_color)
            
            # Use style options for font, alignment etc.
            # Elide text if it overflows
            elided_text = option.fontMetrics.elidedText(text, Qt.ElideRight, text_rect.width())
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, elided_text)
            
        # Restore painter state
        painter.restore()

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

        # --- 4. Platform-Specific Arrow Drawing --- 
        if is_sorted_section:
            import platform # Import platform module here
            if platform.system() == "Windows":
                # Draw simple character indicator for Windows
                indicator_char = "v" if self.sortIndicatorOrder() == Qt.DescendingOrder else "^"
                painter.setPen(text_color) # Use the same text color
                # Draw text centered within the arrow_rect
                painter.drawText(arrow_rect, Qt.AlignCenter, indicator_char)
            else:
                # Draw native arrow for macOS and others
                arrow_option = QStyleOptionHeader() 
                self.initStyleOption(arrow_option) 
                arrow_option.rect = arrow_rect 
                arrow_option.sortIndicator = (QStyleOptionHeader.SortDown 
                                           if self.sortIndicatorOrder() == Qt.DescendingOrder 
                                           else QStyleOptionHeader.SortUp)
                self.style().drawPrimitive(QStyle.PE_IndicatorHeaderArrow, arrow_option, painter, self)
        
        painter.restore()

# ---------------------------------------------

# --- Proxy Model for Sorting ---
class TemplateSortFilterProxyModel(QSortFilterProxyModel):
    """ Custom proxy model to handle sorting based on specific data roles and filtering. """
    COLUMN_HEADERS = ["Name", "Category", "Created", "Modified"] # Keep headers consistent

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_filter_folder_path = None # None means root view (show folders and unfoldered templates)
        self._sort_in_progress = False # Flag to track when sorting is happening

    def set_current_filter_folder(self, folder_path):
        """Set the path of the folder to filter by. None for root."""
        self._current_filter_folder_path = folder_path
        self.invalidateFilter()

    def sort(self, column, order=Qt.AscendingOrder):
        """Override sort to ensure filtering is maintained during sorting."""
        # Maintain a local reference to the current filter settings before sorting
        current_filter_path = self._current_filter_folder_path
        
        # First apply the filter strictly before sorting
        self.invalidateFilter()
        
        # Set flag to track sorting is in progress
        self._sort_in_progress = True
        
        # Perform the sort on the correctly filtered data
        super().sort(column, order)
        
        # Reset the flag and ensure filtering is applied again after sorting
        self._sort_in_progress = False
        
        # Ensure we restore the exact same filter state
        self._current_filter_folder_path = current_filter_path
        
        # Re-apply filtering with a small delay to ensure sorting is completed
        QTimer.singleShot(10, self.invalidateFilter)

    def lessThan(self, left, right):
        """Custom sorting implementation that prioritizes folders and handles different data types."""
        # Get the source model
        source_model = self.sourceModel()
        
        # Get the data from the source model for each index
        left_is_folder = source_model.data(left, IsFolderRole)
        right_is_folder = source_model.data(right, IsFolderRole)
        
        # Always put folders first (regardless of sort order)
        if left_is_folder and not right_is_folder:
            return True  # Folder comes before normal item
        if not left_is_folder and right_is_folder:
            return False # Normal item comes after folder
        
        # If both are folders or both are normal items, sort by the column data
        left_data = source_model.data(left)
        right_data = source_model.data(right)
        
        if left_data is None: return False # None is considered greater than valid data
        if right_data is None: return True # Valid data is considered less than None
        
        try:
            # Attempt numeric comparison first (for dates/timestamps)
            return float(left_data) < float(right_data)
        except (ValueError, TypeError):
            # Fallback to string comparison for non-numeric types
            return str(left_data).lower() < str(right_data).lower()

    def filterAcceptsRow(self, source_row, source_parent_index):
        """ Determines whether a row should be included in the filtered view. """
        source_model = self.sourceModel()
        # Get the index for the first column (Name column) of the source row
        source_index = source_model.index(source_row, 0, source_parent_index)

        if not source_index.isValid():
            return False

        is_folder = source_model.data(source_index, IsFolderRole)
        parent_path = source_model.data(source_index, ParentPathRole)

        # Debugging output to help locate issues
        if self._sort_in_progress:
            item_name = source_model.data(source_index, Qt.DisplayRole)
            parent_str = str(parent_path) if parent_path else "ROOT"
            print(f"[FILTER DEBUG] During sort - checking item '{item_name}', parent: {parent_str}, is_folder: {is_folder}")

        # Never show folders in the list view - they belong in the folders section only
        if is_folder:
            return False

        # Strict filtering based on current folder path context
        if self._current_filter_folder_path is None: 
            # Root view - ONLY show templates with no specific parent (at root level)
            if parent_path == "ROOT" or parent_path is None:
                return True
            # Explicit reject for any template with a parent folder (in a subfolder)
            return False
        else: 
            # Specific folder view - ONLY show templates belonging directly to this folder
            if parent_path == self._current_filter_folder_path:
                return True
            # Explicit reject for any other template
            return False

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
    DEFAULT_ICON_PATH = os.path.join("app", "assets", "icons", "templates", "template_structure_icon.svg")
    WARNING_ICON_PATH = "ICONS/alert-triangle.svg" # Path for the warning icon
    DEFAULT_ICON_SIZE = QSize(18, 18) # Define a default icon size

    def __init__(self, parent=None, template_manager=None, app=None):
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
        
        # Track last mouse press for multi-selection
        self._last_mouse_press_pos = QPoint()
        self._is_cmd_ctrl_pressed = False

    def _load_icons(self):
        """Load icons used in the table view."""
        try:
            self.default_icon = QIcon(self.DEFAULT_ICON_PATH)
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

        for template_or_folder_data in templates_data:
            row_items = [QStandardItem() for _ in self.COLUMN_HEADERS] # Create items for all columns
            
            name = template_or_folder_data.get('name', 'Unknown') # Ensure name exists
            name_item = QStandardItem(name)
            # Store name data for display and editing (if applicable)
            name_item.setData(name, Qt.DisplayRole)
            name_item.setData(name, Qt.EditRole)
            
            is_folder_item = template_or_folder_data.get('is_folder', False)
            parent_folder_path = template_or_folder_data.get('parent_folder', None) # None implies root for templates

            name_item.setData(is_folder_item, IsFolderRole)
            name_item.setData(parent_folder_path, ParentPathRole)
            
            row_items[col_map.get('name', 0)] = name_item
            
            if is_folder_item:
                # Folder specific setup
                name_item.setIcon(QApplication.style().standardIcon(QStyle.SP_DirIcon)) # Standard folder icon
                name_item.setData(False, WarningRole) # Folders don't have warning state like templates
                name_item.setToolTip(f"Folder: {name}")
                # Folders typically don't have category, created, modified in this context
                # You might want to set empty strings or specific placeholders if columns must be filled
                for header, col_idx in col_map.items():
                    if header != 'name' and row_items[col_idx].text() == "": # Only if not already set
                        # Set placeholder or leave empty for folders for non-name columns
                        # For now, let's ensure they are QStandardItem instances
                        if not isinstance(row_items[col_idx], QStandardItem):
                            row_items[col_idx] = QStandardItem("")
                        # Optionally, set empty display/edit roles if needed for consistency
                        row_items[col_idx].setData("", Qt.DisplayRole)
                        row_items[col_idx].setData("", Qt.EditRole)
            else:
                # Template specific setup (existing logic)
                # --- Set Icon based on structure presence --- Corrected Logic ---
                has_structure = bool(template_or_folder_data.get('structure'))
                if not has_structure:
                    name_item.setData(True, WarningRole) # Set the warning flag
                    name_item.setToolTip("This template has no folder structure defined.")
                else:
                    name_item.setIcon(self.default_icon) # Explicitly set default icon here
                    name_item.setData(False, WarningRole) # Explicitly clear warning flag
                    name_item.setToolTip(f"Template: {name}") 
                # ---------------------------------------------------------------
                
                # --- Set Data for Other Columns (for templates) ---
                for header, col_index in col_map.items():
                    if header == 'name': # Already handled
                        continue 
                        
                    raw_value = template_or_folder_data.get(header)
                    # Ensure item for this column exists, if not already the name_item itself
                    if col_index < len(row_items) and isinstance(row_items[col_index], QStandardItem):
                        item = row_items[col_index]
                    else:
                        item = QStandardItem()
                        if col_index < len(row_items): 
                           row_items[col_index] = item
                        else: # Should not happen if row_items initialized correctly
                           print(f"Warning: Column index {col_index} out of bounds for {name}")
                           continue

                    if raw_value is not None:
                        if header in ['created', 'modified']:
                            try:
                                timestamp = float(raw_value)
                                item.setData(timestamp, Qt.EditRole) 
                                display_str = self._format_timestamp(timestamp)
                                item.setData(display_str, Qt.DisplayRole)
                            except (ValueError, TypeError):
                                item.setData(str(raw_value), Qt.DisplayRole) 
                                item.setData(str(raw_value), Qt.EditRole)
                        else:
                            item.setData(str(raw_value), Qt.DisplayRole)
                            item.setData(str(raw_value), Qt.EditRole)
                    # If raw_value is None, item remains empty (default QStandardItem)
            
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
            return Qt.IgnoreAction

        template_names = []
        model = self.model()
        if not model:
            print("[ERROR] startDrag: No model assigned to TableView via self.model()")
            return Qt.IgnoreAction
        
        # Save the current selection state before dragging
        primary_template = None
        multi_selected_templates = []
        gallery = self.parent()
        while gallery is not None:
            if hasattr(gallery, 'selection_manager') and hasattr(gallery, 'template_manager'):
                break
            gallery = gallery.parent()
            
        if gallery and hasattr(gallery, 'selection_manager'):
            print(f"[DEBUG] Table drag: Found gallery with selection_manager")
            # Store selection state before drag
            primary_template = gallery.selection_manager.selected_template
            multi_selected_templates = list(gallery.selection_manager.multi_selected_templates)
            print(f"[DEBUG] Table drag: Saved selection state - Primary: {primary_template.get('name') if primary_template else 'None'}, Multi count: {len(multi_selected_templates)}")
            
            # Use templates from selection manager for multi-selection
            if multi_selected_templates and len(multi_selected_templates) > 0:
                templates_to_drag = multi_selected_templates
                print(f"[DEBUG] Using {len(templates_to_drag)} templates from selection manager for drag")
            else:
                # Fallback to getting templates from the table selection if no multi-selection
                templates_to_drag = []
                for index in selected_indexes:
                    # Get data directly from the model's DisplayRole (proxy should handle this)
                    name = model.data(index, Qt.DisplayRole)
                    if name:
                        # Get full template data from template manager if available
                        if hasattr(gallery, 'template_manager') and gallery.template_manager:
                            template_data = gallery.template_manager.get_template_by_name(name)
                            if template_data:
                                templates_to_drag.append(template_data)
                            else:
                                # Fallback to simple dict if template not found in manager
                                templates_to_drag.append({'name': name})
                        else:
                            # No template manager, use simple dict
                            templates_to_drag.append({'name': name})
                    else:
                        # Use the proxy index row for warning
                        print(f"[WARNING] startDrag: Could not get template name for proxy row {index.row()}")
        else:
            # No selection manager found, fallback to simple template list from selection
            templates_to_drag = []
            for index in selected_indexes:
                # Get data directly from the model's DisplayRole (proxy should handle this)
                name = model.data(index, Qt.DisplayRole)
                if name:
                    # Create a simple template dict for consistency with TemplateCard drag
                    template_dict = {'name': name}
                    templates_to_drag.append(template_dict)
                else:
                    # Use the proxy index row for warning
                    print(f"[WARNING] startDrag: Could not get template name for proxy row {index.row()}")

        if not templates_to_drag:
            print("[WARNING] startDrag: No template names found for selected rows.")
            return Qt.IgnoreAction

        drag = QDrag(self)
        mime_data = QMimeData()
        
        # Use helper to setup mime data consistently
        template_names = setup_drag_mime_data(templates_to_drag, mime_data)
        drag.setMimeData(mime_data)
        
        # Create custom drag pixmap with count indicator for multi-selection
        item_count = len(template_names)
        
        # Create a representative pixmap for the drag (a colored rectangle with text)
        base_pixmap = QPixmap(200, 40)
        base_pixmap.fill(QColor(colors.get('card_bg', '#252526')))
        
        # Add text showing first template name
        painter = QPainter(base_pixmap)
        painter.setPen(QColor(colors.get('text', '#FFFFFF')))
        painter.setFont(QFont("Arial", 10))
        
        # Show first template name, possibly truncated
        display_text = template_names[0]
        if len(display_text) > 20:
            display_text = display_text[:18] + "..."
            
        # Position text with padding
        painter.drawText(10, 25, display_text)
        painter.end()
        
        # Use helper to create final drag pixmap with count
        drag_pixmap = create_drag_pixmap(self, source_pixmap=base_pixmap, item_count=item_count)
        drag.setPixmap(drag_pixmap)
        drag.setHotSpot(QPoint(10, 20))  # Set hotspot in a sensible position
        
        print(f"[DEBUG] Starting drag for {item_count} templates")
        
        # Block selection change signals during drag to prevent clearing selection
        selection_model = self.selectionModel()
        if selection_model:
            selection_model.blockSignals(True)
            
        # Execute the drag
        action_performed = drag.exec_(supportedActions, Qt.CopyAction)  # Use CopyAction to prevent clearing selection
        
        final_result = action_performed

        # If the view is DragOnly, it should ideally only report CopyAction or IgnoreAction,
        # as it's not supposed to be the source of a move.
        if self.dragDropMode() == QAbstractItemView.DragOnly:
            if action_performed == Qt.MoveAction:
                # Even if a MoveAction was reported by drag.exec_,
                # a DragOnly source should report CopyAction,
                # as it implies the data was copied, not moved from the source.
                print(f"[INFO] DragOnly source: drag.exec_ returned MoveAction ({action_performed}). Overriding to CopyAction.")
                final_result = Qt.CopyAction
            elif not (action_performed == Qt.CopyAction or action_performed == Qt.IgnoreAction):
                # If it's not Ignore, and not Copy (and not Move, handled above),
                # then it's some other action like LinkAction.
                # For DragOnly, this is also unexpected. Default to Ignore.
                print(f"[INFO] DragOnly source: drag.exec_ returned unexpected action {action_performed} ({type(action_performed)}). Overriding to IgnoreAction.")
                final_result = Qt.IgnoreAction
        
        # Unblock selection signals
        if selection_model:
            selection_model.blockSignals(False)
            
        # Restore selection state if it was cleared during drag
        if gallery and hasattr(gallery, 'selection_manager'):
            current_primary = gallery.selection_manager.selected_template
            current_multi = gallery.selection_manager.multi_selected_templates
            
            if (not current_primary and primary_template) or (not current_multi and multi_selected_templates):
                print(f"[DEBUG] Table drag: Restoring selection state after drag")
                # Only restore if selection was actually cleared
                gallery.selection_manager.set_selection_state(primary_template, multi_selected_templates)
                
        # Finish the drag operation
        # print(f"[DEBUG] Table drag completed with result: {result}") # Original print
        print(f"[DEBUG] Table drag completed. Reported action: {final_result}, Actual action from exec: {action_performed}")

    def mousePressEvent(self, event):
        # Get the index at the click position
        index = self.indexAt(event.pos())
        
        # Handle right-click on blank area (no valid index)
        if event.button() == Qt.RightButton and not index.isValid():
            # Let the parent class handle non-table click events (like context menu)
            if hasattr(self, 'customContextMenuRequested'):
                self.customContextMenuRequested.emit(event.pos())
            return
        
        # For other cases, use the standard handler
        super().mousePressEvent(event)

    def get_icon_for_template(self, template_name):
        """Return QIcon for the template, using default if specific one not found."""
        # We might add template-specific icons later
        # For now, always use the default SVG structure icon
        
        # Use get_resource_path to find the default icon correctly
        resolved_icon_path = get_resource_path(self.DEFAULT_ICON_PATH)
        
        if os.path.exists(resolved_icon_path):
            return QIcon(resolved_icon_path)
        else:
            print(f"WARN: Default template icon not found at {resolved_icon_path}")
            return QIcon() # Return empty icon


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