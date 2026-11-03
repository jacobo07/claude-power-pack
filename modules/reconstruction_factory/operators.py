"""Source-level rewrite operators. Each operator enumerates SINGLE-SITE rewrites of a source text (`sites(text) -> [new text]`). Operators are
exact inverses of one another where marked (`inverse` names the operator that undoes it; self-inverse ones name themselves), which is how
skeletons are generated: apply inverse operators to a reference source, then search with the forward operators. No operator is language-
or target-specific; the compiler decides whether a rewrite changes the bytes."""
import re

ATOM = r"[A-Za-z_][\w]*(?:(?:->|\.)[A-Za-z_]\w*|\[[\w+\-]+\])*|\d+"


def _swap_binop(sym):
    pat = re.compile(r"(?<![\w)\]])(%s) %s (%s)(?![\w(\[.>])" % (ATOM, re.escape(sym), ATOM))

    def sites(text):
        out = []
        for m in pat.finditer(text):
            if m.group(1) != m.group(2):
                out.append(text[:m.start()] + "%s %s %s" % (m.group(2), sym, m.group(1)) + text[m.end():])
        return out
    return sites


def _flip_cmp(text):
    out = []
    pairs = {"<": ">", ">": "<", "<=": ">=", ">=": "<="}
    for m in re.finditer(r"(?<![\w)\]])(%s) (<=|>=|<|>) (%s)(?![\w(\[.>])" % (ATOM, ATOM), text):
        out.append(text[:m.start()] + "%s %s %s" % (m.group(3), pairs[m.group(2)], m.group(1)) + text[m.end():])
    return out


def _compound(text):
    out = []
    for m in re.finditer(r"\b(\w+(?:\[\w+\])?) = \1 ([+\-|&^]) ([^;]+);", text):
        out.append(text[:m.start()] + "%s %s= %s;" % (m.group(1), m.group(2), m.group(3)) + text[m.end():])
    return out


def _expand(text):
    out = []
    for m in re.finditer(r"\b(\w+(?:\[\w+\])?) ([+\-|&^])= ([^;]+);", text):
        out.append(text[:m.start()] + "%s = %s %s %s;" % (m.group(1), m.group(1), m.group(2), m.group(3)) + text[m.end():])
    return out


def _incr_pre(text):
    return [text[:m.start()] + "++%s" % m.group(1) + text[m.end():] for m in re.finditer(r"\b(\w+)\+\+(?=[;)])", text)]


def _incr_post(text):
    return [text[:m.start()] + "%s++" % m.group(1) + text[m.end():] for m in re.finditer(r"(?<!\+)\+\+(\w+)(?=[;)])", text)]


def _mul_to_shl(text):
    out = []
    for m in re.finditer(r"(?<![\w)\]])(%s) \* (2|4|8|16)(?![\w(\[.>])" % ATOM, text):
        out.append(text[:m.start()] + "%s << %d" % (m.group(1), {"2": 1, "4": 2, "8": 3, "16": 4}[m.group(2)]) + text[m.end():])
    return out


def _shl_to_mul(text):
    out = []
    for m in re.finditer(r"(?<![\w)\]])(%s) << ([1-4])(?![\w])" % ATOM, text):
        out.append(text[:m.start()] + "%s * %d" % (m.group(1), 1 << int(m.group(2))) + text[m.end():])
    return out


def _div_to_shr(text):
    return [text[:m.start()] + "%s >> %d" % (m.group(1), {"2": 1, "4": 2, "8": 3}[m.group(2)]) + text[m.end():]
            for m in re.finditer(r"(?<![\w)\]])(%s) / (2|4|8)(?![\w(\[.>])" % ATOM, text)]


def _shr_to_div(text):
    return [text[:m.start()] + "%s / %d" % (m.group(1), 1 << int(m.group(2))) + text[m.end():]
            for m in re.finditer(r"(?<![\w)\]])(%s) >> ([1-3])(?![\w])" % ATOM, text)]


def _swap_decls(text):
    out = []
    lines = text.split("\n")
    for i in range(len(lines) - 1):
        a, b = lines[i], lines[i + 1]
        if re.match(r"^    [A-Za-z_][\w \*]* \**\w+;$", a) and re.match(r"^    [A-Za-z_][\w \*]* \**\w+;$", b) and a != b:
            out.append("\n".join(lines[:i] + [b, a] + lines[i + 2:]))
    return out


def _braced(text, start):
    """index just past the '}' matching the '{' at text[start]"""
    d = 0
    for i in range(start, len(text)):
        d += text[i] == "{"
        d -= text[i] == "}"
        if d == 0:
            return i + 1
    return -1


_IFELSE = re.compile(r"if \((!\(([^{};]+)\)|([^{};]+))\) \{")


def _swap_ifelse(text):
    out = []
    for m in _IFELSE.finditer(text):
        a_end = _braced(text, m.end() - 1)
        if a_end < 0 or not text[a_end:].startswith(" else {"):
            continue
        b_start = a_end + len(" else ")
        b_end = _braced(text, b_start)
        if b_end < 0:
            continue
        cond = m.group(2) if m.group(2) is not None else "!(%s)" % m.group(3)
        A, B = text[m.end() - 1:a_end], text[b_start:b_end]
        out.append(text[:m.start()] + "if (%s) %s else %s" % (cond, B, A) + text[b_end:])
    return out


def _ret_via_tmp(text):
    out = []
    for m in re.finditer(r"\n(    )return ([^;{}]+);", text):
        if "(" in m.group(2) and not re.search(r"\w\(", m.group(2)):
            continue
        out.append(text[:m.start()] + "\n    {\n        s32 rv;\n        rv = %s;\n        return rv;\n    }" % m.group(2) + text[m.end():])
    return out


def _tmp_inline(text):
    out = []
    for m in re.finditer(r"\n    \{\n        s32 rv;\n        rv = ([^;]+);\n        return rv;\n    \}", text):
        out.append(text[:m.start()] + "\n    return %s;" % m.group(1) + text[m.end():])
    return out


def _neg_eq(text):
    out = []
    for m in re.finditer(r"\(%s\) ?" % "x", text):
        pass
    for m in re.finditer(r"(?<![\w)\]])(%s) (==|!=) (%s)(?![\w(\[.>])" % (ATOM, ATOM), text):
        inv = "!=" if m.group(2) == "==" else "=="
        out.append(text[:m.start()] + "!(%s %s %s)" % (m.group(1), inv, m.group(3)) + text[m.end():])
    return out


def _unneg_eq(text):
    return [text[:m.start()] + "%s %s %s" % (m.group(1), "!=" if m.group(2) == "==" else "==", m.group(3)) + text[m.end():]
            for m in re.finditer(r"!\((%s) (==|!=) (%s)\)" % (ATOM, ATOM), text)]


class Op:
    def __init__(self, name, fn, inverse, family):
        self.name, self.sites, self.inverse, self.family = name, fn, inverse, family


_defs = [
    ("commute_add", _swap_binop("+"), "commute_add", "order"),
    ("commute_mul", _swap_binop("*"), "commute_mul", "order"),
    ("commute_and", _swap_binop("&"), "commute_and", "order"),
    ("commute_or", _swap_binop("|"), "commute_or", "order"),
    ("commute_xor", _swap_binop("^"), "commute_xor", "order"),
    ("commute_eq", _swap_binop("=="), "commute_eq", "order"),
    ("commute_ne", _swap_binop("!="), "commute_ne", "order"),
    ("flip_cmp", _flip_cmp, "flip_cmp", "order"),
    ("compound_assign", _compound, "expand_assign", "style"),
    ("expand_assign", _expand, "compound_assign", "style"),
    ("incr_pre", _incr_pre, "incr_post", "style"),
    ("incr_post", _incr_post, "incr_pre", "style"),
    ("mul_to_shl", _mul_to_shl, "shl_to_mul", "strength"),
    ("shl_to_mul", _shl_to_mul, "mul_to_shl", "strength"),
    ("div_to_shr", _div_to_shr, "shr_to_div", "strength"),
    ("shr_to_div", _shr_to_div, "div_to_shr", "strength"),
    ("swap_decls", _swap_decls, "swap_decls", "layout"),
    ("swap_ifelse", _swap_ifelse, "swap_ifelse", "control"),
    ("ret_via_tmp", _ret_via_tmp, "tmp_inline", "temps"),
    ("tmp_inline", _tmp_inline, "ret_via_tmp", "temps"),
    ("neg_eq", _neg_eq, "unneg_eq", "control"),
    ("unneg_eq", _unneg_eq, "neg_eq", "control"),
]
OPS = {n: Op(n, f, inv, fam) for n, f, inv, fam in _defs}


def apply_all(text, names=None):
    """-> [(op name, new text)] every single-site rewrite, deduplicated, never the identity."""
    seen, out = {text}, []
    for n in (names or OPS):
        for t in OPS[n].sites(text):
            if t not in seen:
                seen.add(t)
                out.append((n, t))
    return out
