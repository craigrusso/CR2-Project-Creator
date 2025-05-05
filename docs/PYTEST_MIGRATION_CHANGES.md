# PyQt Migration Testing Checklist

This document provides a checklist for testing the PyQt migration, focusing on the recently updated components.

## Prerequisites

- Run `python switch_version.py pyqt` to switch to PyQt version
- Ensure PyQt5 is installed

## Functional Testing

### Structure Editor

- [ ] Create a new custom structure
  1. Click "Edit..." button next to the structure dropdown
  2. Verify the structure editor opens
  3. Add folders using the "Add Folder" button
  4. Verify folders appear in the tree
  5. Save the structure with a name
  6. Verify it appears in the structure dropdown

- [ ] Edit an existing structure
  1. Select a custom structure from the dropdown
  2. Click "Edit..." button
  3. Verify the structure editor opens with the existing structure
  4. Make changes (add/remove folders)
  5. Save with the same or new name
  6. Verify changes are reflected

- [ ] Preview structure
  1. Select any structure from the dropdown
  2. Click "Preview Structure" button
  3. Verify the structure preview dialog shows correctly

- [ ] Manage structures
  1. Open the Tools menu
  2. Select "Manage Folder Structures"
  3. Verify the management dialog opens
  4. Test renaming a structure
  5. Test deleting a structure

### Template Management

- [ ] Template gallery functionality
  1. Verify templates appear in the gallery
  2. Test selecting a template
  3. Verify the template is highlighted when selected

- [ ] Template folder management
  1. Create a new folder
  2. Add templates to the folder
  3. Verify templates appear in the folder
  4. Test removing templates from folders

- [ ] Template editing
  1. Edit a template
  2. Verify changes are saved
  3. Verify the template is updated in the gallery

### Project Creation

- [ ] Create a project
  1. Enter a project name
  2. Select an output directory
  3. Select a template file
  4. Choose a structure
  5. Click "Create Project"
  6. Verify the project is created with the correct structure

- [ ] Batch project creation
  1. Click "Batch Create Projects" button
  2. Enter multiple project names
  3. Verify batch creation works with selected settings

## UI Testing

- [ ] Verify all dialogs render correctly
- [ ] Check that all buttons and controls work as expected
- [ ] Verify layouts adjust properly when resizing windows
- [ ] Test dark theme application to components
- [ ] Check tooltips and help text

## Framework Switching

- [ ] Switch back to Tkinter version
  1. Run `python switch_version.py tkinter`
  2. Verify the app loads correctly with Tkinter
  3. Test same functionality as above

- [ ] Switch to PyQt again
  1. Run `python switch_version.py pyqt`
  2. Verify the app loads correctly with PyQt
  3. Verify all changes persistent between framework switches

## Error Handling

- [ ] Test invalid inputs in structure editor
- [ ] Test invalid project names
- [ ] Check error messages display correctly

## Post-Testing

- [ ] Document any issues found
- [ ] Create fixes for any identified bugs
- [ ] Update documentation with changes 