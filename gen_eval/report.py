"""Node 5: report.

Writes results.json, results.csv and report.html into an output folder.
"""

import csv
import html
import json
import os
from datetime import datetime
from typing import Dict, List


def summarize(rows: List[Dict]) -> List[Dict]:
    """Pass rate per generator."""
    order = []
    totals = {}
    passes = {}
    for row in rows:
        name = row["generator"]
        if name not in totals:
            order.append(name)
            totals[name] = 0
            passes[name] = 0

        totals[name] += 1
        if row["passed"]:
            passes[name] += 1

    summary = []
    for name in order:
        rate = passes[name] / totals[name]
        summary.append({
            "generator": name,
            "total": totals[name],
            "passed": passes[name],
            "pass_rate": round(rate, 4),
        })
    return summary


def build_run_info(rows: List[Dict], summary: List[Dict]) -> Dict:
    names = []
    for item in summary:
        names.append(item["generator"])
    has_mock = "mock" in names
    return {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "generators": names,
        "includes_mock": has_mock,
        "note": "Mock output is fake and deterministic. It is not a real model result."
        if has_mock else "",
    }


def checks_as_text(row: Dict) -> str:
    parts = []
    for check in row["checks"]:
        word = "PASS" if check["passed"] else "FAIL"
        parts.append(word + " " + check["type"] + " (" + check["reason"] + ")")
    return "; ".join(parts)


def write_json(path: str, data: Dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def write_csv(path: str, rows: List[Dict]) -> None:
    columns = ["id", "generator", "model", "is_mock", "passed", "output", "checks", "error"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([
                row["id"],
                row["generator"],
                row["model"],
                row["is_mock"],
                row["passed"],
                row["output"],
                checks_as_text(row),
                row["error"],
            ])


CSS = """
body { background: #151722; color: #e6e8f0; margin: 0; padding: 24px;
  font-family: system-ui, -apple-system, Inter, Segoe UI, sans-serif; line-height: 1.5; }
h1 { margin: 0 0 4px 0; color: #a5b4fc; }
h2 { margin-top: 32px; color: #a5b4fc; }
.sub { color: #a9afc4; }
.banner { background: #262a3b; border: 1px solid #6366f1; border-radius: 8px;
  padding: 10px 14px; margin: 16px 0; }
.cards { display: flex; flex-wrap: wrap; gap: 16px; margin: 16px 0; }
.card { background: #1e2130; border: 1px solid #3a3f55; border-radius: 10px;
  padding: 16px 20px; min-width: 200px; }
.card .rate { font-size: 32px; font-weight: 700; color: #a5b4fc; }
.card .label { color: #a9afc4; }
table { border-collapse: collapse; width: 100%; background: #1e2130; }
th, td { border: 1px solid #3a3f55; padding: 8px 10px; text-align: left; vertical-align: top; }
th { background: #262a3b; color: #a5b4fc; }
.pass { color: #4ade80; font-weight: 600; }
.fail { color: #f87171; font-weight: 600; }
ul.checks { margin: 0; padding-left: 18px; }
.reason { color: #a9afc4; }
.output { white-space: pre-wrap; }
"""


def esc(value) -> str:
    """Escape text so model output can never inject HTML."""
    return html.escape(str(value))


def status_html(passed: bool) -> str:
    if passed:
        return '<span class="pass">PASS</span>'
    return '<span class="fail">FAIL</span>'


def build_html(rows: List[Dict], summary: List[Dict], info: Dict) -> str:
    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="en"><head><meta charset="utf-8">')
    parts.append("<title>gen-eval-studio report</title>")
    parts.append("<style>" + CSS + "</style></head><body>")
    parts.append("<h1>gen-eval-studio report</h1>")
    parts.append('<div class="sub">Date: ' + esc(info["date"])
                 + " | Generators: " + esc(", ".join(info["generators"])) + "</div>")

    if info["includes_mock"]:
        parts.append('<div class="banner"><strong>MOCK RUN.</strong> '
                     + esc(info["note"]) + "</div>")

    parts.append('<h2>Pass rate per generator</h2><div class="cards">')
    for item in summary:
        label = item["generator"]
        if item["generator"] == "mock":
            label = "mock (fake)"
        percent = str(round(item["pass_rate"] * 100)) + "%"
        parts.append('<div class="card"><div class="label">' + esc(label) + "</div>"
                     + '<div class="rate">' + esc(percent) + "</div>"
                     + '<div class="label">' + esc(item["passed"]) + " of "
                     + esc(item["total"]) + " prompts passed</div></div>")
    parts.append("</div>")

    parts.append("<h2>Results per prompt and generator</h2>")
    parts.append("<table><tr><th>Prompt</th><th>Generator</th><th>Output</th>"
                 "<th>Checks</th><th>Result</th></tr>")
    for row in rows:
        parts.append("<tr>")
        parts.append("<td>" + esc(row["id"]) + '<br><span class="reason">'
                     + esc(row["prompt"]) + "</span></td>")
        gen_text = row["generator"]
        if row["is_mock"]:
            gen_text = gen_text + " (MOCK)"
        parts.append("<td>" + esc(gen_text) + '<br><span class="reason">'
                     + esc(row["model"]) + "</span></td>")

        if row["error"] != "":
            parts.append('<td class="output"><span class="fail">Error:</span> '
                         + esc(row["error"]) + "</td>")
        else:
            parts.append('<td class="output">' + esc(row["output"]) + "</td>")

        parts.append('<td><ul class="checks">')
        for check in row["checks"]:
            parts.append("<li>" + status_html(check["passed"]) + " " + esc(check["type"])
                         + ' <span class="reason">(' + esc(check["reason"]) + ")</span></li>")
        parts.append("</ul></td>")
        parts.append("<td>" + status_html(row["passed"]) + "</td>")
        parts.append("</tr>")
    parts.append("</table></body></html>")
    return "\n".join(parts)


def write_report(rows: List[Dict], out_dir: str) -> Dict:
    """Write all three files and return the summary data."""
    os.makedirs(out_dir, exist_ok=True)
    summary = summarize(rows)
    info = build_run_info(rows, summary)

    write_json(os.path.join(out_dir, "results.json"),
               {"run": info, "summary": summary, "results": rows})
    write_csv(os.path.join(out_dir, "results.csv"), rows)
    with open(os.path.join(out_dir, "report.html"), "w", encoding="utf-8") as f:
        f.write(build_html(rows, summary, info))
    return {"run": info, "summary": summary}
