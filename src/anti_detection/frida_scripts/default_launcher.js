/**
 * Default launcher script for the Android emulator
 * This script helps ensure the Android UI launches correctly
 * without showing any setup wizards or other intro screens.
 */

console.log('Default launcher script loaded');

// Define common package names for Android launchers across different versions
const LAUNCHER_PACKAGES = [
    "com.android.launcher",
    "com.android.launcher3",
    "com.android.launcher2",
    "com.google.android.apps.nexuslauncher",
    "com.android.systemui"
];

// Hook various setup wizard classes to skip them
function skipSetupWizards() {
    try {
        // Common setup wizard class paths
        const wizardClasses = [
            "com.google.android.setupwizard.SetupWizardActivity",
            "com.google.android.setupwizard.util.SetupWizardUtils",
            "com.android.settings.SetupWizardActivity"
        ];
        
        wizardClasses.forEach(className => {
            try {
                let cls = Java.use(className);
                
                // Hook common methods that might be used to check if setup is complete
                if (cls.isUserSetupComplete) {
                    cls.isUserSetupComplete.implementation = function() {
                        console.log(`[+] Bypassing ${className}.isUserSetupComplete`);
                        return true;
                    };
                }
                
                // Hook other potential methods
                const methodsToHook = [
                    "isSetupComplete", 
                    "isDeviceProvisioned", 
                    "isFirstRun",
                    "shouldShowIntro"
                ];
                
                methodsToHook.forEach(methodName => {
                    if (cls[methodName]) {
                        cls[methodName].implementation = function() {
                            console.log(`[+] Bypassing ${className}.${methodName}`);
                            return methodName.startsWith("is") ? true : false;
                        };
                    }
                });
            } catch (e) {
                // Class may not exist in this Android version, ignore
            }
        });
        
        console.log("[+] Setup wizard hooks installed");
    } catch (e) {
        console.log("[-] Error in skipSetupWizards: " + e);
    }
}

// Ensure the home screen launcher starts
function ensureLauncherStarts() {
    try {
        // Get the Activity Manager service
        const activityManager = Java.use("android.app.ActivityManager");
        
        // Hook getRecentTasks to potentially force our launcher to be visible
        if (activityManager.getRecentTasks) {
            const originalGetRecentTasks = activityManager.getRecentTasks;
            
            activityManager.getRecentTasks.implementation = function() {
                const result = originalGetRecentTasks.apply(this, arguments);
                console.log("[+] getRecentTasks called, ensuring launcher is shown");
                
                // Try to start the launcher
                startLauncher();
                
                return result;
            };
        }
        
        // Also try to directly start the launcher
        setTimeout(startLauncher, 3000);
        
        console.log("[+] Launcher ensure hooks installed");
    } catch (e) {
        console.log("[-] Error in ensureLauncherStarts: " + e);
    }
}

// Helper function to actually start the launcher
function startLauncher() {
    try {
        // Get the context
        Java.perform(function() {
            const currentApplication = Java.use("android.app.ActivityThread").currentApplication();
            const context = currentApplication.getApplicationContext();
            
            // Create an intent to start the launcher
            const Intent = Java.use("android.content.Intent");
            const intent = Intent.$new(Intent.ACTION_MAIN.value);
            intent.addCategory(Intent.CATEGORY_HOME.value);
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK.value);
            
            // Start the activity
            context.startActivity(intent);
            console.log("[+] Launcher activity started");
        });
    } catch (e) {
        console.log("[-] Error starting launcher: " + e);
    }
}

// Main function to execute when script is loaded
function main() {
    console.log("[+] Android launcher helper script loaded");
    
    // Wait for Java to be available
    Java.perform(function() {
        console.log("[+] Java runtime available");
        
        // Apply setup wizard skips
        skipSetupWizards();
        
        // Ensure the launcher is started
        ensureLauncherStarts();
    });
}

// Call the main function when the script is loaded
main();
