import os

class FilesHelper:
    @staticmethod
    def walk_dir(dir: str, verbose: bool = False, logger=None) -> list:
        """
        Recursively walk through a directory and return a list of all file paths.

        Args:
            dir (str): The directory to walk through.
            verbose (bool, optional): If True, print verbose output. Defaults to False.
            logger: Logger instance for logging messages.
        Returns:
            list: A list of file paths.
        """

        file_paths = []
        
        try:
            for root, _, files in os.walk(dir):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            file_paths.append(file_path)
                    except (PermissionError, OSError) as e:
                        if logger:
                            logger.warning(f"Cannot access file: {file} - {str(e)}")
                        elif verbose:
                            print(f"Cannot access file: {file} - {str(e)}")
                        continue
        except (PermissionError, OSError) as e:
            if logger:
                logger.warning(f"Cannot walk directory: {dir} - {str(e)}")
            elif verbose:
                print(f"Cannot walk directory: {dir} - {str(e)}")
        
        return file_paths

    @staticmethod
    def get_dir_contents(dir: str, verbose: bool = False, logger=None) -> list:
        """
        Get the contents of a directory without recursion.

        Args:
            dir (str): The directory to get contents from.
            verbose (bool, optional): If True, print verbose output. Defaults to False.
            logger: Logger instance for logging messages.
        Returns:
            list: A list of file and directory paths in the given directory.
        """

        try:
            items = os.listdir(dir)
            contents = []
            
            for item in items:
                try:
                    full_path = os.path.join(dir, item)
                    if os.path.exists(full_path):
                        contents.append(full_path)
                except (PermissionError, OSError) as e:
                    if logger:
                        logger.warning(f"Cannot access item: {item} - {str(e)}")
                    elif verbose:
                        print(f"Cannot access item: {item} - {str(e)}")
                    continue
            
            return contents
            
        except FileNotFoundError:
            if logger:
                logger.warning(f"Directory not found: {dir}")
            elif verbose:
                print(f"Directory not found: {dir}")
            return []
        except PermissionError as e:
            if logger:
                logger.warning(f"Permission denied accessing directory: {dir} - {str(e)}")
            elif verbose:
                print(f"Permission denied accessing directory: {dir} - {str(e)}")
            return []
        except OSError as e:
            if logger:
                logger.warning(f"OS error accessing directory: {dir} - {str(e)}")
            elif verbose:
                print(f"OS error accessing directory: {dir} - {str(e)}")
            return []
        except Exception as e:
            if logger:
                logger.error(f"Unexpected error accessing directory: {dir} - {str(e)}")
            elif verbose:
                print(f"Unexpected error accessing directory: {dir} - {str(e)}")
            return []

    @staticmethod
    def get_file_metadata(file_path: str, verbose: bool = False, logger=None) -> dict:
        """
        Get metadata of a file including size and modification time.

        Args:
            file_path (str): The path to the file.
            verbose (bool, optional): If True, print verbose output. Defaults to False.
            logger: Logger instance for logging messages.
        Returns:
            dict: A dictionary containing file size, creation time, and modification time.
                  None if the file cannot be accessed.
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
            if logger:
                logger.warning(f"File not found: {file_path}")
            elif verbose:
                print(f"File not found: {file_path}")
            return None
        except PermissionError:
            if logger:
                logger.warning(f"Permission denied: {file_path}")
            elif verbose:
                print(f"Permission denied: {file_path}")
            return None
        except OSError as e:
            if logger:
                logger.warning(f"OS error getting metadata: {file_path} - {str(e)}")
            elif verbose:
                print(f"OS error getting metadata: {file_path} - {str(e)}")
            return None
        except Exception as e:
            if logger:
                logger.error(f"Unexpected error getting metadata: {file_path} - {str(e)}")
            elif verbose:
                print(f"Unexpected error getting metadata: {file_path} - {str(e)}")
            return None