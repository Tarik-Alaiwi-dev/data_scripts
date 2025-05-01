import os
import re
import sys

# --- Core Logic Function ---

def synchronize_renumbering(dir1, dir2, prefix="cell_", extension=".png"):
    """
    Renumbers files matching prefix/extension in two directories
    so they are sequential and synchronized based on the union of their numbers.
    Uses temporary files to avoid conflicts during renaming.

    Args:
        dir1 (str): Path to the first directory.
        dir2 (str): Path to the second directory.
        prefix (str): Filename prefix to match.
        extension (str): Filename extension to match.

    Returns:
        tuple: (renamed_count, error_count) for this pair.
    """
    renamed_count = 0
    error_count = 0
    base_dir1 = os.path.basename(dir1)
    base_dir2 = os.path.basename(dir2)
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+){re.escape(extension)}$")

    def get_ids(directory):
        """Helper to get numeric IDs from filenames."""
        ids = set()
        try:
            for filename in os.listdir(directory):
                match = pattern.match(filename)
                if match:
                    try:
                        ids.add(int(match.group(1)))
                    except ValueError:
                        print(f"Warning: Could not parse number from {filename} in {os.path.basename(directory)}")
            return ids
        except FileNotFoundError:
            print(f"Warning: Directory not found while getting IDs: {directory}")
            return set()
        except Exception as e:
            print(f"Error reading directory {directory} while getting IDs: {e}")
            nonlocal error_count # Modify outer scope error count
            error_count += 1
            return set()

    try:
        all_ids = get_ids(dir1).union(get_ids(dir2))
        if not all_ids:
            # print(f"  No files matching pattern found in either directory for pair ({base_dir1}, {base_dir2}). Skipping renumber.")
            return 0, error_count # Return current counts, might have had read errors

        sorted_ids = sorted(list(all_ids))
        id_mapping = {old_id: new_id for new_id, old_id in enumerate(sorted_ids, start=1)}

        files_to_rename = []
        for old_id in sorted_ids:
            new_id = id_mapping[old_id]
            if old_id != new_id:
                files_to_rename.append((old_id, new_id))

        if not files_to_rename:
            print(f"  Files already sequentially numbered in pair ({base_dir1}, {base_dir2}). No renumbering needed.")
            return 0, error_count

        print(f"  Renumbering required for pair ({base_dir1}, {base_dir2}).")

        # Step 1: Rename to temporary names
        temp_rename_success = {}
        step1_errors = 0
        for old_id, new_id in files_to_rename:
            for directory in [dir1, dir2]:
                old_filename = f"{prefix}{old_id}{extension}"
                old_path = os.path.join(directory, old_filename)
                if os.path.exists(old_path):
                    temp_filename = f"{prefix}{old_id}_TEMP_{new_id}{extension}"
                    temp_path = os.path.join(directory, temp_filename)
                    try:
                        if not os.path.exists(temp_path):
                            os.rename(old_path, temp_path)
                            temp_rename_success[(directory, old_id)] = temp_path
                        else:
                            # Assume temp file is from previous run, add to dict for step 2 check
                            temp_rename_success[(directory, old_id)] = temp_path
                            # print(f"Warning: Temporary file {temp_path} already exists. Will attempt final rename.")
                    except OSError as e:
                        print(f"  Error (Step 1) renaming {old_filename} to temp in {os.path.basename(directory)}: {e}")
                        step1_errors += 1

        # Step 2: Rename temporary files to final names
        step2_errors = 0
        current_renamed_count = 0
        for (directory, old_id), temp_path in temp_rename_success.items():
            new_id = id_mapping[old_id]
            new_filename = f"{prefix}{new_id}{extension}"
            new_path = os.path.join(directory, new_filename)
            dir_base_name = os.path.basename(directory)

            try:
                # Check if the temp file actually exists (might have failed step 1)
                if not os.path.exists(temp_path):
                    # print(f"  Skipping final rename for {prefix}{old_id}{extension} in {dir_base_name}: Temp file {os.path.basename(temp_path)} missing.")
                    continue # Skip if temp file doesn't exist

                # Avoid renaming if final target exists *and* it's not the temp file itself
                if os.path.exists(new_path) and os.path.abspath(new_path) != os.path.abspath(temp_path):
                     print(f"Warning: Final target file {new_path} already exists. Removing before rename.")
                     try:
                         os.remove(new_path)
                     except OSError as e_rem:
                         print(f"  Error removing existing target file {new_path}: {e_rem}")
                         step2_errors += 1
                         continue # Skip rename if couldn't remove conflicting file

                os.rename(temp_path, new_path)
                print(f"  Renamed {os.path.basename(temp_path)} -> {new_filename} in {dir_base_name}")
                current_renamed_count += 1
            except OSError as e:
                print(f"  Error (Step 2) renaming {os.path.basename(temp_path)} to {new_filename} in {dir_base_name}: {e}")
                step2_errors += 1

        renamed_count = current_renamed_count # Update total renamed count for this pair
        error_count += step1_errors + step2_errors # Add errors from both steps

        if renamed_count > 0:
            print(f"  Renumbering summary for pair ({base_dir1}, {base_dir2}): Renamed {renamed_count} files.")
        if error_count > 0:
             print(f"  Renumbering errors for pair ({base_dir1}, {base_dir2}): {error_count}")


        return renamed_count, error_count

    except Exception as e:
        print(f"An unexpected error occurred processing pair ({base_dir1}, {base_dir2}): {e}")
        return renamed_count, error_count + 1 # Return current counts + 1 critical error

# --- Main Callable Function ---

def run_renumbering(base_dir1, base_dir2, prefix="cell_", extension=".png"):
    """
    Finds corresponding subdirectories in two base directories and synchronizes
    file numbering within each pair based on prefix and extension.

    Args:
        base_dir1 (str): Path to the first base directory.
        base_dir2 (str): Path to the second base directory.
        prefix (str): Filename prefix to match.
        extension (str): Filename extension to match.

    Returns:
        tuple: (total_renamed_files, total_pair_errors, skipped_pairs)
    """
    total_renamed = 0
    total_pair_errors = 0
    processed_pairs_count = 0
    skipped_non_dir = 0
    skipped_missing_pair = 0

    print(f"Starting synchronized renumbering for pattern '{prefix}*{extension}'")
    print(f"in corresponding subdirectories of:")
    print(f"  Base Dir 1: {base_dir1}")
    print(f"  Base Dir 2: {base_dir2}")
    print("=" * 50)

    # Basic checks for base directories
    if not os.path.isdir(base_dir1):
        print(f"Error: Base directory 1 not found: {base_dir1}")
        return 0, 1, 0 # Indicate critical error
    if not os.path.isdir(base_dir2):
        print(f"Error: Base directory 2 not found: {base_dir2}")
        return 0, 1, 0 # Indicate critical error

    try:
        items_in_base1 = os.listdir(base_dir1)
    except OSError as e:
        print(f"Error listing directory {base_dir1}: {e}")
        return 0, 1, 0 # Indicate critical error

    for item_name in items_in_base1:
        path_in_dir1 = os.path.join(base_dir1, item_name)

        if os.path.isdir(path_in_dir1):
            path_in_dir2 = os.path.join(base_dir2, item_name)

            if os.path.isdir(path_in_dir2):
                print(f"Processing pair for renumbering: '{item_name}'")
                renamed, errors = synchronize_renumbering(path_in_dir1, path_in_dir2, prefix, extension)
                total_renamed += renamed
                total_pair_errors += errors
                processed_pairs_count += 1
                print("-" * 30)
            else:
                print(f"Skipping '{item_name}': Corresponding directory not found in {base_dir2}")
                skipped_missing_pair += 1
                print("-" * 30)
        else:
            skipped_non_dir += 1

    print("=" * 50)
    print("Overall Renumbering Summary:")
    print(f"  Processed {processed_pairs_count} pair(s) of corresponding subdirectories.")
    print(f"  Total files renamed across all pairs: {total_renamed}")
    if total_pair_errors > 0:
         print(f"  Total errors during pair processing: {total_pair_errors}")
    if skipped_missing_pair > 0:
        print(f"  Skipped {skipped_missing_pair} item(s) due to missing corresponding subdirectory.")
    if skipped_non_dir > 0:
        print(f"  Skipped {skipped_non_dir} non-directory item(s) found in {base_dir1}.")
    print("=" * 50)

    return total_renamed, total_pair_errors, skipped_missing_pair + skipped_non_dir


# --- Direct Execution Block (for standalone testing) ---

# if __name__ == "__main__":
#     # Define default parameters for standalone execution
#     DEFAULT_BASE_ZDJECIA_DIR = r"C:\Users\karol\Downloads\dane\niezabudowane\zdjecia"
#     DEFAULT_BASE_MAPY_DIR = r"C:\Users\karol\Downloads\dane\niezabudowane\mapy"
#     DEFAULT_PREFIX = "cell_"
#     DEFAULT_EXTENSION = ".png"

#     # Run the main processing function with default paths
#     run_renumbering(DEFAULT_BASE_ZDJECIA_DIR, DEFAULT_BASE_MAPY_DIR, DEFAULT_PREFIX, DEFAULT_EXTENSION)