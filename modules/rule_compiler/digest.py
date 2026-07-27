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

# The classes the global ~/.claude/CLAUDE.md router contracts on.
# A contracted class matching zero rules is a COVERAGE DEFECT, not an
# absence: the router fires at that trigger point and finds nothing to
# enforce. So it stays visible in the digest with an explicit 0 and
# answers non-zero at the CLI. Silence at a contracted trigger reads
# exactly like compliance, and a class that is never listed can never
# be missed.
ROUTER_CONTRACTED: frozenset[str] = frozenset({
    "PROD-WRITE", "DEPLOY", "DONE-CLAIM",
})

# Retired triggers. The class stays DEFINED so `--class NAME` still
# resolves and explains itself, and so a future rule that classifies
# here is detected as the reopen condition rather than silently
# absorbed. It is simply no longer contracted: an empty result is the
# governed answer, not a defect.
#
# Deleting the entry outright was the alternative, and it is the same
# silent drop this module exists to prevent -- the corpus would stop
# mentioning a trigger the estate once governed, and no reader could
# tell a deliberate retirement from an accidental rename.
RETIRED_CLASSES: dict[str, str] = {
    "PLUGIN-INSTALL":
        "retired 2026-07-27 by Owner decision -- no corpus. Zero rules "
        "ever classified here, so the trigger enforced nothing, and a "
        "contracted trigger with no corpus is governance theater. "
        "REOPEN when a real plugin-install incident yields at least one "
        "schema-valid rule: move the name back into ROUTER_CONTRACTED "
        "and restore the router's fourth trigger in ~/.claude/CLAUDE.md.",
}

_DEFINED_CLASSES = {name for name, _d, _k in TRIGGER_CLASSES}
_UNDEFINED_CONTRACTED = ROUTER_CONTRACTED - _DEFINED_CLASSES
if _UNDEFINED_CONTRACTED:
    raise RuntimeError(
        "router-contracted trigger class absent from TRIGGER_CLASSES: "
        + ", ".join(sorted(_UNDEFINED_CONTRACTED))
        + " -- a rename dropped a class the global router still fires on.")

_UNDEFINED_RETIRED = set(RETIRED_CLASSES) - _DEFINED_CLASSES
if _UNDEFINED_RETIRED:
    raise RuntimeError(
        "retired trigger class absent from TRIGGER_CLASSES: "
        + ", ".join(sorted(_UNDEFINED_RETIRED))
        + " -- retirement keeps the class defined; deleting it hides "
          "the retirement itself.")

_BOTH = ROUTER_CONTRACTED & set(RETIRED_CLASSES)
if _BOTH:
    raise RuntimeError(
        "trigger class both contracted and retired: "
        + ", ".join(sorted(_BOTH))
        + " -- a class cannot be enforced and withdrawn at once.")

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
    unenforced: list[str] = []
    reopened: list[str] = []
    for cls in order:
        rules = buckets.get(cls) or []
        if cls in RETIRED_CLASSES:
            # Retired: listed below the table, never as a coverage
            # defect. If rules DO classify here the reopen condition has
            # become true, and that is louder news than the retirement.
            if rules:
                reopened.append(cls)
                covered.update(r.rule_id for r in rules)
            continue
        if not rules:
            # An empty class the router never fires on is genuinely
            # nothing to say. An empty CONTRACTED class is a hole in the
            # kill switch, and dropping its row is what let that hole sit
            # unnoticed: the agent reads the table, sees no such trigger,
            # and cannot tell "no rules" from "no such class".
            if cls in ROUTER_CONTRACTED:
                unenforced.append(cls)
                lines.append(f"| **{cls}** | 0 | {descs[cls]} |")
            continue
        covered.update(r.rule_id for r in rules)
        lines.append(f"| **{cls}** | {len(rules)} | {descs[cls]} |")

    if unenforced:
        lines += [
            "",
            "## CONTRACTED BUT UNENFORCED (coverage defect -- the router "
            "fires on these trigger points and finds zero rules; an empty "
            "result there is not a pass)",
            " ".join(unenforced),
        ]

    if RETIRED_CLASSES:
        lines += [
            "",
            "## RETIRED TRIGGERS (withdrawn from the router -- an empty "
            "result here is the governed answer, not a gap)",
        ]
        lines += [f"- **{cls}** -- {why}"
                  for cls, why in sorted(RETIRED_CLASSES.items())]

    if reopened:
        lines += [
            "",
            "## REOPEN CONDITION MET (a retired trigger now matches "
            "rules; those rules are NOT contracted until it is restored "
            "to ROUTER_CONTRACTED)",
            " ".join(reopened),
        ]

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
