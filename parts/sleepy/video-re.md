# Video-Enhanced Reverse Engineering

> Sleepy part. ~350 tokens. Load when: reverse engineer, video analysis, YouTube research,
> competitor analysis, architectural depth, SOTA research, Omni-Plan.
> Auto-activated at DEEP+ tier during Omni-Plan route.

## Rules

### 1. Video Evidence > Text Description
When performing reverse engineering (Rule N: Extreme Architectural Depth), video evidence
outranks text descriptions. A competitor demo video showing live functionality provides
3-5x more architectural insight than a blog post describing the same feature.

### 2. Omni-Plan Video Integration
When Omni-Plan activates for new architecture/system design:
1. Search YouTube for competitor demos, conference talks, tutorials on the topic
2. Extract frames + transcript via `video_analyzer.py`
3. Score frames for architectural value via `vision_scorer.py`
4. Feed high-scoring signals (architecture diagrams, live demos, metrics) into RE decomposition
5. Use extracted metrics as primary benchmarks (not estimates)

### 3. Transcript-First Analysis
For YouTube videos, extract transcript BEFORE watching frames:
- Primary: YouTube captions (free, instant)
- Fallback: faster-whisper local transcription
- Use timestamped transcript to identify key moments, then analyze those frames

### 4. Cross-Project Visual Patterns
When cross_signal_bus detects keyword overlap across projects, check if source signals
have video frames. Visual pattern matching (same UI component, same architecture diagram
type) across projects reveals reusable patterns text matching would miss.

## Commands

| Action | Command |
|--------|---------|
| Analyze YouTube video | `python modules/autoresearch/video_analyzer.py --url <url>` |
| Score video frames | `python modules/autoresearch/vision_scorer.py --frames-dir <dir>` |
| Transcribe audio | `python modules/autoresearch/whisper_bridge.py --audio <file>` |
| Full RE pipeline | `yt-research analyze <url>` (if installed) |
| Enable auto-analysis | Set `video_analysis_enabled: true` in autoresearch config.json |

## Architecture Flow

```
YouTube URL → video_analyzer.py
                ├── yt-research (if installed) → scene detection + NotebookLM
                ├── yt-dlp + ffmpeg (fallback) → interval frames
                ├── youtube-transcript-api → captions
                ├── whisper_bridge.py (fallback) → audio transcription
                └── vision_scorer.py → frame classification + composite score
                        → signal_scorer.py (vision_quality weight: 0.15)
                                → cross_signal_bus.py (visual relay)
```
