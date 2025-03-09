# Cleanup Plan for Unified Folder Management System

After implementing the unified folder management system, the following files and code can be safely removed or modified:

## Files to Remove

1. **app/templates/enhanced_template_manager.py** 
   - This file is now completely redundant as its functionality has been integrated into the main TemplateManager class.

## Code to Clean Up

1. **app/utils/integration.py**
   - Remove references to TemplateManagerEnhanced
   - Update patched functions to use the unified system

2. **app/templates/template_gallery_ui.py**
   - Remove code that creates or initializes TemplateManagerEnhanced

3. **dialog/folder_dialog.py**
   - Remove dual-system code that updates both template managers

## Files to Keep but Modify

1. **app/templates/template_manager_migration.py**
   - Keep this file for users upgrading from previous versions
   - Eventually can be removed in a future release after all users have migrated

## Implementation Order

1. First, make sure the app runs correctly with our changes
2. Remove enhanced_template_manager.py
3. Clean up references in other files
4. Run the app again to ensure everything still works

## Transition Period Considerations

- Keep the proxy system in place for at least one release to ensure backward compatibility
- Add comments to mark code that will be removed in future versions
- Consider adding a version check to disable migration code for new installations 