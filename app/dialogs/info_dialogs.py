#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Dialog windows for displaying information and tutorials.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTabWidget, QWidget,
                           QScrollArea)
from PyQt5.QtCore import Qt

# Import from the same place as APP_NAME and APP_VERSION for consistency
from app.config.app_config import APP_NAME, APP_VERSION
# Define a fallback build number in case import fails
APP_BUILD_NUMBER = "250"
try:
    # Try to import from constants if available
    from app.constants import APP_BUILD_NUMBER
except ImportError:
    try:
        # Try alternative location if first import fails
        from app.config.constants import APP_BUILD_NUMBER
    except ImportError:
        # Keep the fallback value if both imports fail
        pass

from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE

def show_about(app):
    """Show the about dialog"""
    dialog = QDialog(app)
    dialog.setWindowTitle("About")
    dialog.resize(450, 320)
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(10)
    
    # App name and version with build number
    title_label = QLabel(f"{APP_NAME}")
    font = title_label.font()
    font.setBold(True)
    font.setPointSize(16)
    title_label.setFont(font)
    title_label.setAlignment(Qt.AlignCenter)
    title_label.setStyleSheet(f"color: {colors['text']};")
    layout.addWidget(title_label)
    
    # Version with build in parentheses
    version_label = QLabel(f"{APP_VERSION} <span style='color: {colors['secondary_text']}; font-size: 10px;'>(build {APP_BUILD_NUMBER})</span>")
    version_label.setAlignment(Qt.AlignCenter)
    version_label.setStyleSheet(f"color: {colors['text']};")
    layout.addWidget(version_label)
    
    # Copyright info
    copyright_label = QLabel("© 2023-present Craig P. Russo and CR2 Creative")
    copyright_label.setAlignment(Qt.AlignCenter)
    copyright_label.setStyleSheet(f"color: {colors['secondary_text']};")
    layout.addWidget(copyright_label)
    
    # Description
    description = QLabel(
        "Echelon is a professional project creation tool designed to "
        "streamline your workflow by creating consistent project structures and files "
        "from customizable templates."
    )
    description.setWordWrap(True)
    description.setAlignment(Qt.AlignCenter)
    description.setStyleSheet(f"color: {colors['text']};")
    layout.addWidget(description)
    
    # Spacer
    layout.addStretch()
    
    # Close button
    close_button = QPushButton("Close")
    close_button.setStyleSheet(BUTTON_STYLE)
    close_button.clicked.connect(dialog.accept)
    layout.addWidget(close_button)
    
    dialog.exec_()

def show_tutorial(app):
    """Show the tutorial dialog"""
    dialog = QDialog(app)
    dialog.setWindowTitle("Tutorial")
    dialog.resize(600, 500)
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(10)
    
    # Title
    title_label = QLabel("Getting Started with Echelon")
    font = title_label.font()
    font.setBold(True)
    font.setPointSize(14)
    title_label.setFont(font)
    title_label.setAlignment(Qt.AlignCenter)
    title_label.setStyleSheet(f"color: {colors['text']};")
    layout.addWidget(title_label)
    
    # Add tabs
    tabs = {
        "Templates": f"""
<h3>Understanding the Template Gallery</h3>
<p>The <b>Template Gallery</b> (the main area on the right) is your central hub for managing and selecting project templates.</p>

<h4>Browsing & Searching:</h4>
<ul>
    <li>Scroll through the available templates using the Grid or List view (toggle buttons at the top right of the Templates section).</li>
    <li>Use the <b>Search box</b> at the top right to filter templates by name, description, or tags.</li>
</ul>

<h4>Template Items (Cards/List):</h4>
<p>Each item represents a template and shows:</p>
<ul>
    <li><b>Icon & Name:</b> Quick identification.</li>
    <li><b>Category:</b> Helps organize templates. Categories are assigned when creating or editing a template (see Customization tab) and are managed via the 'Manage' button in the Edit Template dialog.</li>
    <li><b>Description:</b> A brief overview of the template's purpose.</li>
    <li><b>Hover Effect:</b> Hovering over an item may change its background color slightly.</li>
    <li><b>Actions (via Right-Click):</b> Right-click on a template item to access actions like:
        <ul>
            <li><b>Edit (✏️):</b> Allows you to modify the template's name, description, category, and structure. (Same as double-clicking).</li>
            <li><b>Duplicate (❐):</b> Creates a copy of the template, prompting you for a new name.</li>
            <li><b>Delete (🗑️):** Permanently removes the template. Use with caution!</li>
        </ul>
    </li>
</ul>

<h4>Selecting & Editing/Previewing a Template:</h4>
<ul>
    <li><b>Single-Click</b> on a template item to select it for project creation. The selected item will be highlighted.</li>
    <li><b>Double-Click</b> on a template item (or Right-Click > Edit) to open the <b>Template Editor</b> window. This window allows you to:
        <ul>
            <li>Modify the template's details (Name, Category, Description).</li>
            <li>Preview and modify the folder/file <b>Structure</b> that the template will create.</li>
        </ul>
    </li>
</ul>

<h4>Folders:</h4>
<ul>
    <li>The <b>Folders list</b> (above the templates) helps you organize templates. Click a folder to view its templates.</li>
    <li><b>Favorites:</b> A default folder. Drag templates from the gallery into this folder icon for quick access.</li>
    <li><b>Custom Folders:</b> Use the <b>New Folder</b> button to create folders. Right-click a folder icon to rename or delete it.</li>
    <li><b>Assigning:</b> Drag a template from the gallery onto a folder icon to assign it. A template can only be in one folder at a time.</li>
</ul>

<h4>Sharing & Backup:</h4>
<ul>
    <li><b>Export/Import:</b> Use the <b>File > Import Template...</b> and <b>File > Export > ...</b> menus to save (export) or load (import) templates as <code>.zip</code> files. This is the primary way to share templates between users or back up your custom templates.</li>
    <li><b>Shared Data Location:</b> For teams or multiple computers, you can configure Echelon to use a shared network drive for its data. Go to <b>Edit > Preferences > Storage</b> and click <b>Change...</b> to select a new Data Root Directory. All templates, settings, and cache will be stored there. <i>Note: Ensure all users have read/write permissions to the chosen shared location. A restart is required after changing the path.</i></li>
</ul>

<h4>Caching Explained:</h4>
<ul>
    <li>When you add a source file (like a <code>.prproj</code> or <code>.aep</code> file) to a template's structure, Echelon copies it to a hidden internal cache.</li>
    <li>When you create a project, Echelon uses the cached copy. This makes project creation faster and means the template doesn't need access to the original file location later.</li>
    <li>Cache settings can be managed under <b>Edit > Preferences > Cache</b>.</li>
</ul>
""",
        "Project Creation": f"""<h3>Creating Projects</h3>
<p>Creating projects is the core function of Echelon.</p>

<h4>1. Select a Template:</h4>
<ul>
    <li>Click on a template item in the <b>Template Gallery</b> (right side) that matches the structure you need. The selected template will be highlighted.</li>
</ul>

<h4>2. Enter Project Names:</h4>
<ul>
    <li>In the <b>Project Settings</b> panel (left side), use the large text box under "Enter Project Names".</li>
    <li><b>Single Project:</b> Type the desired name for your project (e.g., <code>My Awesome Video</code>).</li>
    <li><b>Multiple Projects (Batch):</b> Enter one project name per line. You can also separate names with commas (<code>,</code>) or semicolons (<code>;</code>). Echelon will automatically parse these into individual projects.<br>
        <i>Example:</i>
        <pre><code>Episode 101
Episode 102, Episode 103
Marketing Video; Promo Spot</code></pre>
        This will create 5 projects.
    </li>
</ul>

<h4>3. Choose Output Directory:</h4>
<ul>
    <li>Click the <b>Browse...</b> button below the project name input area.</li>
    <li>Navigate to the main folder where you want your project folder(s) to be created.</li>
    <li>Echelon will create a subfolder for <i>each</i> project name you entered inside this chosen directory.<br>
        <i>Example:</i> If you chose <code>/Users/You/Documents/Projects</code> as the output directory and entered <code>My Awesome Video</code> as the project name, the final structure will be created inside <code>/Users/You/Documents/Projects/My Awesome Video/</code>.
    </li>
</ul>

<h4>4. Create!</h4>
<ul>
    <li>Click the <b>Create Project(s)</b> button at the bottom left.</li>
    <li>Echelon will generate the folder structure and any included files defined by the selected template for each project name entered.</li>
    <li>A progress bar and status messages will appear. For batch operations, a summary window will show the results upon completion.</li>
</ul>

<h4>Recent Projects/Templates:</h4>
<ul>
    <li>The <b>File > Recent Projects</b> and <b>File > Recent Templates</b> menus provide quick access to projects you've created or templates you've used recently.</li>
</ul>
""",
        "Customization": f"""<h3>Customizing Templates</h3>
<p>Echelon allows you to create and modify templates to perfectly fit your workflow.</p>

<h4>Creating a New Template:</h4>
<ol>
    <li>Go to <b>File > New Template...</b> or click the <b>Add Template</b> button in the main window.</li>
    <li>A dialog window will appear. Fill in:
        <ul>
            <li><b>Name:</b> A unique and descriptive name.</li>
            <li><b>Category:</b> Select from the dropdown or type a new one. Click <b>Manage</b> to add/edit/remove categories globally.</li>
            <li><b>Description:</b> Explain what the template is for.</li>
            <li><b>Tags (Optional):</b> Add keywords for searching.</li>
        </ul>
    </li>
    <li>Go to the <b>Structure</b> tab in the dialog.</li>
    <li><b>Define Structure:</b>
        <ul>
            <li>Use the <b>Add Folder</b> or <b>Add File</b> buttons below the tree view.</li>
            <li>Select an item in the tree and use the buttons or right-click menu to <b>Rename</b>, <b>Delete</b>, or add more items <i>inside</i> a selected folder.</li>
            <li>For <b>Files</b>, you can optionally specify a <b>Source File</b> by selecting the file in the tree and using the options that appear. If you select a source file (e.g., a <code>.txt</code> template, an empty <code>.aep</code> project file), that file will be <i>copied</i> into the project structure when the template is used (and stored in Echelon's cache). If left blank, an empty file placeholder is used.</li>
            <li>Use the <code>${{PROJECT_NAME}}</code> variable in file names (e.g., <code>${{PROJECT_NAME}}.prproj</code>) to have the project name automatically inserted when a project is created.</li>
        </ul>
    </li>
    <li>Click <b>Save Template</b>. It will now appear in your Template Gallery.</li>
</ol>

<h4>Editing an Existing Template:</h4>
<ol>
    <li>Find the template item in the <b>Template Gallery</b>.</li>
    <li>Right-click the item and select <b>Edit</b>.</li>
    <li>The same dialog used for creation appears, pre-filled with the template's current information and structure.</li>
    <li>Modify the details or structure as needed (including Category).</li>
    <li>Click <b>Save Template</b> to apply your changes.</li>
</ol>

<h4>Duplicating a Template:</h4>
<ul>
    <li>Right-click the template item you want to copy and select <b>Duplicate</b>. You'll be asked for a new name, and a copy will be created for you to edit.</li>
</ul>

<h4>Importing/Exporting Templates:</h4>
<ul>
    <li>Use <b>File > Import Template...</b> to load a template package (<code>.zip</code> file) shared by someone else or previously exported.</li>
    <li>Use <b>File > Export > All Settings and Templates...</b> to back up <i>all</i> your custom templates and application settings into a single <code>.zip</code> file.</li>
</ul>
"""
    }

    # Tutorial content - now uses the dictionary
    tab_widget = QTabWidget()
    # Apply stylesheet (consider moving this to a central theme/style function later)
    tab_widget.setStyleSheet(f"""
        QTabWidget::pane {{
            border: 1px solid {colors['border']};
            background-color: {colors['card_bg']};
        }}
        QTabBar::tab {{
            background-color: {colors['bg']};
            color: {colors['text']};
            padding: 8px 12px;
            border: 1px solid {colors['border']};
            border-bottom: none;
        }}
        QTabBar::tab:selected {{
            background-color: {colors['card_bg']};
            border-bottom: none; /* Reset bottom border */
            border-top: 2px solid {colors['accent']}; /* Add top accent */
        }}
        QTabBar::tab:!selected {{
             margin-top: 2px; /* Push non-selected tabs down slightly */
        }}
    """)

    for tab_name, tutorial_text in tabs.items():
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        
        # --- Add ScrollArea --- 
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }") # Style scroll area
        scroll_area.verticalScrollBar().setStyleSheet(f"""
            QScrollBar:vertical {{
                border: none;
                background: {colors['card_bg']};
                width: 10px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {colors['secondary_text']};
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }}
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

        # Container widget for the label to go inside the scroll area
        scroll_content_widget = QWidget()
        scroll_content_layout = QVBoxLayout(scroll_content_widget)
        scroll_content_layout.setContentsMargins(15, 15, 15, 15) # Margins inside scroll area
        scroll_content_layout.setSpacing(10) # Spacing for content
        
        # Use QLabel with RichText format for basic Markdown support
        content = QLabel(tutorial_text)
        content.setTextFormat(Qt.RichText) # Allow rich text like bold, lists
        content.setWordWrap(True)
        content.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        # Link color needs to be set explicitly for RichText
        content.setStyleSheet(f"""
            color: {colors['text']};
            a {{ color: {colors['accent']}; }}
            /* Add some basic styling for HTML elements */
            h3 {{ margin-bottom: 10px; }}
            h4 {{ margin-top: 15px; margin-bottom: 5px; }}
            p {{ margin-bottom: 10px; line-height: 150%; }}
            ul, ol {{ margin-left: 20px; margin-bottom: 10px; }}
            li {{ margin-bottom: 5px; }}
            code {{ 
                background-color: {colors['bg']};
                border: 1px solid {colors['border']};
                padding: 1px 4px;
                border-radius: 3px;
                font-family: monospace;
            }}
            pre code {{
                display: block;
                padding: 10px;
                margin: 10px 0;
            }}
        """)
        content.setOpenExternalLinks(True) # Allow opening http links
        scroll_content_layout.addWidget(content)
        scroll_content_layout.addStretch(1) # Add stretch to push content up
        
        scroll_area.setWidget(scroll_content_widget) # Put content widget in scroll area
        tab_layout.addWidget(scroll_area) # Add scroll area to the tab layout

        tab_widget.addTab(tab, tab_name)
            
    layout.addWidget(tab_widget)
    
    # Close button
    close_button = QPushButton("Close")
    close_button.setStyleSheet(BUTTON_STYLE)
    close_button.clicked.connect(dialog.accept)
    layout.addWidget(close_button)
    
    dialog.exec_()
