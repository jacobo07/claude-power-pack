Analyze YouTube video(s) for deep research using yt-research tool.

## Usage

Given a YouTube URL (or multiple URLs), run the full research pipeline:

### Single Video
```bash
yt-research analyze "$ARGUMENTS"
```

### After Analysis

1. Read the generated summary:
```bash
yt-research show <video-id>
```

2. Read the full transcript for detailed context:
```bash
yt-research transcript <video-id>
```

3. View extracted key frames for visual analysis (read the PNG files from the frames directory):
```bash
yt-research frames <video-id>
```
Then use the Read tool to view each frame PNG.

4. For follow-up questions, use NotebookLM:
```bash
yt-research ask <video-id> "your question here"
```

### Batch Mode
For playlists: `yt-research batch --playlist "$ARGUMENTS"`
For multiple URLs: `yt-research batch <url1> <url2> ...`

### Key Behaviors
- Always read summary.md and transcript.txt into context after analysis
- View at least 3-5 key frames for visual understanding
- Use `yt-research ask` for questions that need NotebookLM's deep analysis
- You now have full video context — answer questions as if you watched the video
