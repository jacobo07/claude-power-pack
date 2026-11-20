#!/usr/bin/env python3
"""GEX44 /tmp leaked-temp-dir cleanup (Owner "rec" 2026-11-20, pane 5a77ca0e). usage: tmpclean.py dry|apply
Authorized state: entries directly under /tmp, owned by kobii, name in a leaked temp-dir family, idle > 2 days.
Per item, immediately before its deletion: re-stat (owner, mtime) and refuse if any live process has its cwd or an open
fd inside it (process set refreshed every 2,000 items). Manifest = names actually deleted. Nothing else is touched."""
import os, re, shutil, stat, sys, time
FAM = re.compile(r"^(orca-prepare-gate-|au-cli-|au-mut-[a-z-]+-|a-u-test-|chkpat-|lca-c-led-)[A-Za-z0-9_]{6,}$"
                 r"|^tmp[a-z0-9_]{8}$|^tmp\.[A-Za-z0-9]{10}$|^permuter[a-z0-9_]{8}(\.o)?\.c$|^permuter[a-z0-9_]{8}\.o$")
UID = os.getuid(); CUT = time.time() - 2 * 86400
MAN = "/home/kobii/agora/factory/research/tmp_cleanup_manifest.txt"


def live_paths():
    s = set()
    for p in os.listdir("/proc"):
        if not p.isdigit():
            continue
        for link in [f"/proc/{p}/cwd"] + [f"/proc/{p}/fd/{f}" for f in (os.listdir(f"/proc/{p}/fd") if os.access(f"/proc/{p}/fd", os.R_OK) else [])]:
            try:
                t = os.readlink(link)
            except OSError:
                continue
            if t.startswith("/tmp/"):
                s.add(t.split("/")[2])
    return s


def eligible(name):
    try:
        st = os.lstat("/tmp/" + name)
    except FileNotFoundError:
        return False, "gone"
    if st.st_uid != UID:
        return False, "owner"
    if st.st_mtime > CUT:
        return False, "recent"
    if stat.S_ISLNK(st.st_mode):
        return False, "symlink"
    return True, ""


def main():
    mode = sys.argv[1]
    names = [n for n in os.listdir("/tmp") if FAM.match(n)]
    print("family matches", len(names), flush=True)
    live, kept, done, fam = live_paths(), {}, 0, {}
    man = open(MAN, "a") if mode == "apply" else None
    for i, n in enumerate(names):
        if i % 2000 == 0 and i:
            live = live_paths()
            if mode == "apply":
                print(f"{i}/{len(names)} deleted {done}", flush=True)
        ok, why = eligible(n)
        if ok and n in live:
            ok, why = False, "in use"
        if not ok:
            kept[why] = kept.get(why, 0) + 1
            continue
        key = re.sub(r"[A-Za-z0-9_]{6,}$|[a-z0-9_]{8}(\.o)?\.c$|[a-z0-9_]{8}\.o$", "*", n)
        if mode == "apply":
            ok, why = eligible(n)  # re-check at the destruction itself
            if not ok:
                kept[why] = kept.get(why, 0) + 1
                continue
            p = "/tmp/" + n
            try:
                if os.path.isdir(p):
                    shutil.rmtree(p)
                else:
                    os.remove(p)
            except OSError as e:
                kept["error:" + type(e).__name__] = kept.get("error:" + type(e).__name__, 0) + 1
                continue
            man.write(n + "\n")
        done += 1
        fam[key] = fam.get(key, 0) + 1
    print(("WOULD DELETE" if mode == "dry" else "DELETED"), done, "| kept", kept)
    print("by family", sorted(fam.items(), key=lambda x: -x[1])[:12])
    print("/tmp entries now", len(os.listdir("/tmp")))


if __name__ == "__main__":
    main()
