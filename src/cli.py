import click
from .files_helper import FilesHelper
from .hash_helper import HashHelper
from .constants import HASHES_PICKLE_PATH

@click.group()
def main():
    """A CLI tool to detect duplicate files based on their hashes."""
    pass

@main.command()
@click.option('--verbose', is_flag=True, help='Enable verbose output.')
@click.argument('dirs', nargs=-1, type=click.Path(exists=True), required=True)
def process_dir(verbose: bool, dirs: list[str]):
    """Process the given directories."""

    if verbose:
        click.echo(f"\nLoading existing hashes from {HASHES_PICKLE_PATH}")
    hashes = HashHelper.load_hashes(verbose=verbose)

    for dir in dirs:
        if verbose:
            click.echo(f"\nProcessing directory: {dir}")
        files = FilesHelper.walk_dir(dir, verbose=verbose)
        for file in files:
            hash_value = HashHelper.hash_file(file, verbose=verbose)
            if hash_value in hashes:
                if file not in hashes[hash_value]:
                    hashes[hash_value].append(file)
            else:
                hashes[hash_value] = [file]
    
    HashHelper.save_hashes(hashes, verbose=verbose)

@main.command()
@click.option('--verbose', is_flag=True, help='Enable verbose output.')
def detect_duplicates(verbose: bool):
    """Detect and print duplicate files based on their hashes."""
    hashes = HashHelper.load_hashes(verbose=verbose)

    if verbose:
        click.echo(f"\nLoaded {len(hashes)} unique hashes from {HASHES_PICKLE_PATH}")
    duplicates = {h: paths for h, paths in hashes.items() if len(paths) > 1}

    if duplicates:
        click.echo("Duplicate files found:")
        for hash_value, files in duplicates.items():
            click.echo(f"\nHash: {hash_value}")
            for file in files:
                click.echo(f" - {file}")
    else:
        click.echo("No duplicate files found.")

@main.command()
@click.option('--verbose', is_flag=True, help='Enable verbose output.')
def clear_hashes(verbose: bool):
    """Clear all stored hashes."""
    HashHelper.clear_hashes(verbose=verbose)

if __name__ == '__main__':
    main()
