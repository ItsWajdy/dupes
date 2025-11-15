"""
Constants used across the duplicate files detector application.
"""

# Path to the pickle file storing hashes of files
HASHES_PICKLE_PATH = "hashes.pickle"

# Dictionary representing the empty state of the hashes pickle
EMPTY_HASHES_PICKLE = {'files': {}, 'dirs': {}}