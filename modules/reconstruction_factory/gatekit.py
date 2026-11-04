"""Gate kit: named V-gates with a DRILL each. `--drills` sabotages the instrument a gate measures and requires that gate to turn RED
(a gate that cannot go red is a rumour). Exit codes: 0 all green (or all drills red), 1 a gate red (or a drill left green), 2 UNMEASURED."""
import contextlib
import sys
import traceback


class Unmeasured(Exception):
    pass


@contextlib.contextmanager
def patched(obj, attr, value):
    old = getattr(obj, attr)
    setattr(obj, attr, value)
    try:
        yield
    finally:
        setattr(obj, attr, old)


class Kit:
    def __init__(self, title):
        self.title, self.gates = title, []

    def gate(self, name, drill=None):
        def deco(fn):
            self.gates.append((name, fn, drill))
            return fn
        return deco

    def _run(self, fn, ctx):
        try:
            fn(ctx)
            return "GREEN", ""
        except Unmeasured as e:
            return "UNMEASURED", str(e)
        except AssertionError as e:
            return "RED", str(e)[:300]
        except Exception as e:                      # a crash is red, never silently green
            return "RED", "%s: %s" % (type(e).__name__, traceback.format_exc(limit=2)[-300:] if not str(e) else str(e)[:300])

    def main(self, ctx_factory, argv=None):
        argv = list(sys.argv[1:] if argv is None else argv)
        drills = "--drills" in argv
        only = [a for a in argv if a.startswith("V-")]
        ctx = ctx_factory()
        bad = unm = 0
        try:
            for name, fn, drill in self.gates:
                if only and name not in only:
                    continue
                if not drills:
                    st, why = self._run(fn, ctx)
                    print("%-34s %s %s" % (name, st, why))
                    bad += st == "RED"
                    unm += st == "UNMEASURED"
                else:
                    if drill is None:
                        print("%-34s DRILL-MISSING" % name)
                        bad += 1
                        continue
                    st0, _ = self._run(fn, ctx)
                    with drill(ctx) if _takes(drill) else drill():
                        st, why = self._run(fn, ctx)
                    ok = st0 == "GREEN" and st == "RED"
                    print("%-34s DRILL %s (clean=%s drilled=%s)" % (name, "RED-OK" if ok else "STILL-%s" % st, st0, st))
                    bad += not ok
        finally:
            close = getattr(ctx, "close", None)
            if close:
                close()
        total = len([g for g in self.gates if not only or g[0] in only])
        print("%s: %s (%d gates%s)" % (self.title, "OK" if not bad and not unm else ("UNMEASURED" if unm and not bad else "FAIL"), total, ", drills" if drills else ""))
        return 1 if bad else (2 if unm else 0)


def _takes(fn):
    import inspect
    return len(inspect.signature(fn).parameters) >= 1
