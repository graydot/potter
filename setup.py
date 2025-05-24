#!/usr/bin/env python3
"""
Setup script for Rephrasely - macOS Global Text Rephrasing Service
"""

import os
import sys
import subprocess
import platform

def check_macos():
    """Check if running on macOS"""
    if platform.system() != 'Darwin':
        print("❌ Error: This application is designed for macOS only")
        return False
    print("✅ macOS detected")
    return True

def check_python_version():
    """Check if Python version is adequate"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is adequate")
    return True

def create_virtual_environment():
    """Create a virtual environment if it doesn't exist"""
    venv_path = '.venv'
    
    if os.path.exists(venv_path):
        print(f"✅ Virtual environment already exists at {venv_path}")
        return True
    
    print("📦 Creating virtual environment...")
    try:
        subprocess.check_call([sys.executable, '-m', 'venv', venv_path])
        print(f"✅ Virtual environment created at {venv_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def install_dependencies():
    """Install required Python packages"""
    venv_path = '.venv'
    
    # Determine the correct pip path for the virtual environment
    if os.name == 'nt':  # Windows
        pip_path = os.path.join(venv_path, 'Scripts', 'pip')
        python_path = os.path.join(venv_path, 'Scripts', 'python')
    else:  # macOS/Linux
        pip_path = os.path.join(venv_path, 'bin', 'pip')
        python_path = os.path.join(venv_path, 'bin', 'python')
    
    print("📦 Installing Python dependencies in virtual environment...")
    try:
        # First upgrade pip
        subprocess.check_call([python_path, '-m', 'pip', 'install', '--upgrade', 'pip'])
        
        # Install requirements
        subprocess.check_call([pip_path, 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("\nTrying alternative installation method...")
        try:
            # Try with --user flag as fallback
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', '-r', 'requirements.txt'])
            print("✅ Dependencies installed with --user flag")
            return True
        except subprocess.CalledProcessError as e2:
            print(f"❌ Alternative installation also failed: {e2}")
            return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = '.env'
    if os.path.exists(env_file):
        print("✅ .env file already exists")
        return True
    
    print("📝 Creating .env file...")
    try:
        with open(env_file, 'w') as f:
            f.write("# Add your OpenAI API key here\n")
            f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
            f.write("\n# Optional: Customize other settings\n")
            f.write("# MODEL=gpt-3.5-turbo\n")
            f.write("# MAX_TOKENS=1000\n")
        
        print("✅ .env file created")
        print("⚠️  Please edit .env and add your OpenAI API key")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def create_run_script():
    """Create a convenience script to run the app with the virtual environment"""
    script_content = '''#!/bin/bash
# Rephrasely runner script - automatically uses virtual environment

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if virtual environment exists
if [ ! -d "$DIR/.venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.py first."
    exit 1
fi

# Check if .env file exists
if [ ! -f "$DIR/.env" ]; then
    echo "❌ .env file not found. Please create one with your OpenAI API key."
    exit 1
fi

# Activate virtual environment and run the app
echo "🔄 Starting Rephrasely..."
source "$DIR/.venv/bin/activate"
python "$DIR/rephrasely.py"
'''
    
    try:
        with open('run.sh', 'w') as f:
            f.write(script_content)
        
        # Make it executable
        os.chmod('run.sh', 0o755)
        print("✅ Created run.sh script for easy launching")
        return True
    except Exception as e:
        print(f"❌ Failed to create run.sh script: {e}")
        return False

def check_permissions():
    """Check and guide user about macOS permissions"""
    print("🔐 macOS Permission Requirements:")
    print("   When you first run the app, macOS will ask for:")
    print("   • Accessibility permissions (required for global hotkeys)")
    print("   • Input monitoring permissions (may be required)")
    print()
    print("   Go to: System Preferences > Security & Privacy > Privacy")
    print("   Add Terminal (or Python) to 'Accessibility' and 'Input Monitoring'")
    print()

def main():
    """Main setup function"""
    print("🔄 Rephrasely Setup")
    print("=" * 50)
    
    # Check system requirements
    if not check_macos():
        sys.exit(1)
    
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Create environment file
    if not create_env_file():
        sys.exit(1)
    
    # Create run script
    create_run_script()
    
    # Information about permissions
    check_permissions()
    
    print("🎉 Setup completed!")
    print()
    print("Next steps:")
    print("1. Edit .env file and add your OpenAI API key")
    print("   Get one from: https://platform.openai.com/api-keys")
    print()
    print("2. Test your setup:")
    print("   ./.venv/bin/python test_setup.py")
    print()
    print("3. Run Rephrasely:")
    print("   ./run.sh")
    print("   OR")
    print("   ./.venv/bin/python rephrasely.py")
    print()
    print("4. Grant accessibility permissions when prompted")
    print("5. Test with Cmd+Shift+R in any app")
    print()
    print("Need help? Check the README.md file for detailed instructions.")

if __name__ == "__main__":
    main() 