#!/usr/bin/env python3
"""
GUI interface for the undetected Android emulator.
This module provides a user-friendly interface for controlling the emulator.
"""

import sys
import os
import logging
import threading
import time
import json
from pathlib import Path

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
        QLabel, QComboBox, QTabWidget, QGroupBox, QFormLayout, QLineEdit,
        QCheckBox, QFileDialog, QMessageBox, QSlider, QTextEdit, QSplitter,
        QListWidget, QListWidgetItem, QProgressBar, QSpinBox, QInputDialog
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal
    from PyQt5.QtGui import QIcon, QPixmap
    USE_PYQT5 = True
except ImportError:
    try:
        from PySide6.QtWidgets import (
            QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
            QLabel, QComboBox, QTabWidget, QGroupBox, QFormLayout, QLineEdit,
            QCheckBox, QFileDialog, QMessageBox, QSlider, QTextEdit, QSplitter,
            QListWidget, QListWidgetItem, QProgressBar, QSpinBox, QInputDialog
        )
        from PySide6.QtCore import Qt, QTimer, Signal as pyqtSignal
        from PySide6.QtGui import QIcon, QPixmap
        USE_PYQT5 = False
    except ImportError:
        raise ImportError("Neither PyQt5 nor PySide6 could be imported. Please install one of them.")

from ..core.qemu_wrapper import QEMUWrapper
from ..core.image_manager import ImageManager
from ..core.android_customizer import AndroidCustomizer
from ..anti_detection.hardware_spoof import HardwareSpoofer
from ..anti_detection.sensor_simulator import SensorSimulator
from ..anti_detection.frida_manager import FridaManager
from ..anti_detection.device_profiles import DeviceProfileDatabase

# Import our custom widgets
from .image_download_widget import ImageDownloadWidget
from .device_profile_widget import DeviceProfileWidget

logger = logging.getLogger(__name__)

class EmulatorGUI(QMainWindow):
    """Main GUI window for the undetected Android emulator."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("Undetected Android Emulator")
        self.resize(1024, 768)
        
        # Initialize components
        self.qemu = QEMUWrapper()
        self.image_manager = ImageManager()
        self.android_customizer = AndroidCustomizer()
        self.sensor_simulator = SensorSimulator()
        self.frida_manager = FridaManager()
        self.device_profile_db = DeviceProfileDatabase()
        
        # Set up the UI
        self.init_ui()
        
        # Setup timers for updates
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # Update every second
        
        # State variables
        self.emulator_running = False
        self.selected_system_image = None
        self.selected_data_image = None
        self.selected_device_profile = None
        self.sensor_simulation_active = False
        
        logger.info("GUI initialized")
        
    def init_ui(self):
        """Initialize the user interface."""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QVBoxLayout(main_widget)
        
        # Create tab widget for different sections
        self.tabs = QTabWidget()
        
        # Add tabs
        self.tabs.addTab(self.create_main_tab(), "Main")
        self.tabs.addTab(self.create_images_tab(), "Images")
        self.tabs.addTab(self.create_profiles_tab(), "Device Profiles")
        self.tabs.addTab(self.create_detection_tab(), "Anti-Detection")
        self.tabs.addTab(self.create_settings_tab(), "Settings")
        self.tabs.addTab(self.create_logs_tab(), "Logs")
        
        main_layout.addWidget(self.tabs)
        
        # Status bar at the bottom
        self.status_label = QLabel("Status: Ready")
        main_layout.addWidget(self.status_label)
        
    def create_main_tab(self):
        """Create the main control tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Emulator controls group
        control_group = QGroupBox("Emulator Controls")
        control_layout = QVBoxLayout(control_group)
        
        # Start/Stop buttons
        buttons_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Emulator")
        self.start_button.clicked.connect(self.start_emulator)
        buttons_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Emulator")
        self.stop_button.clicked.connect(self.stop_emulator)
        self.stop_button.setEnabled(False)
        buttons_layout.addWidget(self.stop_button)
        
        control_layout.addLayout(buttons_layout)
        
        # Current configuration display
        config_layout = QFormLayout()
        
        self.system_image_label = QLabel("None selected")
        config_layout.addRow("System Image:", self.system_image_label)
        
        self.data_image_label = QLabel("None selected")
        config_layout.addRow("Data Image:", self.data_image_label)
        
        self.device_profile_label = QLabel("None selected")
        config_layout.addRow("Device Profile:", self.device_profile_label)
        
        self.target_app_input = QLineEdit()
        self.target_app_input.setPlaceholderText("com.linkedin.android")
        config_layout.addRow("Target App:", self.target_app_input)
        
        self.memory_spinner = QSpinBox()
        self.memory_spinner.setRange(1024, 8192)
        self.memory_spinner.setValue(2048)
        self.memory_spinner.setSingleStep(512)
        self.memory_spinner.setSuffix(" MB")
        config_layout.addRow("Memory:", self.memory_spinner)
        
        self.cores_spinner = QSpinBox()
        self.cores_spinner.setRange(1, 8)
        self.cores_spinner.setValue(4)
        config_layout.addRow("CPU Cores:", self.cores_spinner)
        
        control_layout.addLayout(config_layout)
        
        # LinkedIn mode checkbox
        self.linkedin_mode_checkbox = QCheckBox("LinkedIn Detection Bypass Mode")
        self.linkedin_mode_checkbox.setChecked(True)
        control_layout.addWidget(self.linkedin_mode_checkbox)
        
        # Quick setup button
        quick_setup_button = QPushButton("Quick Setup (Auto-configure)")
        quick_setup_button.clicked.connect(self.quick_setup)
        control_layout.addWidget(quick_setup_button)
        
        # Add the control group to the tab
        layout.addWidget(control_group)
        
        # Emulator status group
        status_group = QGroupBox("Emulator Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        status_layout.addWidget(self.status_text)
        
        layout.addWidget(status_group)
        
        return tab
        
    def create_images_tab(self):
        """Create the images management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.image_download_widget = ImageDownloadWidget()
        self.image_download_widget.image_selected.connect(self.on_system_image_selected)
        
        layout.addWidget(self.image_download_widget)
        
        return tab
        
    def create_profiles_tab(self):
        """Create the device profiles management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.device_profile_widget = DeviceProfileWidget()
        self.device_profile_widget.profile_selected.connect(self.on_device_profile_selected)
        
        layout.addWidget(self.device_profile_widget)
        
        return tab
        
    def create_detection_tab(self):
        """Create the anti-detection settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Frida script section
        frida_group = QGroupBox("Frida Scripts")
        frida_layout = QVBoxLayout(frida_group)
        
        self.script_list = QListWidget()
        script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                               "src", "anti_detection", "frida_scripts")
        
        if os.path.exists(script_dir):
            for script_file in os.listdir(script_dir):
                if script_file.endswith('.js'):
                    item = QListWidgetItem(script_file)
                    item.setData(Qt.UserRole, os.path.join(script_dir, script_file))
                    self.script_list.addItem(item)
                    
                    # Select the LinkedIn bypass script by default
                    if script_file == "linkedin_bypass.js":
                        self.script_list.setCurrentItem(item)
        
        frida_layout.addWidget(self.script_list)
        
        script_buttons_layout = QHBoxLayout()
        
        view_script_button = QPushButton("View Script")
        view_script_button.clicked.connect(self.view_frida_script)
        script_buttons_layout.addWidget(view_script_button)
        
        add_script_button = QPushButton("Add Script")
        add_script_button.clicked.connect(self.add_frida_script)
        script_buttons_layout.addWidget(add_script_button)
        
        frida_layout.addLayout(script_buttons_layout)
        
        layout.addWidget(frida_group)
        
        # Sensor simulation section
        sensor_group = QGroupBox("Sensor Simulation")
        sensor_layout = QVBoxLayout(sensor_group)
        
        self.enable_sensors_checkbox = QCheckBox("Enable Sensor Simulation")
        self.enable_sensors_checkbox.setChecked(True)
        sensor_layout.addWidget(self.enable_sensors_checkbox)
        
        sensor_config_layout = QFormLayout()
        
        self.accelerometer_noise_slider = QSlider(Qt.Horizontal)
        self.accelerometer_noise_slider.setRange(0, 100)
        self.accelerometer_noise_slider.setValue(20)
        sensor_config_layout.addRow("Accelerometer Noise:", self.accelerometer_noise_slider)
        
        self.touch_randomization_checkbox = QCheckBox("Randomize Touch Input Patterns")
        self.touch_randomization_checkbox.setChecked(True)
        sensor_config_layout.addRow("", self.touch_randomization_checkbox)
        
        sensor_layout.addLayout(sensor_config_layout)
        
        layout.addWidget(sensor_group)
        
        # Anti-detection methods section
        methods_group = QGroupBox("Anti-Detection Methods")
        methods_layout = QVBoxLayout(methods_group)
        
        self.methods_list = QListWidget()
        methods = [
            "Hardware ID Spoofing", 
            "Build.prop Customization",
            "Frida API Hooking",
            "Virtualization Masking",
            "Sensor Data Simulation",
            "Network Traffic Normalization",
            "Touch Input Randomization",
            "Camera API Spoofing"
        ]
        
        for method in methods:
            item = QListWidgetItem()
            item.setText(method)
            item.setCheckState(Qt.Checked)
            self.methods_list.addItem(item)
            
        methods_layout.addWidget(self.methods_list)
        
        layout.addWidget(methods_group)
        
        return tab
        
    def create_settings_tab(self):
        """Create the settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # QEMU settings
        qemu_group = QGroupBox("QEMU Settings")
        qemu_layout = QFormLayout(qemu_group)
        
        self.qemu_path_input = QLineEdit()
        self.qemu_path_input.setText("qemu-system-x86_64")
        
        qemu_path_layout = QHBoxLayout()
        qemu_path_layout.addWidget(self.qemu_path_input)
        
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_qemu_path)
        qemu_path_layout.addWidget(browse_button)
        
        qemu_layout.addRow("QEMU Path:", qemu_path_layout)
        
        self.enable_kvm_checkbox = QCheckBox("Enable KVM acceleration")
        self.enable_kvm_checkbox.setChecked(True)
        qemu_layout.addRow("", self.enable_kvm_checkbox)
        
        self.enable_vnc_checkbox = QCheckBox("Enable VNC server")
        qemu_layout.addRow("", self.enable_vnc_checkbox)
        
        self.vnc_port_spinner = QSpinBox()
        self.vnc_port_spinner.setRange(5900, 5999)
        self.vnc_port_spinner.setValue(5900)
        self.vnc_port_spinner.setEnabled(False)
        qemu_layout.addRow("VNC Port:", self.vnc_port_spinner)
        
        # Connect the VNC checkbox to the port spinner
        self.enable_vnc_checkbox.stateChanged.connect(
            lambda state: self.vnc_port_spinner.setEnabled(state == Qt.Checked)
        )
        
        layout.addWidget(qemu_group)
        
        # Advanced settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)
        
        self.auto_inject_checkbox = QCheckBox("Auto-inject Frida on app launch")
        self.auto_inject_checkbox.setChecked(True)
        advanced_layout.addRow("", self.auto_inject_checkbox)
        
        self.persistent_profiles_checkbox = QCheckBox("Save profiles between sessions")
        self.persistent_profiles_checkbox.setChecked(True)
        advanced_layout.addRow("", self.persistent_profiles_checkbox)
        
        self.debug_logging_checkbox = QCheckBox("Enable debug logging")
        advanced_layout.addRow("", self.debug_logging_checkbox)
        
        # Connect debug logging checkbox
        self.debug_logging_checkbox.stateChanged.connect(self.toggle_debug_logging)
        
        layout.addWidget(advanced_group)
        
        # Add a stretch to make the layout look better
        layout.addStretch(1)
        
        return tab
        
    def create_logs_tab(self):
        """Create the logs tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        self.log_text.setStyleSheet("font-family: monospace;")
        
        # Create a log handler that updates the log text in a thread-safe way
        class QTextEditLoggerSignals(QObject):
            appendPlainText = pyqtSignal(str)
            
        class QTextEditLogger(logging.Handler):
            def __init__(self, text_edit):
                super().__init__()
                self.text_edit = text_edit
                self.signals = QTextEditLoggerSignals()
                self.signals.appendPlainText.connect(self.text_edit.append)
                self.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
                
            def emit(self, record):
                msg = self.format(record)
                # Use signal to safely update the text edit from any thread
                self.signals.appendPlainText.emit(msg)
                
        # Add the handler to the root logger
        log_handler = QTextEditLogger(self.log_text)
        logging.getLogger().addHandler(log_handler)
        
        layout.addWidget(self.log_text)
        
        # Log control buttons
        buttons_layout = QHBoxLayout()
        
        clear_button = QPushButton("Clear Logs")
        clear_button.clicked.connect(self.log_text.clear)
        buttons_layout.addWidget(clear_button)
        
        save_button = QPushButton("Save Logs")
        save_button.clicked.connect(self.save_logs)
        buttons_layout.addWidget(save_button)
        
        layout.addLayout(buttons_layout)
        
        return tab
        
    def update_status(self):
        """Update the status displays."""
        if self.emulator_running:
            self.status_label.setText("Status: Emulator Running")
            
            # Update status text with more details
            status_info = [
                f"Emulator Status: Running",
                f"System Image: {os.path.basename(self.selected_system_image) if self.selected_system_image else 'None'}",
                f"Data Image: {os.path.basename(self.selected_data_image) if self.selected_data_image else 'None'}",
                f"Device Profile: {self.selected_device_profile['manufacturer'] + ' ' + self.selected_device_profile['model'] if self.selected_device_profile else 'None'}",
                f"Memory: {self.memory_spinner.value()} MB",
                f"CPU Cores: {self.cores_spinner.value()}",
                f"Sensor Simulation: {'Active' if self.sensor_simulation_active else 'Inactive'}",
                f"Target App: {self.target_app_input.text() or 'None'}",
                f"LinkedIn Mode: {'Enabled' if self.linkedin_mode_checkbox.isChecked() else 'Disabled'}"
            ]
            
            self.status_text.setText("\n".join(status_info))
        else:
            self.status_label.setText("Status: Ready")
            
            # Clear the status text or show configuration
            if self.selected_system_image or self.selected_device_profile:
                config_info = [
                    f"Emulator Status: Stopped",
                    f"System Image: {os.path.basename(self.selected_system_image) if self.selected_system_image else 'None'}",
                    f"Data Image: {os.path.basename(self.selected_data_image) if self.selected_data_image else 'None'}",
                    f"Device Profile: {self.selected_device_profile['manufacturer'] + ' ' + self.selected_device_profile['model'] if self.selected_device_profile else 'None'}"
                ]
                self.status_text.setText("\n".join(config_info))
            else:
                self.status_text.setText("Emulator not configured. Please select a system image and device profile.")
    
    def on_system_image_selected(self, image_path):
        """Handle system image selection."""
        self.selected_system_image = image_path
        self.system_image_label.setText(os.path.basename(image_path))
        logger.info(f"Selected system image: {image_path}")
        
    def on_device_profile_selected(self, profile):
        """Handle device profile selection."""
        self.selected_device_profile = profile
        self.device_profile_label.setText(f"{profile['manufacturer']} {profile['model']}")
        logger.info(f"Selected device profile: {profile['manufacturer']} {profile['model']}")
        
    def browse_qemu_path(self):
        """Browse for QEMU executable."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select QEMU Executable",
            "/usr/bin",
            "All Files (*)"
        )
        
        if file_path:
            self.qemu_path_input.setText(file_path)
            
    def toggle_debug_logging(self, state):
        """Toggle debug logging."""
        if state == Qt.Checked:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled")
        else:
            logging.getLogger().setLevel(logging.INFO)
            logger.info("Debug logging disabled")
            
    def save_logs(self):
        """Save logs to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Logs",
            os.path.join(os.path.expanduser("~"), "emulator_logs.txt"),
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write(self.log_text.toPlainText())
                    
                logger.info(f"Logs saved to {file_path}")
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error Saving Logs",
                    f"Failed to save logs: {str(e)}"
                )
                
    def view_frida_script(self):
        """View the selected Frida script."""
        items = self.script_list.selectedItems()
        if items:
            script_path = items[0].data(Qt.UserRole)
            
            try:
                with open(script_path, "r") as f:
                    script_content = f.read()
                    
                # Create a dialog to show the script
                dialog = QDialog(self)
                dialog.setWindowTitle(f"Frida Script: {items[0].text()}")
                dialog.resize(800, 600)
                
                layout = QVBoxLayout(dialog)
                
                script_text = QTextEdit()
                script_text.setReadOnly(True)
                script_text.setLineWrapMode(QTextEdit.NoWrap)
                script_text.setStyleSheet("font-family: monospace;")
                script_text.setText(script_content)
                
                layout.addWidget(script_text)
                
                close_button = QPushButton("Close")
                close_button.clicked.connect(dialog.accept)
                layout.addWidget(close_button)
                
                dialog.exec_()
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error Reading Script",
                    f"Failed to read script: {str(e)}"
                )
                
    def add_frida_script(self):
        """Add a custom Frida script."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Frida Script",
            str(Path.home()),
            "JavaScript Files (*.js);;All Files (*)"
        )
        
        if file_path:
            script_name = os.path.basename(file_path)
            
            # Check if script with same name already exists
            for i in range(self.script_list.count()):
                if self.script_list.item(i).text() == script_name:
                    QMessageBox.warning(
                        self,
                        "Script Already Exists",
                        f"A script with the name '{script_name}' already exists."
                    )
                    return
                    
            # Add to the list
            item = QListWidgetItem(script_name)
            item.setData(Qt.UserRole, file_path)
            self.script_list.addItem(item)
            
            logger.info(f"Added custom Frida script: {file_path}")
            
    def quick_setup(self):
        """Perform quick setup with automatic configuration."""
        # Try to find a system image
        if not self.selected_system_image:
            available_images = self.image_manager.get_available_images()
            if available_images:
                self.selected_system_image = available_images[0]['path']
                self.system_image_label.setText(os.path.basename(self.selected_system_image))
                logger.info(f"Auto-selected system image: {self.selected_system_image}")
            else:
                QMessageBox.warning(
                    self,
                    "No System Images",
                    "No system images available. Please download one in the Images tab."
                )
                self.tabs.setCurrentIndex(1)  # Switch to Images tab
                return
                
        # Create a data image if not selected
        if not self.selected_data_image:
            self.selected_data_image = self.image_manager.create_empty_image("auto_data", size_gb=8)
            if self.selected_data_image:
                self.data_image_label.setText(os.path.basename(self.selected_data_image))
                logger.info(f"Created data image: {self.selected_data_image}")
                
        # Select a device profile if not selected
        if not self.selected_device_profile:
            self.selected_device_profile = self.device_profile_db.get_random_profile()
            if self.selected_device_profile:
                self.device_profile_label.setText(
                    f"{self.selected_device_profile['manufacturer']} {self.selected_device_profile['model']}"
                )
                logger.info(f"Auto-selected device profile: {self.selected_device_profile['manufacturer']} {self.selected_device_profile['model']}")
            else:
                QMessageBox.warning(
                    self,
                    "No Device Profiles",
                    "No device profiles available. Please create one in the Device Profiles tab."
                )
                self.tabs.setCurrentIndex(2)  # Switch to Device Profiles tab
                return
                
        # Set LinkedIn as target app if not specified
        if not self.target_app_input.text():
            self.target_app_input.setText("com.linkedin.android")
            
        # Enable LinkedIn mode
        self.linkedin_mode_checkbox.setChecked(True)
        
        # Show confirmation
        QMessageBox.information(
            self,
            "Quick Setup Complete",
            "Emulator has been automatically configured. You can now start the emulator."
        )
        
    def start_emulator(self):
        """Start the emulator with current configuration."""
        # Validate configuration
        if not self.selected_system_image:
            QMessageBox.warning(
                self,
                "Missing System Image",
                "Please select a system image before starting the emulator."
            )
            return
            
        # Configure QEMU
        self.qemu.set_param("cdrom", self.selected_system_image)
        
        if self.selected_data_image:
            self.qemu.set_param("hda", self.selected_data_image)
            
        self.qemu.set_param("memory", str(self.memory_spinner.value()))
        self.qemu.set_param("smp", str(self.cores_spinner.value()))
        
        # KVM acceleration if enabled
        if self.enable_kvm_checkbox.isChecked():
            self.qemu.set_param("enable-kvm", "")
            
        # VNC server if enabled
        if self.enable_vnc_checkbox.isChecked():
            self.qemu.set_param("vnc", f":{self.vnc_port_spinner.value() - 5900}")
            
        # Apply device profile if selected
        if self.selected_device_profile:
            # Configure sensor simulation
            if self.enable_sensors_checkbox.isChecked():
                if "sensors" in self.selected_device_profile:
                    sensor_profile = {
                        "sensors": self.selected_device_profile["sensors"],
                        "device": {
                            "manufacturer": self.selected_device_profile["manufacturer"],
                            "model": self.selected_device_profile["model"]
                        }
                    }
                    self.sensor_simulator.set_profile(sensor_profile)
                    logger.info("Configured sensor simulation from device profile")
            
        # Start the emulator
        if self.qemu.start():
            logger.info("Emulator started successfully")
            
            self.emulator_running = True
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            # Start sensor simulation if enabled
            if self.enable_sensors_checkbox.isChecked() and self.sensor_simulator.current_profile:
                if self.sensor_simulator.start_simulation():
                    self.sensor_simulation_active = True
                    logger.info("Sensor simulation started")
            
            # Configure and start Frida
            if self.auto_inject_checkbox.isChecked():
                # Get the selected Frida script
                script_path = None
                items = self.script_list.selectedItems()
                if items:
                    script_path = items[0].data(Qt.UserRole)
                    
                if script_path:
                    self.frida_manager.load_script(script_path)
                    
                    # Set target app if specified
                    target_app = self.target_app_input.text().strip()
                    if target_app:
                        self.frida_manager.set_target_package(target_app)
                        
                    # Start monitoring for app launch
                    self.frida_manager.start_monitoring()
                    logger.info(f"Frida monitoring started for {target_app}")
        else:
            QMessageBox.critical(
                self,
                "Emulator Start Failed",
                "Failed to start the emulator. Check the logs for details."
            )
            
    def stop_emulator(self):
        """Stop the running emulator."""
        # Stop Frida injection
        if self.frida_manager.is_monitoring:
            self.frida_manager.stop_monitoring()
            logger.info("Stopped Frida monitoring")
            
        # Stop sensor simulation
        if self.sensor_simulation_active:
            self.sensor_simulator.stop_simulation()
            self.sensor_simulation_active = False
            logger.info("Stopped sensor simulation")
            
        # Stop QEMU
        if self.qemu.stop():
            logger.info("Emulator stopped")
            
            self.emulator_running = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
        else:
            QMessageBox.warning(
                self,
                "Stop Failed",
                "Failed to stop the emulator gracefully. It may still be running."
            )
            
    def closeEvent(self, event):
        """Handle window close event."""
        if self.emulator_running:
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "The emulator is still running. Stop it and exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.stop_emulator()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("emulator_gui.log")
        ]
    )
    
    # Create and show the GUI
    app = QApplication(sys.argv)
    window = EmulatorGUI()
    window.show()
    
    sys.exit(app.exec_() if hasattr(app, 'exec_') else app.exec())