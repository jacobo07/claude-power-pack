# MCP vid-analyzer end-to-end verification plan

**Started:** 2026-05-24T18:12:07Z
**Mode:** EXECUTION (Agent Teams / desatendido), approved inline by Owner.
**Server:** https://paging-pushpin-sandworm.ngrok-free.dev/mcp (note: `.dev` not `.app`; `.app` is offline)
**Source:** `C:\Users\User\Apps\mcp-video-analyzer\server.py`
**Tools to verify:** analyze_video, analyze_video_url (NEW), transcribe_audio, extract_frames

## Test sources

- M2 small (~2.5 MB): `https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4`
- M9 cap-test (~108 MB, used with max_download_mb=10 to trip cap quickly): `https://download.blender.org/peach/bigbuckbunny_movies/big_buck_bunny_480p_h264.mov`
- M10 SSRF: `http://example.com/video.mp4`
- M11 non-video: `https://example.com/index.html`

## Status

| # | Step | Status | Evidence file/section |
|---|---|---|---|
| M1 | tools/list returns 4 | pending | inline below |
| M2 | analyze_video_url with small mp4 | pending | inline |
| M3 | header inspection across routes | pending | inline |
| M4 | (cond) ngrok header middleware | predicted-skip | inline |
| M5 | Owner: reconnect connector in claude.ai | pending (Owner action) | Owner-reported |
| M6 | Owner: prompt LLM with attached video | pending (Owner action) | Owner-reported |
| M7 | server log captures CallToolRequest | pending | server log tail |
| M8 | output: real transcript, no error | pending | tool result |
| M9 | >100MB → hard cap fires cleanly | pending | inline |
| M10 | http:// → SSRF rejection | pending | inline |
| M11 | non-video URL → typed error | pending | inline |
| M12 | (cond) fallback if M6 fails | conditional | inline |
| M13 | MCP-COMPLETION-STANDARD.md drafted | pending | knowledge_vault/core/ |
| M14 | standard committed | pending | git log |
| M15 | session_lessons.md updated | pending | vault/knowledge_base/ |
| M16 | UKDL updated | pending | vault/knowledge_base/ |
| M17 | smoke-test script for MCPs | pending | tools/ or modules/ |
| M18 | final commit | pending | git log |
| M19 | PANE C → DONE-VERIFIED | flag-pending-clarification | (await Owner) |

## Evidence log appended below as execution proceeds.

### M1 PASS (2026-05-24T18:14Z)
`tools/list` returned 4 tools: analyze_video, analyze_video_url, transcribe_audio, extract_frames. `analyze_video_url` required field = `url`.

### M3 PASS (M4 SKIP) (2026-05-24T18:14Z)
3 routes inspected (/.well-known/oauth-protected-resource/mcp, /.well-known/oauth-authorization-server, /mcp). All return `application/json` Content-Type. NO ngrok HTML interstitial on any path. The `ngrok-skip-browser-warning` middleware is not needed for this server (M4 skipped as predicted).

### Latent dependency bug found mid-execution (2026-05-24T18:24Z)
First M2 attempt failed at the tool level with `Error executing tool analyze_video_url: ffmpeg not found.` Root cause: the dependency `imageio-ffmpeg` (declared in requirements.txt) was not actually installed in the runtime Python (`C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`). Server's `_find_ffmpeg()` tried `shutil.which("ffmpeg")` (no), `MCP_FFMPEG_PATH` env (unset), `import imageio_ffmpeg` (ImportError) and finally raised. Fix applied: `pip install imageio-ffmpeg` (0.6.0); bundled ffmpeg binary now at `Python312\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe` (87 MB). Server restarted via Task Scheduler. **Lesson**: requirements.txt is not enough — the runtime Python may have been provisioned without it. Add a smoke-test that imports every requirement at boot.

### M2 PASS (2026-05-24T18:26Z)
Source: `https://media.w3.org/2010/05/sintel/trailer.mp4` (first source `commondatastorage.googleapis.com` gave HTTP 403; switched to w3.org). Elapsed 26.5s, downloaded 4.2 MB, extracted 8 frames, transcribed audio (English, p=0.943, 51.93s duration, 4 segments). Output begins `# Video Analysis ... [0:11] What brings you to t...`. End-to-end real result, no error.

### M9 PASS (2026-05-24T18:27Z)
Source: `https://download.blender.org/peach/bigbuckbunny_movies/big_buck_bunny_480p_h264.mov` (108 MB file). With `max_download_mb=10` the server aborted PRE-stream via Content-Length pre-check: `Download aborted: Content-Length 249229883 exceeds cap of 10485760 bytes`. Clean typed error, no streaming overhead.

### M10 PASS (2026-05-24T18:27Z)
Source: `http://example.com/video.mp4` rejected at scheme check: `Only https:// URLs are accepted ... refuses http://, file://, ftp://, and other schemes to prevent SSRF + filesystem leakage.` 0.24s.

### M11 PASS (2026-05-24T18:31Z)
Source: `https://www.google.com/robots.txt` (text file masquerading as video). Initial example.com retry hit a transient DNS error from urllib's resolver; switched to google.com. ffmpeg correctly detected the file as not a valid container: `Frame extraction failed: ffmpeg failed ... moov atom not found ... Invalid data found when processing input`. Typed error in result body (not an uncaught exception).

### FASE 2 (M5-M8) — pending Owner action
Owner: disconnect + reconnect the connector in claude.ai, attach a video, prompt the LLM to use `analyze_video_url`. Server log tail running on this side; agent will read `CallToolRequest` + URL + result and validate.

