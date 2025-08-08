#!/usr/bin/env python3
"""
Main Raspberry Pi Camera Streaming Server
Manages USB cameras and RTSP streaming
"""

import json
import logging
import signal
import sys
import time
import argparse
from pathlib import Path
from camera_manager import CameraManager
from rtsp_server import RTSPServer
import psutil
import socket

class PiStreamingServer:
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the Pi streaming server
        
        Args:
            config_file: Path to configuration file
        """
        self.logger = self._setup_logging()
        self.config = self._load_config(config_file)
        self.camera_manager = None
        self.rtsp_server = None
        self.running = False
        self.camera_indices = []
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('streaming_server.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
        
    def _load_config(self, config_file: str) -> dict:
        """Load configuration from file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            self.logger.info(f"Loaded configuration from {config_file}")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            # Return default config
            return {
                "cameras": {
                    "resolution": "640x480",
                    "fps": 15,
                    "codec": "h264"
                },
                "rtsp": {
                    "base_port": 8554,
                    "mount_points": ["/cam1", "/cam2", "/cam3"]
                },
                "server": {
                    "host": "0.0.0.0",
                    "debug": False
                }
            }
            
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
        
    def initialize(self) -> bool:
        """
        Initialize camera manager and RTSP server
        
        Returns:
            True if initialization successful
        """
        try:
            # Initialize camera manager
            resolution = self.config['cameras']['resolution']
            fps = self.config['cameras']['fps']
            self.camera_manager = CameraManager(resolution=resolution, fps=fps)
            
            # Initialize all cameras
            init_results = self.camera_manager.initialize_all_cameras()
            
            if not init_results:
                self.logger.error("No cameras detected!")
                return False
                
            self.camera_indices = list(init_results.keys())
            self.logger.info(f"Initialized cameras: {self.camera_indices}")
            
            # Initialize RTSP server
            host = self.config['server']['host']
            base_port = self.config['rtsp']['base_port']
            self.rtsp_server = RTSPServer(host=host, base_port=base_port)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False
            
    def start(self) -> bool:
        """
        Start the streaming server
        
        Returns:
            True if server started successfully
        """
        if not self.initialize():
            return False
            
        try:
            # Start RTSP main loop
            self.rtsp_server.start_main_loop()
            
            # Start RTSP servers for all cameras
            mount_points = self.config['rtsp']['mount_points']
            results = self.rtsp_server.start_all_servers(
                self.camera_indices[:len(mount_points)], 
                mount_points,
                test_mode=False
            )
            
            if not any(results.values()):
                self.logger.error("Failed to start any RTSP servers")
                return False
                
            # Print stream URLs
            self.logger.info("=" * 50)
            self.logger.info("RTSP Stream URLs:")
            urls = self.rtsp_server.get_all_stream_urls()
            
            # Get server IP address
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            
            for cam_idx, url in urls.items():
                # Replace 0.0.0.0 with actual IP
                display_url = url.replace("0.0.0.0", ip_address)
                self.logger.info(f"Camera {cam_idx}: {display_url}")
            self.logger.info("=" * 50)
            
            self.running = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            return False
            
    def monitor_loop(self):
        """Main monitoring loop"""
        monitor_interval = 30  # seconds
        
        while self.running:
            try:
                # Check camera health
                health = self.camera_manager.check_camera_health()
                
                for cam_idx, status in health.items():
                    if status != 'healthy':
                        self.logger.warning(f"Camera {cam_idx} status: {status}")
                        
                        # Attempt reconnection if disconnected
                        if status == 'disconnected':
                            self.logger.info(f"Attempting to reconnect camera {cam_idx}")
                            if self.camera_manager.reconnect_camera(cam_idx):
                                self.logger.info(f"Successfully reconnected camera {cam_idx}")
                                
                # Log system stats
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                self.logger.info(f"System stats - CPU: {cpu_percent}%, "
                               f"Memory: {memory.percent}%")
                
                time.sleep(monitor_interval)
                
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")
                time.sleep(5)
                
    def stop(self):
        """Stop the streaming server"""
        self.running = False
        
        if self.rtsp_server:
            self.rtsp_server.stop_all_servers()
            
        if self.camera_manager:
            self.camera_manager.release_all_cameras()
            
        self.logger.info("Streaming server stopped")
        
    def run(self):
        """Run the streaming server"""
        if not self.start():
            self.logger.error("Failed to start streaming server")
            return
            
        self.logger.info("Streaming server is running. Press Ctrl+C to stop.")
        
        try:
            self.monitor_loop()
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        finally:
            self.stop()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Raspberry Pi Camera Streaming Server"
    )
    parser.add_argument(
        '-c', '--config',
        default='config.json',
        help='Configuration file path'
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run server
    server = PiStreamingServer(config_file=args.config)
    server.run()


if __name__ == "__main__":
    main()