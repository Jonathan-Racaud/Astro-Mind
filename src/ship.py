import os
import json

from lxml import html

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Any

@dataclass
class Overview:
    manufacturer: Optional[str] = None
    years_produced: Optional[str] = None
    ship_type: Optional[str] = None
    cost: Optional[str] = None
    insurance: Optional[str] = None
    expansion: Optional[str] = None

@dataclass
class Specifications:
    landing_pad_size: Optional[str] = None
    dimensions: Optional[str] = None
    pilot_seats: Optional[str] = None
    multicrew: Optional[str] = None
    fighter_hangar: Optional[str] = None
    hull_mass: Optional[str] = None
    mass_lock_factor: Optional[str] = None
    armour: Optional[str] = None
    armour_hardness: Optional[str] = None
    shields: Optional[str] = None
    heat_capacity: Optional[str] = None
    fuel_capacity: Optional[str] = None
    manoeuvrability: Optional[str] = None
    top_speed: Optional[str] = None
    boost_speed: Optional[str] = None
    unladen_jump_range: Optional[str] = None
    cargo_capacity: Optional[str] = None

@dataclass
class Outfitting:
    hardpoints: Optional[str] = None
    internal_compartments: Optional[str] = None

@dataclass
class ShipInfo:
    name: Optional[str] = None
    image_url: Optional[str] = None
    overview: Overview = field(default_factory=Overview)
    specifications: Specifications = field(default_factory=Specifications)
    outfitting: Outfitting = field(default_factory=Outfitting)

def extract_ship_info(html_content: str) -> ShipInfo:
    doc = html.fromstring(html_content)

    aside = doc.xpath('//aside[contains(@class, "portable-infobox")]')
    if not aside:
        raise ValueError("No <aside> element with class 'portable-infobox' found.")
    aside = aside[0]

    # Ship name
    name_el = aside.xpath('.//h2[contains(@class, "pi-title")]/text()')
    name = name_el[0].strip() if name_el else None

    # Image URL
    image_el = aside.xpath('.//figure//img/@src')
    image_url = image_el[0] if image_el else None

    # Initialize empty sections
    overview = Overview()
    specifications = Specifications()
    outfitting = Outfitting()

    # Map labels to fields for each section
    overview_map = {
        "Manufacturer": "manufacturer",
        "Years Produced": "years_produced",
        "Type": "ship_type",
        "Cost": "cost",
        "Insurance": "insurance",
        "Expansion": "expansion",
    }

    specs_map = {
        "Landing Pad Size": "landing_pad_size",
        "Dimensions": "dimensions",
        "Pilot Seats": "pilot_seats",
        "Multicrew": "multicrew",
        "Fighter Hangar": "fighter_hangar",
        "Hull Mass": "hull_mass",
        "Mass Lock Factor": "mass_lock_factor",
        "Armour": "armour",
        "Armour Hardness": "armour_hardness",
        "Shields": "shields",
        "Heat Capacity": "heat_capacity",
        "Fuel Capacity": "fuel_capacity",
        "Manoeuvrability": "manoeuvrability",
        "Top Speed": "top_speed",
        "Boost Speed": "boost_speed",
        "Unladen Jump Range": "unladen_jump_range",
        "Cargo Capacity": "cargo_capacity",
    }

    outfitting_map = {
        "Hardpoints": "hardpoints",
        "Internal Compartments": "internal_compartments",
    }

    # Parse all sections
    for section in aside.xpath('.//section'):
        header = section.xpath('./h2/text()')
        if not header:
            continue
        section_title = header[0].strip()

        for block in section.xpath('.//div[contains(@class, "pi-item pi-data")]'):
            label_el = block.xpath('.//h3/text()')
            value_el = block.xpath('.//div[@class="pi-data-value pi-font"]')

            if not label_el or not value_el:
                continue

            label = label_el[0].strip()
            value = value_el[0].text_content().strip()

            # Match field to section
            if section_title == "Overview" and label in overview_map:
                setattr(overview, overview_map[label], value)
            elif section_title == "Specifications" and label in specs_map:
                setattr(specifications, specs_map[label], value)
            elif section_title == "Outfitting" and label in outfitting_map:
                setattr(outfitting, outfitting_map[label], value)

    return ShipInfo(
        name=name,
        image_url=image_url,
        overview=overview,
        specifications=specifications,
        outfitting=outfitting,
    )

def extract_all_ship_information(directory_path: str) -> List[ShipInfo]:
    ship_infos = []

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)

        # Skip directories or non-HTML files (optional check)
        if not os.path.isfile(file_path) or not filename.lower().endswith((".html", ".htm")):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                html_content = file.read()
                ship_info = extract_ship_info(html_content)
                ship_infos.append(ship_info)
        except Exception as e:
            print(f"[!] Failed to parse {filename}: {e}")

    return ship_infos