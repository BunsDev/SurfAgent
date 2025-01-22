from typing import Dict
import json
from config.log import logger

def safe_json_loads(json_str: str, fallback: Dict, content: str = "") -> Dict:
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        fixed = json_str.replace('""', '"')
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            logger.error("Still can't parse JSON after fix.")
            return fallback