#!/usr/bin/env python3
"""
Launcher for the Kubernetes MCP GUI Client
Checks dependencies and launches the graphical interface
"""

import sys
import subprocess
import os

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['kubernetes']
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies():
    """Install missing dependencies"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "gui_requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def main():
    """Main launcher function"""
    print("🚀 Kubernetes MCP GUI Client Launcher")
    print("=" * 40)
    
    # Check dependencies
    missing = check_dependencies()
    
    if missing:
        print(f"⚠️  Missing packages: {', '.join(missing)}")
        print("Installing dependencies...")
        
        if not install_dependencies():
            print("❌ Failed to install dependencies. Please install manually:")
            print("   pip install -r gui_requirements.txt")
            return
        
        # Check again after installation
        missing = check_dependencies()
        if missing:
            print("❌ Still missing packages after installation")
            return
    
    print("✅ All dependencies satisfied!")
    print("Launching GUI client...")
    
    # Launch the GUI
    try:
        from gui_client import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"❌ Failed to import GUI client: {e}")
        print("Make sure you're running this from the kubernetes directory")
    except Exception as e:
        print(f"❌ GUI launch failed: {e}")

if __name__ == "__main__":
    main()

