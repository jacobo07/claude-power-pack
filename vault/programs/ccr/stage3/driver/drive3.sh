#!/usr/bin/env bash
# CCR Stage 3 GEX44 phase 2 driver (v3): A0 A1 A6 A7 X2, one at a time.
# v3 vs v2: the breaker FAILS CLOSED (a failed or empty measurement trips it; v2's measurement crashed on a stream
# line whose `message` is a string and A4 ran to 6.35M on a 4.5M stop); per-unit stop 2,250,000; a phase cap of
# 7,500,000 over all five units; the plugin is loaded from a snapshot outside the clone so the clone's mod is editable.
# Kill: touch $D/STOP. Log: $D/drive.log.
set -u
R=/home/kobii/missions/ccr-s3; D=/home/kobii/missions/ccr-s3-data; S3=$R/vault/programs/ccr/stage3
CLAUDE=/home/kobii/.local/bin/claude
UNIT_STOP=4500000; PHASE_CAP=15665526; UNITS="A0 A1 A6 A7 X2"
echo '{"class":"bounded-code-worker","id":"ccr-s3-linux-p2"}' > $D/unit.json
rm -rf $D/ccr-mod-snapshot && cp -r $R/mods/cpp-cognitive-runtime $D/ccr-mod-snapshot

spent() {  # processed tokens of the units named in $@ (dedup by message id); prints ERR on any failure
  python3 - "$D" "$@" <<'PY' 2>/dev/null || echo ERR
import json, glob, sys
d, units = sys.argv[1], sys.argv[2:]
seen, tot = set(), 0
for u in units:
    for f in sorted(glob.glob(f"{d}/run-{u}*.jsonl")):
        for line in open(f, errors="replace"):
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if not isinstance(o, dict) or o.get("type") != "assistant":
                continue
            m = o.get("message")
            if not isinstance(m, dict) or not isinstance(m.get("usage"), dict) or m.get("id") in seen:
                continue
            seen.add(m.get("id"))
            us = m["usage"]
            tot += sum(int(us.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens", "output_tokens"))
print(tot)
PY
}
over() { [ "$1" = ERR ] || [ -z "$1" ] || [ "$1" -ge "$2" ]; }   # fail closed
done_receipt() { grep -qE '^Status: (DONE|DONE_WITH_LIMITS)' $S3/WU-$1-receipt.md 2>/dev/null; }

for U in $UNITS; do
  [ -f $D/STOP ] && { echo "$(date -Is) STOP file" >> $D/drive.log; exit 0; }
  if done_receipt $U; then echo "$(date -Is) $U already done" >> $D/drive.log; continue; fi
  avail=$(awk '/MemAvailable/ {print int($2/1048576)}' /proc/meminfo)
  [ "$avail" -lt 4 ] && { echo "$(date -Is) ram_hold $U avail_gb=$avail" >> $D/drive.log; exit 0; }
  phase=$(spent $UNITS); used=$(spent $U)
  over "$phase" $PHASE_CAP && { echo "$(date -Is) halt: phase spend $phase >= $PHASE_CAP (or unmeasurable)" >> $D/drive.log; exit 1; }
  over "$used" $UNIT_STOP && { echo "$(date -Is) halt: $U at $used >= $UNIT_STOP (or unmeasurable)" >> $D/drive.log; exit 1; }
  SID=$(cat /proc/sys/kernel/random/uuid); echo "$SID" > $D/sid-$U
  PROMPT="$(cat $D/packets/WU-$U-linux.md)"
  echo "$(date -Is) start $U sid=$SID phase=$phase" >> $D/drive.log
  cd $R && CCR_WORK_UNIT=$D/unit.json timeout 4h $CLAUDE -p "$PROMPT" --session-id "$SID" \
     --plugin-dir $D/ccr-mod-snapshot --max-turns 90 --permission-mode acceptEdits \
     --allowedTools "Bash Read Edit Write Grep Glob ToolSearch" --output-format stream-json --verbose \
     > $D/run-$U.jsonl 2> $D/run-$U.err < /dev/null &
  CPID=$!
  while kill -0 $CPID 2>/dev/null; do
    sleep 30
    s=$(spent $U); p=$(spent $UNITS)
    if over "$s" $UNIT_STOP || over "$p" $PHASE_CAP; then
      echo "$(date -Is) breaker $U unit=$s phase=$p: killing $CPID" >> $D/drive.log
      pkill -TERM -P $CPID 2>/dev/null; kill -TERM $CPID 2>/dev/null; sleep 5; pkill -KILL -P $CPID 2>/dev/null; kill -KILL $CPID 2>/dev/null
      break
    fi
  done
  wait $CPID 2>/dev/null; rc=$?
  echo "$(date -Is) end $U sid=$SID rc=$rc processed=$(spent $U) status=$(sed -n 2p $S3/WU-$U-receipt.md 2>/dev/null)" >> $D/drive.log
  done_receipt $U || { echo "$(date -Is) halt: $U has no DONE receipt" >> $D/drive.log; exit 1; }
done
echo "$(date -Is) phase 2 all done" >> $D/drive.log
