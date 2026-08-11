# Beacon pid-identity guard (T-BEACON-PID-REUSE-001, 2026-08-11).
#
# build_pane_map.ps1 accepted a beacon whenever its pid was PRESENT in the process
# table. Windows recycles pids, and 275 beacon files accumulate against ~20 real
# panes, so presence alone is not identity. Measured on 2026-08-11, five beacons
# with a "live" pid belonged to: conhost, LenovoVantage, StartMenuExperienceHost,
# svchost -- and one to a genuine claude.exe that had merely inherited a pid used
# by a session from 2026-07-18. That is the overcount the Owner reported (Jacobo
# showed 3 open panes against 2 real terminals).
#
# THE GUARD IS TIME, NOT NAME. There are two beacon writers and they record
# DIFFERENT pids on purpose:
#   kclaude.ps1::Write-PaneSidBeacon -> $PID, the PowerShell wrapper (ProcessName
#                                       "powershell")
#   modules/cpc_os/beacon.py         -> the ancestor claude.exe (ProcessName
#                                       "claude")
# Measured split among live beacons: 7 powershell, 10 claude. So a name allow-list
# would have rejected every kclaude-written beacon -- a far worse regression than
# the bug it set out to fix.
#
# What every honest beacon shares is ordering: the process ALWAYS exists before its
# beacon is written (kclaude writes from inside the wrapper; beacon.py walks up to
# an already-running ancestor). A recycled pid inverts that -- the process starts
# AFTER the beacon it appears to own. One comparison separates them, and it holds
# for both writers without knowing which one wrote the file.
#
# Mirrors the guard beacon.py::owning_pane_pid already applies at WRITE time
# ("Windows reuses pids, so a stale ppid can point at an unrelated live process").
# This is that same reasoning on the READ side, where it was missing.

# Clock skew between Get-Date (beacon) and Process.StartTime is sub-second on one
# host; 300 s is slack so a real pane is never dropped by a measurement artefact.
# Every observed phantom is stale by DAYS, so the slack costs no detection.
$script:BEACON_SKEW_TOLERANCE_SECONDS = 300

function ConvertTo-UtcOrNull {
    <#
      Parses both beacon timestamp shapes without a per-writer branch:
      kclaude.ps1 emits PowerShell 'o'  -> 2026-08-11T09:30:58.9296499Z
      beacon.py   emits ISO with offset -> 2026-08-11T10:38:26.027151+00:00
      Returns $null when unparseable so the caller can fail open.
    #>
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return $null }
    $styles = [System.Globalization.DateTimeStyles]::AdjustToUniversal -bor `
              [System.Globalization.DateTimeStyles]::AssumeUniversal
    $parsed = [datetime]::MinValue
    if ([datetime]::TryParse($Text, [System.Globalization.CultureInfo]::InvariantCulture,
                             $styles, [ref]$parsed)) {
        return $parsed
    }
    return $null
}

function Test-BeaconOwnsPid {
    <#
      $true when the live process plausibly IS the one that wrote the beacon.
      FAIL-OPEN by construction: an unreadable timestamp or an unreadable process
      start time returns $true, i.e. exactly the pre-guard behaviour (presence
      only). The guard may only ever REMOVE a provable phantom, never a pane it
      merely failed to measure.
    #>
    param(
        [datetime]$ProcessStartUtc,
        [string]$BeaconTs,
        [int]$ToleranceSeconds = $script:BEACON_SKEW_TOLERANCE_SECONDS
    )
    $ts = ConvertTo-UtcOrNull $BeaconTs
    if ($null -eq $ts) { return $true }
    if ($null -eq $ProcessStartUtc -or $ProcessStartUtc -eq [datetime]::MinValue) { return $true }
    # Normalise the KIND before comparing. [datetime]::Compare ignores Kind, so a
    # caller that passes Process.StartTime (Kind=Local, e.g. 12:33 local) against a
    # UTC beacon (10:38Z) would read the pane as 2 h "newer" than its own beacon and
    # the guard would drop a REAL pane -- the one failure mode this guard must never
    # have. Caught by V-BEACON-KIND-NORMALISED. Unspecified is taken as UTC per the
    # parameter name; Local is converted.
    $startUtc = $ProcessStartUtc
    if ($ProcessStartUtc.Kind -eq [System.DateTimeKind]::Local) {
        $startUtc = $ProcessStartUtc.ToUniversalTime()
    }
    return ($startUtc -le $ts.AddSeconds($ToleranceSeconds))
}

if ($MyInvocation.InvocationName -ne '.' -and $args -contains '--selftest') {
    $fails = 0
    function _t($name, $cond) {
        if ($cond) { Write-Output "  OK   $name" } else { Write-Output "  FAIL $name"; $script:fails++ }
    }
    # [datetime]'...Z' yields Kind=Local, so every fixture is built explicitly in
    # UTC. Using the cast here is what first hid the Kind bug the guard now handles.
    function _utc($y, $mo, $d, $h, $mi, $s) {
        New-Object System.DateTime $y, $mo, $d, $h, $mi, $s, ([System.DateTimeKind]::Utc)
    }
    $beacon = '2026-08-11T10:38:26.027151+00:00'   # beacon.py shape, 10:38:26Z
    $beaconO = '2026-08-11T09:30:58.9296499Z'      # kclaude.ps1 'o' shape

    # Real pane: the process existed before its beacon was written.
    _t 'V-BEACON-PID-CTIME-KEEPS-OLDER' (Test-BeaconOwnsPid (_utc 2026 8 11 10 33 13) $beacon)
    _t 'V-BEACON-PID-CTIME-KEEPS-EQUAL' (Test-BeaconOwnsPid (_utc 2026 8 11 9 30 58) $beaconO)
    # Recycled pid: the process started days AFTER the beacon it appears to own.
    _t 'V-BEACON-PID-CTIME-REJECTS-NEWER' (-not (Test-BeaconOwnsPid (_utc 2026 8 11 12 0 0) '2026-07-18T15:01:32.6047295Z'))
    _t 'V-BEACON-PID-IDENTITY-REJECTS-FOREIGN' (-not (Test-BeaconOwnsPid (_utc 2026 8 11 11 57 53) '2026-07-17T10:10:04.9934488Z'))
    # Fail-open paths: unmeasurable must never drop a pane.
    _t 'V-BEACON-FAILOPEN-NO-TS' (Test-BeaconOwnsPid (_utc 2026 8 11 12 0 0) '')
    _t 'V-BEACON-FAILOPEN-BAD-TS' (Test-BeaconOwnsPid (_utc 2026 8 11 12 0 0) 'not-a-date')
    _t 'V-BEACON-FAILOPEN-NO-START' (Test-BeaconOwnsPid ([datetime]::MinValue) $beacon)
    # Skew slack keeps a pane whose start is marginally after the beacon.
    _t 'V-BEACON-SKEW-SLACK' (Test-BeaconOwnsPid (_utc 2026 8 11 10 40 0) $beacon)
    # A LOCAL-kind start time must be converted, not compared raw. Without the
    # normalisation this is the case that silently deleted real panes.
    $localStart = (_utc 2026 8 11 10 33 13).ToLocalTime()
    _t 'V-BEACON-KIND-NORMALISED' (Test-BeaconOwnsPid $localStart $beacon)

    if ($fails -gt 0) { Write-Output "BEACON_IDENTITY_SELFTEST=FAIL"; exit 1 }
    Write-Output "BEACON_IDENTITY_SELFTEST=PASS"
    exit 0
}
