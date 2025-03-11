/*
 * Detection bypass script for Frida.
 * This script hooks into various Android APIs commonly used for emulator detection.
 */

// Create a JavaScript object to store our utilities
const EmulatorDetectionBypass = {
    // Store original values for reference
    originalValues: {},
    
    // Initialize the bypass hooks
    init: function() {
        console.log("[+] Initializing emulator detection bypass");
        
        this.hookBuildProperties();
        this.hookSystemProperties();
        this.hookTelephonyManager();
        this.hookSensorManager();
        this.hookPackageManager();
        this.hookConnectivityManager();
        this.hookFileSystem();
        this.hookCpuInfo();
        
        console.log("[+] Emulator detection bypass initialized");
    },
    
    // Hook Android Build class properties
    hookBuildProperties: function() {
        console.log("[*] Hooking Build properties");
        
        const Build = Java.use("android.os.Build");
        const BuildFINGERPRINT = Build.FINGERPRINT.value;
        const BuildMODEL = Build.MODEL.value;
        const BuildMANUFACTURER = Build.MANUFACTURER.value;
        const BuildPRODUCT = Build.PRODUCT.value;
        const BuildBRAND = Build.BRAND.value;
        const BuildDEVICE = Build.DEVICE.value;
        const BuildHARDWARE = Build.HARDWARE.value;
        
        // Store original values
        this.originalValues.BUILD_FINGERPRINT = BuildFINGERPRINT;
        this.originalValues.BUILD_MODEL = BuildMODEL;
        this.originalValues.BUILD_MANUFACTURER = BuildMANUFACTURER;
        this.originalValues.BUILD_PRODUCT = BuildPRODUCT;
        this.originalValues.BUILD_BRAND = BuildBRAND;
        this.originalValues.BUILD_DEVICE = BuildDEVICE;
        this.originalValues.BUILD_HARDWARE = BuildHARDWARE;
        
        // Override Build.FINGERPRINT
        Build.FINGERPRINT.value = "Samsung/SM-G991B/galaxy_s21:12/SP1A.210812.016/G991BXXU3CUK1:user/release-keys";
        // Override Build.MODEL
        Build.MODEL.value = "SM-G991B";
        // Override Build.MANUFACTURER
        Build.MANUFACTURER.value = "Samsung";
        // Override Build.PRODUCT
        Build.PRODUCT.value = "galaxy_s21";
        // Override Build.BRAND
        Build.BRAND.value = "Samsung";
        // Override Build.DEVICE
        Build.DEVICE.value = "galaxy_s21";
        // Override Build.HARDWARE
        Build.HARDWARE.value = "exynos2100";
        
        console.log("[*] Build properties hooked");
    },
    
    // Hook System Properties access
    hookSystemProperties: function() {
        console.log("[*] Hooking System properties");
        
        // Hook System.getProperty() method
        const System = Java.use("java.lang.System");
        System.getProperty.overload("java.lang.String").implementation = function(key) {
            const original = this.getProperty(key);
            
            // Check for common emulator detection properties
            if (key === "ro.kernel.qemu" || 
                key === "ro.kernel.android.qemud" || 
                key === "qemu.hw.mainkeys" || 
                key === "qemu.sf.fake_camera") {
                console.log(`[*] System.getProperty("${key}") intercepted, returning null instead of "${original}"`);
                return null;
            }
            
            // Log other accessed properties for debugging
            console.log(`[*] System.getProperty("${key}") = "${original}"`);
            return original;
        };
        
        // Hook SystemProperties.get() method
        try {
            const SystemProperties = Java.use("android.os.SystemProperties");
            
            SystemProperties.get.overload("java.lang.String").implementation = function(key) {
                const original = this.get(key);
                
                if (key.indexOf("qemu") >= 0 || key.indexOf("goldfish") >= 0 || key.indexOf("emulator") >= 0) {
                    console.log(`[*] SystemProperties.get("${key}") intercepted, returning empty string instead of "${original}"`);
                    return "";
                }
                
                return original;
            };
            
            SystemProperties.get.overload("java.lang.String", "java.lang.String").implementation = function(key, def) {
                const original = this.get(key, def);
                
                if (key.indexOf("qemu") >= 0 || key.indexOf("goldfish") >= 0 || key.indexOf("emulator") >= 0) {
                    console.log(`[*] SystemProperties.get("${key}", "${def}") intercepted, returning "${def}" instead of "${original}"`);
                    return def;
                }
                
                return original;
            };
        } catch (e) {
            console.log("[!] Error hooking SystemProperties: " + e);
        }
        
        console.log("[*] System properties hooked");
    },
    
    // Hook TelephonyManager for device ID and IMEI
    hookTelephonyManager: function() {
        console.log("[*] Hooking TelephonyManager");
        
        const TelephonyManager = Java.use("android.telephony.TelephonyManager");
        
        // Hook getDeviceId
        if (TelephonyManager.getDeviceId) {
            try {
                TelephonyManager.getDeviceId.overload().implementation = function() {
                    const fakeImei = "356938035643809"; // Fake IMEI
                    console.log(`[*] TelephonyManager.getDeviceId() intercepted, returning ${fakeImei}`);
                    return fakeImei;
                };
            } catch (e) {
                console.log("[!] Error hooking TelephonyManager.getDeviceId(): " + e);
            }
        }
        
        // Hook getImei for Android 8+
        if (TelephonyManager.getImei) {
            try {
                TelephonyManager.getImei.overload().implementation = function() {
                    const fakeImei = "356938035643809"; // Fake IMEI
                    console.log(`[*] TelephonyManager.getImei() intercepted, returning ${fakeImei}`);
                    return fakeImei;
                };
                
                TelephonyManager.getImei.overload("int").implementation = function(slotIndex) {
                    const fakeImei = "356938035643809"; // Fake IMEI
                    console.log(`[*] TelephonyManager.getImei(${slotIndex}) intercepted, returning ${fakeImei}`);
                    return fakeImei;
                };
            } catch (e) {
                console.log("[!] Error hooking TelephonyManager.getImei(): " + e);
            }
        }
        
        // Hook getSubscriberId
        if (TelephonyManager.getSubscriberId) {
            try {
                TelephonyManager.getSubscriberId.overload().implementation = function() {
                    const fakeIMSI = "310260000000000"; // Fake IMSI
                    console.log(`[*] TelephonyManager.getSubscriberId() intercepted, returning ${fakeIMSI}`);
                    return fakeIMSI;
                };
            } catch (e) {
                console.log("[!] Error hooking TelephonyManager.getSubscriberId(): " + e);
            }
        }
        
        // Hook getPhoneType
        if (TelephonyManager.getPhoneType) {
            try {
                TelephonyManager.getPhoneType.overload().implementation = function() {
                    const GSM = 1; // GSM phone type
                    console.log(`[*] TelephonyManager.getPhoneType() intercepted, returning GSM (${GSM})`);
                    return GSM;
                };
            } catch (e) {
                console.log("[!] Error hooking TelephonyManager.getPhoneType(): " + e);
            }
        }
        
        // Hook getNetworkOperatorName
        if (TelephonyManager.getNetworkOperatorName) {
            try {
                TelephonyManager.getNetworkOperatorName.overload().implementation = function() {
                    const fakeOperator = "T-Mobile";
                    console.log(`[*] TelephonyManager.getNetworkOperatorName() intercepted, returning ${fakeOperator}`);
                    return fakeOperator;
                };
            } catch (e) {
                console.log("[!] Error hooking TelephonyManager.getNetworkOperatorName(): " + e);
            }
        }
        
        console.log("[*] TelephonyManager hooked");
    },
    
    // Hook SensorManager to simulate real device sensors
    hookSensorManager: function() {
        console.log("[*] Hooking SensorManager");
        
        // This part is complex and requires custom sensor data simulation
        // In practice, we would pass in sensor data from our Python simulator
        
        // For now, we'll just make sure apps detect that all common sensors exist
        try {
            const Context = Java.use("android.content.Context");
            const Sensor = Java.use("android.hardware.Sensor");
            const SensorManager = Java.use("android.hardware.SensorManager");
            
            // Hook getSensorList to ensure all expected sensors are reported
            SensorManager.getSensorList.implementation = function(type) {
                const originalList = this.getSensorList(type);
                
                // If checking for all sensors, make sure we have a complete set
                if (type === Sensor.TYPE_ALL.value) {
                    console.log("[*] SensorManager.getSensorList(ALL) intercepted");
                    
                    // Check if we have at least one of each common sensor type
                    // In a full implementation, we would add missing sensors here
                }
                
                return originalList;
            };
            
            // For specific sensor types that might be checked
            const commonSensorTypes = [
                Sensor.TYPE_ACCELEROMETER.value,
                Sensor.TYPE_GYROSCOPE.value,
                Sensor.TYPE_MAGNETIC_FIELD.value,
                Sensor.TYPE_LIGHT.value,
                Sensor.TYPE_PROXIMITY.value
            ];
            
            // Hook getDefaultSensor
            SensorManager.getDefaultSensor.overload("int").implementation = function(type) {
                const originalSensor = this.getDefaultSensor(type);
                
                if (originalSensor === null && commonSensorTypes.includes(type)) {
                    console.log(`[*] SensorManager.getDefaultSensor(${type}) returned null, spoofing should be implemented here`);
                    // In a full implementation, we would return a fake sensor object here
                    // For now, returning the original null to avoid crashing apps
                }
                
                return originalSensor;
            };
        } catch (e) {
            console.log("[!] Error hooking SensorManager: " + e);
        }
        
        console.log("[*] SensorManager hooked");
    },
    
    // Hook PackageManager to hide emulator packages
    hookPackageManager: function() {
        console.log("[*] Hooking PackageManager");
        
        try {
            const packageManagerClass = Java.use("android.content.pm.PackageManager");
            const List = Java.use("java.util.List");
            
            // List of emulator-related packages to hide
            const emuPackages = [
                "com.android.launcher.StubApp",
                "com.google.android.launcher.layouts.genymotion",
                "com.bluestacks",
                "com.bignox",
                "com.google.android.emu",
                "com.android.emu"
            ];
            
            // Hook getInstalledPackages to filter out emulator packages
            packageManagerClass.getInstalledPackages.overload("int").implementation = function(flags) {
                const packages = this.getInstalledPackages(flags);
                console.log("[*] PackageManager.getInstalledPackages() intercepted");
                
                // Filter would be implemented here in a full implementation
                
                return packages;
            };
            
            // Hook getInstalledApplications to filter out emulator applications
            packageManagerClass.getInstalledApplications.overload("int").implementation = function(flags) {
                const applications = this.getInstalledApplications(flags);
                console.log("[*] PackageManager.getInstalledApplications() intercepted");
                
                // Filter would be implemented here in a full implementation
                
                return applications;
            };
        } catch (e) {
            console.log("[!] Error hooking PackageManager: " + e);
        }
        
        console.log("[*] PackageManager hooked");
    },
    
    // Hook ConnectivityManager for network-related detection
    hookConnectivityManager: function() {
        console.log("[*] Hooking ConnectivityManager");
        
        try {
            const connectivityManagerClass = Java.use("android.net.ConnectivityManager");
            const networkInfoClass = Java.use("android.net.NetworkInfo");
            
            // Hook getActiveNetworkInfo to provide realistic network info
            connectivityManagerClass.getActiveNetworkInfo.implementation = function() {
                const networkInfo = this.getActiveNetworkInfo();
                console.log("[*] ConnectivityManager.getActiveNetworkInfo() intercepted");
                
                // Ensure we're showing as connected
                // A more sophisticated implementation would modify the NetworkInfo object
                
                return networkInfo;
            };
            
            // Hook getNetworkInterfaces in NetworkInterface class to hide emulator interfaces
            const networkInterfaceClass = Java.use("java.net.NetworkInterface");
            const enumerationClass = Java.use("java.util.Enumeration");
            
            networkInterfaceClass.getNetworkInterfaces.implementation = function() {
                const interfaces = this.getNetworkInterfaces();
                console.log("[*] NetworkInterface.getNetworkInterfaces() intercepted");
                
                // A full implementation would filter out emulator-specific interfaces
                
                return interfaces;
            };
        } catch (e) {
            console.log("[!] Error hooking ConnectivityManager: " + e);
        }
        
        console.log("[*] ConnectivityManager hooked");
    },
    
    // Hook filesystem access to hide emulator-specific files
    hookFileSystem: function() {
        console.log("[*] Hooking File system access");
        
        try {
            const File = Java.use("java.io.File");
            
            // List of emulator-specific paths to hide
            const emuPaths = [
                "/sys/devices/virtual/",
                "/sys/qemu_trace",
                "/system/lib/libc_malloc_debug_qemu.so",
                "/sys/kernel/debug/kvm",
                "/dev/socket/qemud",
                "/dev/qemu_pipe",
                "/dev/goldfish_pipe"
            ];
            
            // Hook exists() to hide emulator-specific files
            File.exists.implementation = function() {
                const filePath = this.getAbsolutePath();
                const exists = this.exists();
                
                if (emuPaths.some(path => filePath.startsWith(path))) {
                    console.log(`[*] File.exists() intercepted for ${filePath}, returning false instead of ${exists}`);
                    return false;
                }
                
                return exists;
            };
            
            // Hook isDirectory() for similar reasons
            File.isDirectory.implementation = function() {
                const filePath = this.getAbsolutePath();
                const isDir = this.isDirectory();
                
                if (emuPaths.some(path => filePath.startsWith(path))) {
                    console.log(`[*] File.isDirectory() intercepted for ${filePath}, returning false instead of ${isDir}`);
                    return false;
                }
                
                return isDir;
            };
        } catch (e) {
            console.log("[!] Error hooking File system: " + e);
        }
        
        console.log("[*] File system access hooked");
    },
    
    // Hook CPU info access
    hookCpuInfo: function() {
        console.log("[*] Hooking CPU info access");
        
        try {
            // Hook the Java Runtime.getRuntime().exec() method to intercept commands
            const Runtime = Java.use("java.lang.Runtime");
            
            Runtime.exec.overload("java.lang.String").implementation = function(cmd) {
                console.log(`[*] Runtime.exec("${cmd}") intercepted`);
                
                // Check for commands that might be used for emulator detection
                if (cmd.includes("/proc/cpuinfo") || cmd.includes("getprop")) {
                    // For these commands, we need to modify the process output
                    // This is a placeholder for the actual implementation
                    console.log("[*] CPU/property check command detected, consider returning modified data");
                }
                
                return this.exec(cmd);
            };
            
            // There are multiple overloads of exec() we should hook
            Runtime.exec.overload("[Ljava.lang.String;").implementation = function(cmdArray) {
                if (cmdArray.length > 0) {
                    console.log(`[*] Runtime.exec([${cmdArray.join(", ")}]) intercepted`);
                    
                    // Check for commands that might be used for emulator detection
                    if (cmdArray[0].includes("cat") && cmdArray.length > 1 && cmdArray[1].includes("/proc/cpuinfo")) {
                        console.log("[*] CPU info check detected, consider returning modified data");
                    }
                }
                
                return this.exec(cmdArray);
            };
        } catch (e) {
            console.log("[!] Error hooking CPU info access: " + e);
        }
        
        console.log("[*] CPU info access hooked");
    }
};

// Run the bypass when the script is loaded
EmulatorDetectionBypass.init();

// Export the bypass object for external use
export {EmulatorDetectionBypass};