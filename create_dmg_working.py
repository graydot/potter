#!/usr/bin/env python3
"""
Working DMG Creation Function 
Extracted from working commit eca4af6
"""

import os
import subprocess
import shutil

APP_NAME = "Potter"

def create_dmg_working(app_path):
    """Create a DMG file for distribution with custom background and Applications shortcut"""
    print("💿 Creating DMG for distribution...")
    
    try:
        dmg_name = f"{APP_NAME}-1.0.dmg"
        dmg_path = f"dist/{dmg_name}"
        temp_dmg = f"dist/temp_{dmg_name}"
        
        # Remove existing DMGs
        for path in [dmg_path, temp_dmg]:
            if os.path.exists(path):
                os.remove(path)
        
        # Create temporary DMG folder
        temp_folder = "dist/dmg_temp"
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
        os.makedirs(temp_folder)
        
        # Copy app to temp folder
        shutil.copytree(app_path, f"{temp_folder}/{APP_NAME}.app")
        
        # Create Applications shortcut
        subprocess.run([
            'ln', '-s', '/Applications', f"{temp_folder}/Applications"
        ], check=True)
        
        # Check for custom background
        background_path = None
        background_candidates = [
            "assets/dmg_background.png",
            "assets/potter_dmg_background.png", 
            "dmg_background.png"
        ]
        
        for bg_path in background_candidates:
            if os.path.exists(bg_path):
                background_path = bg_path
                break
        
        # Create initial DMG using srcfolder (the key difference!)
        cmd = [
            'hdiutil', 'create',
            '-size', '100m',
            '-fs', 'HFS+',
            '-volname', APP_NAME,
            '-srcfolder', temp_folder,
            temp_dmg
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ DMG creation failed: {result.stderr}")
            return None
        
        # Mount the DMG for customization (read-write)
        mount_result = subprocess.run([
            'hdiutil', 'attach', temp_dmg, '-mountpoint', '/Volumes/Potter', '-readwrite'
        ], capture_output=True, text=True)
        
        if mount_result.returncode == 0:
            print("🎨 Customizing DMG layout...")
            
            # Copy background if available
            if background_path:
                shutil.copy2(background_path, '/Volumes/Potter/.background.png')
                
            # Create .DS_Store for custom layout (using basic positioning)
            ds_store_script = f'''
tell application "Finder"
    tell disk "{APP_NAME}"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {{400, 100, 900, 400}}
        set viewOptions to the icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to 100
        set position of item "{APP_NAME}.app" of container window to {{150, 200}}
        set position of item "Applications" of container window to {{350, 200}}
        '''
            
            if background_path:
                ds_store_script += f'''
        set background picture of viewOptions to file ".background.png" of disk "{APP_NAME}"
                '''
            
            ds_store_script += '''
        close
        open
        update without registering applications
        delay 2
    end tell
end tell
'''
            
            # Apply layout using AppleScript
            try:
                subprocess.run([
                    'osascript', '-e', ds_store_script
                ], check=False)  # Don't fail if AppleScript fails
            except:
                pass
            
            # Unmount
            subprocess.run(['hdiutil', 'detach', '/Volumes/Potter'], check=False)
        
        # Convert to final compressed DMG
        subprocess.run([
            'hdiutil', 'convert', temp_dmg,
            '-format', 'UDZO',
            '-o', dmg_path
        ], check=True)
        
        # Clean up
        os.remove(temp_dmg)
        shutil.rmtree(temp_folder)
        
        print(f"✅ DMG created: {dmg_path}")
        return dmg_path
            
    except Exception as e:
        print(f"❌ DMG creation error: {e}")
        # Clean up on error
        for path in [temp_dmg, "dist/dmg_temp"]:
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
        return None

if __name__ == "__main__":
    # Test the working DMG creation
    app_path = "dist/Potter.app"
    if os.path.exists(app_path):
        result = create_dmg_working(app_path)
        if result:
            print(f"Success! DMG created at: {result}")
        else:
            print("Failed to create DMG")
    else:
        print(f"App not found at {app_path}")