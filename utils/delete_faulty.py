import os
import sys
from PIL import Image
import numpy as np

# --- Core Logic Functions ---

def get_color_percentage(image_path, target_colors):
    """
    Calculate the total percentage of pixels matching any of the target colors

    Args:
        image_path (str): Path to the image file
        target_colors (list): List of hex color strings to match ('#RRGGBB')

    Returns:
        float: Percentage of pixels matching any target color (0-100), or -1 on error
    """
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        img_array = np.array(img)
        if img_array.ndim != 3 or img_array.shape[2] != 3:
            print(f"Warning: Unexpected image format for {os.path.basename(image_path)}. Shape: {img_array.shape}. Skipping color check.")
            return -1 # Indicate an issue

        pixels = img_array.reshape(-1, 3)
        total_pixels = len(pixels)
        if total_pixels == 0:
            return 0 # Avoid division by zero

        # Convert target hex colors to RGB tuples (set for faster lookup)
        target_rgb_set = set()
        for hex_color in target_colors:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 6:
                try:
                    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                    target_rgb_set.add(rgb)
                except ValueError:
                    print(f"Warning: Invalid hex color '{hex_color}' ignored.")
            else:
                print(f"Warning: Invalid hex color format '{hex_color}' ignored.")

        if not target_rgb_set:
            # print(f"Warning: No valid target colors specified for {image_path}") # Can be noisy
            return 0 # No colors to match

        # Count matching pixels efficiently (using numpy for potential speedup)
        # Create a boolean mask for each target color and combine them
        masks = [np.all(pixels == color, axis=1) for color in target_rgb_set]
        combined_mask = np.logical_or.reduce(masks)
        matching_pixels = np.sum(combined_mask)

        return (matching_pixels / total_pixels) * 100

    except FileNotFoundError:
        print(f"Error: File not found {image_path}")
        return -1
    except Exception as e:
        print(f"Error processing {os.path.basename(image_path)}: {e}")
        return -1

def _process_single_directory_for_faulty(directory, deletion_rules):
    """
    Internal helper: processes a single directory based on color dominance rules.
    """
    deleted_count = 0
    kept_count = 0
    error_count = 0

    print(f"Processing directory: {directory}")
    if not os.path.isdir(directory):
        print(f"Error: Directory not found: {directory}")
        return 0, 0, 1 # Return counts: deleted, kept, error

    for filename in os.listdir(directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tif', '.tiff')):
            filepath = os.path.join(directory, filename)
            if not os.path.isfile(filepath):
                continue

            delete_file = False
            processed_successfully = True

            for colors, threshold in deletion_rules:
                percentage = get_color_percentage(filepath, colors)

                if percentage == -1:
                    # print(f"Skipping deletion check for {filename} due to processing error.") # Error already printed in get_color_percentage
                    error_count += 1
                    processed_successfully = False
                    break # Stop checking rules if error

                if percentage > threshold:
                    print(f"  - Deleting {filename}: Color(s) {colors} cover {percentage:.2f}% (> {threshold}%)")
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                        delete_file = True
                        break # Deleted, no need to check other rules
                    except Exception as e:
                        print(f"  - Failed to delete {filename}: {e}")
                        error_count += 1
                        processed_successfully = False
                        break # Stop checking rules if deletion failed

            if processed_successfully and not delete_file:
                kept_count += 1

    print(f"Finished processing {os.path.basename(directory)}: Deleted: {deleted_count}, Kept: {kept_count}, Errors/Skipped: {error_count}")
    print("-" * 20)
    return deleted_count, kept_count, error_count

# --- Main Callable Function ---

def run_faulty_deletion(base_dir, deletion_rules):
    """
    Iterates through subdirectories of base_dir and deletes images based on color rules.

    Args:
        base_dir (str): The root directory containing subdirectories with images.
        deletion_rules (list): List of tuples: ([list_of_hex_colors], threshold_percentage).
                               Example: [(['#FFFFFF'], 4)]

    Returns:
        tuple: (total_deleted, total_kept, total_errors) across all subdirectories.
    """
    total_deleted = 0
    total_kept = 0
    total_errors = 0
    processed_dirs = 0

    print(f"Starting faulty image deletion process in base directory: {base_dir}")
    print(f"Using deletion rules: {deletion_rules}")
    print("=" * 40)

    if not os.path.isdir(base_dir):
        print(f"Error: Base directory '{base_dir}' not found. Exiting.")
        return 0, 0, 1 # Indicate base dir error

    for item_name in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item_name)
        if os.path.isdir(item_path):
            processed_dirs += 1
            d, k, e = _process_single_directory_for_faulty(item_path, deletion_rules)
            total_deleted += d
            total_kept += k
            total_errors += e
        # else:
            # Optional: Log skipped non-directory items if needed
            # print(f"Skipping non-directory item: {item_name}")

    print("=" * 40)
    print("Overall Faulty Deletion Summary:")
    print(f"  Processed {processed_dirs} subdirectories.")
    print(f"  Total Deleted: {total_deleted}")
    print(f"  Total Kept: {total_kept}")
    if total_errors > 0:
        print(f"  Total Errors/Skipped Files: {total_errors}")
    print("=" * 40)

    return total_deleted, total_kept, total_errors

# --- Direct Execution Block (for standalone testing) ---

# if __name__ == "__main__":
#     # Define default parameters for standalone execution
#     DEFAULT_BASE_DIR = r"C:\Users\karol\Downloads\dane\niezabudowane\zdjecia"
#     # Example: Delete if pure white ('#FFFFFF') is more than 4%
#     DEFAULT_DELETION_RULES = [
#         (['#FFFFFF'], 4)
#         # Add more rules here if needed, e.g.
#         # (['#000000'], 50) # Delete if black is more than 50%
#     ]

#     # Check if the default base directory exists before running
#     if not os.path.isdir(DEFAULT_BASE_DIR):
#         print(f"Error: Default base directory '{DEFAULT_BASE_DIR}' not found.")
#         print("Please edit the DEFAULT_BASE_DIR variable in the script or ensure the directory exists.")
#         sys.exit(1) # Exit if the default path is invalid

#     # Run the main processing function
#     run_faulty_deletion(DEFAULT_BASE_DIR, DEFAULT_DELETION_RULES)