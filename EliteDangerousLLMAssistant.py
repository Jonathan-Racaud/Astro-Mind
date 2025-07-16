import json
import os

from dataclasses import asdict

from src.extract_ship import extract_ship_data

from src.ship import extract_all_ship_information
from src.equipment import extract_all_equipment_information
from src.weapon import extract_all_weapon_info
from src.engineering import extract_all_engineering_information

DATASET_DIR = "dataset"
SHIPS_DATA_DIR = f"{DATASET_DIR}/Ships"
EQUIPMENT_DATA_DIR = f"{DATASET_DIR}/Equipments"
WEAPON_DATA_DIR = f"{DATASET_DIR}/Weapons"
ENGINEERING_DATA_DIR = f"{DATASET_DIR}/Engineering"

def prepare_ships_json():
    ships_info_list = extract_all_ship_information(SHIPS_DATA_DIR)

    with open(f"{SHIPS_DATA_DIR}/ships.json", "w") as ships_json_file:
        json.dump(
            [asdict(ship) for ship in ships_info_list],
            ships_json_file
        )

def prepare_equipments_json():
    equipments_info_list = extract_all_equipment_information(EQUIPMENT_DATA_DIR)

    with open(f"{EQUIPMENT_DATA_DIR}/equipments.json", "w") as equipments_json_file:
        json.dump(
            [asdict(equipment) for equipment in equipments_info_list],
            equipments_json_file
        )

def prepare_weapons_json():
    weapon_info_list = extract_all_weapon_info(WEAPON_DATA_DIR)

    with open(f"{WEAPON_DATA_DIR}/weapons.json", "w") as weapons_json_file:
        json.dump(
            [asdict(weapon) for weapon in weapon_info_list],
            weapons_json_file
        )

def prepare_engineering_json():
    engineering_info_list = extract_all_engineering_information(ENGINEERING_DATA_DIR)

    with open(f"{ENGINEERING_DATA_DIR}/engineering.json", "w") as engineering_json_file:
        json.dump(
            [asdict(engineering) for engineering in engineering_info_list],
            engineering_json_file
        )

def extract_ships_data():
    for filename in os.listdir(SHIPS_DATA_DIR):
        file_path = os.path.join(SHIPS_DATA_DIR, filename)

        # Skip directories or non-HTML files
        if not os.path.isfile(file_path) or not filename.lower().endswith((".html", ".htm")):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                raw_html_doc = file.read()
                ship_data = extract_ship_data(raw_html_doc)

                print(json.dumps(asdict(ship_data), indent=2))

        except Exception as e:
            print(f"[!] Failed to extract data for {filename}: {e}")

def extract():
    extract_ships_data()

def main():
    extract()
    #transform()
    #load()
    # prepare_ships_json()
    # prepare_equipments_json()
    # prepare_weapons_json()
    # prepare_engineering_json()

if __name__ == "__main__":
    main()
