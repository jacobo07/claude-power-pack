#!/usr/bin/env bash
# IC owner-bundle rows 4-10 on GEX44 against a COPY of the laptop corpus. One STEP line per step.
# Run 6: KME-L steps re-scoped to the frozen denominator's projects (Owner option 1, 2026-10-05);
# the CPP-D-W7 second workload keeps its authorized unfiltered form.
REPO=/home/kobii/missions/zero-rescan-run
ROOT=/home/kobii/kme-corpus/projects
OUT=/home/kobii/missions/zero-rescan-out2
PF='KobiiCraft-Core-Files|kme-wt-arena2'
CAP=14400
mkdir -p "$OUT"
SUM="$OUT/summary.txt"
cd "$REPO" || exit 2
run_step() {
  local id="$1"; shift
  local start; start=$(date +%s)
  python3 "$@" >"$OUT/$id.log" 2>"$OUT/$id.err" &
  local pid=$! rchar=0 hwm=0 killed=no
  while kill -0 "$pid" 2>/dev/null; do
    sleep 2
    if [ -r "/proc/$pid/io" ]; then
      local r; r=$(awk '/^rchar:/{print $2}' "/proc/$pid/io" 2>/dev/null); [ -n "$r" ] && rchar=$r
    fi
    if [ -r "/proc/$pid/status" ]; then
      local h; h=$(awk '/^VmHWM:/{print $2}' "/proc/$pid/status" 2>/dev/null); [ -n "$h" ] && hwm=$h
    fi
    if [ $(( $(date +%s) - start )) -gt "$CAP" ]; then kill -9 "$pid"; killed=cap; break; fi
  done
  wait "$pid"; local rc=$?
  local line
  line=$(printf 'STEP %s exit=%s killed=%s wall_s=%s peak_rss_MB=%s read_GB=%s' "$id" "$rc" "$killed" \
    "$(( $(date +%s) - start ))" "$(( hwm / 1024 ))" "$(awk -v b="$rchar" 'BEGIN{printf "%.2f", b/1073741824}')")
  echo "$line" | tee -a "$SUM"
  STEP_RC=$rc; STEP_KILLED=$killed
}
echo "START $(date -Is) head=$(git rev-parse --short HEAD) root=$ROOT project_filter=$PF" | tee -a "$SUM"
run_step r4-population wiki/tools/kme_pillars.py population --denominator KME-L --until auto --expand --root "$ROOT" --project-filter "$PF"
if [ "$STEP_RC" != 0 ] || [ "$STEP_KILLED" != no ]; then echo "STOP population gate failed" | tee -a "$SUM"; echo DONE | tee -a "$SUM"; exit 1; fi
run_step r4-d-kmel  wiki/tools/kme_pillars.py d --denominator KME-L --until auto --expand --root "$ROOT" --project-filter "$PF"
run_step r4-d-w7    wiki/tools/kme_pillars.py d --denominator CPP-D-W7 --expand --root "$ROOT"
run_step r5-e       wiki/tools/kme_pillars.py e --denominator KME-L --until auto --expand --root "$ROOT" --project-filter "$PF"
run_step r6-f       wiki/tools/kme_pillars.py f --denominator KME-L --until auto --expand --root "$ROOT" --project-filter "$PF"
run_step r7-g       wiki/tools/kme_pillars.py g --denominator KME-L --until auto --expand --root "$ROOT" --project-filter "$PF"
run_step r8-h       wiki/tools/kme_pillars.py h --denominator KME-L --until auto --expand --root "$ROOT" --project-filter "$PF"
run_step r9-i       wiki/tools/kme_pillars.py i --denominator KME-L --until auto --expand --root "$ROOT" --project-filter "$PF"
run_step r10-l-rank wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root "$ROOT" --project-filter "$PF"
echo "DONE $(date -Is)" | tee -a "$SUM"
