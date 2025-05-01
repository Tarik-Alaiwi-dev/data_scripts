import os
import sys

try:
    import utils.delete_faulty as delete_faulty
    import utils.delete_unpaired as delete_unpaired
    import utils.fix_order as fix_order
except ImportError:
    print("Error: Could not import utility modules.")
    print("Ensure delete_faulty.py, delete_unpaired.py, and fix_order.py")
    print("are present in a 'utils' subdirectory or adjust the import paths.")
    sys.exit(1)


BASE_DIRECTORY_PAIRS = [
    (r"C:\Users\karol\Downloads\dane\niezabudowane\zdjecia", r"C:\Users\karol\Downloads\dane\niezabudowane\mapy"),
    (r"C:\Users\karol\Downloads\dane\zabudowane\zdjecia", r"C:\Users\karol\Downloads\dane\zabudowane\mapy")

]


FAULTY_RULES = [
    (['#FFFFFF'], 4)
]


FILE_PREFIX = "cell_"
FILE_EXTENSION = ".png"


if __name__ == "__main__":
    print("Starting data cleaning pipeline for subdirectories within base pairs...")
    print("=" * 70)

    for index, base_pair in enumerate(BASE_DIRECTORY_PAIRS):
        base_zdjecia_path, base_mapy_path = base_pair
        pair_label = f"Base Pair {index + 1} ('{os.path.basename(base_zdjecia_path)}' & '{os.path.basename(base_mapy_path)}')"

        print(f"\n--- Processing Base Pair: {pair_label} ---\n")
        print(f"  Zdjecia Base: {base_zdjecia_path}")
        print(f"  Mapy Base:    {base_mapy_path}")
        print("-" * 40)


        base_zdjecia_exists = os.path.isdir(base_zdjecia_path)
        base_mapy_exists = os.path.isdir(base_mapy_path)

        if not base_zdjecia_exists:
            print(f"Error: Base Zdjecia directory not found: {base_zdjecia_path}")
            print(f"Skipping ALL steps for {pair_label}.")
            print("-" * 70)
            continue


        print(f"\nSTEP 1: Deleting faulty images in subdirectories of '{base_zdjecia_path}'...\n")
        deleted_f, kept_f, errors_f = delete_faulty.run_faulty_deletion(
            base_dir=base_zdjecia_path,
            deletion_rules=FAULTY_RULES
        )


        if not base_mapy_exists:
             print(f"\nSTEP 2 & 3 SKIPPED: Base Mapy directory not found: {base_mapy_path}")
        else:
            print(f"\nSTEP 2: Deleting unpaired files between corresponding subdirs of '{base_zdjecia_path}' and '{base_mapy_path}'...\n")
            deleted_unp_z, deleted_unp_m, errors_unp, skipped_unp = delete_unpaired.run_unpaired_deletion(
                base_dir1=base_zdjecia_path,
                base_dir2=base_mapy_path,
                prefix=FILE_PREFIX,
                extension=FILE_EXTENSION
            )

            print(f"\nSTEP 3: Renumbering files between corresponding subdirs of '{base_zdjecia_path}' and '{base_mapy_path}'...\n")
            renamed_count, errors_renum, skipped_renum = fix_order.run_renumbering(
                base_dir1=base_zdjecia_path,
                base_dir2=base_mapy_path,
                prefix=FILE_PREFIX,
                extension=FILE_EXTENSION
            )

        print(f"\n--- Finished processing {pair_label} ---")
        print("-" * 70)


    print("\nOverall data cleaning pipeline finished for all configured base pairs.")
    print("=" * 70)