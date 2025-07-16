import json
import os
import re

from dataclasses import dataclass, asdict
from lxml import html
from typing import Optional, List, Any

@dataclass
class Engineering:
    applicable: Optional[bool]
    engineers: List[str]
    upgrades: List[str]

@dataclass
class Overview:
    image_url: Optional[str]
    slot: Optional[str]
    classes: Optional[str]
    ratings: Optional[str]
    needed_refills: Optional[str]
    default_key: Optional[str]

@dataclass
class EquipmentInfo:
    name: str
    overview: Optional[Overview]
    engineering: Optional[Engineering]
    specifications: List[dict]

def extract_specifications_table(doc) -> List[dict]:
    specifications: List[dict] = []

    # Locate the Specifications table (after the "Specifications" header)
    spec_table = doc.xpath('//span[@id="Specifications"]/following::table[1]')
    if not spec_table:
        return specifications

    headers = spec_table[0].xpath('.//tr[1]/th')
    headers = [
        re.sub(r'[()\s]+', '_', cell.text_content().strip().lower()).strip('_')  # removes spaces & parentheses, trims trailing '_'
        for cell in headers
    ]

    rows = spec_table[0].xpath('.//tbody/tr')
    for row in rows:
        cells = row.xpath('./td')
        if len(cells) != len(headers):
            continue # Skip malformed rows

        row_data = {
            headers[i]: cells[i].text_content().strip()
            for i in range(len(headers))
        }
        specifications.append(row_data)

    return specifications

def extract_equipment_info(content: str) -> EquipmentInfo:
    doc = html.fromstring(content)

    # --- OVERVIEW SECTION ---
    name = None
    overview = Overview(
        image_url=None,
        slot=None,
        classes=None,
        ratings=None,
        needed_refills=None,
        default_key=None
    )

    name = doc.xpath('//*[@id="firstHeading"]/span/text()')[0]
    aside = doc.xpath('//aside[contains(@class, "portable-infobox")]')
    if aside:
        aside = aside[0]

        # Extract name
        title_el = aside.xpath('.//h2[contains(@class, "pi-title")]/text()')
        name = title_el[0].strip() if title_el else name

        # Extract image URL
        image_el = aside.xpath('.//figure[contains(@class, "pi-image")]//img')
        if image_el:
            overview.image_url = image_el[0].get("src")

        # Extract overview fields
        overview_fields = aside.xpath('.//section[h2[text()="Information"]]//div[contains(@class,"pi-data")]')
        for field in overview_fields:
            label_el = field.xpath('.//h3/text()')
            value_el = field.xpath('.//div[@class="pi-data-value"]//text()')

            if label_el and value_el:
                key = label_el[0].strip().lower()
                val = " ".join(v.strip() for v in value_el if v.strip())

                if "slot" in key:
                    overview.slot = val
                elif "class" in key:
                    overview.classes = val
                elif "rating" in key:
                    overview.ratings = val
                elif "refill" in key:
                    overview.needed_refills = val
                elif "key" in key:
                    overview.default_key = val

    # --- SPECIFICATIONS SECTION ---
    specifications = extract_specifications_table(doc)

    # --- ENGINEERING SECTION ---
    applicable = False
    engineers: List[str] = []
    upgrades: List[str] = []

    # Check for "Engineer Modifications" section
    eng_section = doc.xpath('//span[@id="Engineer_Modifications"]/parent::h2')
    if eng_section:
        applicable = True

        # Engineers who can apply (check inside aside if it exists)
        engineer_entries = doc.xpath('//div[contains(@data-source, "engineers")]//a')
        engineers = [a.text_content().strip() for a in engineer_entries if a.text_content().strip()]

        # Engineering upgrades
        upgrade_entries = doc.xpath('//span[@id="Engineer_Modifications"]/following::ul[1]/li/a')
        upgrades = [a.text_content().strip() for a in upgrade_entries if a.text_content().strip()]

    engineering = Engineering(
        applicable=applicable,
        engineers=engineers,
        upgrades=upgrades
    )

    return EquipmentInfo(
        name=name,
        overview=overview,
        specifications=specifications,
        engineering=engineering
    )

def extract_all_equipment_information(directory_path: str) -> List[EquipmentInfo]:
    equipment_infos = []

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)

        # Skip directories or non-HTML files (optional check)
        if not os.path.isfile(file_path) or not filename.lower().endswith((".html", ".htm")):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                html_content = file.read()
                equipment_info = extract_equipment_info(html_content)
                equipment_infos.append(equipment_info)
        except Exception as e:
            print(f"[!] Failed to parse {filename}: {e}")

    return equipment_infos

def equipment_info_to_json(equipment: EquipmentInfo) -> str:
    return json.dumps(asdict(equipment))
