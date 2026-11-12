' hidden_launch.vbs -- start a process with NO window and return at once.
'
'   wscript.exe //B //Nologo hidden_launch.vbs <target> [args...]
'
' <target> ending in .ps1 runs as: powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass
' -WindowStyle Hidden -File <target> [args...]. Anything else runs verbatim as <target> [args...].
'
' Why it exists: a detached powershell spawned from node never runs its script (DETACHED_PROCESS
' leaves the console host without a console), and an attached one dies with node. wscript is a
' GUI-subsystem host that survives a detached spawn, and WshShell.Run style 0 starts the child
' hidden from birth. Callers: hooks/session_start_hub.js (kresume autotype daemon launch),
' gate V-KRA-HUB-LAUNCH-BOOTS in tools/test_kresume_autotype.py.
'
' 2026-11-12: this file was missing from disk and had never been committed, so every /kresume
' arm logged "SKIP kresume_autotype (missing launcher ...)" and the successor waited for a manual
' /kresume. It is tracked now; do not gitignore it.
Option Explicit

Dim args, shell, i, cmd, target
Set args = WScript.Arguments
If args.Count = 0 Then
    WScript.Quit 2
End If

Function Q(s)
    If InStr(s, " ") > 0 Or InStr(s, vbTab) > 0 Or Len(s) = 0 Then
        Q = """" & s & """"
    Else
        Q = s
    End If
End Function

target = args(0)
If LCase(Right(target, 4)) = ".ps1" Then
    cmd = "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File " & Q(target)
Else
    cmd = Q(target)
End If
For i = 1 To args.Count - 1
    cmd = cmd & " " & Q(args(i))
Next

Set shell = CreateObject("WScript.Shell")
shell.Run cmd, 0, False
WScript.Quit 0
