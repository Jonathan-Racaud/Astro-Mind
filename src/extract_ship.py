from lxml import html

from dataclasses import dataclass, field
from typing import Optional, List

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

def has_aside_section(tree, name: str) -> bool:
    return bool(tree.xpath(f"//aside//section/h2[contains(text(), '{name}')]"))

def get_aside_value(tree, data_source: str) -> str:
    value = tree.xpath(f"//aside//div[@data-source='{data_source}']//div[@class='pi-data-value pi-font']//text()")
    return value[0] if value else NotDefined

def get_value_for_label(tree, label):
    val = tree.xpath(f"//aside//h3[contains(@class, 'pi-data-label') and contains(text(),'{label}')]/following-sibling::div[contains(@class, 'pi-data-value')]/text()")

    text = ""
    if len(val) == 1:
        text = val[0].strip() if val else NotDefined
    else:
        text = "\n".join([v.strip() for v in val if v.strip()]) if val else NotDefined

    text = text.replace("×", "x")
    
    return text

def has_section(tree, name: str) -> bool:
    return bool(tree.xpath(f"//h2[span[contains(text(), '{name}')]]"))

def extract_infobox_overview(tree) -> ExtractedShipInfoBoxOverview:
    overview = ExtractedShipInfoBoxOverview()

    overview.manufacturer = get_aside_value(tree, "manufacturer")
    overview.years_produced = get_aside_value(tree, "yearsproduced")
    overview.ship_type = get_aside_value(tree, "type")
    overview.cost = get_aside_value(tree, "cost")
    overview.insurance = get_aside_value(tree, "insurance")
    overview.expansion = get_aside_value(tree, "expansion")
    
    return overview

def extract_infobox_specifications(tree) -> ExtractedShipInfoBoxSpecifications:
    specs = ExtractedShipInfoBoxSpecifications()
    
    specs.landing_pad_size = get_aside_value(tree, "landingpad")
    specs.dimensions = get_aside_value(tree, "dimensions")
    specs.pilot_seats = get_aside_value(tree, "seats")
    specs.multicrew = get_aside_value(tree, "multicrew")
    specs.fighter_hangar = get_aside_value(tree, "fighterhangar")
    specs.hull_mass = get_aside_value(tree, "hullmass")
    specs.mass_lock_factor = get_aside_value(tree, "masslock")
    specs.armour = get_aside_value(tree, "armour")
    specs.armour_hardness = get_aside_value(tree, "armourhardness")
    specs.shields = get_aside_value(tree, "shields")
    specs.heat_capacity = get_aside_value(tree, "heatcapacity")
    specs.fuel_capacity = get_aside_value(tree, "fuelcapacity")
    specs.manoeuvrability = get_aside_value(tree, "manoeuvrability")
    specs.top_speed = get_aside_value(tree, "topspeed")
    specs.boost_speed = get_aside_value(tree, "boostspeed")
    specs.unladen_jump_range = get_aside_value(tree, "unladen")
    specs.cargo_capacity = get_aside_value(tree, "cargocapacity")
    specs.top_speed = get_value_for_label(tree, "Top Speed")
    specs.boost_speed = get_value_for_label(tree, "Boost Speed")
    specs.unladen_jump_range = get_value_for_label(tree, "Unladen Jump Range")
    specs.cargo_capacity = get_value_for_label(tree, "Cargo Capacity")
    
    return specs

def extract_infobox_outfitting(tree) -> ExtractedShipInfoBoxOutfitting:
    outfitting = ExtractedShipInfoBoxOutfitting()
    
    outfitting.hardpoints = get_value_for_label(tree, "Hardpoints")
    outfitting.internal_compartments = get_value_for_label(tree, "Internal Compartments")
    outfitting.reserved_compartments = get_value_for_label(tree, "Reserved Compartments")
    
    return outfitting

def extract_infobox_hardpoints(tree) -> ExtractedShipInfoBoxHardpoints:
    hardpoints = ExtractedShipInfoBoxHardpoints()
    
    hardpoints.utility_mount = get_value_for_label(tree, "Utility Mount")
    hardpoints.weapon_mounts = get_value_for_label(tree, "Weapon Mounts")
    
    return hardpoints

def extract_infobox(tree) -> ExtractedShipInfoBox:
    return ExtractedShipInfoBox(
        overview=extract_infobox_overview(tree),
        specifications=extract_infobox_specifications(tree),
        outfitting=extract_infobox_outfitting(tree) if has_aside_section(tree, "Outfitting") else None,
        hardpoints=extract_infobox_hardpoints(tree) if has_aside_section(tree, "Hardpoints") else None
    )

def extract_outfitting_module(row) -> ExtractedShipOutfittingModule:
    tds = row.xpath(".//td/a/text() | .//td/text()")    
    tds = [td.strip() for td in tds if td.strip()]

    return ExtractedShipOutfittingModule(
        default_system=tds[1] if len(tds) <= 5 else f"{tds[1]} {tds[2]}",
        default_rating=tds[2] if len(tds) <= 5 else tds[3],
        default_class=tds[3] if len(tds) <= 5 else tds[4],
        max_class=tds[4] if len(tds) <= 5 else tds[5]
    )

def extract_outfitting_list(tree, section_title) -> Optional[list]:
    # Find table after a heading with section_title
    heading = tree.xpath(f"//h3[span[contains(text(),'{section_title}')]]")
    if not heading:
        return None
    table = heading[0].getnext()
    if table is not None and table.tag == "table":
        rows = table.xpath(".//tr[position()>1]")  # skip header
        return [extract_outfitting_module(row) for row in rows]
    return None

def extract_outfitting_single(tree, label) -> Optional[ExtractedShipOutfittingModule]:
    # Find row in outfitting table with label
    row = tree.xpath(f"//table//tr[td[contains(text(),'{label}')]]") or tree.xpath(f"//table//tr[td[a[contains(text(),'{label}')]]]")
    if row:
        return extract_outfitting_module(row[0])
    return None

def extract_outfitting(tree) -> ExtractedShipOutfitting:
    return ExtractedShipOutfitting(
        small_hardpoint=extract_outfitting_list(tree, "Small Hardpoint"),
        medium_hardpoint=extract_outfitting_list(tree, "Medium Hardpoint"),
        large_hardpoint=extract_outfitting_list(tree, "Large Hardpoint"),
        utility_mount=extract_outfitting_list(tree, "Utility Mount"),
        bulkhead=extract_outfitting_single(tree, "Bulkhead"),
        reactor_bay=extract_outfitting_single(tree, "Reactor Bay"),
        thrusters_mounting=extract_outfitting_single(tree, "Thrusters Mounting"),
        frame_shift_drive_housing=extract_outfitting_single(tree, "Frame Shift Drive Housing"),
        environment_control=extract_outfitting_single(tree, "Environment Control"),
        power_coupling=extract_outfitting_single(tree, "Power Coupling"),
        sensor_suite=extract_outfitting_single(tree, "Sensor Suite"),
        fuel_store=extract_outfitting_single(tree, "Fuel Store"),
        internal_compartments=extract_outfitting_list(tree, "Internal Compartments")
    )

def extract_overview_text(tree) -> str:
    paras = tree.xpath("//div[contains(@class,'mw-parser-output')]/p[normalize-space(text())]")
    return paras[0].text_content().strip() if paras else ""

def extract_name(tree) -> str:
    name_element = tree.xpath("//h1[@id='firstHeading']/span/text()")
    return name_element[0].strip() if name_element else NotDefined

def extract_ship_data(raw_html_doc: str) -> ExtractedShipData:
    tree = html.fromstring(raw_html_doc)
    name_text = extract_name(tree)
    overview_text = extract_overview_text(tree)
    infobox = extract_infobox(tree)
    outfitting = extract_outfitting(tree) if has_section(tree, "Outfitting") else None

    return ExtractedShipData(
        name=name_text,
        overview_text=overview_text,
        infobox=infobox,
        outfitting=outfitting
    )
