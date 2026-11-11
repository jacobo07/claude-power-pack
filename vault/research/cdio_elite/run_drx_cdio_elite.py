"""Deep Research X (PP modules/deep-research) over the 9 CDIO Elite Web Experience specialists, sequential.

Owner 2026-11-12: integrate CDIO_Elite_Web_Experience_Agent_Pack_v1.0.0 into CDIO, give every agent persistent
memory, and run DRX over each topic ("Los 9 ya, uno tras otro"). Queue pattern copied from
GEO-audit/data/costaluz/ai-visibility-drx-2026-11/run_drx_ai_visibility.py: DRX holds a single-instance lock, other
queues (DRX yield experiment, CostaLuz, Wii) share it, so a busy lock is waited out (bounded), never forced, and a
'deep_research locked' report is a lost race, not a run.
Usage: pythonw run_drx_cdio_elite.py [A B ...]   (default: every topic without DONE.json under drx-out/<T>/)
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP = Path(os.environ["USERPROFILE"]) / ".claude" / "skills" / "claude-power-pack"
DRX = PP / "modules" / "deep-research" / "deep_research.py"
LOCK = PP / "vault" / "research" / ".deep-research.lock"
OUT = HERE / "drx-out"
PY = r"C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"
MODEL = os.environ.get("CLAUDEPP_RESEARCH_MODEL", "claude-sonnet-5-5")
LOCK_WAIT_S, LOCK_POLL_S = 12 * 3600, 120  # queue ahead (yield experiment + CostaLuz) is several hours

CTX = ("A design and conversion lead who builds and audits websites (universal sites plus a restaurant/hospitality "
       "mode) and decides which criteria a team of specialist review agents must enforce. They act on measured "
       "results, named studies, standards and concrete numbers, never on agency opinion.")

TAIL = (" For every claim give the primary source (peer-reviewed study, standard such as WCAG, dataset with sample size "
        "and date, controlled experiment) and say whether it was measured, vendor-asserted or opinion. Name findings "
        "that failed to replicate. Prefer 2020-2026 sources. Mark anything unverified.")

TOPICS = {
    "A_experience-director": (
        "Which UX practices have measured effects on task completion, error rate and comprehension on multi-page "
        "service websites, especially on mobile? What do usability studies show about forms, error recovery, "
        "empty and loading states, and cognitive load?"),
    "B_conversion-strategist": (
        "What do controlled experiments and published A/B test results show about which landing-page and booking or "
        "checkout funnel changes increase completed conversions? Which commonly recommended CRO tactics fail to "
        "replicate, and how large are typical true effect sizes?"),
    "C_consumer-psychologist": (
        "What does peer-reviewed research show about how trust signals, social proof, reviews, scarcity and urgency "
        "cues affect online purchase and booking decisions? Where does the evidence place the line between persuasion "
        "and dark patterns, and what do regulators (EU DSA, FTC, CNMC) classify as deceptive?"),
    "D_art-director": (
        "What does empirical research show about how visual aesthetics, photography, typography and visual "
        "complexity affect first-impression judgments, perceived credibility and usability of websites? How fast are "
        "those judgments formed and how stable are they?"),
    "E_motion-interaction-designer": (
        "What is the measured effect of UI animation, transitions and microinteractions on usability, perceived "
        "performance and comprehension? What does the evidence say about vestibular disorders, prefers-reduced-motion "
        "adoption, and WCAG 2.2 criteria on motion and animation?"),
    "F_information-architect": (
        "What do card sorting, tree testing and navigation studies show about how menu structure, labeling, menu "
        "depth versus breadth, and mobile navigation patterns (hamburger versus visible tabs) affect findability "
        "and task success on websites?"),
    "G_frontend-experience-engineer": (
        "What is the measured relationship between Core Web Vitals (LCP, INP, CLS) and user engagement or "
        "conversion? Which accessibility failures are most common on production websites according to large-scale "
        "audits such as WebAIM Million and HTTP Archive, and which automated tests catch them?"),
    "H_hospitality-brand-strategist": (
        "What does research show about how restaurant and hospitality websites influence reservation and visit "
        "decisions: menu presentation and prices online, food photography, online reviews and ratings, and direct "
        "booking versus third-party platforms such as TheFork or OpenTable?"),
    "I_ux-research-experimentation": (
        "What do methodological studies show about the reliability of A/B testing and usability testing on "
        "low-traffic websites: required sample sizes, peeking and optional stopping, novelty effects, sample ratio "
        "mismatch, and how many participants usability tests need to find most problems?"),
}


def finished(t: str) -> bool:
    return (OUT / t / "DONE.json").exists()


def wait_lock() -> bool:
    t0 = time.time()
    while LOCK.exists():
        if time.time() - t0 > LOCK_WAIT_S:
            return False
        time.sleep(LOCK_POLL_S)
    return True


def lost_race(d: Path) -> bool:
    """The engine answers a busy lock with a 'deep_research locked' report instead of failing: that is not a run."""
    texts = [p.read_text(encoding="utf-8", errors="replace") for p in d.glob("*.md")]
    texts.append((d / "run.log").read_text(encoding="utf-8", errors="replace") if (d / "run.log").exists() else "")
    return any("deep_research locked" in t for t in texts)


def run(t: str) -> str:
    d = OUT / t
    d.mkdir(parents=True, exist_ok=True)
    # 120 s default timed out Sonnet 5.5's decompose call on the first run (A, 2026-11-12 00:21, 0 queries, rc=3);
    # 240 s is the setting the DRX yield experiment's arm B tests.
    env = dict(os.environ, CLAUDEPP_RESEARCH_MODEL=MODEL,
               CLAUDEPP_RESEARCH_LLM_TIMEOUT_S=os.environ.get("CLAUDEPP_RESEARCH_LLM_TIMEOUT_S", "240"))
    cmd = [PY, str(DRX), "--prompt", TOPICS[t] + TAIL, "--depth", "2", "--breadth", "3", "--operator-context", CTX,
           "--out", str(d)]
    for attempt in range(1, 7):
        if not wait_lock():
            return f"{t}: LOCK_BUSY after {LOCK_WAIT_S}s - skipped, rerun later"
        for p in d.glob("*.md"):
            p.unlink()
        t0 = time.time()
        with (d / "run.log").open("wb") as log:
            rc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, env=env).returncode
        if not lost_race(d):
            break
        time.sleep(LOCK_POLL_S)
    else:
        return f"{t}: lost the lock race 6 times - skipped, rerun later"
    rec = {"topic": t, "rc": rc, "model": MODEL, "wall_s": round(time.time() - t0, 1), "attempts": attempt,
           "artifacts": sorted(p.name for p in d.iterdir() if p.name not in ("run.log", "DONE.json"))}
    if rc == 0 and rec["artifacts"]:
        (d / "DONE.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return f"{t}: rc={rc} {rec['wall_s']}s artifacts={rec['artifacts']}"


def main() -> int:
    if sys.stdout is None:  # launched windowless with pythonw.exe: keep the queue log ourselves
        OUT.mkdir(parents=True, exist_ok=True)
        sys.stdout = sys.stderr = (OUT / "queue.log").open("a", encoding="utf-8", buffering=1)
    want = sys.argv[1:] or sorted(TOPICS)
    unknown = [t for t in want if t not in TOPICS]
    if unknown:
        print(f"unknown topics: {unknown}; valid: {sorted(TOPICS)}", flush=True)
        return 2
    for pass_no in (1, 2):  # pass 2 retries topics that ended without DONE.json (e.g. rc=3 INSUFFICIENT)
        todo = [t for t in want if not finished(t)]
        print(f"pass={pass_no} model={MODEL} todo={todo}", flush=True)
        for t in todo:
            print(time.strftime("%Y-%m-%dT%H:%M:%S"), run(t), flush=True)
    (OUT / "QUEUE_DONE.txt").write_text(time.strftime("%Y-%m-%dT%H:%M:%S"), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
