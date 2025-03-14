#!/usr/bin/env python3
"""
Android-x86 image management module for the undetected Android emulator.
This module handles downloading, verifying, and configuring Android-x86 images.
"""

import os
import sys
import logging
import requests
import hashlib
import shutil
import tempfile
import subprocess
import time
import json
from pathlib import Path
from threading import Thread, Event

logger = logging.getLogger(__name__)

class ImageManager:
    """Handles Android-x86 image downloading and management."""
    
    # Official Android-x86 mirror list with direct download links
    MIRROR_LIST = [
        "https://sourceforge.net/projects/android-x86/files/",
        "https://osdn.net/projects/android-x86/downloads/",
        "https://ftp.nluug.nl/pub/os/Linux/distr/android-x86/",
    ]
    
    AVAILABLE_VERSIONS = [
        "9.0-r2", 
        "8.1-r6", 
        "7.1-r5",
        "6.0-r3"
    ]
    
    # Direct download URLs for specific images with multiple mirrors for each
    DIRECT_URLS = {
        "9.0-r2": {
            "x86_64": [
                "https://osdn.net/frs/redir.php?m=nchc&f=android-x86%2F71931%2Fandroid-x86_64-9.0-r2.iso",
                "https://sourceforge.net/projects/android-x86/files/Release%209.0/android-x86_64-9.0-r2.iso/download",
                "https://ftp.nluug.nl/pub/os/Linux/distr/android-x86/Release%209.0/android-x86_64-9.0-r2.iso",
                "https://osdn.mirror.constant.com/android-x86/71931/android-x86_64-9.0-r2.iso"
            ]
        },
        "8.1-r6": {
            "x86_64": [
                "https://osdn.net/frs/redir.php?m=nchc&f=android-x86%2F71931%2Fandroid-x86_64-8.1-r6.iso",
                "https://sourceforge.net/projects/android-x86/files/Release%208.1/android-x86_64-8.1-r6.iso/download",
                "https://ftp.nluug.nl/pub/os/Linux/distr/android-x86/Release%208.1/android-x86_64-8.1-r6.iso",
                "https://osdn.mirror.constant.com/android-x86/71931/android-x86_64-8.1-r6.iso"
            ]
        }
    }
    
    def __init__(self, storage_dir=None):
        """Initialize the image manager with optional storage directory."""
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            # Default to ~/.config/undetected-emulator/images
            self.storage_dir = Path.home() / ".config" / "undetected-emulator" / "images"
            
        # Create storage directory if it doesn't exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_download = None
        self.download_progress = 0
        self.download_cancel = Event()
        self._available_images = None
        
    def get_available_images(self, force_refresh=False):
        """Get list of available images (cached unless force_refresh is True)."""
        if self._available_images is None or force_refresh:
            self._available_images = self._scan_available_images()
        return self._available_images
    
    def _scan_available_images(self):
        """Scan the storage directory for available images."""
        available = []
        
        for image_path in self.storage_dir.glob("*.iso"):
            # Extract version from filename (assumes filename format: android-x86_VERSION_TYPE.iso)
            try:
                filename = image_path.name
                if filename.startswith("android-x86_"):
                    parts = filename.split('_')
                    if len(parts) >= 2:
                        version = parts[1]
                        image_type = parts[2].split('.')[0] if len(parts) >= 3 else "unknown"
                        
                        image_info = {
                            "version": version,
                            "type": image_type,
                            "path": str(image_path),
                            "size": image_path.stat().st_size,
                            "filename": filename
                        }
                        available.append(image_info)
            except Exception as e:
                logger.warning(f"Failed to parse image info for {image_path}: {str(e)}")
                
        return available
    
    def download_image(self, version, image_type="x86_64", callback=None):
        """
        Download an Android-x86 image.
        
        Args:
            version: Android version (e.g., "9.0-r2")
            image_type: Image type (e.g., "x86_64", "x86")
            callback: Optional callback function for progress updates
            
        Returns:
            Path to downloaded image or None if download failed
        """
        if self.current_download:
            logger.error("Another download is already in progress")
            return None
            
        self.download_progress = 0
        self.download_cancel.clear()
        
        image_filename = f"android-x86_{version}_{image_type}.iso"
        target_path = self.storage_dir / image_filename
        
        # Check if image already exists
        if target_path.exists():
            logger.info(f"Image already exists at {target_path}")
            return str(target_path)
            
        # Official files are typically hosted in a version-specific directory
        version_dir = version
        
        # Check if we have direct URLs
        download_url = None
        
        if version in self.DIRECT_URLS and image_type in self.DIRECT_URLS[version]:
            # Try each URL in order until one works
            direct_urls = self.DIRECT_URLS[version][image_type]
            url_errors = []
            
            for url in direct_urls:
                try:
                    logger.info(f"Trying direct URL for {version} {image_type}: {url}")
                    
                    # Do a quick HEAD request to see if the URL is accessible
                    response = requests.head(url, allow_redirects=True, timeout=10)
                    if response.status_code in [200, 301, 302]:
                        download_url = url
                        logger.info(f"Using direct download URL: {download_url}")
                        break
                except Exception as e:
                    error_msg = f"URL {url} failed: {str(e)}"
                    url_errors.append(error_msg)
                    logger.warning(error_msg)
        
        # If no direct URL worked, try fallback using mirrors
        if not download_url:
            logger.warning("Direct URLs failed, trying fallback mirrors")
            for mirror in self.MIRROR_LIST:
                try:
                    if "osdn.net" in mirror:
                        url = f"{mirror}{version_dir}/{image_filename}"
                    elif "sourceforge.net" in mirror:
                        url = f"{mirror}{version_dir}/{image_filename}/download"
                    else:
                        url = f"{mirror}{version_dir}/{image_filename}"
                        
                    # Check if URL exists (HEAD request)
                    logger.info(f"Trying mirror URL: {url}")
                    response = requests.head(url, allow_redirects=True, timeout=10)
                    if response.status_code in [200, 301, 302]:
                        download_url = url
                        logger.info(f"Using mirror URL: {download_url}")
                        break
                except Exception as e:
                    logger.warning(f"Failed to check mirror {mirror}: {str(e)}")
                
        if not download_url:
            logger.error(f"Could not find working download URL for Android-x86 {version} {image_type}")
            return None
            
        # Start download in a separate thread
        download_thread = Thread(
            target=self._download_file,
            args=(download_url, target_path, callback)
        )
        download_thread.daemon = True
        download_thread.start()
        
        self.current_download = {
            "version": version,
            "type": image_type,
            "url": download_url,
            "target_path": str(target_path),
            "thread": download_thread
        }
        
        return str(target_path)
        
    def _download_file(self, url, target_path, callback=None):
        """Download a file with progress tracking and better error handling."""
        temp_path = None
        try:
            # Create temporary file first
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name
            
            logger.info(f"Starting download from {url} to temporary file {temp_path}")
            
            # Setup session with longer timeouts and retry capability
            session = requests.Session()
            session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
            
            # Stream download with progress updates
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = session.get(
                url, 
                stream=True, 
                timeout=60,  # Connect timeout
                headers=headers
            )
            response.raise_for_status()  # Raise an error for bad responses
            
            total_size = int(response.headers.get('content-length', 0))
            if total_size == 0:
                logger.warning(f"Content length not provided for {url}, download progress will not be accurate")
                total_size = 800000000  # Assume approximately 800 MB for Android-x86 ISO
            
            downloaded = 0
            last_percent = 0
            start_time = time.time()
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):  # Use 1MB chunks
                    if self.download_cancel.is_set():
                        logger.info("Download cancelled by user")
                        os.unlink(temp_path)
                        self.current_download = None
                        self.download_progress = 0
                        return
                        
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update progress
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            
                            # Only log progress updates on significant changes
                            if progress >= last_percent + 5:
                                elapsed = time.time() - start_time
                                download_rate = downloaded / elapsed if elapsed > 0 else 0
                                rate_mb = download_rate / (1024 * 1024)
                                
                                logger.info(f"Download progress: {progress}% ({downloaded/1048576:.1f} MB / "
                                            f"{total_size/1048576:.1f} MB) at {rate_mb:.1f} MB/s")
                                last_percent = progress
                            
                            self.download_progress = progress
                            
                            if callback and callable(callback):
                                callback(progress)
            
            # Download completed, move to final location
            logger.info(f"Download completed, moving {temp_path} to {target_path}")
            shutil.move(temp_path, target_path)
            logger.info(f"Successfully downloaded {url} to {target_path}")
            
            # Verify the downloaded image
            if not self._verify_image(target_path):
                logger.warning("The downloaded image couldn't be verified as a valid ISO file")
            
            self._available_images = None  # Refresh available images list
            return True
            
        except requests.exceptions.RequestException as e:
            error_type = type(e).__name__
            logger.error(f"Download failed with {error_type}: {str(e)}")
            if isinstance(e, requests.exceptions.ConnectionError):
                logger.error("Connection error - check your internet connection")
            elif isinstance(e, requests.exceptions.Timeout):
                logger.error("Connection timed out - the server may be busy or unreachable")
            elif isinstance(e, requests.exceptions.HTTPError):
                logger.error(f"HTTP error {e.response.status_code} - the file may not exist")
        except Exception as e:
            logger.error(f"Download failed with unexpected error: {str(e)}")
        
        # Cleanup on error
        try:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
                logger.info(f"Cleaned up temporary file {temp_path}")
        except Exception as cleanup_error:
            logger.warning(f"Error cleaning up temporary file: {str(cleanup_error)}")
        
        # Reset download state
        self.current_download = None
        self.download_progress = 0
        return False
            
    def cancel_download(self):
        """Cancel the current download."""
        if self.current_download:
            self.download_cancel.set()
            return True
        return False
        
    def _verify_image(self, image_path):
        """Verify that the downloaded image is valid."""
        # Basic verification: check if it's a valid ISO file
        try:
            result = subprocess.run(
                ["file", str(image_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            output = result.stdout.decode("utf-8", "ignore")
            if "ISO 9660" in output:
                logger.info(f"Verified image {image_path} as valid ISO 9660 file")
                return True
            else:
                logger.warning(f"Image {image_path} does not appear to be a valid ISO file: {output}")
                return False
        except Exception as e:
            logger.error(f"Failed to verify image {image_path}: {str(e)}")
            return False
            
    def create_empty_image(self, name, size_gb=8):
        """Create an empty disk image for persistent storage."""
        image_path = self.storage_dir / f"{name}.img"
        
        try:
            # Create an empty image file
            subprocess.run(
                ["qemu-img", "create", "-f", "qcow2", str(image_path), f"{size_gb}G"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            logger.info(f"Created empty disk image {image_path} ({size_gb}GB)")
            return str(image_path)
        except Exception as e:
            logger.error(f"Failed to create empty disk image: {str(e)}")
            return None
            
    def delete_image(self, image_path):
        """Delete an image file."""
        try:
            if isinstance(image_path, str):
                image_path = Path(image_path)
                
            if image_path.exists():
                image_path.unlink()
                logger.info(f"Deleted image {image_path}")
                
                # Refresh available images
                self._available_images = None
                return True
            else:
                logger.warning(f"Image {image_path} does not exist")
                return False
        except Exception as e:
            logger.error(f"Failed to delete image {image_path}: {str(e)}")
            return False
            
    def get_latest_version(self):
        """Get the latest available Android-x86 version."""
        if self.AVAILABLE_VERSIONS:
            return self.AVAILABLE_VERSIONS[0]
        return None


if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    
    manager = ImageManager()
    print("Available versions:", manager.AVAILABLE_VERSIONS)
    print("Available images:", manager.get_available_images())
    
    # Uncomment to test downloading
    # def progress_callback(progress):
    #     print(f"Download progress: {progress}%")
    # 
    # manager.download_image("9.0-r2", callback=progress_callback)
    # 
    # # Wait for download to complete
    # while manager.current_download:
    #     time.sleep(1)