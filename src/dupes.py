import os
from .files_helper import FilesHelper
from .hash_helper import HashHelper

class Dupes:
    def __init__(self, verbose: bool = False):
        self.hashes = HashHelper.load_hashes(verbose=verbose)

    def reursive_hash(self, path: str, verbose: bool = False) -> str:
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
            
            try:
                file_hash = HashHelper.hash_file(path, verbose=verbose)
                if file_hash in self.hashes['files']:
                    if path not in self.hashes['files'][file_hash]:
                        self.hashes['files'][file_hash].append(path)
                else:
                    self.hashes['files'][file_hash] = [path]
                
                HashHelper.save_hashes(self.hashes, verbose=verbose)
                return file_hash
            except (IOError, PermissionError) as e:
                print(f"Error hashing file {path}: {e}")
                raise
            except Exception as e:
                print(f"An unexpected error occurred while hashing file {path}: {e}")
                raise
        
        contents_hashes = []

        if verbose:
            print(f"Hashing directory: {path}")
        
        try:
            contents = FilesHelper.get_dir_contents(path, verbose=verbose)
        except (IOError, PermissionError) as e:
            print(f"Error getting contents of directory {path}: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred while getting contents of directory {path}: {e}")
            raise

        for item in contents:
            try:
                item_hash = self.reursive_hash(item, verbose=verbose)
                if item_hash is not None:
                    contents_hashes.append(item_hash)
            except Exception as e:
                print(f"Skipping {item} due to error: {e}")
        
        if verbose:
            print(f"Computed hashes for contents of directory: {path}")

        dir_hash = HashHelper.hash_list(contents_hashes, verbose=verbose)
        if dir_hash in self.hashes['dirs']:
            if path not in self.hashes['dirs'][dir_hash]:
                self.hashes['dirs'][dir_hash].append(path)
        else:
            self.hashes['dirs'][dir_hash] = [path]
        
        try:
            HashHelper.save_hashes(self.hashes, verbose=verbose)
        except (IOError, PermissionError) as e:
            print(f"Error saving hashes for directory {path}: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred while saving hashes for directory {path}: {e}")
            raise
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
        
        if verbose:
            print(f"Detected {len(duplicates['files'])} duplicate files and {len(duplicates['dirs'])} duplicate directories.")
        
        return duplicates
