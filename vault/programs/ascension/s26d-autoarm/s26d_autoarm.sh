#!/usr/bin/env bash
# One-shot watcher (Owner "y" 2026-11-11T16:35:42.826Z, uuid 9b10d5ed, laptop pane d957c937):
# when S27 (m-10566700b1fe) reaches CHECKPOINT_COMPLETE, start S26D on the same mission record.
# Stops itself after acting, when S27 ends any other way, or 48 h after install. Cron: */5, flock.
# DRY=1 prints the actions instead of running them; HOLD_OVERRIDE=checkpoint simulates the trigger.
set -u
export CPP_CLAUDE_EXE=/home/kobii/.local/bin/claude
export PATH=/home/kobii/.local/bin:$PATH
M=m-10566700b1fe
PP=/home/kobii/.claude/skills/claude-power-pack
G=/home/kobii/missions/gen3-pp
V=$G/vault/programs/gsdx-factory-2
SRC=/home/kobii/agora/s26d-autoarm
ST=/home/kobii/.claude/state
DONE=$ST/s26d-autoarm.done
LOG=$ST/s26d-autoarm.log
OT='d957c937-f56d-4447-9386-5d8002fe0b90:2026-11-11T16:35:42.826Z'
DEADLINE=$(cat $SRC/deadline_epoch)
DRY=${DRY:-0}
log() { echo "$(date -u +%FT%TZ) $*" >> $LOG; [ "$DRY" = 1 ] && echo "LOG: $*"; }
run() { if [ "$DRY" = 1 ]; then echo "DRY: $*"; else "$@"; fi; }
uncron() { [ "$DRY" = 1 ] && { echo "DRY: uncron"; return; }; crontab -l 2>/dev/null | grep -v 's26d_autoarm.sh' | crontab -; }
finish() { [ "$DRY" = 1 ] && { echo "DRY: finish $1"; return; }; echo "$1" > $DONE; uncron; }

[ -f $DONE ] && { uncron; exit 0; }
if [ "$(date +%s)" -gt "$DEADLINE" ]; then log "EXPIRED: S27 never reached a checkpoint within 48 h; S26D NOT armed"; finish EXPIRED; exit 0; fi

read -r STATE HOLD < <(python3 -c "
import json;r=json.load(open('$ST/gsd-mission-$M.json'))
print(r['state'], (r.get('owner_hold') or {}).get('kind') or 'none')")
HOLD=${HOLD_OVERRIDE:-$HOLD}
case "$STATE" in
  COMPLETED|HALTED|ORPHANED) log "S27 ended $STATE without a checkpoint hold; S26D NOT armed (a coordinator must decide)"; finish "STOPPED_$STATE"; exit 0;;
esac
[ "$HOLD" = checkpoint ] || exit 0

log "TRIGGER: S27 state=$STATE hold=$HOLD; starting S26D"
cd $G || { log "FAIL: no gen3"; exit 1; }
if [ -n "$(git status --porcelain .planning/PROJECT.md .planning/ROADMAP.md .planning/STATE.md)" ]; then
  log "FAIL: gen3 .planning has uncommitted changes; S26D NOT armed (retry next pass)"; exit 1; fi
SPEND=$(cd $PP && timeout 200 python3 tools/gsd_mission.py topology --mission $M 2>/dev/null | python3 -c "import json,sys;print(json.load(sys.stdin)['spend'])")
[ -n "$SPEND" ] || { log "FAIL: spend unmeasured; retry next pass"; exit 1; }
CEIL=$((SPEND + 11500000))
TS=$(date -u +%Y%m%dT%H%M); A=.planning/milestones/s27-checkpoint-complete-$TS
run mkdir -p $A
run git mv .planning/PROJECT.md .planning/ROADMAP.md .planning/STATE.md $A/ || { log "FAIL: archive"; exit 1; }
[ "$DRY" = 1 ] || printf 'S27 reached CHECKPOINT_COMPLETE; archived %s by s26d_autoarm.sh (Owner y uuid 9b10d5ed). NOT judged by a coordinator yet.\n' "$(date -u +%FT%TZ)" > $A/CLOSE-NOTE.md
run cp $SRC/S26D-PHASES.md $V/
run git add $A $V/S26D-PHASES.md
run git commit -q -m "S26D: archive S27 milestone (checkpoint), add S26D-PHASES.md (auto-arm, Owner y 2026-11-11T16:35Z)"
(cd $PP && run timeout 300 python3 tools/gsd_milestone_scaffold.py ensure --cwd $G --wu-packet $V/S26D-PHASES.md) >> $LOG 2>&1
run git add .planning/PROJECT.md .planning/ROADMAP.md .planning/STATE.md
run git commit -q -m "S26D: scaffold 5-phase milestone from S26D-PHASES.md (mission $M)"
cd $PP
if ! run timeout 300 python3 tools/gsd_mission.py retarget --mission $M --command-file $SRC/s26d_command.txt --reason "S26D auto-arm (Owner y 9b10d5ed)" --expect-cwd $G >> $LOG 2>&1; then
  log "retarget refused; hold --stop then retarget"
  run timeout 300 python3 tools/gsd_mission.py hold --mission $M --stop --reason "S26D auto-arm: stop S27 worker before retarget" >> $LOG 2>&1
  run timeout 300 python3 tools/gsd_mission.py retarget --mission $M --command-file $SRC/s26d_command.txt --reason "S26D auto-arm (Owner y 9b10d5ed)" --expect-cwd $G >> $LOG 2>&1 || { log "FAIL: retarget; S26D NOT armed"; finish FAIL_RETARGET; exit 1; }
  RELEASE=1
fi
run timeout 300 python3 tools/gsd_mission.py authority --mission $M --tokens $CEIL --extend-hours 16 --owner-turn "$OT" --reason "S26D +11.5M/+16h (Owner y 2026-11-11T16:35Z)" >> $LOG 2>&1 || { log "FAIL: authority; S26D NOT armed"; finish FAIL_AUTHORITY; exit 1; }
if [ "${RELEASE:-0}" = 1 ]; then run timeout 300 python3 tools/gsd_mission.py release --mission $M >> $LOG 2>&1
else run timeout 400 python3 tools/gsd_mission.py checkpoint --mission $M --clear --reason "S26D plan (gen3 S26D-PHASES.md)" >> $LOG 2>&1; fi
log "DONE: S26D armed on $M, authority $CEIL (spend $SPEND + 11.5M), +16 h"
finish ARMED
