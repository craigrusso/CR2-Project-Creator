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
        'content': 'Stop recreating the same project folders over and over again.\n\nEchelon lets you create smart project templates that automatically generate organized folder structures with intelligent file naming.\n\n📁 **Step 1: Create Your Template**\nClick the "Add Template" button to get started, then give your template a descriptive name.\n\n🎯 **What you\'ll learn next:**\n• Build your ideal project structure\n• Set up automatic file naming\n• Generate projects instantly\n\nReady to streamline your workflow? Let\'s begin!',
        'image_path': 'slides/SLIDE_01.png',
        'duration': 6000  # Longer duration since there's more content
    },
    {
        'id': 'add_files',
        'title': '📂 Step 2: Build Your Structure',
        'content': 'Now drag and drop files and folders from your computer to build your ideal project structure.\n\n✨ **Pro tip:** Include everything you typically need:\n• Starter files and documents\n• Folder hierarchies for assets, code, docs\n• Configuration files\n• README templates\n\nArrange everything exactly how you like it – this becomes your reusable blueprint!\n\n💡 The arrow shows you where to drop your files and folders.',
        'image_path': 'slides/SLIDE_02_BG.png',
        'arrow_delay': 1000,
        'arrow_image_path': 'slides/SLIDE_02_ARROW.png'
    },
    {
        'id': 'smart_patterns',
        'title': '⚡ Step 3: Add Smart Naming',
        'content': 'Here\'s where the magic happens! Make your files automatically rename themselves.\n\n🎯 **Watch this:** Right-click any file in your template to see the context menu.\n\n**Choose "Use Project Name"** and that file will automatically update its name when you create new projects.\n\n**Need more control?** Select "Custom Naming Patterns" for advanced options.\n\n💡 **Example:** "Template_README.md" becomes "MyAwesomeProject_README.md" automatically!',
        'image_path': 'slides/SLIDE_03_BG.png',
        'multi_step_sequence': [
            {
                'step': 1,
                'delay': 1000,
                'action': 'show_arrow',
                'arrow_image': 'slides/SLIDE_03_ARROW_01.png',
                'description': 'Right-click on any file to access smart naming options'
            },
            {
                'step': 2,
                'delay': 2500,
                'action': 'fade_arrow_show_overlay',
                'fade_out_arrow': 'slides/SLIDE_03_ARROW_01.png',
                'overlay_image': 'slides/SLIDE_03_MENU.png',
                'description': 'Context menu appears with powerful options'
            },
            {
                'step': 3,
                'delay': 2000,
                'action': 'show_final_arrow',
                'arrow_image': 'slides/SLIDE_03_MENU_ARROW.png',
                'description': 'Select "Use Project Name" for automatic file renaming'
            },
            {
                'step': 4,
                'delay': 3000,
                'action': 'show_advanced_arrow',
                'arrow_image': 'slides/SLIDE_03_ADV_ARROW.png',
                'description': 'For more advanced naming options, select "Custom Naming Patterns"'
            }
        ]
    },
    {
        'id': 'create_project',
        'title': '🚀 Step 4: Set Up Your Project',
        'content': 'Your template is ready! Now let\'s set up your new project.\n\n**Enter your project name(s)** in the left panel. You can create multiple projects at once by entering several names.\n\n**Then select your template** on the right side to use for your new project(s).\n\n🎯 **Power Feature: Sequence Variations**\nCheck "Create sequence variations" to automatically generate multiple project versions:\n• **Date Sequences** → MyProject_2024-01-01, MyProject_2024-01-02...\n• **Version Numbers** → MyProject_V01, MyProject_V02...\n• **Sequential Numbers** → MyProject_001, MyProject_002...\n\nPerfect for versioned work, daily tracking, or batch project creation!\n\n💡 **Pro tip:** You can edit any template anytime by double-clicking it, or create variations for different project types.',
        'image_path': 'slides/SLIDE_04_BG.png',
        'arrow_delay': 1500,
        'arrow_image_path': 'slides/SLIDE_04_ARROW.png'
    },
    {
        'id': 'completion',
        'title': '🎉 Click "Create Project(s)" and You\'re Done!',
        'content': 'This is it – the moment of magic! **Click the "Create Project(s)" button** and watch Echelon generate your complete project structure with all files properly named and organized.\n\n**You\'ve just learned how to:**\n✅ Build smart, reusable project templates\n✅ Set up automatic file and folder naming\n✅ Generate perfectly organized projects in seconds\n✅ Create multiple projects simultaneously\n\n🚀 **Ready to transform your workflow?** \nGo ahead and create your first template – your future self will thank you!\n\n💡 *Find this tutorial anytime in the Help menu.*',
        'image_path': 'slides/SLIDE_05_BG.png',
    }
] 