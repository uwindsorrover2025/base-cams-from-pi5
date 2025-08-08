#!/usr/bin/env python3
"""
Photo Gallery Module
Viewer for browsing captured photos
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from PIL import Image, ImageTk
from datetime import datetime
import glob
from typing import List, Tuple, Optional
import threading
import shutil

class PhotoGallery(tk.Toplevel):
    def __init__(self, parent, photos_directory: str = "./captures"):
        """
        Initialize photo gallery window
        
        Args:
            parent: Parent window
            photos_directory: Directory containing photos
        """
        super().__init__(parent)
        
        self.parent = parent
        self.photos_directory = photos_directory
        self.photos = []
        self.current_page = 0
        self.photos_per_page = 12
        self.thumbnail_size = (150, 112)  # 4:3 aspect ratio
        self.selected_photos = set()
        
        # Window setup
        self.title("Photo Gallery")
        self.geometry("1000x700")
        self.minsize(800, 600)
        
        # Create UI
        self._create_widgets()
        
        # Load photos
        self.refresh_gallery()
        
        # Center window
        self._center_window()
        
    def _center_window(self):
        """Center the window on screen"""
        self.update_idletasks()
        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Get window dimensions
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        
        # Calculate position
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.geometry(f"+{x}+{y}")
        
    def _create_widgets(self):
        """Create gallery widgets"""
        # Toolbar
        toolbar = ttk.Frame(self, relief=tk.RAISED, borderwidth=1)
        toolbar.pack(fill=tk.X, padx=2, pady=2)
        
        # Sort options
        ttk.Label(toolbar, text="Sort:").pack(side=tk.LEFT, padx=(10, 5))
        self.sort_var = tk.StringVar(value="Date")
        sort_combo = ttk.Combobox(
            toolbar,
            textvariable=self.sort_var,
            values=["Date", "Name", "Camera"],
            width=10,
            state="readonly"
        )
        sort_combo.pack(side=tk.LEFT, padx=(0, 20))
        sort_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_gallery())
        
        # Filter options
        ttk.Label(toolbar, text="Filter:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_var = tk.StringVar(value="All Cameras")
        self.filter_combo = ttk.Combobox(
            toolbar,
            textvariable=self.filter_var,
            values=["All Cameras", "Camera 1", "Camera 2", "Camera 3"],
            width=15,
            state="readonly"
        )
        self.filter_combo.pack(side=tk.LEFT, padx=(0, 20))
        self.filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_gallery())
        
        # Separator
        ttk.Separator(toolbar, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Action buttons
        self.delete_button = ttk.Button(
            toolbar,
            text="Delete Selected",
            command=self._delete_selected,
            state='disabled'
        )
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        self.export_button = ttk.Button(
            toolbar,
            text="Export Selected",
            command=self._export_selected,
            state='disabled'
        )
        self.export_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar,
            text="Refresh",
            command=self.refresh_gallery
        ).pack(side=tk.LEFT, padx=5)
        
        # Main content area
        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollable photo grid
        self.canvas = tk.Canvas(content_frame, bg='white')
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status bar
        self.status_frame = ttk.Frame(self, relief=tk.SUNKEN, borderwidth=1)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(self.status_frame, text="")
        self.status_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        # Page navigation
        self.page_frame = ttk.Frame(self.status_frame)
        self.page_frame.pack(side=tk.RIGHT, padx=10, pady=2)
        
        # Bind mouse wheel for scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def refresh_gallery(self):
        """Refresh the photo gallery"""
        # Clear current photos
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        self.selected_photos.clear()
        self._update_action_buttons()
        
        # Load photos in background
        thread = threading.Thread(target=self._load_photos_thread, daemon=True)
        thread.start()
        
    def _load_photos_thread(self):
        """Load photos in background thread"""
        try:
            # Get all image files
            patterns = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
            all_photos = []
            
            for pattern in patterns:
                files = glob.glob(os.path.join(self.photos_directory, pattern))
                all_photos.extend(files)
                
            # Apply filter
            filter_value = self.filter_var.get()
            if filter_value != "All Cameras":
                camera_num = filter_value.split()[-1]
                all_photos = [p for p in all_photos if f"cam{camera_num}" in os.path.basename(p)]
                
            # Sort photos
            sort_value = self.sort_var.get()
            if sort_value == "Date":
                all_photos.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            elif sort_value == "Name":
                all_photos.sort(key=lambda x: os.path.basename(x))
            elif sort_value == "Camera":
                all_photos.sort(key=lambda x: self._extract_camera_number(x))
                
            self.photos = all_photos
            
            # Update UI in main thread
            self.after(0, self._display_photos)
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Failed to load photos: {str(e)}"))
            
    def _extract_camera_number(self, filepath: str) -> int:
        """Extract camera number from filename"""
        basename = os.path.basename(filepath)
        if "cam1" in basename:
            return 1
        elif "cam2" in basename:
            return 2
        elif "cam3" in basename:
            return 3
        return 0
        
    def _display_photos(self):
        """Display photos in grid"""
        if not self.photos:
            label = ttk.Label(
                self.scrollable_frame,
                text="No photos found",
                font=('TkDefaultFont', 14),
                foreground='gray'
            )
            label.pack(pady=50)
            self.status_label.config(text="0 photos")
            return
            
        # Create photo grid
        row = 0
        col = 0
        max_cols = 4
        
        for i, photo_path in enumerate(self.photos):
            # Create photo frame
            photo_frame = self._create_photo_frame(photo_path, i)
            photo_frame.grid(row=row, column=col, padx=10, pady=10)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
        # Update status
        self.status_label.config(text=f"{len(self.photos)} photos")
        
    def _create_photo_frame(self, photo_path: str, index: int) -> ttk.Frame:
        """Create a single photo frame with thumbnail"""
        frame = ttk.Frame(self.scrollable_frame, relief=tk.RAISED, borderwidth=1)
        
        # Selection checkbox
        var = tk.BooleanVar()
        checkbox = ttk.Checkbutton(
            frame,
            variable=var,
            command=lambda: self._toggle_selection(index, var.get())
        )
        checkbox.pack(anchor=tk.W, padx=5, pady=2)
        
        try:
            # Load and create thumbnail
            image = Image.open(photo_path)
            image.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            # Photo label
            photo_label = tk.Label(frame, image=photo, cursor="hand2")
            photo_label.image = photo  # Keep a reference
            photo_label.pack(padx=5, pady=5)
            
            # Bind click to view full size
            photo_label.bind("<Button-1>", lambda e: self._view_full_size(photo_path))
            
        except Exception as e:
            # Show error placeholder
            error_label = tk.Label(
                frame,
                text="Error loading\nimage",
                width=20,
                height=8,
                bg='lightgray'
            )
            error_label.pack(padx=5, pady=5)
            
        # Photo info
        basename = os.path.basename(photo_path)
        timestamp = datetime.fromtimestamp(os.path.getmtime(photo_path))
        
        # Extract camera info
        if "cam1" in basename:
            camera = "Camera 1"
        elif "cam2" in basename:
            camera = "Camera 2"
        elif "cam3" in basename:
            camera = "Camera 3"
        else:
            camera = "Unknown"
            
        info_text = f"{camera}\n{timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        info_label = ttk.Label(frame, text=info_text, font=('TkDefaultFont', 9))
        info_label.pack(padx=5, pady=(0, 5))
        
        return frame
        
    def _toggle_selection(self, index: int, selected: bool):
        """Toggle photo selection"""
        if selected:
            self.selected_photos.add(index)
        else:
            self.selected_photos.discard(index)
            
        self._update_action_buttons()
        
    def _update_action_buttons(self):
        """Update action button states"""
        if self.selected_photos:
            self.delete_button.config(state='normal')
            self.export_button.config(state='normal')
        else:
            self.delete_button.config(state='disabled')
            self.export_button.config(state='disabled')
            
    def _view_full_size(self, photo_path: str):
        """View photo in full size"""
        viewer = FullSizeViewer(self, photo_path)
        
    def _delete_selected(self):
        """Delete selected photos"""
        if not self.selected_photos:
            return
            
        count = len(self.selected_photos)
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete {count} photo(s)?"
        )
        
        if result:
            deleted = 0
            for index in sorted(self.selected_photos, reverse=True):
                if index < len(self.photos):
                    try:
                        os.remove(self.photos[index])
                        deleted += 1
                    except Exception as e:
                        print(f"Error deleting {self.photos[index]}: {e}")
                        
            messagebox.showinfo("Delete Complete", f"Deleted {deleted} photo(s)")
            self.refresh_gallery()
            
    def _export_selected(self):
        """Export selected photos"""
        if not self.selected_photos:
            return
            
        # Ask for export directory
        export_dir = filedialog.askdirectory(
            parent=self,
            title="Select Export Directory"
        )
        
        if export_dir:
            exported = 0
            for index in self.selected_photos:
                if index < len(self.photos):
                    try:
                        src = self.photos[index]
                        dst = os.path.join(export_dir, os.path.basename(src))
                        shutil.copy2(src, dst)
                        exported += 1
                    except Exception as e:
                        print(f"Error exporting {src}: {e}")
                        
            messagebox.showinfo("Export Complete", f"Exported {exported} photo(s) to {export_dir}")


class FullSizeViewer(tk.Toplevel):
    """Full size photo viewer window"""
    
    def __init__(self, parent, photo_path: str):
        super().__init__(parent)
        
        self.photo_path = photo_path
        
        # Window setup
        self.title(os.path.basename(photo_path))
        self.geometry("800x600")
        
        # Create UI
        self._create_widgets()
        
        # Load and display photo
        self._load_photo()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        # Bind keys
        self.bind('<Escape>', lambda e: self.destroy())
        
    def _create_widgets(self):
        """Create viewer widgets"""
        # Scrollable canvas
        self.canvas = tk.Canvas(self, bg='black')
        h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        self.canvas.configure(
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set
        )
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure grid weights
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
    def _load_photo(self):
        """Load and display the photo"""
        try:
            # Load image
            image = Image.open(self.photo_path)
            photo = ImageTk.PhotoImage(image)
            
            # Display on canvas
            self.canvas.create_image(0, 0, anchor="nw", image=photo)
            self.canvas.image = photo  # Keep a reference
            
            # Update scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load photo: {str(e)}")
            self.destroy()


# Example usage for testing
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test Main Window")
    root.geometry("400x300")
    
    def show_gallery():
        gallery = PhotoGallery(root)
        
    ttk.Button(root, text="Open Gallery", command=show_gallery).pack(pady=50)
    
    root.mainloop()