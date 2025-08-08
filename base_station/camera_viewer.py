#!/usr/bin/env python3
"""
Camera Viewer Widget
Custom Tkinter widget for displaying camera streams
"""

import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import numpy as np
import threading
import time
from typing import Optional, Callable

class CameraViewer(ttk.Frame):
    def __init__(self, parent, camera_id: int = 0, width: int = 640, height: int = 480, **kwargs):
        """
        Initialize camera viewer widget
        
        Args:
            parent: Parent widget
            camera_id: Camera identifier
            width: Display width
            height: Display height
        """
        super().__init__(parent, **kwargs)
        
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.current_frame = None
        self.is_active = False
        self.update_thread = None
        self.stream_manager = None
        self.overlay_manager = None
        self.aruco_detector = None
        self.camera_name = f"Camera {camera_id + 1}"
        self.enable_aruco = False
        
        # Callbacks
        self.on_double_click = None
        self.on_aruco_detection = None
        
        # Create UI elements
        self._create_widgets()
        
    def _create_widgets(self):
        """Create widget UI elements"""
        # Main frame with border
        self.main_frame = ttk.Frame(self, relief=tk.RIDGE, borderwidth=2)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Video display label
        self.video_label = tk.Label(
            self.main_frame,
            bg='black',
            width=self.width,
            height=self.height
        )
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # Status label
        self.status_label = ttk.Label(
            self.main_frame,
            text="Not Connected",
            anchor=tk.CENTER
        )
        self.status_label.pack(fill=tk.X, pady=2)
        
        # Bind double-click event
        self.video_label.bind("<Double-Button-1>", self._on_double_click)
        
        # Display placeholder
        self._show_placeholder()
        
    def _show_placeholder(self):
        """Show placeholder when no stream is active"""
        # Create black placeholder image
        placeholder = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Add text
        text = f"{self.camera_name} - No Signal"
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(text, font, 1, 2)[0]
        text_x = (self.width - text_size[0]) // 2
        text_y = (self.height + text_size[1]) // 2
        
        cv2.putText(placeholder, text, (text_x, text_y), font, 1, (128, 128, 128), 2)
        
        # Convert and display
        self._display_frame(placeholder)
        
    def set_stream_manager(self, stream_manager):
        """Set the stream manager instance"""
        self.stream_manager = stream_manager
        
    def set_overlay_manager(self, overlay_manager):
        """Set the overlay manager instance"""
        self.overlay_manager = overlay_manager
        
    def set_aruco_detector(self, aruco_detector):
        """Set the ArUco detector instance"""
        self.aruco_detector = aruco_detector
        
    def set_aruco_enabled(self, enabled: bool):
        """Enable or disable ArUco detection"""
        self.enable_aruco = enabled
        
    def set_camera_name(self, name: str):
        """Set camera display name"""
        self.camera_name = name
        
    def start_stream(self):
        """Start displaying the stream"""
        if self.stream_manager and not self.is_active:
            self.is_active = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            
    def stop_stream(self):
        """Stop displaying the stream"""
        self.is_active = False
        if self.update_thread:
            self.update_thread.join(timeout=1)
        self._show_placeholder()
        self.status_label.config(text="Not Connected")
        
    def _update_loop(self):
        """Update loop for displaying frames"""
        fps_timer = time.time()
        fps_counter = 0
        
        while self.is_active:
            try:
                if self.stream_manager and self.stream_manager.is_connected(self.camera_id):
                    # Get frame from stream
                    frame = self.stream_manager.get_frame(self.camera_id)
                    
                    if frame is not None:
                        # Detect ArUco markers if enabled
                        if self.enable_aruco and self.aruco_detector:
                            detections = self.aruco_detector.detect_markers(frame, self.camera_id)
                            
                            # Draw detections on frame
                            frame = self.aruco_detector.draw_detections(frame, detections)
                            
                            # Notify callback if detections found
                            if detections and self.on_aruco_detection:
                                self.on_aruco_detection(self.camera_id, detections)
                        
                        # Apply overlay if available
                        if self.overlay_manager:
                            frame = self.overlay_manager.add_overlay(frame, self.camera_name)
                            
                        # Store current frame
                        self.current_frame = frame.copy()
                        
                        # Resize frame if needed
                        if frame.shape[:2] != (self.height, self.width):
                            frame = cv2.resize(frame, (self.width, self.height))
                            
                        # Display frame
                        self._display_frame(frame)
                        
                        # Update FPS counter
                        fps_counter += 1
                        current_time = time.time()
                        if current_time - fps_timer >= 1.0:
                            stream_info = self.stream_manager.get_stream_info(self.camera_id)
                            if stream_info:
                                fps = stream_info.get('fps', 0)
                                self.status_label.config(text=f"Connected - {fps} FPS")
                            fps_counter = 0
                            fps_timer = current_time
                    else:
                        self.status_label.config(text="Waiting for frames...")
                        time.sleep(0.1)
                else:
                    self._show_placeholder()
                    self.status_label.config(text="Disconnected")
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"Error in camera viewer {self.camera_id}: {e}")
                time.sleep(0.5)
                
    def _display_frame(self, frame: np.ndarray):
        """Display a frame in the label"""
        try:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            image = Image.fromarray(frame_rgb)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image=image)
            
            # Update label
            self.video_label.config(image=photo)
            self.video_label.image = photo  # Keep a reference
            
        except Exception as e:
            print(f"Error displaying frame: {e}")
            
    def _on_double_click(self, event):
        """Handle double-click event"""
        if self.on_double_click:
            self.on_double_click(self.camera_id)
            
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the current displayed frame"""
        return self.current_frame.copy() if self.current_frame is not None else None
        
    def set_double_click_callback(self, callback: Callable):
        """Set callback for double-click events"""
        self.on_double_click = callback
        
    def set_aruco_callback(self, callback: Callable):
        """Set callback for ArUco detections"""
        self.on_aruco_detection = callback
        
    def update_size(self, width: int, height: int):
        """Update viewer size"""
        self.width = width
        self.height = height
        self.video_label.config(width=width, height=height)


# Example usage for testing
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Camera Viewer Test")
    
    viewer = CameraViewer(root, camera_id=0)
    viewer.pack(padx=10, pady=10)
    
    # Add a test button
    def toggle_stream():
        if viewer.is_active:
            viewer.stop_stream()
        else:
            viewer.start_stream()
            
    ttk.Button(root, text="Toggle Stream", command=toggle_stream).pack(pady=5)
    
    root.mainloop()