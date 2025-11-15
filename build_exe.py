"""
Build script for creating Windows executables of the Dupes application.
This script uses PyInstaller to create standalone .exe files.
"""

import os
import subprocess
import sys
import shutil

def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        print("✓ PyInstaller is installed")
        return True
    except ImportError:
        print("✗ PyInstaller is not installed")
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True

def clean_build_dirs():
    """Clean previous build directories."""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}/...")
            shutil.rmtree(dir_name)

def build_gui_exe():
    """Build the GUI version executable."""
    print("\n" + "="*60)
    print("Building GUI executable...")
    print("="*60)
    
    # PyInstaller command for GUI
    cmd = [
        'pyinstaller',
        '--name=DupesFinder',
        '--onefile',  # Single executable file
        '--windowed',  # No console window for GUI
        '--icon=NONE',  # You can add an icon file path here later
        '--add-data', 'src;src',  # Include src directory
        '--hidden-import', 'flet',
        '--hidden-import', 'flet.canvas',
        '--hidden-import', 'flet.matplotlib_chart',
        '--hidden-import', 'flet.plotly_chart',
        '--hidden-import', 'click',
        '--collect-all', 'flet',
        'run_gui.py'  # Use entry point instead of direct src/gui.py
    ]
    
    try:
        subprocess.check_call(cmd)
        print("\n✓ GUI executable built successfully!")
        print("Location: dist/DupesFinder.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Failed to build GUI executable: {e}")
        return False
    
    return True

def build_cli_exe():
    """Build the CLI version executable."""
    print("\n" + "="*60)
    print("Building CLI executable...")
    print("="*60)
    
    # PyInstaller command for CLI
    cmd = [
        'pyinstaller',
        '--name=dupes',
        '--onefile',  # Single executable file
        '--console',  # Keep console window for CLI
        '--icon=NONE',
        '--add-data', 'src;src',  # Include src directory
        '--hidden-import', 'click',
        'run_cli.py'  # Use entry point instead of direct src/cli.py
    ]
    
    try:
        subprocess.check_call(cmd)
        print("\n✓ CLI executable built successfully!")
        print("Location: dist/dupes.exe")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Failed to build CLI executable: {e}")
        return False
    
    return True

def main():
    """Main build function."""
    print("="*60)
    print("Dupes Application - Windows Executable Builder")
    print("="*60)
    
    # Check if PyInstaller is installed
    if not check_pyinstaller():
        print("Failed to install PyInstaller. Exiting.")
        return
    
    # Clean previous builds
    clean_build_dirs()
    
    # Ask user what to build
    print("\nWhat would you like to build?")
    print("1. GUI version only (DupesFinder.exe)")
    print("2. CLI version only (dupes.exe)")
    print("3. Both versions")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    if choice == '1':
        build_gui_exe()
    elif choice == '2':
        build_cli_exe()
    elif choice == '3':
        build_gui_exe()
        build_cli_exe()
    else:
        print("Invalid choice. Exiting.")
        return
    
    print("\n" + "="*60)
    print("Build Complete!")
    print("="*60)
    print("\nYour executable(s) can be found in the 'dist' folder.")
    print("\nYou can distribute these .exe files to test in production.")
    print("They are standalone and don't require Python to be installed.")

if __name__ == '__main__':
    main()
