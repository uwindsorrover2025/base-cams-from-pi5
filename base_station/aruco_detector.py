#!/usr/bin/env python3
"""
ArUco Marker Detection Module
Detects ArUco markers from camera streams and displays results
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import time

@dataclass
class ArUcoDetection:
    """Data class for ArUco detection results"""
    marker_id: int
    corners: np.ndarray
    center: Tuple[int, int]
    distance: float  # Estimated distance in cm
    timestamp: float
    camera_id: int

class ArUcoDetector:
    def __init__(self, dictionary_type: str = "DICT_4X4_100", marker_size_cm: float = 5.0):
        """
        Initialize ArUco detector
        
        Args:
            dictionary_type: ArUco dictionary type (default: DICT_4X4_100)
            marker_size_cm: Physical marker size in centimeters (default: 5.0)
        """
        # ArUco dictionary
        self.aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_100)
        self.aruco_params = cv2.aruco.DetectorParameters_create()
        
        # Marker size for distance estimation
        self.marker_size_cm = marker_size_cm
        
        # Detection history
        self.detections: Dict[int, List[ArUcoDetection]] = {0: [], 1: [], 2: []}
        self.max_history = 100
        
        # Camera calibration (default values, should be calibrated for accuracy)
        self.camera_matrix = np.array([
            [800, 0, 320],
            [0, 800, 240],
            [0, 0, 1]
        ], dtype=float)
        
        self.dist_coeffs = np.zeros((5, 1))
        
    def detect_markers(self, frame: np.ndarray, camera_id: int) -> List[ArUcoDetection]:
        """
        Detect ArUco markers in a frame
        
        Args:
            frame: Input frame
            camera_id: Camera identifier
            
        Returns:
            List of detected markers
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect markers
        corners, ids, rejected = cv2.aruco.detectMarkers(
            gray, 
            self.aruco_dict, 
            parameters=self.aruco_params
        )
        
        detections = []
        
        if ids is not None:
            # Estimate pose for each marker
            rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
                corners, 
                self.marker_size_cm, 
                self.camera_matrix, 
                self.dist_coeffs
            )
            
            for i, marker_id in enumerate(ids.flatten()):
                # Get marker corners
                marker_corners = corners[i][0]
                
                # Calculate center
                center_x = int(np.mean(marker_corners[:, 0]))
                center_y = int(np.mean(marker_corners[:, 1]))
                
                # Estimate distance (Z component of translation vector)
                distance = tvecs[i][0][2] if tvecs is not None else 0
                
                # Create detection object
                detection = ArUcoDetection(
                    marker_id=int(marker_id),
                    corners=marker_corners,
                    center=(center_x, center_y),
                    distance=float(distance),
                    timestamp=time.time(),
                    camera_id=camera_id
                )
                
                detections.append(detection)
                
                # Add to history
                self._add_to_history(camera_id, detection)
                
        return detections
        
    def draw_detections(self, frame: np.ndarray, detections: List[ArUcoDetection], 
                       show_info: bool = True) -> np.ndarray:
        """
        Draw ArUco detections on frame
        
        Args:
            frame: Input frame
            detections: List of detections
            show_info: Whether to show marker info
            
        Returns:
            Frame with drawings
        """
        frame_copy = frame.copy()
        
        for detection in detections:
            # Draw marker outline
            corners = detection.corners.astype(int)
            cv2.polylines(frame_copy, [corners], True, (0, 255, 0), 2)
            
            # Draw marker ID and info
            if show_info:
                # Background for text
                text = f"ID: {detection.marker_id}"
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                
                text_x = detection.center[0] - text_size[0] // 2
                text_y = detection.center[1] - 20
                
                # Draw background rectangle
                cv2.rectangle(
                    frame_copy,
                    (text_x - 5, text_y - text_size[1] - 5),
                    (text_x + text_size[0] + 5, text_y + 5),
                    (0, 0, 0),
                    -1
                )
                
                # Draw text
                cv2.putText(
                    frame_copy,
                    text,
                    (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )
                
                # Draw distance if available
                if detection.distance > 0:
                    dist_text = f"{detection.distance:.1f}cm"
                    cv2.putText(
                        frame_copy,
                        dist_text,
                        (text_x, text_y + 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 0),
                        1
                    )
                    
            # Draw center point
            cv2.circle(frame_copy, detection.center, 5, (0, 0, 255), -1)
            
        return frame_copy
        
    def _add_to_history(self, camera_id: int, detection: ArUcoDetection):
        """Add detection to history"""
        if camera_id in self.detections:
            self.detections[camera_id].append(detection)
            
            # Limit history size
            if len(self.detections[camera_id]) > self.max_history:
                self.detections[camera_id].pop(0)
                
    def get_latest_detections(self, camera_id: int, 
                            time_window: float = 1.0) -> List[ArUcoDetection]:
        """
        Get recent detections for a camera
        
        Args:
            camera_id: Camera identifier
            time_window: Time window in seconds
            
        Returns:
            List of recent detections
        """
        if camera_id not in self.detections:
            return []
            
        current_time = time.time()
        recent = [
            d for d in self.detections[camera_id]
            if current_time - d.timestamp <= time_window
        ]
        
        return recent
        
    def get_unique_markers(self, camera_id: int, 
                          time_window: float = 1.0) -> Dict[int, ArUcoDetection]:
        """
        Get unique markers detected recently
        
        Args:
            camera_id: Camera identifier
            time_window: Time window in seconds
            
        Returns:
            Dictionary of marker_id to most recent detection
        """
        recent = self.get_latest_detections(camera_id, time_window)
        
        unique_markers = {}
        for detection in recent:
            if detection.marker_id not in unique_markers or \
               detection.timestamp > unique_markers[detection.marker_id].timestamp:
                unique_markers[detection.marker_id] = detection
                
        return unique_markers
        
    def set_camera_calibration(self, camera_matrix: np.ndarray, 
                              dist_coeffs: np.ndarray):
        """
        Set camera calibration parameters
        
        Args:
            camera_matrix: Camera intrinsic matrix
            dist_coeffs: Distortion coefficients
        """
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        
    def clear_history(self, camera_id: Optional[int] = None):
        """Clear detection history"""
        if camera_id is not None:
            if camera_id in self.detections:
                self.detections[camera_id].clear()
        else:
            for cam_id in self.detections:
                self.detections[cam_id].clear()


# Utility functions for ArUco operations
def generate_aruco_marker(marker_id: int, size: int = 200) -> np.ndarray:
    """
    Generate an ArUco marker image
    
    Args:
        marker_id: Marker ID (0-99 for 4x4_100)
        size: Size in pixels
        
    Returns:
        Marker image
    """
    aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_100)
    marker_img = cv2.aruco.drawMarker(aruco_dict, marker_id, size)
    return marker_img


def save_aruco_marker(marker_id: int, filename: str, size: int = 200):
    """Save ArUco marker to file"""
    marker = generate_aruco_marker(marker_id, size)
    cv2.imwrite(filename, marker)


# Example usage for testing
if __name__ == "__main__":
    # Create detector
    detector = ArUcoDetector()
    
    # Generate some test markers
    for i in range(5):
        save_aruco_marker(i, f"aruco_marker_{i}.png")
        print(f"Generated ArUco marker {i}")
        
    # Test with a sample image or camera
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Detect markers
        detections = detector.detect_markers(frame, 0)
        
        # Draw results
        result_frame = detector.draw_detections(frame, detections)
        
        # Show result
        cv2.imshow("ArUco Detection", result_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()