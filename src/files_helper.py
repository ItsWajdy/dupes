import os
import sys

class FilesHelper:
    @staticmethod
    def get_dir_contents(dir: str, verbose: bool = False) -> list:
        """
        Get the contents of a directory without recursion.

        Args:
            dir (str): The directory to get contents from.
            verbose (bool, optional): If True, print verbose output. Defaults to False.
        Returns:
            list: A list of file and directory paths in the given directory.
        """

        if verbose:
            print(f"Getting contents of directory: {dir}", file=sys.stderr)
        try:
            contents = [os.path.join(dir, item) for item in os.listdir(dir)]
            return contents
        except FileNotFoundError:
            print(f"Directory not found: {dir}", file=sys.stderr)
            raise # Re-raise to be caught by dupes.py
        except PermissionError:
            print(f"Permission denied to access directory: {dir}", file=sys.stderr)
            raise # Re-raise to be caught by dupes.py
        except Exception as e:
            print(f"An unexpected error occurred while getting contents of directory {dir}: {e}", file=sys.stderr)
            raise
