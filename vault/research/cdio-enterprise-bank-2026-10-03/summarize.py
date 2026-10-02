import json, pathlib
here = pathlib.Path(__file__).parent
# Pass 3: carbon, fluent, atlassian, ui5, ant. Pass 4: primer (row-header fix) and the
# Lightning component library example. Passes 1-2 measured doc-page tables and were discarded.
a = json.loads((here / "measure-pass3.json").read_text(encoding="utf-8"))
b = json.loads((here / "measure-pass4.json").read_text(encoding="utf-8"))
bank = {k: a[k] for k in ("carbon", "fluent", "atlassian", "ui5", "ant")}
bank["primer"] = b["primer"]
bank["lightning"] = b["lightning_lwc"]

cols = ["sys", "rowH", "headH", "font", "padL", "ink", "inkR", "headW", "headCase", "headBgR", "tableBg", "zebra", "divider", "ctlH", "actH", "accents", "font family"]
print(" | ".join(cols))
for k in ("carbon", "lightning", "atlassian", "fluent", "primer", "ui5", "ant"):
    m = bank[k]; t = m.get("table") or {}
    d = (t.get("dividers") or [None])[0]
    print(" | ".join(str(x) for x in [
        k, t.get("bodyRowH"), t.get("headRowH"), t.get("cellFont"), t.get("cellPadL"), t.get("cellInk"), t.get("cellInkRatio"),
        t.get("headWeight"), t.get("headTransform"), t.get("headBgVsTable"), t.get("tableBg"),
        len(t.get("rowBgs") or []),
        f"{d['c']} {d['r']}:1 {d['w']}" if d else "none",
        m.get("controlH"), m.get("actionH"),
        ",".join(f"{c}x{n}" for c, n in (m.get("accentFills") or [])[:3]) or "-",
        (m.get("fonts") or [["?"]])[0][0],
    ]))
