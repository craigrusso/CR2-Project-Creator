# Onboarding Tutorial System

A modular, self-contained onboarding tutorial system for PyQt6 applications that provides both slideshow-style tutorials and guided interactive tours.

## Features

- **📱 Modern Slideshow Tutorials**: Beautiful, animated slideshow with progress indicators
- **🎯 Interactive Guided Tours**: Step-by-step tooltips that highlight specific UI elements
- **💾 State Management**: Automatically tracks tutorial completion and user preferences
- **🎨 Theme Integration**: Uses your app's existing color scheme and styling
- **⚙️ Highly Configurable**: Easy to customize content, timing, and behavior
- **🔌 Easy Integration**: Minimal changes to existing codebase

## Quick Start

### 1. Basic Integration

Add this to your main app class:

```python
from app.onboarding.integration import OnboardingIntegration

class YourMainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Your existing initialization...
        
        # Add onboarding system
        self.onboarding = OnboardingIntegration(self)
        
        # After your UI is set up:
        self.onboarding.setup_ui_references()
        self.onboarding.initialize()
```

### 2. Add Menu Items

```python
def create_menu(self):
    # Your existing menu code...
    
    help_menu = self.menuBar().addMenu("Help")
    help_menu.addAction("Show Welcome Tutorial", self.onboarding.show_welcome)
    help_menu.addAction("Show Guided Tour", self.onboarding.show_guided_tour)
    help_menu.addSeparator()
    help_menu.addAction("Reset Tutorials", self.onboarding.reset_tutorials)
```

### 3. Widget Mapping

In the `integration.py` file, update the `widget_mappings` to match your actual widget references:

```python
widget_mappings = {
    'create_template_button': 'your_create_button_reference',
    'template_name_field': 'your_name_field_reference',
    'structure_editor': 'your_structure_widget_reference',
    # ... etc
}
```

## File Structure

```
app/onboarding/
├── __init__.py              # Module initialization
├── tutorial_manager.py      # Main controller
├── slideshow.py            # Slideshow tutorial component
├── guided_tour.py          # Interactive guided tour component
├── tutorial_state.py       # State and preferences management
├── integration.py          # Easy integration helper
├── config.py              # Configuration and customization
└── README.md              # This file
```

## Components

### TutorialManager
The main controller that coordinates between slideshow and guided tour components.

**Key Methods:**
- `initialize()` - Start the tutorial system
- `show_welcome_slideshow()` - Display slideshow
- `show_guided_tour()` - Start interactive tour
- `reset_tutorials()` - Reset all tutorial progress

### TutorialSlideshow
Beautiful slideshow with:
- Modern card-based design
- Progress indicators
- Smooth animations
- Keyboard navigation
- Auto-advance option

### GuidedTour
Interactive step-by-step guide with:
- Animated tooltips
- UI element highlighting
- Contextual positioning
- Skip/previous/next navigation

### TutorialState
Manages tutorial completion state and preferences:
- Tracks which tutorials have been completed
- Stores user preferences
- Handles first-launch detection
- Saves state to app preferences

## Customization

### Content Customization

Edit `config.py` to customize:

```python
# Change tutorial content
CUSTOM_SLIDESHOW_CONTENT = [
    {
        'title': 'Your Custom Title',
        'content': 'Your custom content...',
        # ...
    }
]

# Modify guided tour steps
CUSTOM_TOUR_STEPS = [
    {
        'title': 'Custom Step',
        'content': 'Custom step content...',
        'target': 'your_widget_name',
        # ...
    }
]
```

### Visual Customization

The system automatically uses your app's color scheme through `app.ui.color_scheme_pyqt`. You can override specific styles in `config.py`:

```python
STYLE_OVERRIDES = {
    'tooltip_border_radius': 16,
    'slideshow_border_radius': 16,
    'progress_bar_height': 8,
}
```

### Timing Configuration

```python
SLIDESHOW_CONFIG = {
    'default_auto_advance_speed': 4000,  # 4 seconds
    'animation_duration': 300,
}

GUIDED_TOUR_CONFIG = {
    'tooltip_size': (350, 250),
    'animation_duration': 300,
}
```

## User Preferences

The system saves these preferences:
- `tutorial_show_welcome_slideshow` - Show slideshow on startup
- `tutorial_show_guided_tour` - Show guided tour
- `tutorial_auto_start` - Auto-start tutorials for new users
- `tutorial_slideshow_auto_advance` - Auto-advance slideshow
- `tutorial_slideshow_speed` - Auto-advance speed
- `tutorial_completed_tutorials` - List of completed tutorials

## Integration with Preferences Dialog

To add tutorial preferences to your existing preferences dialog:

```python
# Get current tutorial preferences
tutorial_prefs = self.onboarding.get_tutorial_preferences()

# Create UI controls for:
# - tutorial_prefs['slideshow_enabled']
# - tutorial_prefs['guided_tour_enabled']
# - tutorial_prefs['auto_start']
# - tutorial_prefs['auto_advance']
# - tutorial_prefs['speed']

# When preferences change:
self.onboarding.update_preferences({
    'slideshow_enabled': checkbox_value,
    'guided_tour_enabled': checkbox_value,
    'auto_start': checkbox_value,
    'auto_advance': checkbox_value,
    'speed': slider_value
})
```

## Events and Signals

The tutorial system emits signals you can connect to:

```python
# Tutorial events
self.onboarding.tutorial_manager.tutorial_started.connect(self.on_tutorial_started)
self.onboarding.tutorial_manager.tutorial_completed.connect(self.on_tutorial_completed)
self.onboarding.tutorial_manager.all_tutorials_completed.connect(self.on_all_completed)

def on_tutorial_started(self, tutorial_type):
    print(f"User started: {tutorial_type}")

def on_tutorial_completed(self, tutorial_type):
    print(f"User completed: {tutorial_type}")
```

## Widget Detection

The guided tour automatically finds your widgets by:

1. **Object Name**: Set widget object names that match the tour expectations
2. **Search Patterns**: Define alternative names in `config.py`
3. **Manual Registration**: Use `register_widget_for_tour(widget, name)`

Example:
```python
# Method 1: Set object names
self.create_button.setObjectName('create_template_button')

# Method 2: Register manually
self.onboarding.tutorial_manager.register_widget_for_tour(
    self.create_button, 
    'create_template_button'
)
```

## Best Practices

1. **Widget Names**: Use descriptive, consistent widget names
2. **Content**: Keep tutorial steps concise and actionable
3. **Testing**: Test tutorials on fresh installs to simulate new user experience
4. **Updates**: Update tutorial content when UI changes significantly
5. **Accessibility**: Ensure tutorials work with screen readers and keyboard navigation

## Troubleshooting

### Widgets Not Found
- Check widget object names match expected names
- Add alternative names to `WIDGET_SEARCH_PATTERNS` in `config.py`
- Use manual registration with `register_widget_for_tour()`

### Tutorials Not Showing
- Check if tutorials are disabled in preferences
- Verify `initialize()` is called after UI setup
- Check console for error messages

### Styling Issues
- Ensure your app's color scheme is properly set up
- Check for CSS conflicts
- Customize styles in `config.py` if needed

## Future Enhancements

Potential additions for future versions:
- Video/GIF support in slideshow
- Interactive elements in slides
- Tutorial analytics and telemetry
- Multi-language support
- Advanced highlighting effects
- Custom animation types

## License

Copyright (c) 2023-present Craig P. Russo and CR2 Creative 