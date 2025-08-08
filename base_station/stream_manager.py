#!/usr/bin/env python3
"""
Stream Manager Module
Handles RTSP stream connections and management
"""

import cv2
import logging
import threading
import time
from typing import Dict, Optional, Tuple, Any
from queue import Queue, Empty
import numpy as np

class StreamManager:
    def __init__(self, buffer_size: int = 5):
        """
        Initialize stream manager
        
        Args:
            buffer_size: Size of frame buffer for each stream
        """
        self.logger = logging.getLogger(__name__)
        self.buffer_size = buffer_size
        self.streams: Dict[int, Dict[str, Any]] = {}
        self.active = False
        self.capture_threads: Dict[int, threading.Thread] = {}
        
    def connect_stream(self, camera_id: int, rtsp_url: str) -> bool:
        """
        Connect to an RTSP stream
        
        Args:
            camera_id: Camera identifier (0, 1, or 2)
            rtsp_url: RTSP URL for the stream
            
        Returns:
            True if connection successful
        """
        try:
            # Disconnect existing stream if any
            if camera_id in self.streams:
                self.disconnect_stream(camera_id)
                
            # Create VideoCapture with GStreamer backend
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_GSTREAMER)
            
            if not cap.isOpened():
                # Try with FFMPEG backend as fallback
                cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
                
            if not cap.isOpened():
                self.logger.error(f"Failed to connect to stream {camera_id}: {rtsp_url}")
                return False
                
            # Set buffer size to reduce latency
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Create frame buffer
            frame_buffer = Queue(maxsize=self.buffer_size)
            
            # Store stream info
            self.streams[camera_id] = {
                'capture': cap,
                'url': rtsp_url,
                'buffer': frame_buffer,
                'connected': True,
                'fps': 0,
                'frame_count': 0,
                'last_frame': None,
                'error_count': 0
            }
            
            # Start capture thread
            self.active = True
            thread = threading.Thread(
                target=self._capture_loop,
                args=(camera_id,),
                daemon=True
            )
            thread.start()
            self.capture_threads[camera_id] = thread
            
            self.logger.info(f"Connected to stream {camera_id}: {rtsp_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting to stream {camera_id}: {e}")
            return False
            
    def disconnect_stream(self, camera_id: int):
        """
        Disconnect a stream
        
        Args:
            camera_id: Camera identifier
        """
        if camera_id in self.streams:
            # Stop capture thread
            self.streams[camera_id]['connected'] = False
            
            # Wait for thread to finish
            if camera_id in self.capture_threads:
                self.capture_threads[camera_id].join(timeout=2)
                del self.capture_threads[camera_id]
                
            # Release capture
            if self.streams[camera_id]['capture'] is not None:
                self.streams[camera_id]['capture'].release()
                
            # Clear buffer
            while not self.streams[camera_id]['buffer'].empty():
                try:
                    self.streams[camera_id]['buffer'].get_nowait()
                except Empty:
                    break
                    
            del self.streams[camera_id]
            self.logger.info(f"Disconnected stream {camera_id}")
            
    def _capture_loop(self, camera_id: int):
        """
        Capture loop for a stream (runs in separate thread)
        
        Args:
            camera_id: Camera identifier
        """
        stream = self.streams[camera_id]
        cap = stream['capture']
        buffer = stream['buffer']
        
        fps_timer = time.time()
        fps_counter = 0
        
        while self.active and stream['connected']:
            try:
                ret, frame = cap.read()
                
                if ret:
                    # Update FPS counter
                    fps_counter += 1
                    current_time = time.time()
                    if current_time - fps_timer >= 1.0:
                        stream['fps'] = fps_counter
                        fps_counter = 0
                        fps_timer = current_time
                        
                    # Update frame count
                    stream['frame_count'] += 1
                    
                    # Add frame to buffer (drop old frames if full)
                    if buffer.full():
                        try:
                            buffer.get_nowait()
                        except Empty:
                            pass
                            
                    buffer.put(frame)
                    stream['last_frame'] = frame
                    stream['error_count'] = 0
                    
                else:
                    # Read failed
                    stream['error_count'] += 1
                    time.sleep(0.1)
                    
                    # Attempt reconnection after multiple failures
                    if stream['error_count'] > 10:
                        self.logger.warning(f"Stream {camera_id} error count exceeded, attempting reconnection")
                        self._reconnect_stream(camera_id)
                        
            except Exception as e:
                self.logger.error(f"Error in capture loop for stream {camera_id}: {e}")
                stream['error_count'] += 1
                time.sleep(0.1)
                
    def _reconnect_stream(self, camera_id: int):
        """
        Attempt to reconnect a stream
        
        Args:
            camera_id: Camera identifier
        """
        if camera_id in self.streams:
            url = self.streams[camera_id]['url']
            self.disconnect_stream(camera_id)
            time.sleep(1)
            self.connect_stream(camera_id, url)
            
    def get_frame(self, camera_id: int) -> Optional[np.ndarray]:
        """
        Get the latest frame from a stream
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Frame as numpy array or None
        """
        if camera_id not in self.streams:
            return None
            
        stream = self.streams[camera_id]
        
        # Try to get frame from buffer
        try:
            frame = stream['buffer'].get_nowait()
            stream['last_frame'] = frame
            return frame
        except Empty:
            # Return last frame if buffer is empty
            return stream['last_frame']
            
    def get_stream_info(self, camera_id: int) -> Optional[Dict]:
        """
        Get information about a stream
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Stream information dictionary
        """
        if camera_id not in self.streams:
            return None
            
        stream = self.streams[camera_id]
        return {
            'connected': stream['connected'],
            'fps': stream['fps'],
            'frame_count': stream['frame_count'],
            'url': stream['url'],
            'error_count': stream['error_count']
        }
        
    def get_all_stream_info(self) -> Dict[int, Dict]:
        """
        Get information about all streams
        
        Returns:
            Dictionary of stream information
        """
        return {
            cam_id: self.get_stream_info(cam_id) 
            for cam_id in self.streams
        }
        
    def is_connected(self, camera_id: int) -> bool:
        """
        Check if a stream is connected
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            True if connected
        """
        return (camera_id in self.streams and 
                self.streams[camera_id]['connected'] and
                self.streams[camera_id]['error_count'] < 10)
                
    def disconnect_all(self):
        """Disconnect all streams"""
        self.active = False
        for cam_id in list(self.streams.keys()):
            self.disconnect_stream(cam_id)
            
    def capture_frame(self, camera_id: int) -> Optional[np.ndarray]:
        """
        Capture a single frame for photo saving
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            High quality frame or None
        """
        if camera_id not in self.streams:
            return None
            
        # Get the most recent frame
        frame = self.get_frame(camera_id)
        if frame is not None:
            # Return a copy to avoid modifications
            return frame.copy()
            
        return None


# Example usage for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    manager = StreamManager()
    
    # Test with local video file or RTSP stream
    test_url = "rtsp://192.168.1.100:8554/cam1"
    
    if manager.connect_stream(0, test_url):
        print("Connected successfully")
        
        # Let it run for a bit
        time.sleep(5)
        
        # Get stream info
        info = manager.get_stream_info(0)
        print(f"Stream info: {info}")
        
        # Get a frame
        frame = manager.get_frame(0)
        if frame is not None:
            print(f"Got frame with shape: {frame.shape}")
            
    manager.disconnect_all()