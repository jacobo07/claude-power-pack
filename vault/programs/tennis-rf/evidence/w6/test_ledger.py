"""RED-first tests for ledger.classify (synthetic call sequences, no transcripts)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import ledger


def C(tools=(), text=False, last=False):
    return {"tools": list(tools), "has_text": text}


def T(name, **inp):
    return {"name": name, "input": inp, "error": False}


def cats(seq):
    return [c for c in ledger.classify(seq)]


def test_first_is_startup():
    assert cats([C([T("Read", file_path="a")])])[0] == "STARTUP"


def test_reread_unchanged_vs_after_edit():
    s = [C(), C([T("Read", file_path="x.s")]), C([T("Read", file_path="x.s")]),
         C([T("Edit", file_path="x.py")]), C([T("Read", file_path="x.py")])]
    out = cats(s)
    assert out[1] == "READ" and out[2] == "REREAD" and out[4] == "READ"


def test_search_control_proof():
    s = [C(), C([T("Grep", pattern="a")]), C([T("PowerShell", command="& $g log -n 3")]),
         C([T("PowerShell", command="python -I test_x.py")])]
    assert cats(s)[1:] == ["SEARCH", "CONTROL", "PROOF"]


def test_repair_after_red_proof_and_recovery():
    red = T("PowerShell", command="python test_x.py"); red["error"] = True
    s = [C(), C([red]), C([T("Edit", file_path="tools/a.py")]),
         C([dict(red)])]
    out = cats(s)
    assert out[2] == "REPAIR"
    assert out[3] == "RECOVERY"


def test_semantic_before_edit_and_receipt():
    s = [C(), C([], text=True), C([T("Write", file_path="evidence/w6/t.py")]),
         C([T("Write", file_path="WU-W6-receipt.md")])]
    out = cats(s)
    assert out[1] == "SEMANTIC" and out[2] == "IMPLEMENT" and out[3] == "RECEIPT"
