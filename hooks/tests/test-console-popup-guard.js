/**
 * Two-pole proof for hooks/console-popup-guard.js.
 * Every BLOCK case is paired with a control in which the fix is present and the guard passes,
 * so an always-block mutant fails the controls and a never-block mutant fails the blocks.
 *   node hooks/tests/test-console-popup-guard.js        (pure run())
 *   node hooks/tests/test-console-popup-guard.js --e2e  (also drives the script over stdin)
 */
"use strict";
const path = require("path");
const { spawnSync } = require("child_process");
const GUARD = path.join(__dirname, "..", "console-popup-guard.js");
const { run } = require(GUARD);

let pass = 0, fail = 0;
function check(id, cond, info) {
  if (cond) { pass++; console.log(`  [OK  ] ${id}`); }
  else { fail++; console.log(`  [FAIL] ${id} ${info || ""}`); }
}
const W = { platform: "win32" };
const ps = (command) => run({ tool_name: "PowerShell", tool_input: { command } }, W);

// The literal neom-portatil.ps1 shape that was live on 2026-10-15.
const NEOM_BAD = [
  "    $linea = 'cmd.exe /c \"\"{0}\" \"{1}\"\"' -f $NODE, $LECTOR",
  "    $creado = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{",
  "      CommandLine      = $linea",
  "      CurrentDirectory = $RAIZ",
  "    }",
].join("\n");
const NEOM_FIXED = NEOM_BAD.replace(
  "      CurrentDirectory = $RAIZ",
  "      CurrentDirectory = $RAIZ\n      ProcessStartupInformation = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ ShowWindow = [uint16]0 }"
);

console.log("console-popup-guard -- V-POPUP");
check("V-POPUP-WMI-BLOCK", ps(NEOM_BAD).block);
check("V-POPUP-WMI-FIXED-PASS", !ps(NEOM_FIXED).block);
check("V-POPUP-WMIMETHOD-BLOCK", ps("Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList 'python x.py'").block);
check("V-POPUP-WMI-QUERY-PASS", !ps("Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Select CreationDate").block);

check("V-POPUP-SP-CMD-BLOCK", ps("Start-Process cmd.exe -ArgumentList '/c ping -n 3 127.0.0.1'").block);
check("V-POPUP-SP-FILEPATH-PY-BLOCK", ps("Start-Process -FilePath \"C:\\Python312\\python.exe\" -ArgumentList 'srv.py'").block);
check("V-POPUP-SP-SCRIPT-BLOCK", ps("Start-Process .\\scripts\\serve.ps1").block);
check("V-POPUP-SP-HIDDEN-PASS", !ps("Start-Process cmd.exe -ArgumentList '/c ping' -WindowStyle Hidden").block);
check("V-POPUP-SP-NONEW-PASS", !ps("Start-Process python.exe -ArgumentList 'x.py' -NoNewWindow -Wait").block);
check("V-POPUP-SP-CONTINUATION-PASS", !ps("Start-Process python.exe `\n  -ArgumentList 'x.py' `\n  -WindowStyle Hidden").block);
check("V-POPUP-SP-GUI-PASS", !ps("Start-Process notepad.exe; Start-Process 'https://example.com'").block);
check("V-POPUP-SP-VAR-PASS", !ps("Start-Process $exe -ArgumentList $a").block);

check("V-POPUP-TASK-CMD-BLOCK", ps("$a = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c x.cmd'").block);
check("V-POPUP-TASK-WSCRIPT-PASS", !ps("$a = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument '//B //Nologo h.vbs cmd.exe /c x.cmd'").block);
check("V-POPUP-TASK-S4U-PASS", !ps("$a = New-ScheduledTaskAction -Execute 'python.exe'; $p = New-ScheduledTaskPrincipal -UserId User -LogonType S4U").block);
check("V-POPUP-SCHTASKS-BLOCK", ps("schtasks /create /tn X /sc minute /tr \"python.exe C:\\x.py\"").block);
check("V-POPUP-SCHTASKS-PYTHONW-PASS", !ps("schtasks /create /tn X /sc minute /tr \"pythonw.exe C:\\x.py\"").block);

check("V-POPUP-BASH-SAME-RULES", run({ tool_name: "Bash", tool_input: { command: "powershell -c \"Start-Process cmd.exe\"" } }, W).block);
check("V-POPUP-NONWIN-PASS", !run({ tool_name: "PowerShell", tool_input: { command: NEOM_BAD } }, { platform: "linux" }).block);

// File ratchet: only GROWTH blocks.
const wr = (content, preText) => run({ tool_name: "Write", tool_input: { file_path: "C:\\x\\a.ps1", content } }, { ...W, preText });
check("V-POPUP-FILE-NEW-DEBT-BLOCK", wr(NEOM_BAD, "").block);
check("V-POPUP-FILE-FIX-PASS", !wr(NEOM_FIXED, NEOM_BAD).block);
check("V-POPUP-FILE-OLD-DEBT-UNRELATED-EDIT-PASS",
  !run({ tool_name: "Edit", tool_input: { file_path: "C:\\x\\a.ps1", old_string: "$RAIZ", new_string: "$RAIZ2" } }, { ...W, preText: NEOM_BAD }).block);
check("V-POPUP-FILE-EDIT-ADDS-DEBT-BLOCK",
  run({ tool_name: "Edit", tool_input: { file_path: "C:\\x\\a.ps1", old_string: "# end", new_string: "Start-Process python.exe x.py" } }, { ...W, preText: "# end" }).block);
check("V-POPUP-FILE-NONSCRIPT-PASS", !run({ tool_name: "Write", tool_input: { file_path: "C:\\x\\notes.md", content: NEOM_BAD } }, W).block);

process.env.CLAUDE_CONSOLE_POPUP_GUARD = "off";
check("V-POPUP-KILLSWITCH", !ps(NEOM_BAD).block);
delete process.env.CLAUDE_CONSOLE_POPUP_GUARD;

if (process.argv.includes("--e2e") && process.platform === "win32") {
  const drive = (payload) => spawnSync(process.execPath, [GUARD], { input: JSON.stringify(payload), encoding: "utf8", timeout: 8000 });
  const b = drive({ tool_name: "PowerShell", tool_input: { command: NEOM_BAD } });
  check("V-POPUP-E2E-BLOCK-EXIT2", b.status === 2 && /CONSOLE POPUP/.test(b.stderr) && /"decision":"block"/.test(b.stdout), `status=${b.status}`);
  const ok = drive({ tool_name: "PowerShell", tool_input: { command: NEOM_FIXED } });
  check("V-POPUP-E2E-CLEAN-EXIT0", ok.status === 0 && !ok.stdout, `status=${ok.status} signal=${ok.signal} err=${ok.error && ok.error.code} stderr=${String(ok.stderr).slice(0, 200)}`);
  const bom = spawnSync(process.execPath, [GUARD], { input: "\uFEFF" + JSON.stringify({ tool_name: "PowerShell", tool_input: { command: NEOM_BAD } }), encoding: "utf8", timeout: 8000 });
  check("V-POPUP-E2E-BOM-STILL-BLOCKS", bom.status === 2, `status=${bom.status}`);
}

console.log(`POPUP_PASS=${pass}/${pass + fail}`);
process.exit(fail ? 1 : 0);
