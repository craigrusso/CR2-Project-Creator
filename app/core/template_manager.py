import os
import json

class TemplateManager:
    def load_templates(self, force_refresh=False):
        """
        Load templates from the templates directory.
        
        Args:
            force_refresh: Force a refresh of the templates.
            
        Returns:
            List of templates.
        """
        # Check if templates already loaded
        if not force_refresh and hasattr(self, 'loaded_templates') and self.loaded_templates:
            return self.loaded_templates
            
        print(f"[DEBUG] Template Manager: Loading templates{' (forced refresh)' if force_refresh else ''}")
        
        templates = []
        template_names = set()  # Use a set to track unique template names
        
        # Get templates directory
        templates_dir = self.get_templates_dir()
        
        if not os.path.exists(templates_dir):
            print(f"[WARNING] Template Manager: Templates directory not found: {templates_dir}")
            os.makedirs(templates_dir, exist_ok=True)
            
        # Load all JSON files from the templates directory
        if os.path.exists(templates_dir):
            for filename in os.listdir(templates_dir):
                if filename.endswith('.json'):
                    template_path = os.path.join(templates_dir, filename)
                    
                    try:
                        # Load template from file
                        with open(template_path, 'r', encoding='utf-8') as f:
                            template_data = json.load(f)
                            
                        # Skip if not a valid template
                        if not isinstance(template_data, dict):
                            print(f"[WARNING] Template Manager: Invalid template format in file: {filename}")
                            continue
                            
                        # Get or create template name
                        template_name = template_data.get('name')
                        if not template_name:
                            # Derive name from filename
                            template_name = os.path.splitext(filename)[0].replace('_', ' ')
                            template_data['name'] = template_name
                            
                        # Normalize the template name for comparison
                        normalized_name = template_name.strip().lower()
                        
                        # Skip duplicate templates
                        if normalized_name in template_names:
                            print(f"[WARNING] Template Manager: Skipping duplicate template: {template_name}")
                            continue
                            
                        # Add path to template data
                        template_data['path'] = template_path
                        
                        # Add to tracked names
                        template_names.add(normalized_name)
                        
                        # Add to templates list
                        templates.append(template_data)
                        print(f"[DEBUG] Template Manager: Loaded template: {template_name}")
                    except Exception as e:
                        print(f"[ERROR] Template Manager: Error loading template {filename}: {e}")
                        
        # Sort templates by name
        templates.sort(key=lambda t: t.get('name', '').lower())
        
        print(f"[INFO] Template Manager: Loaded {len(templates)} templates")
        self.loaded_templates = templates
        return templates
        
    def get_templates_dir(self):
        """
        Get the templates directory path.
        
        Returns:
            str: Path to templates directory.
        """
        # Use app_config or fallback to local path
        try:
            from app.core.app_config import AppConfig
            config = AppConfig.get_instance()
            return config.get_templates_dir()
        except ImportError:
            # Fallback to a default location if app_config not available
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            return os.path.join(base_dir, 'templates')
        except Exception as e:
            print(f"[ERROR] Template Manager: Error getting templates directory: {e}")
            # Fallback to a default location
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            return os.path.join(base_dir, 'templates') 