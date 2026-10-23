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


# Theme: dark is the fallback, light via [data-theme=light]. The head script picks
# ?theme=light|dark, then a saved choice, then the system setting. Same palette and
# toggle as the other abhidatta Lab demos.
HEAD = """<meta name="color-scheme" content="dark light">
<meta name="theme-color" content="#151722">
<script>/* Theme: ?theme=light|dark, else saved choice, else system setting, else dark. Same pf-theme key as the portfolio. */
(function(){var d=document.documentElement,t;try{var q=new URLSearchParams(location.search).get('theme');if(q==='light'||q==='dark'){localStorage.setItem('pf-theme',q);t=q}else t=localStorage.getItem('pf-theme')}catch(e){}
if(t!=='light'&&t!=='dark')t=window.matchMedia&&matchMedia('(prefers-color-scheme: light)').matches?'light':'dark';d.dataset.theme=t;
var m=document.querySelector('meta[name=theme-color]');if(m)m.content=t==='light'?'#e9edf2':'#151722'})()</script>
"""

SHELL_CSS = """/* Shared demo shell: tokens mirror the abhidatta portfolio. Dark is the fallback; light via [data-theme=light]. */
:root{color-scheme:dark;--ink:230 232 240;
  --bg:#151722;--panel:#1e2130;--panel-2:#262a3b;--line:#3a3f55;--line-2:rgb(var(--ink) / .14);
  --fg:#e6e8f0;--fg-2:#cdd1de;--muted:#a9afc4;--accent:#a5b4fc;--brand:#5b5bd6;--brand-hover:#4f46e5;--on-brand:#f8f9fb;
  --ok:#4ade80;--bad:#f87171;--dot:#ff5c9e;--bar:rgba(21,23,34,.72);--shadow:0 8px 30px rgba(8,9,15,.35);
  --font:"Inter Variable",Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
:root[data-theme=light]{color-scheme:light;--ink:42 48 59;
  --bg:#e9edf2;--panel:#f8f9fb;--panel-2:#f3f5f8;--line:#cfd5de;--line-2:rgba(42,48,59,.15);
  --fg:#2a303b;--fg-2:#3a414d;--muted:#5f6672;--accent:#5b56c2;--brand:#5b56c2;--brand-hover:#4a45a8;--on-brand:#f8f9fb;
  --ok:#136c4c;--bad:#b42d48;--dot:#c03a76;--bar:rgba(243,245,248,.78);--shadow:0 8px 30px rgba(30,40,60,.08)}
.ds-skip{position:fixed;left:16px;top:-60px;z-index:100;background:var(--fg);color:var(--bg);padding:10px 14px;border-radius:10px;font-weight:600;text-decoration:none}
.ds-skip:focus{top:16px}
.ds-bar{position:sticky;top:10px;z-index:30;display:flex;align-items:center;gap:12px;max-width:1280px;margin:10px auto 0;width:calc(100% - 24px);box-sizing:border-box;
  padding:7px 8px 7px 14px;border-radius:12px;border:1px solid var(--line-2);background:var(--bar);
  backdrop-filter:blur(16px) saturate(170%);-webkit-backdrop-filter:blur(16px) saturate(170%);box-shadow:var(--shadow);
  font-family:var(--font);font-size:13px;color:var(--fg-2)}
.ds-bar a{color:inherit;text-decoration:none}
.ds-bar__home{display:inline-flex;align-items:center;gap:8px;padding:4px 6px;margin-left:-6px;border-radius:8px;transition:background .15s}
.ds-bar__home:hover{background:rgb(var(--ink) / .06);color:var(--fg)}
.ds-bar__logo{font-weight:700;color:var(--fg);letter-spacing:-.03em}.ds-bar__logo span{color:var(--dot)}
.ds-bar__sep,.ds-bar__lab{color:var(--muted)}
.ds-bar__name{font-weight:550;color:var(--fg);padding-left:12px;border-left:1px solid var(--line-2)}
.ds-bar__cta{margin-left:auto;padding:6px 12px;border-radius:999px;border:1px solid var(--line-2);background:rgb(var(--ink) / .04);color:var(--fg)!important;font-weight:550;transition:background .15s,border-color .15s}
.ds-bar__cta:hover{background:rgb(var(--ink) / .09)}
.ds-bar__theme{display:inline-grid;place-items:center;width:30px;height:30px;padding:0;border-radius:999px;border:1px solid var(--line-2);
  background:rgb(var(--ink) / .04);color:var(--fg-2);cursor:pointer;transition:background .15s,color .15s;flex:none}
.ds-bar__theme:hover{background:rgb(var(--ink) / .09);color:var(--fg)}
.ds-bar :focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media (max-width:560px){.ds-bar__sep,.ds-bar__lab,.ds-bar__cta{display:none}.ds-bar__theme{margin-left:auto}}
"""

BAR = """<a class="ds-skip" href="#main">Skip to content</a>
<header class="ds-bar">
  <a class="ds-bar__home" href="https://www.abhidattasrichandan.com/lab"><span aria-hidden="true">&larr;</span><span class="ds-bar__logo">abhidatta<span>.</span></span><span class="ds-bar__sep" aria-hidden="true">/</span><span class="ds-bar__lab">Lab</span></a>
  <span class="ds-bar__name" aria-current="page">gen-eval-studio</span>
  <a class="ds-bar__cta" href="https://www.abhidattasrichandan.com">View portfolio</a>
  <button type="button" class="ds-bar__theme" id="ds-theme"></button>
</header>
<script>/* Icon-only light/dark switch (same as the portfolio nav). Shows the theme you would switch to. Follows the system until you choose. */
(function(){var d=document.documentElement,b=document.getElementById('ds-theme'),m=document.querySelector('meta[name=theme-color]');
var sun='<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
var moon='<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>';
function apply(t){d.dataset.theme=t;if(m)m.content=t==='light'?'#e9edf2':'#151722';var n=t==='light'?'dark':'light';b.innerHTML=n==='light'?sun:moon;b.setAttribute('aria-label','Switch to '+n+' theme');b.title='Switch to '+n+' theme'}
apply(d.dataset.theme==='light'?'light':'dark');
b.addEventListener('click',function(){var t=d.dataset.theme==='light'?'dark':'light';try{localStorage.setItem('pf-theme',t)}catch(e){}apply(t)});
if(window.matchMedia){var q=matchMedia('(prefers-color-scheme: light)');var f=function(e){var s=null;try{s=localStorage.getItem('pf-theme')}catch(x){}if(s!=='light'&&s!=='dark')apply(e.matches?'light':'dark')};q.addEventListener?q.addEventListener('change',f):q.addListener(f)}})()</script>
"""

CSS = SHELL_CSS + """
body { background: var(--bg); color: var(--fg); margin: 0;
  font-family: var(--font); line-height: 1.5; }
main { padding: 24px; max-width: 1280px; margin: 0 auto; box-sizing: border-box; }
h1 { margin: 0 0 4px 0; color: var(--accent); }
h2 { margin-top: 32px; color: var(--accent); }
.sub { color: var(--muted); }
.banner { background: var(--panel-2); border: 1px solid var(--brand); border-radius: 8px;
  padding: 10px 14px; margin: 16px 0; }
.cards { display: flex; flex-wrap: wrap; gap: 16px; margin: 16px 0; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
  padding: 16px 20px; min-width: 200px; }
.card .rate { font-size: 32px; font-weight: 700; color: var(--accent); }
.card .label { color: var(--muted); }
.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; min-width: 720px; background: var(--panel); }
th, td { border: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }
th { background: var(--panel-2); color: var(--accent); }
.pass { color: var(--ok); font-weight: 600; }
.fail { color: var(--bad); font-weight: 600; }
ul.checks { margin: 0; padding-left: 18px; }
.reason { color: var(--muted); }
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
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    parts.append(HEAD)
    parts.append("<title>gen-eval-studio report</title>")
    parts.append("<style>" + CSS + "</style></head><body>")
    parts.append(BAR)
    parts.append('<main id="main">')
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
    parts.append("<div class='table-wrap'><table><tr><th>Prompt</th><th>Generator</th><th>Output</th>"
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
    parts.append("</table></div></main></body></html>")
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
