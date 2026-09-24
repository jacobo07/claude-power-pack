"""Product demo capability: real software flows -> reproducible, validated demo videos.

Pipeline (each stage is its own module, each hands the next a file on disk):
    spec       semantic demo spec (targets by role/label/testid, beats, stages, budget)
    capture    drive the REAL product in a bounded child; settled-state frames + telemetry
    timeline   presentation time map, synthetic cursor path, anchored callouts
    stage      HTML composition implementing the motion-promo film contract
    render     skills/motion-promo/scripts/render_film.py, run bounded
    validate   four-outcome verdict on the rendered artifact
    manifest   provenance envelope; staleness compares a later probe against it

Clean-room implementation (see vault/knowledge_base/product_demo/recordly-disposition.md).
"""
