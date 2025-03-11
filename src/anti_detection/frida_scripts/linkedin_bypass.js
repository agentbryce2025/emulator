/*
 * LinkedIn-specific detection bypass script for Frida.
 * This script specifically targets LinkedIn's detection methods.
 */

(function() {
    'use strict';

    // Create a JavaScript object to store our utilities
    const LinkedInBypass = {
        // Profile data to spoof
        deviceProfile: {
            // Will be populated dynamically by our Python code
        },
        
        // Initialize the bypass hooks
        init: function(profile) {
            console.log("[+] Initializing LinkedIn detection bypass");
            
            // Store profile data if provided
            if (profile) {
                this.deviceProfile = JSON.parse(profile);
                console.log("[+] Loaded device profile: " + this.deviceProfile.manufacturer + " " + this.deviceProfile.model);
            }
            
            this.hookBuiltInChecks();
            this.hookLinkedInSpecificChecks();
            this.hookJavaScriptBridge();
            this.hookNetworkCalls();
            this.hookSensorsAPI();
            this.hookCameraAPI();
            this.hookTouchEvents();
            
            console.log("[+] LinkedIn detection bypass initialized");
        },
        
        // Hook LinkedIn's built-in emulator checks
        hookBuiltInChecks: function() {
            console.log("[*] Hooking built-in emulator checks");
            
            // Hook LinkedIn's custom EmulatorDetector class (if it exists)
            try {
                if (Java.available) {
                    // Search for common detector class patterns
                    ['com.linkedin.android.utils.EmulatorDetector',
                     'com.linkedin.android.security.EmulatorChecker',
                     'com.linkedin.android.common.security.DeviceVerifier'].forEach(className => {
                        try {
                            const EmulatorCheckerClass = Java.use(className);
                            
                            // Hook all methods that return boolean
                            const methods = EmulatorCheckerClass.class.getDeclaredMethods();
                            methods.forEach(method => {
                                const methodName = method.getName();
                                const returnType = method.getReturnType().getName();
                                
                                if (returnType === 'boolean') {
                                    try {
                                        EmulatorCheckerClass[methodName].overload().implementation = function() {
                                            console.log(`[*] Bypassed ${className}.${methodName}() - returning false`);
                                            return false;  // Not an emulator
                                        };
                                        console.log(`[+] Hooked ${className}.${methodName}()`);
                                    } catch (e) {
                                        // Method might have parameters or overloads
                                    }
                                }
                            });
                        } catch (e) {
                            // Class not found, continue to the next one
                        }
                    });
                }
            } catch (e) {
                console.log("[-] Error hooking built-in checks: " + e);
            }
        },
        
        // Hook LinkedIn-specific detection checks
        hookLinkedInSpecificChecks: function() {
            console.log("[*] Hooking LinkedIn-specific checks");
            
            try {
                if (Java.available) {
                    // LinkedIn uses a few specific methods for device verification
                    const securityClasses = [
                        'com.linkedin.android.security.SecurityChecker',
                        'com.linkedin.android.utils.SecurityUtils',
                        'com.linkedin.security.DeviceIntegrityChecker'
                    ];
                    
                    securityClasses.forEach(className => {
                        try {
                            const SecurityClass = Java.use(className);
                            
                            // Hook security methods
                            ['isRooted', 'isEmulator', 'isDeviceCompromised', 'hasSecurityIssue'].forEach(methodName => {
                                try {
                                    SecurityClass[methodName].overload().implementation = function() {
                                        console.log(`[*] Bypassed ${className}.${methodName}() - returning false`);
                                        return false;
                                    };
                                    console.log(`[+] Hooked ${className}.${methodName}()`);
                                } catch (e) {
                                    // Method doesn't exist or has different signature
                                }
                            });
                        } catch (e) {
                            // Class not found, continue to the next one
                        }
                    });
                    
                    // LinkedIn might also use analytics packages for device verification
                    try {
                        const DeviceInfo = Java.use('com.linkedin.android.analytics.DeviceInfo');
                        DeviceInfo.isEmulator.implementation = function() {
                            console.log("[*] Bypassed DeviceInfo.isEmulator() - returning false");
                            return false;
                        };
                    } catch (e) {
                        // Class or method not found
                    }
                }
            } catch (e) {
                console.log("[-] Error hooking LinkedIn-specific checks: " + e);
            }
        },
        
        // Hook JavaScript bridge (WebView) calls
        hookJavaScriptBridge: function() {
            console.log("[*] Hooking JavaScript bridge");
            
            try {
                if (Java.available) {
                    // Hook WebView addJavascriptInterface to monitor JS bridges
                    const WebView = Java.use('android.webkit.WebView');
                    WebView.addJavascriptInterface.overload('java.lang.Object', 'java.lang.String').implementation = function(obj, name) {
                        console.log(`[*] WebView.addJavascriptInterface called with name: ${name}`);
                        
                        // Track the object being registered for JS interface
                        if (name === 'DeviceInfo' || name === 'SecurityChecker') {
                            // Proxy the object to modify its behavior
                            try {
                                const objClass = obj.getClass();
                                const methods = objClass.getDeclaredMethods();
                                
                                methods.forEach(method => {
                                    const methodName = method.getName();
                                    const returnType = method.getReturnType().getName();
                                    
                                    if (returnType === 'boolean' && 
                                        (methodName.includes('isEmulator') || 
                                         methodName.includes('isRooted') || 
                                         methodName.includes('check'))) {
                                        try {
                                            const targetClass = Java.use(objClass.getName());
                                            targetClass[methodName].implementation = function() {
                                                console.log(`[*] Bypassed JS bridge ${name}.${methodName}() - returning false`);
                                                return false;
                                            };
                                        } catch (e) {
                                            // Method can't be hooked or has different signature
                                        }
                                    }
                                });
                            } catch (e) {
                                console.log(`[-] Error proxying JS interface object: ${e}`);
                            }
                        }
                        
                        // Call the original method
                        return this.addJavascriptInterface(obj, name);
                    };
                }
            } catch (e) {
                console.log("[-] Error hooking JavaScript bridge: " + e);
            }
        },
        
        // Hook network calls to intercept device data being sent
        hookNetworkCalls: function() {
            console.log("[*] Hooking network calls");
            
            try {
                if (Java.available) {
                    // Hook OkHttp (commonly used by LinkedIn)
                    try {
                        const OkHttpClient = Java.use('okhttp3.OkHttpClient');
                        const Request = Java.use('okhttp3.Request');
                        const RequestBuilder = Java.use('okhttp3.Request$Builder');
                        
                        // Hook builder to detect device info gathering
                        RequestBuilder.build.implementation = function() {
                            const request = this.build();
                            const url = request.url().toString();
                            
                            // If this is a request to LinkedIn analytics or security endpoints
                            if (url.includes('analytics') || 
                                url.includes('security') || 
                                url.includes('verification') || 
                                url.includes('api.linkedin.com')) {
                                
                                console.log(`[*] LinkedIn API call detected: ${url}`);
                                
                                // Consider modifying request headers or body here if needed
                                // This would require more complex modification of the request
                            }
                            
                            return request;
                        };
                        
                        // Also hook the response processing in case there's device fingerprinting
                        const Response = Java.use('okhttp3.Response');
                        Response.body.implementation = function() {
                            const originalBody = this.body();
                            
                            // Here we could modify response data if needed
                            // For example, LinkedIn might return instructions to perform additional checks
                            
                            return originalBody;
                        };
                    } catch (e) {
                        console.log("[-] Error hooking OkHttp: " + e);
                    }
                }
            } catch (e) {
                console.log("[-] Error hooking network calls: " + e);
            }
        },
        
        // Hook sensors API for more realistic values
        hookSensorsAPI: function() {
            console.log("[*] Hooking sensors API");
            
            try {
                if (Java.available) {
                    // Hook the SensorManager to provide realistic sensor data
                    const SensorManager = Java.use('android.hardware.SensorManager');
                    const Sensor = Java.use('android.hardware.Sensor');
                    
                    // Hook getSensorList to show a realistic set of sensors
                    SensorManager.getSensorList.overload('int').implementation = function(type) {
                        const originalList = this.getSensorList(type);
                        
                        // Let's allow the real implementation for most sensor types
                        // LinkedIn checks for these sensors being present and realistic
                        return originalList;
                    };
                    
                    // Hook registerListener to intercept sensor registration
                    SensorManager.registerListener.overload(
                        'android.hardware.SensorEventListener', 
                        'android.hardware.Sensor', 
                        'int'
                    ).implementation = function(listener, sensor, samplingPeriodUs) {
                        console.log(`[*] Sensor listener registered for sensor type: ${sensor.getType()}`);
                        
                        // Register the real listener
                        const result = this.registerListener(listener, sensor, samplingPeriodUs);
                        
                        // For accelerometer, we could hook the SensorEventListener to provide realistic values
                        if (sensor.getType() === 1) { // TYPE_ACCELEROMETER
                            console.log("[*] Hooking accelerometer values");
                            
                            // Here we would hook the listener's onSensorChanged method
                            // to provide realistic accelerometer data
                            // This requires finding the listener instance which is complex
                        }
                        
                        return result;
                    };
                }
            } catch (e) {
                console.log("[-] Error hooking sensors API: " + e);
            }
        },
        
        // Hook camera API to fake camera availability
        hookCameraAPI: function() {
            console.log("[*] Hooking camera API");
            
            try {
                if (Java.available) {
                    // Hook Camera API to pretend we have a camera
                    const Camera = Java.use('android.hardware.Camera');
                    
                    // getNumberOfCameras is often used to check if device has cameras
                    Camera.getNumberOfCameras.implementation = function() {
                        console.log("[*] Camera.getNumberOfCameras called - returning 2");
                        return 2; // Pretend we have front and back cameras
                    };
                    
                    // getCameraInfo is used to check camera capabilities
                    Camera.getCameraInfo.implementation = function(cameraId, cameraInfo) {
                        this.getCameraInfo(cameraId, cameraInfo);
                        console.log(`[*] Camera.getCameraInfo called for camera id: ${cameraId}`);
                        // cameraInfo is modified in-place by the original method
                        // We could modify its values here if needed
                        return;
                    };
                    
                    // Also hook Camera2 API which might be used on newer Android versions
                    try {
                        const CameraManager = Java.use('android.hardware.camera2.CameraManager');
                        CameraManager.getCameraIdList.implementation = function() {
                            console.log("[*] CameraManager.getCameraIdList called - returning fake camera IDs");
                            return Java.array('java.lang.String', ['0', '1']); // Front and back cameras
                        };
                    } catch (e) {
                        // Camera2 API not available or not being used
                    }
                }
            } catch (e) {
                console.log("[-] Error hooking camera API: " + e);
            }
        },
        
        // Hook touch events to simulate real human behavior
        hookTouchEvents: function() {
            console.log("[*] Hooking touch events");
            
            try {
                if (Java.available) {
                    // LinkedIn might analyze touch patterns to detect automated input
                    const MotionEvent = Java.use('android.view.MotionEvent');
                    
                    // Hook the obtain methods which create MotionEvents
                    MotionEvent.obtain.overload(
                        'long', 'long', 'int', 'float', 'float', 'float', 'float', 'int', 'float', 'float', 'int', 'int'
                    ).implementation = function(downTime, eventTime, action, x, y, pressure, size, metaState, xPrecision, yPrecision, deviceId, edgeFlags) {
                        // Add slight variations to touch data to make it seem more human
                        if (action === 0 || action === 2) { // ACTION_DOWN or ACTION_MOVE
                            // Add small random variation to pressure and size
                            pressure += (Math.random() - 0.5) * 0.01;
                            size += (Math.random() - 0.5) * 0.01;
                            
                            console.log(`[*] Modified MotionEvent (${action}) at (${x}, ${y}) with pressure ${pressure}`);
                        }
                        
                        return this.obtain(downTime, eventTime, action, x, y, pressure, size, metaState, xPrecision, yPrecision, deviceId, edgeFlags);
                    };
                }
            } catch (e) {
                console.log("[-] Error hooking touch events: " + e);
            }
        },
    };
    
    // Export the module
    return {
        init: function(profile) {
            LinkedInBypass.init(profile);
        }
    };
})();