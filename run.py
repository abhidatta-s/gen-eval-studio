"""Command line entry point.

Examples:
  python3 run.py
  python3 run.py --generators mock,hf --model meta-llama/Llama-3.2-3B-Instruct
"""

import argparse
import os
import sys
from datetime import datetime

from gen_eval.generators import GeneratorError, check_ready
from gen_eval.pipeline import run_pipeline
from gen_eval.report import write_report


def parse_args():
    parser = argparse.ArgumentParser(description="Run prompts through generators and score them.")
    parser.add_argument("--prompts", default="prompts/sample_prompts.json",
                        help="path to the prompts JSON file")
    parser.add_argument("--generators", default="mock",
                        help="comma separated list: mock, hf, ollama (default: mock)")
    parser.add_argument("--model", default=None,
                        help="model name for hf or ollama (each has its own default)")
    parser.add_argument("--out", default=None,
                        help="output folder (default: runs/<timestamp>)")
    return parser.parse_args()


def print_summary(summary, out_dir):
    print("")
    print("Generator      Passed   Total   Pass rate")
    print("-------------  ------   -----   ---------")
    for item in summary:
        name = item["generator"]
        if name == "mock":
            name = "mock (fake)"
        percent = str(round(item["pass_rate"] * 100)) + "%"
        print(name.ljust(13) + "  " + str(item["passed"]).rjust(6) + "   "
              + str(item["total"]).rjust(5) + "   " + percent.rjust(9))
    print("")
    print("Files written to: " + out_dir)


def main() -> int:
    args = parse_args()

    names = []
    for part in args.generators.split(","):
        part = part.strip()
        if part != "":
            names.append(part)

    # Check everything is ready BEFORE running, so errors are friendly.
    try:
        for name in names:
            check_ready(name)
    except GeneratorError as problem:
        print("Error: " + str(problem))
        return 1

    out_dir = args.out
    if out_dir is None:
        out_dir = os.path.join("runs", datetime.now().strftime("%Y%m%d-%H%M%S"))

    try:
        rows = run_pipeline(args.prompts, names, args.model)
    except (ValueError, OSError) as problem:
        print("Error: " + str(problem))
        return 1

    result = write_report(rows, out_dir)
    print_summary(result["summary"], out_dir)
    if "mock" in names:
        print("Note: mock output is fake. It is not a real model result.")
    for row in rows:
        if row["error"] != "":
            print("Problem with " + row["generator"] + " on " + row["id"] + ": " + row["error"])
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
