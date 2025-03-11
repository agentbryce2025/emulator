#!/usr/bin/env python3
"""
Frida scripts manager for the undetected Android emulator.
This module handles loading and managing Frida scripts for runtime manipulation.
"""

import os
import logging
import frida
import time
import threading
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class FridaManager:
    """Manages Frida scripts for runtime manipulation and anti-detection."""
    
    def __init__(self, scripts_dir=None, device_id=None):
        """Initialize Frida manager with optional scripts directory."""
        self.scripts_dir = scripts_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "frida_scripts"
        )
        self.device = None
        self.device_id = device_id
        self.sessions = {}
        self.scripts = {}
        self.connected = False
        
        # Ensure scripts directory exists
        os.makedirs(self.scripts_dir, exist_ok=True)
        
        # Try to connect to the device
        self._connect_to_device()
        
    def _connect_to_device(self):
        """Connect to the Android device using Frida."""
        try:
            if self.device_id:
                # Connect to specific device
                self.device = frida.get_device(self.device_id)
            else:
                # Get the local USB device
                try:
                    self.device = frida.get_usb_device(timeout=1)
                except frida.TimedOutError:
                    # Fall back to local device
                    try:
                        self.device = frida.get_local_device()
                    except frida.InvalidArgumentError:
                        # Try to get any available device
                        devices = frida.enumerate_devices()
                        if devices:
                            self.device = devices[0]
                        else:
                            logger.error("No devices available")
                            return False
            
            self.connected = True
            logger.info(f"Connected to device: {self.device.name} (id: {self.device.id})")
            return True
        except Exception as e:
            logger.error(f"Error connecting to device: {str(e)}")
            self.connected = False
            return False
            
    def get_device_info(self):
        """Get information about the connected device."""
        if not self.connected or not self.device:
            logger.error("Not connected to any device")
            return None
            
        try:
            device_info = {
                "id": self.device.id,
                "name": self.device.name,
                "type": self.device.type,
            }
            
            logger.info(f"Device info: {json.dumps(device_info)}")
            return device_info
        except Exception as e:
            logger.error(f"Error getting device info: {str(e)}")
            return None
            
    def list_running_applications(self):
        """List all running applications on the device."""
        if not self.connected or not self.device:
            logger.error("Not connected to any device")
            return []
            
        try:
            apps = self.device.enumerate_applications()
            app_list = [{"name": app.name, "identifier": app.identifier, "pid": app.pid} for app in apps]
            
            logger.info(f"Found {len(app_list)} running applications")
            return app_list
        except Exception as e:
            logger.error(f"Error listing applications: {str(e)}")
            return []
            
    def get_available_scripts(self):
        """Get a list of available Frida scripts."""
        try:
            scripts = []
            for file in os.listdir(self.scripts_dir):
                if file.endswith(".js"):
                    scripts.append(file)
                    
            logger.info(f"Found {len(scripts)} Frida scripts")
            return scripts
        except Exception as e:
            logger.error(f"Error listing scripts: {str(e)}")
            return []
            
    def _on_message(self, message, data, app_id):
        """Handle messages from Frida scripts."""
        if message["type"] == "send":
            logger.info(f"[{app_id}] {message['payload']}")
        elif message["type"] == "error":
            logger.error(f"[{app_id}] {message['stack']}")
            
    def inject_script(self, app_id, script_name=None, script_content=None):
        """Inject a Frida script into a running application."""
        if not self.connected or not self.device:
            logger.error("Not connected to any device")
            return False
            
        if not script_name and not script_content:
            logger.error("Either script_name or script_content must be provided")
            return False
            
        # Determine script content
        if script_name and not script_content:
            script_path = os.path.join(self.scripts_dir, script_name)
            if not os.path.exists(script_path):
                logger.error(f"Script {script_name} not found")
                return False
                
            try:
                with open(script_path, "r") as f:
                    script_content = f.read()
            except Exception as e:
                logger.error(f"Error reading script {script_name}: {str(e)}")
                return False
                
        try:
            # Check if we already have a session for this app
            if app_id in self.sessions:
                # Resume if suspended
                if not self.sessions[app_id].is_detached:
                    logger.info(f"Session for {app_id} already exists")
                    return True
                else:
                    # Session is detached, clean it up
                    del self.sessions[app_id]
                    if app_id in self.scripts:
                        del self.scripts[app_id]
            
            # Try to attach to the process
            try:
                # First, try by identifier (package name)
                session = self.device.attach(app_id)
            except frida.ProcessNotFoundError:
                # If that fails, try by PID if it's a number
                if app_id.isdigit():
                    session = self.device.attach(int(app_id))
                else:
                    # Try to spawn the process
                    pid = self.device.spawn([app_id])
                    session = self.device.attach(pid)
                    self.device.resume(pid)
            
            # Create a script with the provided content
            script = session.create_script(script_content)
            
            # Set up the message handler
            script.on("message", lambda message, data: self._on_message(message, data, app_id))
            
            # Load the script
            script.load()
            
            # Store session and script
            self.sessions[app_id] = session
            self.scripts[app_id] = script
            
            logger.info(f"Injected script into {app_id}")
            return True
        except Exception as e:
            logger.error(f"Error injecting script into {app_id}: {str(e)}")
            return False
            
    def inject_detection_bypass(self, app_id):
        """Inject the detection bypass script into a running application."""
        bypass_script = "detection_bypass.js"
        return self.inject_script(app_id, script_name=bypass_script)
        
    def detach_from_application(self, app_id):
        """Detach from a running application."""
        if app_id not in self.sessions:
            logger.warning(f"No session for {app_id}")
            return False
            
        try:
            # Unload the script if it exists
            if app_id in self.scripts:
                try:
                    self.scripts[app_id].unload()
                except:
                    pass
                del self.scripts[app_id]
            
            # Detach the session
            try:
                if not self.sessions[app_id].is_detached:
                    self.sessions[app_id].detach()
            except:
                pass
            del self.sessions[app_id]
            
            logger.info(f"Detached from {app_id}")
            return True
        except Exception as e:
            logger.error(f"Error detaching from {app_id}: {str(e)}")
            return False
            
    def detach_all(self):
        """Detach from all applications."""
        app_ids = list(self.sessions.keys())
        success = True
        
        for app_id in app_ids:
            if not self.detach_from_application(app_id):
                success = False
                
        return success
        
    def close(self):
        """Clean up resources before shutting down."""
        self.detach_all()
        self.connected = False
        logger.info("Frida manager closed")


if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    
    print("Starting Frida Manager test...")
    
    frida_manager = FridaManager()
    
    print("Connected to device:", frida_manager.connected)
    
    if frida_manager.connected:
        print("Device info:", frida_manager.get_device_info())
        print("Available scripts:", frida_manager.get_available_scripts())
        
        print("Running applications:")
        for app in frida_manager.list_running_applications():
            print(f"- {app['name']} ({app['identifier']})")
            
        # Test would continue with actual app injection if run on a real device
        
    frida_manager.close()
    print("Frida Manager test complete.")