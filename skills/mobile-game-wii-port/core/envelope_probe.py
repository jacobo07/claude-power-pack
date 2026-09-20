#!/usr/bin/env python3
"""Phase 3 -- identify the container, then the payload inside it.

Plaintext is rarely the thing you want. Expect layers: a magic, a compression
envelope, then a payload that is itself a compiled format with its own header.

It peels one layer at a time and reports each. Where it can decompress with the
standard library it does, and it says whether the stream ENDED where it claimed
to -- a decoder that stops early and reports success has measured the prefix it
understood, not the file.

The Lua reader exists because of a measured trap: a header field is a BUILD
CHOICE, not a constant. The source corpus is Lua 5.1 with lua_Number as float32
instead of the stock double, so every stock-header tool rejects all 622 files.
Read the header before choosing a downstream tool.

Stdlib only.
"""
from __future__ import annotations

import json
import lzma
import os
import struct
import sys
import zlib

ROVIO_LZMA_MAGIC = b"\x89LZMA\r\n\x1a\n"

CONTAINERS = [
    (b"7z\xbc\xaf\x27\x1c", "7z archive"),
    (b"PK\x03\x04", "ZIP archive"),
    (b"\x1f\x8b", "gzip"),
    (b"\x1bLua", "Lua bytecode (no compression envelope)"),
    (b"RIFF", "RIFF container"),
    (b"OggS", "Ogg container"),
    (b"\x89PNG\r\n\x1a\n", "PNG"),
    (b"PVR\x03", "PVR texture v3"),
    (b"DDS ", "DDS texture"),
]

LUA_NUMBER_NOTE = {
    8: "8 B -- the stock double build; standard tools accept this",
    4: "4 B -- a float32 build. Stock luac and every decompiler built for the "
       "default header will REJECT or misread these chunks, and the original "
       "computed in single precision, which the port must reproduce",
}


def decode_lzma_props(props: bytes) -> dict:
    d = props[0]
    lc, d2 = d % 9, d // 9
    lp, pb = d2 % 5, d2 // 5
    dict_size = struct.unpack("<I", props[1:5])[0]
    return {"props_byte": f"0x{props[0]:02x}", "lc": lc, "lp": lp, "pb": pb,
            "dictionary_bytes": dict_size}


def try_lzma_alone(blob: bytes):
    """Decode an LZMA-alone stream: 5 B props, 8 B declared size, then data.

    Always returns (info, payload). payload is b"" on any failure, so the
    caller never has to tell a dict from a tuple.
    """
    if len(blob) < 13:
        return {"ok": False, "why": "shorter than an LZMA-alone header"}, b""
    props = blob[:5]
    declared = struct.unpack("<Q", blob[5:13])[0]
    info = decode_lzma_props(props)
    info["declared_size"] = None if declared == 0xFFFFFFFFFFFFFFFF else declared
    dec = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
    try:
        out = dec.decompress(blob)
    except lzma.LZMAError as exc:
        info.update({"ok": False, "why": f"LZMA error: {exc}"})
        return info, b""
    info.update({
        "ok": True,
        "produced_size": len(out),
        "unused_trailing_bytes": len(dec.unused_data),
        "stream_ended": dec.eof,
        "declared_matches_produced": (info["declared_size"] is None
                                      or info["declared_size"] == len(out)),
    })
    return info, out


def read_lua_header(blob: bytes) -> dict:
    if len(blob) < 12 or not blob.startswith(b"\x1bLua"):
        return {"ok": False, "why": "no Lua signature"}
    ver, fmt, endian, i_sz, st_sz, ins_sz, num_sz, integral = struct.unpack(
        "<BBBBBBBB", blob[4:12])
    return {
        "ok": True,
        "version": f"{ver >> 4}.{ver & 0xF}",
        "version_byte": f"0x{ver:02x}",
        "format": "official (0)" if fmt == 0 else f"non-standard ({fmt})",
        "endianness": "little" if endian == 1 else "big",
        "sizeof_int": i_sz,
        "sizeof_size_t": st_sz,
        "sizeof_Instruction": ins_sz,
        "sizeof_lua_Number": num_sz,
        "lua_Number_note": LUA_NUMBER_NOTE.get(num_sz, f"{num_sz} B -- unusual"),
        "integral": bool(integral),
        "stock_header": (ver == 0x51 and fmt == 0 and endian == 1 and i_sz == 4
                         and ins_sz == 4 and num_sz == 8 and not integral),
    }


def identify(blob: bytes) -> dict:
    if blob.startswith(ROVIO_LZMA_MAGIC):
        return {"container": "custom 9-byte magic + LZMA-alone",
                "magic": ROVIO_LZMA_MAGIC.hex(), "payload_offset": len(ROVIO_LZMA_MAGIC)}
    for magic, label in CONTAINERS:
        if blob.startswith(magic):
            return {"container": label, "magic": magic.hex(), "payload_offset": 0}
    if len(blob) >= 2 and blob[0] == 0x78 and (blob[0] * 256 + blob[1]) % 31 == 0:
        return {"container": "zlib stream", "magic": blob[:2].hex(), "payload_offset": 0}
    if len(blob) >= 13 and blob[0] <= 224:
        return {"container": "possible raw LZMA-alone (no magic)",
                "magic": None, "payload_offset": 0}
    return {"container": "UNKNOWN", "magic": None, "payload_offset": 0}


def probe(blob: bytes) -> dict:
    layers = []
    outer = identify(blob)
    layers.append({"layer": 0, **outer, "bytes": len(blob)})
    payload = b""

    if "LZMA-alone" in outer["container"]:
        info, payload = try_lzma_alone(blob[outer["payload_offset"]:])
        layers.append({"layer": 1, "decoder": "lzma FORMAT_ALONE", **info})
    elif outer["container"] == "zlib stream":
        try:
            payload = zlib.decompress(blob)
            layers.append({"layer": 1, "decoder": "zlib", "ok": True,
                           "produced_size": len(payload)})
        except zlib.error as exc:
            layers.append({"layer": 1, "decoder": "zlib", "ok": False, "why": str(exc)})
    elif outer["container"] == "gzip":
        try:
            payload = zlib.decompress(blob, 16 + zlib.MAX_WBITS)
            layers.append({"layer": 1, "decoder": "gzip", "ok": True,
                           "produced_size": len(payload)})
        except zlib.error as exc:
            layers.append({"layer": 1, "decoder": "gzip", "ok": False, "why": str(exc)})
    elif outer["container"].startswith("Lua bytecode"):
        payload = blob

    if payload[:4] == b"\x1bLua":
        layers.append({"layer": len(layers), "payload": "Lua bytecode",
                       **read_lua_header(payload)})
    elif payload:
        inner = identify(payload)
        layers.append({"layer": len(layers), "payload": inner["container"],
                       "bytes": len(payload)})
    return {"layers": layers, "payload_bytes": len(payload)}


def main(argv) -> int:
    if len(argv) < 2:
        print(__doc__.strip())
        print("\nusage: envelope_probe.py <file> [--json]")
        return 0
    path = argv[1]
    if not os.path.isfile(path):
        print(f"UNREADABLE_INPUT: {path} is not a file", file=sys.stderr)
        return 2
    with open(path, "rb") as fh:
        blob = fh.read()
    result = probe(blob)

    if "--json" in argv:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print(f"=== Phase 3 envelope probe: {path} ({len(blob):,} B) ===\n")
    for layer in result["layers"]:
        idx = layer.get("layer")
        if "container" in layer:
            print(f"  layer {idx}: {layer['container']}")
        elif "decoder" in layer:
            ok = layer.get("ok")
            print(f"  layer {idx}: {layer['decoder']} -> "
                  f"{'decoded' if ok else 'FAILED'}")
            if ok:
                print(f"            props {layer.get('props_byte')} "
                      f"lc={layer.get('lc')} lp={layer.get('lp')} "
                      f"pb={layer.get('pb')} "
                      f"dict={layer.get('dictionary_bytes', 0):,} B")
                print(f"            produced {layer.get('produced_size', 0):,} B, "
                      f"declared {layer.get('declared_size')}, "
                      f"trailing unused {layer.get('unused_trailing_bytes')}, "
                      f"stream ended {layer.get('stream_ended')}")
                if not layer.get("declared_matches_produced"):
                    print("            DECLARED SIZE DOES NOT MATCH PRODUCED -- "
                          "the decode is partial")
            else:
                print(f"            {layer.get('why')}")
        elif layer.get("payload") == "Lua bytecode":
            print(f"  layer {idx}: Lua bytecode")
            print(f"            version {layer['version']} "
                  f"({layer['version_byte']}), {layer['format']}, "
                  f"{layer['endianness']}-endian")
            print(f"            int={layer['sizeof_int']} "
                  f"size_t={layer['sizeof_size_t']} "
                  f"Instruction={layer['sizeof_Instruction']} "
                  f"lua_Number={layer['sizeof_lua_Number']}")
            print(f"            lua_Number: {layer['lua_Number_note']}")
            if not layer["stock_header"]:
                print("            NON-STOCK HEADER -- pick downstream tools "
                      "on these fields, not on the Lua version alone")
        else:
            print(f"  layer {idx}: {layer.get('payload')} "
                  f"({layer.get('bytes', 0):,} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
