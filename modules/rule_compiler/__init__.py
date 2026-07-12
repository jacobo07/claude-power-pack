"""Rule Compiler (P1) -- hard rules become a compiled, validated artifact.

Sealed by the AKOS macro audit (2026-07-12). The kill switch was inert:
the router named a section that does not exist, and the file that holds
the rules is ~361 KB against a 256 KB tool read limit. Both branches
dead-ended, on every production write, deploy, done-claim and plugin
install.

    from modules.rule_compiler import compile_rules, write_artifacts
    res = compile_rules()
    write_artifacts(res)
"""
from .compiler import (
    DB_PATH,
    DIGEST_PATH,
    REJECTIONS_PATH,
    CompileResult,
    compile_rules,
    show,
    write_artifacts,
)
from .digest import DIGEST_MAX_BYTES, TRIGGER_CLASSES, classify
from .schema import REASON_HELP, Form, Reason, Rule, validate

__all__ = [
    "CompileResult", "compile_rules", "write_artifacts", "show",
    "DIGEST_PATH", "DB_PATH", "REJECTIONS_PATH", "DIGEST_MAX_BYTES",
    "TRIGGER_CLASSES", "classify",
    "Rule", "Form", "Reason", "REASON_HELP", "validate",
]
