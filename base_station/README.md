# Base Station Camera Viewer

A Python Tkinter application for viewing RTSP camera streams from Raspberry Pi with photo capture and gallery features.

## Features

- **Dual Camera View**: Display 2 camera streams simultaneously
- **Camera Switching**: Select which cameras to display in each viewer
- **Photo Capture**: Capture photos from selected cameras with timestamp
- **Photo Gallery**: Browse, sort, and manage captured photos
- **Timestamp Overlay**: Add date/time and camera name to streams
- **IP Configuration**: Easy setup of Raspberry Pi connection
- **ArUco Marker Detection**: Real-time detection of ArUco markers (4x4_100 dictionary)

## Prerequisites

- Python 3.8+
- Tkinter (usually included with Python)
- Network connection to Raspberry Pi

## Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Create captures directory:**
```bash
mkdir -p captures
```

## Configuration

Edit `config.json` to set default values:
- Raspberry Pi IP address
- Camera ports
- Display settings
- Capture settings
- Overlay preferences

## Running the Application

```bash
python base_station_gui.py
```

## Usage Guide

### Connecting to Cameras

1. Click **File → IP Configuration** to set your Raspberry Pi's IP address
2. Click the **Connect** button to start streaming
3. The status bar will show connection status

### Viewing Streams

- Two camera views are displayed side by side
- Use the dropdown menus to select which camera to display in each view
- Double-click a view to maximize it (future feature)

### Capturing Photos

1. Click the **📷 Capture** button or press **Space**
2. Select which cameras to capture from
3. Choose save location (default: ./captures)
4. Click **Capture Selected**

Photos are saved with timestamp filenames:
- `cam1_2025-08-08_16-30-45.jpg`

### Photo Gallery

1. Click the **🖼️ Gallery** button or press **G**
2. Browse captured photos in thumbnail grid
3. Click a thumbnail to view full size
4. Select multiple photos for bulk operations:
   - Delete selected
   - Export to another folder

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Open capture dialog |
| G | Open photo gallery |
| A | Toggle ArUco detection |
| 1/2/3 | Switch camera in first viewer |
| F11 | Toggle fullscreen |
| Escape | Close dialogs |

### ArUco Marker Detection

1. **Enable Detection:**
   - Click View → ArUco Detection → Enable Detection
   - Or press 'A' to toggle

2. **View Results:**
   - ArUco status panel appears on the right
   - Click View → ArUco Detection → Show Detection Display
   - Separate window shows detailed results for judges

3. **Supported Markers:**
   - Dictionary: 4x4_100 (IDs 0-99)
   - Minimum size: 2" x 2" (5cm x 5cm)
   - Real-time detection with distance estimation

## Troubleshooting

### Cannot Connect to Streams

1. **Check Raspberry Pi is running:**
   ```bash
   ssh pi@[PI_IP]
   systemctl status camera-streaming
   ```

2. **Verify network connectivity:**
   ```bash
   ping [PI_IP]
   ```

3. **Check firewall settings:**
   - Ensure ports 8554-8556 are open
   - Disable firewall temporarily for testing

### Poor Stream Quality

- Reduce resolution in Raspberry Pi config
- Check network bandwidth
- Ensure good WiFi signal strength

### Application Crashes

- Check `base_station.log` for errors
- Verify all dependencies are installed
- Try with a single camera first

## Advanced Configuration

### Timestamp Overlay Options

In `config.json`:
```json
"overlay": {
  "enabled": true,
  "position": "bottom-left",  // or "bottom-right", "top-left", "top-right"
  "font_size": 12,
  "background_opacity": 0.7
}
```

### Stream Buffer Size

Adjust for latency vs. smoothness:
```json
"display": {
  "buffer_size": 5  // Lower = less latency, Higher = smoother playback
}
```

## Development

### Project Structure
```
base_station/
├── base_station_gui.py      # Main application
├── camera_viewer.py         # Camera display widget
├── stream_manager.py        # RTSP connection management
├── timestamp_overlay.py     # Overlay rendering
├── ip_config_dialog.py      # IP configuration dialog
├── photo_capture_dialog.py  # Photo capture dialog
├── photo_gallery.py         # Gallery viewer
├── aruco_detector.py        # ArUco marker detection
├── aruco_display_window.py  # ArUco results display
├── config.json             # Configuration file
└── captures/               # Captured photos directory
```

### Adding New Features

1. Create new module in appropriate file
2. Import in `base_station_gui.py`
3. Add menu items or buttons as needed
4. Update keyboard shortcuts if applicable

## Known Issues

- Fullscreen double-click not yet implemented
- No audio support (RTSP video only)
- Gallery pagination not implemented