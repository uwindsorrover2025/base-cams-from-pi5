#!/usr/bin/env python3
"""
Base Station GUI Application
Main application for viewing camera streams and managing photos
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import cv2
from datetime import datetime
import logging
import sys
from typing import Dict, List, Optional

# Import custom modules
from camera_viewer import CameraViewer
from stream_manager import StreamManager
from timestamp_overlay import TimestampOverlay
from ip_config_dialog import IPConfigDialog
from photo_capture_dialog import PhotoCaptureDialog
from photo_gallery import PhotoGallery

class BaseStationGUI:
    def __init__(self):
        """Initialize the base station GUI application"""
        self.root = tk.Tk()
        self.root.title("Camera Streaming Viewer")
        self.root.geometry("1280x600")
        self.root.minsize(1024, 480)
        
        # Initialize components
        self.config = self._load_config()
        self.stream_manager = StreamManager(buffer_size=self.config['display']['buffer_size'])
        self.overlay_manager = TimestampOverlay(
            enabled=self.config['overlay']['enabled'],
            position=self.config['overlay']['position'],
            font_size=self.config['overlay']['font_size'],
            background_opacity=self.config['overlay']['background_opacity']
        )
        
        # Camera viewers
        self.camera_viewers = []
        self.camera_assignments = [0, 1]  # Which cameras are assigned to each viewer
        
        # Setup logging
        self._setup_logging()
        
        # Create UI
        self._create_menu()
        self._create_widgets()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Start with configured IP
        self._update_window_title()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('base_station.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self) -> dict:
        """Load configuration from file"""
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            # Return default config
            return {
                "raspberry_pi": {
                    "ip": "192.168.1.100",
                    "ports": {"cam1": 8554, "cam2": 8555, "cam3": 8556}
                },
                "display": {
                    "window_size": "1280x480",
                    "fps": 30,
                    "buffer_size": 5
                },
                "saved_ips": [],
                "capture": {
                    "save_directory": "./captures",
                    "image_format": "jpg",
                    "quality": 95,
                    "timestamp_format": "%Y-%m-%d_%H-%M-%S"
                },
                "overlay": {
                    "enabled": True,
                    "position": "bottom-left",
                    "font_size": 12,
                    "background_opacity": 0.7
                }
            }
            
    def _save_config(self):
        """Save configuration to file"""
        try:
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            
    def _create_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="IP Configuration...", command=self._show_ip_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        
        # Overlay submenu
        overlay_menu = tk.Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label="Timestamp Overlay", menu=overlay_menu)
        
        self.overlay_enabled_var = tk.BooleanVar(value=self.config['overlay']['enabled'])
        overlay_menu.add_checkbutton(
            label="Enable Overlay",
            variable=self.overlay_enabled_var,
            command=self._toggle_overlay
        )
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Photo Gallery", command=self._show_gallery)
        view_menu.add_separator()
        view_menu.add_command(label="Fullscreen", command=self._toggle_fullscreen, accelerator="F11")
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Keyboard Shortcuts", command=self._show_shortcuts)
        help_menu.add_command(label="About", command=self._show_about)
        
    def _create_widgets(self):
        """Create main UI widgets"""
        # Toolbar
        toolbar = ttk.Frame(self.root, relief=tk.RAISED, borderwidth=1)
        toolbar.pack(fill=tk.X, padx=2, pady=2)
        
        # Camera selection dropdowns
        ttk.Label(toolbar, text="Camera 1:").pack(side=tk.LEFT, padx=(10, 5))
        self.cam1_var = tk.StringVar(value="Camera 1")
        self.cam1_combo = ttk.Combobox(
            toolbar,
            textvariable=self.cam1_var,
            values=["Camera 1", "Camera 2", "Camera 3"],
            width=12,
            state="readonly"
        )
        self.cam1_combo.pack(side=tk.LEFT, padx=(0, 20))
        self.cam1_combo.bind("<<ComboboxSelected>>", lambda e: self._on_camera_change(0))
        
        ttk.Label(toolbar, text="Camera 2:").pack(side=tk.LEFT, padx=(0, 5))
        self.cam2_var = tk.StringVar(value="Camera 2")
        self.cam2_combo = ttk.Combobox(
            toolbar,
            textvariable=self.cam2_var,
            values=["Camera 1", "Camera 2", "Camera 3"],
            width=12,
            state="readonly"
        )
        self.cam2_combo.pack(side=tk.LEFT, padx=(0, 30))
        self.cam2_combo.bind("<<ComboboxSelected>>", lambda e: self._on_camera_change(1))
        
        # Action buttons
        self.capture_button = ttk.Button(
            toolbar,
            text="📷 Capture",
            command=self._show_capture_dialog
        )
        self.capture_button.pack(side=tk.LEFT, padx=5)
        
        self.gallery_button = ttk.Button(
            toolbar,
            text="🖼️ Gallery",
            command=self._show_gallery
        )
        self.gallery_button.pack(side=tk.LEFT, padx=5)
        
        # Connection button
        self.connect_button = ttk.Button(
            toolbar,
            text="Connect",
            command=self._toggle_connection
        )
        self.connect_button.pack(side=tk.RIGHT, padx=10)
        
        # Main content area
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create camera viewers
        for i in range(2):
            viewer = CameraViewer(
                content_frame,
                camera_id=i,
                width=640,
                height=480
            )
            viewer.set_stream_manager(self.stream_manager)
            viewer.set_overlay_manager(self.overlay_manager)
            viewer.set_camera_name(f"Camera {i + 1}")
            viewer.set_double_click_callback(self._on_viewer_double_click)
            viewer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
            
            self.camera_viewers.append(viewer)
            
        # Status bar
        self.status_bar = ttk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(
            self.status_bar,
            text="Disconnected"
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        self.time_label = ttk.Label(
            self.status_bar,
            text=""
        )
        self.time_label.pack(side=tk.RIGHT, padx=10, pady=2)
        
        # Start time update
        self._update_time()
        
        # Bind keyboard shortcuts
        self.root.bind("<F11>", lambda e: self._toggle_fullscreen())
        self.root.bind("<space>", lambda e: self._show_capture_dialog())
        self.root.bind("g", lambda e: self._show_gallery())
        self.root.bind("1", lambda e: self._switch_camera(0, 0))
        self.root.bind("2", lambda e: self._switch_camera(0, 1))
        self.root.bind("3", lambda e: self._switch_camera(0, 2))
        
    def _update_window_title(self):
        """Update window title with current IP"""
        ip = self.config['raspberry_pi']['ip']
        self.root.title(f"Camera Streaming Viewer - [IP: {ip}]")
        
    def _update_time(self):
        """Update time display in status bar"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self._update_time)
        
    def _show_ip_config(self):
        """Show IP configuration dialog"""
        dialog = IPConfigDialog(
            self.root,
            self.config['raspberry_pi'],
            self.config.get('saved_ips', [])
        )
        self.root.wait_window(dialog)
        
        result = dialog.get_result()
        if result:
            # Update configuration
            self.config['raspberry_pi'] = result
            
            # Save IP to history
            ip = result['ip']
            if ip not in self.config['saved_ips']:
                self.config['saved_ips'].append(ip)
                if len(self.config['saved_ips']) > 10:  # Keep last 10
                    self.config['saved_ips'].pop(0)
                    
            self._save_config()
            self._update_window_title()
            
            # Reconnect if already connected
            if any(self.stream_manager.is_connected(i) for i in range(3)):
                self._disconnect_streams()
                self._connect_streams()
                
    def _toggle_connection(self):
        """Toggle connection to streams"""
        if any(self.stream_manager.is_connected(i) for i in range(3)):
            self._disconnect_streams()
        else:
            self._connect_streams()
            
    def _connect_streams(self):
        """Connect to all camera streams"""
        self.connect_button.config(text="Connecting...", state='disabled')
        self.status_label.config(text="Connecting to streams...")
        
        ip = self.config['raspberry_pi']['ip']
        ports = self.config['raspberry_pi']['ports']
        
        # Connect to all three cameras
        success_count = 0
        for i, (cam, port) in enumerate([
            ('cam1', ports['cam1']),
            ('cam2', ports['cam2']),
            ('cam3', ports['cam3'])
        ]):
            url = f"rtsp://{ip}:{port}/{cam}"
            if self.stream_manager.connect_stream(i, url):
                success_count += 1
                self.logger.info(f"Connected to camera {i}: {url}")
            else:
                self.logger.error(f"Failed to connect to camera {i}: {url}")
                
        if success_count > 0:
            self.connect_button.config(text="Disconnect", state='normal')
            self.status_label.config(text=f"Connected ({success_count}/3 cameras)")
            
            # Start displaying streams
            for viewer in self.camera_viewers:
                viewer.start_stream()
        else:
            self.connect_button.config(text="Connect", state='normal')
            self.status_label.config(text="Connection failed")
            messagebox.showerror(
                "Connection Failed",
                f"Failed to connect to any cameras at {ip}\n"
                "Please check:\n"
                "- Raspberry Pi is running the streaming server\n"
                "- IP address is correct\n"
                "- Both devices are on the same network"
            )
            
    def _disconnect_streams(self):
        """Disconnect all streams"""
        # Stop viewers
        for viewer in self.camera_viewers:
            viewer.stop_stream()
            
        # Disconnect streams
        self.stream_manager.disconnect_all()
        
        self.connect_button.config(text="Connect", state='normal')
        self.status_label.config(text="Disconnected")
        
    def _on_camera_change(self, viewer_index: int):
        """Handle camera selection change"""
        if viewer_index == 0:
            cam_name = self.cam1_var.get()
        else:
            cam_name = self.cam2_var.get()
            
        # Extract camera number
        cam_num = int(cam_name.split()[-1]) - 1
        
        # Update assignment
        self.camera_assignments[viewer_index] = cam_num
        
        # Update viewer
        self.camera_viewers[viewer_index].camera_id = cam_num
        self.camera_viewers[viewer_index].set_camera_name(cam_name)
        
    def _switch_camera(self, viewer_index: int, camera_index: int):
        """Switch camera for a viewer"""
        if viewer_index < len(self.camera_viewers):
            combo = self.cam1_combo if viewer_index == 0 else self.cam2_combo
            combo.set(f"Camera {camera_index + 1}")
            self._on_camera_change(viewer_index)
            
    def _toggle_overlay(self):
        """Toggle timestamp overlay"""
        enabled = self.overlay_enabled_var.get()
        self.overlay_manager.set_enabled(enabled)
        self.config['overlay']['enabled'] = enabled
        self._save_config()
        
    def _show_capture_dialog(self):
        """Show photo capture dialog"""
        if not any(self.stream_manager.is_connected(i) for i in range(3)):
            messagebox.showwarning(
                "Not Connected",
                "Please connect to cameras first"
            )
            return
            
        camera_names = ["Camera 1", "Camera 2", "Camera 3"]
        dialog = PhotoCaptureDialog(
            self.root,
            camera_names,
            self.config['capture']['save_directory']
        )
        
        def capture_callback(selected_cameras, save_directory):
            """Callback to capture photos"""
            for cam_idx in selected_cameras:
                frame = self.stream_manager.capture_frame(cam_idx)
                if frame is not None:
                    # Apply overlay
                    if self.overlay_manager.enabled:
                        frame = self.overlay_manager.add_overlay(
                            frame,
                            f"Camera {cam_idx + 1}"
                        )
                        
                    # Generate filename
                    timestamp = datetime.now().strftime(
                        self.config['capture']['timestamp_format']
                    )
                    filename = f"cam{cam_idx + 1}_{timestamp}.{self.config['capture']['image_format']}"
                    filepath = os.path.join(save_directory, filename)
                    
                    # Save image
                    cv2.imwrite(
                        filepath,
                        frame,
                        [cv2.IMWRITE_JPEG_QUALITY, self.config['capture']['quality']]
                    )
                    self.logger.info(f"Saved photo: {filepath}")
                    
        dialog.set_capture_callback(capture_callback)
        
    def _show_gallery(self):
        """Show photo gallery"""
        gallery = PhotoGallery(
            self.root,
            self.config['capture']['save_directory']
        )
        
    def _on_viewer_double_click(self, camera_id: int):
        """Handle double-click on camera viewer"""
        # Could implement fullscreen view for single camera
        self.logger.info(f"Double-clicked on camera {camera_id}")
        
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        current_state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current_state)
        
    def _show_shortcuts(self):
        """Show keyboard shortcuts dialog"""
        shortcuts = """
Keyboard Shortcuts:

Space       - Capture Photo
G           - Open Gallery
1/2/3       - Switch Camera in Viewer 1
F11         - Toggle Fullscreen
Ctrl+Q      - Quit

Double-click on a camera view to maximize it.
        """
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)
        
    def _show_about(self):
        """Show about dialog"""
        about_text = """
Camera Streaming Viewer
Version 1.0

A dual-camera RTSP streaming viewer with photo capture
and gallery features.

Designed for Raspberry Pi camera streaming.
        """
        messagebox.showinfo("About", about_text)
        
    def _on_close(self):
        """Handle application close"""
        # Disconnect streams
        self._disconnect_streams()
        
        # Save configuration
        self._save_config()
        
        # Destroy window
        self.root.destroy()
        
    def run(self):
        """Run the application"""
        self.logger.info("Starting Base Station GUI")
        self.root.mainloop()


def main():
    """Main entry point"""
    app = BaseStationGUI()
    app.run()


if __name__ == "__main__":
    main()