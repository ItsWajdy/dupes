import os
import sys

class FilesHelper:
    @staticmethod
    def walk_dir(dir: str, verbose: bool = False) -> list:
        """
        Recursively walk through a directory and return a list of all file paths.

        Args:
            dir (str): The directory to walk through.
            verbose (bool, optional): If True, print verbose output. Defaults to False.
        Returns:
            list: A list of file paths.
        """

        file_paths = []
        for root, _, files in os.walk(dir):
            if verbose:
                print(f"Walking through directory: {root}", file=sys.stderr)
            for file in files:
                file_paths.append(os.path.join(root, file))
        return file_paths

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
            return []

    @staticmethod
    def get_file_metadata(file_path: str, verbose: bool = False) -> dict:
        """
        Get metadata of a file including size and modification time.

        Args:
            file_path (str): The path to the file.
            verbose (bool, optional): If True, print verbose output. Defaults to False.
        Returns:
            dict: A dictionary containing file size, creation time, and modification time.
        """
        try:
            if verbose:
                print(f"Getting metadata for file: {file_path}", file=sys.stderr)
            stats = os.stat(file_path)
            metadata = {
                "size": stats.st_size,
                "type": stats.st_mode,
                "date_modified": stats.st_mtime,
            }
            if verbose:
                print(f"\nMetadata for {file_path}: {metadata}", file=sys.stderr)
            return metadata
        except FileNotFoundError:
            print(f"File not found: {file_path}", file=sys.stderr)
            return None
