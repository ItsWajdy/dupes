import click
import os
import shutil
from .dupes import Dupes
from .hash_helper import HashHelper
from .constants import HASHES_PICKLE_PATH
from .filters import DuplicateFilter, SizeFilter


def make_clickable_path(path: str) -> str:
    """
    Create a clickable hyperlink for terminals that support OSC 8.
    Falls back to plain text if hyperlinks are not supported.
    """
    # Convert to absolute path and URL format
    abs_path = os.path.abspath(path)
    # Use file:// URI scheme
    file_uri = f"file:///{abs_path.replace(os.sep, '/')}"
    
    # OSC 8 format: \033]8;;URI\033\\TEXT\033]8;;\033\\
    # This works in: Windows Terminal, iTerm2, GNOME Terminal, and many modern terminals
    return f"\033]8;;{file_uri}\033\\{path}\033]8;;\033\\"

@click.group()
def main():
    """A CLI tool to detect duplicate files based on their hashes."""
    pass

@main.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
@click.argument('dirs', nargs=-1, type=click.Path(exists=True), required=True)
def process_dir(verbose: bool, dirs: list[str]):
    """Process the given directories."""
    import time

    dupes = Dupes(verbose=verbose)
    for dir in dirs:
        if verbose:
            click.echo(f"\nProcessing directory: {dir}")
        
        start_time = time.time()
        # Use optimized scanning that filters by file size first
        # include_dirs=False skips directory duplicate detection for much faster scanning
        dupes.scan_optimized(dir, verbose, include_dirs=False)
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        click.echo(f"Scan complete for {dir}. (took {elapsed_time:.2f} seconds)")

@main.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
@click.option('--no-links', is_flag=True, help='Disable clickable file links.')
@click.option('--file-type', '-t', type=click.Choice(['all', 'images', 'videos', 'documents', 'audio', 'archives', 'code']), default='all', help='Filter by file type.')
@click.option('--min-size', '-s', default='', help='Minimum file size (e.g., 10MB, 1GB).')
@click.option('--sort-by', type=click.Choice(['size', 'name', 'date', 'path']), default='size', help='Sort results by specified criteria.')
@click.option('--search', default='', help='Search for specific text in file paths.')
def detect_duplicates(verbose: bool, no_links: bool, file_type: str, min_size: str, sort_by: str, search: str):
    """Detect and print duplicate files based on their hashes with filtering and sorting options."""

    dupes = Dupes(verbose=verbose)
    duplicates = dupes.detect_duplicates(verbose=verbose)
    
    # Apply filters and sorting
    min_size_bytes = SizeFilter.parse_size_string(min_size) if min_size else 0
    duplicates = DuplicateFilter.filter_duplicates(
        duplicates,
        file_type=file_type,
        min_size=min_size_bytes,
        sort_by=sort_by,
        reverse_sort=True,
        search_query=search
    )
    
    # Sort groups by size (largest first)
    duplicates = DuplicateFilter.sort_duplicate_groups(duplicates, sort_by='group_size')

    duplicated_dirs_exist = len(duplicates['dirs'].items()) > 0
    duplicated_files_exist = len(duplicates['files'].items()) > 0

    if duplicated_dirs_exist:
        click.echo("\nDuplicate folders found:")
        for hash_value, dirs in duplicates['dirs'].items():
            click.echo(f"\nHash: {hash_value}")
            for dir in dirs:
                display_path = dir if no_links else make_clickable_path(dir)
                click.echo(f" - {display_path}")
    else:
        click.echo("No duplicate folders found.")
    
    if duplicated_files_exist:
        click.echo("\n\n\nDuplicate files found:")
        for hash_value, files in duplicates['files'].items():
            click.echo(f"\nHash: {hash_value}")
            for file in files:
                display_path = file if no_links else make_clickable_path(file)
                click.echo(f" - {display_path}")
    else:
        click.echo("No duplicate files found.")

@main.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
def clear_hashes(verbose: bool):
    """Clear all stored hashes."""
    HashHelper.clear_hashes(verbose=verbose)

@main.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
@click.option('--interactive', '-i', is_flag=True, help='Interactively choose which duplicates to delete.')
@click.option('--auto', '-a', is_flag=True, help='Automatically delete all duplicates except the first one found.')
@click.option('--dry-run', '-d', is_flag=True, help='Show what would be deleted without actually deleting.')
@click.option('--no-links', is_flag=True, help='Disable clickable file links.')
@click.option('--file-type', '-t', type=click.Choice(['all', 'images', 'videos', 'documents', 'audio', 'archives', 'code']), default='all', help='Filter by file type.')
@click.option('--min-size', '-s', default='', help='Minimum file size (e.g., 10MB, 1GB).')
@click.option('--sort-by', type=click.Choice(['size', 'name', 'date', 'path']), default='size', help='Sort results by specified criteria.')
@click.option('--search', default='', help='Search for specific text in file paths.')
def delete_duplicates(verbose: bool, interactive: bool, auto: bool, dry_run: bool, no_links: bool, 
                     file_type: str, min_size: str, sort_by: str, search: str):
    """Delete duplicate files, keeping only the first occurrence of each. Supports filtering and sorting."""
    
    if interactive and auto:
        click.echo("Error: Cannot use both --interactive and --auto flags together.")
        return
    
    if not interactive and not auto:
        click.echo("Error: Must specify either --interactive or --auto mode.")
        return

    dupes = Dupes(verbose=verbose)
    duplicates = dupes.detect_duplicates(verbose=verbose)
    
    # Apply filters and sorting
    min_size_bytes = SizeFilter.parse_size_string(min_size) if min_size else 0
    duplicates = DuplicateFilter.filter_duplicates(
        duplicates,
        file_type=file_type,
        min_size=min_size_bytes,
        sort_by=sort_by,
        reverse_sort=True,
        search_query=search
    )
    
    # Sort groups by size (largest first)
    duplicates = DuplicateFilter.sort_duplicate_groups(duplicates, sort_by='group_size')

    duplicated_files_exist = len(duplicates['files'].items()) > 0
    duplicated_dirs_exist = len(duplicates['dirs'].items()) > 0

    if not duplicated_files_exist and not duplicated_dirs_exist:
        click.echo("No duplicates found.")
        return

    total_deleted = 0
    total_space_saved = 0

    # Handle duplicate files
    if duplicated_files_exist:
        click.echo("\n=== Duplicate Files ===")
        for hash_value, files in duplicates['files'].items():
            if len(files) <= 1:
                continue
                
            click.echo(f"\nDuplicate group (hash: {hash_value[:8]}...):")
            first_file, *duplicate_files = files
            display_first = first_file if no_links else make_clickable_path(first_file)
            click.echo(f"  [KEEP] {display_first}")
            
            for file_path in duplicate_files:
                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                display_path = file_path if no_links else make_clickable_path(file_path)
                
                should_delete = False
                if auto:
                    should_delete = True
                elif interactive:
                    click.echo(f"  [DELETE?] {display_path} ({file_size} bytes)")
                    should_delete = click.confirm(f"    Delete this file?")
                
                if should_delete:
                    if dry_run:
                        click.echo(f"  [DRY RUN] Would delete: {display_path}")
                        total_space_saved += file_size
                        total_deleted += 1
                    else:
                        try:
                            os.remove(file_path)
                            dupes.remove_path(file_path)
                            click.echo(f"  [DELETED] {display_path}")
                            total_space_saved += file_size
                            total_deleted += 1
                        except Exception as e:
                            click.echo(f"  [ERROR] Failed to delete {display_path}: {e}")
                else:
                    if interactive:
                        click.echo(f"  [SKIPPED] {display_path}")

    # Handle duplicate directories
    if duplicated_dirs_exist:
        click.echo("\n=== Duplicate Directories ===")
        for hash_value, dirs in duplicates['dirs'].items():
            if len(dirs) <= 1:
                continue
                
            click.echo(f"\nDuplicate group (hash: {hash_value[:8]}...):")
            first_dir, *duplicate_dirs = dirs
            display_first = first_dir if no_links else make_clickable_path(first_dir)
            click.echo(f"  [KEEP] {display_first}")
            
            for dir_path in duplicate_dirs:
                # Calculate directory size
                dir_size = 0
                try:
                    for dirpath, dirnames, filenames in os.walk(dir_path):
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            if os.path.exists(filepath):
                                dir_size += os.path.getsize(filepath)
                except:
                    dir_size = 0
                
                display_path = dir_path if no_links else make_clickable_path(dir_path)
                
                should_delete = False
                if auto:
                    should_delete = True
                elif interactive:
                    click.echo(f"  [DELETE?] {display_path} ({dir_size} bytes)")
                    should_delete = click.confirm(f"    Delete this directory?")
                
                if should_delete:
                    if dry_run:
                        click.echo(f"  [DRY RUN] Would delete: {display_path}")
                        total_space_saved += dir_size
                        total_deleted += 1
                    else:
                        try:
                            shutil.rmtree(dir_path)
                            dupes.remove_path(dir_path)
                            click.echo(f"  [DELETED] {display_path}")
                            total_space_saved += dir_size
                            total_deleted += 1
                        except Exception as e:
                            click.echo(f"  [ERROR] Failed to delete {display_path}: {e}")
                else:
                    if interactive:
                        click.echo(f"  [SKIPPED] {display_path}")

    # Summary
    action_word = "Would delete" if dry_run else "Deleted"
    size_mb = total_space_saved / (1024 * 1024)
    click.echo(f"\n=== Summary ===")
    click.echo(f"{action_word} {total_deleted} duplicate items")
    click.echo(f"Space {'that would be' if dry_run else ''} freed: {size_mb:.2f} MB ({total_space_saved} bytes)")

if __name__ == '__main__':
    main()
