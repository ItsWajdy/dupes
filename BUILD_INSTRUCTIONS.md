# Building Executable for Production Testing

This guide explains how to export your Dupes application as a standalone .exe file for testing in production on Windows.

## Table of Contents
1. [Quick Start (Recommended)](#quick-start-recommended)
2. [Method 1: Using Flet's Built-in Packaging](#method-1-using-flets-built-in-packaging-gui-only)
3. [Method 2: Using the Build Script](#method-2-using-the-build-script)
4. [Method 3: Manual PyInstaller](#method-3-manual-pyinstaller)
5. [Testing Your Executable](#testing-your-executable)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start (Recommended)

### For GUI Application

The **easiest method** is to use Flet's built-in packaging tool:

```bash
# Install flet if not already installed
pip install flet

# Build the GUI executable (recommended for GUI apps)
flet pack src/gui.py --name "DupesFinder" --icon NONE
```

This will create a standalone executable in the `dist` folder.

### For CLI Application

Use the provided build script:

```bash
python build_exe.py
```

Then select option 2 for CLI only.

---

## Method 1: Using Flet's Built-in Packaging (GUI Only)

Flet has a built-in `flet pack` command that's optimized for Flet applications.

### Step 1: Install Flet
```bash
pip install flet
```

### Step 2: Build the Executable
```bash
flet pack run_gui.py --name "DupesFinder" --icon NONE
```

**Note:** We use `run_gui.py` instead of `src/gui.py` to handle relative imports properly when packaged.

#### Optional Parameters:
- `--name "YourAppName"`: Set the executable name
- `--icon path/to/icon.ico`: Add a custom icon
- `--onefile`: Package everything into a single .exe file (default)
- `--add-data "src;src"`: Include additional data files

### Step 3: Find Your Executable
Your executable will be in: `dist/DupesFinder.exe`

---

## Method 2: Using the Build Script

I've created a convenient build script that handles both GUI and CLI versions.

### Step 1: Run the Build Script
```bash
python build_exe.py
```

### Step 2: Choose Your Build Option
The script will prompt you:
```
What would you like to build?
1. GUI version only (DupesFinder.exe)
2. CLI version only (dupes.exe)
3. Both versions

Enter your choice (1/2/3):
```

### Step 3: Wait for Build to Complete
The script will:
- Install PyInstaller if needed
- Clean previous builds
- Build your selected executable(s)
- Report success and location

### Step 4: Find Your Executables
- GUI version: `dist/DupesFinder.exe`
- CLI version: `dist/dupes.exe`

---

## Method 3: Manual PyInstaller

If you prefer manual control, you can use PyInstaller directly.

### Step 1: Install PyInstaller
```bash
pip install pyinstaller
```

### Step 2: Build GUI Version
```bash
pyinstaller --name=DupesFinder --onefile --windowed --add-data "src;src" --hidden-import flet --collect-all flet src/gui.py
```

### Step 3: Build CLI Version
```bash
pyinstaller --name=dupes --onefile --console --add-data "src;src" --hidden-import click src/cli.py
```

### PyInstaller Options Explained:
- `--name`: Name of the output executable
- `--onefile`: Bundle everything into a single .exe file
- `--windowed`: No console window (GUI only)
- `--console`: Keep console window (CLI only)
- `--add-data "src;src"`: Include the src directory
- `--hidden-import`: Include modules that PyInstaller might miss
- `--collect-all flet`: Include all Flet dependencies
- `--icon=path/to/icon.ico`: Add a custom icon (optional)

---

## Testing Your Executable

### GUI Version (DupesFinder.exe)

1. **Navigate to the dist folder:**
   ```bash
   cd dist
   ```

2. **Run the executable:**
   ```bash
   DupesFinder.exe
   ```
   Or simply double-click `DupesFinder.exe` in File Explorer.

3. **Test functionality:**
   - Click "Select Directory"
   - Choose a folder to scan
   - Verify duplicates are found
   - Test deletion features
   - Test filters and sorting

### CLI Version (dupes.exe)

1. **Navigate to the dist folder:**
   ```bash
   cd dist
   ```

2. **Test help command:**
   ```bash
   dupes.exe --help
   ```

3. **Scan a directory:**
   ```bash
   dupes.exe process-dir C:\path\to\test\folder
   ```

4. **Detect duplicates:**
   ```bash
   dupes.exe detect-duplicates
   ```

5. **Delete duplicates interactively:**
   ```bash
   dupes.exe delete-duplicates --interactive
   ```

---

## Distributing Your Executable

### What Gets Packaged
The .exe file includes:
- ✅ Python interpreter
- ✅ All your code (src/ directory)
- ✅ All dependencies (flet, click, etc.)
- ✅ Required system libraries

### What's NOT Needed on Target Machine
- ❌ Python installation
- ❌ pip packages
- ❌ Source code

### Distribution Checklist
1. ✅ Copy the .exe file from the `dist` folder
2. ✅ Test it on a clean machine without Python
3. ✅ Include a README with usage instructions
4. ✅ Note: First run may take longer (extracting bundled files)

---

## Troubleshooting

### Issue: "PyInstaller not found"
**Solution:** Install PyInstaller
```bash
pip install pyinstaller
```

### Issue: "ModuleNotFoundError" when running .exe
**Solution:** Add the missing module as a hidden import:
```bash
pyinstaller --hidden-import module_name ...
```

### Issue: Antivirus flags the .exe as suspicious
**Solution:** This is common with PyInstaller. Options:
1. Add an exception in your antivirus
2. Sign the executable with a code signing certificate
3. Distribute the source code for users to build themselves

### Issue: .exe file is too large
**Solution:** 
- Flet apps are typically 50-100 MB due to browser dependencies
- This is normal and expected
- Consider using UPX compression (advanced):
  ```bash
  pyinstaller --upx-dir=/path/to/upx ...
  ```

### Issue: "Failed to execute script"
**Solution:** 
1. Test in console mode first (remove `--windowed`)
2. Check for missing data files
3. Verify all imports are included
4. Check the error logs in `%TEMP%` folder

### Issue: GUI doesn't show/starts slowly
**Solution:**
- First run is slower (extracting files)
- Subsequent runs are faster
- Check Windows Defender isn't scanning it repeatedly

### Issue: Hash pickle file location errors
**Solution:** The app creates a pickle file. In production:
- It will be created in the user's temp directory
- Location: `%TEMP%\dupes_hashes.pkl`
- This is handled automatically

---

## Advanced: Customizing the Build

### Adding a Custom Icon
1. Create or download a `.ico` file
2. Update the build command:
   ```bash
   flet pack src/gui.py --name "DupesFinder" --icon path/to/icon.ico
   ```

### Reducing File Size
```bash
pyinstaller --onefile --windowed --strip --noupx src/gui.py
```

### Including Additional Files
```bash
pyinstaller --add-data "config.json;." --add-data "assets;assets" src/gui.py
```

### Creating an Installer (Advanced)
After building the .exe, you can use tools like:
- **Inno Setup** (free, recommended)
- **NSIS** (free)
- **InstallForge** (free)
- **Advanced Installer** (paid)

---

## Recommended Workflow

### For Development Testing:
```bash
# Quick build with Flet
flet pack src/gui.py --name "DupesFinder"
```

### For Production Release:
```bash
# Use the build script for both versions
python build_exe.py
# Choose option 3 (both versions)
```

### After Building:
1. Test both executables thoroughly
2. Test on a machine without Python
3. Create a release package with:
   - DupesFinder.exe (GUI)
   - dupes.exe (CLI) 
   - README.md
   - LICENSE (if applicable)

---

## Quick Reference Commands

```bash
# Install dependencies
pip install pyinstaller flet

# Quick GUI build (Flet)
flet pack src/gui.py --name "DupesFinder"

# Quick build (Script)
python build_exe.py

# Manual GUI build
pyinstaller --name=DupesFinder --onefile --windowed --collect-all flet src/gui.py

# Manual CLI build
pyinstaller --name=dupes --onefile --console src/cli.py

# Test the executable
cd dist
DupesFinder.exe
```

---

## Next Steps

After successfully building your executable:

1. ✅ Test thoroughly on your development machine
2. ✅ Test on a clean Windows machine without Python
3. ✅ Test with various directory structures
4. ✅ Verify all features work (scan, delete, filters)
5. ✅ Package for distribution with documentation
6. ✅ Consider code signing for production releases

---

## Support

For issues with:
- **PyInstaller:** https://pyinstaller.org/en/stable/
- **Flet packaging:** https://flet.dev/docs/guides/python/packaging-desktop-app
- **This project:** Check the README.md or create an issue on GitHub

---

**Note:** The first time you run the executable, it may take a few seconds to start as it extracts bundled files. Subsequent runs will be faster.
