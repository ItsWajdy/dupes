import os
import hashlib
import pickle
from src.constants import HASHES_PICKLE_PATH
from src.constants import EMPTY_HASHES_PICKLE
from typing import Optional

class HashHelper:
    @staticmethod
    def hash_file(filepath: str, verbose: bool = False, logger=None) -> str:
        """
        Hash a file using SHA-256.

        Args:
            filepath (str): The path to the file.
            verbose (bool, optional): If True, print verbose output. Defaults to False.
            logger: Logger instance for logging messages.
        Returns:
            str: The SHA-256 hash of the file.
        Raises:
            PermissionError: If the file cannot be read due to permissions.
            OSError: If the file cannot be read for other reasons.
            IOError: If there's an I/O error reading the file.
        """
        
        BUF_SIZE = 65536  # Read in 64kb chunks
        sha256 = hashlib.sha256()

        try:
            with open(filepath, 'rb') as f:
                while True:
                    data = f.read(BUF_SIZE)
                    if not data:
                        break
                    sha256.update(data)
            
            return sha256.hexdigest()
            
        except PermissionError:
            raise PermissionError(f"Permission denied")
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found")
        except IsADirectoryError:
            raise IsADirectoryError(f"Expected file but got directory")
        except OSError as e:
            raise OSError(f"OS error: {str(e)}")
        except Exception as e:
            raise IOError(f"Unexpected error reading file: {str(e)}")

    @staticmethod
    def hash_list(hashes: list[str], verbose: bool = False, logger=None) -> str:
        """
        Hash a list of strings using SHA-256.

        Args:
            hashes (list[str]): The list of strings to hash.
            verbose (bool, optional): If True, print verbose output. Defaults to False.
            logger: Logger instance for logging messages.
        Returns:
            str: The SHA-256 hash of the concatenated strings.
        """

        try:
            sha256 = hashlib.sha256()

            for item in sorted(hashes):
                if item is not None:  # Skip None values from failed hashes
                    sha256.update(item.encode('utf-8'))

            return sha256.hexdigest()
        except Exception as e:
            # If hashing fails, return a hash of empty string
            # This shouldn't happen but provides a fallback
            if logger:
                logger.warning(f"Error hashing list, using fallback: {str(e)}")
            return hashlib.sha256(b'').hexdigest()

    @staticmethod
    def load_hashes(verbose: bool = False, logger=None) -> dict:
        """
        Load hashes from a pickle file.

        Args:
            verbose (bool, optional): If True, print verbose output. Defaults to False.
            logger: Logger instance for logging messages.
        Returns:
            dict: The loaded hashes.
        """

        try:
            if os.path.exists(HASHES_PICKLE_PATH):
                with open(HASHES_PICKLE_PATH, 'rb') as f:
                    hashes = pickle.load(f)
                    
                    if not isinstance(hashes, dict) or 'files' not in hashes or 'dirs' not in hashes:
                        if logger:
                            logger.warning("Invalid hash file structure, creating new one")
                        elif verbose:
                            print(f"Invalid hash file structure, creating new one")
                        return EMPTY_HASHES_PICKLE.copy()
                    
                    return hashes
            else:
                return EMPTY_HASHES_PICKLE.copy()
                
        except (pickle.PickleError, EOFError) as e:
            if logger:
                logger.warning(f"Error loading pickle file: {str(e)}. Creating new hash file.")
            elif verbose:
                print(f"Error loading pickle file: {str(e)}. Creating new hash file.")
            return EMPTY_HASHES_PICKLE.copy()
        except Exception as e:
            if logger:
                logger.warning(f"Unexpected error loading hashes: {str(e)}. Creating new hash file.")
            elif verbose:
                print(f"Unexpected error loading hashes: {str(e)}. Creating new hash file.")
            return EMPTY_HASHES_PICKLE.copy()
    
    @staticmethod
    def save_hashes(hashes: dict, verbose: bool = False, logger=None) -> bool:
        """
        Save hashes to a pickle file.

        Args:
            hashes (dict): The hashes to save.
            verbose (bool, optional): If True, print verbose output. Defaults to False.
            logger: Logger instance for logging messages.
        Returns:
            bool: True if successful, False otherwise.
        """

        try:
            # Create a backup of existing file if it exists
            if os.path.exists(HASHES_PICKLE_PATH):
                backup_path = f"{HASHES_PICKLE_PATH}.backup"
                try:
                    import shutil
                    shutil.copy2(HASHES_PICKLE_PATH, backup_path)
                except Exception:
                    pass
            
            with open(HASHES_PICKLE_PATH, 'wb') as f:
                pickle.dump(hashes, f)
            
            return True
            
        except PermissionError as e:
            if logger:
                logger.error(f"Permission denied when saving hashes: {str(e)}")
            elif verbose:
                print(f"Permission denied when saving hashes: {str(e)}")
            return False
        except OSError as e:
            if logger:
                logger.error(f"OS error when saving hashes: {str(e)}")
            elif verbose:
                print(f"OS error when saving hashes: {str(e)}")
            return False
        except Exception as e:
            if logger:
                logger.error(f"Unexpected error saving hashes: {str(e)}")
            elif verbose:
                print(f"Unexpected error saving hashes: {str(e)}")
            return False
    
    @staticmethod
    def clear_hashes(verbose: bool = False, logger=None) -> bool:
        """
        Clear all stored hashes.

        Args:
            verbose (bool, optional): If True, print verbose output. Defaults to False.
            logger: Logger instance for logging messages.
        Returns:
            bool: True if successful, False otherwise.
        """

        try:
            return HashHelper.save_hashes(EMPTY_HASHES_PICKLE.copy(), verbose=verbose, logger=logger)
        except Exception as e:
            if logger:
                logger.error(f"Error clearing hashes: {str(e)}")
            elif verbose:
                print(f"Error clearing hashes: {str(e)}")
            return False