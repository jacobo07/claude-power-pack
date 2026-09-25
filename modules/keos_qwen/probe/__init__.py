"""Measurements that answer a question, as opposed to gates that defend one.

A gate runs forever and must never be wrong. A probe runs once, answers, and is
read. Keeping them in different packages stops a probe's convenient assumption
from quietly becoming a gate's contract.

ASCII only: `open(path, "w")` truncates before encoding, and the GEX44 VM warns
it runs with latin1 native name encoding whenever a unit's locale is unpinned.
"""
