"""
Allows `python -m sleepless_qa` to dispatch to the CLI.

The package directory is `sleepless_qa` (underscore) so `python -m sleepless_qa`
resolves correctly. User-facing brand strings keep the hyphen (`sleepless-qa`).
"""

from .cli import main

if __name__ == "__main__":
    import sys
    sys.exit(main())
