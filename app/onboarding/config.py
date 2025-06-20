#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Onboarding System Configuration

Customize the onboarding system behavior and content here.
"""

# Tutorial timing configuration
SLIDESHOW_CONFIG = {
    'default_auto_advance_speed': 4000,  # milliseconds
    'min_speed': 2000,
    'max_speed': 10000,
    'animation_duration': 300,  # slide transition duration
}

# UI styling overrides (optional)
STYLE_OVERRIDES = {
    'slideshow_border_radius': 16,
    'progress_bar_height': 8,
    'button_spacing': 10,
}

# Tutorial content customization
TUTORIAL_CONTENT = {
    'app_name': 'Echelon',  # Your app name
    'welcome_title': '👋 Welcome to {app_name}!',
    'completion_message': '🎉 You\'re All Set!',
    'skip_confirmation': False,  # Whether to confirm before skipping
}

# Feature flags
FEATURES = {
    'auto_start_on_first_launch': True,
    'show_progress_indicator': True,
    'enable_keyboard_navigation': True,
    'enable_skip_confirmation': False,
    'enable_analytics_events': False,  # For future use
}

# Default preferences
DEFAULT_PREFERENCES = {
    'show_welcome_slideshow': True,
    'auto_start_tutorials': True,
    'slideshow_auto_advance': False,
    'slideshow_speed': SLIDESHOW_CONFIG['default_auto_advance_speed'],
}

# Slideshow customization
CUSTOM_SLIDESHOW_CONTENT = [
    {
        'title': 'Welcome to Echelon',
        'content': 'Create organized project structures with ease using templates and custom configurations.\n\n📁 Step 1: Create a Template\nFirst, you\'ll create a template that defines your project structure.\n\n• Click the "Add Template" button to get started\n• Give your template a descriptive name\n• This template will be reusable for all future projects of this type\n\nThink of it as creating a blueprint for your projects!',
        'image_path': 'sample_svgs/SLIDE 01.png',
        'duration': 6000  # Longer duration since there's more content
    },
    {
        'id': 'add_files',
        'title': '📂 Step 2: Add Files & Folders',
        'content': 'Next, you\'ll build your project structure by dragging files and folders.\n\n• Drag files and folders from your computer into the template area\n• Organize them exactly how you want your projects structured\n• You can create folders, add starter files, and set up your ideal workflow\n\nThis becomes your project template that you can use over and over!',
        'image_path': 'sample_svgs/SLIDE_02_BG.png',
        'arrow_delay': 1000,
        'arrow_image_path': 'sample_svgs/SLIDE_02_ARROW.png'
    },
    {
        'id': 'smart_patterns',
        'title': '⚡ Step 3: Smart File Patterns',
        'content': 'Here\'s the powerful part - smart file renaming!\n\n• Right-click on any file in your template structure\n• This opens a context menu with powerful options\n• Choose "Use Project Name" to automatically rename files\n• For more advanced naming options, you can select "Custom Naming Patterns"\n• Files will be renamed when you create new projects\n\nFor example: "MyTemplate.txt" becomes "MyNewProject.txt" automatically!',
        'image_path': 'sample_svgs/SLIDE_03_BG.png',
        'multi_step_sequence': [
            {
                'step': 1,
                'delay': 1000,
                'action': 'show_arrow',
                'arrow_image': 'sample_svgs/SLIDE_03_ARROW.png',
                'description': 'Right-click on any file to access smart naming options'
            },
            {
                'step': 2,
                'delay': 3000,
                'action': 'fade_arrow_show_overlay',
                'overlay_image': 'sample_svgs/SLIDE_03_MENU.png',
                'description': 'Context menu appears with powerful options'
            },
            {
                'step': 3,
                'delay': 2000,
                'action': 'show_final_arrow',
                'arrow_image': 'sample_svgs/SLIDE_03_MENU_ARROW.png',
                'description': 'Select "Use Project Name" for automatic file renaming'
            },
            {
                'step': 4,
                'delay': 3000,
                'action': 'show_advanced_arrow',
                'arrow_image': 'sample_svgs/SLIDE_03_ADV_ARROW.png',
                'description': 'For more advanced naming options, select "Custom Naming Patterns"'
            }
        ]
    },
    {
        'id': 'create_project',
        'title': '🚀 Step 4: Create Your Project',
        'content': 'Ready to create a project? Now enter your project name in the Project Settings panel and then select a template that you want to use.\n\nQuick tip: To edit a template just double click it or right click it.',
        'image_path': 'sample_svgs/SLIDE_04_BG.png',
        'arrow_delay': 1500,
        'arrow_image_path': 'sample_svgs/SLIDE_04_ARROW.png'
    },
    {
        'id': 'completion',
        'title': '🎉 You\'re All Set!',
        'content': 'That\'s it! You now know how to:\n\n✅ Create reusable project templates\n✅ Add and organize files and folders\n✅ Set up smart file naming patterns\n✅ Generate new projects instantly\n\nReady to start creating amazing projects? Click the "Create Project(s)" button to create your projects and you\'re done!\n\nTip: You can always access this tutorial again from the Help menu.',
        'image_path': 'sample_svgs/SLIDE_05_BG.png',
    }
] 