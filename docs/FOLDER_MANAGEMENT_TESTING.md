# Folder Management Testing Checklist

This document provides a checklist for manually testing the unified folder management system to ensure it works correctly.

## Test Prerequisites

- Application is running with the unified folder management system
- You have the necessary permissions to create/modify/delete folders

## Test Scenarios

### 1. Creating Folders

- [ ] Click on "Manage Templates" from the application menu
- [ ] Select the "Folders" tab
- [ ] Click "New Folder" button
- [ ] Enter a name for the new folder (e.g., "Test Folder 1")
- [ ] Verify the folder appears in the list
- [ ] Click "Close" to return to the main application
- [ ] **VERIFICATION**: Check that the new folder appears in the folder dropdown in the main UI

### 2. Creating Folders from Main UI

- [ ] From the main UI, find the folder creation shortcut/button
- [ ] Create a new folder (e.g., "Test Folder 2")
- [ ] **VERIFICATION**: Check that the new folder appears in the folder dropdown immediately
- [ ] Return to "Manage Templates" dialog and verify the folder also appears there

### 3. Renaming Folders

- [ ] Go to "Manage Templates" dialog and select "Folders" tab
- [ ] Select an existing folder (e.g., "Test Folder 1")
- [ ] Click "Rename" button
- [ ] Change the name (e.g., to "Renamed Test Folder")
- [ ] **VERIFICATION**: Check that the renamed folder appears correctly in the folder dropdown in the main UI
- [ ] **VERIFICATION**: The old folder name should no longer be visible in the dropdown

### 4. Deleting Folders

- [ ] Go to "Manage Templates" dialog and select "Folders" tab
- [ ] Select a folder (e.g., "Test Folder 2")
- [ ] Click "Delete" button
- [ ] Confirm deletion when prompted
- [ ] **VERIFICATION**: Check that the deleted folder is removed from the list
- [ ] **VERIFICATION**: Check that the deleted folder is no longer present in the folder dropdown in the main UI

### 5. Adding Templates to Folders

- [ ] Select a template from the template gallery
- [ ] Open the template editor
- [ ] Check one of your test folders in the folder assignment list
- [ ] Save the template
- [ ] **VERIFICATION**: Filter templates by your test folder and confirm the template appears there

### 6. Edge Cases

- [ ] Try creating a folder with the same name as an existing folder (should show error)
- [ ] Try creating a folder with special characters (should handle appropriately)
- [ ] Try deleting the "Recent" or "Favorites" folders (should not be allowed)
- [ ] Try renaming a folder to an existing name (should show error)

## Test Results

Document any issues you encounter during testing:

1. Issue: 
   - Steps to reproduce: 
   - Expected behavior: 
   - Actual behavior: 

## Conclusion

All tests: ☐ PASSED | ☐ FAILED

Notes and observations: 