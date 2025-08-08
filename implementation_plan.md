# Camera Streaming System Implementation Plan

## Project Structure

```
rover_cameras_base/
├── raspberry_pi/
│   ├── pi_streaming_server.py
│   ├── camera_manager.py
│   ├── rtsp_server.py
│   ├── config.json
│   ├── requirements.txt
│   └── README.md
│
├── base_station/
│   ├── base_station_gui.py
│   ├── camera_viewer.py
│   ├── ip_config_dialog.py
│   ├── photo_capture_dialog.py
│   ├── photo_gallery.py
│   ├── stream_manager.py
│   ├── timestamp_overlay.py
│   ├── config.json
│   ├── requirements.txt
│   ├── README.md
│   └── captures/
│       └── .gitkeep
│
└── camera_streaming_architecture.md
```

## Raspberry Pi Implementation Details

### 1. Main Streaming Server (`pi_streaming_server.py`)
- Initialize USB cameras using OpenCV
- Create GStreamer pipelines for each camera
- Launch RTSP server instances
- Monitor camera status
- Handle graceful shutdown

### 2. Camera Manager (`camera_manager.py`)
- Detect available USB cameras
- Configure camera parameters (resolution, FPS)
- Handle camera reconnection
- Provide camera status API

### 3. RTSP Server (`rtsp_server.py`)
- GStreamer RTSP server wrapper
- Create streaming pipelines
- Manage port allocation
- Handle client connections

### 4. Configuration (`config.json`)
```json
{
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
    "debug": false
  }
}
```

## Base Station Implementation Details

### 1. Main GUI Application (`base_station_gui.py`)
- Tkinter main window
- Layout with 2 camera views
- Camera selection controls
- Photo capture button
- Gallery button
- Menu bar with settings
- Status bar with timestamp

### 2. Camera Viewer Widget (`camera_viewer.py`)
- Custom Tkinter widget for video display
- OpenCV integration for RTSP streams
- Frame buffer management
- Connection status display
- Timestamp overlay rendering

### 3. IP Configuration Dialog (`ip_config_dialog.py`)
- Modal dialog for IP settings
- Input validation
- Save/load configurations
- Test connection button

### 4. Photo Capture Dialog (`photo_capture_dialog.py`)
- Modal dialog for capture options
- Camera selection checkboxes
- Preview of selected cameras
- Capture button with progress
- Save location settings

### 5. Photo Gallery (`photo_gallery.py`)
- Thumbnail grid view
- Full-size image viewer
- Sort and filter options
- Delete functionality
- Export selected photos

### 6. Timestamp Overlay (`timestamp_overlay.py`)
- Add timestamp to frames
- Configurable position and format
- Camera name inclusion
- Semi-transparent background

### 7. Stream Manager (`stream_manager.py`)
- RTSP connection management
- Stream switching logic
- Error handling and reconnection
- Performance monitoring

### 8. Configuration (`config.json`)
```json
{
  "raspberry_pi": {
    "ip": "192.168.1.100",
    "ports": {
      "cam1": 8554,
      "cam2": 8555,
      "cam3": 8556
    }
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
    "enabled": true,
    "position": "bottom-left",
    "font_size": 12,
    "background_opacity": 0.7
  }
}
```

## GUI Layout Design

```
+---------------------------------------------------------------+
|  Camera Streaming Viewer - [IP: 192.168.1.100]               |
+---------------------------------------------------------------+
| File | Settings | View | Help                                 |
+---------------------------------------------------------------+
| Camera 1: [Dropdown ▼] | Camera 2: [Dropdown ▼] | [📷] [🖼️] |
+---------------------------------------------------------------+
|                             |                              |
|                             |                              |
|    Camera View 1            |    Camera View 2             |
|    (640x480)               |    (640x480)                |
|                             |                              |
| 2025-08-08 16:00:00 | Cam1 | 2025-08-08 16:00:00 | Cam2  |
+-----------------------------+------------------------------+
| Connected | FPS: 15/15 | Bitrate: 2.5 Mbps | Photos: 42    |
+---------------------------------------------------------------+

Legend:
[📷] = Capture Photo button
[🖼️] = Gallery button
```

## Key Implementation Features

### Raspberry Pi Side
1. **Auto-discovery**: Automatically detect USB cameras on startup
2. **Hot-plug support**: Handle camera connect/disconnect
3. **Resource management**: Efficient CPU/memory usage
4. **Logging**: Detailed logs for debugging
5. **Systemd service**: Run as system service

### Base Station Side
1. **Responsive UI**: Smooth video playback
2. **Quick switching**: Instant camera switching
3. **Connection resilience**: Auto-reconnect on network issues
4. **Fullscreen mode**: Double-click to fullscreen a view
5. **Keyboard shortcuts**:
   - Space: Capture photo
   - G: Open gallery
   - 1-3: Switch cameras
   - F: Toggle fullscreen
6. **Photo management**: Organized capture storage
7. **Timestamp overlay**: Customizable overlay on streams

## Dependencies

### Raspberry Pi
- Python 3.9+
- OpenCV (cv2)
- GStreamer 1.0
- gst-rtsp-server
- numpy
- psutil

### Base Station
- Python 3.8+
- tkinter (usually included)
- OpenCV (cv2)
- Pillow (PIL)
- numpy
- threading

## Development Steps

1. **Phase 1**: Basic streaming (1 camera)
   - Simple RTSP server on Pi
   - Basic GUI with single view

2. **Phase 2**: Multi-camera support
   - 3 camera streams on Pi
   - Dual view in GUI

3. **Phase 3**: Camera switching
   - Implement switching logic
   - Add UI controls

4. **Phase 4**: Photo capture
   - Capture dialog implementation
   - Timestamp overlay
   - Photo storage

5. **Phase 5**: Gallery
   - Thumbnail generation
   - Gallery viewer
   - Photo management

6. **Phase 6**: Polish
   - IP configuration dialog
   - Error handling
   - Performance optimization

## Testing Strategy

1. **Unit Tests**
   - Camera detection
   - RTSP URL generation
   - Configuration loading

2. **Integration Tests**
   - Pi to Base connection
   - Stream switching
   - Error recovery

3. **Performance Tests**
   - CPU usage on Pi
   - Network bandwidth
   - GUI responsiveness

## Deployment

### Raspberry Pi
```bash
# Clone repository
git clone <repo-url> ~/camera_streaming
cd ~/camera_streaming/raspberry_pi

# Install dependencies
pip install -r requirements.txt

# Run server
python pi_streaming_server.py

# Or install as service
sudo cp camera_streaming.service /etc/systemd/system/
sudo systemctl enable camera_streaming
sudo systemctl start camera_streaming
```

### Base Station
```bash
# Clone repository
git clone <repo-url> ~/camera_streaming
cd ~/camera_streaming/base_station

# Install dependencies
pip install -r requirements.txt

# Run GUI
python base_station_gui.py
```

## Enhanced GUI Features

### Photo Capture Dialog
```
+----------------------------------+
|      Capture Photo               |
+----------------------------------+
| Select cameras to capture:       |
|                                  |
| ☑ Camera 1 (Living Room)        |
| ☑ Camera 2 (Kitchen)            |
| ☐ Camera 3 (Garage)             |
|                                  |
| Save to: ./captures/             |
| [Browse...]                      |
|                                  |
| [Capture Selected] [Cancel]      |
+----------------------------------+
```

### Photo Gallery View
```
+---------------------------------------------------------------+
|  Photo Gallery - 42 photos                           [X]      |
+---------------------------------------------------------------+
| Sort: [Date ▼] | Filter: [All Cameras ▼] | [Delete] [Export] |
+---------------------------------------------------------------+
| +-------+ +-------+ +-------+ +-------+ +-------+ +-------+  |
| |       | |       | |       | |       | |       | |       |  |
| | Thumb | | Thumb | | Thumb | | Thumb | | Thumb | | Thumb |  |
| |       | |       | |       | |       | |       | |       |  |
| +-------+ +-------+ +-------+ +-------+ +-------+ +-------+  |
| Cam1     Cam2     Cam3     Cam1     Cam2     Cam3          |
| 16:00    16:01    16:02    16:03    16:04    16:05         |
|                                                              |
| +-------+ +-------+ +-------+ +-------+ +-------+ +-------+  |
| |       | |       | |       | |       | |       | |       |  |
| | Thumb | | Thumb | | Thumb | | Thumb | | Thumb | | Thumb |  |
| |       | |       | |       | |       | |       | |       |  |
| +-------+ +-------+ +-------+ +-------+ +-------+ +-------+  |
+---------------------------------------------------------------+
| Page 1 of 7                              [<] [1] [2] [3] [>] |
+---------------------------------------------------------------+
```