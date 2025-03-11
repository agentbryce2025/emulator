#!/usr/bin/env python3
"""
Device profile management widget for the undetected Android emulator GUI.
This module provides a user interface for managing device profiles.
"""

import sys
import os
import logging
import json
from pathlib import Path

try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, 
        QListWidget, QListWidgetItem, QMessageBox, QFileDialog, QTabWidget,
        QGroupBox, QFormLayout, QLineEdit, QSpinBox, QTextEdit, QDialog
    )
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QIcon
except ImportError:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, 
        QListWidget, QListWidgetItem, QMessageBox, QFileDialog, QTabWidget,
        QGroupBox, QFormLayout, QLineEdit, QSpinBox, QTextEdit, QDialog
    )
    from PySide6.QtCore import Qt, Signal as pyqtSignal
    from PySide6.QtGui import QIcon

from ..anti_detection.device_profiles import DeviceProfileDatabase

logger = logging.getLogger(__name__)

class ProfileDetailsDialog(QDialog):
    """Dialog for viewing detailed profile information."""
    
    def __init__(self, profile_data, parent=None):
        """Initialize the profile details dialog."""
        super().__init__(parent)
        self.profile_data = profile_data
        self.setWindowTitle(f"Profile Details: {profile_data['manufacturer']} {profile_data['model']}")
        self.resize(600, 500)
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Create a tab widget for different profile sections
        tabs = QTabWidget()
        
        # Basic information tab
        basic_tab = QWidget()
        basic_layout = QFormLayout(basic_tab)
        
        for key in ['manufacturer', 'model', 'brand', 'product', 'device', 'android_version', 'sdk', 'build_id']:
            if key in self.profile_data:
                basic_layout.addRow(f"{key.replace('_', ' ').title()}:", QLabel(str(self.profile_data[key])))
                
        tabs.addTab(basic_tab, "Basic Info")
        
        # Build.prop tab
        build_tab = QWidget()
        build_layout = QVBoxLayout(build_tab)
        
        build_text = QTextEdit()
        build_text.setReadOnly(True)
        build_text.setLineWrapMode(QTextEdit.NoWrap)
        
        if "build_prop" in self.profile_data:
            build_props = self.profile_data["build_prop"]
            build_text.setText("\n".join([f"{k}={v}" for k, v in build_props.items()]))
            
        build_layout.addWidget(build_text)
        tabs.addTab(build_tab, "Build Properties")
        
        # Hardware tab
        hardware_tab = QWidget()
        hardware_layout = QFormLayout(hardware_tab)
        
        # CPU info
        if "cpu" in self.profile_data:
            cpu = self.profile_data["cpu"]
            hardware_layout.addRow("CPU Processors:", QLabel(str(cpu.get("processors", "Unknown"))))
            hardware_layout.addRow("CPU Architecture:", QLabel(cpu.get("architecture", "Unknown")))
            hardware_layout.addRow("CPU Features:", QLabel(", ".join(cpu.get("features", []))))
            
        # GPU info
        if "gpu" in self.profile_data:
            gpu = self.profile_data["gpu"]
            hardware_layout.addRow("GPU Vendor:", QLabel(gpu.get("vendor", "Unknown")))
            hardware_layout.addRow("GPU Renderer:", QLabel(gpu.get("renderer", "Unknown")))
            hardware_layout.addRow("GPU Version:", QLabel(gpu.get("version", "Unknown")))
            
        # Screen info
        if "screen" in self.profile_data:
            screen = self.profile_data["screen"]
            hardware_layout.addRow("Screen Resolution:", QLabel(f"{screen.get('width', 0)}x{screen.get('height', 0)}"))
            hardware_layout.addRow("Screen Density:", QLabel(f"{screen.get('density', 0)} dpi"))
            hardware_layout.addRow("Refresh Rate:", QLabel(f"{screen.get('refresh_rate', 60)} Hz"))
            
        tabs.addTab(hardware_tab, "Hardware")
        
        # Sensors tab
        sensors_tab = QWidget()
        sensors_layout = QVBoxLayout(sensors_tab)
        
        sensors_text = QTextEdit()
        sensors_text.setReadOnly(True)
        
        if "sensors" in self.profile_data:
            sensors = self.profile_data["sensors"]
            sensors_info = []
            
            for sensor_type, sensor_data in sensors.items():
                sensors_info.append(f"--- {sensor_type.upper()} ---")
                for key, value in sensor_data.items():
                    sensors_info.append(f"{key}: {value}")
                sensors_info.append("")
                
            sensors_text.setText("\n".join(sensors_info))
            
        sensors_layout.addWidget(sensors_text)
        tabs.addTab(sensors_tab, "Sensors")
        
        # Add the tabs to the layout
        layout.addWidget(tabs)
        
        # Add a close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        layout.addWidget(close_button)

class DeviceProfileWidget(QWidget):
    """Widget for managing device profiles."""
    
    # Signal emitted when a profile is selected
    profile_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize the device profile widget."""
        super().__init__(parent)
        
        self.profile_db = DeviceProfileDatabase()
        
        self.init_ui()
        self.update_profile_list()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Available profiles group
        profiles_group = QGroupBox("Available Device Profiles")
        profiles_layout = QVBoxLayout(profiles_group)
        
        self.profile_list = QListWidget()
        self.profile_list.setSelectionMode(QListWidget.SingleSelection)
        self.profile_list.itemSelectionChanged.connect(self.on_profile_selected)
        
        profiles_layout.addWidget(self.profile_list)
        
        # Buttons for profile management
        buttons_layout = QHBoxLayout()
        
        view_button = QPushButton("View Details")
        view_button.clicked.connect(self.view_profile_details)
        
        import_button = QPushButton("Import")
        import_button.clicked.connect(self.import_profile)
        
        export_button = QPushButton("Export")
        export_button.clicked.connect(self.export_selected_profile)
        
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_selected_profile)
        
        buttons_layout.addWidget(view_button)
        buttons_layout.addWidget(import_button)
        buttons_layout.addWidget(export_button)
        buttons_layout.addWidget(delete_button)
        
        profiles_layout.addLayout(buttons_layout)
        
        # Custom profile group
        custom_group = QGroupBox("Create Custom Profile")
        custom_layout = QFormLayout(custom_group)
        
        self.manufacturer_input = QLineEdit()
        custom_layout.addRow("Manufacturer:", self.manufacturer_input)
        
        self.model_input = QLineEdit()
        custom_layout.addRow("Model:", self.model_input)
        
        self.android_version_input = QComboBox()
        self.android_version_input.addItems(["12", "11", "10", "9", "8.1"])
        custom_layout.addRow("Android Version:", self.android_version_input)
        
        create_button = QPushButton("Create Profile")
        create_button.clicked.connect(self.create_custom_profile)
        custom_layout.addRow("", create_button)
        
        # Random profile group
        random_group = QGroupBox("Random Profile")
        random_layout = QVBoxLayout(random_group)
        
        random_button = QPushButton("Select Random Profile")
        random_button.clicked.connect(self.select_random_profile)
        random_layout.addWidget(random_button)
        
        # Add all groups to the main layout
        layout.addWidget(profiles_group)
        layout.addWidget(custom_group)
        layout.addWidget(random_group)
        
        # Add a stretch to make the layout look better
        layout.addStretch(1)
        
    def update_profile_list(self):
        """Update the list of available profiles."""
        self.profile_list.clear()
        
        profile_names = self.profile_db.get_profile_names()
        
        for name in profile_names:
            profile = self.profile_db.get_profile(name)
            if profile:
                item = QListWidgetItem()
                item.setText(f"{profile['manufacturer']} {profile['model']} (Android {profile['android_version']})")
                item.setData(Qt.UserRole, name)
                self.profile_list.addItem(item)
                
    def on_profile_selected(self):
        """Handle profile selection in the list."""
        items = self.profile_list.selectedItems()
        if items:
            profile_name = items[0].data(Qt.UserRole)
            profile = self.profile_db.get_profile(profile_name)
            
            if profile:
                self.profile_selected.emit(profile)
                
    def view_profile_details(self):
        """View detailed information for the selected profile."""
        items = self.profile_list.selectedItems()
        if items:
            profile_name = items[0].data(Qt.UserRole)
            profile = self.profile_db.get_profile(profile_name)
            
            if profile:
                dialog = ProfileDetailsDialog(profile, self)
                dialog.exec_()
                
    def import_profile(self):
        """Import a device profile from a JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Device Profile",
            str(Path.home()),
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, "r") as f:
                    profile_data = json.load(f)
                    
                # Validate minimum required fields
                required_fields = ['manufacturer', 'model', 'android_version']
                missing_fields = [field for field in required_fields if field not in profile_data]
                
                if missing_fields:
                    QMessageBox.warning(
                        self,
                        "Invalid Profile",
                        f"The profile is missing required fields: {', '.join(missing_fields)}"
                    )
                    return
                    
                # Generate a name for the profile
                name = f"{profile_data['manufacturer']}_{profile_data['model']}".lower().replace(' ', '_')
                
                # Save the profile
                if self.profile_db.create_profile(name, profile_data):
                    QMessageBox.information(
                        self,
                        "Profile Imported",
                        f"Imported profile: {profile_data['manufacturer']} {profile_data['model']}"
                    )
                    
                    self.update_profile_list()
                else:
                    QMessageBox.warning(
                        self,
                        "Import Error",
                        "Failed to save the imported profile. It may already exist."
                    )
                    
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Import Error",
                    f"Failed to import the profile: {str(e)}"
                )
                
    def export_selected_profile(self):
        """Export the selected profile to a JSON file."""
        items = self.profile_list.selectedItems()
        if items:
            profile_name = items[0].data(Qt.UserRole)
            profile = self.profile_db.get_profile(profile_name)
            
            if profile:
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Export Device Profile",
                    str(Path.home() / f"{profile_name}.json"),
                    "JSON Files (*.json);;All Files (*)"
                )
                
                if file_path:
                    try:
                        with open(file_path, "w") as f:
                            json.dump(profile, f, indent=2)
                            
                        QMessageBox.information(
                            self,
                            "Profile Exported",
                            f"Exported profile to: {file_path}"
                        )
                        
                    except Exception as e:
                        QMessageBox.warning(
                            self,
                            "Export Error",
                            f"Failed to export the profile: {str(e)}"
                        )
                        
    def delete_selected_profile(self):
        """Delete the selected profile."""
        items = self.profile_list.selectedItems()
        if items:
            profile_name = items[0].data(Qt.UserRole)
            
            # Ask for confirmation
            reply = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete the profile '{profile_name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.profile_db.delete_profile(profile_name):
                    self.update_profile_list()
                    logger.info(f"Deleted profile: {profile_name}")
                else:
                    QMessageBox.warning(
                        self,
                        "Deletion Error",
                        "Failed to delete the profile. See the logs for details."
                    )
                    
    def create_custom_profile(self):
        """Create a custom device profile."""
        manufacturer = self.manufacturer_input.text().strip()
        model = self.model_input.text().strip()
        android_version = self.android_version_input.currentText()
        
        if not manufacturer or not model:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter both manufacturer and model name."
            )
            return
            
        # Generate a basic profile
        profile = {
            "manufacturer": manufacturer,
            "model": model,
            "brand": manufacturer.lower(),
            "product": model.lower().replace(' ', '_'),
            "device": model.lower().replace(' ', '_'),
            "board": model.lower().replace(' ', '_'),
            "hardware": model.lower().replace(' ', '_'),
            "platform": model.lower().replace(' ', '_'),
            "android_version": android_version,
            "sdk": str(21 + int(float(android_version))),  # Approximate SDK from version
            "build_id": f"QP1A.{android_version}0101.001",
            "fingerprint": f"{manufacturer.lower()}/{model.lower().replace(' ', '_')}/{model.lower().replace(' ', '_')}:{android_version}/QP1A.{android_version}0101.001:user/release-keys",
            "build_time": "1609459200000",  # January 1, 2021
            "security_patch": "2021-01-01",
            "build_description": f"{model.lower().replace(' ', '_')}-user {android_version} QP1A.{android_version}0101.001 release-keys",
            "sensors": {
                "accelerometer": {
                    "name": "BMI160 Accelerometer",
                    "vendor": "Bosch",
                    "resolution": 0.0012,
                    "max_range": 39.2266,
                    "power": 0.13,
                    "min_delay": 10000
                },
                "gyroscope": {
                    "name": "BMI160 Gyroscope",
                    "vendor": "Bosch",
                    "resolution": 0.001,
                    "max_range": 34.906586,
                    "power": 0.13,
                    "min_delay": 10000
                },
                "magnetometer": {
                    "name": "AK09915 Magnetometer",
                    "vendor": "AKM",
                    "resolution": 0.15,
                    "max_range": 4912,
                    "power": 0.1,
                    "min_delay": 10000
                },
                "light": {
                    "name": "TSL2540 Light sensor",
                    "vendor": "AMS",
                    "resolution": 1.0,
                    "max_range": 65535,
                    "power": 0.1,
                    "min_delay": 0
                },
                "proximity": {
                    "name": "TSL2540 Proximity sensor",
                    "vendor": "AMS",
                    "resolution": 1.0,
                    "max_range": 5,
                    "power": 0.1,
                    "min_delay": 0
                }
            },
            "cpu": {
                "processors": 8,
                "architecture": "arm64-v8a",
                "features": ["neon", "aes", "pmull", "sha1", "sha2", "crc32"],
                "governor": "schedutil",
                "min_freq": 300000,
                "max_freq": 2400000,
                "abi_list": ["arm64-v8a", "armeabi-v7a", "armeabi"]
            },
            "gpu": {
                "vendor": "Qualcomm",
                "renderer": "Adreno 650",
                "version": "OpenGL ES 3.2",
                "extensions": []
            },
            "battery": {
                "capacity": 4000,
                "technology": "Li-ion"
            },
            "screen": {
                "density": 420,
                "width": 1080,
                "height": 2340,
                "refresh_rate": 60,
                "sizeCategory": 4
            },
            "network": {
                "imei_prefix": "35291011",
                "sim_operator": "310260",
                "cell_operator": "T-Mobile",
                "network_types": ["LTE", "HSDPA", "HSUPA", "UMTS", "EDGE", "GPRS"]
            }
        }
        
        # Generate a name for the profile
        name = f"{manufacturer}_{model}".lower().replace(' ', '_')
        
        # Add build.prop
        profile["build_prop"] = self.profile_db._generate_build_prop(profile)
        
        # Save the profile
        if self.profile_db.create_profile(name, profile):
            QMessageBox.information(
                self,
                "Profile Created",
                f"Created profile: {manufacturer} {model}"
            )
            
            self.update_profile_list()
            
            # Clear the input fields
            self.manufacturer_input.clear()
            self.model_input.clear()
        else:
            QMessageBox.warning(
                self,
                "Creation Error",
                "Failed to create the profile. It may already exist."
            )
            
    def select_random_profile(self):
        """Select a random profile from the available profiles."""
        random_profile = self.profile_db.get_random_profile()
        
        if random_profile:
            self.profile_selected.emit(random_profile)
            
            # Find and select the item in the list
            for i in range(self.profile_list.count()):
                item = self.profile_list.item(i)
                profile_name = item.data(Qt.UserRole)
                profile = self.profile_db.get_profile(profile_name)
                
                if (profile['manufacturer'] == random_profile['manufacturer'] and 
                    profile['model'] == random_profile['model']):
                    self.profile_list.setCurrentItem(item)
                    break
                    
            # Show a message
            QMessageBox.information(
                self,
                "Random Profile Selected",
                f"Selected random profile: {random_profile['manufacturer']} {random_profile['model']}"
            )
        else:
            QMessageBox.warning(
                self,
                "No Profiles Available",
                "No profiles are available to select from."
            )
            
    def get_selected_profile(self):
        """Get the currently selected profile, or None if none selected."""
        items = self.profile_list.selectedItems()
        if items:
            profile_name = items[0].data(Qt.UserRole)
            return self.profile_db.get_profile(profile_name)
        return None