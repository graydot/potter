#!/usr/bin/env python3
"""
Version Codename Utilities for Potter Releases
Extracts the current version codename from Swift BuildInfo for use in release process
"""

import subprocess
import re
import os
import sys
from pathlib import Path

def get_codename_for_version(version_string):
    """Get codename for a specific version (deterministic based on version and date)"""
    try:
        # Parse version to get major.minor.patch
        version_parts = version_string.split('.')
        if len(version_parts) != 3:
            return "Unknown"
        
        major, minor, patch = map(int, version_parts)
        
        # Create a deterministic seed based on version components
        # This ensures the same version always gets the same codename
        version_seed = (major * 1000) + (minor * 100) + patch
        
        # Create a temporary Swift script with the version-based seed
        temp_script = f'''
import Foundation

// MARK: - Creative Build Names Generator
struct CreativeBuildNames {{
    static func generate(versionSeed: Int) -> (buildName: String, versionCodename: String) {{
        let adjectives = [
            "Swift", "Clever", "Nimble", "Brilliant", "Elegant", "Graceful",
            "Luminous", "Radiant", "Stellar", "Cosmic", "Ethereal", "Mystical",
            "Quantum", "Phoenix", "Tornado", "Lightning", "Thunder", "Aurora"
        ]
        
        let nouns = [
            "Potter", "Alchemist", "Wizard", "Sage", "Oracle", "Mage",
            "Artisan", "Craftsman", "Sculptor", "Weaver", "Architect", "Builder",
            "Voyager", "Explorer", "Pioneer", "Pathfinder", "Trailblazer", "Navigator"
        ]
        
        let versionNames = [
            "Midnight Codex", "Digital Sorcery", "Swift Enchantment", "Code Alchemy",
            "Text Transmutation", "AI Resonance", "Neural Harmony", "Data Symphony",
            "Quantum Quill", "Silicon Dreams", "Binary Ballet", "Algorithm Aria",
            "Compiler Crescendo", "Runtime Rhapsody", "Memory Melody", "Thread Tango"
        ]
        
        // Use version-based seed for deterministic naming per version
        let seed = versionSeed % 1000
        
        let adjective = adjectives[seed % adjectives.count]
        let noun = nouns[(seed + 7) % nouns.count]
        let versionName = versionNames[(seed + 13) % versionNames.count]
        
        return (
            buildName: "\\(adjective) \\(noun) #\\(versionSeed)",
            versionCodename: versionName
        )
    }}
}}

// Extract codename and print it
let names = CreativeBuildNames.generate(versionSeed: {version_seed})
print("CODENAME:\\(names.versionCodename)")
print("BUILD_NAME:\\(names.buildName)")
'''
        
        # Write temporary script
        temp_file = "/tmp/extract_version_codename.swift"
        with open(temp_file, 'w') as f:
            f.write(temp_script)
        
        # Run Swift script
        result = subprocess.run(['swift', temp_file], capture_output=True, text=True)
        
        # Clean up
        os.remove(temp_file)
        
        if result.returncode == 0:
            # Parse output to extract codename
            for line in result.stdout.split('\n'):
                if line.startswith('CODENAME:'):
                    return line.split('CODENAME:')[1].strip()
        else:
            print(f"Swift execution failed: {result.stderr}")
            
    except Exception as e:
        print(f"Error extracting codename for version {version_string}: {e}")
    
    return "Unknown"

def get_current_codename():
    """Extract current version codename from Swift ProcessManager"""
    try:
        # Create a temporary Swift script to extract the codename
        temp_script = '''
import Foundation
import AppKit

// MARK: - Creative Build Names Generator
struct CreativeBuildNames {
    static func generate() -> (buildName: String, versionCodename: String) {
        let adjectives = [
            "Swift", "Clever", "Nimble", "Brilliant", "Elegant", "Graceful",
            "Luminous", "Radiant", "Stellar", "Cosmic", "Ethereal", "Mystical",
            "Quantum", "Phoenix", "Tornado", "Lightning", "Thunder", "Aurora"
        ]
        
        let nouns = [
            "Potter", "Alchemist", "Wizard", "Sage", "Oracle", "Mage",
            "Artisan", "Craftsman", "Sculptor", "Weaver", "Architect", "Builder",
            "Voyager", "Explorer", "Pioneer", "Pathfinder", "Trailblazer", "Navigator"
        ]
        
        let versionNames = [
            "Midnight Codex", "Digital Sorcery", "Swift Enchantment", "Code Alchemy",
            "Text Transmutation", "AI Resonance", "Neural Harmony", "Data Symphony",
            "Quantum Quill", "Silicon Dreams", "Binary Ballet", "Algorithm Aria",
            "Compiler Crescendo", "Runtime Rhapsody", "Memory Melody", "Thread Tango"
        ]
        
        // Use consistent random seed based on build date for reproducible names
        let today = Date()
        let dayComponent = Calendar.current.component(.day, from: today)
        let monthComponent = Calendar.current.component(.month, from: today)
        let yearComponent = Calendar.current.component(.year, from: today)
        let seed = dayComponent + (monthComponent * 31)
        
        let adjective = adjectives[seed % adjectives.count]
        let noun = nouns[(seed + 7) % nouns.count]
        let versionName = versionNames[(seed + 13) % versionNames.count]
        
        // Generate build number based on date for uniqueness
        let buildNumber = ((yearComponent - 2024) * 365) + ((monthComponent - 1) * 31) + dayComponent
        
        return (
            buildName: "\\(adjective) \\(noun) #\\(buildNumber)",
            versionCodename: versionName
        )
    }
}

// Extract codename and print it
let names = CreativeBuildNames.generate()
print("CODENAME:\\(names.versionCodename)")
print("BUILD_NAME:\\(names.buildName)")
'''
        
        # Write temporary script
        temp_file = "/tmp/extract_codename.swift"
        with open(temp_file, 'w') as f:
            f.write(temp_script)
        
        # Run Swift script
        result = subprocess.run(['swift', temp_file], capture_output=True, text=True)
        
        # Clean up
        os.remove(temp_file)
        
        if result.returncode == 0:
            # Parse output to extract codename
            for line in result.stdout.split('\n'):
                if line.startswith('CODENAME:'):
                    return line.split('CODENAME:')[1].strip()
        else:
            print(f"Swift execution failed: {result.stderr}")
            
    except Exception as e:
        print(f"Error extracting codename: {e}")
    
    return "Unknown"

def get_current_build_name():
    """Extract current build name from Swift ProcessManager"""
    try:
        # Create a temporary Swift script to extract the build name
        temp_script = '''
import Foundation
import AppKit

// MARK: - Creative Build Names Generator
struct CreativeBuildNames {
    static func generate() -> (buildName: String, versionCodename: String) {
        let adjectives = [
            "Swift", "Clever", "Nimble", "Brilliant", "Elegant", "Graceful",
            "Luminous", "Radiant", "Stellar", "Cosmic", "Ethereal", "Mystical",
            "Quantum", "Phoenix", "Tornado", "Lightning", "Thunder", "Aurora"
        ]
        
        let nouns = [
            "Potter", "Alchemist", "Wizard", "Sage", "Oracle", "Mage",
            "Artisan", "Craftsman", "Sculptor", "Weaver", "Architect", "Builder",
            "Voyager", "Explorer", "Pioneer", "Pathfinder", "Trailblazer", "Navigator"
        ]
        
        let versionNames = [
            "Midnight Codex", "Digital Sorcery", "Swift Enchantment", "Code Alchemy",
            "Text Transmutation", "AI Resonance", "Neural Harmony", "Data Symphony",
            "Quantum Quill", "Silicon Dreams", "Binary Ballet", "Algorithm Aria",
            "Compiler Crescendo", "Runtime Rhapsody", "Memory Melody", "Thread Tango"
        ]
        
        // Use consistent random seed based on build date for reproducible names
        let today = Date()
        let dayComponent = Calendar.current.component(.day, from: today)
        let monthComponent = Calendar.current.component(.month, from: today)
        let yearComponent = Calendar.current.component(.year, from: today)
        let seed = dayComponent + (monthComponent * 31)
        
        let adjective = adjectives[seed % adjectives.count]
        let noun = nouns[(seed + 7) % nouns.count]
        let versionName = versionNames[(seed + 13) % versionNames.count]
        
        // Generate build number based on date for uniqueness
        let buildNumber = ((yearComponent - 2024) * 365) + ((monthComponent - 1) * 31) + dayComponent
        
        return (
            buildName: "\\(adjective) \\(noun) #\\(buildNumber)",
            versionCodename: versionName
        )
    }
}

// Extract build name and print it
let names = CreativeBuildNames.generate()
print("BUILD_NAME:\\(names.buildName)")
'''
        
        # Write temporary script
        temp_file = "/tmp/extract_build_name.swift"
        with open(temp_file, 'w') as f:
            f.write(temp_script)
        
        # Run Swift script
        result = subprocess.run(['swift', temp_file], capture_output=True, text=True)
        
        # Clean up
        os.remove(temp_file)
        
        if result.returncode == 0:
            # Parse output to extract build name
            for line in result.stdout.split('\n'):
                if line.startswith('BUILD_NAME:'):
                    return line.split('BUILD_NAME:')[1].strip()
        else:
            print(f"Swift execution failed: {result.stderr}")
            
    except Exception as e:
        print(f"Error extracting build name: {e}")
    
    return "Unknown"

def sanitize_for_filename(name):
    """Sanitize codename for use in filenames"""
    # Replace spaces with hyphens, remove special characters
    sanitized = re.sub(r'[^\w\s-]', '', name)
    sanitized = re.sub(r'\s+', '-', sanitized)
    return sanitized

def get_enhanced_dmg_name(version):
    """Get DMG filename with version codename"""
    codename = get_current_codename()
    sanitized_codename = sanitize_for_filename(codename)
    return f"Potter-{version}-{sanitized_codename}.dmg"

def get_enhanced_release_title(version):
    """Get GitHub release title with version codename"""
    codename = get_current_codename()
    return f"Potter {version} - {codename}"

def get_enhanced_volume_name(version):
    """Get DMG volume name with version codename"""
    codename = get_current_codename()
    return f"Potter {version} - {codename}"

if __name__ == "__main__":
    """Test the utilities"""
    print("Testing Version Codename Utilities")
    print("=" * 40)
    
    codename = get_current_codename()
    build_name = get_current_build_name()
    
    print(f"Current Codename: {codename}")
    print(f"Current Build Name: {build_name}")
    print(f"Sanitized for filename: {sanitize_for_filename(codename)}")
    
    # Test with sample version
    version = "2.1.10"
    print(f"\nFor version {version}:")
    print(f"DMG Name: {get_enhanced_dmg_name(version)}")
    print(f"Release Title: {get_enhanced_release_title(version)}")
    print(f"Volume Name: {get_enhanced_volume_name(version)}")