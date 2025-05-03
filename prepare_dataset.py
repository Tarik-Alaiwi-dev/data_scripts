import os
import datasets
from PIL import Image
import re
import logging

BASE_DATA_PATH = r"C:\Users\karol\Desktop\duuuzo_danych"
HF_DATASET_NAME = "TarikKarol/mag-map-v2"
SPLIT_DIRS = ["niezabudowane", "zabudowane"]
SPLIT_MAPPING = {"niezabudowane": 0, "zabudowane": 1}

TYPES = ["mapy", "zdjecia"]
CELL_PATTERN = re.compile(r"^cell_(\d+)\.png$")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_examples():
    skipped_pairs = 0
    generated_count = 0

    for split_dir_name in SPLIT_DIRS:
        photos_split_path = os.path.join(BASE_DATA_PATH, split_dir_name, "zdjecia")
        maps_split_path = os.path.join(BASE_DATA_PATH, split_dir_name, "mapy")

        if not os.path.isdir(photos_split_path):
            logging.warning(f"'zdjecia' directory not found for split '{split_dir_name}', skipping: {photos_split_path}")
            continue
        if not os.path.isdir(maps_split_path):
            logging.warning(f"'mapy' directory not found for split '{split_dir_name}', skipping pairing: {maps_split_path}")
            continue

        split_value = SPLIT_MAPPING.get(split_dir_name)
        if split_value is None:
             logging.error(f"Unexpected split directory name '{split_dir_name}' not found in SPLIT_MAPPING. Skipping split.")
             continue

        for city_name in os.listdir(photos_split_path):
            photos_city_path = os.path.join(photos_split_path, city_name)
            maps_city_path = os.path.join(maps_split_path, city_name)

            if not os.path.isdir(photos_city_path):
                continue

            if not os.path.isdir(maps_city_path):
                logging.warning(f"'mapy' directory not found for city '{city_name}' in split '{split_dir_name}', skipping city: {maps_city_path}")
                continue

            for filename in os.listdir(photos_city_path):
                match = CELL_PATTERN.match(filename)
                if match:
                    cell_id_str = match.group(1)
                    try:
                        cell_id = int(cell_id_str)
                    except ValueError:
                        logging.warning(f"Could not parse cell ID from {filename} in {photos_city_path}, skipping.")
                        continue

                    photo_path = os.path.join(photos_city_path, filename)
                    map_filename = filename
                    map_path = os.path.join(maps_city_path, map_filename)

                    if os.path.isfile(map_path):
                        yield {
                            "image_map": map_path,
                            "image_photo": photo_path,
                            "split_name": split_value,
                            "city": city_name,
                            "cell_id": cell_id
                        }
                        generated_count += 1
                    else:
                        logging.warning(f"Missing map pair for {photo_path}. Expected: {map_path}")
                        skipped_pairs += 1

    logging.info(f"Finished generating examples. Generated: {generated_count}, Skipped due to missing pairs: {skipped_pairs}")

logging.info("Starting dataset creation...")

features = datasets.Features({
    "image_map": datasets.Image(),
    "image_photo": datasets.Image(),
    "split_name": datasets.Value("int32"),
    "city": datasets.Value("string"),
    "cell_id": datasets.Value("int32"),
})

my_dataset = datasets.Dataset.from_generator(
    generate_examples,
    features=features
)

logging.info(f"Dataset created with {len(my_dataset)} examples.")
print("\nDataset Schema:")
print(my_dataset)
print("\nFirst example:")
print(my_dataset[0] if len(my_dataset) > 0 else "Dataset is empty.")

logging.info(f"Pushing dataset to Hub: {HF_DATASET_NAME}")
try:
    my_dataset.push_to_hub(HF_DATASET_NAME, private=False)
    logging.info("Dataset push successful!")
    logging.info(f"Access your dataset at: https://huggingface.co/datasets/{HF_DATASET_NAME}")
except Exception as e:
    logging.error(f"Failed to push dataset to Hub: {e}")