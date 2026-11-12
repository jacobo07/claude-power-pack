"""Coordinator (c84eb8e1) independent check of S34K oc/oracle16.jsonl with own DOL + ELF readers (indep_check.py),
not s26c_oracle. Per id: (1) target fn bytes from the stage capsule object (cohort path) via the coordinator ELF reader;
(2) ORIGINAL DOL bytes at the id address via the coordinator DOL reader, masking only the object's own relocation
words; (3) sha256 of those bytes must equal the oracle row's code_sha256 AND the S30K candidate's own_fn_sha256
(the compiled exact). Negative control: the same code vs DOL at address+4 must differ."""
import hashlib, importlib.util, json, sys
sys.path = [p for p in sys.path if p not in ("/tmp", "")]  # /tmp holds stray modules (dis.py) that shadow the stdlib
_spec = importlib.util.spec_from_file_location("indep_check", "/home/kobii/agora/indep-c84/indep_check.py")
ic = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ic)  # chdir to t1; DOL path; dol_reader; elf_fn

CAPSULE = "/home/kobii/ksr_stage/ksrmb-s25-20261111-140212/capsule"
OC = "evidence/ascension/s34k/oc/"
cohort = json.load(open(OC + "cohort.json"))
rows = {r["id"]: r for r in map(json.loads, open(OC + "oracle16.jsonl"))}
held = {}
for line in open(cohort["source"]):
    r = json.loads(line)
    if r["id"] in cohort["ids"] and r.get("canon_arm") and r.get("state") == "BINARY_EXACT":
        held[r["id"]] = r
read, dsha = ic.dol_reader(ic.DOL)
print("DOL", dsha[:16], "ids", len(cohort["ids"]), "oracle rows", len(rows), "heldout rows", len(held))
ok = neg = 0
bad = []
for i in cohort["ids"]:
    r, h = rows.get(i), held.get(i)
    if not r or not h:
        bad.append((i, "NO_ROW")); continue
    code, masked = ic.elf_fn(f"{CAPSULE}/{cohort['objs'][i]}", r["sym"])
    addr = int(i.split(":")[1], 16)
    eq = lambda d: all(code[w:w + 4] == d[w:w + 4] for w in range(0, len(code), 4) if w not in masked)  # noqa: E731
    same, shifted = eq(read(addr, len(code))), eq(read(addr + 4, len(code)))
    csha = hashlib.sha256(code).hexdigest()
    chain = csha == r["code_sha256"] == h["own_fn_sha256"]
    neg += not shifted
    if same and chain and len(code) == r["size"]:
        ok += 1
    else:
        bad.append((i, f"dol={same} chain={chain} size={len(code)}/{r['size']}"))
    print(i, r["sym"], f"{len(code)}B", "masked", len(masked), "DOL", "MATCH" if same else "DIFF",
          "chain", "OK" if chain else "BROKEN", "neg+4", "DIFF" if not shifted else "SAME")
n = len(cohort["ids"])
print(f"INDEP_S34K ok {ok}/{n} neg_detected {neg}/{n} bad {bad}")
print("INDEP_S34K_PASS" if n > 0 and ok == n and not bad and neg == n else "INDEP_S34K_FAIL")
