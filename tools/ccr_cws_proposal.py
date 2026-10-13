#!/usr/bin/env python3
"""ccr_cws_proposal.py -- Minimum safe CWS for the short lookup class: PROPOSAL ONLY, not enforced.

Plan: vault/plans/ccr-v4-stage3-2026-10-13.md, unit A2 item 3. The TypeScript form of this proposal is
vault/programs/ccr/stage3/a2/cws-short-lookup.patch (not applied to mods/cpp-cognitive-runtime).

A short lookup reads a few files and answers; it never writes. Its closure keeps in front only the read
tools plus ToolSearch (the runtime's page tool is always kept), and on top of the bounded-code-worker
drops it drops the two attachment kinds that A2 measured as kept but unused by such a task. It KEEPS
deferred_tools_delta: that list is how a withheld tool is found again (a page fault), so dropping it
would turn a cheap fault into a failure. That is the "safe" in minimum safe.

`simulate` projects the call-1 saving on measured sessions from the attachment bytes they actually
sent. Tool schemas removed by the narrower tool list are NOT projected: the receipts hold no schema
bytes for tools kept in front, so that part stays UNKNOWN until a probe with --tools Read,Grep,Glob.
"""
from __future__ import annotations

BASE_UNIT_DROPS = frozenset({'skill_listing', 'agent_listing_delta', 'mcp_instructions_delta'})

PROPOSAL = {
    'class': 'short-lookup',
    'tools': ('Read', 'Grep', 'Glob', 'ToolSearch'),
    'drop_attachments': BASE_UNIT_DROPS | {'hook_additional_context', 'remote_session_change'},
    'drop_sections': frozenset({'memory'}),
    'keep_required': frozenset({'deferred_tools_delta', 'environment', 'model', 'date', 'session_context'}),
}
WRITE_TOOLS = frozenset({'Edit', 'Write', 'NotebookEdit', 'Bash', 'PowerShell'})


def decide_attachment(type_: str, proposal: dict = PROPOSAL) -> str:
    if type_ == 'instructions':
        return 'replace'  # kernel + index, as for every unit
    return 'drop' if type_ in proposal['drop_attachments'] else 'keep'


def decide_tool(tool: str, proposal: dict = PROPOSAL) -> str:
    if tool.endswith('cpp-cognitive-runtime__page') or tool == 'page':
        return 'keep'
    return 'keep' if tool in proposal['tools'] else 'defer'


def check_safe(proposal: dict = PROPOSAL) -> list[str]:
    """Violations of the safety invariants; empty means the proposal is admissible for a canary."""
    bad = []
    if 'ToolSearch' not in proposal['tools']:
        bad.append('ToolSearch not in front: deferred tools become unreachable')
    for t in sorted(proposal['keep_required'] & proposal['drop_attachments']):
        bad.append(f'drops required attachment {t}')
    for t in sorted(WRITE_TOOLS & set(proposal['tools'])):
        bad.append(f'write-capable tool {t} in front of a read-only class')
    return bad


def simulate(facts: dict, bpt: float, proposal: dict = PROPOSAL) -> dict:
    """Projected call-1 tokens removed beyond what the session already sent (attachments only)."""
    removed = {}
    for t, sent in facts['attach1'].items():
        if sent and decide_attachment(t, proposal) == 'drop':
            removed[t] = round(sent / bpt)
    total = sum(removed.values())
    return {'sid': facts['sid'], 'ctx1': facts['ctx1'], 'removed': removed, 'removed_tokens': total,
            'projected_ctx1': facts['ctx1'] - total, 'tool_schema_saving': 'UNKNOWN'}
