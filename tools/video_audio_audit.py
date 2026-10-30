"""Acoustic audit of a finished video: what a machine can say about its audio, and nothing it cannot.

    python -I scripts/audio-audit.py <video.mp4> [--lines vo-lines-qlb.json --key qlb-b1] [--out report.json]

Measures: stream durations (audio vs picture), integrated loudness / loudness range / true peak (ffmpeg ebur128), silent gaps (silencedetect),
the ASR transcript with word times (faster-whisper small, English), speaking rate, the text difference against the scripted voice lines, the
level of the voice windows against the level of the gaps (the bed: music + SFX), and whether the tail is cut (audio shorter than picture).

It does NOT judge diction, naturalness, pacing as a listener would, or taste. The verdict string is therefore at most
TRANSCRIBED + ACOUSTIC-MEASURED; AUDIO VERIFIED needs a person to listen.
"""
import argparse
import difflib
import json
import re
import subprocess
import sys


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout, p.stderr


def probe(path):
    out = {}
    for sel in ("v:0", "a:0"):
        rc, so, _ = run(["ffprobe", "-v", "error", "-select_streams", sel, "-show_entries", "stream=codec_name,duration", "-of", "json", path])
        s = (json.loads(so).get("streams") or [{}])[0] if rc == 0 else {}
        out[sel] = {"codec": s.get("codec_name"), "duration": float(s["duration"]) if s.get("duration") else None}
    return out


def loudness(path):
    _, _, err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"])
    tail = err[err.rfind("Summary:"):] if "Summary:" in err else err
    def pick(label):
        m = re.search(label + r":\s+(-?[\d.]+)", tail)
        return float(m.group(1)) if m else None
    return {"lufs": pick("I"), "lra": pick("LRA"), "true_peak_dbfs": pick("Peak")}


def silences(path, noise_db=-38, min_d=0.5):
    _, _, err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", f"silencedetect=n={noise_db}dB:d={min_d}", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    ends = [(float(a), float(b)) for a, b in re.findall(r"silence_end: (-?[\d.]+) \| silence_duration: ([\d.]+)", err)]
    return {"count": len(starts), "starts": starts, "ends_dur": ends}


def mean_volume(path, t0, t1):
    if t1 - t0 < 0.15:
        return None
    _, _, err = run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{t0:.2f}", "-t", f"{t1 - t0:.2f}", "-i", path, "-af", "volumedetect", "-f", "null", "-"])
    m = re.search(r"mean_volume: (-?[\d.]+) dB", err)
    return float(m.group(1)) if m else None


def transcribe(path):
    from faster_whisper import WhisperModel
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(path, language="en", word_timestamps=True, vad_filter=False)
    out = []
    for s in segs:
        out.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(),
                    "words": [(w.word.strip(), round(w.start, 2), round(w.end, 2)) for w in s.words]})
    return out


def norm_words(text):
    return re.findall(r"[a-z0-9€']+", text.lower().replace("’", "'"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--lines")
    ap.add_argument("--key")
    ap.add_argument("--out")
    a = ap.parse_args()

    pr = probe(a.video)
    rep = {"file": a.video, "streams": pr, "loudness": loudness(a.video), "silence": silences(a.video)}
    v, au = pr["v:0"]["duration"], pr["a:0"]["duration"]
    rep["tail_cut"] = bool(v and au and au + 0.05 < v)
    rep["audio_minus_picture_s"] = round(au - v, 3) if v and au else None

    segs = transcribe(a.video)
    rep["transcript"] = [{"start": s["start"], "end": s["end"], "text": s["text"]} for s in segs]
    words = [w for s in segs for w in s["words"]]
    if words:
        span = words[-1][2] - words[0][1]
        rep["speech"] = {"first_word_s": words[0][1], "last_word_s": words[-1][2], "words": len(words), "wpm_over_span": round(len(words) / span * 60, 1) if span > 0 else None}
        # longest pause between consecutive words
        gaps = [(round(words[i + 1][1] - words[i][2], 2), words[i][2]) for i in range(len(words) - 1)]
        rep["speech"]["longest_inter_word_gap_s"] = max(gaps)[0] if gaps else None
        # voice windows vs the bed between them
        vo = [mean_volume(a.video, s["start"], s["end"]) for s in segs]
        bed = []
        edges = [0.0] + [x for s in segs for x in (s["start"], s["end"])] + [au or 0]
        for i in range(0, len(edges) - 1, 2):
            bed.append(mean_volume(a.video, edges[i], edges[i + 1]))
        vo_v = [x for x in vo if x is not None]
        bed_v = [x for x in bed if x is not None]
        rep["balance"] = {"voice_mean_db": round(sum(vo_v) / len(vo_v), 1) if vo_v else None, "gap_bed_mean_db": round(sum(bed_v) / len(bed_v), 1) if bed_v else None}
        # NOT a voice-to-bed balance: the bed (music + SFX) is sidechain-ducked under the voice (scripts/vo-mix.mjs), so the level inside a voice
        # window is the voice plus an already-ducked bed and the gap level is the bed at full level. The two cannot be separated from the mix.
        rep["balance"]["status"] = "INCONCLUSIVE: window levels only; voice alone is not observable in a finished mix"

    if a.lines and a.key:
        lines = json.load(open(a.lines, encoding="utf-8-sig"))[a.key]["lines"]
        script = norm_words(" ".join(l["text"] for l in lines))
        heard = norm_words(" ".join(s["text"] for s in segs))
        sm = difflib.SequenceMatcher(a=script, b=heard)
        diffs = [(op, script[i1:i2], heard[j1:j2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]
        rep["script_match"] = {"ratio": round(sm.ratio(), 3), "diffs": diffs}

    rep["verdict"] = "TRANSCRIBED + ACOUSTIC-MEASURED (not heard; AUDIO VERIFIED requires a listener)"
    text = json.dumps(rep, ensure_ascii=False, indent=2)
    if a.out:
        open(a.out, "w", encoding="utf-8", newline="\n").write(text + "\n")
    print(text)


if __name__ == "__main__":
    sys.exit(main())
