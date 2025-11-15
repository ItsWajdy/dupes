import flet as ft
import os
import shutil
import subprocess
import platform
from .dupes import Dupes
from .hash_helper import HashHelper
from .filters import DuplicateFilter, SizeFilter

class DupesGUI:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Dupes Finder"
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.dupes = Dupes()
        self.current_scan_path = None
        self.skip_confirmation = True
        self.pending_delete_path = None
        self.confirmation_overlay = None
        self.total_space_saved = 0  # Track space saved across deletions
        self.selected_items = set()  # Track selected items for bulk operations
        self.checkboxes = {}  # Map path -> checkbox reference
        self.current_duplicates = None  # Store current duplicates for operations
        self.scan_stop_requested = False  # Flag to stop scanning
        self.updating_ui = False  # Flag to prevent concurrent UI updates
        self.last_displayed_count = 0  # Track how many duplicates we've displayed
        self.max_initial_display = 100  # Maximum number of duplicate items to show initially
        
        # Keyboard navigation
        self.focused_index = -1  # Currently focused item index (-1 = none)
        self.selectable_items = []  # List of (path, row_control) tuples in order
        self.item_rows = {}  # Map path -> row control for highlighting
        
        # Filter and sort settings
        self.filter_file_type = 'all'
        self.filter_min_size = 0
        self.sort_by = 'size'
        self.search_query = ''
        self.raw_duplicates = None  # Store unfiltered duplicates
        self.hidden_groups = set()  # Track hidden groups by (item_type, hash_value)
        
        # Pre-scan options
        self.prescan_exclude_folders = ''
        self.prescan_file_types = ''
        self.prescan_min_size = ''
        self.prescan_scan_subfolders = True
        self.prescan_include_hidden = False

        self.setup_ui()
        
        # Setup keyboard event handler
        self.page.on_keyboard_event = self.on_keyboard_event

    def setup_ui(self):
        """Create and arrange the UI components."""
        self.dir_picker = ft.FilePicker(on_result=self.on_dir_picked)
        self.page.overlay.append(self.dir_picker)
        
        # FilePicker for selecting folders to exclude
        self.exclude_folder_picker = ft.FilePicker(on_result=self.on_exclude_folder_picked)
        self.page.overlay.append(self.exclude_folder_picker)
        
        # Pre-scan options controls
        self.exclude_folders_input = ft.TextField(
            label="Exclude folders (comma-separated)",
            hint_text="e.g., node_modules, .git, temp",
            width=300,
            on_change=self.on_prescan_option_change,
            data='exclude_folders',
            read_only=False,
        )
        
        # Button to browse for folders to exclude
        self.browse_exclude_button = ft.IconButton(
            icon="folder_open",
            tooltip="Browse for folder to exclude",
            on_click=self.on_browse_exclude_folder,
        )
        
        self.file_types_input = ft.TextField(
            label="File types (comma-separated)",
            hint_text="e.g., .jpg, .png, .mp4 (empty = all)",
            width=250,
            on_change=self.on_prescan_option_change,
            data='file_types',
        )
        
        self.prescan_min_size_input = ft.TextField(
            label="Min file size",
            hint_text="e.g., 1MB, 100KB",
            width=150,
            on_change=self.on_prescan_option_change,
            data='min_size',
        )
        
        self.scan_subfolders_switch = ft.Switch(
            label="Scan subfolders",
            value=True,
            on_change=self.on_prescan_option_change,
            data='scan_subfolders',
        )
        
        self.include_hidden_switch = ft.Switch(
            label="Include hidden files",
            value=False,
            on_change=self.on_prescan_option_change,
            data='include_hidden',
        )

        self.select_dir_button = ft.ElevatedButton(
            "Select Directory to Scan",
            icon="folder_open",
            on_click=self.on_select_dir_button_click,
            height=40,
        )

        self.start_scan_button = ft.ElevatedButton(
            "Start Scan",
            icon="play_arrow",
            on_click=self.on_start_scan_button_click,
            bgcolor="#4caf50",
            color="white",
            visible=False,
            height=40,
        )

        self.stop_scan_button = ft.ElevatedButton(
            "Stop Scan",
            icon="stop",
            on_click=self.stop_scan,
            bgcolor="#d32f2f",
            color="white",
            visible=False,
            height=40,
        )

        self.selected_dir_text = ft.Text("", size=12, weight=ft.FontWeight.BOLD)
        self.scan_status = ft.Text(size=12, selectable=True, expand=True)
        self.space_stats = ft.Text("", size=12, weight=ft.FontWeight.BOLD)
        self.space_saved = ft.Text("", size=12, color="green")
        
        self.progress_bar = ft.ProgressBar(visible=False)
        self.results_view = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=False)

        # Pre-scan options panel (collapsible)
        self.prescan_options = ft.Container(
            content=ft.Column([
                ft.Text("Pre-Scan Options", weight=ft.FontWeight.BOLD, size=14),
                ft.Row([
                    ft.Row([
                        self.exclude_folders_input,
                        self.browse_exclude_button,
                    ], spacing=5),
                    self.file_types_input,
                    self.prescan_min_size_input,
                ], spacing=10, wrap=True),
                ft.Row([
                    self.scan_subfolders_switch,
                    self.include_hidden_switch,
                ], spacing=20),
            ], spacing=8),
            bgcolor="#1e1e1e",
            padding=10,
            border_radius=ft.border_radius.all(5),
            border=ft.border.all(1, "#404040"),
            visible=True,
        )
        
        # Compact top bar with all controls in one row
        top_bar = ft.Container(
            content=ft.Column([
                ft.Row(
                    [
                        self.select_dir_button,
                        self.start_scan_button,
                        self.stop_scan_button,
                        ft.Container(width=10),  # Spacer
                        self.selected_dir_text,
                        self.scan_status,
                        ft.Container(width=10),  # Spacer
                        self.space_stats,
                        ft.Container(width=10),  # Spacer
                        self.space_saved,
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                self.progress_bar,
            ], spacing=5),
            bgcolor="#2d2d2d",
            padding=10,
            border_radius=ft.border_radius.all(5),
        )

        self.page.add(
            ft.Column(
                [
                    self.prescan_options,
                    top_bar,
                    ft.Container(
                        content=self.results_view,
                        border=ft.border.all(1, "outline"),
                        border_radius=ft.border_radius.all(5),
                        padding=10,
                        expand=True,
                    ),
                ],
                spacing=5,
                expand=True,
            )
        )

    def on_browse_exclude_folder(self, e):
        """Handle browse button click for selecting folders to exclude."""
        self.exclude_folder_picker.get_directory_path()
    
    def on_exclude_folder_picked(self, e: ft.FilePickerResultEvent):
        """Callback for when an exclude folder is selected."""
        if e.path:
            # Get the folder name from the full path
            folder_name = os.path.basename(e.path)
            
            # Add to the exclude folders text field
            current_value = self.exclude_folders_input.value.strip()
            if current_value:
                # Append with comma separator if there's already content
                new_value = f"{current_value}, {folder_name}"
            else:
                new_value = folder_name
            
            self.exclude_folders_input.value = new_value
            self.prescan_exclude_folders = new_value
            self.page.update()
    
    def on_prescan_option_change(self, e):
        """Handle pre-scan option changes."""
        if hasattr(e.control, 'data'):
            control_type = e.control.data
            
            if control_type == 'exclude_folders':
                self.prescan_exclude_folders = e.control.value
            elif control_type == 'file_types':
                self.prescan_file_types = e.control.value
            elif control_type == 'min_size':
                self.prescan_min_size = e.control.value
            elif control_type == 'scan_subfolders':
                self.prescan_scan_subfolders = e.control.value
            elif control_type == 'include_hidden':
                self.prescan_include_hidden = e.control.value
    
    def on_select_dir_button_click(self, e):
        """Handle Select Directory button click."""
        # Show pre-scan options when user clicks Select Directory
        self.prescan_options.visible = True
        self.page.update()
        self.dir_picker.get_directory_path()
    
    def on_confirmation_toggle_change(self, e):
        """Handle the confirmation toggle switch change."""
        self.skip_confirmation = e.control.value
        self.page.update()

    def stop_scan(self, e=None):
        """Stop the current scan."""
        self.scan_stop_requested = True
        self.scan_status.value = "Stopping scan..."
        self.page.update()
    
    def on_dir_picked(self, e: ft.FilePickerResultEvent):
        """Callback for when a directory is selected."""
        if e.path:
            # Store the selected path but don't start scanning yet
            self.current_scan_path = e.path
            
            # Update UI to show selection and enable Start Scan button
            self.selected_dir_text.value = f"📁 Selected: {e.path}"
            self.start_scan_button.visible = True
            self.prescan_options.visible = True  # Keep options visible for configuration
            self.page.update()
    
    def on_start_scan_button_click(self, e):
        """Handle Start Scan button click."""
        if self.current_scan_path:
            self.scan_directory(self.current_scan_path)

    def scan_directory(self, path: str):
        """Scan the selected directory for duplicates with progressive display."""
        import time
        import threading
        
        # Reset space statistics for new scan (before starting threads)
        self.total_space_saved = 0
        
        self.current_scan_path = path
        self.scan_status.value = f"Scanning: {path}..."
        self.space_stats.value = ""
        self.space_saved.value = ""
        self.progress_bar.visible = True
        self.scanning_active = True
        self.scan_stop_requested = False
        self.select_dir_button.visible = False
        self.start_scan_button.visible = False
        self.selected_dir_text.value = ""
        self.stop_scan_button.visible = True
        
        # Hide pre-scan options during scan
        self.prescan_options.visible = False
        self.page.update()

        # Clear all hashes from the pickle file to ensure a fresh scan
        HashHelper.clear_hashes()
        self.dupes = Dupes() # This will now load an empty hash dict
        self.dupes.stop_requested = False  # Initialize stop flag on dupes object
        
        start_time = time.time()
        
        def scan_thread():
            """Background scanning thread"""
            try:
                # Pass the stop flag to the scanner
                self.dupes.stop_requested = False
                
                # Parse pre-scan options
                exclude_folders = []
                if self.prescan_exclude_folders.strip():
                    exclude_folders = [f.strip() for f in self.prescan_exclude_folders.split(',')]
                
                file_types = None
                if self.prescan_file_types.strip():
                    file_types = [f.strip() for f in self.prescan_file_types.split(',')]
                
                min_size = 0
                if self.prescan_min_size.strip():
                    from .filters import SizeFilter
                    min_size = SizeFilter.parse_size_string(self.prescan_min_size)
                
                # Use optimized scanning that filters by file size first
                # include_dirs=False skips directory duplicate detection for much faster scanning
                self.dupes.scan_optimized(
                    path, 
                    verbose=False, 
                    include_dirs=False,
                    exclude_folders=exclude_folders,
                    file_types=file_types,
                    min_size=min_size,
                    scan_subfolders=self.prescan_scan_subfolders,
                    include_hidden=self.prescan_include_hidden
                )
                
                end_time = time.time()
                elapsed_time = end_time - start_time
                
                # Get final duplicate count
                duplicates = self.dupes.detect_duplicates(verbose=False)
                dup_count = sum(len(paths)-1 for paths in duplicates.get('files', {}).values())
                dup_count += sum(len(paths)-1 for paths in duplicates.get('dirs', {}).values())
                
                # Format time
                if elapsed_time >= 60:
                    minutes = int(elapsed_time // 60)
                    seconds = int(elapsed_time % 60)
                    time_str = f"{minutes}:{seconds:02d} minutes"
                else:
                    time_str = f"{elapsed_time:.2f} seconds"
                
                if self.scan_stop_requested:
                    self.scan_status.value = f"Scanned: {path} - Scan stopped by user (Found {dup_count} dupes in {time_str})"
                else:
                    self.scan_status.value = f"Scanned: {path} - (Found {dup_count} dupes in {time_str})"
                
                self.scanning_active = False
                self.progress_bar.visible = False
                self.stop_scan_button.visible = False
                self.select_dir_button.visible = True
                
                # Final update to show all duplicates
                self.display_duplicates(duplicates)
                self.page.update()
            except Exception as e:
                self.scan_status.value = f"Error during scan: {e}"
                self.scanning_active = False
                self.progress_bar.visible = False
                self.stop_scan_button.visible = False
                self.select_dir_button.visible = True
                self.page.update()
        
        def update_thread():
            """Thread that updates UI with found duplicates - throttled for performance"""
            update_count = 0
            last_ui_update = 0
            UI_UPDATE_INTERVAL = 2.0  # Update UI every 2 seconds (was 0.1 - 20x less frequent)
            
            while self.scanning_active:
                time.sleep(0.1)  # Check status frequently for responsive stop
                update_count += 1
                current_time = time.time()
                
                # Check if stop was requested
                if self.scan_stop_requested:
                    self.dupes.stop_requested = True
                    # Don't break immediately, let one more cycle complete
                
                # Only update UI at intervals (not every loop iteration)
                if current_time - last_ui_update >= UI_UPDATE_INTERVAL:
                    # Prevent concurrent UI updates
                    if self.updating_ui:
                        continue
                    
                    self.updating_ui = True
                    try:
                        # Get current duplicates found so far
                        duplicates = self.dupes.detect_duplicates(verbose=False)
                        
                        # Only update if we have duplicates
                        if duplicates.get('files') or duplicates.get('dirs'):
                            dup_count = sum(len(paths)-1 for paths in duplicates.get('files', {}).values())
                            if self.scan_stop_requested:
                                self.scan_status.value = f"Stopping scan..."
                            else:
                                self.scan_status.value = f"Scanning: {path}... (Found {dup_count} duplicates so far)"
                            
                            # Use optimized display during scanning
                            self.display_duplicates_optimized(duplicates)
                            self.page.update()
                            last_ui_update = current_time
                    finally:
                        self.updating_ui = False
        
        # Start both threads
        scanner = threading.Thread(target=scan_thread, daemon=True)
        updater = threading.Thread(target=update_thread, daemon=True)
        
        scanner.start()
        updater.start()

    def get_path_size(self, path: str) -> int:
        """Get the size of a file or directory in bytes."""
        try:
            if os.path.isfile(path):
                return os.path.getsize(path)
            elif os.path.isdir(path):
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        try:
                            total_size += os.path.getsize(filepath)
                        except (OSError, FileNotFoundError):
                            pass
                return total_size
        except (OSError, FileNotFoundError):
            return 0
        return 0
    
    def format_size(self, size_bytes: int) -> str:
        """Format bytes into human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def calculate_recoverable_space(self, duplicates: dict) -> int:
        """Calculate total space that can be recovered by deleting duplicates."""
        total_space = 0
        
        # For files, sum up sizes of all but the first (kept) file in each group
        for hash_value, paths in duplicates.get('files', {}).items():
            if len(paths) > 1:
                for path in paths[1:]:  # Skip the first (kept) file
                    total_space += self.get_path_size(path)
        
        # For directories, sum up sizes of all but the first (kept) directory in each group
        for hash_value, paths in duplicates.get('dirs', {}).items():
            if len(paths) > 1:
                for path in paths[1:]:  # Skip the first (kept) directory
                    total_space += self.get_path_size(path)
        
        return total_space

    def open_path(self, path: str):
        """Open a file or directory in the default application or file explorer."""
        try:
            if platform.system() == 'Windows':
                # On Windows, use os.startfile to open files/folders
                if os.path.isfile(path):
                    # Open file in default application
                    os.startfile(path)
                else:
                    # Open folder in file explorer
                    os.startfile(path)
            elif platform.system() == 'Darwin':  # macOS
                # Use 'open' command on macOS
                subprocess.run(['open', path], check=True)
            else:  # Linux and other Unix-like systems
                # Use 'xdg-open' on Linux
                subprocess.run(['xdg-open', path], check=True)
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Error opening {path}: {e}"),
                open=True
            )
            self.page.update()

    def is_smart_selectable(self, path: str) -> bool:
        """
        Determine if a path should be auto-selected based on smart criteria.
        Returns True if the path is in temp folders, downloads, or deeper nested paths.
        """
        path_lower = path.lower()
        
        # Common temp and temporary directories
        temp_indicators = ['temp', 'tmp', 'cache', 'download', 'downloads', 'recyclebin', 'recycle.bin', 'trash']
        
        # Check if path contains temp/download indicators
        for indicator in temp_indicators:
            if indicator in path_lower:
                return True
        
        return False
    
    def get_path_depth(self, path: str) -> int:
        """Get the depth of a path (number of directory separators)."""
        return path.count(os.sep)
    
    def on_checkbox_change(self, e, path: str):
        """Handle checkbox state changes."""
        if e.control.value:
            self.selected_items.add(path)
        else:
            self.selected_items.discard(path)
        self.page.update()
    
    def select_all_duplicates(self, e):
        """Select all duplicate items (not the kept ones)."""
        self.selected_items.clear()
        
        if not self.current_duplicates:
            return
        
        # Select all files except the first (kept) one in each group
        for hash_value, paths in self.current_duplicates.get('files', {}).items():
            if len(paths) > 1:
                for path in paths[1:]:
                    self.selected_items.add(path)
                    if path in self.checkboxes:
                        self.checkboxes[path].value = True
        
        # Select all directories except the first (kept) one in each group
        for hash_value, paths in self.current_duplicates.get('dirs', {}).items():
            if len(paths) > 1:
                for path in paths[1:]:
                    self.selected_items.add(path)
                    if path in self.checkboxes:
                        self.checkboxes[path].value = True
        
        self.page.update()
    
    def select_none(self, e):
        """Deselect all items."""
        self.selected_items.clear()
        
        for checkbox in self.checkboxes.values():
            checkbox.value = False
        
        self.page.update()
    
    def smart_select(self, e):
        """Smart select duplicates based on criteria: temp folders, downloads, deeper paths."""
        self.selected_items.clear()
        
        if not self.current_duplicates:
            return
        
        # Process files
        for hash_value, paths in self.current_duplicates.get('files', {}).items():
            if len(paths) > 1:
                deletable_paths = paths[1:]  # Skip the first (kept) file
                
                # Find paths with smart criteria
                smart_paths = [p for p in deletable_paths if self.is_smart_selectable(p)]
                
                # If no smart paths found, select deeper nested paths
                if not smart_paths:
                    path_depths = [(p, self.get_path_depth(p)) for p in deletable_paths]
                    max_depth = max(depth for _, depth in path_depths)
                    smart_paths = [p for p, depth in path_depths if depth == max_depth]
                
                # Select the smart paths
                for path in smart_paths:
                    self.selected_items.add(path)
                    if path in self.checkboxes:
                        self.checkboxes[path].value = True
        
        # Process directories
        for hash_value, paths in self.current_duplicates.get('dirs', {}).items():
            if len(paths) > 1:
                deletable_paths = paths[1:]  # Skip the first (kept) directory
                
                # Find paths with smart criteria
                smart_paths = [p for p in deletable_paths if self.is_smart_selectable(p)]
                
                # If no smart paths found, select deeper nested paths
                if not smart_paths:
                    path_depths = [(p, self.get_path_depth(p)) for p in deletable_paths]
                    max_depth = max(depth for _, depth in path_depths)
                    smart_paths = [p for p, depth in path_depths if depth == max_depth]
                
                # Select the smart paths
                for path in smart_paths:
                    self.selected_items.add(path)
                    if path in self.checkboxes:
                        self.checkboxes[path].value = True
        
        self.page.update()
    
    def delete_selected(self, e):
        """Delete all selected items."""
        if not self.selected_items:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("No items selected for deletion."),
                open=True
            )
            self.page.update()
            return
        
        # Confirmation for bulk delete
        if not self.skip_confirmation:
            self.show_bulk_delete_confirmation()
        else:
            self.execute_bulk_delete()
    
    def execute_bulk_delete(self):
        """Execute bulk deletion of selected items."""
        deleted_count = 0
        total_size = 0
        failed_items = []
        
        items_to_delete = list(self.selected_items)
        
        for path in items_to_delete:
            try:
                size = self.get_path_size(path)
                
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    continue
                
                deleted_count += 1
                total_size += size
                self.total_space_saved += size
                self.dupes.remove_path(path)
                
            except Exception as e:
                failed_items.append(f"{path}: {str(e)}")
        
        # Clear selection
        self.selected_items.clear()
        self.checkboxes.clear()
        
        # Show result
        message = f"Successfully deleted {deleted_count} item(s) - Freed: {self.format_size(total_size)}"
        if failed_items:
            message += f"\n\nFailed to delete {len(failed_items)} item(s)"
        
        self.page.snack_bar = ft.SnackBar(
            ft.Text(message),
            open=True
        )
        
        # Refresh the view
        duplicates = self.dupes.detect_duplicates()
        self.display_duplicates(duplicates)
        self.page.update()
    
    def hide_group(self, hash_value: str, item_type: str):
        """Hide a duplicate group from the list."""
        self.hidden_groups.add((item_type, hash_value))
        
        # Show notification
        self.page.snack_bar = ft.SnackBar(
            ft.Text(f"Group hidden. {len(self.hidden_groups)} group(s) hidden total."),
            open=True
        )
        
        # Refresh the display
        if self.current_duplicates:
            self.display_duplicates(self.current_duplicates, skip_filter=True)
    
    def unhide_all_groups(self, e=None):
        """Unhide all hidden groups."""
        count = len(self.hidden_groups)
        self.hidden_groups.clear()
        
        # Show notification
        self.page.snack_bar = ft.SnackBar(
            ft.Text(f"All {count} hidden group(s) have been unhidden."),
            open=True
        )
        
        # Refresh the display
        if self.current_duplicates:
            self.display_duplicates(self.current_duplicates, skip_filter=True)
    
    def delete_group(self, hash_value: str, item_type: str):
        """Delete all duplicates in a specific group (keeping the first one)."""
        if not self.current_duplicates:
            return
        
        paths = self.current_duplicates.get(item_type, {}).get(hash_value, [])
        if len(paths) <= 1:
            return
        
        # Delete all except the first (kept) one
        deletable_paths = paths[1:]
        
        if not self.skip_confirmation:
            self.show_group_delete_confirmation(deletable_paths, hash_value)
        else:
            self.execute_group_delete(deletable_paths)
    
    def execute_group_delete(self, paths_to_delete):
        """Execute deletion of all items in a group."""
        deleted_count = 0
        total_size = 0
        failed_items = []
        
        for path in paths_to_delete:
            try:
                size = self.get_path_size(path)
                
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    continue
                
                deleted_count += 1
                total_size += size
                self.total_space_saved += size
                self.dupes.remove_path(path)
                
            except Exception as e:
                failed_items.append(f"{path}: {str(e)}")
        
        # Clear selection
        self.selected_items.clear()
        self.checkboxes.clear()
        
        # Show result
        message = f"Successfully deleted {deleted_count} item(s) from group - Freed: {self.format_size(total_size)}"
        if failed_items:
            message += f"\n\nFailed to delete {len(failed_items)} item(s)"
        
        self.page.snack_bar = ft.SnackBar(
            ft.Text(message),
            open=True
        )
        
        # Refresh the view
        duplicates = self.dupes.detect_duplicates()
        self.display_duplicates(duplicates)
        self.page.update()

    def apply_filters(self):
        """Apply current filters and sorting to raw duplicates."""
        if not self.raw_duplicates:
            return {'files': {}, 'dirs': {}}
        
        # Apply filters using DuplicateFilter
        filtered = DuplicateFilter.filter_duplicates(
            self.raw_duplicates,
            file_type=self.filter_file_type,
            min_size=self.filter_min_size,
            sort_by=self.sort_by,
            reverse_sort=True,  # Largest first for size
            search_query=self.search_query
        )
        
        # Also sort the groups by size (largest groups first)
        filtered = DuplicateFilter.sort_duplicate_groups(filtered, sort_by='group_size')
        
        return filtered
    
    def on_filter_change(self, e):
        """Handle filter/sort control changes."""
        # Update filter settings based on control
        if hasattr(e.control, 'data'):
            control_type = e.control.data
            
            if control_type == 'file_type':
                self.filter_file_type = e.control.value
            elif control_type == 'sort_by':
                self.sort_by = e.control.value
            elif control_type == 'min_size':
                # Parse the size input
                size_text = e.control.value.strip()
                if size_text:
                    self.filter_min_size = SizeFilter.parse_size_string(size_text)
                else:
                    self.filter_min_size = 0
            elif control_type == 'search':
                self.search_query = e.control.value
        
        # Re-apply filters and display
        if self.raw_duplicates:
            filtered = self.apply_filters()
            self.display_duplicates(filtered, skip_filter=True)
    
    def display_duplicates_optimized(self, duplicates: dict):
        """
        Optimized display for during-scan updates. Uses throttled update frequency
        but shows full interactive results so user can delete while scanning.
        """
        # Just use the regular display method - the optimization is in the update frequency (2s instead of 0.1s)
        self.display_duplicates(duplicates)
    
    def display_duplicates(self, duplicates: dict, skip_filter: bool = False):
        """Display the found duplicates in the results view."""
        # Store raw duplicates if this is a new scan
        if not skip_filter:
            self.raw_duplicates = duplicates
            duplicates = self.apply_filters()
        
        self.results_view.controls.clear()
        self.checkboxes.clear()
        self.selected_items.clear()
        self.current_duplicates = duplicates
        
        # Reset keyboard navigation
        self.focused_index = -1
        self.selectable_items.clear()
        self.item_rows.clear()
        
        if not duplicates.get('files') and not duplicates.get('dirs'):
            self.results_view.controls.append(ft.Text("No duplicates found."))
            self.space_stats.value = ""
            self.space_saved.value = ""
        else:
            # Calculate and display recoverable space
            recoverable_space = self.calculate_recoverable_space(duplicates)
            self.space_stats.value = f"💾 Recoverable: {self.format_size(recoverable_space)}"
            if self.total_space_saved > 0:
                self.space_saved.value = f"✅ Saved: {self.format_size(self.total_space_saved)}"
            else:
                self.space_saved.value = ""
            
            # Compact control bar at top of results
            control_bar = ft.Container(
                content=ft.Column([
                    # First row: Filter controls
                    ft.Row([
                        ft.Dropdown(
                            label="File Type",
                            value=self.filter_file_type,
                            options=[
                                ft.dropdown.Option("all", "All Files"),
                                ft.dropdown.Option("images", "Images"),
                                ft.dropdown.Option("videos", "Videos"),
                                ft.dropdown.Option("documents", "Documents"),
                                ft.dropdown.Option("audio", "Audio"),
                                ft.dropdown.Option("archives", "Archives"),
                                ft.dropdown.Option("code", "Code"),
                            ],
                            width=150,
                            on_change=self.on_filter_change,
                            data='file_type',
                        ),
                        ft.Dropdown(
                            label="Sort By",
                            value=self.sort_by,
                            options=[
                                ft.dropdown.Option("size", "Size (Largest First)"),
                                ft.dropdown.Option("name", "Name"),
                                ft.dropdown.Option("date", "Date Modified"),
                                ft.dropdown.Option("path", "Path"),
                            ],
                            width=180,
                            on_change=self.on_filter_change,
                            data='sort_by',
                        ),
                        ft.TextField(
                            label="Min Size (e.g., 10MB, 1GB)",
                            width=180,
                            on_submit=self.on_filter_change,
                            on_blur=self.on_filter_change,
                            data='min_size',
                        ),
                        ft.TextField(
                            label="Search in paths",
                            width=200,
                            on_change=self.on_filter_change,
                            data='search',
                        ),
                    ], spacing=10, wrap=True, alignment=ft.MainAxisAlignment.START),
                    # Second row: Bulk operation buttons with skip toggle on the right
                    ft.Row([
                        ft.ElevatedButton(
                            "Select All Duplicates",
                            icon="select_all",
                            on_click=self.select_all_duplicates,
                            bgcolor="#1976d2",
                            color="white",
                            height=35,
                        ),
                        ft.ElevatedButton(
                            "Select None",
                            icon="deselect",
                            on_click=self.select_none,
                            bgcolor="#616161",
                            color="white",
                            height=35,
                        ),
                        ft.ElevatedButton(
                            "Smart Select",
                            icon="auto_awesome",
                            on_click=self.smart_select,
                            bgcolor="#7b1fa2",
                            color="white",
                            height=35,
                            tooltip="Auto-select items in temp/download folders or deeper paths",
                        ),
                        ft.ElevatedButton(
                            "Delete Selected",
                            icon="delete_sweep",
                            on_click=self.delete_selected,
                            bgcolor="#d32f2f",
                            color="white",
                            height=35,
                        ),
                        ft.ElevatedButton(
                            f"Unhide All ({len(self.hidden_groups)})" if self.hidden_groups else "Unhide All",
                            icon="visibility",
                            on_click=self.unhide_all_groups,
                            bgcolor="#00695c",
                            color="white",
                            height=35,
                            tooltip="Show all hidden groups",
                            visible=len(self.hidden_groups) > 0,
                        ),
                        ft.Container(expand=True),  # Spacer to push switch to the right
                        ft.Switch(
                            label="Skip delete confirm",
                            value=self.skip_confirmation,
                            on_change=self.on_confirmation_toggle_change,
                        ),
                    ], spacing=10, alignment=ft.MainAxisAlignment.START),
                ], spacing=10),
                bgcolor="#2d2d2d",
                border_radius=ft.border_radius.all(5),
                padding=10,
            )
            
            self.results_view.controls.append(control_bar)
            
            # Display file duplicates
            for hash_value, paths in duplicates.get('files', {}).items():
                # Skip hidden groups
                if ('files', hash_value) in self.hidden_groups:
                    continue
                
                # Calculate group size
                group_size = sum(self.get_path_size(p) for p in paths)
                
                # Group header with "Delete Group" and "Hide Group" buttons
                group_header = ft.Row(
                    [
                        ft.Text(
                            f"Duplicate files (hash: {hash_value[:8]}...) - Group Size: {self.format_size(group_size)}",
                            weight=ft.FontWeight.BOLD,
                            expand=True,
                        ),
                        ft.ElevatedButton(
                            "Hide Group",
                            icon="visibility_off",
                            on_click=lambda e, h=hash_value: self.hide_group(h, 'files'),
                            bgcolor="#616161",
                            color="white",
                            height=35,
                        ),
                        ft.ElevatedButton(
                            "Delete All in Group",
                            icon="delete_forever",
                            on_click=lambda e, h=hash_value: self.delete_group(h, 'files'),
                            bgcolor="#f57c00",
                            color="white",
                            height=35,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                
                self.results_view.controls.append(group_header)
                
                if not paths: continue
                first_path, *deletable_paths = paths
                
                # Make the kept path clickable
                def make_open_handler(file_path):
                    return lambda e: self.open_path(file_path)
                
                kept_size = self.get_path_size(first_path)
                self.results_view.controls.append(
                    ft.Row([
                        ft.Text("  [Kept] "),
                        ft.TextButton(
                            text=first_path,
                            on_click=make_open_handler(first_path),
                            tooltip="Click to open file",
                            style=ft.ButtonStyle(padding=0),
                        ),
                        ft.Text(f" ({self.format_size(kept_size)})", color="gray", size=12),
                    ])
                )
                
                for path in deletable_paths:
                    def make_checkbox_handler(file_path):
                        return lambda e: self.on_checkbox_change(e, file_path)
                    
                    def make_delete_handler(file_path):
                        return lambda e: self.confirm_delete(file_path)
                    
                    def make_open_handler(file_path):
                        return lambda e: self.open_path(file_path)
                    
                    file_size = self.get_path_size(path)
                    
                    # Create checkbox and store reference
                    checkbox = ft.Checkbox(
                        value=False,
                        on_change=make_checkbox_handler(path),
                    )
                    self.checkboxes[path] = checkbox
                    
                    # Create row for this item
                    item_row = ft.Row(
                        [
                            checkbox,
                            ft.TextButton(
                                text=path,
                                on_click=make_open_handler(path),
                                tooltip="Click to open file",
                                expand=True,
                                style=ft.ButtonStyle(padding=0),
                            ),
                            ft.Text(f"{self.format_size(file_size)}", color="gray", size=12),
                            ft.IconButton(
                                icon="delete",
                                icon_color="red",
                                on_click=make_delete_handler(path),
                                tooltip="Delete this file",
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    )
                    
                    # Track for keyboard navigation
                    self.selectable_items.append((path, item_row))
                    self.item_rows[path] = item_row
                    
                    self.results_view.controls.append(item_row)

            # Display directory duplicates
            for hash_value, paths in duplicates.get('dirs', {}).items():
                # Skip hidden groups
                if ('dirs', hash_value) in self.hidden_groups:
                    continue
                
                # Calculate group size
                group_size = sum(self.get_path_size(p) for p in paths)
                
                # Group header with "Delete Group" and "Hide Group" buttons
                group_header = ft.Row(
                    [
                        ft.Text(
                            f"Duplicate directories (hash: {hash_value[:8]}...) - Group Size: {self.format_size(group_size)}",
                            weight=ft.FontWeight.BOLD,
                            expand=True,
                        ),
                        ft.ElevatedButton(
                            "Hide Group",
                            icon="visibility_off",
                            on_click=lambda e, h=hash_value: self.hide_group(h, 'dirs'),
                            bgcolor="#616161",
                            color="white",
                            height=35,
                        ),
                        ft.ElevatedButton(
                            "Delete All in Group",
                            icon="delete_forever",
                            on_click=lambda e, h=hash_value: self.delete_group(h, 'dirs'),
                            bgcolor="#f57c00",
                            color="white",
                            height=35,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                
                self.results_view.controls.append(
                    ft.Container(
                        content=group_header,
                        margin=ft.margin.only(top=10),
                    )
                )
                
                if not paths: continue
                first_path, *deletable_paths = paths
                
                # Make the kept path clickable
                def make_open_handler(dir_path):
                    return lambda e: self.open_path(dir_path)
                
                kept_size = self.get_path_size(first_path)
                self.results_view.controls.append(
                    ft.Row([
                        ft.Text("  [Kept] "),
                        ft.TextButton(
                            text=first_path,
                            on_click=make_open_handler(first_path),
                            tooltip="Click to open directory",
                            style=ft.ButtonStyle(padding=0),
                        ),
                        ft.Text(f" ({self.format_size(kept_size)})", color="gray", size=12),
                    ])
                )
                
                for path in deletable_paths:
                    def make_checkbox_handler(dir_path):
                        return lambda e: self.on_checkbox_change(e, dir_path)
                    
                    def make_delete_handler(dir_path):
                        return lambda e: self.confirm_delete(dir_path)
                    
                    def make_open_handler(dir_path):
                        return lambda e: self.open_path(dir_path)
                    
                    dir_size = self.get_path_size(path)
                    
                    # Create checkbox and store reference
                    checkbox = ft.Checkbox(
                        value=False,
                        on_change=make_checkbox_handler(path),
                    )
                    self.checkboxes[path] = checkbox
                    
                    # Create row for this item
                    item_row = ft.Row(
                        [
                            checkbox,
                            ft.TextButton(
                                text=path,
                                on_click=make_open_handler(path),
                                tooltip="Click to open directory",
                                expand=True,
                                style=ft.ButtonStyle(padding=0),
                            ),
                            ft.Text(f"{self.format_size(dir_size)}", color="gray", size=12),
                            ft.IconButton(
                                icon="delete",
                                icon_color="red",
                                on_click=make_delete_handler(path),
                                tooltip="Delete this directory",
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    )
                    
                    # Track for keyboard navigation
                    self.selectable_items.append((path, item_row))
                    self.item_rows[path] = item_row
                    
                    self.results_view.controls.append(item_row)
        self.page.update()

    def confirm_delete(self, path_to_delete: str):
        """Show a confirmation dialog before deleting a file or directory."""
        if self.skip_confirmation:
            # Skip dialog and delete directly
            self.delete_path(path_to_delete)
            return

        self.pending_delete_path = path_to_delete
        self.show_confirmation_overlay()

    def show_confirmation_overlay(self):
        """Show a custom confirmation overlay."""
        def on_cancel(e):
            self.hide_confirmation_overlay()

        def on_confirm(e):
            self.delete_path(self.pending_delete_path)
            self.hide_confirmation_overlay()

        # Create the confirmation overlay
        self.confirmation_overlay = ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Confirm Deletion",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Divider(),
                            ft.Text(
                                f"Are you sure you want to delete this item?\n\n{os.path.basename(self.pending_delete_path)}\n\nThis action cannot be undone.",
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Row(
                                [
                                    ft.ElevatedButton(
                                        "Cancel",
                                        on_click=on_cancel,
                                        bgcolor="#666666",
                                        color="white",
                                    ),
                                    ft.ElevatedButton(
                                        "Delete",
                                        on_click=on_confirm,
                                        bgcolor="#d32f2f",
                                        color="white",
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        tight=True,
                    ),
                    padding=20,
                    width=400,
                ),
                elevation=10,
            ),
            bgcolor="rgba(0, 0, 0, 0.7)",
            alignment=ft.alignment.center,
            width=self.page.width,
            height=self.page.height,
        )

        self.page.overlay.append(self.confirmation_overlay)
        self.page.update()

    def hide_confirmation_overlay(self):
        """Hide the confirmation overlay."""
        if self.confirmation_overlay in self.page.overlay:
            self.page.overlay.remove(self.confirmation_overlay)
            self.confirmation_overlay = None
            self.pending_delete_path = None
            self.page.update()
    
    def show_bulk_delete_confirmation(self):
        """Show confirmation dialog for bulk deletion."""
        def on_cancel(e):
            self.hide_confirmation_overlay()

        def on_confirm(e):
            self.execute_bulk_delete()
            self.hide_confirmation_overlay()

        num_items = len(self.selected_items)
        total_size = sum(self.get_path_size(p) for p in self.selected_items)
        
        # Create the confirmation overlay
        self.confirmation_overlay = ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Confirm Bulk Deletion",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Divider(),
                            ft.Text(
                                f"Are you sure you want to delete {num_items} selected item(s)?\n\nTotal size: {self.format_size(total_size)}\n\nThis action cannot be undone.",
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Row(
                                [
                                    ft.ElevatedButton(
                                        "Cancel",
                                        on_click=on_cancel,
                                        bgcolor="#666666",
                                        color="white",
                                    ),
                                    ft.ElevatedButton(
                                        "Delete All",
                                        on_click=on_confirm,
                                        bgcolor="#d32f2f",
                                        color="white",
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        tight=True,
                    ),
                    padding=20,
                    width=450,
                ),
                elevation=10,
            ),
            bgcolor="rgba(0, 0, 0, 0.7)",
            alignment=ft.alignment.center,
            width=self.page.width,
            height=self.page.height,
        )

        self.page.overlay.append(self.confirmation_overlay)
        self.page.update()
    
    def show_group_delete_confirmation(self, paths_to_delete, hash_value):
        """Show confirmation dialog for group deletion."""
        def on_cancel(e):
            self.hide_confirmation_overlay()

        def on_confirm(e):
            self.execute_group_delete(paths_to_delete)
            self.hide_confirmation_overlay()

        num_items = len(paths_to_delete)
        total_size = sum(self.get_path_size(p) for p in paths_to_delete)
        
        # Create the confirmation overlay
        self.confirmation_overlay = ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Confirm Group Deletion",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Divider(),
                            ft.Text(
                                f"Are you sure you want to delete all {num_items} duplicate(s) in this group?\n\nHash: {hash_value[:16]}...\nTotal size: {self.format_size(total_size)}\n\nThe first item will be kept. This action cannot be undone.",
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Row(
                                [
                                    ft.ElevatedButton(
                                        "Cancel",
                                        on_click=on_cancel,
                                        bgcolor="#666666",
                                        color="white",
                                    ),
                                    ft.ElevatedButton(
                                        "Delete Group",
                                        on_click=on_confirm,
                                        bgcolor="#d32f2f",
                                        color="white",
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        tight=True,
                    ),
                    padding=20,
                    width=450,
                ),
                elevation=10,
            ),
            bgcolor="rgba(0, 0, 0, 0.7)",
            alignment=ft.alignment.center,
            width=self.page.width,
            height=self.page.height,
        )

        self.page.overlay.append(self.confirmation_overlay)
        self.page.update()

    def delete_path(self, path_to_delete: str):
        """Delete a file or directory and refresh the view."""
        try:
            # Calculate size before deletion
            size_deleted = self.get_path_size(path_to_delete)
            
            if os.path.isfile(path_to_delete):
                os.remove(path_to_delete)
            elif os.path.isdir(path_to_delete):
                shutil.rmtree(path_to_delete)
            else:
                return
            
            # Update space saved
            self.total_space_saved += size_deleted
            
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Successfully deleted {path_to_delete} - Freed: {self.format_size(size_deleted)}"),
                open=True
            )
            
            # Update the internal state and refresh the UI
            self.dupes.remove_path(path_to_delete)
            duplicates = self.dupes.detect_duplicates()
            self.display_duplicates(duplicates)
            self.page.update()

        except Exception as e:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error deleting {path_to_delete}: {e}"), open=True)
            self.page.update()
    
    def on_keyboard_event(self, e: ft.KeyboardEvent):
        """Handle keyboard events for navigation and actions."""
        # Don't handle keyboard events when overlay is visible
        if self.confirmation_overlay:
            return
        
        # Don't handle if no items to navigate
        if not self.selectable_items:
            return
        
        # Arrow Down - Navigate to next item
        if e.key == "Arrow Down" and not e.ctrl and not e.shift and not e.alt:
            self.navigate_down()
        
        # Arrow Up - Navigate to previous item
        elif e.key == "Arrow Up" and not e.ctrl and not e.shift and not e.alt:
            self.navigate_up()
        
        # Space - Toggle selection of focused item
        elif e.key == " " and not e.ctrl and not e.shift and not e.alt:
            self.toggle_focused_item()
        
        # Delete - Delete focused item or selected items
        elif e.key == "Delete" and not e.ctrl and not e.shift and not e.alt:
            self.delete_focused_or_selected()
        
        # Ctrl+A - Select all duplicates
        elif e.key == "A" and e.ctrl and not e.shift and not e.alt:
            self.select_all_duplicates(None)
    
    def navigate_down(self):
        """Navigate to the next item in the list."""
        if not self.selectable_items:
            return
        
        # Clear previous highlight
        if self.focused_index >= 0 and self.focused_index < len(self.selectable_items):
            path, row = self.selectable_items[self.focused_index]
            row.bgcolor = None
        
        # Move to next item
        self.focused_index = min(self.focused_index + 1, len(self.selectable_items) - 1)
        
        # Highlight new focused item
        if self.focused_index >= 0 and self.focused_index < len(self.selectable_items):
            path, row = self.selectable_items[self.focused_index]
            row.bgcolor = "#404040"
            
            # Scroll to make item visible (approximate)
            # Note: Flet doesn't have precise scroll control, but we can try to keep it in view
            
        self.page.update()
    
    def navigate_up(self):
        """Navigate to the previous item in the list."""
        if not self.selectable_items:
            return
        
        # Clear previous highlight
        if self.focused_index >= 0 and self.focused_index < len(self.selectable_items):
            path, row = self.selectable_items[self.focused_index]
            row.bgcolor = None
        
        # Move to previous item
        if self.focused_index == -1:
            self.focused_index = len(self.selectable_items) - 1
        else:
            self.focused_index = max(self.focused_index - 1, 0)
        
        # Highlight new focused item
        if self.focused_index >= 0 and self.focused_index < len(self.selectable_items):
            path, row = self.selectable_items[self.focused_index]
            row.bgcolor = "#404040"
        
        self.page.update()
    
    def toggle_focused_item(self):
        """Toggle selection of the currently focused item."""
        if self.focused_index < 0 or self.focused_index >= len(self.selectable_items):
            return
        
        path, row = self.selectable_items[self.focused_index]
        
        if path in self.checkboxes:
            checkbox = self.checkboxes[path]
            checkbox.value = not checkbox.value
            
            # Update selected_items set
            if checkbox.value:
                self.selected_items.add(path)
            else:
                self.selected_items.discard(path)
            
            self.page.update()
    
    def delete_focused_or_selected(self):
        """Delete the focused item, or all selected items if any are selected."""
        # If items are selected, delete all selected
        if self.selected_items:
            self.delete_selected(None)
        # Otherwise, delete the focused item
        elif self.focused_index >= 0 and self.focused_index < len(self.selectable_items):
            path, row = self.selectable_items[self.focused_index]
            self.confirm_delete(path)

def main():
    ft.app(target=lambda page: DupesGUI(page))

if __name__ == "__main__":
    main()
