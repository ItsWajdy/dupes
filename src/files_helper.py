import os

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

        try:
            contents = [os.path.join(dir, item) for item in os.listdir(dir)]
            return contents
        except FileNotFoundError:
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
            stats = os.stat(file_path)
            metadata = {
                "size": stats.st_size,
                "type": stats.st_mode,
                "date_modified": stats.st_mtime,
            }
            return metadata
        except FileNotFoundError:
            return None