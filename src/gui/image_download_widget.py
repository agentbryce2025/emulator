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
        QGroupBox, QFormLayout, QSpinBox, QApplication, QInputDialog
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal
    from PyQt5.QtGui import QIcon
except ImportError:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, 
        QProgressBar, QListWidget, QListWidgetItem, QMessageBox, QFileDialog,
        QGroupBox, QFormLayout, QSpinBox, QApplication, QInputDialog
    )
    from PySide6.QtCore import Qt, QTimer, Signal as pyqtSignal
    from PySide6.QtGui import QIcon

from ..core.image_manager import ImageManager

logger = logging.getLogger(__name__)

class ImageDownloadWidget(QWidget):
    """Widget for downloading and managing Android-x86 images."""
    
    # Signal emitted when a new image is downloaded or selected
    # Signal emitting the image info dictionary
    image_selected = pyqtSignal(object)
    
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
        
        use_local_button = QPushButton("Use Local File")
        use_local_button.clicked.connect(self.import_image)
        use_local_button.setToolTip("Select a locally downloaded Android-x86 ISO file")
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_download)
        self.cancel_button.setVisible(False)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(download_button)
        buttons_layout.addWidget(use_local_button)
        buttons_layout.addWidget(self.cancel_button)
        download_layout.addLayout(buttons_layout)
        
        # Add direct download link info
        download_help = QLabel(
            "<small>Having trouble with downloads? " 
            "<a href='https://www.android-x86.org/download.html'>Download directly</a> "
            "and use the 'Use Local File' button</small>"
        )
        download_help.setOpenExternalLinks(True)
        download_help.setWordWrap(True)
        download_layout.addWidget(download_help)
        
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
            # Store the entire image info dictionary
            item.setData(Qt.UserRole, image)
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
            image_info = item.data(Qt.UserRole)
            path = image_info['path']
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
            image_info = items[0].data(Qt.UserRole)
            self.image_selected.emit(image_info)
            
    def delete_selected_image(self):
        """Delete the selected image."""
        items = self.image_list.selectedItems()
        if items:
            image_info = items[0].data(Qt.UserRole)
            image_path = image_info['path']
            
            # Ask for confirmation
            reply = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete the selected image?\n\n{image_info['filename']}",
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
        # Default to Downloads directory if it exists, otherwise home directory
        default_dir = str(Path.home() / "Downloads")
        if not os.path.exists(default_dir):
            default_dir = str(Path.home())
            
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Android-x86 ISO Image",
            default_dir,
            "ISO Images (*.iso);;All Files (*)"
        )
        
        if not file_path:
            return  # User cancelled
            
        import shutil
        
        # Get the destination directory and filename
        target_basename = os.path.basename(file_path)
        
        # If the filename doesn't look like an Android-x86 image, suggest renaming it
        if not target_basename.startswith("android-x86"):
            # Guess the version from the file name if possible
            version = None
            for v in self.image_manager.AVAILABLE_VERSIONS:
                if v in file_path:
                    version = v
                    break
                    
            if not version:
                version = "9.0-r2"  # Default to latest version
                
            # Guess architecture
            arch = "x86_64" if "64" in file_path else "x86"
            
            # Suggest new filename
            suggested_name = f"android-x86_{version}_{arch}.iso"
            
            # Ask user if they want to rename it
            rename_msg = (
                f"The selected file '{target_basename}' doesn't follow the Android-x86 naming convention.\n\n"
                f"For better compatibility, would you like to rename it to '{suggested_name}'?"
            )
            
            rename = QMessageBox.question(
                self,
                "Rename File?",
                rename_msg,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if rename == QMessageBox.Yes:
                target_basename = suggested_name
        
        try:
            # Ensure the target directory exists
            os.makedirs(self.image_manager.storage_dir, exist_ok=True)
            
            # Final target path
            target_path = os.path.join(self.image_manager.storage_dir, target_basename)
            
            # Check if the file already exists
            if os.path.exists(target_path):
                confirm = QMessageBox.question(
                    self,
                    "File Exists",
                    f"The file '{target_basename}' already exists in the image directory. Overwrite?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if confirm != QMessageBox.Yes:
                    return
            
            # Show progress message
            progress_msg = QMessageBox(self)
            progress_msg.setWindowTitle("Importing Image")
            progress_msg.setText(f"Copying {os.path.basename(file_path)}...\nThis may take a while for large files.")
            progress_msg.setStandardButtons(QMessageBox.NoButton)
            progress_msg.show()
            
            # Process events to update the UI
            QApplication.processEvents()
            
            try:
                # Copy the file
                shutil.copy2(file_path, target_path)
                
                # Close progress message
                progress_msg.close()
                
                QMessageBox.information(
                    self,
                    "Import Successful",
                    f"Imported '{target_basename}' successfully."
                )
                
                logger.info(f"Imported image from {file_path} to {target_path}")
                
                # Update the image list
                self.update_image_list()
                
                # Select the imported image
                for i in range(self.image_list.count()):
                    item = self.image_list.item(i)
                    image_info = item.data(Qt.UserRole)
                    if image_info["path"] == target_path:
                        self.image_list.setCurrentItem(item)
                        # Emit the selected image info
                        self.image_selected.emit(image_info)
                        break
            finally:
                # Close progress message if it's still open
                try:
                    progress_msg.close()
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Failed to import image: {str(e)}")
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import the image:\n\n{str(e)}\n\nPlease make sure you have permissions to copy files and enough disk space."
            )
                
    def create_data_image(self):
        """Create a new data image file."""
        size_gb = self.data_size_spinner.value()
        
        # Ask for a name
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
        """Get the image info of the currently selected image, or None if none selected."""
        items = self.image_list.selectedItems()
        if items:
            return items[0].data(Qt.UserRole)
        return None