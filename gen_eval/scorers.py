"""Node 4: score.

Every check is a tiny function that returns (passed, reason).
No AI is involved: the rules are transparent, so you can explain each result.
A prompt passes only if ALL of its checks pass.

Future work: an optional "llm_judge" check could ask a model to grade the
output. It is not implemented here.
"""

import re
from typing import Dict, List, Tuple


def count_words(text: str) -> int:
    """Count words by splitting on whitespace."""
    return len(text.split())


def check_max_words(text: str, limit: int) -> Tuple[bool, str]:
    n = count_words(text)
    if n <= limit:
        return True, str(n) + " words, limit is " + str(limit)
    return False, str(n) + " words, over the limit of " + str(limit)


def check_min_words(text: str, minimum: int) -> Tuple[bool, str]:
    n = count_words(text)
    if n >= minimum:
        return True, str(n) + " words, minimum is " + str(minimum)
    return False, str(n) + " words, under the minimum of " + str(minimum)


def check_must_include(text: str, phrases: List[str]) -> Tuple[bool, str]:
    lowered = text.lower()
    missing = []
    for phrase in phrases:
        if phrase.lower() not in lowered:
            missing.append(phrase)
    if len(missing) == 0:
        return True, "all required phrases found"
    return False, "missing: " + ", ".join(missing)


def check_must_not_include(text: str, phrases: List[str]) -> Tuple[bool, str]:
    lowered = text.lower()
    found = []
    for phrase in phrases:
        if phrase.lower() in lowered:
            found.append(phrase)
    if len(found) == 0:
        return True, "no banned phrases found"
    return False, "found banned: " + ", ".join(found)


def check_regex(text: str, pattern: str) -> Tuple[bool, str]:
    if re.search(pattern, text) is not None:
        return True, "matches pattern " + pattern
    return False, "does not match pattern " + pattern


def check_no_digits(text: str) -> Tuple[bool, str]:
    """Useful for TTS: numbers should be written out as words."""
    digits = re.findall(r"[0-9]", text)
    if len(digits) == 0:
        return True, "no digits"
    return False, "contains " + str(len(digits)) + " digit(s)"


def run_check(check: Dict, text: str) -> Tuple[bool, str]:
    """Pick the right check function based on check["type"]."""
    kind = check.get("type")
    if kind == "max_words":
        return check_max_words(text, check["value"])
    if kind == "min_words":
        return check_min_words(text, check["value"])
    if kind == "must_include":
        return check_must_include(text, check["value"])
    if kind == "must_not_include":
        return check_must_not_include(text, check["value"])
    if kind == "regex":
        return check_regex(text, check["value"])
    if kind == "no_digits":
        return check_no_digits(text)
    raise ValueError("Unknown check type: " + str(kind))


def score(text: str, checks: List[Dict]) -> Dict:
    """Run all checks on `text`. Returns {"passed": bool, "checks": [...]}."""
    results = []
    all_passed = True
    for check in checks:
        passed, reason = run_check(check, text)
        results.append({"type": check["type"], "passed": passed, "reason": reason})
        if not passed:
            all_passed = False
    return {"passed": all_passed, "checks": results}
