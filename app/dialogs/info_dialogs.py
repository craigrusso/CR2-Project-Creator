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
    
    title_label = QLabel("📚 Echelon User Guide")
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
        "🎯 Quick Start": f"""
<h3>🚀 Get Started in 5 Minutes</h3>
<p>New to Echelon? This quick overview will have you creating projects in minutes.</p>

<h4>🎬 Watch the Welcome Tutorial</h4>
<p>First time here? Go to <b>Help > Show Welcome Tutorial</b> for a visual walkthrough of the core workflow.</p>

<h4>⚡ The 4-Step Workflow</h4>
<ol>
    <li><b>📁 Create Template:</b> Click "Add Template" → Build your ideal project structure</li>
    <li><b>🏷️ Smart Naming:</b> Right-click files → Select "Use Project Name" for automatic renaming</li>
    <li><b>📝 Enter Names:</b> Type your project name(s) in the left panel</li>
    <li><b>🎉 Create:</b> Select template + Click "Create Project(s)" = Done!</li>
</ol>

<h4>💡 Pro Tips for Beginners</h4>
<ul>
    <li><b>Start Simple:</b> Create your first template with just a few folders and files</li>
    <li><b>Use Examples:</b> Check out the built-in example templates for inspiration</li>
    <li><b>Drag & Drop:</b> Build structures by dragging files/folders from your computer</li>
    <li><b>Test First:</b> Create a test project to see how your template works</li>
</ul>

<h4>🔗 Next Steps</h4>
<p>Once you've created your first project, explore the other tabs for advanced features like:</p>
<ul>
    <li><b>Smart Naming:</b> Automatic file renaming with variables</li>
    <li><b>Batch Creation:</b> Generate multiple projects at once</li>
    <li><b>Team Workflows:</b> Share templates and collaborate</li>
</ul>
""",
        "🚀 Project Creation": f"""
<h3>📂 Master Project Creation</h3>
<p>Transform your templates into organized project structures with powerful automation features.</p>

<h4>🎯 Basic Project Creation</h4>
<ol>
    <li><b>Select Template:</b> Click any template in the gallery (right side) - it will highlight when selected</li>
    <li><b>Enter Project Name:</b> Type your project name in the left panel text box</li>
    <li><b>Choose Location:</b> Click "Browse..." to select where projects will be created</li>
    <li><b>Create:</b> Hit "Create Project(s)" and watch the magic happen!</li>
</ol>

<h4>⚡ Batch Project Creation</h4>
<p>Create multiple projects simultaneously with these input methods:</p>
<ul>
    <li><b>Line Breaks:</b> One project per line</li>
    <li><b>Commas:</b> <code>Project A, Project B, Project C</code></li>
    <li><b>Semicolons:</b> <code>Video 1; Video 2; Video 3</code></li>
    <li><b>Mixed:</b> Combine any separators as needed</li>
</ul>
<p><b>Example batch input:</b></p>
<pre><code>Marketing Campaign 2024
Social Media Video
Product Demo, Tutorial Series
Brand Guidelines; Style Guide</code></pre>
<p><i>This creates 6 separate projects automatically!</i></p>

<h4>🎛️ Sequence Variations (Power Feature)</h4>
<p>Check <b>"Create sequence variations"</b> to automatically generate multiple project versions:</p>

<h5>📅 Date Sequences</h5>
<ul>
    <li><b>Daily:</b> <code>MyProject_2024-01-01, MyProject_2024-01-02...</code></li>
    <li><b>Weekly:</b> <code>MyProject_2024-01-01, MyProject_2024-01-08...</code></li>
    <li><b>Monthly:</b> <code>MyProject_2024-01-01, MyProject_2024-02-01...</code></li>
    <li><b>Custom Formats:</b> YYYY-MM-DD, YYYYMMDD, MM/DD/YYYY, and more</li>
</ul>

<h5>🏷️ Version Numbers</h5>
<ul>
    <li><b>Standard:</b> <code>MyProject_V01, MyProject_V02, MyProject_V03...</code></li>
    <li><b>Formats:</b> V1/v1, Ver1, Version1 - choose your style</li>
    <li><b>Prefix/Suffix:</b> Put versions before or after project names</li>
</ul>

<h5>🔢 Sequential Numbers</h5>
<ul>
    <li><b>Basic:</b> <code>MyProject_001, MyProject_002, MyProject_003...</code></li>
    <li><b>Padding:</b> 1-digit, 2-digit, or 3-digit formatting</li>
    <li><b>Custom Start:</b> Begin numbering from any value</li>
</ul>

<h4>📊 Project Creation Results</h4>
<p>After creation, Echelon shows you:</p>
<ul>
    <li><b>Success Count:</b> How many projects were created successfully</li>
    <li><b>Detailed Report:</b> Individual results for each project</li>
    <li><b>Error Handling:</b> Clear messages for any issues encountered</li>
    <li><b>File Locations:</b> Direct links to your new project folders</li>
</ul>

<h4>🕒 Recent Projects & Templates</h4>
<ul>
    <li><b>File > Recent Projects:</b> Quick access to recently created project folders</li>
    <li><b>File > Recent Templates:</b> Jump back to templates you've used</li>
    <li><b>Smart Suggestions:</b> Echelon remembers your workflow patterns</li>
</ul>
""",
        "🎨 Templates & Smart Naming": f"""
<h3>🏗️ Build Intelligent Templates</h3>
<p>Create reusable project blueprints with automatic file naming and advanced customization.</p>

<h4>📁 Template Gallery Navigation</h4>
<ul>
    <li><b>Grid/List View:</b> Toggle between visual cards and detailed list views</li>
    <li><b>Search & Filter:</b> Find templates by name, description, category, or tags</li>
    <li><b>Categories:</b> Organize templates into logical groups (Web, Video, Design, etc.)</li>
    <li><b>Folders:</b> Create custom folders and drag templates to organize your workflow</li>
</ul>

<h4>⚡ Template Actions</h4>
<ul>
    <li><b>Single-Click:</b> Select template for project creation</li>
    <li><b>Double-Click:</b> Open template editor for modifications</li>
    <li><b>Right-Click Menu:</b>
        <ul>
            <li><b>Edit (✏️):</b> Modify template structure and settings</li>
            <li><b>Duplicate (📋):</b> Create a copy for customization</li>
            <li><b>Delete (🗑️):</b> Permanently remove template</li>
        </ul>
    </li>
</ul>

<h4>🎯 Creating New Templates</h4>
<ol>
    <li><b>Start:</b> Click "Add Template" or <b>File > New Template...</b></li>
    <li><b>Details:</b> Enter name, category, description, and optional tags</li>
    <li><b>Structure:</b> Switch to Structure tab and build your project layout</li>
    <li><b>Build Methods:</b>
        <ul>
            <li><b>Drag & Drop:</b> Pull files/folders from your computer</li>
            <li><b>Manual Creation:</b> Use "Add Folder" and "Add File" buttons</li>
            <li><b>Source Files:</b> Link actual files to be copied into projects</li>
        </ul>
    </li>
</ol>

<h4>🧠 Smart Naming System</h4>
<p>Make your files automatically rename themselves when creating projects:</p>

<h5>🏷️ Basic Smart Naming</h5>
<ul>
    <li><b>Right-click any file</b> in your template structure</li>
    <li><b>Select "Use Project Name"</b> - file will auto-rename with project name</li>
    <li><b>Example:</b> <code>Template_README.md</code> → <code>MyProject_README.md</code></li>
</ul>

<h5>🎛️ Advanced Custom Patterns</h5>
<p>For power users, select <b>"Custom Naming Patterns"</b> to access variables:</p>
<ul>
    <li><b>${{PROJECT_NAME}}:</b> Inserts the project name</li>
    <li><b>${{DATE}}:</b> Adds current date in various formats</li>
    <li><b>${{SEQUENCE}}:</b> Sequential numbering for batch projects</li>
    <li><b>${{CUSTOM}}:</b> User-defined variables for complex workflows</li>
</ul>

<h5>📝 Pattern Examples</h5>
<pre><code># Basic patterns
${{PROJECT_NAME}}_Script.docx
${{PROJECT_NAME}}_v01.prproj

# Date patterns  
${{PROJECT_NAME}}_${{DATE:YYYY-MM-DD}}.txt
Meeting_Notes_${{DATE:MM-DD-YYYY}}.docx

# Advanced combinations
${{PROJECT_NAME}}_Draft_${{SEQUENCE:001}}_${{DATE:YYYYMMDD}}.pdf</code></pre>

<h4>🔧 Template Management</h4>
<h5>📤 Import/Export</h5>
<ul>
    <li><b>Import:</b> <code>File > Import Template...</code> - Load .zip template packages</li>
    <li><b>Export Single:</b> Right-click template → Export for sharing</li>
    <li><b>Export All:</b> <code>File > Export > All Settings...</code> - Complete backup</li>
</ul>

<h5>💾 File Caching</h5>
<ul>
    <li><b>Automatic:</b> Source files are cached for faster project creation</li>
    <li><b>Efficient:</b> Templates work without accessing original file locations</li>
    <li><b>Settings:</b> Manage cache in <code>Edit > Preferences > Cache</code></li>
</ul>

<h4>👥 Team Collaboration</h4>
<ul>
    <li><b>Shared Storage:</b> <code>Edit > Preferences > Storage</code> - Set network location</li>
    <li><b>Template Sharing:</b> Export/import workflows for team consistency</li>
    <li><b>Version Control:</b> Use template descriptions to track changes</li>
        </ul>
""",
        "🔧 Advanced Tips & Troubleshooting": f"""
<h3>💡 Pro Tips & Problem Solving</h3>
<p>Master advanced workflows and resolve common issues like a power user.</p>

<h4>⚡ Power User Workflows</h4>

<h5>🚀 Productivity Shortcuts</h5>
<ul>
    <li><b>Keyboard Navigation:</b> Use arrow keys in template gallery, Enter to select</li>
    <li><b>Quick Duplicate:</b> Right-click template → Duplicate for rapid variations</li>
    <li><b>Batch Naming:</b> Use Excel/Sheets to generate project name lists, then copy-paste</li>
    <li><b>Template Favorites:</b> Drag frequently used templates to Favorites folder</li>
</ul>

<h5>📊 Advanced Project Organization</h5>
<ul>
    <li><b>Nested Structures:</b> Create deep folder hierarchies for complex projects</li>
    <li><b>Conditional Files:</b> Use multiple templates for different project phases</li>
    <li><b>Version Templates:</b> Create separate templates for Draft/Review/Final versions</li>
    <li><b>Client Workflows:</b> Build client-specific templates with branded assets</li>
</ul>

<h4>🛠️ Common Issues & Solutions</h4>

<h5>❌ Template Problems</h5>
<ul>
    <li><b>Template Won't Save:</b> Check file permissions, ensure template name is unique</li>
    <li><b>Missing Source Files:</b> Re-link files in template editor, check file paths</li>
    <li><b>Structure Not Updating:</b> Refresh template gallery, restart Echelon if needed</li>
    <li><b>Categories Missing:</b> Use "Manage Categories" to restore or recreate</li>
</ul>

<h5>🚫 Project Creation Failures</h5>
<ul>
    <li><b>Permission Denied:</b> Check output directory write permissions</li>
    <li><b>Disk Space:</b> Ensure sufficient storage for all projects</li>
    <li><b>Path Too Long:</b> Shorten project names or choose shorter output paths</li>
    <li><b>Special Characters:</b> Avoid <code>\\/:*?"<>|</code> in project names</li>
</ul>

<h5>⚙️ Performance Issues</h5>
<ul>
    <li><b>Slow Template Loading:</b> Clear cache in Preferences > Cache</li>
    <li><b>Large File Handling:</b> Consider using file links instead of embedded files</li>
    <li><b>Memory Usage:</b> Close unused template editors, restart app periodically</li>
</ul>

<h4>🔒 Data Management & Backup</h4>

<h5>💾 Backup Strategies</h5>
<ul>
    <li><b>Regular Exports:</b> Weekly exports of all templates and settings</li>
    <li><b>Version Control:</b> Keep dated backups of important templates</li>
    <li><b>Cloud Storage:</b> Store exports in Dropbox, Google Drive, or OneDrive</li>
    <li><b>Team Sync:</b> Share template packages with team members regularly</li>
</ul>

<h5>🔄 Migration & Updates</h5>
<ul>
    <li><b>New Computer:</b> Export all settings, install Echelon, import settings</li>
    <li><b>App Updates:</b> Templates are preserved, but export before major updates</li>
    <li><b>Shared Drives:</b> Test network permissions before switching storage locations</li>
</ul>

<h4>🎯 Optimization Tips</h4>

<h5>⚡ Speed Improvements</h5>
<ul>
    <li><b>Template Design:</b> Avoid excessive nesting, keep structures reasonable</li>
    <li><b>File Sizes:</b> Use smaller source files when possible</li>
    <li><b>Batch Limits:</b> Create 50 projects or fewer in single batch operations</li>
    <li><b>Cache Maintenance:</b> Periodically clear cache to free disk space</li>
</ul>

<h5>🎨 User Experience</h5>
<ul>
    <li><b>Descriptive Names:</b> Use clear, searchable template names and descriptions</li>
    <li><b>Consistent Categories:</b> Establish category naming conventions</li>
    <li><b>Tag Everything:</b> Add relevant tags for better searchability</li>
    <li><b>Regular Cleanup:</b> Archive or delete unused templates periodically</li>
</ul>

<h4>🆘 Getting Help</h4>
<ul>
    <li><b>Welcome Tutorial:</b> <code>Help > Show Welcome Tutorial</code> - Visual walkthrough</li>
    <li><b>This Guide:</b> <code>Help > Tutorial</code> - Comprehensive reference</li>
    <li><b>Reset Tutorials:</b> <code>Help > Reset Tutorials</code> - Start fresh</li>
    <li><b>Check Updates:</b> <code>Help > Check for Updates</code> - Latest features</li>
    <li><b>About Info:</b> <code>Help > About Echelon</code> - Version and system info</li>
</ul>

<h4>🎓 Learning Resources</h4>
<ul>
    <li><b>Start Simple:</b> Begin with basic templates, add complexity gradually</li>
    <li><b>Experiment:</b> Test templates with sample projects before important work</li>
    <li><b>Community:</b> Share templates with colleagues, learn from their approaches</li>
    <li><b>Documentation:</b> Keep notes on your template designs and naming conventions</li>
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
            color: {colors['accent']};
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
                font-size: 14px;
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
                font-size: 20px;
                font-weight: 600;
                margin: 0 0 16px 0;
                padding-bottom: 8px;
                border-bottom: 2px solid {colors['accent']};
            }}
            h4 {{ 
                color: {colors['text']};
                font-size: 16px;
                font-weight: 600;
                margin: 24px 0 8px 0;
            }}
            h5 {{ 
                color: {colors['accent']};
                font-size: 14px;
                font-weight: 600;
                margin: 16px 0 6px 0;
            }}
            p {{ 
                margin: 0 0 12px 0; 
                line-height: 1.6;
            }}
            ul, ol {{ 
                margin: 0 0 16px 0;
                padding-left: 24px;
            }}
            li {{ 
                margin-bottom: 6px;
                line-height: 1.5;
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
