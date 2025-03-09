# Project Creator Tool

A tool for creating project structures from templates. Available in both Tkinter and PyQt versions.

## Features

- Create projects from file templates or directory templates
- Customize folder structures for different project types
- Save and reuse custom folder structures
- Batch creation of multiple projects
- Recent projects and templates tracking
- Template categorization and filtering
- Modern UI with PyQt option (space-efficient dropdown menus)
- Drag and drop functionality for templates and folders
- Cross-platform compatibility (Windows, macOS, Linux)

## Recent Updates (March 2025)

- Added batch project creation to PyQt version
- Converted categories UI from horizontal scrolling to dropdown menu
- Improved UI space utilization and layout
- Enhanced thread safety for batch operations

## Project Structure

The project is organized into the following directories:

- `app/` - Main application package
  - `core/` - Core application functionality
    - `app.py` - Main application class
    - `app_module.py` - Application module
    - `app_module_pyqt.py` - PyQt application module
    - `app_config.py` - Configuration settings
    - `app_initialization.py` - Initialization code
    - `project_builder.py` - Project creation logic
    - `project_operations.py` - Project operations
    - `structures.py` - Project structure definitions
  - `templates/` - Template management
    - `template_manager.py` - Template management
    - `templates.py` - Template definitions
    - `enhanced_template_manager.py` - Enhanced template management
    - `enhanced_template_card.py` - Template card UI component
    - `template_category_manager.py` - Category management
    - `template_gallery_ui.py` - Template gallery UI
    - `template_gallery_ui_pyqt.py` - PyQt template gallery UI
    - `template_folder_card.py` - Folder card UI component
    - `add_template_canvas.py` - Template canvas
    - `import_template.py` - Template import functionality
  - `ui/` - User interface components
    - `app_ui.py` - Main UI
    - `ui_components.py` - UI components
    - `app_theme.py` - Theme management
    - `color_scheme.py` - Color schemes
  - `utils/` - Utility functions
    - `utils.py` - General utilities
    - `integration.py` - Integration with external tools
  - `dialogs/` - Dialog windows (redirects to dialog/)

- `dialog/` - Dialog windows
  - `batch_dialog.py` - Batch creation dialog
  - `dialog_windows.py` - Common dialog windows
  - `about_dialog.py` - About dialog
  - `preferences_dialog.py` - Preferences dialog
  - `tutorial_dialog.py` - Tutorial dialog
  - `preview_dialog.py` - Preview dialog
  - `template_dialogs.py` - Template-related dialogs
  - `template_management_dialog.py` - Template management dialog
  - `folder_dialog.py` - Folder dialog
  - `category_dialog.py` - Category dialog
  - `template_edit_dialog.py` - Template editing dialog

- `main.py` - Main entry point
- `enhance_app.py` - Enhanced application entry point

## Working with Templates

### File Templates
Single file templates are useful when you want to create projects based on a specific file (like a Premiere project file, After Effects template, Photoshop document, etc). The system will create a folder structure and place the template file in the appropriate folder, renamed to match your project name.

### Directory Templates
Directory templates allow you to use an entire directory as a template. This is useful when:
- You need to include multiple files in your project template
- You want to create a project with a specific folder structure and starter files
- You need to include configuration files, scripts, or other supporting files

Directory templates support smart renaming - any files with `{{PROJECT_NAME}}` in the filename will be renamed with the actual project name. Text files within the template can also use placeholders like `{{PROJECT_NAME}}`, `{{DATE}}`, and `{{YEAR}}` that will be replaced with appropriate values.

## Running the Application

To run the application:

```
python main.py
```

For the enhanced version:

```
python enhance_app.py
```

### Switching between Tkinter and PyQt versions

The application offers both Tkinter and PyQt implementations. You can switch between them using the provided script:

```
python switch_version.py tkinter   # Switch to Tkinter version
python switch_version.py pyqt      # Switch to PyQt version
```

Or run without arguments for an interactive menu:

```
python switch_version.py
```

This will backup your current main.py file and replace it with the appropriate version.

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2023-present Craig P. Russo and CR2 Creative