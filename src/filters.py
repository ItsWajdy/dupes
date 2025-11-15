"""
Filtering and sorting utilities for duplicate file results.
"""
import os
import re
from typing import Dict, List, Tuple
from datetime import datetime


class FileTypeFilter:
    """Filter files by their type/extension."""
    
    # Common file extensions by category
    IMAGES = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', 
              '.tiff', '.tif', '.raw', '.heic', '.heif', '.psd', '.ai'}
    
    VIDEOS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', 
              '.mpg', '.mpeg', '.3gp', '.f4v', '.swf', '.vob', '.ogv'}
    
    DOCUMENTS = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', 
                 '.ppt', '.pptx', '.csv', '.ods', '.odp', '.tex', '.md', '.epub'}
    
    AUDIO = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus', 
             '.ape', '.alac', '.aiff'}
    
    ARCHIVES = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso', 
                '.dmg', '.pkg', '.deb', '.rpm'}
    
    CODE = {'.py', '.js', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go', 
            '.rs', '.rb', '.php', '.swift', '.kt', '.ts', '.tsx', '.jsx', '.html', 
            '.css', '.scss', '.sass', '.less', '.sql', '.sh', '.bat', '.ps1'}
    
    @staticmethod
    def get_extension(path: str) -> str:
        """Get the file extension in lowercase."""
        return os.path.splitext(path)[1].lower()
    
    @classmethod
    def filter_by_type(cls, paths: List[str], file_type: str) -> List[str]:
        """
        Filter paths by file type.
        
        Args:
            paths: List of file paths
            file_type: One of 'images', 'videos', 'documents', 'audio', 'archives', 'code', 'all'
        
        Returns:
            Filtered list of paths
        """
        if file_type == 'all':
            return paths
        
        type_map = {
            'images': cls.IMAGES,
            'videos': cls.VIDEOS,
            'documents': cls.DOCUMENTS,
            'audio': cls.AUDIO,
            'archives': cls.ARCHIVES,
            'code': cls.CODE,
        }
        
        extensions = type_map.get(file_type.lower(), set())
        if not extensions:
            return paths
        
        return [p for p in paths if cls.get_extension(p) in extensions]


class SizeFilter:
    """Filter files by size."""
    
    @staticmethod
    def get_file_size(path: str) -> int:
        """Get file size in bytes, returns 0 on error."""
        try:
            if os.path.isfile(path):
                return os.path.getsize(path)
            elif os.path.isdir(path):
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        try:
                            total_size += os.path.getsize(filepath)
                        except (OSError, FileNotFoundError):
                            pass
                return total_size
        except (OSError, FileNotFoundError):
            return 0
        return 0
    
    @staticmethod
    def parse_size_string(size_str: str) -> int:
        """
        Parse a size string like '10MB', '5.5GB', '100KB' to bytes.
        
        Args:
            size_str: Size string (e.g., '10MB', '5.5GB')
        
        Returns:
            Size in bytes
        """
        size_str = size_str.strip().upper()
        
        # Extract number and unit
        match = re.match(r'([\d.]+)\s*([KMGT]?B?)', size_str)
        if not match:
            return 0
        
        value = float(match.group(1))
        unit = match.group(2)
        
        multipliers = {
            '': 1,
            'B': 1,
            'K': 1024,
            'KB': 1024,
            'M': 1024 ** 2,
            'MB': 1024 ** 2,
            'G': 1024 ** 3,
            'GB': 1024 ** 3,
            'T': 1024 ** 4,
            'TB': 1024 ** 4,
        }
        
        return int(value * multipliers.get(unit, 1))
    
    @classmethod
    def filter_by_min_size(cls, paths: List[str], min_size: int) -> List[str]:
        """
        Filter paths by minimum size.
        
        Args:
            paths: List of file paths
            min_size: Minimum size in bytes
        
        Returns:
            Filtered list of paths
        """
        if min_size <= 0:
            return paths
        
        return [p for p in paths if cls.get_file_size(p) >= min_size]


class DuplicateSorter:
    """Sort duplicate file groups."""
    
    @staticmethod
    def get_file_modified_time(path: str) -> float:
        """Get file modification time, returns 0 on error."""
        try:
            return os.path.getmtime(path)
        except (OSError, FileNotFoundError):
            return 0
    
    @staticmethod
    def sort_paths(paths: List[str], sort_by: str, reverse: bool = False) -> List[str]:
        """
        Sort paths by specified criteria.
        
        Args:
            paths: List of file paths
            sort_by: One of 'size', 'name', 'date', 'path'
            reverse: If True, sort in reverse order
        
        Returns:
            Sorted list of paths
        """
        if sort_by == 'size':
            # Sort by file size
            return sorted(paths, key=lambda p: SizeFilter.get_file_size(p), reverse=not reverse)
        
        elif sort_by == 'name':
            # Sort by filename (basename)
            return sorted(paths, key=lambda p: os.path.basename(p).lower(), reverse=reverse)
        
        elif sort_by == 'date':
            # Sort by modification date
            return sorted(paths, key=lambda p: DuplicateSorter.get_file_modified_time(p), reverse=not reverse)
        
        elif sort_by == 'path':
            # Sort by full path
            return sorted(paths, key=lambda p: p.lower(), reverse=reverse)
        
        else:
            # Default: no sorting
            return paths


class SearchFilter:
    """Search/filter paths by text query."""
    
    @staticmethod
    def search_paths(paths: List[str], query: str, case_sensitive: bool = False) -> List[str]:
        """
        Search paths for a text query.
        
        Args:
            paths: List of file paths
            query: Search query string
            case_sensitive: If True, perform case-sensitive search
        
        Returns:
            Filtered list of paths matching the query
        """
        if not query:
            return paths
        
        if not case_sensitive:
            query = query.lower()
            return [p for p in paths if query in p.lower()]
        else:
            return [p for p in paths if query in p]


class DuplicateFilter:
    """Main filtering and sorting interface for duplicate results."""
    
    @staticmethod
    def filter_duplicates(duplicates: Dict[str, Dict[str, List[str]]], 
                         file_type: str = 'all',
                         min_size: int = 0,
                         sort_by: str = 'size',
                         reverse_sort: bool = True,
                         search_query: str = '') -> Dict[str, Dict[str, List[str]]]:
        """
        Apply filters and sorting to duplicate results.
        
        Args:
            duplicates: Dictionary with 'files' and 'dirs' keys containing duplicate groups
            file_type: Filter by file type ('all', 'images', 'videos', 'documents', etc.)
            min_size: Minimum file size in bytes (0 for no filter)
            sort_by: Sort criteria ('size', 'name', 'date', 'path')
            reverse_sort: If True, reverse the sort order (for size: largest first)
            search_query: Text to search in file paths
        
        Returns:
            Filtered and sorted duplicates dictionary
        """
        filtered = {'files': {}, 'dirs': {}}
        
        # Process file duplicates
        for hash_value, paths in duplicates.get('files', {}).items():
            # Apply filters
            filtered_paths = paths
            
            # File type filter
            filtered_paths = FileTypeFilter.filter_by_type(filtered_paths, file_type)
            
            # Size filter
            filtered_paths = SizeFilter.filter_by_min_size(filtered_paths, min_size)
            
            # Search filter
            filtered_paths = SearchFilter.search_paths(filtered_paths, search_query)
            
            # Only keep groups with duplicates (2+ files)
            if len(filtered_paths) > 1:
                # Sort the paths
                filtered_paths = DuplicateSorter.sort_paths(filtered_paths, sort_by, reverse_sort)
                filtered['files'][hash_value] = filtered_paths
        
        # Process directory duplicates
        for hash_value, paths in duplicates.get('dirs', {}).items():
            # Apply filters
            filtered_paths = paths
            
            # Size filter
            filtered_paths = SizeFilter.filter_by_min_size(filtered_paths, min_size)
            
            # Search filter
            filtered_paths = SearchFilter.search_paths(filtered_paths, search_query)
            
            # Only keep groups with duplicates (2+ directories)
            if len(filtered_paths) > 1:
                # Sort the paths
                filtered_paths = DuplicateSorter.sort_paths(filtered_paths, sort_by, reverse_sort)
                filtered['dirs'][hash_value] = filtered_paths
        
        return filtered
    
    @staticmethod
    def sort_duplicate_groups(duplicates: Dict[str, Dict[str, List[str]]], 
                             sort_by: str = 'size') -> Dict[str, Dict[str, List[str]]]:
        """
        Sort entire duplicate groups (not just paths within groups).
        
        Args:
            duplicates: Dictionary with 'files' and 'dirs' keys
            sort_by: Sort groups by 'group_size', 'count', or 'hash'
        
        Returns:
            Dictionary with sorted groups
        """
        sorted_result = {'files': {}, 'dirs': {}}
        
        # Sort files groups
        if sort_by == 'group_size':
            # Sort by total size of all duplicates in group
            sorted_items = sorted(
                duplicates.get('files', {}).items(),
                key=lambda x: sum(SizeFilter.get_file_size(p) for p in x[1]),
                reverse=True
            )
        elif sort_by == 'count':
            # Sort by number of duplicates
            sorted_items = sorted(
                duplicates.get('files', {}).items(),
                key=lambda x: len(x[1]),
                reverse=True
            )
        else:
            # Default: keep original order
            sorted_items = list(duplicates.get('files', {}).items())
        
        sorted_result['files'] = dict(sorted_items)
        
        # Sort dirs groups
        if sort_by == 'group_size':
            sorted_items = sorted(
                duplicates.get('dirs', {}).items(),
                key=lambda x: sum(SizeFilter.get_file_size(p) for p in x[1]),
                reverse=True
            )
        elif sort_by == 'count':
            sorted_items = sorted(
                duplicates.get('dirs', {}).items(),
                key=lambda x: len(x[1]),
                reverse=True
            )
        else:
            sorted_items = list(duplicates.get('dirs', {}).items())
        
        sorted_result['dirs'] = dict(sorted_items)
        
        return sorted_result
