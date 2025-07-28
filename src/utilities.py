import os
import re

def is_dir_empty(path: str) -> bool:
    return not os.listdir(path)

def normalize_str(s: str) -> str:
    return '-'.join(re.sub(r'\W+', ' ', s.lower()).strip().split())
