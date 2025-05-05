"""
Script to copy template_structure_icon.svg to all required locations
"""
import os
import sys
import shutil

def main():
    # Source file
    source_file = os.path.join('app', 'assets', 'icons', 'template_structure_icon.svg')
    if not os.path.exists(source_file):
        source_file = os.path.join('ICONS', 'templates', 'template_structure_icon.svg')
        if not os.path.exists(source_file):
            print("ERROR: template_structure_icon.svg not found!")
            return 1
    
    print(f"Found source file: {source_file}")
    
    # Target locations
    target_dirs = [
        # Distribution directory structure
        os.path.join('WIN_BUILD', 'INTEL', 'dist', 'Echelon', '_internal'),
        os.path.join('WIN_BUILD', 'INTEL', 'dist', 'Echelon', '_internal', 'app', 'assets', 'icons'),
        os.path.join('WIN_BUILD', 'INTEL', 'dist', 'Echelon', '_internal', 'app', 'assets', 'icons', 'templates'),
        os.path.join('WIN_BUILD', 'INTEL', 'dist', 'Echelon', '_internal', 'ICONS', 'templates'),
        os.path.join('WIN_BUILD', 'INTEL', 'dist', 'Echelon', '_internal', 'icons', 'templates'),
        os.path.join('WIN_BUILD', 'INTEL', 'dist', 'Echelon'),
        # Original locations
        os.path.join('app', 'assets', 'icons'),
        os.path.join('app', 'assets', 'icons', 'templates'),
        os.path.join('ICONS', 'templates'),
    ]
    
    # Create directories and copy the file
    for target_dir in target_dirs:
        try:
            os.makedirs(target_dir, exist_ok=True)
            target_file = os.path.join(target_dir, 'template_structure_icon.svg')
            shutil.copy2(source_file, target_file)
            print(f"Copied to: {target_file}")
        except Exception as e:
            print(f"Error copying to {target_dir}: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 