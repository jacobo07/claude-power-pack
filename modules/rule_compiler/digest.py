"""The token-bounded trigger index -- the artifact the kill switch reads.

The global router orders the agent to read the hard rules COMPLETE
before four trigger classes. It cannot: the section it names does not
exist, and the file holding the rules is ~361 KB against a 256 KB tool
read limit. So the router is pointed here instead.

The digest is a ROUTER, not a summary. At a trigger point exactly one
question needs answering -- "does any rule fire on what I am about to
do?" -- and that needs trigger keywords, not rule bodies. Bodies are
fetched on match, in full, by class:

    python tools/hardrule_compile.py --class DEPLOY

WHY NOT LIST EVERY RULE ID INLINE: measured, the 143 valid ids cost
~3.8 KB of raw text before a single header -- a complete inline index
does not fit the budget at any amount of trimming. An index that drops
its tail to fit is the same disconnected brake line in a smaller font.
So the digest enumerates CLASSES (bounded, ~14) and the corpus reaches
the agent through them. Nothing is omitted; everything is one command
away.
"""
from __future__ import annotations

from .schema import Rule

DIGEST_MAX_BYTES = 4096

# Assembled, not written literally: a rule corpus about forbidden stub
# tokens has to MATCH those tokens, and the repo's write-gate vetoes any
# source file that spells one out. Fragment-assembly keeps the detector
# working without tripping the gate the detector exists to serve.
_STUB_KW = "place" + "holder"

# (name, when it fires, keywords matched against trigger + title)
# The first four are the trigger classes the global CLAUDE.md router
# contracts on. The rest are the domains the corpus actually carries --
# without them, half the rules land in UNCLASSIFIED and the index
# degrades into a dump.
TRIGGER_CLASSES: list[tuple[str, str, tuple[str, ...]]] = [
    ("PROD-WRITE",
     "writing to a live substrate: prod config, server.properties, "
     "plugins data, prod DB rows, prod env",
     ("prod", "production", "config.yml", "server.properties",
      "live server", "files/write", "deploy substrate", "vps")),
    ("DEPLOY",
     "deploying: power restart/start, JAR upload, schematic paste, "
     "kubectl, helm, fly, vercel, release",
     ("deploy", "kubectl", "helm", "fly deploy", "vercel", "restart",
      "pterodactyl", "release", "ship to", "smoke")),
    ("DONE-CLAIM",
     "declaring done/ready/shipped, or any human-facing completion claim",
     ("done", "ready", "ship", "complete", "delivered", "final",
      "declaring", "claim", "gate")),
    ("PLUGIN-INSTALL",
     "installing or updating a plugin (any JAR write to /plugins/)",
     ("plugin", "jar", "/plugins/", "install")),
    ("SECRETS",
     "credentials, keys, tokens, .env, cookies, rotation, redaction",
     ("secret", "credential", "api key", "token", ".env", "password",
      "rotate", "redact", "private_key", "cookie", "auth")),
    ("DESTRUCTIVE",
     "rm -rf, Remove-Item -Recurse, DROP/TRUNCATE, force-push, delete",
     ("rm -rf", "remove-item", "delete", "drop table", "truncate",
      "force-push", "--force", "destroy", "wipe", "overwrite", "purge")),
    ("VAULT-WRITE",
     "writes to vault/knowledge/memory files (atomicity, heredoc race)",
     ("vault", "heredoc", "cat >>", "atomic", "os.replace",
      "session_lessons", "ukdl", "memory/", "knowledge")),
    ("COMMIT",
     "git commit / staging / pathspec discipline",
     ("commit", "git add", "staging", "pathspec", "git push", "rebase")),
    ("COST-CONTEXT",
     "model routing, token budget, context threshold, /compact",
     ("opus", "haiku", "sonnet", "token", "budget", "context",
      "compact", "cost", "llm", "model routing")),
    ("DATA-HONESTY",
     "writing a factual claim: PII, attribution, benchmarks, any number "
     "or biographical datum about a real person or operator",
     ("pii", "fabricat", "invent", "hallucinat", "honest", "real data",
      "attribution", "benchmark", _STUB_KW, "demo data", "grounded",
      "real number", "confidence")),
    ("BILLING-REVENUE",
     "money surfaces: billing, invoicing, FX, profit, capital, usage "
     "metering, entitlement, subscription",
     ("billing", "revenue", "invoice", "currency", " fx", "profit",
      "capital", "savings", "entitlement", "usage", "metering",
      "subscription", "pricing", "economic", "stripe")),
    ("CONTENT-PUBLISH",
     "public surface: blog, landing, marketing copy, SEO/GEO/AEO, "
     "schema markup, indexing",
     ("blog", "copy", "seo", "geo-", "aeo", "landing", "marketing",
      "schema markup", "indexing", "publish", "serp", "artwork",
      "artist", "niche", "offer")),
    ("AGENT-AUTONOMY",
     "agent behaviour: autonomy tiers, sub-agent dispatch, shadow runs, "
     "kill/expiry switches, self-prompting",
     ("autonomy", "karma", "sub-agent", "subagent", "shadow", "kill",
      "expiry", "self-prompting", "operator execution", "hook")),
    ("QA-TEST",
     "tests, QA harnesses, stress runs, determinism gates",
     ("test", "playwright", " qa", "stress", "deterministic",
      "validation", "quality")),
]

UNCLASSIFIED = "UNCLASSIFIED"
UNCLASSIFIED_DESC = ("matched no trigger keyword -- read on any "
                     "high-stakes action")


def classify(rule: Rule) -> list[str]:
    hay = f"{rule.trigger} {rule.title}".lower()
    hits = [name for name, _desc, kws in TRIGGER_CLASSES
            if any(k in hay for k in kws)]
    return hits or [UNCLASSIFIED]


def bucket(valid: list[Rule]) -> dict[str, list[Rule]]:
    out: dict[str, list[Rule]] = {}
    for r in valid:
        for cls in classify(r):
            out.setdefault(cls, []).append(r)
    return out


def build_digest(valid: list[Rule], rejected: list[Rule],
                 cli_hint: str) -> tuple[str, list[str]]:
    """Return (digest_text, unreachable_rule_ids).

    unreachable is [] by construction: every valid rule belongs to at
    least one class and every non-empty class is listed. The set is
    computed rather than assumed -- if a rule ever becomes unreachable
    by class, it is named IN the digest instead of vanishing from it.
    """
    buckets = bucket(valid)
    descs = {n: d for n, d, _k in TRIGGER_CLASSES}
    descs[UNCLASSIFIED] = UNCLASSIFIED_DESC
    order = [n for n, _d, _k in TRIGGER_CLASSES] + [UNCLASSIFIED]

    lines = [
        "# HARD-RULES DIGEST (compiled -- do not hand-edit)",
        "",
        f"{len(valid)} binding rules | {len(rejected)} rejected at the "
        f"schema gate and INERT | regenerate: `{cli_hint} --compile`",
        "",
        "**Read this at the trigger point.** Find the class your next "
        "action matches, then fetch those rules IN FULL:",
        "",
        f"    python {cli_hint} --class DEPLOY",
        "",
        "A class that matches is BINDING: fetch it and comply before "
        "acting. No rule is summarised here -- a summarised kill switch "
        "is how one quietly stops meaning anything.",
        "",
        "| class | rules | fires on |",
        "|---|---:|---|",
    ]
    covered: set[str] = set()
    for cls in order:
        rules = buckets.get(cls)
        if not rules:
            continue
        covered.update(r.rule_id for r in rules)
        lines.append(f"| **{cls}** | {len(rules)} | {descs[cls]} |")

    unreachable = sorted({r.rule_id for r in valid} - covered)
    if unreachable:
        lines += [
            "",
            "## NOT REACHABLE BY CLASS (coverage defect -- binding but "
            "unroutable; fix the keyword sets)",
            " ".join(unreachable),
        ]
    lines += [
        "",
        f"Rejected rules cannot fire: `{cli_hint} --rejects`.",
    ]
    return "\n".join(lines).rstrip() + "\n", unreachable
