import click
from rich.console import Console
from rich.table import Table
from src.dupes import Dupes
from src.hash_helper import HashHelper
from src.logger import Logger, SimpleLogger
from src.constants import HASHES_PICKLE_PATH

console = Console()

@click.group()
def main():
    """A CLI tool to detect duplicate files based on their hashes."""
    pass

@main.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
@click.argument('dirs', nargs=-1, type=click.Path(exists=True), required=True)
def process_dir(verbose: bool, dirs: list[str]):
    """Process the given directories."""
    
    logger = Logger(verbose=verbose, max_log_lines=15)
    dupes = Dupes(verbose=verbose, logger=logger)
    
    try:
        # First, count total items to process
        logger.info("Scanning directories to count items...")
        total_files = 0
        total_dirs = 0
        
        for dir_path in dirs:
            counts = dupes.count_items(dir_path)
            total_files += counts['files']
            total_dirs += counts['dirs']
        
        logger.info(f"Found {total_files} files and {total_dirs} directories to process")
        
        # Start the live display with progress bar
        logger.start()
        task_id = logger.add_task("Processing files and directories", total=total_files)
        
        # Process each directory
        for dir_path in dirs:
            logger.info(f"Processing: {dir_path}")
            dupes.reursive_hash(dir_path, verbose, task_id=task_id)
        
        logger.success(f"Completed processing {dupes.file_count} files and {dupes.dir_count} directories")
        
        # Stop the live display
        logger.stop()
        
        logger.print("\n✨ [bold green]Processing complete![/bold green]", style="bold")
        logger.print(f"Hashes saved to [cyan]{HASHES_PICKLE_PATH}[/cyan]")
        
    except KeyboardInterrupt:
        logger.stop()
        logger.print("\n[yellow]Processing interrupted by user[/yellow]")
    except Exception as e:
        logger.stop()
        logger.print(f"\n[bold red]Error:[/bold red] {str(e)}")

@main.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
def detect_duplicates(verbose: bool):
    """Detect and print duplicate files based on their hashes."""
    
    logger = SimpleLogger(verbose=verbose)
    dupes = Dupes(verbose=verbose)
    
    logger.info("Analyzing hashes for duplicates...")
    duplicates = dupes.detect_duplicates(verbose=verbose)

    duplicated_dirs_exist = len(duplicates['dirs'].items()) > 0
    duplicated_files_exist = len(duplicates['files'].items()) > 0

    console.print()
    
    if duplicated_dirs_exist:
        console.print("[bold cyan]Duplicate Folders Found:[/bold cyan]\n")
        
        for idx, (hash_value, dirs) in enumerate(duplicates['dirs'].items(), 1):
            table = Table(title=f"Group {idx}", show_header=False, border_style="cyan")
            table.add_column("Path", style="yellow")
            
            for dir_path in dirs:
                table.add_row(dir_path)
            
            console.print(table)
            console.print(f"[dim]Hash: {hash_value}[/dim]\n")
    else:
        console.print("[green]✓ No duplicate folders found[/green]\n")
    
    if duplicated_files_exist:
        console.print("[bold magenta]Duplicate Files Found:[/bold magenta]\n")
        
        for idx, (hash_value, files) in enumerate(duplicates['files'].items(), 1):
            table = Table(title=f"Group {idx}", show_header=False, border_style="magenta")
            table.add_column("Path", style="yellow")
            
            for file_path in files:
                table.add_row(file_path)
            
            console.print(table)
            console.print(f"[dim]Hash: {hash_value}[/dim]\n")
    else:
        console.print("[green]✓ No duplicate files found[/green]\n")
    
    # Summary
    if duplicated_dirs_exist or duplicated_files_exist:
        logger.warning(
            f"Found {len(duplicates['dirs'])} duplicate folder groups "
            f"and {len(duplicates['files'])} duplicate file groups"
        )
    else:
        logger.success("No duplicates found!")

@main.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
def clear_hashes(verbose: bool):
    """Clear all stored hashes."""
    
    logger = SimpleLogger(verbose=verbose)
    
    if click.confirm("Are you sure you want to clear all stored hashes?"):
        HashHelper.clear_hashes(verbose=verbose)
        logger.success(f"Cleared all hashes from {HASHES_PICKLE_PATH}")
    else:
        logger.info("Operation cancelled")

if __name__ == '__main__':
    main()