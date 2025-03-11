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
        QListWidget, QProgressBar
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
            QListWidget, QProgressBar
        )
        from PySide6.QtCore import Qt, QTimer, Signal as pyqtSignal
        from PySide6.QtGui import QIcon, QPixmap
        USE_PYQT5 = False
    except ImportError:
        print("Error: Neither PyQt5 nor PySide6 is installed. Please install one of them.")
        sys.exit(1)

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.qemu_wrapper import QEMUWrapper
    from anti_detection.hardware_spoof import HardwareSpoofer
    from anti_detection.sensor_simulator import SensorSimulator
    from anti_detection.frida_manager import FridaManager
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

logger = logging.getLogger(__name__)

class LogHandler(logging.Handler):
    """Custom log handler that emits signals with log messages."""
    
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
        
    def emit(self, record):
        log_entry = self.format(record)
        self.signal.emit(log_entry)

class EmulatorGUI(QMainWindow):
    """Main GUI window for the undetected Android emulator."""
    
    log_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Undetected Android Emulator")
        self.setMinimumSize(800, 600)
        
        # Initialize components
        self.qemu = QEMUWrapper()
        self.hardware_spoofer = HardwareSpoofer()
        self.sensor_simulator = SensorSimulator()
        self.frida_manager = None  # Initialized later, only when needed
        
        # Set up logging
        self._setup_logging()
        
        # Build the UI
        self._create_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Initialize state
        self.emulator_running = False
        self.sensor_simulation_active = False
        
        logger.info("Emulator GUI initialized")
        
    def _setup_logging(self):
        """Set up logging to capture logs in the UI."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Create a handler that emits signals
        handler = LogHandler(self.log_signal)
        handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
        root_logger.addHandler(handler)
        
    def _create_ui(self):
        """Create the user interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Create tabs
        self.emulator_tab = QWidget()
        self.hardware_tab = QWidget()
        self.sensors_tab = QWidget()
        self.anti_detection_tab = QWidget()
        self.settings_tab = QWidget()
        
        tab_widget.addTab(self.emulator_tab, "Emulator")
        tab_widget.addTab(self.hardware_tab, "Hardware Profile")
        tab_widget.addTab(self.sensors_tab, "Sensor Simulation")
        tab_widget.addTab(self.anti_detection_tab, "Anti-Detection")
        tab_widget.addTab(self.settings_tab, "Settings")
        
        # Set up each tab
        self._setup_emulator_tab()
        self._setup_hardware_tab()
        self._setup_sensors_tab()
        self._setup_anti_detection_tab()
        self._setup_settings_tab()
        
        # Log area at the bottom
        log_group = QGroupBox("Logs")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        main_layout.addWidget(log_group)
        
    def _setup_emulator_tab(self):
        """Set up the Emulator tab."""
        layout = QVBoxLayout(self.emulator_tab)
        
        # Control group
        control_group = QGroupBox("Emulator Control")
        control_layout = QHBoxLayout()
        control_group.setLayout(control_layout)
        
        self.start_button = QPushButton("Start Emulator")
        self.stop_button = QPushButton("Stop Emulator")
        self.stop_button.setEnabled(False)
        self.screenshot_button = QPushButton("Take Screenshot")
        self.screenshot_button.setEnabled(False)
        
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.screenshot_button)
        
        layout.addWidget(control_group)
        
        # Configuration group
        config_group = QGroupBox("Emulator Configuration")
        config_layout = QFormLayout()
        config_group.setLayout(config_layout)
        
        self.system_image_path = QLineEdit()
        self.browse_button = QPushButton("Browse...")
        
        system_image_layout = QHBoxLayout()
        system_image_layout.addWidget(self.system_image_path)
        system_image_layout.addWidget(self.browse_button)
        
        self.memory_combo = QComboBox()
        for mem in ["1024", "2048", "4096", "8192"]:
            self.memory_combo.addItem(f"{mem} MB", mem)
        self.memory_combo.setCurrentIndex(1)  # Default to 2048 MB
        
        self.cpu_cores_combo = QComboBox()
        for cores in ["1", "2", "4", "8"]:
            self.cpu_cores_combo.addItem(f"{cores} core(s)", cores)
        self.cpu_cores_combo.setCurrentIndex(2)  # Default to 4 cores
        
        self.display_combo = QComboBox()
        self.display_combo.addItem("GTK", "gtk")
        self.display_combo.addItem("SDL", "sdl")
        self.display_combo.addItem("None (Headless)", "none")
        
        config_layout.addRow("System Image:", system_image_layout)
        config_layout.addRow("Memory:", self.memory_combo)
        config_layout.addRow("CPU Cores:", self.cpu_cores_combo)
        config_layout.addRow("Display:", self.display_combo)
        
        layout.addWidget(config_group)
        
        # Status group
        status_group = QGroupBox("Emulator Status")
        status_layout = QFormLayout()
        status_group.setLayout(status_layout)
        
        self.status_label = QLabel("Not running")
        self.uptime_label = QLabel("0:00:00")
        self.cpu_usage_label = QLabel("0%")
        self.memory_usage_label = QLabel("0%")
        
        status_layout.addRow("Status:", self.status_label)
        status_layout.addRow("Uptime:", self.uptime_label)
        status_layout.addRow("CPU Usage:", self.cpu_usage_label)
        status_layout.addRow("Memory Usage:", self.memory_usage_label)
        
        layout.addWidget(status_group)
        
        # Stretch to fill remaining space
        layout.addStretch()
        
    def _setup_hardware_tab(self):
        """Set up the Hardware Profile tab."""
        layout = QVBoxLayout(self.hardware_tab)
        
        # Profile selection group
        profile_group = QGroupBox("Hardware Profile")
        profile_layout = QHBoxLayout()
        profile_group.setLayout(profile_layout)
        
        self.profile_combo = QComboBox()
        self.profile_combo.addItem("Create New Profile...", "new")
        
        # Add existing profiles
        for profile in self.hardware_spoofer.available_profiles:
            self.profile_combo.addItem(profile, profile)
            
        self.load_profile_button = QPushButton("Load")
        self.save_profile_button = QPushButton("Save")
        self.delete_profile_button = QPushButton("Delete")
        
        profile_layout.addWidget(QLabel("Profile:"))
        profile_layout.addWidget(self.profile_combo, 1)
        profile_layout.addWidget(self.load_profile_button)
        profile_layout.addWidget(self.save_profile_button)
        profile_layout.addWidget(self.delete_profile_button)
        
        layout.addWidget(profile_group)
        
        # Device information group
        device_group = QGroupBox("Device Information")
        device_layout = QFormLayout()
        device_group.setLayout(device_layout)
        
        self.manufacturer_input = QLineEdit("Samsung")
        self.model_input = QLineEdit("Galaxy S21")
        
        self.android_version_combo = QComboBox()
        for version in ["8.0", "8.1", "9.0", "10.0", "11.0", "12.0", "13.0", "14.0"]:
            self.android_version_combo.addItem(f"Android {version}", version)
        self.android_version_combo.setCurrentIndex(5)  # Default to Android 12.0
        
        device_layout.addRow("Manufacturer:", self.manufacturer_input)
        device_layout.addRow("Model:", self.model_input)
        device_layout.addRow("Android Version:", self.android_version_combo)
        
        layout.addWidget(device_group)
        
        # Identifiers group
        identifiers_group = QGroupBox("Device Identifiers")
        identifiers_layout = QFormLayout()
        identifiers_group.setLayout(identifiers_layout)
        
        self.imei_input = QLineEdit()
        self.imei_input.setReadOnly(True)
        self.serial_input = QLineEdit()
        self.serial_input.setReadOnly(True)
        self.mac_address_input = QLineEdit()
        self.mac_address_input.setReadOnly(True)
        self.android_id_input = QLineEdit()
        self.android_id_input.setReadOnly(True)
        
        self.regenerate_ids_button = QPushButton("Regenerate IDs")
        
        identifiers_layout.addRow("IMEI:", self.imei_input)
        identifiers_layout.addRow("Serial:", self.serial_input)
        identifiers_layout.addRow("MAC Address:", self.mac_address_input)
        identifiers_layout.addRow("Android ID:", self.android_id_input)
        identifiers_layout.addRow("", self.regenerate_ids_button)
        
        layout.addWidget(identifiers_group)
        
        # Stretch to fill remaining space
        layout.addStretch()
        
    def _setup_sensors_tab(self):
        """Set up the Sensor Simulation tab."""
        layout = QVBoxLayout(self.sensors_tab)
        
        # Sensor profile group
        profile_group = QGroupBox("Sensor Profile")
        profile_layout = QHBoxLayout()
        profile_group.setLayout(profile_layout)
        
        self.sensor_profile_combo = QComboBox()
        self.sensor_profile_combo.addItem("Create New Profile...", "new")
        
        # Add existing profiles
        for profile in self.sensor_simulator.available_profiles:
            self.sensor_profile_combo.addItem(profile, profile)
            
        self.load_sensor_profile_button = QPushButton("Load")
        self.save_sensor_profile_button = QPushButton("Save")
        
        profile_layout.addWidget(QLabel("Profile:"))
        profile_layout.addWidget(self.sensor_profile_combo, 1)
        profile_layout.addWidget(self.load_sensor_profile_button)
        profile_layout.addWidget(self.save_sensor_profile_button)
        
        layout.addWidget(profile_group)
        
        # Device type and activity
        device_group = QGroupBox("Device Configuration")
        device_layout = QFormLayout()
        device_group.setLayout(device_layout)
        
        self.device_type_combo = QComboBox()
        self.device_type_combo.addItem("Smartphone", "smartphone")
        self.device_type_combo.addItem("Tablet", "tablet")
        self.device_type_combo.addItem("Smartwatch", "smartwatch")
        
        self.activity_type_combo = QComboBox()
        self.activity_type_combo.addItem("Stationary", "stationary")
        self.activity_type_combo.addItem("Walking", "walking")
        self.activity_type_combo.addItem("Running", "running")
        self.activity_type_combo.addItem("Driving", "driving")
        
        self.create_sensor_profile_button = QPushButton("Create Profile")
        
        device_layout.addRow("Device Type:", self.device_type_combo)
        device_layout.addRow("Activity Type:", self.activity_type_combo)
        device_layout.addRow("", self.create_sensor_profile_button)
        
        layout.addWidget(device_group)
        
        # Sensor controls
        control_group = QGroupBox("Sensor Simulation Control")
        control_layout = QHBoxLayout()
        control_group.setLayout(control_layout)
        
        self.start_simulation_button = QPushButton("Start Simulation")
        self.stop_simulation_button = QPushButton("Stop Simulation")
        self.stop_simulation_button.setEnabled(False)
        
        control_layout.addWidget(self.start_simulation_button)
        control_layout.addWidget(self.stop_simulation_button)
        
        layout.addWidget(control_group)
        
        # Sensor values display
        values_group = QGroupBox("Current Sensor Values")
        values_layout = QFormLayout()
        values_group.setLayout(values_layout)
        
        self.accelerometer_x_label = QLabel("0.0")
        self.accelerometer_y_label = QLabel("0.0")
        self.accelerometer_z_label = QLabel("9.81")
        
        self.gyroscope_x_label = QLabel("0.0")
        self.gyroscope_y_label = QLabel("0.0")
        self.gyroscope_z_label = QLabel("0.0")
        
        acc_layout = QHBoxLayout()
        acc_layout.addWidget(QLabel("x:"))
        acc_layout.addWidget(self.accelerometer_x_label)
        acc_layout.addWidget(QLabel("y:"))
        acc_layout.addWidget(self.accelerometer_y_label)
        acc_layout.addWidget(QLabel("z:"))
        acc_layout.addWidget(self.accelerometer_z_label)
        
        gyro_layout = QHBoxLayout()
        gyro_layout.addWidget(QLabel("x:"))
        gyro_layout.addWidget(self.gyroscope_x_label)
        gyro_layout.addWidget(QLabel("y:"))
        gyro_layout.addWidget(self.gyroscope_y_label)
        gyro_layout.addWidget(QLabel("z:"))
        gyro_layout.addWidget(self.gyroscope_z_label)
        
        values_layout.addRow("Accelerometer:", acc_layout)
        values_layout.addRow("Gyroscope:", gyro_layout)
        
        layout.addWidget(values_group)
        
        # Stretch to fill remaining space
        layout.addStretch()
        
    def _setup_anti_detection_tab(self):
        """Set up the Anti-Detection tab."""
        layout = QVBoxLayout(self.anti_detection_tab)
        
        # Frida section
        frida_group = QGroupBox("Frida Runtime Manipulation")
        frida_layout = QVBoxLayout()
        frida_group.setLayout(frida_layout)
        
        # Application list
        apps_layout = QHBoxLayout()
        apps_layout.addWidget(QLabel("Running Applications:"))
        
        self.apps_list = QListWidget()
        self.refresh_apps_button = QPushButton("Refresh")
        
        apps_layout.addWidget(self.apps_list, 1)
        
        refresh_layout = QVBoxLayout()
        refresh_layout.addWidget(self.refresh_apps_button)
        refresh_layout.addStretch()
        
        apps_layout.addLayout(refresh_layout)
        
        frida_layout.addLayout(apps_layout)
        
        # Injection controls
        injection_layout = QHBoxLayout()
        
        self.inject_button = QPushButton("Inject Anti-Detection")
        self.detach_button = QPushButton("Detach from Application")
        
        injection_layout.addWidget(self.inject_button)
        injection_layout.addWidget(self.detach_button)
        
        frida_layout.addLayout(injection_layout)
        
        layout.addWidget(frida_group)
        
        # Additional anti-detection options
        options_group = QGroupBox("Anti-Detection Options")
        options_layout = QVBoxLayout()
        options_group.setLayout(options_layout)
        
        self.disable_qemu_props_check = QCheckBox("Disable QEMU Properties")
        self.disable_qemu_props_check.setChecked(True)
        
        self.randomize_touch_check = QCheckBox("Randomize Touch Input Patterns")
        self.randomize_touch_check.setChecked(True)
        
        self.hide_virtual_files_check = QCheckBox("Hide Virtual Device Files")
        self.hide_virtual_files_check.setChecked(True)
        
        options_layout.addWidget(self.disable_qemu_props_check)
        options_layout.addWidget(self.randomize_touch_check)
        options_layout.addWidget(self.hide_virtual_files_check)
        
        layout.addWidget(options_group)
        
        # Testing section
        testing_group = QGroupBox("Detection Testing")
        testing_layout = QVBoxLayout()
        testing_group.setLayout(testing_layout)
        
        self.test_linkedin_button = QPushButton("Test LinkedIn Detection")
        self.test_custom_button = QPushButton("Test Custom Application")
        
        testing_layout.addWidget(self.test_linkedin_button)
        testing_layout.addWidget(self.test_custom_button)
        
        layout.addWidget(testing_group)
        
        # Stretch to fill remaining space
        layout.addStretch()
        
    def _setup_settings_tab(self):
        """Set up the Settings tab."""
        layout = QVBoxLayout(self.settings_tab)
        
        # General settings group
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout()
        general_group.setLayout(general_layout)
        
        self.auto_start_check = QCheckBox()
        self.auto_save_check = QCheckBox()
        
        general_layout.addRow("Auto-start on launch:", self.auto_start_check)
        general_layout.addRow("Auto-save profiles:", self.auto_save_check)
        
        layout.addWidget(general_group)
        
        # Paths group
        paths_group = QGroupBox("File Paths")
        paths_layout = QFormLayout()
        paths_group.setLayout(paths_layout)
        
        self.profiles_path_input = QLineEdit()
        self.profiles_path_input.setText(os.path.expanduser("~/.config/undetected-emulator/"))
        self.profiles_path_button = QPushButton("Browse...")
        
        profiles_path_layout = QHBoxLayout()
        profiles_path_layout.addWidget(self.profiles_path_input)
        profiles_path_layout.addWidget(self.profiles_path_button)
        
        paths_layout.addRow("Profiles directory:", profiles_path_layout)
        
        layout.addWidget(paths_group)
        
        # Advanced settings group
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QVBoxLayout()
        advanced_group.setLayout(advanced_layout)
        
        self.enable_logging_check = QCheckBox("Enable detailed logging")
        self.enable_logging_check.setChecked(True)
        
        self.debug_mode_check = QCheckBox("Debug mode")
        
        advanced_layout.addWidget(self.enable_logging_check)
        advanced_layout.addWidget(self.debug_mode_check)
        
        layout.addWidget(advanced_group)
        
        # About section
        about_group = QGroupBox("About")
        about_layout = QVBoxLayout()
        about_group.setLayout(about_layout)
        
        about_text = QLabel(
            "Undetected Android Emulator v0.1.0\n"
            "© 2025 agentbryce2025\n\n"
            "This application provides an Android emulator with anti-detection capabilities.\n"
            "For research and educational purposes only."
        )
        about_text.setAlignment(Qt.AlignCenter)
        
        about_layout.addWidget(about_text)
        
        layout.addWidget(about_group)
        
        # Stretch to fill remaining space
        layout.addStretch()
        
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        # Emulator tab
        self.start_button.clicked.connect(self.start_emulator)
        self.stop_button.clicked.connect(self.stop_emulator)
        self.screenshot_button.clicked.connect(self.take_screenshot)
        self.browse_button.clicked.connect(self.browse_system_image)
        
        # Hardware tab
        self.profile_combo.currentIndexChanged.connect(self.on_profile_changed)
        self.load_profile_button.clicked.connect(self.load_hardware_profile)
        self.save_profile_button.clicked.connect(self.save_hardware_profile)
        self.delete_profile_button.clicked.connect(self.delete_hardware_profile)
        self.regenerate_ids_button.clicked.connect(self.regenerate_identifiers)
        
        # Sensors tab
        self.sensor_profile_combo.currentIndexChanged.connect(self.on_sensor_profile_changed)
        self.load_sensor_profile_button.clicked.connect(self.load_sensor_profile)
        self.save_sensor_profile_button.clicked.connect(self.save_sensor_profile)
        self.create_sensor_profile_button.clicked.connect(self.create_sensor_profile)
        self.start_simulation_button.clicked.connect(self.start_sensor_simulation)
        self.stop_simulation_button.clicked.connect(self.stop_sensor_simulation)
        
        # Anti-detection tab
        self.refresh_apps_button.clicked.connect(self.refresh_applications)
        self.inject_button.clicked.connect(self.inject_anti_detection)
        self.detach_button.clicked.connect(self.detach_from_application)
        self.test_linkedin_button.clicked.connect(self.test_linkedin_detection)
        self.test_custom_button.clicked.connect(self.test_custom_application)
        
        # Settings tab
        self.profiles_path_button.clicked.connect(self.browse_profiles_path)
        
        # Log signal
        self.log_signal.connect(self.update_log)
        
    def start_emulator(self):
        """Start the Android emulator."""
        # Update QEMU parameters from UI
        self.qemu.set_param("memory", self.memory_combo.currentData())
        self.qemu.set_param("smp", self.cpu_cores_combo.currentData())
        self.qemu.set_param("display", self.display_combo.currentData())
        
        # Set system image if provided
        system_image = self.system_image_path.text()
        if system_image:
            self.qemu.set_param("hda", system_image)
        else:
            QMessageBox.warning(self, "Warning", "No system image selected!")
            return
            
        # Attempt to start the emulator
        if self.qemu.start():
            self.emulator_running = True
            self.status_label.setText("Running")
            
            # Update UI
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.screenshot_button.setEnabled(True)
            
            # Start a timer to update uptime
            self.start_time = time.time()
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.update_status)
            self.update_timer.start(1000)  # Update every second
            
            logger.info("Emulator started successfully")
        else:
            QMessageBox.critical(self, "Error", "Failed to start emulator!")
            logger.error("Failed to start emulator")
            
    def stop_emulator(self):
        """Stop the Android emulator."""
        if self.qemu.stop():
            self.emulator_running = False
            self.status_label.setText("Not running")
            
            # Update UI
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.screenshot_button.setEnabled(False)
            
            # Stop the update timer
            if hasattr(self, 'update_timer'):
                self.update_timer.stop()
                
            logger.info("Emulator stopped successfully")
        else:
            QMessageBox.critical(self, "Error", "Failed to stop emulator!")
            logger.error("Failed to stop emulator")
            
    def take_screenshot(self):
        """Take a screenshot of the current emulator state."""
        if not self.emulator_running:
            QMessageBox.warning(self, "Warning", "Emulator is not running!")
            return
            
        # Get save path from user
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Screenshot", "", "PNG Images (*.png);;All Files (*)"
        )
        
        if not save_path:
            return
            
        # Take the screenshot
        if self.qemu.screenshot(save_path):
            QMessageBox.information(self, "Success", f"Screenshot saved to {save_path}")
            logger.info(f"Screenshot saved to {save_path}")
        else:
            QMessageBox.critical(self, "Error", "Failed to take screenshot!")
            logger.error("Failed to take screenshot")
            
    def browse_system_image(self):
        """Browse for Android system image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Android System Image", "", 
            "Disk Images (*.img *.iso);;All Files (*)"
        )
        
        if file_path:
            self.system_image_path.setText(file_path)
            logger.info(f"Selected system image: {file_path}")
            
    def update_status(self):
        """Update the emulator status display."""
        if not self.emulator_running:
            return
            
        # Update uptime
        elapsed = int(time.time() - self.start_time)
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        
        self.uptime_label.setText(f"{hours}:{minutes:02d}:{seconds:02d}")
        
        # Check if emulator is still alive
        if not self.qemu.is_alive():
            logger.warning("Emulator process terminated unexpectedly")
            self.emulator_running = False
            self.status_label.setText("Terminated")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.screenshot_button.setEnabled(False)
            self.update_timer.stop()
            
            QMessageBox.warning(self, "Warning", "Emulator process terminated unexpectedly!")
            
    def on_profile_changed(self, index):
        """Handle hardware profile selection change."""
        if index <= 0:
            # New profile or invalid selection
            return
            
        profile_name = self.profile_combo.currentData()
        logger.info(f"Selected hardware profile: {profile_name}")
        
    def load_hardware_profile(self):
        """Load the selected hardware profile."""
        if self.profile_combo.currentIndex() <= 0:
            QMessageBox.warning(self, "Warning", "Please select a valid profile!")
            return
            
        profile_name = self.profile_combo.currentData()
        
        if self.hardware_spoofer.load_profile(profile_name):
            # Update UI with profile data
            profile = self.hardware_spoofer.current_profile
            
            self.manufacturer_input.setText(profile.get("manufacturer", ""))
            self.model_input.setText(profile.get("model", ""))
            
            # Set Android version
            android_version = profile.get("android_version", "12.0")
            index = self.android_version_combo.findData(android_version)
            if index >= 0:
                self.android_version_combo.setCurrentIndex(index)
                
            # Update identifiers
            identifiers = profile.get("identifiers", {})
            self.imei_input.setText(identifiers.get("imei", ""))
            self.serial_input.setText(identifiers.get("serial", ""))
            self.mac_address_input.setText(identifiers.get("mac_address", ""))
            self.android_id_input.setText(identifiers.get("android_id", ""))
            
            logger.info(f"Loaded hardware profile: {profile_name}")
            QMessageBox.information(self, "Success", f"Profile '{profile_name}' loaded successfully")
        else:
            QMessageBox.critical(self, "Error", f"Failed to load profile '{profile_name}'!")
            
    def save_hardware_profile(self):
        """Save the current hardware profile."""
        profile_name = self.profile_combo.currentData()
        
        if profile_name == "new":
            # Get profile name from user
            profile_name, ok = QInputDialog.getText(
                self, "Save Profile", "Enter profile name:"
            )
            
            if not ok or not profile_name:
                return
                
        # Create/update profile from UI values
        manufacturer = self.manufacturer_input.text()
        model = self.model_input.text()
        android_version = self.android_version_combo.currentData()
        
        # Create new profile or update existing
        if not self.hardware_spoofer.current_profile:
            self.hardware_spoofer.create_new_profile(manufacturer, model, android_version)
        else:
            # Update existing profile
            profile = self.hardware_spoofer.current_profile
            profile["manufacturer"] = manufacturer
            profile["model"] = model
            profile["android_version"] = android_version
            
        # Save the profile
        if self.hardware_spoofer.save_profile(profile_name):
            logger.info(f"Saved hardware profile: {profile_name}")
            
            # Update profile combo if needed
            if self.profile_combo.findData(profile_name) < 0:
                self.profile_combo.addItem(profile_name, profile_name)
                self.profile_combo.setCurrentText(profile_name)
                
            QMessageBox.information(self, "Success", f"Profile '{profile_name}' saved successfully")
        else:
            QMessageBox.critical(self, "Error", f"Failed to save profile '{profile_name}'!")
            
    def delete_hardware_profile(self):
        """Delete the selected hardware profile."""
        if self.profile_combo.currentIndex() <= 0:
            QMessageBox.warning(self, "Warning", "Please select a valid profile!")
            return
            
        profile_name = self.profile_combo.currentData()
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion", 
            f"Are you sure you want to delete the profile '{profile_name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        # Delete the profile file
        profile_file = os.path.join(
            self.hardware_spoofer.profile_path, f"{profile_name}.json"
        )
        
        try:
            if os.path.exists(profile_file):
                os.remove(profile_file)
                
                # Remove from combo box
                index = self.profile_combo.findData(profile_name)
                if index >= 0:
                    self.profile_combo.removeItem(index)
                    
                # Remove from spoofer's available profiles
                if profile_name in self.hardware_spoofer.available_profiles:
                    self.hardware_spoofer.available_profiles.remove(profile_name)
                    
                logger.info(f"Deleted hardware profile: {profile_name}")
                QMessageBox.information(self, "Success", f"Profile '{profile_name}' deleted successfully")
            else:
                QMessageBox.warning(self, "Warning", f"Profile file not found!")
        except Exception as e:
            logger.error(f"Error deleting profile '{profile_name}': {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to delete profile: {str(e)}")
            
    def regenerate_identifiers(self):
        """Regenerate device identifiers."""
        # Get basic device info from UI
        manufacturer = self.manufacturer_input.text()
        model = self.model_input.text()
        android_version = self.android_version_combo.currentData()
        
        # Create a new profile with these values to generate new IDs
        profile = self.hardware_spoofer.create_new_profile(manufacturer, model, android_version)
        
        # Update UI with new identifiers
        identifiers = profile.get("identifiers", {})
        self.imei_input.setText(identifiers.get("imei", ""))
        self.serial_input.setText(identifiers.get("serial", ""))
        self.mac_address_input.setText(identifiers.get("mac_address", ""))
        self.android_id_input.setText(identifiers.get("android_id", ""))
        
        logger.info("Regenerated device identifiers")
        
    def on_sensor_profile_changed(self, index):
        """Handle sensor profile selection change."""
        if index <= 0:
            # New profile or invalid selection
            return
            
        profile_name = self.sensor_profile_combo.currentData()
        logger.info(f"Selected sensor profile: {profile_name}")
        
    def load_sensor_profile(self):
        """Load the selected sensor profile."""
        if self.sensor_profile_combo.currentIndex() <= 0:
            QMessageBox.warning(self, "Warning", "Please select a valid sensor profile!")
            return
            
        profile_name = self.sensor_profile_combo.currentData()
        
        if self.sensor_simulator.load_profile(profile_name):
            # Update UI with profile data
            profile = self.sensor_simulator.current_profile
            
            # Set device type
            device_type = profile.get("device_type", "smartphone")
            index = self.device_type_combo.findData(device_type)
            if index >= 0:
                self.device_type_combo.setCurrentIndex(index)
                
            # Set activity type
            activity_type = profile.get("activity_type", "stationary")
            index = self.activity_type_combo.findData(activity_type)
            if index >= 0:
                self.activity_type_combo.setCurrentIndex(index)
                
            logger.info(f"Loaded sensor profile: {profile_name}")
            QMessageBox.information(self, "Success", f"Sensor profile '{profile_name}' loaded successfully")
        else:
            QMessageBox.critical(self, "Error", f"Failed to load sensor profile '{profile_name}'!")
            
    def save_sensor_profile(self):
        """Save the current sensor profile."""
        profile_name = self.sensor_profile_combo.currentData()
        
        if profile_name == "new" or not profile_name:
            # Get profile name from user
            profile_name, ok = QInputDialog.getText(
                self, "Save Sensor Profile", "Enter profile name:"
            )
            
            if not ok or not profile_name:
                return
                
        # Ensure we have a current profile
        if not self.sensor_simulator.current_profile:
            QMessageBox.warning(self, "Warning", "No sensor profile to save. Create a profile first!")
            return
                
        # Save the profile
        if self.sensor_simulator.save_profile(profile_name):
            logger.info(f"Saved sensor profile: {profile_name}")
            
            # Update profile combo if needed
            if self.sensor_profile_combo.findData(profile_name) < 0:
                self.sensor_profile_combo.addItem(profile_name, profile_name)
                self.sensor_profile_combo.setCurrentText(profile_name)
                
            QMessageBox.information(self, "Success", f"Sensor profile '{profile_name}' saved successfully")
        else:
            QMessageBox.critical(self, "Error", f"Failed to save sensor profile '{profile_name}'!")
            
    def create_sensor_profile(self):
        """Create a new sensor profile based on UI settings."""
        device_type = self.device_type_combo.currentData()
        activity_type = self.activity_type_combo.currentData()
        
        # Create the profile
        profile = self.sensor_simulator.create_device_profile(device_type, activity_type)
        
        if profile:
            logger.info(f"Created new sensor profile: {device_type}, {activity_type}")
            QMessageBox.information(
                self, "Success", 
                f"Created new sensor profile for {device_type} ({activity_type})"
            )
        else:
            QMessageBox.critical(self, "Error", "Failed to create sensor profile!")
            
    def start_sensor_simulation(self):
        """Start the sensor data simulation."""
        if not self.sensor_simulator.current_profile:
            QMessageBox.warning(self, "Warning", "No sensor profile loaded or created!")
            return
            
        if self.sensor_simulator.start_simulation():
            self.sensor_simulation_active = True
            
            # Update UI
            self.start_simulation_button.setEnabled(False)
            self.stop_simulation_button.setEnabled(True)
            
            # Start a timer to update sensor values display
            self.sensor_update_timer = QTimer()
            self.sensor_update_timer.timeout.connect(self.update_sensor_display)
            self.sensor_update_timer.start(100)  # Update 10 times per second
            
            logger.info("Sensor simulation started")
        else:
            QMessageBox.critical(self, "Error", "Failed to start sensor simulation!")
            
    def stop_sensor_simulation(self):
        """Stop the sensor data simulation."""
        if self.sensor_simulator.stop_simulation():
            self.sensor_simulation_active = False
            
            # Update UI
            self.start_simulation_button.setEnabled(True)
            self.stop_simulation_button.setEnabled(False)
            
            # Stop the update timer
            if hasattr(self, 'sensor_update_timer'):
                self.sensor_update_timer.stop()
                
            logger.info("Sensor simulation stopped")
        else:
            QMessageBox.critical(self, "Error", "Failed to stop sensor simulation!")
            
    def update_sensor_display(self):
        """Update the sensor values display."""
        if not self.sensor_simulation_active:
            return
            
        # Get current sensor values
        values = self.sensor_simulator.get_current_values()
        
        # Update accelerometer values
        if "accelerometer" in values:
            acc = values["accelerometer"]
            self.accelerometer_x_label.setText(f"{acc.get('x', 0.0):.2f}")
            self.accelerometer_y_label.setText(f"{acc.get('y', 0.0):.2f}")
            self.accelerometer_z_label.setText(f"{acc.get('z', 9.81):.2f}")
            
        # Update gyroscope values
        if "gyroscope" in values:
            gyro = values["gyroscope"]
            self.gyroscope_x_label.setText(f"{gyro.get('x', 0.0):.2f}")
            self.gyroscope_y_label.setText(f"{gyro.get('y', 0.0):.2f}")
            self.gyroscope_z_label.setText(f"{gyro.get('z', 0.0):.2f}")
            
    def refresh_applications(self):
        """Refresh the list of running applications."""
        # Initialize Frida manager if needed
        if not self.frida_manager:
            self.frida_manager = FridaManager()
            
        # Clear current list
        self.apps_list.clear()
        
        # Get running applications
        apps = self.frida_manager.list_running_applications()
        
        for app in apps:
            self.apps_list.addItem(f"{app['name']} ({app['identifier']})")
            
        if apps:
            logger.info(f"Found {len(apps)} running applications")
        else:
            logger.warning("No running applications found or Frida not connected")
            QMessageBox.warning(
                self, "Warning", 
                "No running applications found or Frida not connected to the device!"
            )
            
    def inject_anti_detection(self):
        """Inject anti-detection scripts into the selected application."""
        # Check if an application is selected
        if not self.apps_list.currentItem():
            QMessageBox.warning(self, "Warning", "Please select an application first!")
            return
            
        # Initialize Frida manager if needed
        if not self.frida_manager:
            self.frida_manager = FridaManager()
            
        # Extract application ID from selected item text
        item_text = self.apps_list.currentItem().text()
        app_id = item_text.split("(")[-1].split(")")[0]
        
        # Inject the detection bypass script
        if self.frida_manager.inject_detection_bypass(app_id):
            logger.info(f"Injected anti-detection into {app_id}")
            QMessageBox.information(
                self, "Success", 
                f"Anti-detection scripts injected into {app_id}"
            )
        else:
            QMessageBox.critical(
                self, "Error", 
                f"Failed to inject anti-detection scripts into {app_id}!"
            )
            
    def detach_from_application(self):
        """Detach from the selected application."""
        # Check if an application is selected
        if not self.apps_list.currentItem():
            QMessageBox.warning(self, "Warning", "Please select an application first!")
            return
            
        # Check if Frida manager is initialized
        if not self.frida_manager:
            QMessageBox.warning(self, "Warning", "Frida manager not initialized!")
            return
            
        # Extract application ID from selected item text
        item_text = self.apps_list.currentItem().text()
        app_id = item_text.split("(")[-1].split(")")[0]
        
        # Detach from the application
        if self.frida_manager.detach_from_application(app_id):
            logger.info(f"Detached from {app_id}")
            QMessageBox.information(self, "Success", f"Detached from {app_id}")
        else:
            QMessageBox.critical(self, "Error", f"Failed to detach from {app_id}!")
            
    def test_linkedin_detection(self):
        """Test LinkedIn emulator detection."""
        # TODO: Implement LinkedIn detection test
        QMessageBox.information(
            self, "Not Implemented", 
            "LinkedIn detection testing is not yet implemented."
        )
        
    def test_custom_application(self):
        """Test custom application emulator detection."""
        # TODO: Implement custom application detection test
        QMessageBox.information(
            self, "Not Implemented", 
            "Custom application detection testing is not yet implemented."
        )
        
    def browse_profiles_path(self):
        """Browse for profiles directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Profiles Directory", self.profiles_path_input.text()
        )
        
        if directory:
            self.profiles_path_input.setText(directory)
            
    def update_log(self, message):
        """Update the log display with a new message."""
        self.log_text.append(message)
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        
    def closeEvent(self, event):
        """Handle window close event."""
        # Stop emulator if running
        if self.emulator_running:
            self.stop_emulator()
            
        # Stop sensor simulation if running
        if self.sensor_simulation_active:
            self.stop_sensor_simulation()
            
        # Close Frida manager if initialized
        if self.frida_manager:
            self.frida_manager.close()
            
        # Accept the close event
        event.accept()


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("emulator.log")
        ]
    )
    
    app = QApplication(sys.argv)
    window = EmulatorGUI()
    window.show()
    sys.exit(app.exec_() if USE_PYQT5 else app.exec())