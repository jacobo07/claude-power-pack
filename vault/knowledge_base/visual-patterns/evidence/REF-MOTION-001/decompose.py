"""Decode the reference video, measure per-frame change, and emit contact sheets."""
import os, subprocess, sys
import numpy as np
import imageio_ffmpeg
from PIL import Image

SRC = r"C:\Users\User\Downloads\coltonholland.ai_fc7fbac9b18f4d438a7932f276d3ec9d_1.mp4"
OUT = os.path.dirname(os.path.abspath(__file__))
W, H = 180, 320  # quarter-res analysis frames

ff = imageio_ffmpeg.get_ffmpeg_exe()
raw = subprocess.run([ff, "-v", "error", "-i", SRC, "-vf", f"scale={W}:{H}",
                      "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
n = len(raw) // (W * H * 3)
frames = np.frombuffer(raw, np.uint8)[: n * W * H * 3].reshape(n, H, W, 3).astype(np.int16)
fps = 30.08
print(f"frames={n} fps={fps}")

# Global change and regional change (top band / middle / bottom band) so a stable
# device frame vs changing inner content shows up as a spatial split, not a guess.
bands = {"top": slice(0, H // 4), "mid": slice(H // 4, 3 * H // 4), "bot": slice(3 * H // 4, H)}
rows = []
for i in range(1, n):
    d = np.abs(frames[i] - frames[i - 1]).mean(axis=2)
    rows.append((i, i / fps, d.mean(), *(d[b].mean() for b in bands.values())))
with open(os.path.join(OUT, "diff.tsv"), "w") as f:
    f.write("frame\tt\tall\ttop\tmid\tbot\n")
    for r in rows:
        f.write("%d\t%.3f\t%.2f\t%.2f\t%.2f\t%.2f\n" % r)

# Per-pixel temporal variance map: where in the frame does anything ever move?
var = frames.astype(np.float32).mean(axis=3).std(axis=0)
Image.fromarray(np.clip(var * 4, 0, 255).astype(np.uint8)).resize((360, 640)).save(os.path.join(OUT, "variance.png"))

def sheet(idx, name, cols=6, scale=1.0):
    ims = [Image.fromarray(frames[i].astype(np.uint8)) for i in idx]
    w, h = int(W * scale), int(H * scale)
    rows_ = (len(ims) + cols - 1) // cols
    s = Image.new("RGB", (cols * w, rows_ * (h + 14)), "white")
    from PIL import ImageDraw
    dr = ImageDraw.Draw(s)
    for k, (i, im) in enumerate(zip(idx, ims)):
        x, y = (k % cols) * w, (k // cols) * (h + 14)
        s.paste(im.resize((w, h)), (x, y + 14))
        dr.text((x + 2, y), f"f{i} {i/fps:.2f}s", fill="black")
    s.save(os.path.join(OUT, name))

sheet(list(range(0, n, 6)), "sheet_every6.png", cols=8)
for part, (a, b) in enumerate([(0, 60), (60, 120), (120, n)]):
    sheet(list(range(a, b, 2)), f"sheet_dense_{part}.png", cols=10)
print("ok")
