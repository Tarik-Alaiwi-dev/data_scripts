import os
import sys

# --- Core Logic Function ---

def find_and_delete_unmatched_files(dir1, dir2, prefix="cell_", extension=".png"):
    """
    Compares files in two directories based on prefix/extension
    and deletes files present in one but not the other.
    Assumes dir1 and dir2 are valid directory paths.

    Args:
        dir1 (str): Path to the first directory.
        dir2 (str): Path to the second directory.
        prefix (str): Filename prefix to match.
        extension (str): Filename extension to match.

    Returns:
        tuple: (deleted_count_dir1, deleted_count_dir2, error_count)
    """
    deleted_count_dir1 = 0
    deleted_count_dir2 = 0
    error_count = 0
    base_dir1 = os.path.basename(dir1)
    base_dir2 = os.path.basename(dir2)

    try:
        files_dir1 = set([f for f in os.listdir(dir1) if f.startswith(prefix) and f.endswith(extension)])
        files_dir2 = set([f for f in os.listdir(dir2) if f.startswith(prefix) and f.endswith(extension)])

        only_in_dir1 = files_dir1 - files_dir2
        only_in_dir2 = files_dir2 - files_dir1

        for filename in only_in_dir1:
            filepath = os.path.join(dir1, filename)
            try:
                os.remove(filepath)
                print(f"  - Deleted {filename} from {base_dir1} (no match in {base_dir2})")
                deleted_count_dir1 += 1
            except OSError as e:
                print(f"  - Error deleting {filepath}: {e}")
                error_count += 1

        for filename in only_in_dir2:
            filepath = os.path.join(dir2, filename)
            try:
                os.remove(filepath)
                print(f"  - Deleted {filename} from {base_dir2} (no match in {base_dir1})")
                deleted_count_dir2 += 1
            except OSError as e:
                print(f"  - Error deleting {filepath}: {e}")
                error_count += 1

        if deleted_count_dir1 > 0 or deleted_count_dir2 > 0 or error_count > 0:
            print(f"    Cleanup summary for pair ({base_dir1}, {base_dir2}):")
            print(f"      Deleted from {base_dir1}: {deleted_count_dir1}")
            print(f"      Deleted from {base_dir2}: {deleted_count_dir2}")
            if error_count > 0:
                print(f"      Errors: {error_count}")
        else:
            print(f"    No unmatched files found in pair ({base_dir1}, {base_dir2}).")

        return deleted_count_dir1, deleted_count_dir2, error_count

    except FileNotFoundError as e:
        print(f"Error: Could not access directory: {e}. Skipping pair ({base_dir1}, {base_dir2}).")
        return 0, 0, 1 # Indicate error occurred for this pair
    except Exception as e:
        print(f"An unexpected error occurred processing pair ({base_dir1}, {base_dir2}): {e}")
        return 0, 0, 1 # Indicate error occurred for this pair

# --- Main Callable Function ---

def run_unpaired_deletion(base_dir1, base_dir2, prefix="cell_", extension=".png"):
    """
    Finds corresponding subdirectories in two base directories and deletes
    unmatched files within each pair based on prefix and extension.

    Args:
        base_dir1 (str): Path to the first base directory.
        base_dir2 (str): Path to the second base directory.
        prefix (str): Filename prefix to match.
        extension (str): Filename extension to match.

    Returns:
        tuple: (total_deleted_dir1, total_deleted_dir2, total_pair_errors, skipped_pairs)
    """
    total_deleted_dir1 = 0
    total_deleted_dir2 = 0
    total_pair_errors = 0
    processed_pairs_count = 0
    skipped_non_dir = 0
    skipped_missing_pair = 0

    print(f"Starting unmatched file cleanup between corresponding subdirectories of:")
    print(f"  Base Dir 1: {base_dir1}")
    print(f"  Base Dir 2: {base_dir2}")
    print(f"  Matching pattern: {prefix}*{extension}")
    print("=" * 50)

    # Basic checks for base directories
    if not os.path.isdir(base_dir1):
        print(f"Error: Base directory 1 not found: {base_dir1}")
        return 0, 0, 1, 0 # Indicate critical error
    if not os.path.isdir(base_dir2):
        print(f"Error: Base directory 2 not found: {base_dir2}")
        return 0, 0, 1, 0 # Indicate critical error

    try:
        items_in_base1 = os.listdir(base_dir1)
    except OSError as e:
        print(f"Error listing directory {base_dir1}: {e}")
        return 0, 0, 1, 0 # Indicate critical error

    for item_name in items_in_base1:
        path_in_dir1 = os.path.join(base_dir1, item_name)

        if os.path.isdir(path_in_dir1):
            path_in_dir2 = os.path.join(base_dir2, item_name)

            if os.path.isdir(path_in_dir2):
                print(f"Processing pair: '{item_name}'")
                d1, d2, err = find_and_delete_unmatched_files(path_in_dir1, path_in_dir2, prefix, extension)
                total_deleted_dir1 += d1
                total_deleted_dir2 += d2
                total_pair_errors += err
                processed_pairs_count += 1
                print("-" * 30)
            else:
                print(f"Skipping '{item_name}': Corresponding directory not found in {base_dir2}")
                skipped_missing_pair += 1
                print("-" * 30)
        else:
            skipped_non_dir += 1

    print("=" * 50)
    print("Overall Unpaired Deletion Summary:")
    print(f"  Processed {processed_pairs_count} pair(s) of corresponding subdirectories.")
    print(f"  Total files deleted from {os.path.basename(base_dir1)} subdirs: {total_deleted_dir1}")
    print(f"  Total files deleted from {os.path.basename(base_dir2)} subdirs: {total_deleted_dir2}")
    if total_pair_errors > 0:
        print(f"  Total errors during pair processing: {total_pair_errors}")
    if skipped_missing_pair > 0:
        print(f"  Skipped {skipped_missing_pair} item(s) due to missing corresponding subdirectory.")
    if skipped_non_dir > 0:
        print(f"  Skipped {skipped_non_dir} non-directory item(s) found in {base_dir1}.")
    print("=" * 50)

    return total_deleted_dir1, total_deleted_dir2, total_pair_errors, skipped_missing_pair + skipped_non_dir


# # --- Direct Execution Block (for standalone testing) ---

# if __name__ == "__main__":
#     # Define default parameters for standalone execution
#     DEFAULT_BASE_ZDJECIA_DIR = r"C:\Users\karol\Downloads\dane\niezabudowane\zdjecia"
#     DEFAULT_BASE_MAPY_DIR = r"C:\Users\karol\Downloads\dane\niezabudowane\mapy"
#     DEFAULT_PREFIX = "cell_"
#     DEFAULT_EXTENSION = ".png"

#     # Run the main processing function with default paths
#     run_unpaired_deletion(DEFAULT_BASE_ZDJECIA_DIR, DEFAULT_BASE_MAPY_DIR, DEFAULT_PREFIX, DEFAULT_EXTENSION)
