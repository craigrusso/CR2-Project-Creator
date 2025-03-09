#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import platform
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, StringVar, BooleanVar
from tkinter.constants import *
import time

from app.core.app_config import APP_NAME, APP_VERSION, RECENT_TEMPLATES_MAX, setup_dpi_awareness
from app.ui.color_scheme import colors
from app.utils.utils import load_config, save_config, truncate_path
from app.ui.ui_components import ToolTip, CardFrame, SearchBox, TemplateFileCard
from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder
from dialog.dialog_windows import (preview_structure, show_batch_create, show_about, 
                          show_tutorial, show_preferences)
from app.templates.templates import (populate_template_gallery, select_template_from_gallery, 
                     get_template_file, clear_template_file, clear_structure_template,
                     rename_current_template, rename_template_file)
from app.core.structures import (create_custom_structure, edit_structure, update_structure_dropdown,
                     manage_structures)
from app.core.project_operations import (create_project, handle_batch_create, 
                             open_recent_project, clear_recent_projects,
                             use_recent_template, clear_recent_templates,
                             add_to_recent_templates, update_card_highlighting,
                             remove_from_recent_templates)
from app.utils.utils import (load_recent_projects, save_recent_projects, 
                 open_folder, create_sample_templates, load_recent_templates,
                 save_recent_templates)
from app.ui.app_ui import create_ui
from app.ui.app_theme import configure_styles, apply_theme_to_widgets
from app.core.app_initialization import initialize_app, load_app_config, load_app_recent_projects, load_app_recent_templates

# Initialize sample templates if needed
create_sample_templates()

class ProjectCreatorApp:
    """
    Main application class for CR2 Creative Pro project creator
    """
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} - Project Creator {APP_VERSION}")
        
        # Increase initial size to ensure all elements fit, including bottom buttons
        self.root.geometry("1080x800+300+100")  # Initial size that fits all elements comfortably
        self.root.minsize(900, 780)  # Increased minimum height to ensure bottom elements are visible
        self.root.configure(background=colors["bg"])
        
        # Create a fixed bottom container to hold both buttons and status bar
        self.bottom_container = tk.Frame(root, height=80, bg=colors["bg"])
        self.bottom_container.pack(side=BOTTOM, fill=X, pady=0)
        self.bottom_container.pack_propagate(False)  # Prevent frame from shrinking
        
        # Status bar with fixed height and guaranteed space
        status_frame = tk.Frame(self.bottom_container, height=26, bg=colors["card_bg"])
        status_frame.pack(side=BOTTOM, fill=X, pady=(0, 5))  # Added padding below
        status_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        self.status_var = StringVar()
        self.status_var.set("Ready")
        self.status_bar = tk.Label(status_frame, textvariable=self.status_var, 
                                 bg=colors["card_bg"], fg=colors["text"],
                                 anchor=W, padx=10)
        self.status_bar.pack(fill=BOTH, expand=True)
        
        # Initialize the application (partial)
        # Set up managers, state, and configuration
        initialize_app(self)
        
        # Create the UI and menu
        create_ui(self)
        self.create_menu()
        
        # Now load recent items that depend on UI elements
        self.load_recent_projects()
        self.load_recent_templates()
        
        # Set application icon
        self.set_app_icon()
        
        # Check for updates
        self.root.after(2000, self.check_for_updates)
    
    def _update_ui_from_config(self):
        """Update UI elements based on config values"""
        # Update advanced options visibility
        advanced_value = self.config.get("show_advanced_options", False)
        self.advanced_var.set(advanced_value)
        
        # Update any other UI elements based on config
        
    def set_app_icon(self):
        """Set the application icon based on platform"""
        try:
            if platform.system() == "Windows":
                icon_path = os.path.join(os.path.dirname(__file__), "images", "app_icon.ico")
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
            elif platform.system() == "Darwin":  # macOS
                # macOS uses the .icns file automatically from the app bundle
                pass
        except Exception as e:
            print(f"Error setting app icon: {e}")
    
    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        
        file_menu.add_command(label="Save Template...", command=lambda: self.template_manager.save_template_ui(self))
        file_menu.add_command(label="Import Template...", command=lambda: self.template_manager.import_template_ui(self))
        file_menu.add_command(label="Manage Templates...", command=lambda: self.template_manager.manage_templates_ui(self))
        file_menu.add_separator()
        
        # Recent projects submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Projects", menu=self.recent_menu)
        self.update_recent_menu()
        
        file_menu.add_command(label="Clear Recent Projects", command=lambda: clear_recent_projects(self))
        file_menu.add_separator()
        
        # Recent templates submenu
        self.recent_templates_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Templates", menu=self.recent_templates_menu)
        self.update_recent_templates_menu()
        
        file_menu.add_command(label="Clear Recent Templates", command=lambda: clear_recent_templates(self))
        file_menu.add_separator()
        
        file_menu.add_command(label="Exit", command=self.root.destroy)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        edit_menu.add_command(label="Preferences...", command=lambda: show_preferences(self))
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Remove the advanced options menu item
        # view_menu.add_checkbutton(label="Advanced Options", variable=self.advanced_var, command=self.toggle_advanced)
        
        # Add some other view options instead
        view_menu.add_command(label="Refresh Template Gallery", command=lambda: populate_template_gallery(self))
        view_menu.add_command(label="Refresh Structure List", command=lambda: update_structure_dropdown(self))
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        tools_menu.add_command(label="Batch Create...", command=lambda: show_batch_create(self))
        tools_menu.add_command(label="Create Custom Structure...", command=lambda: create_custom_structure(self))
        tools_menu.add_command(label="Manage Custom Structures...", command=lambda: manage_structures(self))
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        help_menu.add_command(label="Tutorial", command=lambda: show_tutorial(self))
        help_menu.add_command(label="About", command=lambda: show_about(self))
    
    def filter_templates(self, *args):
        """Filter templates based on search term and category"""
        # Just call populate_template_gallery which handles filtering internally
        populate_template_gallery(self)
    
    def update_recent_templates_gallery(self):
        """Update the recent templates gallery"""
        # Clear existing cards
        for card in self.recent_template_cards:
            card.destroy()
        
        self.recent_template_cards = []
        
        # Get recent templates
        templates = self.recent_templates
        
        if not templates:
            # Show message when no recent templates
            msg_frame = tk.Frame(self.recent_templates_frame, bg=colors["bg"])
            msg_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
            
            msg = tk.Label(msg_frame, 
                         text="No recent templates. Templates will appear here after you use them.",
                         bg=colors["bg"], fg=colors["text"])
            msg.pack(pady=20)
            
            # Add to cards to enable clearing
            self.recent_template_cards.append(msg_frame)
            return
        
        # Add template cards
        for template in templates:
            # Handle both string paths and dictionary templates
            if isinstance(template, str):
                template_path = template
            elif isinstance(template, dict):
                template_path = template.get('path', '')
            else:
                # Skip invalid entries
                continue
            
            # Check if the template file exists
            if not template_path or not os.path.exists(template_path):
                continue
                
            # Create a card for each recent template
            card = TemplateFileCard(
                self.recent_templates_frame,
                template_path,
                select_callback=lambda path=template_path: use_recent_template(self, {'path': path} if isinstance(path, str) else path),
                remove_callback=lambda path=template_path: remove_from_recent_templates(self, path)
            )
            card.pack(fill=X, padx=5, pady=5, anchor=NW)
            
            # Add to list for later reference
            self.recent_template_cards.append(card)
        
        # After adding all cards, apply highlighting for the selected template
        if hasattr(self, 'selected_template_file') and self.selected_template_file:
            self._highlight_in_gallery(self.selected_template_file)
    
    def get_output_dir(self):
        """Open directory dialog to select output location"""
        directory = filedialog.askdirectory(title="Select Output Location")
        if directory:
            self.root_path = directory
            
            # Save to config
            config = load_config()
            config["last_directory"] = directory
            save_config(config)
            
            # Update display
            display_path = truncate_path(directory)
            if hasattr(self, 'output_path'):
                self.output_path.config(text=display_path)
            
            # Update status message
            self.status_var.set(f"Output location set to: {directory}")
            
            return directory
        return None
    
    def get_current_output_dir(self):
        """Get the current output directory path"""
        output_dir_type = getattr(self, 'output_dir_type', StringVar(value="default"))
        
        if output_dir_type.get() == "custom" and hasattr(self, 'custom_dir_var'):
            custom_dir = self.custom_dir_var.get()
            if custom_dir and os.path.isdir(custom_dir):
                return custom_dir
            
        # If the root path is set, use that
        if hasattr(self, 'root_path') and self.root_path and os.path.isdir(self.root_path):
            return self.root_path
        
        # Return an empty string if no location is set
        if not self.paths["output_dir"] or not os.path.isdir(self.paths["output_dir"]):
            return ""
        
        # Return default if set
        return self.paths["output_dir"]
    
    def update_recent_menu(self):
        """Update the recent projects menu with the list of recent projects"""
        # Clear the menu
        self.recent_menu.delete(0, tk.END)
        
        if not self.recent_projects:
            self.recent_menu.add_command(label="No Recent Projects", state=DISABLED)
            return
            
        # Add each recent project
        for project in self.recent_projects:
            # Truncate path for display
            display_path = truncate_path(project, max_length=50)
            
            # Add command to open the project
            self.recent_menu.add_command(
                label=display_path, 
                command=lambda p=project: open_recent_project(self, p)
            )
    
    def load_config(self):
        """Load application configuration"""
        load_app_config(self)
    
    def load_recent_projects(self):
        """Load recent projects"""
        load_app_recent_projects(self)
    
    def load_recent_templates(self):
        """Load recent templates"""
        load_app_recent_templates(self)
    
    def reset_form(self):
        """Reset the form to default state"""
        # Clear template selections
        clear_template_file(self)
        clear_structure_template(self)
        
        # Reset form fields
        if hasattr(self, 'project_name_var'):
            self.project_name_var.set("")
            
        if hasattr(self, 'output_dir_type'):
            self.output_dir_type.set("default")
            
        if hasattr(self, 'custom_dir_var'):
            self.custom_dir_var.set("")
            
        # Reset dropdown selections
        if hasattr(self, 'structure_var'):
            self.structure_var.set("Default")
            
        if hasattr(self, 'category_var'):
            self.category_var.set("All Categories")
            
        # Clear search
        if hasattr(self, 'search_var'):
            self.search_var.set("")
            
        # Update structure dropdown
        if hasattr(self, 'structure_dropdown'):
            update_structure_dropdown(self)
            
        # Refresh template gallery
        populate_template_gallery(self)
    
    def _highlight_in_gallery(self, template_path):
        """Highlight the selected template in the gallery"""
        # Reset all cards
        for card in self.template_cards:
            self._reset_card(card)
        
        for card in self.recent_template_cards:
            self._reset_card(card)
        
        # Ensure template_path is a string for comparison
        if isinstance(template_path, dict):
            template_path = template_path.get("path", "")
        
        # Define highlight colors for better visual effect
        highlight_border = colors["highlight_border"]  # Bright blue outline
        highlight_bg = colors["highlight_bg"]      # Darker blue fill
        highlight_text = colors["highlight_text"]  # White text
        
        # Highlight the selected card
        for cards in [self.template_cards, self.recent_template_cards]:
            for card in cards:
                if isinstance(card, TemplateFileCard) and card.template_path == template_path:
                    # Mark card as highlighted
                    card.is_highlighted = True
                    
                    # Set border and background of card frame
                    card.card_frame.configure(
                        bg=highlight_bg,
                        highlightbackground=highlight_border,
                        highlightthickness=2
                    )
                    
                    # Set colors of all child elements
                    card.icon_label.configure(bg=highlight_bg, fg=highlight_text)
                    card.info_frame.configure(bg=highlight_bg)
                    
                    # Update info frame contents with white text
                    for widget in card.info_frame.winfo_children():
                        widget.configure(bg=highlight_bg, fg=highlight_text)
                    
                    # Make sure remove button stays visible on highlighted cards
                    if hasattr(card, 'remove_btn_frame'):
                        card.remove_btn_frame.configure(bg=highlight_bg)
                        
                    if hasattr(card, 'remove_btn'):
                        card.remove_btn.configure(bg=highlight_bg, fg="white")
                    
                    break
    
    def _reset_card(self, card):
        """Reset card styling to default"""
        if not isinstance(card, TemplateFileCard):
            return
        
        # Mark card as not highlighted
        card.is_highlighted = False
        
        # Reset card frame styling - border should match background
        card.card_frame.configure(
            bg=colors["card_bg"],
            highlightbackground=colors["card_bg"],
            highlightthickness=1
        )
        
        # Reset all child elements
        card.icon_label.configure(bg=colors["card_bg"], fg=colors["text"])
        card.info_frame.configure(bg=colors["card_bg"])
        
        # Reset text colors appropriately
        card.name_label.configure(bg=colors["card_bg"], fg=colors["text"])
        card.path_label.configure(bg=colors["card_bg"], fg=colors["secondary_text"])
        
        # Reset remove button if it exists
        if hasattr(card, 'remove_btn_frame'):
            card.remove_btn_frame.configure(bg=colors["card_bg"])
            
        if hasattr(card, 'remove_btn'):
            card.remove_btn.configure(bg=colors["card_bg"], fg="white")
    
    def trigger_template_updated(self):
        """Called when templates have been updated"""
        # Refresh the template gallery
        populate_template_gallery(self)
        
        # Update structure dropdown
        update_structure_dropdown(self)
        
        # Update the menu
        self.update_recent_templates_menu()
    
    def update_recent_templates_menu(self):
        """Update the recent templates menu"""
        # Clear the menu
        self.recent_templates_menu.delete(0, tk.END)
        
        if not self.recent_templates:
            self.recent_templates_menu.add_command(label="No Recent Templates", state=DISABLED)
            return
            
        # Add each recent template
        for template in self.recent_templates:
            # Handle both string paths and dictionary templates
            if isinstance(template, str):
                template_path = template
                display_name = os.path.basename(template)
            elif isinstance(template, dict):
                template_path = template.get('path', '')
                display_name = template.get('name') or os.path.basename(template_path)
            else:
                continue  # Skip invalid entries
            
            # Add command to use the template
            self.recent_templates_menu.add_command(
                label=display_name, 
                command=lambda p=template: use_recent_template(self, p)
            )
    
    def on_resize(self, event):
        """Handle window resize events"""
        # Only respond to root window resizes
        if event.widget != self.root:
            return
            
        # Get current time to throttle expensive operations
        current_time = time.time()
        
        # Only perform expensive operations occasionally during resize
        # Store the last resize time as an attribute if it doesn't exist
        if not hasattr(self, '_last_resize_time'):
            self._last_resize_time = 0
            
        # Skip expensive operations if we've resized recently (throttle to once per 0.5 seconds)
        if current_time - self._last_resize_time < 0.5:
            return
            
        # Update the last resize time
        self._last_resize_time = current_time
            
        # Update layout based on new window size
        width = event.width
        
        # Adjust the layout of responsive elements
        if hasattr(self, 'template_gallery_frame'):
            if hasattr(self.template_gallery_frame, 'update_scrollregion'):
                self.template_gallery_frame.update_scrollregion()
            
        if hasattr(self, 'recent_templates_frame'):
            if hasattr(self.recent_templates_frame, 'update_scrollregion'):
                self.recent_templates_frame.update_scrollregion()
            
        # Force refresh of the enhanced template gallery - but only after resize is complete
        # We'll use root.after to delay this until resizing stops
        if hasattr(self, '_resize_timer_id'):
            self.root.after_cancel(self._resize_timer_id)
            
        def delayed_gallery_update():
            # Only refresh if needed
            if hasattr(self, 'template_manager_enhanced') and hasattr(self, 'template_list_frame'):
                try:
                    from app.templates.template_gallery_ui import populate_enhanced_gallery
                    populate_enhanced_gallery(self)
                except Exception as e:
                    print(f"Error refreshing gallery on resize: {e}")
        
        # Schedule gallery update for 300ms after resize stops
        self._resize_timer_id = self.root.after(300, delayed_gallery_update)
    
    def show_status_message(self, message, message_type="info", duration=5000):
        """
        Display a message in the status bar with appropriate color coding.
        
        Parameters:
        - message: The message to display
        - message_type: "error" (red), "success" (green), "warning" (yellow), or "info" (default)
        - duration: How long to show the colored message before reverting (in ms)
        """
        if not hasattr(self, 'status_bar') or not hasattr(self, 'status_var'):
            print(f"Status message (no UI): {message}")
            return
            
        # Define colors for different message types
        message_colors = {
            "error": {"bg": "#FF3333", "fg": "#FFFFFF"},     # Bright red with white text
            "success": {"bg": "#33CC33", "fg": "#FFFFFF"},   # Bright green with white text
            "warning": {"bg": "#FFCC00", "fg": "#000000"},   # Bright yellow with black text
            "info": {"bg": colors["card_bg"], "fg": colors["text"]}  # Default theme colors
        }
        
        # Set message text with prefix
        prefix = ""
        if message_type == "error":
            prefix = "⚠️ Error: "
        elif message_type == "success":
            prefix = "✓ Success! "
        elif message_type == "warning":
            prefix = "⚠️ Warning: "
            
        # Update the message text
        self.status_var.set(f"{prefix}{message}")
        
        # Get colors for this message type
        style = message_colors.get(
            message_type, 
            {"bg": colors["card_bg"], "fg": colors["text"]}
        )
        
        # Apply colors directly to the widget
        self.status_bar.config(bg=style["bg"], fg=style["fg"])
        
        # Force immediate update
        self.status_bar.update_idletasks()
        self.root.update_idletasks()
        
        # Reset after delay if not an info message
        if message_type != "info":
            self.root.after(duration, self._reset_status_bar)
    
    def _reset_status_bar(self):
        """Reset the status bar to its default appearance"""
        if hasattr(self, 'status_bar'):
            self.status_bar.config(bg=colors["card_bg"], fg=colors["text"])
            self.status_bar.update_idletasks()
            self.root.update_idletasks()
    
    def check_for_updates(self):
        """Check for application updates"""
        # This is a placeholder for update checking functionality
        # In a real application, this would connect to a server to check for updates
        
        def update_check_complete():
            # This function would be called when the update check is complete
            pass
        
        # Simulate an asynchronous update check
        self.root.after(1000, update_check_complete)


if __name__ == "__main__":
    # Enable HiDPI awareness
    setup_dpi_awareness()
    
    # Create root window
    root = tk.Tk()
    
    # Create application
    app = ProjectCreatorApp(root)
    
    # Run the application
    root.mainloop()
