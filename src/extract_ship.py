import re

from dataclasses import dataclass
from typing import Optional, List
from bs4 import BeautifulSoup

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

@dataclass
class ExtractedShipOutfittingModule:
    default_system: str = "Empty"
    default_rating: str = "--"
    default_class: str = "--"
    max_class: str = "1"

@dataclass
class ExtractedShipOutfitting:
    small_hardpoint: Optional[List[ExtractedShipOutfittingModule]] = None
    medium_hardpoint: Optional[List[ExtractedShipOutfittingModule]] = None
    large_hardpoint: Optional[List[ExtractedShipOutfittingModule]] = None
    utility_mount: Optional[List[ExtractedShipOutfittingModule]] = None
    bulkhead: Optional[ExtractedShipOutfittingModule] = None
    reactor_bay: Optional[ExtractedShipOutfittingModule] = None
    thrusters_mounting: Optional[ExtractedShipOutfittingModule] = None
    frame_shift_drive_housing: Optional[ExtractedShipOutfittingModule] = None
    environment_control: Optional[ExtractedShipOutfittingModule] = None
    power_coupling: Optional[ExtractedShipOutfittingModule] = None
    sensor_suite: Optional[ExtractedShipOutfittingModule] = None
    fuel_store: Optional[ExtractedShipOutfittingModule] = None
    internal_compartments: Optional[List[ExtractedShipOutfittingModule]] = None

@dataclass
class ExtractedShipData:
    name: str = NotDefined
    overview_text: str = NotDefined
    infobox: Optional[ExtractedShipInfoBox] = None
    outfitting: Optional[ExtractedShipOutfitting] = None

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

def has_section(soup, name: str) -> bool:
    return bool(soup.select_one(f"h2 span:-soup-contains('{name}')"))

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

def extract_outfitting_module(row) -> ExtractedShipOutfittingModule:
    tds = []
    for td in row.find_all("td"):
        # Prefer <a> text if present, else td text
        if td.a:
            tds.append(td.a.get_text(strip=True))
        else:
            tds.append(td.get_text(strip=True))
    tds = [td for td in tds if td]
    
    return ExtractedShipOutfittingModule(
        default_system=tds[1] if len(tds) <= 5 else f"{tds[1]} {tds[2]}",
        default_rating=tds[2] if len(tds) <= 5 else tds[3],
        default_class=tds[3] if len(tds) <= 5 else tds[4],
        max_class=tds[4] if len(tds) <= 5 else tds[5]
    )

def extract_outfitting_list(soup, section_title) -> Optional[List[ExtractedShipOutfittingModule]]:
    table = soup.select("table.article-table > tbody")[0]

    modules = []

    def extract_info(row):
        tds = [td for td in row.find_all("td", recursive=False) if not td.has_attr("rowspan")]
    
        modules.append(ExtractedShipOutfittingModule(
            default_system=tds[0].get_text(), # if len(tds) < 5 else tds[1],
            default_rating=tds[1].get_text(), # if len(tds) < 5 else tds[2],
            default_class=tds[2].get_text(), # if len(tds) < 5 else tds[3],
            max_class=tds[3].get_text(), # if len(tds) < 5 else tds[4]
        ))

    for row in table.find_all("tr"):
        td = row.find("td")

        if td and td.has_attr("rowspan"):
            td_label = td.get_text().rstrip()
            
            if td_label == section_title:
                extract_info(row)
                siblings = row.find_next_siblings("tr")[0:int(td["rowspan"]) - 1]

                for sibling in siblings:
                    extract_info(sibling)

    return modules

def extract_outfitting_single(soup, label) -> Optional[ExtractedShipOutfittingModule]:
    # Find table row with td containing label
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            tds = row.find_all("td")
            if any(label in td.get_text() for td in tds):
                return extract_outfitting_module(row)
    return None

def extract_outfitting(soup) -> ExtractedShipOutfitting:
    return ExtractedShipOutfitting(
        small_hardpoint=extract_outfitting_list(soup, "Small Hardpoint"),
        medium_hardpoint=extract_outfitting_list(soup, "Medium Hardpoint"),
        large_hardpoint=extract_outfitting_list(soup, "Large Hardpoint"),
        utility_mount=extract_outfitting_list(soup, "Utility Mount"),
        bulkhead=extract_outfitting_single(soup, "Bulkhead"),
        reactor_bay=extract_outfitting_single(soup, "Reactor Bay"),
        thrusters_mounting=extract_outfitting_single(soup, "Thrusters Mounting"),
        frame_shift_drive_housing=extract_outfitting_single(soup, "Frame Shift Drive Housing"),
        environment_control=extract_outfitting_single(soup, "Environment Control"),
        power_coupling=extract_outfitting_single(soup, "Power Coupling"),
        sensor_suite=extract_outfitting_single(soup, "Sensor Suite"),
        fuel_store=extract_outfitting_single(soup, "Fuel Store"),
        internal_compartments=extract_outfitting_list(soup, "Internal Compartments")
    )

def extract_overview_text(soup) -> str:
    overview_header = soup.select_one("h2 span:-soup-contains('Overview')").parent

    if not overview_header:
        return NotDefined

    paragraphs = overview_header.find_next_siblings("p")
    text = "".join(p.get_text() for p in paragraphs)
    
    return text if text != "" else NotDefined

def extract_name(soup) -> str:
    name = soup.select("#firstHeading")[0].find("span")

    if not name: return NotDefined
    
    return name.get_text(strip=True)

def extract_ship_data(raw_html_doc: str) -> ExtractedShipData:
    soup = BeautifulSoup(raw_html_doc, "html.parser")
    name_text = extract_name(soup)
    overview_text = extract_overview_text(soup)
    infobox = extract_infobox(soup)
    outfitting = extract_outfitting(soup) if has_section(soup, "Outfitting") else None

    return ExtractedShipData(
        name=name_text,
        overview_text=overview_text,
        infobox=infobox,
        outfitting=outfitting
    )
