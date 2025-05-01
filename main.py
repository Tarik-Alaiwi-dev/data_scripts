# main.py
import os
import sys

# Assuming the edited scripts are in a 'utils' subdirectory
# relative to main.py, or adjust the import path as needed.
try:
    import utils.delete_faulty as delete_faulty
    import utils.delete_unpaired as delete_unpaired
    import utils.fix_order as fix_order
except ImportError:
    print("Error: Could not import utility modules.")
    print("Ensure delete_faulty.py, delete_unpaired.py, and fix_order.py")
    print("are present in a 'utils' subdirectory or adjust the import paths.")
    sys.exit(1)

# --- Configuration ---

# List of tuples, where each tuple is (base_zdjecia_directory, base_mapy_directory)
# These are the PARENT directories containing the actual subdirectories to process.
BASE_DIRECTORY_PAIRS = [
    # (r"C:\Users\karol\Downloads\dane\niezabudowane", r"C:\Users\karol\Downloads\dane\niezabudowane"), # Example if zdjecia/mapy are inside niezabudowane
    # (r"C:\Users\karol\Downloads\dane\zabudowane", r"C:\Users\karol\Downloads\dane\zabudowane")       # Example if zdjecia/mapy are inside zabudowane
    # --- OR ---
    # If 'zdjecia' and 'mapy' are directly inside 'dane':
    # (r"C:\Users\karol\Downloads\dane", r"C:\Users\karol\Downloads\dane")
    # The script will then look for pairs like 'niezabudowane/zdjecia' vs 'niezabudowane/mapy'
    # inside the 'dane' directory. Adjust these paths based on your ACTUAL structure.

    # Based on your original paths, it seems like this might be what you intended:
    # List of pairs of directories where the *immediate children* should be processed pairwise
    # (PARENT_OF_ZDJECIA_FOLDERS, PARENT_OF_MAPY_FOLDERS)
    # This assumes you have:
    # C:\Users\karol\Downloads\dane\niezabudowane\zdjecia\SUBDIR1
    # C:\Users\karol\Downloads\dane\niezabudowane\zdjecia\SUBDIR2
    # C:\Users\karol\Downloads\dane\niezabudowane\mapy\SUBDIR1
    # C:\Users\karol\Downloads\dane\niezabudowane\mapy\SUBDIR2
    # etc.
    # *If this structure is correct*, use these paths:
    (r"C:\Users\karol\Downloads\dane\niezabudowane\zdjecia", r"C:\Users\karol\Downloads\dane\niezabudowane\mapy"),
    (r"C:\Users\karol\Downloads\dane\zabudowane\zdjecia", r"C:\Users\karol\Downloads\dane\zabudowane\mapy")

]


# Faulty deletion rules (applied only to the 'zdjecia' subdirectories)
FAULTY_RULES = [
    (['#FFFFFF'], 4) # Example: Delete if > 4% white
]

# File matching pattern for unpaired deletion and renumbering within subdirectories
FILE_PREFIX = "cell_"
FILE_EXTENSION = ".png"

# --- Execution ---
if __name__ == "__main__":
    print("Starting data cleaning pipeline for subdirectories within base pairs...")
    print("=" * 70)

    # Loop through each configured pair of BASE directories
    for index, base_pair in enumerate(BASE_DIRECTORY_PAIRS):
        base_zdjecia_path, base_mapy_path = base_pair
        # Create a label for cleaner output, focusing on the base paths being processed
        pair_label = f"Base Pair {index + 1} ('{os.path.basename(base_zdjecia_path)}' & '{os.path.basename(base_mapy_path)}')" # Simplified label

        print(f"\n--- Processing Base Pair: {pair_label} ---\n")
        print(f"  Zdjecia Base: {base_zdjecia_path}")
        print(f"  Mapy Base:    {base_mapy_path}")
        print("-" * 40)


        # --- Base Directory Existence Checks ---
        base_zdjecia_exists = os.path.isdir(base_zdjecia_path)
        base_mapy_exists = os.path.isdir(base_mapy_path)

        if not base_zdjecia_exists:
            print(f"Error: Base Zdjecia directory not found: {base_zdjecia_path}")
            print(f"Skipping ALL steps for {pair_label}.")
            print("-" * 70)
            continue # Move to the next pair

        # --- Step 1: Delete faulty images in subdirectories of the ZDJECIA base path ---
        # Calls the runner function which iterates through subdirs
        print(f"\nSTEP 1: Deleting faulty images in subdirectories of '{base_zdjecia_path}'...\n")
        # Note: run_faulty_deletion iterates through subdirs of the given base_dir
        deleted_f, kept_f, errors_f = delete_faulty.run_faulty_deletion(
            base_dir=base_zdjecia_path,
            deletion_rules=FAULTY_RULES
        )
        # Summary is printed by the run_faulty_deletion function


        # --- Step 2: Delete unpaired files between corresponding subdirectories ---
        if not base_mapy_exists:
             print(f"\nSTEP 2 & 3 SKIPPED: Base Mapy directory not found: {base_mapy_path}")
        else:
            # Calls the runner function which finds and processes corresponding subdirs
            print(f"\nSTEP 2: Deleting unpaired files between corresponding subdirs of '{base_zdjecia_path}' and '{base_mapy_path}'...\n")
            # Note: run_unpaired_deletion iterates through common subdirs
            deleted_unp_z, deleted_unp_m, errors_unp, skipped_unp = delete_unpaired.run_unpaired_deletion(
                base_dir1=base_zdjecia_path,
                base_dir2=base_mapy_path,
                prefix=FILE_PREFIX,
                extension=FILE_EXTENSION
            )
            # Summary is printed by run_unpaired_deletion

            # --- Step 3: Fix numbering order between corresponding subdirectories ---
            # Calls the runner function which finds and processes corresponding subdirs
            print(f"\nSTEP 3: Renumbering files between corresponding subdirs of '{base_zdjecia_path}' and '{base_mapy_path}'...\n")
            # Note: run_renumbering iterates through common subdirs
            renamed_count, errors_renum, skipped_renum = fix_order.run_renumbering(
                base_dir1=base_zdjecia_path,
                base_dir2=base_mapy_path,
                prefix=FILE_PREFIX,
                extension=FILE_EXTENSION
            )
            # Summary is printed by run_renumbering

        print(f"\n--- Finished processing {pair_label} ---")
        print("-" * 70)


    print("\nOverall data cleaning pipeline finished for all configured base pairs.")
    print("=" * 70)