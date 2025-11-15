"""
Entry point for the Dupes GUI application.
This script properly handles imports when packaged as an executable.
"""
import sys
import os

# Add the parent directory to the Python path to allow imports
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = sys._MEIPASS
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))

# Add the application path to sys.path
sys.path.insert(0, application_path)

# Now import and run the GUI
from src.gui import main

if __name__ == '__main__':
    main()
