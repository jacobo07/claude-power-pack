"""UMVM M2: image carry of one epoch from its transcript, with per-image token cost from the real pixel size.

Cost model = the CCR mod's imageTokens (w*h/750 after the 1568 px / 1.15 MP downscale), calibrated
2026-10-12 against provider usage: a 1033x917 PNG estimated 1,264 tok, measured 1,318 +/- 30 (next-call delta
minus the known text rows). An image appended before call k is re-sent by calls k..N, so its carry is
tok * (N - k + 1). Usage: python image_carry.py <transcript.jsonl>
"""
import base64, hashlib, json, math, sys


def dims(data: str):
    b = base64.b64decode(data[:350000] + "=" * (-len(data[:350000]) % 4))
    if b[:2] == b"\x89P":
        return int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")
    if b[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(b):
            if b[i] != 0xFF:
                i += 1
                continue
            m = b[i + 1]
            if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                return (b[i + 7] << 8) | b[i + 8], (b[i + 5] << 8) | b[i + 6]
            i += 2 + ((b[i + 2] << 8) | b[i + 3])
    return None


PIXELS_PER_TOKEN = 750  # no megapixel cap on Opus 5.5: 2000x1278 measured ~3,420 vs 3,408 (see the mod's imageTokens)


def tokens(w: int, h: int) -> int:
    return math.ceil(w * h / PIXELS_PER_TOKEN)


def images_in(x, out):
    if isinstance(x, list):
        for y in x:
            images_in(y, out)
    elif isinstance(x, dict):
        if x.get("type") == "image" and isinstance(x.get("source", {}).get("data"), str):
            out.append(x["source"]["data"])
        elif "content" in x:
            images_in(x["content"], out)


def main(path: str) -> dict:
    calls, seen, imgs = [], set(), []
    for line in open(path, encoding="utf-8"):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        if o.get("isSidechain"):
            continue
        m = o.get("message") or {}
        if o.get("type") == "assistant" and m.get("id") and m["id"] not in seen and m.get("usage"):
            seen.add(m["id"])
            u = m["usage"]
            calls.append(u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0))
        elif o.get("type") == "user":
            found = []
            images_in(m.get("content"), found)
            for d in found:
                wh = dims(d)
                imgs.append({"after_call": len(calls), "hash": hashlib.sha256(d.encode()).hexdigest()[:12],
                             "w": wh[0] if wh else None, "h": wh[1] if wh else None, "tok": tokens(*wh) if wh else None})
    n = len(calls)
    for i in imgs:
        i["rides"] = n - i["after_call"]
        i["carry"] = (i["tok"] or 0) * i["rides"]
    total = sum(calls)
    carry = sum(i["carry"] for i in imgs)
    hashes = [i["hash"] for i in imgs]
    return {"calls": n, "processed": total, "images": len(imgs), "unique_images": len(set(hashes)),
            "image_tok_once": sum(i["tok"] or 0 for i in imgs), "image_carry": carry,
            "image_share": round(carry / total, 4) if total else None,
            "first_call": calls[0] if calls else None, "last_call": calls[-1] if calls else None,
            "floor_share": round(calls[0] * n / total, 4) if total else None, "unknown_dims": sum(1 for i in imgs if i["tok"] is None),
            "per_image": imgs}


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1]), indent=1))
