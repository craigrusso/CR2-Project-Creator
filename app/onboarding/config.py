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

# Guided tour configuration
GUIDED_TOUR_CONFIG = {
    'tooltip_size': (350, 250),  # (width, height)
    'highlight_padding': 8,  # pixels around highlighted widget
    'highlight_border_width': 3,
    'animation_duration': 300,
    'position_offset': (20, 20),  # (x, y) offset from target widget
}

# UI styling overrides (optional)
STYLE_OVERRIDES = {
    'tooltip_border_radius': 16,
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

# Widget search patterns for guided tour
# Add alternative names for your widgets here
WIDGET_SEARCH_PATTERNS = {
    'create_template_button': [
        'create_template_btn',
        'createTemplateButton', 
        'btnCreateTemplate',
        'new_template_button',
        'add_template_btn'
    ],
    'template_name_field': [
        'template_name',
        'templateNameField',
        'name_input',
        'template_name_edit',
        'template_title_field'
    ],
    'structure_editor': [
        'structure_area',
        'structureEditor',
        'template_structure',
        'file_tree',
        'structure_tree_widget'
    ],
    'project_name_field': [
        'project_name',
        'projectNameField',
        'name_field',
        'project_name_edit',
        'output_name_field'
    ],
    'template_gallery': [
        'gallery',
        'templateGallery',
        'template_list',
        'gallery_widget',
        'template_view'
    ]
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
    'show_guided_tour': True,
    'auto_start_tutorials': True,
    'slideshow_auto_advance': False,
    'slideshow_speed': SLIDESHOW_CONFIG['default_auto_advance_speed'],
    'auto_start_guided_tour_after_slideshow': True,  # New setting
}

# Tutorial step customization
# You can modify these to match your app's specific workflow
CUSTOM_TOUR_STEPS = [
    {
        'id': 'create_template',
        'title': '🎯 Create Your First Template',
        'content': 'Click this button to create a new template. This will be your project blueprint!',
        'target': 'create_template_button',
        'highlight': True,
        'wait_for_action': False,  # Whether to wait for user to perform the action
    },
    {
        'id': 'name_template',
        'title': '📝 Name Your Template',
        'content': 'Give your template a descriptive name that represents the type of projects you\'ll create.',
        'target': 'template_name_field',
        'highlight': True,
        'wait_for_action': False,
    },
    {
        'id': 'build_structure',
        'title': '📁 Drag Files & Folders',
        'content': 'Drag files and folders from your computer into this area to build your project structure.',
        'target': 'structure_editor',
        'highlight': True,
        'wait_for_action': False,
    },
    {
        'id': 'smart_patterns',
        'title': '⚡ Smart File Patterns',
        'content': 'Right-click on any file to set up smart naming patterns. Files will be automatically renamed in new projects!',
        'target': 'structure_editor',
        'highlight': True,
        'wait_for_action': False,
    },
    {
        'id': 'create_project',
        'title': '🚀 Create Projects',
        'content': 'Enter a project name here and click "Create Project" to generate your new project instantly!',
        'target': 'project_name_field',
        'highlight': True,
        'wait_for_action': False,
    },
    {
        'id': 'template_gallery',
        'title': '📊 Template Gallery',
        'content': 'All your saved templates appear here. Click any template to use it for creating new projects.',
        'target': 'template_gallery',
        'highlight': True,
        'wait_for_action': False,
    }
]

# Slideshow customization
CUSTOM_SLIDESHOW_CONTENT = [
    {
        'title': 'Welcome to Echelon',
        'content': 'Create organized project structures with ease using templates and custom configurations.\n\n📁 Step 1: Create a Template\nFirst, you\'ll create a template that defines your project structure.\n\n• Click the "Create Template" button to get started\n• Give your template a descriptive name\n• This template will be reusable for all future projects of this type\n\nThink of it as creating a blueprint for your projects!',
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
        'content': 'Ready to create a project? It\'s super simple:\n\n• Enter your project name in the text field\n• Choose your output location\n• Click "Create Project" and watch the magic happen!\n\nYou can also create multiple versions with date sequences for iterative work.',
        'image_path': None,
    },
    {
        'id': 'completion',
        'title': '🎉 You\'re All Set!',
        'content': 'That\'s it! You now know how to:\n\n✅ Create reusable project templates\n✅ Add and organize files and folders\n✅ Set up smart file naming patterns\n✅ Generate new projects instantly\n\nReady to start creating amazing projects? Let\'s dive in!\n\nTip: You can always access this tutorial again from the Help menu.',
        'image_path': None,
    }
] 