#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import platform
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, StringVar, BooleanVar
from tkinter.constants import *
import time

from app.core.app_config import (APP_NAME, APP_VERSION, colors, setup_dpi_awareness,
                      RECENT_TEMPLATES_MAX)
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
        
        # Initialize the application
        initialize_app(self)
        
        # Create the UI
        create_ui(self)
        
        # Create the menu
        self.create_menu()
        
        # Set application icon
        self.set_app_icon()
        
        # Check for updates
        self.root.after(2000, self.check_for_updates)
    
    def _update_ui_from_config(self):
        """Update UI elements based on config values"""
        # Update advanced options visibility
        advanced_value = self.config.get("show_advanced_options", False)
        self.advanced_options_visible.set(advanced_value)
        
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
        
        view_menu.add_checkbutton(label="Advanced Options", variable=self.advanced_options_visible, command=self.toggle_advanced)
        
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
    
    def toggle_advanced(self):
        """Toggle visibility of advanced options"""
        # Update config
        self.config["show_advanced_options"] = self.advanced_options_visible.get()
        save_config(self.config)
        
        # Ensure that the advanced section is visible if enabled
        def ensure_visibility():
            # Find any parent ScrollableFrame
            for widget in self.advanced_frame.winfo_children():
                parent = widget
                while parent:
                    if hasattr(parent, "update_scrollregion"):
                        parent.update_scrollregion()
                        break
                    parent = parent.master
        
        # Execute after a short delay to ensure UI has been updated
        self.root.after(100, ensure_visibility)
        
        # Show or hide the advanced options section
        if self.advanced_options_visible.get():
            self.advanced_frame.pack(fill=X, padx=20, pady=(0, 20), after=self.basic_frame)
            
            # Ensure scrollable containers update their scroll region
            for frame in [self.template_gallery_frame, self.recent_templates_frame]:
                if hasattr(frame, "update_scrollregion"):
                    frame.update_scrollregion()
        else:
            self.advanced_frame.pack_forget()
            
    def filter_templates(self, *args):
        """Filter templates based on search term and category"""
        search_term = self.search_var.get() if hasattr(self, 'search_var') else ""
        category = self.category_var.get() if hasattr(self, 'category_var') else None
        
        if category == "All Categories":
            category = None
            
        # Update the template gallery with filtered templates
        populate_template_gallery(self, search_term, category)
    
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
            msg_frame = tk.Frame(self.recent_templates_container, bg=colors["bg"])
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
                self.recent_templates_container,
                template_path,
                select_callback=lambda path=template_path: use_recent_template(self, {'path': path} if isinstance(path, str) else path),
                remove_callback=lambda path=template_path: remove_from_recent_templates(self, path)
            )
            card.pack(fill=X, padx=5, pady=5, anchor=NW)
            
            # Add to list for later reference
            self.recent_template_cards.append(card)
            
        # Highlight card if it matches current selection
        if hasattr(self, 'selected_template_file') and self.selected_template_file:
            self._highlight_in_gallery(self.selected_template_file)
    
    def get_output_dir(self):
        """Get the output directory, either default or user selected"""
        output_dir_type = getattr(self, 'output_dir_type', StringVar(value="default"))
        
        if output_dir_type.get() == "custom" and hasattr(self, 'custom_dir_var'):
            custom_dir = self.custom_dir_var.get()
            if custom_dir and os.path.isdir(custom_dir):
                return custom_dir
                
        # Return default if custom not set or invalid
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
            
        # Reset advanced options
        if hasattr(self, 'advanced_options_visible'):
            self.advanced_options_visible.set(False)
            self.toggle_advanced()
            
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
        for template_path in self.recent_templates:
            # Get filename for display
            display_name = os.path.basename(template_path)
            
            # Add command to use the template
            self.recent_templates_menu.add_command(
                label=display_name, 
                command=lambda p=template_path: use_recent_template(self, p)
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
                    from template_gallery_ui import populate_enhanced_gallery
                    populate_enhanced_gallery(self)
                except Exception as e:
                    print(f"Error refreshing gallery on resize: {e}")
        
        # Schedule gallery update for 300ms after resize stops
        self._resize_timer_id = self.root.after(300, delayed_gallery_update)
    
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
