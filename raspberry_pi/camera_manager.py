#!/usr/bin/env python3
"""
Camera Manager Module
Handles USB camera detection, initialization, and management
"""

import cv2
import logging
import time
from typing import List, Dict, Optional, Tuple

class CameraManager:
    def __init__(self, resolution: str = "640x480", fps: int = 15):
        """
        Initialize the camera manager
        
        Args:
            resolution: Camera resolution as "widthxheight"
            fps: Frames per second
        """
        self.logger = logging.getLogger(__name__)
        self.resolution = tuple(map(int, resolution.split('x')))
        self.fps = fps
        self.cameras: Dict[int, cv2.VideoCapture] = {}
        self.camera_info: Dict[int, Dict] = {}
        
    def detect_cameras(self, max_cameras: int = 3) -> List[int]:
        """
        Detect available USB cameras
        
        Args:
            max_cameras: Maximum number of cameras to check
            
        Returns:
            List of available camera indices
        """
        available_cameras = []
        
        for i in range(max_cameras * 2):  # Check more indices in case of gaps
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # Test if we can actually read from the camera
                ret, _ = cap.read()
                if ret:
                    available_cameras.append(i)
                    self.logger.info(f"Found camera at index {i}")
                cap.release()
                
                if len(available_cameras) >= max_cameras:
                    break
                    
        self.logger.info(f"Detected {len(available_cameras)} cameras: {available_cameras}")
        return available_cameras[:max_cameras]
        
    def initialize_camera(self, camera_index: int) -> bool:
        """
        Initialize a specific camera with configured settings
        
        Args:
            camera_index: Camera device index
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cap = cv2.VideoCapture(camera_index)
            
            if not cap.isOpened():
                self.logger.error(f"Failed to open camera {camera_index}")
                return False
                
            # Set camera properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Verify settings were applied
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            self.cameras[camera_index] = cap
            self.camera_info[camera_index] = {
                'resolution': (actual_width, actual_height),
                'fps': actual_fps,
                'status': 'active'
            }
            
            self.logger.info(f"Initialized camera {camera_index}: "
                           f"{actual_width}x{actual_height} @ {actual_fps} fps")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing camera {camera_index}: {e}")
            return False
            
    def initialize_all_cameras(self) -> Dict[int, bool]:
        """
        Initialize all detected cameras
        
        Returns:
            Dictionary mapping camera index to initialization success
        """
        detected_cameras = self.detect_cameras()
        results = {}
        
        for idx in detected_cameras:
            results[idx] = self.initialize_camera(idx)
            
        return results
        
    def get_frame(self, camera_index: int) -> Optional[Tuple[bool, any]]:
        """
        Get a frame from specified camera
        
        Args:
            camera_index: Camera device index
            
        Returns:
            Tuple of (success, frame) or None if camera not available
        """
        if camera_index not in self.cameras:
            return None
            
        try:
            ret, frame = self.cameras[camera_index].read()
            if not ret:
                self.camera_info[camera_index]['status'] = 'error'
                self.logger.warning(f"Failed to read from camera {camera_index}")
            return ret, frame
        except Exception as e:
            self.logger.error(f"Error reading from camera {camera_index}: {e}")
            self.camera_info[camera_index]['status'] = 'error'
            return False, None
            
    def check_camera_health(self) -> Dict[int, str]:
        """
        Check health status of all cameras
        
        Returns:
            Dictionary mapping camera index to status
        """
        health_status = {}
        
        for idx, cap in self.cameras.items():
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    health_status[idx] = 'healthy'
                    self.camera_info[idx]['status'] = 'active'
                else:
                    health_status[idx] = 'not_responding'
                    self.camera_info[idx]['status'] = 'error'
            else:
                health_status[idx] = 'disconnected'
                self.camera_info[idx]['status'] = 'disconnected'
                
        return health_status
        
    def reconnect_camera(self, camera_index: int) -> bool:
        """
        Attempt to reconnect a disconnected camera
        
        Args:
            camera_index: Camera device index
            
        Returns:
            True if reconnection successful
        """
        if camera_index in self.cameras:
            self.cameras[camera_index].release()
            del self.cameras[camera_index]
            
        time.sleep(1)  # Brief pause before reconnection attempt
        return self.initialize_camera(camera_index)
        
    def get_camera_info(self, camera_index: int) -> Optional[Dict]:
        """
        Get information about a specific camera
        
        Args:
            camera_index: Camera device index
            
        Returns:
            Camera information dictionary or None
        """
        return self.camera_info.get(camera_index)
        
    def get_all_camera_info(self) -> Dict[int, Dict]:
        """
        Get information about all cameras
        
        Returns:
            Dictionary of all camera information
        """
        return self.camera_info.copy()
        
    def release_camera(self, camera_index: int):
        """
        Release a specific camera
        
        Args:
            camera_index: Camera device index
        """
        if camera_index in self.cameras:
            self.cameras[camera_index].release()
            del self.cameras[camera_index]
            del self.camera_info[camera_index]
            self.logger.info(f"Released camera {camera_index}")
            
    def release_all_cameras(self):
        """Release all cameras"""
        for idx in list(self.cameras.keys()):
            self.release_camera(idx)
        self.logger.info("Released all cameras")


# Example usage for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    manager = CameraManager()
    results = manager.initialize_all_cameras()
    
    print(f"Initialization results: {results}")
    print(f"Camera info: {manager.get_all_camera_info()}")
    
    # Test frame capture
    for idx in manager.cameras:
        ret, frame = manager.get_frame(idx)
        if ret:
            print(f"Successfully captured frame from camera {idx}")
            
    manager.release_all_cameras()