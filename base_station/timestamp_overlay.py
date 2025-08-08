#!/usr/bin/env python3
"""
Timestamp Overlay Module
Adds timestamp and camera name overlay to video frames
"""

import cv2
import numpy as np
from datetime import datetime
from typing import Tuple, Optional

class TimestampOverlay:
    def __init__(self, enabled: bool = True, position: str = "bottom-left", 
                 font_size: int = 12, background_opacity: float = 0.7):
        """
        Initialize timestamp overlay
        
        Args:
            enabled: Whether overlay is enabled
            position: Position of overlay ("bottom-left", "bottom-right", "top-left", "top-right")
            font_size: Font size for timestamp text
            background_opacity: Opacity of background (0.0 to 1.0)
        """
        self.enabled = enabled
        self.position = position
        self.font_size = font_size
        self.background_opacity = background_opacity
        
        # OpenCV font settings
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = font_size / 20.0
        self.font_thickness = 1
        self.text_color = (255, 255, 255)  # White
        self.background_color = (0, 0, 0)  # Black
        
    def add_overlay(self, frame: np.ndarray, camera_name: str = "", 
                   timestamp: Optional[datetime] = None) -> np.ndarray:
        """
        Add timestamp overlay to a frame
        
        Args:
            frame: Video frame as numpy array
            camera_name: Name of the camera
            timestamp: Timestamp to display (current time if None)
            
        Returns:
            Frame with overlay added
        """
        if not self.enabled:
            return frame
            
        # Get timestamp
        if timestamp is None:
            timestamp = datetime.now()
            
        # Format timestamp text
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        if camera_name:
            text = f"{timestamp_str} | {camera_name}"
        else:
            text = timestamp_str
            
        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(
            text, self.font, self.font_scale, self.font_thickness
        )
        
        # Calculate position
        padding = 10
        frame_height, frame_width = frame.shape[:2]
        
        if "bottom" in self.position:
            y = frame_height - padding - baseline
        else:
            y = padding + text_height
            
        if "right" in self.position:
            x = frame_width - padding - text_width
        else:
            x = padding
            
        # Draw background rectangle
        bg_pt1 = (x - padding//2, y - text_height - padding//2)
        bg_pt2 = (x + text_width + padding//2, y + baseline + padding//2)
        
        # Create overlay on a copy to apply transparency
        overlay = frame.copy()
        cv2.rectangle(overlay, bg_pt1, bg_pt2, self.background_color, -1)
        
        # Apply transparency
        frame = cv2.addWeighted(overlay, self.background_opacity, 
                               frame, 1 - self.background_opacity, 0)
        
        # Draw text
        cv2.putText(frame, text, (x, y), self.font, self.font_scale, 
                   self.text_color, self.font_thickness, cv2.LINE_AA)
        
        return frame
        
    def set_enabled(self, enabled: bool):
        """Enable or disable overlay"""
        self.enabled = enabled
        
    def set_position(self, position: str):
        """Set overlay position"""
        valid_positions = ["bottom-left", "bottom-right", "top-left", "top-right"]
        if position in valid_positions:
            self.position = position
            
    def set_font_size(self, size: int):
        """Set font size"""
        self.font_size = size
        self.font_scale = size / 20.0
        
    def set_background_opacity(self, opacity: float):
        """Set background opacity (0.0 to 1.0)"""
        self.background_opacity = max(0.0, min(1.0, opacity))


# Example usage for testing
if __name__ == "__main__":
    # Create a test frame
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    test_frame[:] = (50, 50, 50)  # Dark gray
    
    # Create overlay instance
    overlay = TimestampOverlay()
    
    # Add overlay to frame
    frame_with_overlay = overlay.add_overlay(test_frame, "Camera 1")
    
    # Display the result
    cv2.imshow("Test Overlay", frame_with_overlay)
    cv2.waitKey(0)
    cv2.destroyAllWindows()