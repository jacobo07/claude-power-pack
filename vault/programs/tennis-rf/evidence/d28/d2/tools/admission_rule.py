"""WU-D2 step 3: the lint rule source_lint.py lacks. UNDECLARED_MACRO: an ALL-CAPS identifier used in the unit that
nothing in the unit defines (#define, enum constant, typedef/struct name, extern). Under `-nodefaults` mwcc has no
NULL, so m2c's `!= NULL` / `= NULL` fails with "undefined identifier" at 0.01 s. Pure, stdlib-only; same shape as
source_lint.lint_unit (findings are "CODE: detail"). Not wired into source_lint.py (outside this unit's scope)."""
import re

UNDECLARED_MACRO = "UNDECLARED_MACRO"
_TOKEN = re.compile(r"/\*.*?\*/|//[^\n]*|\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'", re.S)
_CAPS = re.compile(r"\b([A-Z][A-Z0-9_]{2,})\b")
_DEFINE = re.compile(r"^\s*#\s*define\s+(\w+)", re.M)
_ENUMC = re.compile(r"\benum\b[^{;]*\{([^}]*)\}")
_DECL_NAME = re.compile(r"\b(\w+)\s*(?:\[[^\]]*\])*\s*[;,=)]")


def strip_noise(text):
    return _TOKEN.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def lint_macros(source_text):
    code = strip_noise(source_text or "")
    defined = set(_DEFINE.findall(code))
    for body in _ENUMC.findall(code):
        defined.update(re.findall(r"\b(\w+)\b\s*(?:=[^,]*)?(?:,|$)", body))
    used = {m for m in _CAPS.findall(code)}
    # names the unit itself declares (typedef/struct/extern names such as a global array) are not macros
    declared = set(re.findall(r"\b(?:struct|typedef|extern)\b[^;{]*?\b(\w+)\b\s*(?:\[[^\]]*\])*\s*[;{]", code))
    missing = sorted(used - defined - declared)
    if missing:
        return ["%s: %s used with no #define in the unit (-nodefaults provides none)" % (UNDECLARED_MACRO, ", ".join(missing[:5]))]
    return []
