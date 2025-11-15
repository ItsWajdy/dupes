import click
from .dupes import Dupes
from .hash_helper import HashHelper
from .constants import HASHES_PICKLE_PATH

@click.group()
def main():
    """A CLI tool to detect duplicate files based on their hashes."""
    pass

@main.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
@click.argument('dirs', nargs=-1, type=click.Path(exists=True), required=True)
def process_dir(verbose: bool, dirs: list[str]):
    """Process the given directories."""

    dupes = Dupes(verbose=verbose)
    for dir in dirs:
        if verbose:
            click.echo(f"\nProcessing directory: {dir}")
        
        dupes.reursive_hash(dir, verbose)

@main.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
def detect_duplicates(verbose: bool):
    """Detect and print duplicate files based on their hashes."""

    dupes = Dupes(verbose=verbose)
    duplicates = dupes.detect_duplicates(verbose=verbose)

    duplicated_dirs_exist = len(duplicates['dirs'].items()) > 0
    duplicated_files_exist = len(duplicates['files'].items()) > 0

    if duplicated_dirs_exist:
        click.echo("\nDuplicate folders found:")
        for hash_value, dirs in duplicates['dirs'].items():
            click.echo(f"\nHash: {hash_value}")
            for dir in dirs:
                click.echo(f" - {dir}")
    else:
        click.echo("No duplicate folders found.")
    
    if duplicated_files_exist:
        click.echo("\n\n\nDuplicate files found:")
        for hash_value, files in duplicates['files'].items():
            click.echo(f"\nHash: {hash_value}")
            for file in files:
                click.echo(f" - {file}")
    else:
        click.echo("No duplicate files found.")

@main.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
def clear_hashes(verbose: bool):
    """Clear all stored hashes."""
    try:
        HashHelper.clear_hashes(verbose=verbose)
    except Exception as e:
        click.echo(f"Error clearing hashes: {e}", err=True)

if __name__ == '__main__':
    main()
