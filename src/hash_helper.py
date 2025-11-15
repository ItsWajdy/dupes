import os
import hashlib
import pickle
import sys
import hashlib
from src.constants import HASHES_PICKLE_PATH
from src.constants import EMPTY_HASHES_PICKLE

class HashHelper:
    @staticmethod
    def hash_file(filepath: str, verbose: bool = False, stop_check=None) -> str:
        """
        Hash a file using SHA-256.

        Args:
            filepath (str): The path to the file.
            verbose (bool, optional): If True, print verbose output. Defaults to False.
            stop_check (callable): Optional function that returns True if hashing should stop
        Returns:
            str: The SHA-256 hash of the file, or None if stopped
        """
        
        BUF_SIZE = 1048576  # Read in 1MB chunks (16x faster than 64KB)
        sha256 = hashlib.sha256()

        if verbose:
            print(f"Hashing file: {filepath}", file=sys.stderr)
        with open(filepath, 'rb') as f:
            while True:
                # Check if we should stop between chunks
                if stop_check and stop_check():
                    return None
                    
                data = f.read(BUF_SIZE)
                if not data:
                    break
                sha256.update(data)

        return sha256.hexdigest()
    
    @staticmethod
    def quick_hash_file(filepath: str) -> str:
        """
        Quick hash using only the first 8KB of a file.
        Used for initial filtering before full hash.

        Args:
            filepath (str): The path to the file.
        Returns:
            str: The SHA-256 hash of the first 8KB.
        """
        sha256 = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                # Read only first 8KB for quick comparison
                data = f.read(8192)
                sha256.update(data)
        except (OSError, IOError):
            pass
        return sha256.hexdigest()

    @staticmethod
    def hash_list(hashes: list[str], verbose: bool = False) -> str:
        """
        Hash a list of strings using SHA-256.

        Args:
            hashes (list[str]): The list of strings to hash.
            verbose (bool, optional): If True, print verbose output. Defaults to False.
        Returns:
            str: The SHA-256 hash of the concatenated strings.
        """

        sha256 = hashlib.sha256()

        if verbose:
            print(f"Hashing list of {len(hashes)} items.", file=sys.stderr)
        for item in sorted(hashes):
            sha256.update(item.encode('utf-8'))

        return sha256.hexdigest()

    @staticmethod
    def load_hashes(verbose: bool = False) -> dict:
        """
        Load hashes from a pickle file.

        Args:
            verbose (bool, optional): If True, print verbose output. Defaults to False.
        Returns:
            dict: The loaded hashes.
        """

        if os.path.exists(HASHES_PICKLE_PATH):
            if verbose:
                print(f"Loading hashes from {HASHES_PICKLE_PATH}")
            try:
                with open(HASHES_PICKLE_PATH, 'rb') as f:
                    return pickle.load(f)
            except (EOFError, pickle.UnpicklingError) as e:
                if verbose:
                    print(f"Warning: Corrupted pickle file at {HASHES_PICKLE_PATH}. Starting fresh. Error: {e}", file=sys.stderr)
                return EMPTY_HASHES_PICKLE
        else:
            if verbose:
                print(f"No existing hash file found at {HASHES_PICKLE_PATH}. Starting fresh.")
            return EMPTY_HASHES_PICKLE
    
    @staticmethod
    def save_hashes(hashes: dict, verbose: bool = False):
        """
        Save hashes to a pickle file.

        Args:
            hashes (dict): The hashes to save.
            verbose (bool, optional): If True, print verbose output. Defaults to False.
        Returns:
            None
        """

        with open(HASHES_PICKLE_PATH, 'wb') as f:
            pickle.dump(hashes, f)
        if verbose:
            print(f"Saved {len(hashes)} hashes to {HASHES_PICKLE_PATH}")
    
    @staticmethod
    def clear_hashes(verbose: bool = False):
        """
        Clear all stored hashes.

        Args:
            verbose (bool, optional): If True, print verbose output. Defaults to False.
        Returns:
            None
        """

        HashHelper.save_hashes(EMPTY_HASHES_PICKLE, verbose=verbose)
        if verbose:
            print(f"Cleared all hashes in {HASHES_PICKLE_PATH}")
