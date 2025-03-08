#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter.constants import *

# Import from our centralized color scheme instead of app_config
from app.ui.color_scheme import colors, CARD_NORMAL, CARD_HOVER, CARD_SELECTED
from app.ui.ui_components import ToolTip, ScrollableFrame, SearchBox, CardFrame
from app.templates.enhanced_template_card import TemplateCardEnhanced
from app.templates.template_folder_card import TemplateFolderCard
from app.templates.add_template_canvas import AddTemplateCanvas
from app.templates.enhanced_template_manager import TemplateManagerEnhanced
from app.templates.template_category_manager import TemplateCategoryManager
from dialog.template_dialogs import edit_template_dialog, manage_templates_dialog, create_new_category, create_new_folder
from app.ui.app_ui import run_import_dialog

# Use the blue highlight color from our color scheme
BLUE_HIGHLIGHT = colors["highlight_bg"]

class CanvasButton(tk.Canvas):
    """
    A canvas-based button with consistent styling for the template gallery
    """
    def __init__(self, parent, text="", icon=None, width=80, height=30, callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Set fixed size
        self.configure(width=width, height=height, highlightthickness=0, bg=colors["card_bg"])
        
        # Create a rounded rectangle button with a blue background
        self.blue_bg = self.create_rectangle(2, 2, width-2, height-2, fill=BLUE_HIGHLIGHT, outline="", width=0)
        
        # Round the corners by creating small arcs
        corner_radius = 5
        # Top-left corner
        self.create_arc(2, 2, 2+corner_radius*2, 2+corner_radius*2, start=90, extent=90, fill=BLUE_HIGHLIGHT, outline="")
        # Top-right corner
        self.create_arc(width-2-corner_radius*2, 2, width-2, 2+corner_radius*2, start=0, extent=90, fill=BLUE_HIGHLIGHT, outline="")
        # Bottom-left corner
        self.create_arc(2, height-2-corner_radius*2, 2+corner_radius*2, height-2, start=180, extent=90, fill=BLUE_HIGHLIGHT, outline="")
        # Bottom-right corner
        self.create_arc(width-2-corner_radius*2, height-2-corner_radius*2, width-2, height-2, start=270, extent=90, fill=BLUE_HIGHLIGHT, outline="")
        
        # Add the text
        if text:
            self.text_id = self.create_text(width//2, height//2, text=text, fill="white", font=("Segoe UI", 10))
        
        # Add icon if provided instead of text
        if icon:
            if icon == "+":
                # Add the plus symbol
                self.plus_h = self.create_line(width//2-6, height//2, width//2+6, height//2, fill="white", width=2)
                self.plus_v = self.create_line(width//2, height//2-6, width//2, height//2+6, fill="white", width=2)
            elif icon == "gear":
                # Simple gear icon
                gear_radius = 8
                self.create_oval(width//2-gear_radius, height//2-gear_radius, 
                               width//2+gear_radius, height//2+gear_radius, 
                               outline="white", width=1.5)
                for i in range(8):
                    angle = i * 45 * 3.14159 / 180
                    x1 = width//2 + (gear_radius-2) * 0.8 * 0.707 * (i % 2 + 1) * (1 if i < 4 else -1)
                    y1 = height//2 + (gear_radius-2) * 0.8 * 0.707 * (i % 2 + 1) * (1 if i < 2 or (i > 3 and i < 6) else -1)
                    self.create_line(width//2, height//2, x1, y1, fill="white", width=1.5)
            elif icon == "hamburger":
                # Hamburger menu icon (3 horizontal lines)
                line_width = 10
                # Top line
                self.create_line(width//2-line_width//2, height//2-5, 
                               width//2+line_width//2, height//2-5, 
                               fill="white", width=1.5)
                # Middle line
                self.create_line(width//2-line_width//2, height//2, 
                               width//2+line_width//2, height//2, 
                               fill="white", width=1.5)
                # Bottom line
                self.create_line(width//2-line_width//2, height//2+5, 
                               width//2+line_width//2, height//2+5, 
                               fill="white", width=1.5)
            elif icon == "folder":
                # Simple folder icon
                self.create_rectangle(width//2-8, height//2-4, width//2+8, height//2+5, outline="white", width=1.5)
                self.create_line(width//2-8, height//2-4, width//2-4, height//2-7, width//2+8, height//2-7, fill="white", width=1.5)
        
        # Bind click event
        if callback:
            self.bind("<Button-1>", lambda e: callback())
            # Change cursor to hand when hovering
            self.bind("<Enter>", self.on_enter)
            self.bind("<Leave>", self.on_leave)
    
    def on_enter(self, event):
        """Handle mouse enter event"""
        self.configure(cursor="hand2")
        # Slightly darker blue on hover
        self.itemconfig(self.blue_bg, fill="#36648B")  # Darker blue
    
    def on_leave(self, event):
        """Handle mouse leave event"""
        self.configure(cursor="")
        # Restore original color
        self.itemconfig(self.blue_bg, fill=BLUE_HIGHLIGHT)

def create_template_gallery_enhanced(app):
    """
    Create an enhanced template gallery with folder support and better organization
    """
    # Create template manager wrapper if needed
    if not hasattr(app, 'template_manager_enhanced'):
        app.template_manager_enhanced = TemplateManagerEnhanced(app.template_manager)
        app.category_manager = TemplateCategoryManager(app.template_manager)
    
    # Find the parent frame (template gallery container)
    parent_frame = None
    
    # First try to find it through the app's templates_card (created in app_ui.py)
    if hasattr(app, 'templates_card') and app.templates_card is not None:
        parent_frame = app.templates_card
    
    # If not found, look for it through the template_list_frame
    if parent_frame is None and hasattr(app, 'template_list_frame') and app.template_list_frame is not None:
        parent_frame = app.template_list_frame.master
    
    # If still not found, search for it in the UI
    if parent_frame is None:
        # Look for right_panel which should contain the template gallery
        for widget in app.root.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Frame):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, tk.Frame):
                                for card in grandchild.winfo_children():
                                    if isinstance(card, CardFrame) or (hasattr(card, 'title_label') and 
                                                                     hasattr(card.title_label, 'cget') and 
                                                                     'Template Gallery' in card.title_label.cget('text')):
                                        parent_frame = card
                                        break
    
    # If we still didn't find it, use the right panel or create a new frame
    if parent_frame is None:
        print("Warning: Could not find template gallery container. Creating a new one.")
        # Find or create right panel
        content_frame = None
        for widget in app.root.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Frame) and len(child.winfo_children()) >= 2:
                        content_frame = child
                        break
        
        if content_frame:
            # Assume the second child is the right panel
            right_panel = content_frame.winfo_children()[1]
            # Create a new card frame
            parent_frame = CardFrame(right_panel, title="File Structure Templates")
            parent_frame.pack(fill=BOTH, expand=True)
        else:
            # Last resort - create a new top-level window
            parent_frame = tk.Toplevel(app.root)
            parent_frame.title("File Structure Templates")
            parent_frame.geometry("600x500")
    
    # Store reference to the parent frame
    app.templates_card = parent_frame
    
    # COMPLETELY REMOVE THE OLD FILTER FRAME
    if hasattr(app, 'filter_frame'):
        try:
            for widget in app.filter_frame.winfo_children():
                widget.destroy()
            app.filter_frame.destroy()  # Actually destroy the frame itself
            delattr(app, 'filter_frame')  # Remove the attribute from app
        except Exception as e:
            print(f"Warning: Error cleaning up filter_frame: {e}")
    
    # Clean up any old controls frames
    for attr in ['top_controls_frame', 'bottom_controls_frame']:
        if hasattr(app, attr):
            try:
                getattr(app, attr).destroy()
                delattr(app, attr)
            except Exception as e:
                print(f"Warning: Error cleaning up {attr}: {e}")
    
    # Clear all widgets in parent_frame to start fresh
    try:
        for widget in parent_frame.winfo_children():
            widget.destroy()
    except Exception as e:
        print(f"Warning: Error clearing parent_frame: {e}")
    
    # Create a completely fresh UI structure
    
    # Create a title frame at the top
    title_frame = tk.Frame(parent_frame, bg=colors["card_bg"], height=40)
    title_frame.pack(fill=X, side=TOP, pady=(5, 0))
    
    # Add a custom title label (don't rely on CardFrame's title)
    title_label = tk.Label(title_frame, text="File Structure Templates", font=("Segoe UI", 14, "bold"),
                          bg=colors["card_bg"], fg=colors["text"])
    title_label.pack(side=LEFT, padx=10, pady=5)
    
    # Create the controls frame right below the title
    app.top_controls_frame = tk.Frame(parent_frame, bg=colors["card_bg"], height=45)
    app.top_controls_frame.pack(fill=X, side=TOP, pady=(0, 5), padx=5)
    
    # Control buttons frame (right side) - create this FIRST to ensure buttons get priority
    button_frame = tk.Frame(app.top_controls_frame, bg=colors["card_bg"])
    button_frame.pack(side=RIGHT, padx=(0, 5))
    
    # Button container for canvas buttons - highest priority
    canvas_button_frame = tk.Frame(button_frame, bg=colors["card_bg"])
    canvas_button_frame.pack(side=RIGHT, padx=(10, 0))
    
    # Create folder button
    folder_btn = CanvasButton(canvas_button_frame, icon="folder", width=30, height=30,
                            callback=lambda: create_new_folder(app))
    folder_btn.pack(side=LEFT, padx=(5, 0))
    ToolTip(folder_btn, "Create Folder")
    
    # Add template button
    add_btn = CanvasButton(canvas_button_frame, icon="+", width=30, height=30,
                         callback=lambda: run_import_dialog(app))
    add_btn.pack(side=LEFT, padx=(5, 0))
    ToolTip(add_btn, "Add Template")
    
    # Manage button
    manage_btn = CanvasButton(canvas_button_frame, icon="hamburger", width=30, height=30,
                            callback=lambda: manage_templates_dialog(app))
    manage_btn.pack(side=LEFT, padx=(5, 0))
    ToolTip(manage_btn, "Manage Templates")
    
    # Category filter button - medium priority
    category_frame = tk.Frame(button_frame, bg=colors["card_bg"])
    category_frame.pack(side=RIGHT, padx=(5, 0))
    
    category_label = tk.Label(category_frame, text="Category:", bg=colors["card_bg"], fg=colors["text"])
    category_label.pack(side=LEFT)
    
    app.category_var = tk.StringVar(value="All")
    categories = ["All"] + app.category_manager.get_all_categories()
    
    category_menu = ttk.OptionMenu(category_frame, app.category_var, "All", *categories, 
                                 command=lambda x: app.filter_templates())
    category_menu.pack(side=LEFT, padx=(5, 0))
    
    # Folder filter button
    folder_frame = tk.Frame(button_frame, bg=colors["card_bg"])
    folder_frame.pack(side=RIGHT, padx=(10, 0))
    
    folder_label = tk.Label(folder_frame, text="Folder:", bg=colors["card_bg"], fg=colors["text"])
    folder_label.pack(side=LEFT)
    
    app.folder_var = tk.StringVar(value="All")
    folders = ["All"] + list(app.template_manager_enhanced.folders.keys())
    
    folder_menu = ttk.OptionMenu(folder_frame, app.folder_var, "All", *folders, 
                               command=lambda x: app.filter_templates())
    folder_menu.pack(side=LEFT, padx=(5, 0))
    
    # Search box - lowest priority (can shrink if needed)
    app.search_box = SearchBox(app.top_controls_frame, callback=app.filter_templates)
    app.search_box.pack(side=LEFT, fill=X, expand=True, padx=(5, 10))
    
    # Add a separator line
    separator = tk.Frame(parent_frame, height=1, bg=colors["secondary_text"])
    separator.pack(fill=X, padx=5, pady=(0, 5))
    
    # Create the template list frame AFTER the controls and separator
    if hasattr(app, 'template_list_frame'):
        try:
            app.template_list_frame.destroy()
        except Exception as e:
            print(f"Warning: Error destroying old template_list_frame: {e}")
    
    app.template_list_frame = ScrollableFrame(parent_frame, bg=colors["card_bg"])
    app.template_list_frame.pack(fill=BOTH, expand=True, pady=(0, 5), padx=5)
    
    # Populate with templates
    populate_enhanced_gallery(app)
    
    # Force UI update to ensure the gallery is rendered immediately
    app.root.update_idletasks()


def populate_enhanced_gallery(app):
    """Populate the enhanced gallery with templates and folders"""
    try:
        # Make sure the template list frame exists and is visible
        if not hasattr(app, 'template_list_frame') or not app.template_list_frame:
            print("Error: template_list_frame not found")
            return
        
        # Clear existing templates
        for widget in app.template_list_frame.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Get appropriate templates based on filters
        templates = filter_templates_enhanced(app)
        
        # Display message if no templates
        if not templates:
            no_templates_label = tk.Label(app.template_list_frame.scrollable_frame, 
                                        text="No templates found", font=("Segoe UI", 11),
                                        bg=colors["card_bg"], fg=colors["text"])
            no_templates_label.pack(pady=20)
            # Force UI update
            app.root.update_idletasks()
            return
        
        # Define dark text for better contrast on blue
        dark_text = "#FFFFFF"  # White text for better visibility on blue
        
        # If folder is selected, show folder contents
        folder = app.folder_var.get() if hasattr(app, 'folder_var') else "All"
        if folder != "All" and folder in app.template_manager_enhanced.folders:
            # Show folder header with back button
            folder_header = tk.Frame(app.template_list_frame.scrollable_frame, bg=colors["card_bg"])
            folder_header.pack(fill=X, pady=(0, 10))
            
            back_btn = CanvasButton(folder_header, text="←", width=30, height=30,
                                  callback=lambda: back_to_all_folders(app))
            back_btn.pack(side=LEFT)
            
            folder_title = tk.Label(folder_header, text=f"Folder: {folder}", font=("Segoe UI", 11, "bold"),
                                  bg=colors["card_bg"], fg=colors["text"])
            folder_title.pack(side=LEFT, padx=10)
            
            # Show only templates in this folder
            templates = app.template_manager_enhanced.get_folder_templates(folder)
        
        # Create template cards
        for template in templates:
            card = create_template_card_enhanced(
                app.template_list_frame.scrollable_frame, 
                template,
                app
            )
            card.pack(fill=X, pady=5, padx=5)
            
            # Force fixed height for consistency
            card.config(height=80)
            
            # Explicitly add hover effects to the card and all its children
            if not hasattr(card, '_on_hover_enter') or not hasattr(card, '_on_hover_leave'):
                # Define hover effect functions if they don't exist
                def _on_hover_enter(event, card=card):
                    # Skip if card is already highlighted (has blue highlight)
                    if hasattr(card, 'is_highlighted') and card.is_highlighted:
                        return
                    if card.cget("bg") == colors["highlight_bg"]:
                        return
                    
                    # Use hover bg that matches left side structure template
                    hover_bg = "#303030"  # Match hover effect from app_ui.py
                    
                    # Update card and all its components
                    card.configure(bg=hover_bg, highlightbackground=hover_bg)
                    
                    # Update icon label if it exists
                    if hasattr(card, 'icon_label'):
                        card.icon_label.configure(bg=hover_bg)
                    
                    # Update info frame and all its children
                    if hasattr(card, 'info_frame'):
                        card.info_frame.configure(bg=hover_bg)
                        for widget in card.info_frame.winfo_children():
                            widget.configure(bg=hover_bg)
                    
                    # Update action frame if it exists
                    if hasattr(card, 'action_frame'):
                        card.action_frame.configure(bg=hover_bg)
                        
                        # Update canvas buttons if they exist
                        for child in card.action_frame.winfo_children():
                            if hasattr(child, 'update_background'):
                                child.update_background(hover_bg)
                            else:
                                child.configure(bg=hover_bg)
                    
                    # Set cursor
                    card.configure(cursor="hand2")
                
                def _on_hover_leave(event, card=card):
                    # Skip if card is highlighted with blue
                    if hasattr(card, 'is_highlighted') and card.is_highlighted:
                        return
                    if card.cget("bg") == colors["highlight_bg"]:
                        return
                    
                    # Reset to regular background using colors that match left side
                    bg = colors["bg"]  # Match structure template bg color
                    
                    # Update card and all its components
                    card.configure(bg=bg, highlightbackground=bg)
                    
                    # Update icon label if it exists
                    if hasattr(card, 'icon_label'):
                        card.icon_label.configure(bg=bg, fg=colors["text"])
                    
                    # Update info frame and all its children
                    if hasattr(card, 'info_frame'):
                        card.info_frame.configure(bg=bg)
                        
                        # Reset all child widgets with appropriate colors
                        if hasattr(card, 'name_label'):
                            card.name_label.configure(bg=bg, fg=colors["text"])
                        if hasattr(card, 'category_label'):
                            card.category_label.configure(bg=bg, fg=colors["secondary_text"])
                        if hasattr(card, 'desc_label'):
                            card.desc_label.configure(bg=bg, fg=colors["text"])
                    
                    # Update action frame if it exists
                    if hasattr(card, 'action_frame'):
                        card.action_frame.configure(bg=bg)
                        
                        # Reset canvas buttons if they exist
                        for child in card.action_frame.winfo_children():
                            if hasattr(child, 'update_background'):
                                child.update_background(bg)
                            else:
                                child.configure(bg=bg)
                    
                    # Reset cursor
                    card.configure(cursor="")
                
                # Attach these methods to the card
                card._on_hover_enter = _on_hover_enter
                card._on_hover_leave = _on_hover_leave
            
            # Bind hover events to card
            card.bind("<Enter>", card._on_hover_enter)
            card.bind("<Leave>", card._on_hover_leave)
            
            # Also bind hover events to card's children
            if hasattr(card, 'icon_label'):
                card.icon_label.bind("<Enter>", card._on_hover_enter)
                card.icon_label.bind("<Leave>", card._on_hover_leave)
            
            if hasattr(card, 'info_frame'):
                card.info_frame.bind("<Enter>", card._on_hover_enter)
                card.info_frame.bind("<Leave>", card._on_hover_leave)
                
                for widget in card.info_frame.winfo_children():
                    widget.bind("<Enter>", card._on_hover_enter)
                    widget.bind("<Leave>", card._on_hover_leave)
            
            # Also bind to action frame if it exists
            if hasattr(card, 'action_frame'):
                card.action_frame.bind("<Enter>", card._on_hover_enter)
                card.action_frame.bind("<Leave>", card._on_hover_leave)
            
            # Immediately apply the non-hover style to all cards
            # This ensures the initial style is correct before any interactions
            card._on_hover_leave(None)
            
            # Highlight if this is the currently selected template
            if hasattr(app, 'current_template') and app.current_template and template == app.current_template:
                # Mark card as highlighted to prevent hover effects
                card.is_highlighted = True
                
                # Apply highlight colors matching the left side structure template
                # These values match the highlight_current_structure function in structures.py
                highlight_bg = "#2C4F76"  # Darker blue fill
                highlight_border = "#4682B4"  # Bright blue outline
                highlight_text = "white"  # Text color
                
                # Update card with highlight styling
                card.configure(
                    bg=highlight_bg, 
                    highlightbackground=highlight_border,
                    highlightthickness=2
                )
                
                # Update the icon label
                if hasattr(card, 'icon_label'):
                    card.icon_label.configure(bg=highlight_bg, fg=highlight_text)
                
                # Update the info frame and all its contents
                if hasattr(card, 'info_frame'):
                    card.info_frame.configure(bg=highlight_bg)
                    
                    # Update all info frame widgets with highlight text for contrast
                    for widget in card.info_frame.winfo_children():
                        widget.configure(bg=highlight_bg, fg=highlight_text)
                
                # Update action frame if it exists
                if hasattr(card, 'action_frame'):
                    card.action_frame.configure(bg=highlight_bg)
                    
                    # Update canvas buttons if they exist
                    for child in card.action_frame.winfo_children():
                        if hasattr(child, 'update_background'):
                            child.update_background(highlight_bg)
                        else:
                            child.configure(bg=highlight_bg)
                
                # Force UI update to ensure changes are applied immediately
                card.update()
        
        # Update scrollregion to ensure all templates are visible
        app.template_list_frame.update_scrollregion()
        
        # Force UI update to ensure all template cards are rendered immediately
        app.root.update_idletasks()
            
    except Exception as e:
        print(f"Error populating enhanced gallery: {e}")
        import traceback
        traceback.print_exc()


def filter_templates_enhanced(app):
    """Filter templates based on search, category and folder"""
    search_term = app.search_box.get() if hasattr(app, 'search_box') else ""
    category = app.category_var.get() if hasattr(app, 'category_var') else "All"
    folder = app.folder_var.get() if hasattr(app, 'folder_var') else "All"
    
    # Start with all templates
    templates = app.template_manager.templates
    
    # Apply folder filter first
    if folder != "All" and folder in app.template_manager_enhanced.folders:
        # If we're explicitly showing a folder, we'll handle this in the populate function
        # to properly show the folder header
        pass
    
    # Apply search filter
    if search_term:
        search_term = search_term.lower()
        templates = [t for t in templates if 
                   search_term in t["name"].lower() or 
                   search_term in t.get("description", "").lower()]
    
    # Apply category filter
    if category and category != "All":
        templates = [t for t in templates if t["category"] == category]
    
    return templates


def create_template_card_enhanced(parent, template, app):
    """Create an enhanced template card with delete and edit capabilities"""
    card = TemplateCardEnhanced(
        parent, 
        template,
        select_callback=lambda t=template: select_template_from_gallery(app, t),
        delete_callback=lambda t=template: delete_template_confirm(app, t),
        edit_callback=lambda t=template: edit_template_dialog(app, t)
    )
    
    # Initial styling to match left side structure template
    card.configure(
        highlightbackground=colors["bg"],
        highlightthickness=1
    )
    
    return card


def select_template_from_gallery(app, template):
    """Select a template from the gallery"""
    # Store the selected template
    app.current_template = template
    
    # Set as current structure template if needed
    if hasattr(app, 'selected_structure_template'):
        app.selected_structure_template = template
    
    # Use highlight colors matching the left side structure template
    highlight_bg = "#2C4F76"  # Darker blue fill
    highlight_border = "#4682B4"  # Bright blue outline
    highlight_text = "white"  # Text color
    
    # Iterate through all template cards to update highlighting
    if hasattr(app, 'template_list_frame') and app.template_list_frame:
        # Make sure we have a scrollable frame
        if not hasattr(app.template_list_frame, 'scrollable_frame'):
            print("Error: template_list_frame does not have scrollable_frame")
            return
            
        # Find all template cards and update them
        for widget in app.template_list_frame.scrollable_frame.winfo_children():
            # Check if this is a template card
            if hasattr(widget, 'template') and widget.template == template:
                # This is the selected template - highlight it
                widget.is_highlighted = True
                
                # Apply highlight styling matching left side structure template
                widget.configure(
                    bg=highlight_bg, 
                    highlightbackground=highlight_border, 
                    highlightthickness=2
                )
                
                # Update the icon label if it exists
                if hasattr(widget, 'icon_label'):
                    widget.icon_label.configure(bg=highlight_bg, fg=highlight_text)
                
                # Update the info frame and all its children
                if hasattr(widget, 'info_frame'):
                    widget.info_frame.configure(bg=highlight_bg)
                    
                    # Apply white text to all children for better contrast
                    for child in widget.info_frame.winfo_children():
                        child.configure(bg=highlight_bg, fg=highlight_text)
                
                # Update action frame if it exists
                if hasattr(widget, 'action_frame'):
                    widget.action_frame.configure(bg=highlight_bg)
                    
                    # Update canvas buttons if they exist
                    for child in widget.action_frame.winfo_children():
                        if hasattr(child, 'update_background'):
                            child.update_background(highlight_bg)
                        else:
                            child.configure(bg=highlight_bg)
                
                # Force immediate UI update
                widget.update()
            elif hasattr(widget, 'template'):
                # This is not the selected template - reset highlighting
                widget.is_highlighted = False
                
                # Reset to regular styling matching the background color
                widget.configure(
                    bg=colors["bg"], 
                    highlightbackground=colors["bg"], 
                    highlightthickness=1
                )
                
                # Reset icon label if it exists
                if hasattr(widget, 'icon_label'):
                    widget.icon_label.configure(bg=colors["bg"], fg=colors["text"])
                
                # Reset info frame and all its children
                if hasattr(widget, 'info_frame'):
                    widget.info_frame.configure(bg=colors["bg"])
                    
                    # Reset text colors for all children
                    for child in widget.info_frame.winfo_children():
                        if 'name_label' in str(child):
                            child.configure(bg=colors["bg"], fg=colors["text"])
                        elif 'category_label' in str(child):
                            child.configure(bg=colors["bg"], fg=colors["secondary_text"])
                        elif 'desc_label' in str(child):
                            child.configure(bg=colors["bg"], fg=colors["text"])
                        else:
                            child.configure(bg=colors["bg"])
                
                # Reset action frame if it exists
                if hasattr(widget, 'action_frame'):
                    widget.action_frame.configure(bg=colors["bg"])
                    
                    # Reset canvas buttons if they exist
                    for child in widget.action_frame.winfo_children():
                        if hasattr(child, 'update_background'):
                            child.update_background(colors["bg"])
                        else:
                            child.configure(bg=colors["bg"])
                
                # Force immediate UI update
                widget.update()
    
    # Update the preview
    if hasattr(app, 'update_template_preview'):
        app.update_template_preview()


def delete_template_confirm(app, template):
    """Confirm and delete a template"""
    template_name = template["name"]
    
    # Confirm deletion
    confirm = messagebox.askyesno("Confirm Deletion", 
                                f"Are you sure you want to delete the template '{template_name}'?")
    if not confirm:
        return False
    
    # Delete the template
    success = app.template_manager.delete_template(template_name)
    
    if success:
        # Also remove from any folders
        for folder_name in app.template_manager_enhanced.folders:
            if template_name in app.template_manager_enhanced.folders[folder_name]:
                app.template_manager_enhanced.folders[folder_name].remove(template_name)
        
        # Save folder changes
        app.template_manager_enhanced.save_folders()
        
        # Reload template gallery
        populate_enhanced_gallery(app)
        
        # Update status
        app.status_var.set(f"Template '{template_name}' deleted")
        
        return True
    else:
        messagebox.showerror("Error", f"Failed to delete template '{template_name}'")
        return False


def back_to_all_folders(app):
    """Reset folder filter to show all templates"""
    if hasattr(app, 'folder_var'):
        app.folder_var.set("All")
        populate_enhanced_gallery(app)
        
        # Force UI update
        app.root.update_idletasks()
