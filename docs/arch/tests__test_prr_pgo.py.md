# Architecture Spec -- `tests/test_prr_pgo.py`

<!-- ADS:AUTO -->
_Auto-generated from source by ADS. This block is regenerated on change; edits here are overwritten._

**Files:** 1  ·  **LOC:** 90  ·  **Public symbols:** 6

### Public interface
- `test_profile_reads_epoch_start_growth_and_peak_from_a_recycled_run()` (function, `tests/test_prr_pgo.py`)
- `test_profile_of_an_unrecycled_run_has_no_epoch_start()` (function, `tests/test_prr_pgo.py`)
- `test_ledger_is_append_only_and_refuses_a_duplicate_source(tmp_path)` (function, `tests/test_prr_pgo.py`)
- `test_recommend_admits_with_a_profile_and_refuses_another_plane(tmp_path)` (function, `tests/test_prr_pgo.py`)
- `test_load_skips_corrupt_lines(tmp_path)` (function, `tests/test_prr_pgo.py`)
- `test_profile_refuses_rows_without_samples()` (function, `tests/test_prr_pgo.py`)

### Dependencies
`json`, `pytest`

### Module type
- single-file module
<!-- /ADS:AUTO -->

<!-- ADS:OWNER -->
_Owner-authored. ADS never modifies this block._

- Design decisions: _(Owner-defined; fill in during planning.)_
- Tradeoffs: _(Owner-defined; fill in during planning.)_
- What this module does NOT do: _(Owner-defined; fill in during planning.)_
<!-- /ADS:OWNER -->
