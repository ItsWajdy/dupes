import os
import hashlib
import pickle
import sys
import hashlib
from src.constants import HASHES_PICKLE_PATH
from src.constants import EMPTY_HASHES_PICKLE

class HashHelper:
    @staticmethod
    def hash_file(filepath: str, verbose: bool = False) -> str:
        """
        Hash a file using SHA-256.

        Args:
            filepath (str): The path to the file.
            verbose (bool, optional): If True, print verbose output. Defaults to False.
        Returns:
            str: The SHA-256 hash of the file.
        """
        
        BUF_SIZE = 65536  # Read in 64kb chunks
        sha256 = hashlib.sha256()

        if verbose:
            print(f"Hashing file: {filepath}", file=sys.stderr)
        with open(filepath, 'rb') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                sha256.update(data)

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
            with open(HASHES_PICKLE_PATH, 'rb') as f:
                return pickle.load(f)
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
