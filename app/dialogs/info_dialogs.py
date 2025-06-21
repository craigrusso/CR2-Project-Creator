#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Dialog windows for displaying information and tutorials.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTabWidget, QWidget,
                           QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QDesktopServices, QFont

# Import from the same place as APP_NAME and APP_VERSION for consistency
from app.config.app_config import APP_NAME, APP_VERSION_NUMBER
from app.constants import APP_BUILD_NUMBER
from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE
from app.constants import get_resource_path

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
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title_label.setStyleSheet(f"color: {colors['text']};")
    layout.addWidget(title_label)
    
    # Version with build in parentheses
    version_label = QLabel(f"{APP_VERSION_NUMBER} <span style='color: {colors['secondary_text']}; font-size: 10px;'>(build {APP_BUILD_NUMBER})</span>")
    version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    version_label.setStyleSheet(f"color: {colors['text']};")
    layout.addWidget(version_label)
    
    # Copyright info
    copyright_label = QLabel("© 2023-present Craig P. Russo and CR2 Creative")
    copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    copyright_label.setStyleSheet(f"color: {colors['secondary_text']};")
    layout.addWidget(copyright_label)
    
    # Description
    description = QLabel(
        "Echelon is a professional project creation tool designed to "
        "streamline your workflow by creating consistent project structures and files "
        "from customizable templates."
    )
    description.setWordWrap(True)
    description.setAlignment(Qt.AlignmentFlag.AlignCenter)
    description.setStyleSheet(f"color: {colors['text']};")
    layout.addWidget(description)
    
    # Spacer
    layout.addStretch()
    
    # Close button
    close_button = QPushButton("Close")
    close_button.setStyleSheet(BUTTON_STYLE)
    close_button.clicked.connect(dialog.accept)
    layout.addWidget(close_button)
    
    dialog.exec()

def show_tutorial(app):
    """Show the comprehensive user guide dialog"""
    dialog = QDialog(app)
    dialog.setWindowTitle("Echelon User Guide")
    dialog.resize(800, 650)  # Larger for better readability
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(24, 24, 24, 24)
    layout.setSpacing(16)
    
    # Modern header with subtitle
    header_widget = QWidget()
    header_layout = QVBoxLayout(header_widget)
    header_layout.setContentsMargins(0, 0, 0, 0)
    header_layout.setSpacing(4)
    
    title_label = QLabel("Echelon User Guide")
    font = title_label.font()
    font.setBold(True)
    font.setPointSize(18)
    title_label.setFont(font)
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title_label.setStyleSheet(f"color: {colors['text']}; margin-bottom: 4px;")
    
    subtitle_label = QLabel("Complete reference for all features and advanced workflows")
    subtitle_font = subtitle_label.font()
    subtitle_font.setPointSize(11)
    subtitle_label.setFont(subtitle_font)
    subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    subtitle_label.setStyleSheet(f"color: {colors['secondary_text']}; margin-bottom: 16px;")
    
    header_layout.addWidget(title_label)
    header_layout.addWidget(subtitle_label)
    layout.addWidget(header_widget)
    
    # Add tabs with modern, comprehensive content
    tabs = {
        "Quick Start": f"""
<h3>Get Started in 5 Minutes</h3>
<p>New to Echelon? This quick overview will have you creating projects in minutes.</p>

<h4>Watch the Welcome Tutorial</h4>
<p>First time here? Go to <strong>Help > Show Welcome Tutorial</strong> for a visual walkthrough of the core workflow.</p>

<h4>The 4-Step Workflow</h4>
<ol>
    <li><strong>Build Template:</strong> Start with example templates or create your own structure</li>
    <li><strong>Smart Naming:</strong> Right-click files → Select "Use Project Name" for automatic renaming</li>
    <li><strong>Enter Names:</strong> Type your project name(s) in the left panel</li>
    <li><strong>Create:</strong> Select template + Click "Create Project(s)" = Done!</li>
</ol>

<h4>Example Templates</h4>
<p>Echelon includes built-in example templates to get you started:</p>
<ul>
    <li><strong>Web Development:</strong> HTML, CSS, JavaScript project structure</li>
    <li><strong>Video Production:</strong> Organized folders for footage, audio, exports</li>
    <li><strong>Design Projects:</strong> Assets, mockups, and deliverables structure</li>
    <li><strong>Music Production:</strong> Tracks, samples, and project organization</li>
    <li><strong>General Projects:</strong> Basic folder structures for any workflow</li>
</ul>

<h4>Customizing Your Environment</h4>
<ul>
    <li><strong>Hide Examples:</strong> Go to <strong>Edit > Preferences > Templates</strong> and uncheck "Show example templates" to clean up your gallery</li>
    <li><strong>Categories:</strong> Organize templates into custom categories for better workflow</li>
    <li><strong>Start Simple:</strong> Begin with example templates, then customize or create your own</li>
</ul>

<h4>Next Steps</h4>
<p>Once you understand the basics, explore the other tabs to learn about:</p>
<ul>
    <li><strong>Template Building:</strong> Create custom templates from scratch</li>
    <li><strong>Smart Naming:</strong> Automatic file renaming with variables</li>
    <li><strong>Batch Creation:</strong> Generate multiple projects at once</li>
</ul>
""",
        "Templates": f"""
<h3>Build Intelligent Templates</h3>
<p>Create reusable project blueprints with automatic file naming and advanced customization.</p>

<h4>Template Gallery Navigation</h4>
<ul>
    <li><strong>Grid/List View:</strong> Toggle between visual cards and detailed list views</li>
    <li><strong>Search & Filter:</strong> Find templates by name, description, category, or tags</li>
    <li><strong>Categories:</strong> Organize templates into logical groups (Web, Video, Design, etc.)</li>
    <li><strong>Folders:</strong> Create custom folders and drag templates to organize your workflow</li>
</ul>

<h4>Template Actions</h4>
<ul>
    <li><strong>Single-Click:</strong> Select template for project creation</li>
    <li><strong>Double-Click:</strong> Open template editor for modifications</li>
    <li><strong>Right-Click Menu:</strong>
        <ul>
            <li><strong>Edit:</strong> Modify template structure and settings</li>
            <li><strong>Duplicate:</strong> Create a copy for customization</li>
            <li><strong>Delete:</strong> Permanently remove template</li>
        </ul>
    </li>
</ul>

<h4>Creating New Templates</h4>
<ol>
    <li><strong>Start:</strong> Click "Add Template" or <strong>File > New Template...</strong></li>
    <li><strong>Details:</strong> Enter name, category, description, and optional tags</li>
    <li><strong>Structure:</strong> Switch to Structure tab and build your project layout</li>
    <li><strong>Build Methods:</strong>
        <ul>
            <li><strong>Drag & Drop:</strong> Pull files/folders from your computer</li>
            <li><strong>Manual Creation:</strong> Use "Add Folder" and "Add File" buttons</li>
            <li><strong>Source Files:</strong> Link actual files to be copied into projects</li>
        </ul>
    </li>
</ol>

<h4>Smart Naming System</h4>
<p>Make your files automatically rename themselves when creating projects:</p>

<h5>Basic Smart Naming</h5>
<ul>
    <li><strong>Right-click any file</strong> in your template structure</li>
    <li><strong>Select "Use Project Name"</strong> - file will auto-rename with project name</li>
    <li><strong>Example:</strong> <code>Template_README.md</code> → <code>MyProject_README.md</code></li>
</ul>

<h5>Advanced Custom Patterns</h5>
<p>For power users, select <strong>"Custom Naming Patterns"</strong> to access variables:</p>
<ul>
    <li><strong>${{PROJECT_NAME}}:</strong> Inserts the project name</li>
    <li><strong>${{DATE}}:</strong> Adds current date in various formats</li>
    <li><strong>${{SEQUENCE}}:</strong> Sequential numbering for batch projects</li>
    <li><strong>${{CUSTOM}}:</strong> User-defined variables for complex workflows</li>
</ul>

<h5>Pattern Examples</h5>
<pre><code># Basic patterns
${{PROJECT_NAME}}_Script.docx
${{PROJECT_NAME}}_v01.prproj

# Date patterns  
${{PROJECT_NAME}}_${{DATE:YYYY-MM-DD}}.txt
Meeting_Notes_${{DATE:MM-DD-YYYY}}.docx

# Advanced combinations
${{PROJECT_NAME}}_Draft_${{SEQUENCE:001}}_${{DATE:YYYYMMDD}}.pdf</code></pre>

<h4>Template Management</h4>
<h5>Import/Export</h5>
<ul>
    <li><strong>Import:</strong> <code>File > Import Template...</code> - Load .zip template packages</li>
    <li><strong>Export Single:</strong> Right-click template → Export for sharing</li>
    <li><strong>Export All:</strong> <code>File > Export > All Settings...</code> - Complete backup</li>
</ul>

<h5>File Caching</h5>
<ul>
    <li><strong>Automatic:</strong> Source files are cached for faster project creation</li>
    <li><strong>Efficient:</strong> Templates work without accessing original file locations</li>
    <li><strong>Settings:</strong> Manage cache in <code>Edit > Preferences > Cache</code></li>
</ul>

<h4>Team Collaboration</h4>
<ul>
    <li><strong>Shared Storage:</strong> <code>Edit > Preferences > Storage</code> - Set network location</li>
    <li><strong>Template Sharing:</strong> Export/import workflows for team consistency</li>
    <li><strong>Version Control:</strong> Use template descriptions to track changes</li>
</ul>
""",
        "Project Creation": f"""
<h3>Master Project Creation</h3>
<p>Transform your templates into organized project structures with powerful automation features.</p>

<h4>Basic Project Creation</h4>
<ol>
    <li><strong>Select Template:</strong> Click any template in the gallery (right side) - it will highlight when selected</li>
    <li><strong>Enter Project Name:</strong> Type your project name in the left panel text box</li>
    <li><strong>Choose Location:</strong> Click "Browse..." to select where projects will be created</li>
    <li><strong>Create:</strong> Hit "Create Project(s)" and watch the magic happen!</li>
</ol>

<h4>Batch Project Creation</h4>
<p>Create multiple projects simultaneously with these input methods:</p>
<ul>
    <li><strong>Line Breaks:</strong> One project per line</li>
    <li><strong>Commas:</strong> <code>Project A, Project B, Project C</code></li>
    <li><strong>Semicolons:</strong> <code>Video 1; Video 2; Video 3</code></li>
    <li><strong>Mixed:</strong> Combine any separators as needed</li>
</ul>
<p><strong>Example batch input:</strong></p>
<pre><code>Marketing Campaign 2024
Social Media Video
Product Demo, Tutorial Series
Brand Guidelines; Style Guide</code></pre>
<p><em>This creates 6 separate projects automatically!</em></p>

<h4>⚙️ Sequence Variations (Power Feature)</h4>
<p>Check <strong>"Create sequence variations"</strong> to automatically generate multiple project versions:</p>

<h5>Date Sequences</h5>
<ul>
    <li><strong>Daily:</strong> <code>MyProject_2024-01-01, MyProject_2024-01-02...</code></li>
    <li><strong>Weekly:</strong> <code>MyProject_2024-01-01, MyProject_2024-01-08...</code></li>
    <li><strong>Monthly:</strong> <code>MyProject_2024-01-01, MyProject_2024-02-01...</code></li>
    <li><strong>Custom Formats:</strong> YYYY-MM-DD, YYYYMMDD, MM/DD/YYYY, and more</li>
</ul>

<h5>Version Numbers</h5>
<ul>
    <li><strong>Standard:</strong> <code>MyProject_V01, MyProject_V02, MyProject_V03...</code></li>
    <li><strong>Formats:</strong> V1/v1, Ver1, Version1 - choose your style</li>
    <li><strong>Prefix/Suffix:</strong> Put versions before or after project names</li>
</ul>

<h5>Sequential Numbers</h5>
<ul>
    <li><strong>Basic:</strong> <code>MyProject_001, MyProject_002, MyProject_003...</code></li>
    <li><strong>Padding:</strong> 1-digit, 2-digit, or 3-digit formatting</li>
    <li><strong>Custom Start:</strong> Begin numbering from any value</li>
</ul>

<h4>Project Creation Results</h4>
<p>After creation, Echelon shows you:</p>
<ul>
    <li><strong>Success Count:</strong> How many projects were created successfully</li>
    <li><strong>Detailed Report:</strong> Individual results for each project</li>
    <li><strong>Error Handling:</strong> Clear messages for any issues encountered</li>
    <li><strong>File Locations:</strong> Direct links to your new project folders</li>
</ul>

<h4>Recent Projects & Templates</h4>
<ul>
    <li><strong>File > Recent Projects:</strong> Quick access to recently created project folders</li>
    <li><strong>File > Recent Templates:</strong> Jump back to templates you've used</li>
    <li><strong>Smart Suggestions:</strong> Echelon remembers your workflow patterns</li>
</ul>
""",
        "Advanced": f"""
<h3>Pro Tips & Problem Solving</h3>
<p>Master advanced workflows and resolve common issues like a power user.</p>

<h4>Power User Workflows</h4>

<h5>Productivity Shortcuts</h5>
<ul>
    <li><strong>Keyboard Navigation:</strong> Use arrow keys in template gallery, Enter to select</li>
    <li><strong>Quick Duplicate:</strong> Right-click template → Duplicate for rapid variations</li>
    <li><strong>Batch Naming:</strong> Use Excel/Sheets to generate project name lists, then copy-paste</li>
    <li><strong>Template Favorites:</strong> Drag frequently used templates to Favorites folder</li>
</ul>

<h5>Advanced Project Organization</h5>
<ul>
    <li><strong>Nested Structures:</strong> Create deep folder hierarchies for complex projects</li>
    <li><strong>Conditional Files:</strong> Use multiple templates for different project phases</li>
    <li><strong>Version Templates:</strong> Create separate templates for Draft/Review/Final versions</li>
    <li><strong>Client Workflows:</strong> Build client-specific templates with branded assets</li>
</ul>

<h4>Common Issues & Solutions</h4>

<h5>Template Problems</h5>
<ul>
    <li><strong>Template Won't Save:</strong> Check file permissions, ensure template name is unique</li>
    <li><strong>Missing Source Files:</strong> Re-link files in template editor, check file paths</li>
    <li><strong>Structure Not Updating:</strong> Refresh template gallery, restart Echelon if needed</li>
    <li><strong>Categories Missing:</strong> Use "Manage Categories" to restore or recreate</li>
</ul>

<h5>Project Creation Failures</h5>
<ul>
    <li><strong>Permission Denied:</strong> Check output directory write permissions</li>
    <li><strong>Disk Space:</strong> Ensure sufficient storage for all projects</li>
    <li><strong>Path Too Long:</strong> Shorten project names or choose shorter output paths</li>
    <li><strong>Special Characters:</strong> Avoid <code>\\/:*?"<>|</code> in project names</li>
</ul>

<h5>Performance Issues</h5>
<ul>
    <li><strong>Slow Template Loading:</strong> Clear cache in Preferences > Cache</li>
    <li><strong>Large File Handling:</strong> Consider using file links instead of embedded files</li>
    <li><strong>Memory Usage:</strong> Close unused template editors, restart app periodically</li>
</ul>

<h4>Data Management & Backup</h4>

<h5>Backup Strategies</h5>
<ul>
    <li><strong>Regular Exports:</strong> Weekly exports of all templates and settings</li>
    <li><strong>Version Control:</strong> Keep dated backups of important templates</li>
    <li><strong>Cloud Storage:</strong> Store exports in Dropbox, Google Drive, or OneDrive</li>
    <li><strong>Team Sync:</strong> Share template packages with team members regularly</li>
</ul>

<h5>Migration & Updates</h5>
<ul>
    <li><strong>New Computer:</strong> Export all settings, install Echelon, import settings</li>
    <li><strong>App Updates:</strong> Templates are preserved, but export before major updates</li>
    <li><strong>Shared Drives:</strong> Test network permissions before switching storage locations</li>
</ul>

<h4>Optimization Tips</h4>

<h5>Speed Improvements</h5>
<ul>
    <li><strong>Template Design:</strong> Avoid excessive nesting, keep structures reasonable</li>
    <li><strong>File Sizes:</strong> Use smaller source files when possible</li>
    <li><strong>Batch Limits:</strong> Create 50 projects or fewer in single batch operations</li>
    <li><strong>Cache Maintenance:</strong> Periodically clear cache to free disk space</li>
</ul>

<h5>User Experience</h5>
<ul>
    <li><strong>Descriptive Names:</strong> Use clear, searchable template names and descriptions</li>
    <li><strong>Consistent Categories:</strong> Establish category naming conventions</li>
    <li><strong>Tag Everything:</strong> Add relevant tags for better searchability</li>
    <li><strong>Regular Cleanup:</strong> Archive or delete unused templates periodically</li>
</ul>

<h4>Getting Help</h4>
<ul>
    <li><strong>Welcome Tutorial:</strong> <code>Help > Show Welcome Tutorial</code> - Visual walkthrough</li>
    <li><strong>This Guide:</strong> <code>Help > Tutorial</code> - Comprehensive reference</li>
    <li><strong>Reset Tutorials:</strong> <code>Help > Reset Tutorials</code> - Start fresh</li>
    <li><strong>Check Updates:</strong> <code>Help > Check for Updates</code> - Latest features</li>
    <li><strong>About Info:</strong> <code>Help > About Echelon</code> - Version and system info</li>
</ul>

<h4>Learning Resources</h4>
<ul>
    <li><strong>Start Simple:</strong> Begin with basic templates, add complexity gradually</li>
    <li><strong>Experiment:</strong> Test templates with sample projects before important work</li>
    <li><strong>Community:</strong> Share templates with colleagues, learn from their approaches</li>
    <li><strong>Documentation:</strong> Keep notes on your template designs and naming conventions</li>
</ul>
""",
    }

    # Create modern tab widget with enhanced styling
    tab_widget = QTabWidget()
    tab_widget.setStyleSheet(f"""
        QTabWidget::pane {{
            border: 1px solid {colors['border']};
            background-color: {colors['card_bg']};
            border-radius: 8px;
            margin-top: 8px;
        }}
        QTabBar::tab {{
            background-color: {colors['bg']};
            color: {colors['text']};
            padding: 12px 20px;
            border: 1px solid {colors['border']};
            border-bottom: none;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            margin-right: 2px;
            font-weight: 500;
            min-width: 120px;
        }}
        QTabBar::tab:selected {{
            background-color: {colors['card_bg']};
            border-bottom: none;
            border-top: 3px solid {colors['accent']};
            color: white;
            font-weight: 600;
        }}
        QTabBar::tab:!selected {{
            margin-top: 4px;
            color: {colors['secondary_text']};
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {colors['hover_bg']};
            color: {colors['text']};
        }}
    """)

    for tab_name, tutorial_text in tabs.items():
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        
        # Create modern scroll area with enhanced styling
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{ 
                border: none; 
                background-color: transparent;
                border-radius: 6px;
            }}
        """)
        
        # Enhanced scrollbar styling
        scroll_area.verticalScrollBar().setStyleSheet(f"""
            QScrollBar:vertical {{
                border: none;
                background: {colors['card_bg']};
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {colors['secondary_text']};
                min-height: 24px;
                border-radius: 6px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {colors['text']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

        # Content container with enhanced styling
        scroll_content_widget = QWidget()
        scroll_content_layout = QVBoxLayout(scroll_content_widget)
        scroll_content_layout.setContentsMargins(24, 20, 24, 20)
        scroll_content_layout.setSpacing(12)
        
        # Enhanced content label with better typography
        content = QLabel(tutorial_text)
        content.setTextFormat(Qt.TextFormat.RichText)
        content.setWordWrap(True)
        content.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        content.setStyleSheet(f"""
            QLabel {{
                color: {colors['text']};
                line-height: 1.6;
                font-size: 16px;
            }}
            a {{ 
                color: {colors['accent']}; 
                text-decoration: none;
            }}
            a:hover {{ 
                text-decoration: underline; 
            }}
            h3 {{ 
                color: {colors['text']};
                font-size: 24px;
                font-weight: 600;
                margin: 0 0 16px 0;
                padding-bottom: 8px;
                border-bottom: 2px solid {colors['accent']};
            }}
            h4 {{ 
                color: {colors['text']};
                font-size: 20px;
                font-weight: 600;
                margin: 24px 0 8px 0;
            }}
            h5 {{ 
                color: {colors['accent']};
                font-size: 18px;
                font-weight: 600;
                margin: 16px 0 6px 0;
            }}
            p {{ 
                margin: 0 0 12px 0; 
                line-height: 1.6;
                font-weight: 400;
            }}
            ul, ol {{ 
                margin: 0 0 16px 0;
                padding-left: 20px;
            }}
            li {{ 
                margin-bottom: 8px;
                line-height: 1.6;
                font-weight: 400;
            }}
            ul ul, ol ol {{
                margin: 8px 0 8px 0;
                padding-left: 16px;
            }}
            strong {{
                font-weight: 600;
                color: {colors['text']};
            }}
            em {{
                font-style: italic;
                color: {colors['text']};
            }}
            code {{ 
                background-color: {colors['bg']};
                border: 1px solid {colors['border']};
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
                font-size: 13px;
                color: {colors['accent']};
            }}
            pre {{
                background-color: {colors['bg']};
                border: 1px solid {colors['border']};
                border-radius: 6px;
                padding: 16px;
                margin: 16px 0;
                overflow-x: auto;
            }}
            pre code {{
                background: none;
                border: none;
                padding: 0;
                display: block;
                color: {colors['text']};
            }}
        """)
        content.setOpenExternalLinks(True)
        scroll_content_layout.addWidget(content)
        scroll_content_layout.addStretch(1)
        
        scroll_area.setWidget(scroll_content_widget)
        tab_layout.addWidget(scroll_area)

        tab_widget.addTab(tab, tab_name)
            
    layout.addWidget(tab_widget)
    
    # Modern footer with close button
    footer_widget = QWidget()
    footer_layout = QHBoxLayout(footer_widget)
    footer_layout.setContentsMargins(0, 16, 0, 0)
    
    footer_layout.addStretch()
    
    close_button = QPushButton("✕ Close Guide")
    close_button.setFixedSize(140, 40)
    close_button.setCursor(Qt.CursorShape.PointingHandCursor)
    close_button.setStyleSheet(f"""
        QPushButton {{
            background-color: {colors['accent']};
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            padding: 0px 16px;
        }}
        QPushButton:hover {{
            background-color: {colors['accent_hover']};
            transform: translateY(-1px);
        }}
        QPushButton:pressed {{
            background-color: {colors['accent']};
            transform: translateY(0px);
        }}
    """)
    close_button.clicked.connect(dialog.accept)
    footer_layout.addWidget(close_button)
    
    footer_layout.addStretch()
    layout.addWidget(footer_widget)
    
    dialog.exec()
