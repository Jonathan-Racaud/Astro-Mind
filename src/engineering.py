import json
import os

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from lxml import html as lxml_html

@dataclass
class EngineeringGradeEffect:
    grade: int
    effects: str

@dataclass
class EngineeringUpgradeEffect:
    name: str
    availability: List[str] = field(default_factory=list)
    grades: List[EngineeringGradeEffect] = field(default_factory=list)

def extract_effect_name(tree) -> str:
    # Try to get from <h1> or <title>
    h1 = tree.xpath('//h1[contains(@class, "page-header__title")]')
    if h1:
        span = h1[0].xpath('.//span[contains(@class, "mw-page-title-main")]')
        if span:
            return span[0].text_content().strip()
        return h1[0].text_content().strip()
    title = tree.xpath('//title')
    if title:
        return title[0].text.split("|")[0].strip()
    return ""

def extract_availability(tree) -> List[str]:
    # Find the Availability section by headline id
    availability = tree.xpath('//span[@id="Availability"]/following::ul[1]')[0]

    if availability is None:
        return []
    

    availabilities = []
    for li in availability:
        a = li.xpath('./a[1]/text()')[0]
        availabilities.append(a)

    return availabilities

def extract_grade(tree, level) -> Optional[EngineeringGradeEffect]:
    grade_table = tree.xpath(f'//span[@id="Grade_1{level}"]/following::table[1]') 

    if grade_table is None:
        return None
    
    if not grade_table:
        return None

    table = grade_table[0]
    headers = [th.text_content().strip() for th in table.xpath('.//thead/tr/th')]
    rows = table.xpath('.//tbody/tr')

    effects = ""
    for row in rows:
        cells = row.xpath('./td|./th')
        row_values = [cell.text_content().strip() for cell in cells]
        effects += ",".join(v.replace("\n", " ").replace("\r", " ") for v in row_values) + "\n"

    return EngineeringGradeEffect(grade=level, effects=effects)

def extract_grades(tree) -> List[EngineeringGradeEffect]:
    grades = []

    for level in range(1, 6):
        grade_effect = extract_grade(tree, level)
        if grade_effect:
            grades.append(grade_effect)
    
    return grades

def extract_engineering_effect(html: str) -> EngineeringUpgradeEffect:
    tree = lxml_html.fromstring(html)
    name = extract_effect_name(tree)
    availability = extract_availability(tree)
    grades = extract_grades(tree)
    return EngineeringUpgradeEffect(name=name, availability=availability, grades=grades)

def extract_all_engineering_information(data_dir: str) -> List[EngineeringUpgradeEffect]:
    import os
    import glob

    engineering_effects = []
    files = glob.glob(os.path.join(data_dir, "*.html"))
    
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            effect = extract_engineering_effect(content)
            engineering_effects.append(effect)

    return engineering_effects

def engineering_upgrade_effect_to_json(upgrade: EngineeringUpgradeEffect) -> str:
    return json.dumps(asdict(upgrade))