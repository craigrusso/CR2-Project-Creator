#!/usr/bin/env python3
# Script to update copyright notices in all Python files

import os
import re
import sys
from pathlib import Path

def update_copyright_in_file(file_path):
    """Update copyright notice in a Python file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if file starts with shebang
    has_shebang = content.startswith('#!/usr/bin/env python')
    
    # Define patterns to match existing copyright lines
    copyright_patterns = [
        r'# Copyright \d+ CR2 Creative Pro Tools',
        r'# Copyright (c) 2023-present Craig P. Russo and CR2 Creative'
    ]
    
    # New copyright notice
    new_copyright = '# Copyright (c) 2023-present Craig P. Russo and CR2 Creative'
    
    # Try to replace existing copyright notices
    for pattern in copyright_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, new_copyright, content)
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Updated copyright in {file_path}")
            return True
    
    # If no copyright notice was found, add one after shebang if exists
    if has_shebang:
        shebang_end = content.find('\n') + 1
        new_content = content[:shebang_end] + new_copyright + '\n' + content[shebang_end:]
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Added copyright to {file_path}")
        return True
    
    # If no shebang, add copyright at the beginning
    if not any(pattern in content for pattern in copyright_patterns):
        new_content = new_copyright + '\n\n' + content
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Added copyright to {file_path}")
        return True
    
    return False

def main():
    """Main function to walk through directories and update copyright notices."""
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Keep track of files updated
    updated_files = []
    skipped_files = []
    
    # Walk through all directories
    for root, dirs, files in os.walk(workspace_dir):
        # Skip .git directory
        if '.git' in dirs:
            dirs.remove('.git')
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
        if '.cursor' in dirs:
            dirs.remove('.cursor')
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if update_copyright_in_file(file_path):
                    updated_files.append(file_path)
                else:
                    skipped_files.append(file_path)
    
    print(f"\nUpdated {len(updated_files)} files")
    if skipped_files:
        print(f"Skipped {len(skipped_files)} files")
    
    # Also update README.md to mention the license
    readme_path = os.path.join(workspace_dir, 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r') as f:
            readme_content = f.read()
        
        # Add license section if not already present
        if 'License' not in readme_content:
            license_section = "\n\n## License\n\nThis project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License - see the [LICENSE](LICENSE) file for details.\n\nCopyright (c) 2023-present Craig P. Russo and CR2 Creative"
            
            with open(readme_path, 'a') as f:
                f.write(license_section)
            print(f"Added license section to README.md")
    
if __name__ == "__main__":
    main() 