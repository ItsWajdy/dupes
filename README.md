# Duplicate Files Detector

`dupes` is a command-line interface (CLI) tool designed to detect duplicate files within specified directories by comparing their cryptographic hashes. This tool helps you identify and manage redundant files on your system.

## Features

- **Hash-based Detection**: Identifies duplicate files by comparing their SHA256 hashes, ensuring accuracy.
- **Directory Processing**: Recursively scans one or more directories to find all files.
- **Persistent Hash Storage**: Stores computed hashes to avoid re-hashing files that haven't changed, speeding up subsequent scans.
- **Clear Hashes**: Option to clear all stored hashes.
- **Verbose Output**: Provides detailed output during processing for better insights.

## Installation

You can install the project in editable mode:

```bash
git clone https://github.com/ItsWajdy/dupes.git
cd dupes
pip install -e .
```

## Usage

The `dupes` tool provides several commands to manage and detect duplicate files.

### `dupes process-dir [DIRS...]`

Processes one or more directories, calculates file hashes, and stores them. If a file's hash already exists, its path is added to the list of files with that hash.

**Arguments:**

- `DIRS`: One or more paths to the directories you want to process.

**Options:**

- `--verbose`: Enable verbose output to see detailed processing information.

**Example:**

```bash
dupes process-dir /path/to/your/directory1 /path/to/your/directory2 --verbose
```

### `dupes detect-duplicates`

Detects and prints all duplicate files based on the currently stored hashes.

**Options:**

- `--verbose`: Enable verbose output to see detailed information about loaded hashes.

**Example:**

```bash
dupes detect-duplicates --verbose
```

### `dupes clear-hashes`

Clears all previously stored hashes. This is useful if you want to start a fresh scan or if your file system has changed significantly.

**Options:**

- `--verbose`: Enable verbose output to confirm the clearing of hashes.

**Example:**

```bash
dupes clear-hashes --verbose
```

## How it Works

1.  **Hashing**: For each file in the specified directories, the tool calculates a SHA256 hash.
2.  **Storage**: These hashes and their corresponding file paths are stored in a persistent pickle file (`hashes.pickle`) to optimize future scans.
3.  **Detection**: When `detect-duplicates` is run, it compares the stored hashes. If multiple files share the same hash, they are identified as duplicates.

## Development

To contribute to `dupes`, follow these steps:

1.  Fork the repository.
2.  Clone your forked repository:
    ```bash
    git clone https://github.com/ItsWajdy/dupes.git
    cd dupes
    ```
3.  Create a virtual environment and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -e .
    pip install -r requirements.txt
    ```
4.  Make your changes and test them.
5.  Commit your changes and push to your fork.
6.  Open a pull request.
