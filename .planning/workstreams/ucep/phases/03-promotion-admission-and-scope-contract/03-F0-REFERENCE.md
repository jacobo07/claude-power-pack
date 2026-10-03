# Phase 3 F0 reference: the seven grandfathered generation files

Measured by the orchestrator (epoch 3) at HEAD `d61b5c23`, before any Phase 3 execution. The SHA-256 is
over the exact worktree bytes. All seven files hold no CR (`crlf_in_worktree=False`), so these are the
LF bytes. Command: `[System.Security.Cryptography.SHA256]` over `[IO.File]::ReadAllBytes`, for each
`vault/tower/baselines/**/B*.json`.

This file is independent of whatever table the executor pins in code. At the end of Phase 3, both must
agree with each other, and both must agree with a fresh measurement. If the code table matches itself
but not this file, it was derived from the post-state.

| sha256 | file |
|---|---|
| 1a50144150bf7134c966fd832a368a18958a363a7fb8cfc9bbe8ea481a0a2407 | vault/tower/baselines/kobiicraft_mode/B0.json |
| bcb20d37f568a8873710990e4e43351010e882ac6fcd0f38b1e387a1d674dc64 | vault/tower/baselines/persistent_state/B0.json |
| 0586c6a27eba0fdd3a7793c8e8ed32bd5ab9104cb09085faba7b456af8f315f2 | vault/tower/baselines/persistent_state/B1.json |
| 98e8d33fef37ae75732cd92694d4ef20bd68ce8649c3239f6dfd8d16a5eea2d7 | vault/tower/baselines/web_surface/B0.json |
| 2e54ac452ac256703fb5a3d9b8252ed30a903ab3d64f651c16174727ee5cd8e1 | vault/tower/baselines/web_surface/B1.json |
| 2603cf39889cb421c9fd31968b706d68a79aa7f14539173a4eb669761a4bc1bd | vault/tower/baselines/wii_homebrew/B0.json |
| f255befaed5f66238361f74f47c71523802fab90a05119dfc9198355ac43451a | vault/tower/baselines/wii_homebrew/B1.json |

Cross-check: the tower injection hook printed `persistent_state/B0 (sha256 bcb20d37f568)` this session,
and that matches row 2.
