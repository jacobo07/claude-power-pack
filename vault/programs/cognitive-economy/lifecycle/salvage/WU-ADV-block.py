# --------------------------------------------------------------------------- advance (WU-ADV)
# The sweep itself advances APPROVED work: an approval record (`<state>/approvals/<id>.json`) names a plan;
# the first unit of the plan's `units:` list without a complete receipt is armed through the atomic arm
# when its predecessor's receipt exists and the goal has the authority. CPP_SWEEP_ADVANCE=off disables.
ADVANCE_RESERVE = 300_000


def advance_on() -> bool:
    return os.environ.get("CPP_SWEEP_ADVANCE", "").lower() != "off"


def _adv_dir() -> Path:
    return lr.state_dir() / "advance"


def _adv_log(goal: str, unit: str | None, status: str, why: str = "", **extra) -> bool:
    """Append one decision to advance-log.jsonl only when it differs from the last one for the goal."""
    d = _adv_dir()
    d.mkdir(parents=True, exist_ok=True)
    last_p = d / f"last-{goal}.json"
    try:
        last = json.loads(last_p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        last = {}
    sig = f"{unit}|{status}|{why}"
    if last.get("sig") == sig:
        return False
    with open(d / "advance-log.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"at": time.time(), "goal": goal, "unit": unit, "status": status,
                             "why": why, **extra}) + "\n")
    last_p.write_text(json.dumps({"sig": sig}), encoding="utf-8")
    return True


def parse_plan(path: Path) -> dict:
    """Frontmatter of an approved plan: status, units (in order), packet_dir, packet_shas {unit: hex-prefix}."""
    text = Path(path).read_text(encoding="utf-8-sig")
    m = re.match(r"\A---\s*\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        raise MissionError(f"plan {path} has no frontmatter")
    fm = {}
    for ln in m.group(1).splitlines():
        k, sep, v = ln.partition(":")
        if sep:
            fm[k.strip()] = v.strip()
    units = [u.strip() for u in re.sub(r"[\[\]]", "", fm.get("units", "")).split(",") if u.strip()]
    shas = dict(re.findall(r"([\w.-]+)\s*=\s*([0-9a-fA-F]{6,64})", fm.get("packet_shas", "")))
    return {"status": fm.get("status", ""), "units": units, "packet_dir": fm.get("packet_dir", ""),
            "packet_shas": shas, "goal": fm.get("goal", "")}


def receipt_complete(path: Path) -> bool:
    """A gate/PASS receipt. A stub, an in-progress or a partial receipt is not one."""
    try:
        body = Path(path).read_text(encoding="utf-8-sig")
    except OSError:
        return False
    if re.search(r"STUB|IN PROGRESS|PARTIAL", body):
        return False
    return bool(re.search(r"PASS|Status:\s*DONE", body))


def goal_headroom(goal: str | None) -> int | None:
    """remaining - open of an EXISTING goal ledger with a cap; None otherwise (never creates a ledger)."""
    if not goal:
        return None
    try:
        import mission_spend as ms
        if not (ms.goal_root() / goal).exists():
            return None
        st = ms._goal_ledger(goal).status()
        if st.get("remaining") is None:
            return None
        return int(st["remaining"]) - int(st.get("open") or 0)
    except Exception:  # noqa: BLE001
        return None


def _live_unit_mission(unit: str, packet: Path) -> dict | None:
    want = os.path.normcase(str(packet.resolve()))
    for r in all_missions():
        if r.get("state") in TERMINAL:
            continue
        wp = (r.get("wu_packet") or {}).get("path")
        if (r.get("goal") or {}).get("unit") == f"lc-{unit}" or (
                wp and os.path.normcase(str(Path(wp).resolve())) == want):
            return r
    return None


def _file_sha(p: Path) -> str:
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def apply_approval(rec: dict, *, goal_ledger=None) -> dict:
    """Consume-once: cap_delta goes through declare_cap with source naming approval_id, never twice."""
    aid = rec["approval_id"]
    if rec.get("consumed"):
        return {"applied": False, "why": f"record marked consumed ({rec['consumed']})"}
    delta = int(rec.get("cap_delta") or 0)
    if delta <= 0:
        return {"applied": False, "why": "no cap_delta"}
    if goal_ledger is None:
        import mission_spend as ms
        goal_ledger = ms._goal_ledger(rec["goal"])
    cur = goal_ledger.status().get("cap")
    if cur is None:
        return {"applied": False, "why": "goal has no cap"}
    res = goal_ledger.declare_cap(int(cur) + delta, f"plan {str(rec.get('plan_commit', ''))[:12]}",
                                  approval_id=aid)
    return {"applied": bool(res.get("ok")) and "already consumed" not in res.get("reason", ""),
            "why": res.get("reason", ""), "cap": res.get("cap")}


def advance_unit(rec: dict, plan: dict, unit: str, repo: Path, *, arm_fn=None, headroom=None) -> dict:
    """Arm ONE unit of an approved plan if every precondition holds. Returns {status, why, ...}."""
    goal = rec["goal"]
    if unit not in plan["units"]:
        return {"status": "NOT_LISTED", "why": f"{unit} is not in the plan's units list"}
    i = plan["units"].index(unit)
    pdir = repo / plan["packet_dir"]
    packet = pdir / f"{unit}.md"
    route = pdir / f"route-{unit}.json"
    if i > 0 and not receipt_complete(pdir / f"{plan['units'][i - 1]}-receipt.md"):
        return {"status": "WAITING_FOR_RECEIPT", "why": f"predecessor {plan['units'][i - 1]} has no complete receipt"}
    if not packet.exists() or not route.exists():
        return {"status": "WAITING_FOR_AUTHORITY", "why": "packet or route file missing"}
    sha = _file_sha(packet)
    want = plan["packet_shas"].get(unit)
    if want and not sha.startswith(want.lower()):
        return {"status": "WAITING_FOR_AUTHORITY", "why": f"packet sha {sha[:12]} != plan sha {want}"}
    est = (rec.get("estimates") or {}).get(unit)
    if not est:
        return {"status": "WAITING_FOR_AUTHORITY", "why": "no estimate for the unit in the approval record"}
    room = (headroom or goal_headroom)(goal)
    if room is None or room < int(est) + ADVANCE_RESERVE:
        return {"status": "WAITING_FOR_AUTHORITY",
                "why": f"goal {goal} headroom {room} < estimate {est} + reserve {ADVANCE_RESERVE}"}
    live = _live_unit_mission(unit, packet)
    if live:
        return {"status": "RUNNING", "why": f"{live['mission_id']} ({live['state']}) holds {unit}"}
    import hashlib
    key = hashlib.sha256(f"{goal}|{unit}|{sha}".encode()).hexdigest()[:24]
    kp = _adv_dir() / "keys" / f"{key}.json"
    kp.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(kp, "x", encoding="utf-8") as fh:      # persisted BEFORE the arm: a second pass is a no-op
            json.dump({"goal": goal, "unit": unit, "packet_sha256": sha, "at": time.time()}, fh)
    except FileExistsError:
        return {"status": "ALREADY_ARMED", "why": f"singleflight key {key} present"}
    res = (arm_fn or arm_chain)(str(repo), "/gsd-autonomous", wu_packet=str(packet), token_estimate=int(est),
                                route=str(route), parallel_unit=f"lc-{unit}", max_cycles=3,
                                rollover_protocol=CAPSULE_V2, ce_goal=goal)
    return {"status": "ARMED" if res.get("ok") else "ARM_FAILED", "why": res.get("why") or "",
            "mission_id": res.get("mission_id"), "key": key}


def advance_pass(*, arm_fn=None, headroom=None, ledger_for=None) -> list[dict]:
    rows = []
    adir = lr.state_dir() / "approvals"
    if not advance_on() or not adir.is_dir():
        return rows
    for ap in sorted(adir.glob("*.json")):
        try:
            rec = json.loads(ap.read_text(encoding="utf-8-sig"))
            goal = rec["goal"]
            repo = Path(rec.get("repo") or ".")
            plan_path = Path(rec["plan_path"])
            if not plan_path.is_absolute():
                plan_path = repo / plan_path
            plan = parse_plan(plan_path)
            if not plan["status"].upper().startswith("APPROVED"):
                row = {"status": "WAITING_FOR_AUTHORITY", "why": f"plan status {plan['status']!r}"}
            else:
                if rec.get("cap_delta"):
                    ap_res = apply_approval(rec, goal_ledger=ledger_for(goal) if ledger_for else None)
                    if ap_res.get("applied"):
                        _adv_log(goal, None, "CAP_APPLIED", rec["approval_id"], cap=ap_res.get("cap"))
                row = None
                pdir = repo / plan["packet_dir"]
                for u in plan["units"]:
                    if not receipt_complete(pdir / f"{u}-receipt.md"):
                        row = {"unit": u, **advance_unit(rec, plan, u, repo, arm_fn=arm_fn, headroom=headroom)}
                        break
                if row is None:
                    row = {"status": "PLAN_COMPLETE", "why": "every unit has a receipt"}
            row.setdefault("unit", None)
            _adv_log(goal, row["unit"], row["status"], row.get("why", ""))
            rows.append({"mission_id": f"advance:{goal}", "action": "advance", **row})
        except Exception as exc:  # noqa: BLE001 -- one bad record never stops the pass
            rows.append({"mission_id": f"advance:{ap.stem}", "action": "advance", "status": "ERROR",
                         "error": f"{type(exc).__name__}: {exc}"[:300]})
    return rows


def supervise(*args, **kw) -> list[dict]:
    rows = _supervise_core(*args, **kw)
    dry = kw.get("dry_run", args[1] if len(args) > 1 else False)
    if not dry:
        try:
            rows = rows + advance_pass()
        except Exception as exc:  # noqa: BLE001
            rows = rows + [{"mission_id": "advance", "action": "advance", "status": "ERROR",
                            "error": f"{type(exc).__name__}: {exc}"[:300]}]
    return rows


