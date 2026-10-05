"""Is hook_success stdout part of model context? Regress per-interval context growth on text features (zero-model).
Positive control: tool_result chars and rendered chars must get coefficient ~0.2-0.4 tok/char; a feature with coefficient ~0 is not context.
Negative control: a shuffled hs_out column must also give ~0 (instrument can return 0)."""
import json, sys, random
import numpy as np
S = json.load(open(sys.argv[1]))
rows = []
for s in S:
    c = s["calls"]
    for i, f in enumerate(s["feats"]):
        if i + 1 >= len(c): break
        d = c[i + 1][1] - c[i][1]
        if d < 0 or d > 120000: continue  # compaction / resume jumps
        rows.append((d, c[i][2], f["tr"], f["ut"], f["rend"] - f["rend_hac"], f["rend_hac"], f["hs_out"]))
A = np.array(rows, float); y = A[:, 0]
names = ["out_tok", "tool_result", "user_text", "rendered_other", "rendered_hook_ctx", "hook_success_stdout"]
X = A[:, 1:]
def fit(X, label):
    # robust-ish: drop top 1% residual rows after first fit
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    r = y - X @ b; keep = np.abs(r) < np.quantile(np.abs(r), 0.99)
    b2 = np.linalg.lstsq(X[keep], y[keep], rcond=None)[0]
    print(label, "n", int(keep.sum()), " ".join(f"{n}={v:.3f}" for n, v in zip(names, b2)))
    return b2
print("intervals", len(y), "sum growth", int(y.sum()))
fit(X, "REAL")
Xs = X.copy(); random.seed(1); idx = list(range(len(y))); random.shuffle(idx); Xs[:, 5] = X[idx, 5]
fit(Xs, "SHUFFLED hook_success_stdout (negative control)")
nz = X[:, 5] > 0
print("intervals with hook_success stdout >0:", int(nz.sum()), "of", len(y), "mean stdout chars there", X[nz, 5].mean())
# direct contrast: mean growth beyond expected for intervals with/without hook_success
b = fit(X[:, :5], "WITHOUT hook_success column") if False else None
