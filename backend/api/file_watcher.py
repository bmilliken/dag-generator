"""
File Watcher Service for DAG Generator

This module watches for changes in the projects directory and tracks
when files are modified, but doesn't automatically reload the DAG.
Instead, it provides information about pending changes.
"""

import os
import time
import threading
from typing import Set, Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent


class YamlFileHandler(FileSystemEventHandler):
    """Handler for YAML file system events."""
    
    def __init__(self, callback):
        """
        Initialize the handler.
        
        Args:
            callback: Function to call when a YAML file changes
        """
        self.callback = callback
        self._debounce_timers = {}
        self._lock = threading.Lock()
    
    def _should_process_file(self, file_path: str) -> bool:
        """Check if the file should be processed."""
        return (file_path.endswith('.yml') or file_path.endswith('.yaml')) and not file_path.startswith('.')
    
    def _debounced_callback(self, event_type: str, file_path: str):
        """Debounced callback to avoid multiple rapid calls for the same file."""
        with self._lock:
            # Cancel existing timer for this file
            if file_path in self._debounce_timers:
                self._debounce_timers[file_path].cancel()
            
            # Create new timer
            timer = threading.Timer(0.5, lambda: self.callback(event_type, file_path))
            self._debounce_timers[file_path] = timer
            timer.start()
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if not event.is_directory and self._should_process_file(event.src_path):
            self._debounced_callback('modified', event.src_path)
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation events."""
        if not event.is_directory and self._should_process_file(event.src_path):
            self._debounced_callback('created', event.src_path)
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion events."""
        if not event.is_directory and self._should_process_file(event.src_path):
            self._debounced_callback('deleted', event.src_path)


class FileWatcherService:
    """Service to watch for file changes and track pending updates."""
    
    def __init__(self):
        self.observer = None
        self.is_watching = False
        self.pending_changes: Set[str] = set()
        self.last_changes: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def _on_file_changed(self, event_type: str, file_path: str):
        """Handle file change events."""
        with self._lock:
            self.pending_changes.add(file_path)
            self.last_changes[file_path] = time.time()
            print(f"📁 File {event_type}: {file_path} (changes pending)")
    
    def has_pending_changes(self, project_name: str) -> bool:
        """Check if there are pending changes for a project."""
        projects_dir = self.get_projects_directory()
        project_path = os.path.join(projects_dir, project_name)
        
        with self._lock:
            return any(change.startswith(project_path) for change in self.pending_changes)
    
    def get_pending_changes(self, project_name: str = None) -> Set[str]:
        """Get list of pending changes, optionally filtered by project."""
        with self._lock:
            if project_name:
                projects_dir = self.get_projects_directory()
                project_path = os.path.join(projects_dir, project_name)
                return {change for change in self.pending_changes if change.startswith(project_path)}
            return self.pending_changes.copy()
    
    def clear_pending_changes(self, project_name: str = None):
        """Clear pending changes, optionally filtered by project."""
        with self._lock:
            if project_name:
                projects_dir = self.get_projects_directory()
                project_path = os.path.join(projects_dir, project_name)
                self.pending_changes = {
                    change for change in self.pending_changes 
                    if not change.startswith(project_path)
                }
            else:
                self.pending_changes.clear()
    
    def start_watching(self, directory: str):
        """Start watching a directory for changes."""
        if self.is_watching:
            self.stop_watching()
        
        if not os.path.exists(directory):
            print(f"Warning: Directory {directory} does not exist")
            return
        
        self.observer = Observer()
        handler = YamlFileHandler(self._on_file_changed)
        
        # Watch the directory recursively
        self.observer.schedule(handler, directory, recursive=True)
        
        try:
            self.observer.start()
            self.is_watching = True
            print(f"📁 Started watching directory: {directory}")
        except Exception as e:
            print(f"Error starting file watcher: {e}")
    
    def stop_watching(self):
        """Stop watching for file changes."""
        if self.observer and self.is_watching:
            self.observer.stop()
            self.observer.join()
            self.is_watching = False
            print("📁 Stopped file watching")
    
    def get_projects_directory(self) -> str:
        """Get the projects directory path."""
        # Check if we're running in Docker (projects mounted at /app/projects)
        if os.path.exists("/app/projects"):
            return "/app/projects"
        else:
            # Local development path
            return os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "projects")


# Global file watcher instance
file_watcher = FileWatcherService()
