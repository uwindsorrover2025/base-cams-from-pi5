#!/usr/bin/env python3
"""
RTSP Server Module
Handles GStreamer RTSP server creation and management
"""

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GLib
import logging
import threading
from typing import Dict, Optional

class RTSPServer:
    def __init__(self, host: str = "0.0.0.0", base_port: int = 8554):
        """
        Initialize the RTSP server
        
        Args:
            host: Host IP address to bind to
            base_port: Base port number for RTSP streams
        """
        self.logger = logging.getLogger(__name__)
        self.host = host
        self.base_port = base_port
        self.servers: Dict[int, GstRtspServer.RTSPServer] = {}
        self.factories: Dict[int, GstRtspServer.RTSPMediaFactory] = {}
        self.main_loop = None
        self.loop_thread = None
        
        # Initialize GStreamer
        Gst.init(None)
        
    def create_pipeline_string(self, camera_index: int, 
                              width: int = 640, height: int = 480, 
                              fps: int = 15) -> str:
        """
        Create GStreamer pipeline string for camera streaming
        
        Args:
            camera_index: Camera device index
            width: Video width
            height: Video height
            fps: Frames per second
            
        Returns:
            GStreamer pipeline string
        """
        pipeline = (
            f"v4l2src device=/dev/video{camera_index} ! "
            f"video/x-raw,width={width},height={height},framerate={fps}/1 ! "
            f"videoconvert ! "
            f"x264enc speed-preset=ultrafast tune=zerolatency bitrate=1500 ! "
            f"rtph264pay config-interval=1 name=pay0 pt=96"
        )
        
        return pipeline
        
    def create_test_pipeline_string(self) -> str:
        """
        Create a test pipeline string (for development without cameras)
        
        Returns:
            GStreamer test pipeline string
        """
        pipeline = (
            "videotestsrc pattern=ball ! "
            "video/x-raw,width=640,height=480,framerate=15/1 ! "
            "videoconvert ! "
            "x264enc speed-preset=ultrafast tune=zerolatency bitrate=1500 ! "
            "rtph264pay config-interval=1 name=pay0 pt=96"
        )
        
        return pipeline
        
    def start_server(self, camera_index: int, mount_point: str, port: int, 
                    test_mode: bool = False) -> bool:
        """
        Start an RTSP server for a specific camera
        
        Args:
            camera_index: Camera device index
            mount_point: RTSP mount point (e.g., "/cam1")
            port: Port number for this server
            test_mode: Use test pattern instead of real camera
            
        Returns:
            True if server started successfully
        """
        try:
            # Create RTSP server
            server = GstRtspServer.RTSPServer()
            server.set_address(self.host)
            server.set_service(str(port))
            
            # Create media factory
            factory = GstRtspServer.RTSPMediaFactory()
            
            # Set pipeline
            if test_mode:
                pipeline = self.create_test_pipeline_string()
            else:
                pipeline = self.create_pipeline_string(camera_index)
                
            factory.set_launch(pipeline)
            factory.set_shared(True)
            
            # Get mount points and add factory
            mounts = server.get_mount_points()
            mounts.add_factory(mount_point, factory)
            
            # Attach server to main context
            server.attach(None)
            
            self.servers[camera_index] = server
            self.factories[camera_index] = factory
            
            self.logger.info(f"Started RTSP server for camera {camera_index} "
                           f"on port {port} at {mount_point}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start RTSP server for camera {camera_index}: {e}")
            return False
            
    def start_all_servers(self, camera_indices: list, mount_points: list, 
                         test_mode: bool = False) -> Dict[int, bool]:
        """
        Start RTSP servers for all cameras
        
        Args:
            camera_indices: List of camera device indices
            mount_points: List of RTSP mount points
            test_mode: Use test patterns instead of real cameras
            
        Returns:
            Dictionary mapping camera index to start success
        """
        results = {}
        
        for i, (cam_idx, mount) in enumerate(zip(camera_indices, mount_points)):
            port = self.base_port + i
            results[cam_idx] = self.start_server(cam_idx, mount, port, test_mode)
            
        return results
        
    def start_main_loop(self):
        """Start the GStreamer main loop in a separate thread"""
        if self.main_loop is None:
            self.main_loop = GLib.MainLoop()
            self.loop_thread = threading.Thread(target=self._run_main_loop)
            self.loop_thread.daemon = True
            self.loop_thread.start()
            self.logger.info("Started GStreamer main loop")
            
    def _run_main_loop(self):
        """Run the GStreamer main loop"""
        try:
            self.main_loop.run()
        except Exception as e:
            self.logger.error(f"Main loop error: {e}")
            
    def stop_server(self, camera_index: int):
        """
        Stop a specific RTSP server
        
        Args:
            camera_index: Camera device index
        """
        if camera_index in self.servers:
            # GstRtspServer doesn't have a direct stop method,
            # but we can remove the mount point
            server = self.servers[camera_index]
            mounts = server.get_mount_points()
            # Remove all factories (this effectively stops the stream)
            for path in ["/cam1", "/cam2", "/cam3"]:
                mounts.remove_factory(path)
            
            del self.servers[camera_index]
            del self.factories[camera_index]
            
            self.logger.info(f"Stopped RTSP server for camera {camera_index}")
            
    def stop_all_servers(self):
        """Stop all RTSP servers"""
        for cam_idx in list(self.servers.keys()):
            self.stop_server(cam_idx)
            
        if self.main_loop and self.main_loop.is_running():
            self.main_loop.quit()
            if self.loop_thread:
                self.loop_thread.join(timeout=2)
                
        self.logger.info("Stopped all RTSP servers")
        
    def get_stream_url(self, camera_index: int, mount_point: str) -> Optional[str]:
        """
        Get the RTSP stream URL for a camera
        
        Args:
            camera_index: Camera device index
            mount_point: RTSP mount point
            
        Returns:
            RTSP URL string or None
        """
        if camera_index in self.servers:
            port = self.base_port + list(self.servers.keys()).index(camera_index)
            return f"rtsp://{self.host}:{port}{mount_point}"
        return None
        
    def get_all_stream_urls(self) -> Dict[int, str]:
        """
        Get all active stream URLs
        
        Returns:
            Dictionary mapping camera index to RTSP URL
        """
        urls = {}
        mount_points = ["/cam1", "/cam2", "/cam3"]
        
        for i, cam_idx in enumerate(self.servers.keys()):
            if i < len(mount_points):
                urls[cam_idx] = self.get_stream_url(cam_idx, mount_points[i])
                
        return urls


# Example usage for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    server = RTSPServer()
    server.start_main_loop()
    
    # Start test streams
    results = server.start_all_servers([0, 1, 2], ["/cam1", "/cam2", "/cam3"], 
                                      test_mode=True)
    print(f"Server start results: {results}")
    print(f"Stream URLs: {server.get_all_stream_urls()}")
    
    # Keep running
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop_all_servers()