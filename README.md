# CR2 Creative Project Creator v4

A powerful template-based project creator for creative professionals. This application allows you to create project folder structures from templates with ease.

## Recent UX Improvements

### Template File Selection Streamlined

The application has been updated to improve the user experience by:

1. **Removing redundant template file selection**: Previously, users needed to select both a template and a separate template file, which was redundant. Now, templates directly include their files.

2. **Simplified workflow**: Now you simply:
   - Enter a project name
   - Select an output directory
   - Select a template from the gallery
   - Click "Create Project"

3. **Better template management**: Templates now properly include their file structure, making it easier to manage and use templates.

## Features

- Modern, dark-themed interface
- Template gallery with categories and search
- Custom folder structures
- File placeholders with project name substitution
- Batch project creation
- Recent projects and templates tracking

## Setup

1. Ensure you have Python 3.6+ installed
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python main.py
   ```

## Creating Templates

Templates can be easily created and managed through the built-in template editor. Templates include:

- Template name and description
- Associated files (which will be automatically copied to new projects)
- Folder structure (optional)
- Category assignment

## Development

This application is built using:
- Python 3
- PyQt5 for the user interface
- Custom template management system

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2023-present Craig P. Russo and CR2 Creative