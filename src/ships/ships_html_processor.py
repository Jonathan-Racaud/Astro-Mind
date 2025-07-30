from dataclasses import dataclass
from typing import List, Optional

from ..html_processor import BaseHTMLProcessor, ContentChunk

NotDefined = "N/A"

@dataclass
class ExtractedShipInfoBoxOverview:
    manufacturer: str = NotDefined
    years_produced: str = NotDefined
    ship_type: str = NotDefined
    cost: str = NotDefined
    insurance: str = NotDefined
    expansion: str = NotDefined

@dataclass
class ExtractedShipInfoBoxSpecifications:
    hangar_type: str = NotDefined
    landing_pad_size: str = NotDefined
    dimensions: str = NotDefined
    pilot_seats: str = NotDefined
    multicrew: str = NotDefined
    fighter_hangar: str = NotDefined
    hull_mass: str = NotDefined
    mass_lock_factor: str = NotDefined
    armour: str = NotDefined
    armour_hardness: str = NotDefined
    shields: str = NotDefined
    heat_capacity: str = NotDefined
    fuel_capacity: str = NotDefined
    manoeuvrability: str = NotDefined
    top_speed: str = NotDefined
    boost_speed: str = NotDefined
    unladen_jump_range: str = NotDefined
    cargo_capacity: str = NotDefined

@dataclass
class ExtractedShipInfoBoxOutfitting:
    hardpoints: str = NotDefined
    internal_compartments: str = NotDefined
    reserved_compartments: str = NotDefined

@dataclass
class ExtractedShipInfoBoxHardpoints:
    utility_mount: str = NotDefined
    weapon_mounts: str = NotDefined

@dataclass
class ExtractedShipInfoBox:
    overview: Optional[ExtractedShipInfoBoxOverview] = None
    specifications: Optional[ExtractedShipInfoBoxSpecifications] = None
    outfitting: Optional[ExtractedShipInfoBoxOutfitting] = None
    hardpoints: Optional[ExtractedShipInfoBoxHardpoints] = None

def has_aside_section(soup, name: str) -> bool:
    return bool(soup.select_one(f"aside section h2:-soup-contains('{name}')"))

def get_aside_value(soup, data_source: str) -> str:
    div = soup.select_one(f"aside div[data-source='{data_source}'] div.pi-data-value.pi-font")
    if div:
        text = div.get_text()
        return text if text else NotDefined
    return NotDefined

def get_value_for_label(soup, label):
    # Find h3 label in aside, then get next sibling div with class pi-data-value
    for h3 in soup.select("aside h3.pi-data-label"):
        if label in h3.get_text():
            value_divs = []
            sib = h3.find_next_sibling()
            while sib and 'pi-data-value' in sib.get('class', []):
                value_divs.append(sib.get_text())
                sib = sib.find_next_sibling()
            if not value_divs:
                return NotDefined
            text = "\n".join([v.replace("×", "x") for v in value_divs if v])
            return text
    return NotDefined

def extract_infobox_overview(soup) -> ExtractedShipInfoBoxOverview:
    overview = ExtractedShipInfoBoxOverview()
    overview.manufacturer = get_aside_value(soup, "manufacturer")
    overview.years_produced = get_aside_value(soup, "yearsproduced")
    overview.ship_type = get_aside_value(soup, "type")
    overview.cost = get_aside_value(soup, "cost")
    overview.insurance = get_aside_value(soup, "insurance")
    overview.expansion = get_aside_value(soup, "expansion")
    return overview

def extract_infobox_specifications(soup) -> ExtractedShipInfoBoxSpecifications:
    specs = ExtractedShipInfoBoxSpecifications()
    specs.landing_pad_size = get_aside_value(soup, "landingpad")
    specs.dimensions = get_aside_value(soup, "dimensions")
    specs.pilot_seats = get_aside_value(soup, "seats")
    specs.multicrew = get_aside_value(soup, "multicrew")
    specs.fighter_hangar = get_aside_value(soup, "fighterhangar")
    specs.hull_mass = get_aside_value(soup, "hullmass")
    specs.mass_lock_factor = get_aside_value(soup, "masslock")
    specs.armour = get_aside_value(soup, "armour")
    specs.armour_hardness = get_aside_value(soup, "armourhardness")
    specs.shields = get_aside_value(soup, "shields")
    specs.heat_capacity = get_aside_value(soup, "heatcapacity")
    specs.fuel_capacity = get_aside_value(soup, "fuelcapacity")
    specs.manoeuvrability = get_aside_value(soup, "manoeuvrability")
    specs.top_speed = get_aside_value(soup, "topspeed")
    specs.boost_speed = get_aside_value(soup, "boostspeed")
    specs.unladen_jump_range = get_aside_value(soup, "unladen")
    specs.cargo_capacity = get_aside_value(soup, "cargocapacity")
    # Try to get values by label as well (may overwrite above)
    specs.top_speed = get_value_for_label(soup, "Top Speed")
    specs.boost_speed = get_value_for_label(soup, "Boost Speed")
    specs.unladen_jump_range = get_value_for_label(soup, "Unladen Jump Range")
    specs.cargo_capacity = get_value_for_label(soup, "Cargo Capacity")
    return specs

def extract_infobox_outfitting(soup) -> ExtractedShipInfoBoxOutfitting:
    outfitting = ExtractedShipInfoBoxOutfitting()
    outfitting.hardpoints = get_value_for_label(soup, "Hardpoints")
    outfitting.internal_compartments = get_value_for_label(soup, "Internal Compartments")
    outfitting.reserved_compartments = get_value_for_label(soup, "Reserved Compartments")
    return outfitting

def extract_infobox_hardpoints(soup) -> ExtractedShipInfoBoxHardpoints:
    hardpoints = ExtractedShipInfoBoxHardpoints()
    hardpoints.utility_mount = get_value_for_label(soup, "Utility Mount")
    hardpoints.weapon_mounts = get_value_for_label(soup, "Weapon Mounts")
    return hardpoints

def extract_infobox(soup) -> ExtractedShipInfoBox:
    return ExtractedShipInfoBox(
        overview=extract_infobox_overview(soup),
        specifications=extract_infobox_specifications(soup),
        outfitting=extract_infobox_outfitting(soup) if has_aside_section(soup, "Outfitting") else None,
        hardpoints=extract_infobox_hardpoints(soup) if has_aside_section(soup, "Hardpoints") else None
    )

class ShipHTMLProcessor(BaseHTMLProcessor):
    ENTITY_TYPE = "ship"
    
    def _extract_entity_name(self) -> str:
        name_element = self.soup.select_one("#firstHeading span")
        return name_element.get_text(strip=True) if name_element else "Unknown Ship"

    def _normalize_section(self, header: str) -> str:
        header_lower = header.lower()
        if 'overview' in header_lower: return 'overview'
        if 'specif' in header_lower: return 'specifications'
        if 'outfit' in header_lower: return 'outfitting'
        return 'other'

    def extract_chunks(self) -> List[ContentChunk]:
        chunks = super().extract_chunks()
        infobox = extract_infobox(self.soup)
        
        for chunk in chunks:
            if chunk.section_type == 'overview':
                chunk.infobox = infobox.__dict__ if infobox else None
        return chunks
