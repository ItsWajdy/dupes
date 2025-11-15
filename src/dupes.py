import os
from collections import defaultdict
from .files_helper import FilesHelper
from .hash_helper import HashHelper

class Dupes:
    def __init__(self, verbose: bool = False):
        self.hashes = HashHelper.load_hashes(verbose=verbose)
        self._pending_saves = False
        self._file_size_cache = {}  # Cache file sizes for optimization
        self.stop_requested = False  # Flag to stop scanning

    def reursive_hash(self, path: str, verbose: bool = False, save_on_complete: bool = True) -> str:
        """
        Recursively hash a file or directory.

        Args:
            path (str): The path to the file or directory.
            verbose (bool, optional): If True, print verbose output. Defaults to False.
        Returns:
            str: The hash of the file or directory.
        """
        
        if os.path.isfile(path):
            if verbose:
                print(f"Hashing file: {path}")
            
            file_hash = HashHelper.hash_file(path, verbose=False)  # Don't log individual files
            if file_hash in self.hashes['files']:
                if path not in self.hashes['files'][file_hash]:
                    self.hashes['files'][file_hash].append(path)
            else:
                self.hashes['files'][file_hash] = [path]
            
            self._pending_saves = True
            return file_hash
        
        contents_hashes = []

        if verbose:
            print(f"Hashing directory: {path}")
        
        contents = FilesHelper.get_dir_contents(path, verbose=False)  # Don't log each directory
        for item in contents:
            item_hash = self.reursive_hash(item, verbose=verbose, save_on_complete=False)
            contents_hashes.append(item_hash)
        
        if verbose:
            print(f"Computed hashes for contents of directory: {path}")

        dir_hash = HashHelper.hash_list(contents_hashes, verbose=False)  # Don't log list hashing
        if dir_hash in self.hashes['dirs']:
            if path not in self.hashes['dirs'][dir_hash]:
                self.hashes['dirs'][dir_hash].append(path)
        else:
            self.hashes['dirs'][dir_hash] = [path]
        
        self._pending_saves = True
        
        # Only save at the top level of recursion
        if save_on_complete:
            HashHelper.save_hashes(self.hashes, verbose=verbose)
            self._pending_saves = False
        
        return dir_hash

    def flush_hashes(self, verbose: bool = False):
        """
        Flush any pending hash saves to disk.
        
        Args:
            verbose (bool, optional): If True, print verbose output. Defaults to False.
        """
        if self._pending_saves:
            HashHelper.save_hashes(self.hashes, verbose=verbose)
            self._pending_saves = False
            if verbose:
                print("Flushed pending hashes to disk.")
    
    def remove_path(self, path_to_remove: str, verbose: bool = False):
        """
        Removes a specific path from the internal hashes dictionary and saves the changes.
        """
        hash_to_find = None
        found_in = None

        # Check in files
        for hash_value, paths in self.hashes['files'].items():
            if path_to_remove in paths:
                hash_to_find = hash_value
                found_in = 'files'
                break
        
        # Check in dirs if not found in files
        if not hash_to_find:
            for hash_value, paths in self.hashes['dirs'].items():
                if path_to_remove in paths:
                    hash_to_find = hash_value
                    found_in = 'dirs'
                    break

        if hash_to_find and found_in:
            self.hashes[found_in][hash_to_find].remove(path_to_remove)
            # If the list for this hash is now empty or has only one file, it's no longer a duplicate group
            if len(self.hashes[found_in][hash_to_find]) < 2:
                del self.hashes[found_in][hash_to_find]
            
            HashHelper.save_hashes(self.hashes, verbose=verbose)
            if verbose:
                print(f"Removed {path_to_remove} and updated hashes.")
    
    def scan_optimized(self, path: str, verbose: bool = False, include_dirs: bool = False,
                       exclude_folders: list = None, file_types: list = None, 
                       min_size: int = 0, scan_subfolders: bool = True, 
                       include_hidden: bool = False) -> str:
        """
        Optimized scanning that uses size-based pre-filtering.
        Only hashes files that have duplicate sizes.
        
        Args:
            path (str): The path to scan
            verbose (bool, optional): If True, print verbose output
            include_dirs (bool, optional): If True, also scan for duplicate directories (slower)
            exclude_folders (list, optional): List of folder names to exclude from scan
            file_types (list, optional): List of file extensions to include (e.g., ['.jpg', '.png']). None = all files
            min_size (int, optional): Minimum file size in bytes to include in scan
            scan_subfolders (bool, optional): If True, scan recursively. If False, only scan top level
            include_hidden (bool, optional): If True, include hidden files/folders
        Returns:
            str: The hash of the path
        """
        # Normalize exclude folders and file types
        exclude_folders = [f.lower().strip() for f in (exclude_folders or [])]
        if file_types:
            file_types = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in file_types]
        if os.path.isfile(path):
            # Single file - just hash it
            return self.reursive_hash(path, verbose=verbose)
        
        if verbose:
            print(f"Collecting files from: {path}")
        
        # Step 1: Collect all files and group by size (fast operation)
        size_to_files = defaultdict(list)
        dir_paths = []
        
        def is_hidden(file_path):
            """Check if a file or folder is hidden"""
            basename = os.path.basename(file_path)
            # Unix-like hidden files start with '.'
            if basename.startswith('.'):
                return True
            # Windows hidden files (check attribute)
            try:
                import stat
                if os.name == 'nt':  # Windows
                    import ctypes
                    attrs = ctypes.windll.kernel32.GetFileAttributesW(file_path)
                    # FILE_ATTRIBUTE_HIDDEN = 0x2
                    return attrs != -1 and bool(attrs & 0x2)
            except:
                pass
            return False
        
        def should_exclude_folder(folder_path):
            """Check if folder should be excluded"""
            if not exclude_folders:
                return False
            folder_name = os.path.basename(folder_path).lower()
            folder_full = folder_path.lower()
            for exclude in exclude_folders:
                if exclude in folder_name or exclude in folder_full:
                    return True
            return False
        
        def should_include_file(file_path, size):
            """Check if file should be included based on filters"""
            # Check file size
            if size < min_size:
                return False
            
            # Check file type
            if file_types:
                ext = os.path.splitext(file_path)[1].lower()
                if ext not in file_types:
                    return False
            
            return True
        
        def collect_files(dir_path, depth=0):
            """Recursively collect all files and their sizes"""
            try:
                for item in os.listdir(dir_path):
                    item_path = os.path.join(dir_path, item)
                    
                    # Skip hidden files/folders if not included
                    if not include_hidden and is_hidden(item_path):
                        continue
                    
                    try:
                        if os.path.isfile(item_path):
                            size = os.path.getsize(item_path)
                            # Apply filters
                            if should_include_file(item_path, size):
                                size_to_files[size].append(item_path)
                        elif os.path.isdir(item_path):
                            # Check if folder should be excluded
                            if should_exclude_folder(item_path):
                                if verbose:
                                    print(f"Excluding folder: {item_path}")
                                continue
                            
                            dir_paths.append(item_path)
                            # Only recurse if scan_subfolders is True
                            if scan_subfolders:
                                collect_files(item_path, depth + 1)
                    except (OSError, PermissionError):
                        continue
            except (OSError, PermissionError):
                pass
        
        collect_files(path)
        
        if verbose:
            total_files = sum(len(files) for files in size_to_files.values())
            print(f"Collected {total_files} files")
        
        # Step 2: Only hash files that have duplicate sizes
        files_to_hash = []
        unique_size_files = 0
        
        for size, file_list in size_to_files.items():
            if len(file_list) > 1:
                # Multiple files with same size - need to hash them
                files_to_hash.extend(file_list)
            else:
                # Unique size - automatically unique file, no need to hash
                unique_size_files += 1
        
        if verbose:
            print(f"Skipping {unique_size_files} files with unique sizes")
            print(f"Hashing {len(files_to_hash)} files with duplicate sizes")
        
        # Step 3: For large files, use quick hash first (2-stage hashing)
        LARGE_FILE_THRESHOLD = 1024 * 1024  # 1MB
        quick_hash_groups = defaultdict(list)
        small_files = []
        
        for file_path in files_to_hash:
            try:
                size = os.path.getsize(file_path)
                if size > LARGE_FILE_THRESHOLD:
                    # Large file - use quick hash first
                    quick_hash = HashHelper.quick_hash_file(file_path)
                    quick_hash_groups[quick_hash].append(file_path)
                else:
                    # Small file - add to direct hash list
                    small_files.append(file_path)
            except (OSError, PermissionError):
                continue
        
        if verbose:
            print(f"Using quick hash for {len(files_to_hash) - len(small_files)} large files")
            print(f"Direct hashing {len(small_files)} small files")
        
        # Hash small files directly
        for file_path in small_files:
            # Check if stop was requested
            if self.stop_requested:
                if verbose:
                    print("Scan stopped by user")
                break
                
            try:
                # Pass stop check to allow interrupting during file hashing
                file_hash = HashHelper.hash_file(file_path, verbose=False, stop_check=lambda: self.stop_requested)
                if file_hash is None:  # Stopped during hashing
                    break
                if file_hash in self.hashes['files']:
                    if file_path not in self.hashes['files'][file_hash]:
                        self.hashes['files'][file_hash].append(file_path)
                else:
                    self.hashes['files'][file_hash] = [file_path]
                self._pending_saves = True
            except (OSError, PermissionError):
                continue
        
        # For large files: only fully hash if quick hash matches
        large_files_to_full_hash = []
        for quick_hash, file_list in quick_hash_groups.items():
            if len(file_list) > 1:
                # Multiple files with same quick hash - need full hash
                large_files_to_full_hash.extend(file_list)
            # Files with unique quick hash are definitely unique - skip them!
        
        if verbose:
            skipped_large = len(files_to_hash) - len(small_files) - len(large_files_to_full_hash)
            print(f"Skipped {skipped_large} large files with unique quick hashes")
            print(f"Full hashing {len(large_files_to_full_hash)} large files with matching quick hashes")
        
        # Full hash for large files that need it
        for file_path in large_files_to_full_hash:
            # Check if stop was requested
            if self.stop_requested:
                if verbose:
                    print("Scan stopped by user")
                break
                
            try:
                # Pass stop check to allow interrupting during file hashing
                file_hash = HashHelper.hash_file(file_path, verbose=False, stop_check=lambda: self.stop_requested)
                if file_hash is None:  # Stopped during hashing
                    break
                if file_hash in self.hashes['files']:
                    if file_path not in self.hashes['files'][file_hash]:
                        self.hashes['files'][file_hash].append(file_path)
                else:
                    self.hashes['files'][file_hash] = [file_path]
                self._pending_saves = True
            except (OSError, PermissionError):
                continue
        
        # Step 4: Process directories recursively (for directory duplicate detection)
        # This is SLOW for large directory trees, so it's optional
        if include_dirs:
            if verbose:
                print(f"Processing {len(dir_paths)} directories for duplicate detection...")
            for dir_path in dir_paths:
                try:
                    self.reursive_hash(dir_path, verbose=False, save_on_complete=False)
                except (OSError, PermissionError):
                    continue
        elif verbose:
            print(f"Skipping directory duplicate detection (set include_dirs=True to enable)")
        
        # Save once at the end
        if self._pending_saves:
            HashHelper.save_hashes(self.hashes, verbose=verbose)
            self._pending_saves = False
        
        return "scan_complete"
    
    def detect_duplicates(self, verbose: bool = False) -> dict:
        """
        Detect duplicate files and directories based on their hashes.

        Args:
            verbose (bool, optional): If True, print verbose output. Defaults to False.
        Returns:
            dict: A dictionary with duplicate files and directories.
        """

        duplicates = {'files': {}, 'dirs': {}}

        for hash_value, paths in self.hashes['files'].items():
            if len(paths) > 1:
                duplicates['files'][hash_value] = paths
        
        for hash_value, paths in self.hashes['dirs'].items():
            if len(paths) > 1:
                duplicates['dirs'][hash_value] = paths
        
        if verbose:
            print(f"Detected {len(duplicates['files'])} duplicate files and {len(duplicates['dirs'])} duplicate directories.")
        
        return duplicates
