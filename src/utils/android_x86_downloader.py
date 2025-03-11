#!/usr/bin/env python3
"""
Android-x86 image downloader and configurator.
This module handles downloading and configuring Android-x86 images.
"""

import os
import sys
import logging
import requests
from pathlib import Path
import tempfile
import subprocess
import shutil
import re
from tqdm import tqdm

logger = logging.getLogger(__name__)

class AndroidX86Downloader:
    """Handles downloading and configuring Android-x86 images."""
    
    def __init__(self, download_dir=None):
        """Initialize the Android-x86 downloader."""
        self.download_dir = download_dir or os.path.join(
            os.path.expanduser("~"), ".config", "undetected-emulator", "images"
        )
        
        # Ensure download directory exists
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Base URL for Android-x86 downloads
        self.base_url = "https://sourceforge.net/projects/android-x86/files/"
        
        # Available Android versions
        self.available_versions = {
            "9.0": "android-x86-9.0-r2.iso",
            "8.1": "android-x86-8.1-r6.iso",
            "7.1": "android-x86-7.1-r5.iso",
            "6.0": "android-x86-6.0-r3.iso",
        }
        
    def list_available_versions(self):
        """List all available Android-x86 versions."""
        return list(self.available_versions.keys())
        
    def list_downloaded_images(self):
        """List all downloaded images."""
        downloaded_images = []
        
        for file in os.listdir(self.download_dir):
            if file.endswith(".iso") or file.endswith(".img"):
                downloaded_images.append(file)
                
        return downloaded_images
        
    def download_image(self, version, force=False):
        """Download an Android-x86 image."""
        if version not in self.available_versions:
            logger.error(f"Version {version} not available")
            return False
            
        image_name = self.available_versions[version]
        output_path = os.path.join(self.download_dir, image_name)
        
        # Check if image already exists
        if os.path.exists(output_path) and not force:
            logger.info(f"Image {image_name} already downloaded")
            return output_path
            
        # Determine download URL
        download_url = f"{self.base_url}/releases/{version}/{image_name}/download"
        
        logger.info(f"Downloading Android-x86 {version} from {download_url}...")
        
        try:
            # First request to get the redirect URL
            response = requests.get(download_url, stream=True, allow_redirects=True)
            
            # Get file size from headers
            total_size = int(response.headers.get('content-length', 0))
            
            # Download with progress bar
            with open(output_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=image_name) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            
            logger.info(f"Download complete: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
            
    def convert_to_qcow2(self, iso_path, output_path=None):
        """Convert ISO to QCOW2 disk image for better performance."""
        if not os.path.exists(iso_path):
            logger.error(f"ISO file not found: {iso_path}")
            return False
            
        if output_path is None:
            # Generate output path based on ISO name
            base_name = os.path.basename(iso_path)
            name_without_ext = os.path.splitext(base_name)[0]
            output_path = os.path.join(self.download_dir, f"{name_without_ext}.qcow2")
            
        # Check if output file already exists
        if os.path.exists(output_path):
            logger.warning(f"Output file {output_path} already exists, will be overwritten")
            
        logger.info(f"Converting {iso_path} to QCOW2 format...")
        
        try:
            # Create a new QCOW2 image (8GB size)
            subprocess.run(
                ["qemu-img", "create", "-f", "qcow2", output_path, "8G"],
                check=True
            )
            
            logger.info(f"Conversion complete: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Error converting image: {str(e)}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
            
    def create_modified_iso(self, iso_path, hardware_profile, output_path=None):
        """Create a modified ISO with custom hardware profile."""
        if not os.path.exists(iso_path):
            logger.error(f"ISO file not found: {iso_path}")
            return False
            
        if output_path is None:
            # Generate output path based on ISO name
            base_name = os.path.basename(iso_path)
            name_without_ext = os.path.splitext(base_name)[0]
            output_path = os.path.join(self.download_dir, f"{name_without_ext}_modified.iso")
            
        # Check if output file already exists
        if os.path.exists(output_path):
            logger.warning(f"Output file {output_path} already exists, will be overwritten")
            
        logger.info(f"Creating modified ISO with custom hardware profile...")
        
        # Create temporary directory for ISO extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_dir = os.path.join(temp_dir, "iso_content")
            os.makedirs(extract_dir, exist_ok=True)
            
            try:
                # Mount ISO
                mount_dir = os.path.join(temp_dir, "mount")
                os.makedirs(mount_dir, exist_ok=True)
                
                subprocess.run(
                    ["mount", "-o", "loop", iso_path, mount_dir],
                    check=True
                )
                
                # Copy content
                subprocess.run(
                    ["cp", "-r", f"{mount_dir}/.", extract_dir],
                    check=True
                )
                
                # Unmount
                subprocess.run(
                    ["umount", mount_dir],
                    check=True
                )
                
                # Modify build.prop
                system_dir = os.path.join(extract_dir, "system")
                build_prop_path = os.path.join(system_dir, "build.prop")
                
                if os.path.exists(build_prop_path):
                    # Backup original build.prop
                    shutil.copy(build_prop_path, f"{build_prop_path}.bak")
                    
                    # Generate new build.prop content
                    build_prop_content = ""
                    with open(build_prop_path, "r") as f:
                        build_prop_content = f.read()
                        
                    # Replace properties with our custom ones
                    for key, value in hardware_profile["build_prop"].items():
                        # Check if property already exists
                        pattern = re.compile(f"^{key}=.*$", re.MULTILINE)
                        if pattern.search(build_prop_content):
                            # Replace existing property
                            build_prop_content = pattern.sub(f"{key}={value}", build_prop_content)
                        else:
                            # Add new property
                            build_prop_content += f"{key}={value}\n"
                            
                    # Write modified build.prop
                    with open(build_prop_path, "w") as f:
                        f.write(build_prop_content)
                        
                    logger.info("Modified build.prop with custom hardware profile")
                else:
                    logger.warning("build.prop not found in ISO")
                    
                # Create new ISO
                subprocess.run(
                    [
                        "genisoimage", "-l", "-J", "-R", "-V", "ANDROID_X86_MOD",
                        "-b", "isolinux/isolinux.bin", "-c", "isolinux/boot.cat",
                        "-no-emul-boot", "-boot-load-size", "4", "-boot-info-table",
                        "-o", output_path, extract_dir
                    ],
                    check=True
                )
                
                logger.info(f"Created modified ISO: {output_path}")
                return output_path
            except subprocess.CalledProcessError as e:
                logger.error(f"Error creating modified ISO: {str(e)}")
                if os.path.exists(output_path):
                    os.remove(output_path)
                return False
            finally:
                # Ensure ISO is unmounted in case of error
                try:
                    subprocess.run(["umount", mount_dir], check=False)
                except:
                    pass

if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    downloader = AndroidX86Downloader()
    
    print("Available versions:", downloader.list_available_versions())
    print("Downloaded images:", downloader.list_downloaded_images())