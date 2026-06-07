"""CPP Setup OS -- BL-SETUP-OS-001 (Sprint 3).

Superior-to-official-plugin setup OS: it EXECUTES (scan -> ROI -> secure
install + rollback), not just recommends.

Public API:
  * scanner: scan, summarize, ProjectProfile, Field, Source
  * roi_analyzer: analyze, Recommendation
  * secure_installer: dry_run, InstallPlan
"""
from .scanner import Field, ProjectProfile, Source, scan, summarize

# Only the import-safe scanner is eager. roi_analyzer / secure_installer
# are imported from their submodules by consumers
# (from modules.setup_os.roi_analyzer import analyze) -- keeping them out
# of __init__ avoids the runpy double-import warning under `-m`.
__all__ = ["Field", "ProjectProfile", "Source", "scan", "summarize"]
