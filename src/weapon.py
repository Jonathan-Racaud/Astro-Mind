import json
import os
import re

from dataclasses import dataclass, asdict
from lxml import html
from typing import Optional, List, Any

@dataclass
class EngineeringInfo:
    modifications: Optional[List[str]]
    experimental_effects: Optional[List[str]]

@dataclass
class WeaponInfo:
    name: str
    specifications: List[dict]
    engineering: EngineeringInfo

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
            continue  # Skip malformed rows

        row_data = {
            headers[i]: cells[i].text_content().strip()
            for i in range(len(headers))
        }
        specifications.append(row_data)

    return specifications

def extract_engineering_info(doc) -> EngineeringInfo:
    modifications = None
    experimental_effects = None

    eng_h2 = doc.xpath('//h2[span[@id="Engineering"]]')
    if eng_h2:
        # Modifications
        mods_ul = doc.xpath('//h3[span[@id="Modifications"]]/following-sibling::ul[1]')
        if mods_ul:
            modifications = [li.text_content().strip() for li in mods_ul[0].xpath('./li')]
        # Experimental Effects
        exp_ul = doc.xpath('//h3[span[@id="Experimental_Effects"]]/following-sibling::ul[1]')
        if exp_ul:
            experimental_effects = [li.text_content().strip() for li in exp_ul[0].xpath('./li')]

    return EngineeringInfo(
        modifications=modifications,
        experimental_effects=experimental_effects
    )

def extract_weapon_info(html_content: str) -> WeaponInfo:
    tree = html.fromstring(html_content)

    # Extract weapon name
    name_elem = tree.xpath('//h1[@id="firstHeading"]/span[@class="mw-page-title-main"]')
    name = name_elem[0].text_content().strip() if name_elem else ""

    # --- SPECIFICATIONS SECTION ---
    specifications = extract_specifications_table(tree)

    # --- ENGINEERING SECTION ---
    engineering = extract_engineering_info(tree)

    return WeaponInfo(
        name=name,
        specifications=specifications,
        engineering=engineering
    )

def extract_all_weapon_info(directory_path: str) -> List[WeaponInfo]:
    weapon_info_list = []

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)

        # Skip directories or non-HTML files (optional check)
        if not os.path.isfile(file_path) or not filename.lower().endswith((".html", ".htm")):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                html_content = file.read()
                weapon_info = extract_weapon_info(html_content)
                weapon_info_list.append(weapon_info)
        except Exception as e:
            print(f"[!] Failed to parse {filename}: {e}")

    return weapon_info_list

def weapon_info_to_json(weapon: WeaponInfo) -> str:
    return json.dumps(asdict(weapon))