"""Glue: runs the nodes in order.

load_prompts -> render_template -> generate -> score -> report

Each node lives in its own module and can be tested alone. This file only
connects them.
"""

from typing import Dict, List, Optional

from gen_eval.generators import GeneratorError, generate, model_label
from gen_eval.prompts import load_prompts
from gen_eval.scorers import score
from gen_eval.templates import render_template


def run_one(item: Dict, generator: str, model: Optional[str]) -> Dict:
    """Render, generate and score a single prompt with a single generator."""
    prompt_text = render_template(item["template"], item["variables"])

    output = ""
    error = ""
    try:
        output = generate(generator, prompt_text, item["variables"], model)
    except GeneratorError as problem:
        # One failed call should not stop the whole run.
        error = str(problem)

    if error == "":
        scored = score(output, item["checks"])
        passed = scored["passed"]
        checks = scored["checks"]
    else:
        passed = False
        checks = []

    return {
        "id": item["id"],
        "generator": generator,
        "model": model_label(generator, model),
        "is_mock": generator == "mock",
        "prompt": prompt_text,
        "output": output,
        "error": error,
        "passed": passed,
        "checks": checks,
    }


def run_pipeline(prompts_path: str, generators: List[str], model: Optional[str]) -> List[Dict]:
    """Run every prompt through every generator. Returns one row per pair."""
    items = load_prompts(prompts_path)
    rows = []
    for item in items:
        for generator in generators:
            rows.append(run_one(item, generator, model))
    return rows
