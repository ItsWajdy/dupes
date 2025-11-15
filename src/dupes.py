import os
from src.files_helper import FilesHelper
from src.hash_helper import HashHelper
from src.logger import Logger

class Dupes:
    def __init__(self, verbose: bool = False, logger: Logger = None):
        self.hashes = HashHelper.load_hashes(verbose=verbose)
        self.logger = logger
        self.file_count = 0
        self.dir_count = 0

    def count_items(self, path: str) -> dict:
        """
        Count the total number of files and directories to process.
        
        Args:
            path (str): The path to count from
            
        Returns:
            dict: Dictionary with 'files' and 'dirs' counts
        """
        counts = {'files': 0, 'dirs': 0}
        
        if os.path.isfile(path):
            counts['files'] = 1
            return counts
        
        for _, dirs, files in os.walk(path):
            counts['files'] += len(files)
            counts['dirs'] += len(dirs)
        
        return counts

    def reursive_hash(self, path: str, verbose: bool = False, task_id: int = None) -> str:
        """
        Recursively hash a file or directory.

        Args:
            path (str): The path to the file or directory.
            verbose (bool, optional): If True, print verbose output. Defaults to False.
            task_id (int, optional): Progress task ID for updating progress bar.
        Returns:
            str: The hash of the file or directory.
        """
        
        if os.path.isfile(path):
            if self.logger:
                self.logger.debug(f"Hashing file: {path}")
            
            file_hash = HashHelper.hash_file(path, verbose=verbose)
            
            if file_hash in self.hashes['files']:
                if path not in self.hashes['files'][file_hash]:
                    self.hashes['files'][file_hash].append(path)
            else:
                self.hashes['files'][file_hash] = [path]
            
            HashHelper.save_hashes(self.hashes, verbose=verbose)
            
            # Update progress
            self.file_count += 1
            if self.logger and task_id is not None:
                self.logger.update_task(task_id, advance=1)
            
            return file_hash
        
        contents_hashes = []

        if self.logger:
            self.logger.debug(f"Hashing directory: {path}")
        
        contents = FilesHelper.get_dir_contents(path, verbose=verbose)
        for item in contents:
            item_hash = self.reursive_hash(item, verbose=verbose, task_id=task_id)
            contents_hashes.append(item_hash)
        
        if self.logger:
            self.logger.debug(f"Computed hashes for directory: {path}")

        dir_hash = HashHelper.hash_list(contents_hashes, verbose=verbose)
        
        if dir_hash in self.hashes['dirs']:
            if path not in self.hashes['dirs'][dir_hash]:
                self.hashes['dirs'][dir_hash].append(path)
        else:
            self.hashes['dirs'][dir_hash] = [path]
        
        HashHelper.save_hashes(self.hashes, verbose=verbose)
        
        # Update progress for directory
        self.dir_count += 1
        if self.logger and task_id is not None:
            self.logger.update_task(task_id, advance=0)  # Don't advance, just refresh
        
        return dir_hash
    
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
        
        if self.logger:
            self.logger.info(
                f"Found {len(duplicates['files'])} duplicate file groups "
                f"and {len(duplicates['dirs'])} duplicate directory groups"
            )
        
        return duplicates