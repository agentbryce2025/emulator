#!/usr/bin/env python3
"""
Emulator Detection Test Runner
This script provides a simple interface to run automated detection tests.
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Import the automated test framework
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.test.automated_detection_test import AutomatedDetectionTest
from src.anti_detection.device_profiles import DeviceProfileDatabase

def setup_logging():
    """Set up logging configuration."""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file = os.path.join(log_dir, f"test_run_{timestamp}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )
    
    return log_file

def main():
    """Main function for the test runner."""
    parser = argparse.ArgumentParser(
        description="Run automated emulator detection tests",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--list-profiles", 
        action="store_true", 
        help="List available device profiles and exit"
    )
    parser.add_argument(
        "--profile", 
        help="Specific device profile to test"
    )
    parser.add_argument(
        "--all-profiles", 
        action="store_true", 
        help="Test all available profiles"
    )
    parser.add_argument(
        "--android-version", 
        help="Android version to use for tests"
    )
    parser.add_argument(
        "--duration", 
        type=int, 
        default=60, 
        help="Test duration in seconds"
    )
    parser.add_argument(
        "--output-dir", 
        help="Directory to save test results"
    )
    parser.add_argument(
        "--linkedin-only", 
        action="store_true", 
        help="Only test against LinkedIn detection"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_file = setup_logging()
    logger = logging.getLogger("test_runner")
    logger.info("Emulator Detection Test Runner starting")
    logger.info(f"Logging to: {log_file}")
    
    # Handle --list-profiles flag
    if args.list_profiles:
        profile_db = DeviceProfileDatabase()
        profiles = profile_db.get_profile_names()
        
        print("\nAvailable Device Profiles:")
        print("=========================")
        for i, profile in enumerate(profiles):
            print(f"{i+1}. {profile}")
        print()
        return 0
    
    # Create output directory
    output_dir = args.output_dir
    if not output_dir:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "test_results", 
            f"test_run_{timestamp}"
        )
        
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Test results will be saved to: {output_dir}")
    
    # Create test framework
    test_framework = AutomatedDetectionTest(output_dir=output_dir)
    
    # Set up test cases
    test_cases = []
    
    if args.all_profiles:
        # Test all available profiles
        profile_db = DeviceProfileDatabase()
        profiles = profile_db.get_profile_names()
        
        logger.info(f"Setting up tests for all {len(profiles)} available profiles")
        
        for profile_name in profiles:
            profile = profile_db.get_profile(profile_name)
            if profile:
                test_cases.append({
                    "name": f"test_{profile_name.replace(' ', '_')}",
                    "device_profile": profile,
                    "android_version": args.android_version,
                    "duration": args.duration,
                    "linkedin_only": args.linkedin_only
                })
    elif args.profile:
        # Test a specific profile
        profile_db = DeviceProfileDatabase()
        profile = profile_db.get_profile(args.profile)
        
        if not profile:
            logger.error(f"Profile '{args.profile}' not found")
            profiles = profile_db.get_profile_names()
            logger.info(f"Available profiles: {', '.join(profiles)}")
            return 1
            
        test_cases.append({
            "name": f"test_{args.profile.replace(' ', '_')}",
            "device_profile": profile,
            "android_version": args.android_version,
            "duration": args.duration,
            "linkedin_only": args.linkedin_only
        })
    else:
        # Use default test cases (framework will create them)
        test_cases = None
    
    # Run the tests
    logger.info(f"Starting test run with {len(test_cases) if test_cases else 'default'} test cases")
    test_framework.run_tests(test_cases)
    
    # Generate report
    report_file = test_framework.generate_report()
    if report_file:
        logger.info(f"Test report generated: {report_file}")
    
    # Print summary
    test_framework.print_summary()
    
    # Return success if all tests passed
    if all(test["result"]["success"] for test in test_framework.test_results):
        logger.info("All tests passed!")
        return 0
    else:
        logger.warning("Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())