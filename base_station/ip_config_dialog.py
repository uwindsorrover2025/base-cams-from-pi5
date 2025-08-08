#!/usr/bin/env python3
"""
IP Configuration Dialog
Modal dialog for configuring Raspberry Pi IP address and ports
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from typing import Dict, List, Optional
import socket
import threading

class IPConfigDialog(tk.Toplevel):
    def __init__(self, parent, current_config: Dict, saved_ips: List[str] = None):
        """
        Initialize IP configuration dialog
        
        Args:
            parent: Parent window
            current_config: Current configuration dictionary
            saved_ips: List of previously saved IP addresses
        """
        super().__init__(parent)
        
        self.parent = parent
        self.current_config = current_config.copy()
        self.saved_ips = saved_ips or []
        self.result = None
        
        # Window setup
        self.title("IP Configuration")
        self.geometry("400x350")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Create UI
        self._create_widgets()
        
        # Center window
        self._center_window()
        
        # Focus on IP entry
        self.ip_entry.focus_set()
        
    def _center_window(self):
        """Center the dialog on parent window"""
        self.update_idletasks()
        
        # Get parent position
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get dialog size
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        
        # Calculate position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f"+{x}+{y}")
        
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main frame with padding
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title label
        title_label = ttk.Label(
            main_frame,
            text="Configure Raspberry Pi Connection",
            font=('TkDefaultFont', 12, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # IP Address section
        ttk.Label(main_frame, text="IP Address:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # IP entry with dropdown for saved IPs
        ip_frame = ttk.Frame(main_frame)
        ip_frame.grid(row=1, column=1, sticky=tk.EW, pady=5)
        
        self.ip_var = tk.StringVar(value=self.current_config.get('ip', '192.168.1.100'))
        
        if self.saved_ips:
            self.ip_entry = ttk.Combobox(
                ip_frame,
                textvariable=self.ip_var,
                values=self.saved_ips,
                width=20
            )
        else:
            self.ip_entry = ttk.Entry(ip_frame, textvariable=self.ip_var, width=20)
            
        self.ip_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Test connection button
        self.test_button = ttk.Button(
            ip_frame,
            text="Test",
            command=self._test_connection,
            width=6
        )
        self.test_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Port configuration
        ttk.Label(main_frame, text="Camera Ports:").grid(row=2, column=0, sticky=tk.NW, pady=(20, 5))
        
        ports_frame = ttk.Frame(main_frame)
        ports_frame.grid(row=2, column=1, sticky=tk.EW, pady=(20, 5))
        
        self.port_vars = {}
        default_ports = self.current_config.get('ports', {})
        
        for i, (cam, default_port) in enumerate([
            ('cam1', 8554), ('cam2', 8555), ('cam3', 8556)
        ]):
            ttk.Label(ports_frame, text=f"Camera {i+1}:").grid(row=i, column=0, sticky=tk.W, pady=2)
            
            self.port_vars[cam] = tk.IntVar(value=default_ports.get(cam, default_port))
            port_entry = ttk.Entry(
                ports_frame,
                textvariable=self.port_vars[cam],
                width=10
            )
            port_entry.grid(row=i, column=1, sticky=tk.W, padx=(5, 0), pady=2)
            
        # Status label
        self.status_label = ttk.Label(main_frame, text="", foreground="gray")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=4, column=0, columnspan=2, sticky=tk.EW, pady=10
        )
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, sticky=tk.E)
        
        ttk.Button(
            button_frame,
            text="OK",
            command=self._on_ok,
            width=10
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=10
        ).pack(side=tk.LEFT)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        
        # Bind Enter key
        self.bind('<Return>', lambda e: self._on_ok())
        self.bind('<Escape>', lambda e: self._on_cancel())
        
    def _validate_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            return True
        except:
            return False
            
    def _test_connection(self):
        """Test connection to Raspberry Pi"""
        ip = self.ip_var.get().strip()
        
        if not self._validate_ip(ip):
            messagebox.showerror("Invalid IP", "Please enter a valid IP address")
            return
            
        # Disable button during test
        self.test_button.config(state='disabled', text='Testing...')
        self.status_label.config(text="Testing connection...", foreground="blue")
        
        # Run test in thread to avoid blocking UI
        thread = threading.Thread(target=self._test_connection_thread, args=(ip,))
        thread.daemon = True
        thread.start()
        
    def _test_connection_thread(self, ip: str):
        """Test connection in separate thread"""
        try:
            # Try to connect to first camera port
            port = self.port_vars['cam1'].get()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            # Update UI in main thread
            if result == 0:
                self.after(0, self._test_success, ip)
            else:
                self.after(0, self._test_failed, f"Cannot connect to {ip}:{port}")
                
        except Exception as e:
            self.after(0, self._test_failed, str(e))
            
    def _test_success(self, ip: str):
        """Handle successful connection test"""
        self.test_button.config(state='normal', text='Test')
        self.status_label.config(
            text=f"✓ Successfully connected to {ip}",
            foreground="green"
        )
        
    def _test_failed(self, error: str):
        """Handle failed connection test"""
        self.test_button.config(state='normal', text='Test')
        self.status_label.config(
            text=f"✗ Connection failed: {error}",
            foreground="red"
        )
        
    def _on_ok(self):
        """Handle OK button click"""
        ip = self.ip_var.get().strip()
        
        # Validate IP
        if not self._validate_ip(ip):
            messagebox.showerror("Invalid IP", "Please enter a valid IP address")
            return
            
        # Validate ports
        ports = {}
        for cam, var in self.port_vars.items():
            try:
                port = var.get()
                if port < 1 or port > 65535:
                    raise ValueError
                ports[cam] = port
            except:
                messagebox.showerror(
                    "Invalid Port",
                    f"Please enter valid port numbers (1-65535)"
                )
                return
                
        # Save result
        self.result = {
            'ip': ip,
            'ports': ports
        }
        
        self.destroy()
        
    def _on_cancel(self):
        """Handle Cancel button click"""
        self.result = None
        self.destroy()
        
    def get_result(self) -> Optional[Dict]:
        """Get dialog result"""
        return self.result


# Example usage for testing
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test Main Window")
    root.geometry("600x400")
    
    def show_dialog():
        config = {
            'ip': '192.168.1.100',
            'ports': {'cam1': 8554, 'cam2': 8555, 'cam3': 8556}
        }
        saved_ips = ['192.168.1.100', '192.168.1.101', '10.0.0.5']
        
        dialog = IPConfigDialog(root, config, saved_ips)
        root.wait_window(dialog)
        
        if dialog.get_result():
            print(f"New configuration: {dialog.get_result()}")
        else:
            print("Dialog cancelled")
            
    ttk.Button(root, text="Open IP Config", command=show_dialog).pack(pady=50)
    
    root.mainloop()