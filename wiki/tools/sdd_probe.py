"""Live probe of SDD-OS claims, using the real modules against a temp repo."""
import sys, tempfile, pathlib
sys.path.insert(0, r"C:\Users\User\.claude\skills\claude-power-pack")
from modules.spec_gate.gate import classify_tier
from modules.sdd_os.pre_exec_gate import evaluate

print("== tier classification ==")
for p in ["add a billing endpoint for invoices",
          "refactor the APIs and modules for invoices",
          "refactor the api module for invoices",
          "change the cron schedule to run hourly and drop the old table",
          "rename get_user to fetch_user across the public SDK",
          "do the thing we discussed yesterday"]:
    r = classify_tier(p)
    print(f"T{r.tier}  {p!r}  reason={getattr(r, 'reason', '')!s:.70}")

print("\n== empty-skeleton binding ==")
task = "add a billing endpoint for invoices"
with tempfile.TemporaryDirectory() as d:
    root = pathlib.Path(d)
    ctrl = evaluate(task, root)  # control: no spec at all
    print(f"control(no spec): tier={ctrl.tier} action={ctrl.action}")
    (root / "vault" / "specs").mkdir(parents=True)
    (root / "vault" / "specs" / "empty.md").write_text(
        "---\ncovers: [billing]\nstatus: draft\ntier: 2\n---\n\n## Acceptance criteria\n\nAC-001:\n",
        encoding="utf-8")
    dec = evaluate(task, root)
    print(f"empty draft spec: tier={dec.tier} action={dec.action} spec={dec.spec_path.name if dec.spec_path else None}")
    unrelated = "fix billing typo in the README footer"
    dec2 = evaluate(unrelated, root)
    print(f"unrelated task sharing token 'billing': tier={dec2.tier} action={dec2.action}")
