#!/usr/bin/env python3
"""
Script to simulate a downloaded Android image for testing purposes.
Creates a dummy ISO file that will satisfy the basic checks.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger("simulate_image")

def create_dummy_iso(output_path, size_mb=10):
    """Create a dummy ISO file that will pass basic verification."""
    try:
        # Create directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create basic ISO file structure using mkisofs/genisoimage
        temp_dir = "/tmp/dummy_iso_content"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Create some dummy files
        with open(f"{temp_dir}/README.txt", "w") as f:
            f.write("Android-x86 Simulation\n")
            f.write("This is a simulated Android-x86 image for testing.\n")
        
        # Create various directories to simulate Android-x86 structure
        os.makedirs(f"{temp_dir}/system", exist_ok=True)
        os.makedirs(f"{temp_dir}/boot", exist_ok=True)
        os.makedirs(f"{temp_dir}/kernel", exist_ok=True)
        os.makedirs(f"{temp_dir}/efi", exist_ok=True)
        
        # Generate ISO file
        try:
            # Try with mkisofs first
            subprocess.run(
                ["mkisofs", "-o", output_path, "-r", temp_dir],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            try:
                # Try with genisoimage as an alternative
                subprocess.run(
                    ["genisoimage", "-o", output_path, "-r", temp_dir],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            except (subprocess.SubprocessError, FileNotFoundError):
                # If both fail, create a simple file with the ISO9660 signature
                with open(output_path, "wb") as f:
                    # Write a basic ISO9660 signature
                    f.write(b"\x01CD001\x01")
                    # Fill with zeros to get desired size
                    f.seek(size_mb * 1024 * 1024 - 1)
                    f.write(b"\0")
        
        logger.info(f"Created simulated Android image at: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create simulated Android image: {str(e)}")
        return False

def main():
    """Main function."""
    if len(sys.argv) < 2:
        version = "9.0-r2"
        logger.info(f"No version specified, using default: {version}")
    else:
        version = sys.argv[1]
    
    image_type = "x86_64" if len(sys.argv) < 3 else sys.argv[2]
    
    # Set output path
    config_dir = Path.home() / ".config" / "undetected-emulator" / "images"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    iso_name = f"android-x86_{version}_{image_type}.iso"
    output_path = config_dir / iso_name
    
    if create_dummy_iso(output_path):
        logger.info(f"Successfully created simulated Android-x86 image: {output_path}")
        logger.info(f"Size: {os.path.getsize(output_path) / (1024*1024):.2f} MB")
        
        # Verify file type
        try:
            result = subprocess.run(
                ["file", str(output_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"File verification: {result.stdout.decode('utf-8')}")
        except Exception as e:
            logger.warning(f"Could not verify file type: {str(e)}")
            
        # Show files that would be available to the ImageManager
        logger.info("Available images:")
        for item in config_dir.glob("*.iso"):
            logger.info(f"  - {item.name} ({item.stat().st_size / (1024*1024):.2f} MB)")
            
        return 0
    else:
        logger.error("Failed to create simulated Android image")
        return 1

if __name__ == "__main__":
    sys.exit(main())