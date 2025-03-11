#!/usr/bin/env python3
"""
Device profile selection dialog for the emulator GUI.
This module provides a dialog for selecting and configuring device profiles.
"""

import os
import sys
import logging
import json

try:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
        QPushButton, QGroupBox, QFormLayout, QDialogButtonBox,
        QTabWidget, QWidget, QLineEdit, QCheckBox, QMessageBox
    )
    from PyQt5.QtCore import Qt, pyqtSignal
    USE_PYQT5 = True
except ImportError:
    try:
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
            QPushButton, QGroupBox, QFormLayout, QDialogButtonBox,
            QTabWidget, QWidget, QLineEdit, QCheckBox, QMessageBox
        )
        from PySide6.QtCore import Qt, Signal as pyqtSignal
        USE_PYQT5 = False
    except ImportError:
        print("Error: Neither PyQt5 nor PySide6 is installed. Please install one of them.")
        sys.exit(1)

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.device_profile_db import DeviceProfileDB
    from anti_detection.hardware_spoof import HardwareSpoofer
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

logger = logging.getLogger(__name__)

class DeviceProfileDialog(QDialog):
    """Dialog for selecting and configuring device profiles."""
    
    profileSelected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize the device profile dialog."""
        super().__init__(parent)
        
        self.setWindowTitle("Device Profile Selection")
        self.setMinimumSize(600, 400)
        
        # Initialize components
        self.db = DeviceProfileDB()
        self.hardware_spoofer = HardwareSpoofer()
        
        self.selected_profile = None
        
        # Build the UI
        self._create_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Initialize available profiles
        self._load_manufacturers()
        
    def _create_ui(self):
        """Create the user interface."""
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Create tabs
        self.database_tab = QWidget()
        self.custom_tab = QWidget()
        
        tab_widget.addTab(self.database_tab, "Real Device Database")
        tab_widget.addTab(self.custom_tab, "Custom Profile")
        
        # Set up each tab
        self._setup_database_tab()
        self._setup_custom_tab()
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        main_layout.addWidget(button_box)
        
    def _setup_database_tab(self):
        """Set up the Real Device Database tab."""
        layout = QVBoxLayout(self.database_tab)
        
        # Selection group
        selection_group = QGroupBox("Select Device")
        selection_layout = QFormLayout()
        selection_group.setLayout(selection_layout)
        
        self.manufacturer_combo = QComboBox()
        self.device_combo = QComboBox()
        self.android_version_combo = QComboBox()
        
        selection_layout.addRow("Manufacturer:", self.manufacturer_combo)
        selection_layout.addRow("Device:", self.device_combo)
        selection_layout.addRow("Android Version:", self.android_version_combo)
        
        layout.addWidget(selection_group)
        
        # Device details group
        details_group = QGroupBox("Device Details")
        details_layout = QFormLayout()
        details_group.setLayout(details_layout)
        
        self.model_label = QLabel("")
        self.fingerprint_label = QLabel("")
        self.hardware_label = QLabel("")
        self.sensors_label = QLabel("")
        
        details_layout.addRow("Model:", self.model_label)
        details_layout.addRow("Build Fingerprint:", self.fingerprint_label)
        details_layout.addRow("Hardware:", self.hardware_label)
        details_layout.addRow("Sensors:", self.sensors_label)
        
        layout.addWidget(details_group)
        
        # Identity options group
        identity_group = QGroupBox("Identity Options")
        identity_layout = QFormLayout()
        identity_group.setLayout(identity_layout)
        
        self.random_ids_check = QCheckBox("Generate random identifiers")
        self.random_ids_check.setChecked(True)
        
        identity_layout.addRow("", self.random_ids_check)
        
        layout.addWidget(identity_group)
        
        # Stretch to fill remaining space
        layout.addStretch()
        
    def _setup_custom_tab(self):
        """Set up the Custom Profile tab."""
        layout = QVBoxLayout(self.custom_tab)
        
        # Basic info group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout()
        basic_group.setLayout(basic_layout)
        
        self.custom_manufacturer_input = QLineEdit("Samsung")
        self.custom_model_input = QLineEdit("Galaxy S21")
        
        self.custom_android_version_combo = QComboBox()
        for version in ["8.0", "8.1", "9.0", "10.0", "11.0", "12.0", "13.0", "14.0"]:
            self.custom_android_version_combo.addItem(f"Android {version}", version)
        self.custom_android_version_combo.setCurrentIndex(5)  # Default to Android 12.0
        
        basic_layout.addRow("Manufacturer:", self.custom_manufacturer_input)
        basic_layout.addRow("Model:", self.custom_model_input)
        basic_layout.addRow("Android Version:", self.custom_android_version_combo)
        
        layout.addWidget(basic_group)
        
        # Sensors group
        sensors_group = QGroupBox("Available Sensors")
        sensors_layout = QVBoxLayout()
        sensors_group.setLayout(sensors_layout)
        
        self.accelerometer_check = QCheckBox("Accelerometer")
        self.gyroscope_check = QCheckBox("Gyroscope")
        self.magnetometer_check = QCheckBox("Magnetometer")
        self.proximity_check = QCheckBox("Proximity")
        self.light_check = QCheckBox("Light")
        self.pressure_check = QCheckBox("Pressure")
        self.temperature_check = QCheckBox("Temperature")
        self.humidity_check = QCheckBox("Humidity")
        
        self.accelerometer_check.setChecked(True)
        self.gyroscope_check.setChecked(True)
        self.magnetometer_check.setChecked(True)
        self.proximity_check.setChecked(True)
        self.light_check.setChecked(True)
        
        sensors_layout.addWidget(self.accelerometer_check)
        sensors_layout.addWidget(self.gyroscope_check)
        sensors_layout.addWidget(self.magnetometer_check)
        sensors_layout.addWidget(self.proximity_check)
        sensors_layout.addWidget(self.light_check)
        sensors_layout.addWidget(self.pressure_check)
        sensors_layout.addWidget(self.temperature_check)
        sensors_layout.addWidget(self.humidity_check)
        
        layout.addWidget(sensors_group)
        
        # Create Profile button
        self.create_profile_button = QPushButton("Create Custom Profile")
        layout.addWidget(self.create_profile_button)
        
        # Stretch to fill remaining space
        layout.addStretch()
        
    def _connect_signals(self):
        """Connect signals for UI interactions."""
        self.manufacturer_combo.currentIndexChanged.connect(self._on_manufacturer_changed)
        self.device_combo.currentIndexChanged.connect(self._on_device_changed)
        self.android_version_combo.currentIndexChanged.connect(self._on_version_changed)
        self.create_profile_button.clicked.connect(self._on_create_custom_profile)
        
    def _load_manufacturers(self):
        """Load the list of manufacturers."""
        self.manufacturer_combo.clear()
        
        for manufacturer in self.db.get_manufacturers():
            self.manufacturer_combo.addItem(manufacturer, manufacturer)
            
        if self.manufacturer_combo.count() > 0:
            # Load devices for first manufacturer
            self._on_manufacturer_changed()
            
    def _on_manufacturer_changed(self):
        """Handle manufacturer selection change."""
        manufacturer = self.manufacturer_combo.currentData()
        if not manufacturer:
            return
            
        self.device_combo.clear()
        
        devices = self.db.get_devices(manufacturer)
        for device in devices:
            self.device_combo.addItem(device, device)
            
        if self.device_combo.count() > 0:
            # Load details for first device
            self._on_device_changed()
            
    def _on_device_changed(self):
        """Handle device selection change."""
        manufacturer = self.manufacturer_combo.currentData()
        device = self.device_combo.currentData()
        
        if not manufacturer or not device:
            return
            
        # Load profile
        profile = self.db.get_device_profile(manufacturer, device)
        
        if not profile:
            return
            
        # Update Android version combo
        self.android_version_combo.clear()
        
        for version in profile["android_versions"]:
            self.android_version_combo.addItem(f"Android {version}", version)
            
        # Set details
        self.model_label.setText(profile["model"])
        self.fingerprint_label.setText(profile["properties"]["ro.build.fingerprint"])
        self.hardware_label.setText(profile["properties"].get("ro.hardware", "unknown"))
        self.sensors_label.setText(", ".join(profile["sensors"]))
        
        # Generate the hardware profile
        self._update_selected_profile()
        
    def _on_version_changed(self):
        """Handle Android version selection change."""
        self._update_selected_profile()
        
    def _update_selected_profile(self):
        """Update the selected profile based on UI selections."""
        manufacturer = self.manufacturer_combo.currentData()
        device = self.device_combo.currentData()
        android_version = self.android_version_combo.currentData()
        
        if not manufacturer or not device or not android_version:
            return
            
        # Generate hardware profile
        self.selected_profile = self.db.generate_hardware_profile(
            manufacturer, device, android_version
        )
        
        # Generate random IDs if checked
        if self.random_ids_check.isChecked() and self.selected_profile:
            self.selected_profile["identifiers"]["imei"] = self.db._generate_imei()
            self.selected_profile["identifiers"]["serial"] = self.db._generate_serial()
            self.selected_profile["identifiers"]["mac_address"] = self.db._generate_mac_address()
            self.selected_profile["identifiers"]["android_id"] = self.db._generate_android_id()
            self.selected_profile["build_prop"]["ro.serialno"] = self.selected_profile["identifiers"]["serial"]
            self.selected_profile["build_prop"]["ro.boot.serialno"] = self.selected_profile["identifiers"]["serial"]
        
    def _on_create_custom_profile(self):
        """Create a custom device profile."""
        manufacturer = self.custom_manufacturer_input.text().strip()
        model = self.custom_model_input.text().strip()
        android_version = self.custom_android_version_combo.currentData()
        
        if not manufacturer or not model or not android_version:
            QMessageBox.warning(self, "Input Error", "Please fill in all fields")
            return
            
        # Collect selected sensors
        sensors = []
        if self.accelerometer_check.isChecked():
            sensors.append("accelerometer")
        if self.gyroscope_check.isChecked():
            sensors.append("gyroscope")
        if self.magnetometer_check.isChecked():
            sensors.append("magnetometer")
        if self.proximity_check.isChecked():
            sensors.append("proximity")
        if self.light_check.isChecked():
            sensors.append("light")
        if self.pressure_check.isChecked():
            sensors.append("pressure")
        if self.temperature_check.isChecked():
            sensors.append("temperature")
        if self.humidity_check.isChecked():
            sensors.append("humidity")
        
        # Use the hardware spoofer to create a profile
        self.selected_profile = self.hardware_spoofer.create_new_profile(
            manufacturer, model, android_version
        )
        
        # Update sensors
        self.selected_profile["sensors"] = {
            "accelerometer": "accelerometer" in sensors,
            "gyroscope": "gyroscope" in sensors,
            "magnetometer": "magnetometer" in sensors,
            "proximity": "proximity" in sensors,
            "light": "light" in sensors,
            "pressure": "pressure" in sensors,
            "temperature": "temperature" in sensors,
            "humidity": "humidity" in sensors
        }
        
        QMessageBox.information(self, "Profile Created", 
                               f"Custom profile for {manufacturer} {model} created successfully")
        
    def accept(self):
        """Handle dialog acceptance."""
        if not self.selected_profile:
            QMessageBox.warning(self, "No Profile", "Please select or create a device profile")
            return
            
        # Emit the selected profile
        self.profileSelected.emit(self.selected_profile)
        
        super().accept()

if __name__ == "__main__":
    # Simple test
    import sys
    from PyQt5.QtWidgets import QApplication
    
    logging.basicConfig(level=logging.INFO)
    
    app = QApplication(sys.argv)
    dialog = DeviceProfileDialog()
    
    def on_profile_selected(profile):
        print("Selected profile:", json.dumps(profile, indent=2))
        
    dialog.profileSelected.connect(on_profile_selected)
    
    dialog.show()
    app.exec_()