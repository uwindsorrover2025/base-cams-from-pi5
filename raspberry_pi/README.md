# Raspberry Pi Camera Streaming Server

This server streams USB cameras connected to a Raspberry Pi via RTSP protocol.

## Prerequisites

- Raspberry Pi 5 (or compatible)
- 3 USB cameras
- Python 3.9+
- GStreamer libraries

## Installation

1. **Install system dependencies:**
```bash
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-opencv \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-rtsp \
    libgstrtspserver-1.0-0 \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-rtsp-server-1.0
```

2. **Install Python dependencies:**
```bash
pip3 install -r requirements.txt
```

## Configuration

Edit `config.json` to customize settings:
- Camera resolution and FPS
- RTSP server ports
- Mount points for each camera

## Running the Server

### Manual Start
```bash
python3 pi_streaming_server.py
```

### With Debug Mode
```bash
python3 pi_streaming_server.py --debug
```

### As a System Service

1. Create service file:
```bash
sudo nano /etc/systemd/system/camera-streaming.service
```

2. Add the following content:
```ini
[Unit]
Description=Camera Streaming Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/camera_streaming/raspberry_pi
ExecStart=/usr/bin/python3 /home/pi/camera_streaming/raspberry_pi/pi_streaming_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable camera-streaming
sudo systemctl start camera-streaming
```

4. Check service status:
```bash
sudo systemctl status camera-streaming
```

## Stream URLs

Once running, the server will display RTSP URLs for each camera:
- Camera 0: `rtsp://[PI_IP]:8554/cam1`
- Camera 1: `rtsp://[PI_IP]:8555/cam2`
- Camera 2: `rtsp://[PI_IP]:8556/cam3`

## Troubleshooting

### Camera Not Detected
- Check USB connections
- Run `ls /dev/video*` to see available devices
- Check permissions: `sudo usermod -a -G video $USER`

### Stream Not Working
- Check firewall: `sudo ufw allow 8554:8556/tcp`
- Verify GStreamer installation: `gst-inspect-1.0 rtspserver`
- Check logs: `journalctl -u camera-streaming -f`

### Performance Issues
- Monitor CPU usage with `htop`
- Reduce resolution or FPS in config.json
- Ensure adequate power supply for Pi and cameras

## Logs

Logs are saved to `streaming_server.log` in the current directory.