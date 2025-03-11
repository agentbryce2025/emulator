#!/usr/bin/env python3
"""
Android-x86 image download widget for the undetected Android emulator GUI.
This module provides a user interface for downloading and managing Android-x86 images.
"""

import sys
import os
import logging
from pathlib import Path

try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, 
        QProgressBar, QListWidget, QListWidgetItem, QMessageBox, QFileDialog,
        QGroupBox, QFormLayout, QSpinBox
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal
    from PyQt5.QtGui import QIcon
except ImportError:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, 
        QProgressBar, QListWidget, QListWidgetItem, QMessageBox, QFileDialog,
        QGroupBox, QFormLayout, QSpinBox
    )
    from PySide6.QtCore import Qt, QTimer, Signal as pyqtSignal
    from PySide6.QtGui import QIcon

from ..core.image_manager import ImageManager

logger = logging.getLogger(__name__)

class ImageDownloadWidget(QWidget):
    """Widget for downloading and managing Android-x86 images."""
    
    # Signal emitted when a new image is downloaded or selected
    image_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize the image download widget."""
        super().__init__(parent)
        
        self.image_manager = ImageManager()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        
        self.init_ui()
        self.populate_version_dropdown()
        self.update_image_list()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Available images group
        images_group = QGroupBox("Available Images")
        images_layout = QVBoxLayout(images_group)
        
        self.image_list = QListWidget()
        self.image_list.setSelectionMode(QListWidget.SingleSelection)
        self.image_list.itemSelectionChanged.connect(self.on_image_selected)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.update_image_list)
        
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_selected_image)
        
        import_button = QPushButton("Import Image")
        import_button.clicked.connect(self.import_image)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(refresh_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(import_button)
        
        images_layout.addWidget(self.image_list)
        images_layout.addLayout(buttons_layout)
        
        # Download new image group
        download_group = QGroupBox("Download Android-x86 Image")
        download_layout = QVBoxLayout(download_group)
        
        form_layout = QFormLayout()
        
        self.version_dropdown = QComboBox()
        form_layout.addRow("Android Version:", self.version_dropdown)
        
        self.type_dropdown = QComboBox()
        self.type_dropdown.addItems(["x86_64", "x86"])
        form_layout.addRow("Architecture:", self.type_dropdown)
        
        download_layout.addLayout(form_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        download_layout.addWidget(self.progress_bar)
        
        download_button = QPushButton("Download")
        download_button.clicked.connect(self.download_image)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_download)
        self.cancel_button.setVisible(False)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(download_button)
        buttons_layout.addWidget(self.cancel_button)
        download_layout.addLayout(buttons_layout)
        
        # Create data image group
        data_image_group = QGroupBox("Create Data Image")
        data_layout = QVBoxLayout(data_image_group)
        
        form_layout = QFormLayout()
        
        self.data_size_spinner = QSpinBox()
        self.data_size_spinner.setRange(1, 64)
        self.data_size_spinner.setValue(8)
        self.data_size_spinner.setSuffix(" GB")
        form_layout.addRow("Size:", self.data_size_spinner)
        
        data_layout.addLayout(form_layout)
        
        create_button = QPushButton("Create Data Image")
        create_button.clicked.connect(self.create_data_image)
        data_layout.addWidget(create_button)
        
        # Add all groups to the main layout
        layout.addWidget(images_group)
        layout.addWidget(download_group)
        layout.addWidget(data_image_group)
        
        # Add a stretch to make the layout look better
        layout.addStretch(1)
        
    def populate_version_dropdown(self):
        """Populate the version dropdown with available Android-x86 versions."""
        self.version_dropdown.clear()
        self.version_dropdown.addItems(self.image_manager.AVAILABLE_VERSIONS)
        
    def update_image_list(self):
        """Update the list of available images."""
        self.image_list.clear()
        
        available_images = self.image_manager.get_available_images(force_refresh=True)
        
        for image in available_images:
            item = QListWidgetItem()
            item.setText(f"{image['filename']} ({self.format_size(image['size'])})")
            item.setData(Qt.UserRole, image['path'])
            self.image_list.addItem(item)
            
    def format_size(self, size_bytes):
        """Format file size in bytes to a human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
        
    def download_image(self):
        """Download a new Android-x86 image."""
        version = self.version_dropdown.currentText()
        image_type = self.type_dropdown.currentText()
        
        # Check if image already exists
        for i in range(self.image_list.count()):
            item = self.image_list.item(i)
            path = item.data(Qt.UserRole)
            if f"android-x86_{version}_{image_type}.iso" in path:
                QMessageBox.information(
                    self,
                    "Image Already Exists",
                    f"The selected image (Android {version} {image_type}) already exists."
                )
                return
        
        # Start the download
        result = self.image_manager.download_image(
            version,
            image_type=image_type,
            callback=None  # Progress will be updated by timer
        )
        
        if result:
            self.progress_bar.setVisible(True)
            self.cancel_button.setVisible(True)
            self.timer.start(500)  # Update progress every 500ms
            
            logger.info(f"Started downloading Android-x86 {version} ({image_type})")
        else:
            QMessageBox.warning(
                self,
                "Download Error",
                "Failed to start the download. See the logs for details."
            )
            
    def update_progress(self):
        """Update the download progress bar."""
        if self.image_manager.current_download:
            self.progress_bar.setValue(self.image_manager.download_progress)
        else:
            # Download completed or failed
            self.timer.stop()
            self.progress_bar.setVisible(False)
            self.cancel_button.setVisible(False)
            self.update_image_list()
            
    def cancel_download(self):
        """Cancel the current download."""
        if self.image_manager.cancel_download():
            self.progress_bar.setVisible(False)
            self.cancel_button.setVisible(False)
            self.timer.stop()
            
            logger.info("Download cancelled")
        
    def on_image_selected(self):
        """Handle image selection in the list."""
        items = self.image_list.selectedItems()
        if items:
            image_path = items[0].data(Qt.UserRole)
            self.image_selected.emit(image_path)
            
    def delete_selected_image(self):
        """Delete the selected image."""
        items = self.image_list.selectedItems()
        if items:
            image_path = items[0].data(Qt.UserRole)
            
            # Ask for confirmation
            reply = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete the selected image?\n\n{image_path}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.image_manager.delete_image(image_path):
                    self.update_image_list()
                    logger.info(f"Deleted image: {image_path}")
                else:
                    QMessageBox.warning(
                        self,
                        "Deletion Error",
                        "Failed to delete the image. See the logs for details."
                    )
                    
    def import_image(self):
        """Import an existing Android-x86 image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Android-x86 Image",
            str(Path.home()),
            "ISO Images (*.iso);;All Files (*)"
        )
        
        if file_path:
            # Copy the file to the image directory
            import shutil
            try:
                filename = os.path.basename(file_path)
                target_path = os.path.join(self.image_manager.storage_dir, filename)
                
                # Check if the file already exists
                if os.path.exists(target_path):
                    reply = QMessageBox.question(
                        self,
                        "File Already Exists",
                        f"A file with the name {filename} already exists. Overwrite?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply == QMessageBox.No:
                        return
                
                shutil.copy2(file_path, target_path)
                logger.info(f"Imported image from {file_path} to {target_path}")
                
                self.update_image_list()
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Import Error",
                    f"Failed to import the image: {str(e)}"
                )
                
    def create_data_image(self):
        """Create a new data image file."""
        size_gb = self.data_size_spinner.value()
        
        # Ask for a name
        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(
            self,
            "Data Image Name",
            "Enter a name for the data image:"
        )
        
        if ok and name:
            # Create the image
            result = self.image_manager.create_empty_image(name, size_gb=size_gb)
            
            if result:
                QMessageBox.information(
                    self,
                    "Data Image Created",
                    f"Created a {size_gb}GB data image at:\n{result}"
                )
                
                self.update_image_list()
            else:
                QMessageBox.warning(
                    self,
                    "Creation Error",
                    "Failed to create the data image. See the logs for details."
                )
                
    def get_selected_image(self):
        """Get the path of the currently selected image, or None if none selected."""
        items = self.image_list.selectedItems()
        if items:
            return items[0].data(Qt.UserRole)
        return None