#!/usr/bin/env python3
"""
ArUco Detection Display Window
Separate window to display ArUco detection results for judges
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Dict, List, Optional
from aruco_detector import ArUcoDetection

class ArUcoDisplayWindow(tk.Toplevel):
    def __init__(self, parent):
        """
        Initialize ArUco detection display window
        
        Args:
            parent: Parent window
        """
        super().__init__(parent)
        
        self.parent = parent
        self.title("ArUco Marker Detection Display")
        self.geometry("800x600")
        
        # Make window stay on top for judges
        self.attributes('-topmost', True)
        
        # Detection data
        self.detections: Dict[int, Dict[int, ArUcoDetection]] = {0: {}, 1: {}, 2: {}}
        self.update_lock = threading.Lock()
        
        # Create UI
        self._create_widgets()
        
        # Start update loop
        self.update_display()
        
        # Handle close event
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
    def _create_widgets(self):
        """Create display widgets"""
        # Title
        title_label = ttk.Label(
            self,
            text="ArUco Marker Detection Results",
            font=('TkDefaultFont', 16, 'bold')
        )
        title_label.pack(pady=10)
        
        # Main frame with scrollbar
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Canvas for scrollable content
        canvas = tk.Canvas(main_frame, bg='white')
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas = canvas
        
        # Camera sections
        self.camera_frames = {}
        for cam_id in range(3):
            frame = self._create_camera_section(cam_id)
            frame.pack(fill=tk.X, padx=5, pady=5)
            self.camera_frames[cam_id] = frame
            
        # Summary section
        self.summary_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text="Detection Summary",
            padding="10"
        )
        self.summary_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.summary_label = ttk.Label(
            self.summary_frame,
            text="No markers detected",
            font=('TkDefaultFont', 12)
        )
        self.summary_label.pack()
        
        # Timestamp
        self.timestamp_label = ttk.Label(
            self,
            text="",
            font=('TkDefaultFont', 10),
            foreground='gray'
        )
        self.timestamp_label.pack(pady=5)
        
    def _create_camera_section(self, camera_id: int) -> ttk.LabelFrame:
        """Create section for camera detections"""
        frame = ttk.LabelFrame(
            self.scrollable_frame,
            text=f"Camera {camera_id + 1}",
            padding="10"
        )
        
        # Table for detections
        columns = ('Marker ID', 'Position', 'Distance', 'Last Seen')
        tree = ttk.Treeview(frame, columns=columns, height=4, show='headings')
        
        # Configure columns
        tree.heading('Marker ID', text='Marker ID')
        tree.heading('Position', text='Position (x,y)')
        tree.heading('Distance', text='Distance (cm)')
        tree.heading('Last Seen', text='Last Seen')
        
        tree.column('Marker ID', width=100)
        tree.column('Position', width=150)
        tree.column('Distance', width=120)
        tree.column('Last Seen', width=150)
        
        tree.pack(fill=tk.X)
        
        # Store reference
        frame.tree = tree
        
        return frame
        
    def update_detections(self, camera_id: int, detections: Dict[int, ArUcoDetection]):
        """
        Update detections for a camera
        
        Args:
            camera_id: Camera identifier
            detections: Dictionary of marker_id to detection
        """
        with self.update_lock:
            self.detections[camera_id] = detections.copy()
            
    def update_display(self):
        """Update the display with latest detections"""
        try:
            with self.update_lock:
                all_markers = set()
                
                # Update each camera section
                for cam_id, frame in self.camera_frames.items():
                    tree = frame.tree
                    
                    # Clear existing items
                    for item in tree.get_children():
                        tree.delete(item)
                        
                    # Add current detections
                    detections = self.detections.get(cam_id, {})
                    for marker_id, detection in detections.items():
                        all_markers.add(marker_id)
                        
                        # Format data
                        position = f"({detection.center[0]}, {detection.center[1]})"
                        distance = f"{detection.distance:.1f}" if detection.distance > 0 else "N/A"
                        last_seen = time.strftime(
                            "%H:%M:%S", 
                            time.localtime(detection.timestamp)
                        )
                        
                        # Insert row
                        tree.insert('', 'end', values=(
                            marker_id,
                            position,
                            distance,
                            last_seen
                        ))
                        
                # Update summary
                if all_markers:
                    summary_text = f"Total unique markers detected: {len(all_markers)}\n"
                    summary_text += f"Marker IDs: {', '.join(map(str, sorted(all_markers)))}"
                else:
                    summary_text = "No markers currently detected"
                    
                self.summary_label.config(text=summary_text)
                
                # Update timestamp
                self.timestamp_label.config(
                    text=f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
        except Exception as e:
            print(f"Error updating ArUco display: {e}")
            
        # Schedule next update
        self.after(100, self.update_display)  # 10Hz update rate
        
    def _on_close(self):
        """Handle window close"""
        # Don't actually close, just hide
        self.withdraw()
        
    def show(self):
        """Show the window"""
        self.deiconify()
        self.lift()
        self.attributes('-topmost', True)
        
    def hide(self):
        """Hide the window"""
        self.withdraw()


class ArUcoStatusPanel(ttk.Frame):
    """
    Small status panel to embed in main GUI
    Shows brief ArUco detection status
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.detections = {0: {}, 1: {}, 2: {}}
        
        # Create widgets
        self._create_widgets()
        
    def _create_widgets(self):
        """Create status panel widgets"""
        # Title
        title = ttk.Label(
            self,
            text="ArUco Status",
            font=('TkDefaultFont', 10, 'bold')
        )
        title.pack(anchor=tk.W)
        
        # Status labels for each camera
        self.camera_labels = {}
        for cam_id in range(3):
            label = ttk.Label(
                self,
                text=f"Cam {cam_id + 1}: No markers",
                font=('TkDefaultFont', 9)
            )
            label.pack(anchor=tk.W, padx=(10, 0))
            self.camera_labels[cam_id] = label
            
        # Total markers label
        self.total_label = ttk.Label(
            self,
            text="Total markers: 0",
            font=('TkDefaultFont', 9, 'bold')
        )
        self.total_label.pack(anchor=tk.W, pady=(5, 0))
        
    def update_status(self, camera_id: int, detections: Dict[int, ArUcoDetection]):
        """Update status for a camera"""
        self.detections[camera_id] = detections
        
        # Update camera label
        marker_count = len(detections)
        if marker_count > 0:
            marker_ids = sorted(detections.keys())
            text = f"Cam {camera_id + 1}: {marker_count} markers ({', '.join(map(str, marker_ids))})"
        else:
            text = f"Cam {camera_id + 1}: No markers"
            
        self.camera_labels[camera_id].config(text=text)
        
        # Update total
        all_markers = set()
        for cam_detections in self.detections.values():
            all_markers.update(cam_detections.keys())
            
        self.total_label.config(text=f"Total unique markers: {len(all_markers)}")


# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test Main Window")
    root.geometry("400x300")
    
    # Create display window
    display = ArUcoDisplayWindow(root)
    
    # Create status panel
    status = ArUcoStatusPanel(root)
    status.pack(padx=10, pady=10)
    
    # Test button
    def show_display():
        display.show()
        
    ttk.Button(root, text="Show ArUco Display", command=show_display).pack(pady=10)
    
    # Simulate some detections
    import numpy as np
    from aruco_detector import ArUcoDetection
    
    def simulate_detection():
        # Create fake detection
        detection = ArUcoDetection(
            marker_id=42,
            corners=np.array([[0, 0], [100, 0], [100, 100], [0, 100]]),
            center=(50, 50),
            distance=30.5,
            timestamp=time.time(),
            camera_id=0
        )
        
        display.update_detections(0, {42: detection})
        status.update_status(0, {42: detection})
        
        # Schedule next simulation
        root.after(2000, simulate_detection)
        
    # Start simulation
    root.after(1000, simulate_detection)
    
    root.mainloop()