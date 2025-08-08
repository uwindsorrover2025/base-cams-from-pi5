#!/usr/bin/env python3
"""
Photo Capture Dialog
Modal dialog for selecting cameras and capturing photos
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from typing import Dict, List, Optional, Callable
from datetime import datetime

class PhotoCaptureDialog(tk.Toplevel):
    def __init__(self, parent, camera_names: List[str], save_directory: str = "./captures"):
        """
        Initialize photo capture dialog
        
        Args:
            parent: Parent window
            camera_names: List of camera names
            save_directory: Default save directory
        """
        super().__init__(parent)
        
        self.parent = parent
        self.camera_names = camera_names
        self.save_directory = save_directory
        self.selected_cameras = []
        self.capture_callback = None
        
        # Window setup
        self.title("Capture Photo")
        self.geometry("350x400")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Create UI
        self._create_widgets()
        
        # Center window
        self._center_window()
        
    def _center_window(self):
        """Center the dialog on parent window"""
        self.update_idletasks()
        
        # Get parent position
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get dialog size
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        
        # Calculate position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f"+{x}+{y}")
        
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main frame with padding
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Select Cameras to Capture",
            font=('TkDefaultFont', 12, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Camera selection frame
        selection_frame = ttk.LabelFrame(main_frame, text="Cameras", padding="10")
        selection_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Camera checkboxes
        self.camera_vars = []
        for i, name in enumerate(self.camera_names):
            var = tk.BooleanVar(value=True)
            self.camera_vars.append(var)
            
            checkbox = ttk.Checkbutton(
                selection_frame,
                text=name,
                variable=var
            )
            checkbox.pack(anchor=tk.W, pady=5)
            
        # Select/Deselect all buttons
        button_frame = ttk.Frame(selection_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Select All",
            command=self._select_all,
            width=12
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            button_frame,
            text="Deselect All",
            command=self._deselect_all,
            width=12
        ).pack(side=tk.LEFT)
        
        # Save location frame
        location_frame = ttk.LabelFrame(main_frame, text="Save Location", padding="10")
        location_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Directory display
        self.dir_var = tk.StringVar(value=self.save_directory)
        dir_label = ttk.Label(
            location_frame,
            textvariable=self.dir_var,
            relief=tk.SUNKEN,
            padding="5"
        )
        dir_label.pack(fill=tk.X, pady=(0, 10))
        
        # Browse button
        ttk.Button(
            location_frame,
            text="Browse...",
            command=self._browse_directory
        ).pack()
        
        # Capture info
        info_label = ttk.Label(
            main_frame,
            text="Photos will be saved with timestamp filenames",
            foreground="gray"
        )
        info_label.pack(pady=(0, 10))
        
        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X)
        
        self.capture_button = ttk.Button(
            action_frame,
            text="Capture Selected",
            command=self._on_capture,
            width=15
        )
        self.capture_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            action_frame,
            text="Cancel",
            command=self._on_cancel,
            width=15
        ).pack(side=tk.LEFT)
        
        # Progress label (hidden initially)
        self.progress_label = ttk.Label(
            main_frame,
            text="",
            foreground="blue"
        )
        
        # Bind keys
        self.bind('<Return>', lambda e: self._on_capture())
        self.bind('<Escape>', lambda e: self._on_cancel())
        
    def _select_all(self):
        """Select all cameras"""
        for var in self.camera_vars:
            var.set(True)
            
    def _deselect_all(self):
        """Deselect all cameras"""
        for var in self.camera_vars:
            var.set(False)
            
    def _browse_directory(self):
        """Browse for save directory"""
        directory = filedialog.askdirectory(
            parent=self,
            title="Select Save Directory",
            initialdir=self.save_directory
        )
        
        if directory:
            self.save_directory = directory
            self.dir_var.set(directory)
            
    def _on_capture(self):
        """Handle capture button click"""
        # Get selected cameras
        self.selected_cameras = [
            i for i, var in enumerate(self.camera_vars) if var.get()
        ]
        
        if not self.selected_cameras:
            messagebox.showwarning(
                "No Selection",
                "Please select at least one camera to capture"
            )
            return
            
        # Create directory if it doesn't exist
        os.makedirs(self.save_directory, exist_ok=True)
        
        # Show progress
        self.capture_button.config(state='disabled')
        self.progress_label.pack(pady=(10, 0))
        self.progress_label.config(text="Capturing photos...")
        
        # Execute capture callback if set
        if self.capture_callback:
            self.after(100, self._execute_capture)
        else:
            self.destroy()
            
    def _execute_capture(self):
        """Execute the capture callback"""
        try:
            if self.capture_callback:
                self.capture_callback(self.selected_cameras, self.save_directory)
            self.progress_label.config(
                text=f"✓ Captured {len(self.selected_cameras)} photo(s)",
                foreground="green"
            )
            self.after(1000, self.destroy)
        except Exception as e:
            messagebox.showerror(
                "Capture Error",
                f"Failed to capture photos: {str(e)}"
            )
            self.capture_button.config(state='normal')
            self.progress_label.config(text="")
            
    def _on_cancel(self):
        """Handle cancel button click"""
        self.selected_cameras = []
        self.destroy()
        
    def set_capture_callback(self, callback: Callable):
        """Set callback function for capture action"""
        self.capture_callback = callback
        
    def get_selected_cameras(self) -> List[int]:
        """Get list of selected camera indices"""
        return self.selected_cameras
        
    def get_save_directory(self) -> str:
        """Get selected save directory"""
        return self.save_directory


# Example usage for testing
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test Main Window")
    root.geometry("600x400")
    
    def show_dialog():
        camera_names = ["Camera 1 (Living Room)", "Camera 2 (Kitchen)", "Camera 3 (Garage)"]
        
        dialog = PhotoCaptureDialog(root, camera_names)
        
        def capture_callback(cameras, directory):
            print(f"Capturing from cameras: {cameras}")
            print(f"Saving to: {directory}")
            # Simulate capture delay
            import time
            time.sleep(1)
            
        dialog.set_capture_callback(capture_callback)
        root.wait_window(dialog)
        
        print(f"Selected cameras: {dialog.get_selected_cameras()}")
        print(f"Save directory: {dialog.get_save_directory()}")
        
    ttk.Button(root, text="Open Capture Dialog", command=show_dialog).pack(pady=50)
    
    root.mainloop()