#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from typing import Dict, List, Any, Optional, Callable, Union
import logging
import threading
import time
import os
import json

# Set up logging
logger = logging.getLogger(__name__)

class LazyLoader:
    """
    Implements lazy loading for application resources.
    Loads items only when needed, improving startup time and memory usage.
    """
    
    def __init__(self):
        self._cache = {}
        self._loading_status = {}
        self._load_callbacks = {}
    
    def register_lazy_resource(self, resource_id: str, loader_func: Callable, 
                              max_age: Optional[int] = None) -> None:
        """
        Register a resource for lazy loading
        
        Args:
            resource_id: Identifier for the resource
            loader_func: Function to call to load the resource
            max_age: Maximum age in seconds before resource should be reloaded (None = no expiry)
        """
        self._cache[resource_id] = {
            "data": None,
            "loader": loader_func,
            "max_age": max_age,
            "last_loaded": None
        }
        logger.debug(f"Registered lazy resource: {resource_id}")
    
    def get_resource(self, resource_id: str, force_reload: bool = False) -> Any:
        """
        Get a resource, loading it if needed
        
        Args:
            resource_id: Identifier for the resource
            force_reload: Whether to force reload the resource
            
        Returns:
            The loaded resource or None if not available yet
        """
        if resource_id not in self._cache:
            logger.warning(f"Attempted to access unregistered resource: {resource_id}")
            return None
        
        resource = self._cache[resource_id]
        
        # Check if resource needs loading
        if (resource["data"] is None or force_reload or 
            (resource["max_age"] is not None and resource["last_loaded"] is not None and 
             time.time() - resource["last_loaded"] > resource["max_age"])):
            
            # If not already loading, start loading
            if resource_id not in self._loading_status or not self._loading_status[resource_id]:
                self._loading_status[resource_id] = True
                thread = threading.Thread(target=self._load_resource, args=(resource_id,))
                thread.daemon = True
                thread.start()
                logger.debug(f"Started loading resource: {resource_id}")
            
            # Return existing data (might be None) while loading
            return resource["data"]
        
        return resource["data"]
    
    def _load_resource(self, resource_id: str) -> None:
        """
        Load a resource in a background thread
        
        Args:
            resource_id: Identifier for the resource
        """
        try:
            resource = self._cache[resource_id]
            data = resource["loader"]()
            
            # Update cache
            resource["data"] = data
            resource["last_loaded"] = time.time()
            
            logger.debug(f"Successfully loaded resource: {resource_id}")
            
            # Call callbacks
            if resource_id in self._load_callbacks:
                for callback in self._load_callbacks[resource_id]:
                    try:
                        callback(data)
                    except Exception as e:
                        logger.error(f"Error in callback for {resource_id}: {e}")
        except Exception as e:
            logger.error(f"Error loading resource {resource_id}: {e}")
        finally:
            self._loading_status[resource_id] = False
    
    def register_load_callback(self, resource_id: str, callback: Callable) -> bool:
        """
        Register a callback to be called when a resource is loaded
        
        Args:
            resource_id: Identifier for the resource
            callback: Function to call when resource is loaded
            
        Returns:
            True if callback was registered, False if resource doesn't exist
        """
        if resource_id not in self._cache:
            logger.warning(f"Attempted to register callback for unregistered resource: {resource_id}")
            return False
        
        if resource_id not in self._load_callbacks:
            self._load_callbacks[resource_id] = []
        
        self._load_callbacks[resource_id].append(callback)
        
        # If resource is already loaded, call callback immediately
        if self._cache[resource_id]["data"] is not None:
            try:
                callback(self._cache[resource_id]["data"])
            except Exception as e:
                logger.error(f"Error in immediate callback for {resource_id}: {e}")
        
        return True
    
    def preload_resource(self, resource_id: str) -> bool:
        """
        Trigger loading of a resource ahead of time
        
        Args:
            resource_id: Identifier for the resource
            
        Returns:
            True if preload was started, False if resource doesn't exist
        """
        if resource_id not in self._cache:
            logger.warning(f"Attempted to preload unregistered resource: {resource_id}")
            return False
        
        # Start loading if not already loading
        if resource_id not in self._loading_status or not self._loading_status[resource_id]:
            self.get_resource(resource_id)
            return True
        
        return False


class BatchResourceLoader:
    """
    Handles loading of resources in batches to improve performance.
    Useful for loading multiple templates or files in a directory.
    """
    
    def __init__(self, batch_size: int = 10):
        """
        Initialize the batch loader
        
        Args:
            batch_size: Number of items to load in each batch
        """
        self.batch_size = batch_size
        self._items_to_load = []
        self._is_loading = False
        self._load_complete_callbacks = []
        self._batch_complete_callbacks = []
        self._item_load_callbacks = []
    
    def add_items(self, items: List[Dict[str, Any]], 
                 loader_func: Callable[[Dict[str, Any]], Any]) -> None:
        """
        Add items to be loaded in batches
        
        Args:
            items: List of items to load
            loader_func: Function to call to load each item
        """
        for item in items:
            self._items_to_load.append({
                "item": item,
                "loader": loader_func,
                "loaded": False,
                "data": None
            })
        
        logger.debug(f"Added {len(items)} items to batch loader, total: {len(self._items_to_load)}")
    
    def start_loading(self) -> None:
        """Start the batch loading process"""
        if self._is_loading:
            logger.debug("Batch loading already in progress")
            return
        
        self._is_loading = True
        thread = threading.Thread(target=self._load_batches)
        thread.daemon = True
        thread.start()
        logger.debug("Started batch loading process")
    
    def _load_batches(self) -> None:
        """Load items in batches"""
        try:
            unloaded_items = [item for item in self._items_to_load if not item["loaded"]]
            total_items = len(unloaded_items)
            items_loaded = 0
            batch_num = 0
            
            logger.debug(f"Starting to load {total_items} items in batches of {self.batch_size}")
            
            while unloaded_items:
                # Get next batch
                batch = unloaded_items[:self.batch_size]
                unloaded_items = unloaded_items[self.batch_size:]
                batch_num += 1
                
                logger.debug(f"Loading batch {batch_num} with {len(batch)} items")
                
                # Load each item in the batch
                for item_data in batch:
                    try:
                        item = item_data["item"]
                        loader = item_data["loader"]
                        data = loader(item)
                        
                        # Store loaded data
                        item_data["data"] = data
                        item_data["loaded"] = True
                        items_loaded += 1
                        
                        # Call item load callbacks
                        for callback in self._item_load_callbacks:
                            try:
                                callback(item, data)
                            except Exception as e:
                                logger.error(f"Error in item load callback: {e}")
                    except Exception as e:
                        logger.error(f"Error loading item in batch: {e}")
                
                # Call batch complete callbacks
                for callback in self._batch_complete_callbacks:
                    try:
                        callback(batch_num, items_loaded, total_items)
                    except Exception as e:
                        logger.error(f"Error in batch complete callback: {e}")
                
                # Add a short delay between batches to avoid hogging resources
                time.sleep(0.05)
            
            logger.debug(f"Completed loading {items_loaded} items in {batch_num} batches")
            
            # Call load complete callbacks
            for callback in self._load_complete_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in load complete callback: {e}")
        except Exception as e:
            logger.error(f"Error in batch loading process: {e}")
        finally:
            self._is_loading = False
    
    def on_load_complete(self, callback: Callable[[], None]) -> None:
        """
        Register a callback to be called when all items are loaded
        
        Args:
            callback: Function to call when loading is complete
        """
        self._load_complete_callbacks.append(callback)
    
    def on_batch_complete(self, callback: Callable[[int, int, int], None]) -> None:
        """
        Register a callback to be called when a batch is loaded
        
        Args:
            callback: Function to call when a batch is loaded (batch_num, items_loaded, total_items)
        """
        self._batch_complete_callbacks.append(callback)
    
    def on_item_loaded(self, callback: Callable[[Dict[str, Any], Any], None]) -> None:
        """
        Register a callback to be called when an item is loaded
        
        Args:
            callback: Function to call when an item is loaded (item, data)
        """
        self._item_load_callbacks.append(callback)
    
    def get_loaded_items(self) -> List[Dict[str, Any]]:
        """
        Get all loaded items
        
        Returns:
            List of loaded items with their data
        """
        return [{"item": item["item"], "data": item["data"]} 
                for item in self._items_to_load if item["loaded"]]
    
    def get_load_progress(self) -> Dict[str, int]:
        """
        Get the loading progress
        
        Returns:
            Dictionary with total, loaded, and remaining counts
        """
        total = len(self._items_to_load)
        loaded = sum(1 for item in self._items_to_load if item["loaded"])
        return {
            "total": total,
            "loaded": loaded,
            "remaining": total - loaded,
            "percent": round(loaded / total * 100) if total > 0 else 100
        }


# Singleton instances for global use
lazy_loader = LazyLoader()
template_loader = BatchResourceLoader(batch_size=5)
structure_loader = BatchResourceLoader(batch_size=3)

def optimize_template_loading(template_manager):
    """
    Set up lazy loading for templates
    
    Args:
        template_manager: The TemplateManager instance
    """
    # Register template loading function
    lazy_loader.register_lazy_resource(
        "all_templates", 
        template_manager.get_all_templates,
        max_age=60  # Reload every minute if requested
    )
    
    # Register structure loading function
    lazy_loader.register_lazy_resource(
        "custom_structures",
        lambda: template_manager.custom_structures,
        max_age=60
    )
    
    logger.info("Template and structure lazy loading optimizations applied")
    
    # Use a safer approach for preloading in the background
    def safe_preload(resource_id):
        try:
            lazy_loader.preload_resource(resource_id)
        except Exception as e:
            logger.warning(f"Error preloading resource {resource_id}: {e}")
    
    # Start preloading templates in the background
    template_thread = threading.Thread(target=safe_preload, args=("all_templates",))
    template_thread.daemon = True  # Make thread exit when main thread exits
    
    structures_thread = threading.Thread(target=safe_preload, args=("custom_structures",))
    structures_thread.daemon = True
    
    # Start threads with a slight delay to allow UI to initialize first
    timer = threading.Timer(1.0, lambda: template_thread.start())
    timer.daemon = True
    timer.start()
    
    timer2 = threading.Timer(1.5, lambda: structures_thread.start())
    timer2.daemon = True
    timer2.start()


def optimize_file_io(base_dir):
    """
    Optimize file I/O operations for the given directory
    
    Args:
        base_dir: Base directory for optimization
    """
    # Define optimized JSON loading function with caching
    json_cache = {}
    
    def optimized_load_json(file_path, max_age=30):
        """Optimized JSON loading with caching"""
        if file_path in json_cache:
            cache_time, data = json_cache[file_path]
            if time.time() - cache_time < max_age:
                return data
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            json_cache[file_path] = (time.time(), data)
            return data
        except Exception as e:
            logger.error(f"Error loading JSON file {file_path}: {e}")
            return None
    
    # Register the optimized function globally
    import app.utils.utils
    app.utils.utils.optimized_load_json = optimized_load_json
    
    logger.info(f"File I/O optimizations applied for {base_dir}") 