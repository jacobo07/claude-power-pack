"""Full-res crops of the device mockup region, so inner-app state changes are readable."""
import os, subprocess
import numpy as np
import imageio_ffmpeg
from PIL import Image, ImageDraw

SRC = r"C:\Users\User\Downloads\coltonholland.ai_fc7fbac9b18f4d438a7932f276d3ec9d_1.mp4"
OUT = os.path.dirname(os.path.abspath(__file__))
W, H = 720, 1280
X0, X1, Y0, Y1 = 150, 570, 330, 930  # generous: camera drifts

raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", SRC, "-f", "rawvideo",
                      "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
n = len(raw) // (W * H * 3)
fr = np.frombuffer(raw, np.uint8)[: n * W * H * 3].reshape(n, H, W, 3)
fps = 30.08

def sheet(idx, name, cols=8, s=0.55):
    cw, ch = int((X1 - X0) * s), int((Y1 - Y0) * s)
    rows = (len(idx) + cols - 1) // cols
    im = Image.new("RGB", (cols * cw, rows * (ch + 16)), "white")
    d = ImageDraw.Draw(im)
    for k, i in enumerate(idx):
        x, y = (k % cols) * cw, (k // cols) * (ch + 16)
        im.paste(Image.fromarray(fr[i, Y0:Y1, X0:X1]).resize((cw, ch)), (x, y + 16))
        d.text((x + 3, y + 2), f"f{i} {i/fps:.2f}s", fill="black")
    im.save(os.path.join(OUT, name))

sheet(list(range(0, 88, 4)), "crop_a.png")
sheet(list(range(88, n, 4)), "crop_b.png")
# Densest window (3.2-4.4s had the largest change): every frame.
sheet(list(range(96, 136, 2)), "crop_dense_transition.png", cols=10, s=0.45)
print(n)
