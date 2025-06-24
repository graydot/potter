#!/usr/bin/env python3
"""
Potter Version Manager
Provides deterministic version management with single source of truth
"""

import os
import plistlib
import re
from pathlib import Path

# Single source of truth for version
INFO_PLIST_PATH = "swift-potter/Sources/Resources/Info.plist"

def get_current_version():
    """Get current version from the authoritative source (Info.plist)"""
    if not os.path.exists(INFO_PLIST_PATH):
        raise FileNotFoundError(f"Info.plist not found at {INFO_PLIST_PATH}")
    
    with open(INFO_PLIST_PATH, 'rb') as f:
        plist_data = plistlib.load(f)
    
    version = plist_data.get('CFBundleShortVersionString')
    if not version:
        raise ValueError("CFBundleShortVersionString not found in Info.plist")
    
    return version

def set_version(new_version):
    """Set version in the authoritative source (Info.plist)"""
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        raise ValueError(f"Invalid version format: {new_version}. Must be X.Y.Z")
    
    if not os.path.exists(INFO_PLIST_PATH):
        raise FileNotFoundError(f"Info.plist not found at {INFO_PLIST_PATH}")
    
    # Read current plist
    with open(INFO_PLIST_PATH, 'rb') as f:
        plist_data = plistlib.load(f)
    
    # Update version fields
    plist_data['CFBundleVersion'] = new_version
    plist_data['CFBundleShortVersionString'] = new_version
    
    # Write back
    with open(INFO_PLIST_PATH, 'wb') as f:
        plistlib.dump(plist_data, f)
    
    print(f"✅ Updated version to {new_version} in {INFO_PLIST_PATH}")
    return new_version

def bump_version(current_version, bump_type='patch'):
    """Bump version number deterministically"""
    parts = current_version.split('.')
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {current_version}. Must be X.Y.Z")
    
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}. Must be 'major', 'minor', or 'patch'")
    
    return f"{major}.{minor}.{patch}"

def main():
    """CLI interface for version management"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Potter Version Manager')
    parser.add_argument('--get', action='store_true', help='Get current version')
    parser.add_argument('--set', help='Set specific version (X.Y.Z format)')
    parser.add_argument('--bump', choices=['major', 'minor', 'patch'], help='Bump version')
    
    args = parser.parse_args()
    
    if args.get:
        version = get_current_version()
        print(version)
    elif args.set:
        set_version(args.set)
    elif args.bump:
        current = get_current_version()
        new_version = bump_version(current, args.bump)
        set_version(new_version)
        print(f"Bumped {args.bump} version: {current} → {new_version}")
    else:
        # Default: show current version
        version = get_current_version()
        print(f"Current version: {version}")

if __name__ == "__main__":
    main()