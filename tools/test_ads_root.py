#!/usr/bin/env python3
"""V-ADS-ROOT -- el generador no debe escribir donde le dejaron la shell.

QUE PRUEBA, Y POR QUE ESTE FICHERO EXISTE
-----------------------------------------
ADS recibe el `cwd` del payload de Stop y lo trataba como raiz del repo. El
sintoma visible fue documentacion sobre los ficheros de un plugin escrita
dentro del arbol de OTRO plugin. La causa no fue que faltara un guardia:
habia uno, `_is_git_repo`, y pasaba -- pregunta `--is-inside-work-tree`, que
para cualquier ruta bajo el repo solo puede responder "si". Un guardia que no
puede devolver la otra respuesta no es un guardia.

El defecto peor no era el visible. El interruptor de apagado se buscaba bajo
esa misma base equivocada, asi que un repo que SI se habia dado de baja volvia
a generar documentacion en cuanto un turno terminaba por debajo de su raiz.
Una baja que deja de aplicarse en silencio es peor que el fichero mal puesto,
porque el fichero se ve.

Los dos casos que de verdad importan estan conducidos en rojo aqui: sin la
correccion, `test_killswitch_desde_subdirectorio` genera documentacion sobre
un repo que pidio no tenerla.

stdlib-only. No toca ningun repo real: monta uno de usar y tirar.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.ads.detector import repo_root, resolve_git  # noqa: E402

_PASES = 0
_FALLOS = 0


def _ok(gate: str, evidencia: str) -> None:
    global _PASES
    _PASES += 1
    print(f"  OK   {gate}: {evidencia}")


def _fail(gate: str, diagnostico: str) -> None:
    global _FALLOS
    _FALLOS += 1
    print(f"  FAIL {gate}: {diagnostico}")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [resolve_git(), "-C", str(repo), *args],
        capture_output=True, text=True, timeout=30,
        encoding="utf-8", errors="replace",
    )


def _montar_repo(base: Path) -> tuple[Path, Path]:
    """Un repo real con un subdirectorio que parece un modulo propio."""
    raiz = base / "repo"
    sub = raiz / "plugins" / "UnPluginCualquiera"
    sub.mkdir(parents=True)
    (raiz / "docs").mkdir()
    _git(raiz.parent, "init", "repo")
    _git(raiz, "config", "user.email", "gate@example.invalid")
    _git(raiz, "config", "user.name", "gate")
    (raiz / "semilla.txt").write_text("semilla\n", encoding="utf-8")
    _git(raiz, "add", "-A")
    _git(raiz, "commit", "-m", "semilla")
    return raiz, sub


def test_raiz_desde_subdirectorio(base: Path) -> None:
    raiz, sub = _montar_repo(base)
    obtenido = repo_root(sub)
    if obtenido == raiz.resolve():
        _ok("V-ADS-ROOT-FROM-SUBDIR", f"{sub.name} -> {obtenido.name}")
    else:
        _fail("V-ADS-ROOT-FROM-SUBDIR",
              f"esperaba {raiz}, obtuve {obtenido}")

    # Control positivo del propio test: si la resolucion fuera la identidad
    # -- el comportamiento ANTIGUO -- este gate no distinguiria nada. Que la
    # respuesta sea DISTINTA de la entrada es lo que le da informacion.
    if obtenido != sub.resolve():
        _ok("V-ADS-ROOT-NOT-IDENTITY",
            "la raiz resuelta difiere del directorio de invocacion")
    else:
        _fail("V-ADS-ROOT-NOT-IDENTITY",
              "resolvio a si mismo: el gate no puede ver el defecto")


def test_raiz_desde_la_raiz(base: Path) -> None:
    raiz, _ = _montar_repo(base)
    obtenido = repo_root(raiz)
    if obtenido == raiz.resolve():
        _ok("V-ADS-ROOT-IDEMPOTENT", "invocar en la raiz no la mueve")
    else:
        _fail("V-ADS-ROOT-IDEMPOTENT", f"{raiz} -> {obtenido}")


def test_fuera_de_repo(base: Path) -> None:
    suelto = base / "sin_git"
    suelto.mkdir()
    obtenido = repo_root(suelto)
    if obtenido == suelto.resolve():
        _ok("V-ADS-ROOT-NO-REPO-FALLBACK",
            "sin git responde la ruta dada, no una raiz inventada")
    else:
        _fail("V-ADS-ROOT-NO-REPO-FALLBACK",
              f"invento una raiz: {obtenido}")


def test_killswitch_desde_subdirectorio(base: Path) -> None:
    """LA RAMA ROJA. Sin la correccion, esto genera documentacion.

    El repo se da de baja en su raiz y la invocacion llega desde un
    subdirectorio, que es exactamente como llega en produccion.
    """
    from tools.ads_sync import sync

    raiz, sub = _montar_repo(base)
    (raiz / "docs" / ".ads-disabled").write_text("", encoding="utf-8")

    # El cambio tiene que ser de los que el detector SI documenta, o el
    # verde no distingue nada: en la primera version puse un fichero suelto,
    # que se clasifica MINOR, y la clausula de "no quedo documentacion"
    # salia verde tambien SIN la correccion -- verde por vacio, no por
    # acierto. Un paquete nuevo es lo que dispara CREATED de verdad.
    paquete = raiz / "paquete_nuevo"
    paquete.mkdir()
    (paquete / "__init__.py").write_text("", encoding="utf-8")
    (paquete / "modulo.py").write_text(
        "\n".join(f"def f{i}(): return {i}" for i in range(80)),
        encoding="utf-8")

    resumen = sync(sub)
    if resumen.get("disabled") is True:
        _ok("V-ADS-KILLSWITCH-FROM-SUBDIR",
            "la baja declarada en la raiz se respeta desde un subdirectorio")
    else:
        _fail("V-ADS-KILLSWITCH-FROM-SUBDIR",
              f"genero pese a la baja: {resumen}")

    # La base sobre la que `sync` resuelve todo -- la baja, la deteccion y
    # el destino de escritura -- es este campo. Es lo que de verdad decide
    # donde acaban los ficheros, y difiere entre los dos mundos, asi que es
    # lo que puede sostener un veredicto.
    if resumen.get("repo") == str(raiz.resolve()):
        _ok("V-ADS-SYNC-RESOLVES-ROOT",
            f"sync resolvio la raiz real: {raiz.name}")
    else:
        _fail("V-ADS-SYNC-RESOLVES-ROOT",
              f"sync trabajo sobre {resumen.get('repo')}")

    # Se conserva como cinturon, pero se declara lo que es: en este montaje
    # sale verde CON y SIN la correccion, porque la ruta mal unida rompe
    # tambien la deteccion de paquete y nada llega a escribirse. Cubre la
    # regresion futura; no acredita la de hoy. Un gate que no distingue sus
    # clausulas acreditadas de las que no lo estan miente por agregacion.
    huerfanos = list(sub.rglob("docs/arch/*.md"))
    if not huerfanos:
        _ok("V-ADS-NO-DOCS-IN-SUBDIR",
            "sin documentacion en el subdirectorio (clausula NO mutada)")
    else:
        _fail("V-ADS-NO-DOCS-IN-SUBDIR",
              f"{len(huerfanos)} fichero(s) mal ubicados: {huerfanos[:3]}")


def main() -> int:
    if not shutil.which(resolve_git()) and not Path(resolve_git()).exists():
        print("INCONCLUSIVE: no hay git invocable; el gate no pudo juzgar.")
        return 2

    base = Path(tempfile.mkdtemp(prefix="ads_root_gate_"))
    os.environ.setdefault("CLAUDE_ADS_NOW", "2026-01-01T00:00:00Z")
    try:
        for prueba in (test_raiz_desde_subdirectorio,
                       test_raiz_desde_la_raiz,
                       test_fuera_de_repo,
                       test_killswitch_desde_subdirectorio):
            caja = base / prueba.__name__
            caja.mkdir()
            try:
                prueba(caja)
            except Exception as exc:                       # noqa: BLE001
                # Un fallo del propio verificador NO es un fallo del sujeto:
                # se nombra aparte para que no se lea como una regresion.
                _fail(prueba.__name__,
                      f"VERIFICADOR ROTO: {type(exc).__name__}: {exc}")
    finally:
        shutil.rmtree(base, ignore_errors=True)

    total = _PASES + _FALLOS
    print(f"ADS_ROOT_PASS={_PASES}/{total}  threshold={total}/{total}")
    return 0 if _FALLOS == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
