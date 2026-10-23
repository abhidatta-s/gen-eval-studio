"""Node 1: load_prompts.

Reads the prompt set from a JSON file and checks that each item has the
fields the rest of the pipeline needs.
"""

import json
from typing import Dict, List

REQUIRED_FIELDS = ["id", "template", "variables", "checks"]


def load_prompts(path: str) -> List[Dict]:
    """Return a list of prompt dicts read from the JSON file at `path`."""
    with open(path, "r", encoding="utf-8") as f:
        items = json.load(f)

    if not isinstance(items, list):
        raise ValueError("Prompt file must contain a JSON list of prompts.")

    # Fail early with a clear message, instead of a confusing KeyError later.
    for item in items:
        for field in REQUIRED_FIELDS:
            if field not in item:
                raise ValueError(
                    "Prompt is missing the field '" + field + "': " + str(item)
                )
    return items
