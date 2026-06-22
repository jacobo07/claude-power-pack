<#
  install_pp_extension.ps1 -- package the PP Sessions extension to a .vsix and
  install it into Cursor. Idempotent; safe to re-run.

  Packaging is done by hand (System.IO.Compression with forward-slash zip entry
  names) because @vscode/vsce is unusable on this host (npm "Class extends value
  undefined" -- broken node/npm machinery). A .vsix is just a zip with a
  vsixmanifest + [Content_Types].xml at the root and the payload under extension/.
#>
[CmdletBinding()]
param(
  [string]$CursorCli = "C:\Users\User\AppData\Local\Programs\cursor\resources\app\bin\cursor.cmd"
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$repo = Split-Path $PSScriptRoot -Parent
$extDir = Join-Path $repo "extension"
$vsix = Join-Path $repo "pp-sessions.vsix"
$utf8 = New-Object System.Text.UTF8Encoding($false)

Write-Output "[1/4] Refreshing pane_map (data the extension reads)..."
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "build_pane_map.ps1")

Write-Output "[2/4] Packaging .vsix by hand..."
$manifest = @'
<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id="pp-sessions" Version="0.1.0" Publisher="kobii" />
    <DisplayName>PP Sessions</DisplayName>
    <Description xml:space="preserve">Side panel of resumable Claude Code panes derived from disk truth. One-click exact resume, no History restored.</Description>
    <Tags>claude-code,sessions,resume,cursor</Tags>
    <Categories>Other</Categories>
    <GalleryFlags>Public</GalleryFlags>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="^1.80.0" />
      <Property Id="Microsoft.VisualStudio.Code.ExtensionDependencies" Value="" />
      <Property Id="Microsoft.VisualStudio.Code.ExtensionPack" Value="" />
      <Property Id="Microsoft.VisualStudio.Code.ExtensionKind" Value="workspace" />
    </Properties>
    <License>extension/LICENSE.txt</License>
  </Metadata>
  <Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation>
  <Dependencies/>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true" />
    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" Addressable="true" />
    <Asset Type="Microsoft.VisualStudio.Services.Content.License" Path="extension/LICENSE.txt" Addressable="true" />
  </Assets>
</PackageManifest>
'@
$ctypes = @'
<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json"/>
  <Default Extension="js" ContentType="application/javascript"/>
  <Default Extension="md" ContentType="text/markdown"/>
  <Default Extension="svg" ContentType="image/svg+xml"/>
  <Default Extension="txt" ContentType="text/plain"/>
  <Default Extension="vsixmanifest" ContentType="text/xml"/>
</Types>
'@
if (Test-Path $vsix) { [System.IO.File]::Delete($vsix) }
$zip = [System.IO.Compression.ZipFile]::Open($vsix, 'Create')
function Add-Text($z, $name, $text, $enc) { $e = $z.CreateEntry($name); $s = $e.Open(); $b = $enc.GetBytes($text); $s.Write($b, 0, $b.Length); $s.Close() }
Add-Text $zip "extension.vsixmanifest" $manifest $utf8
Add-Text $zip "[Content_Types].xml" $ctypes $utf8
foreach ($f in (Get-ChildItem $extDir -Recurse -File)) {
  $rel = $f.FullName.Substring($extDir.Length + 1) -replace '\\', '/'
  [void][System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $f.FullName, "extension/$rel")
}
$zip.Dispose()
if (-not (Test-Path $vsix)) { throw "VSIX not produced" }
Write-Output ("    built: " + $vsix + " (" + (Get-Item $vsix).Length + " bytes)")

Write-Output "[3/4] Installing into Cursor..."
if (-not (Test-Path $CursorCli)) { throw "Cursor CLI not found: $CursorCli" }
& $CursorCli --install-extension $vsix --force
if ($LASTEXITCODE -ne 0) { throw "cursor --install-extension failed (exit $LASTEXITCODE)" }

Write-Output "[4/4] Verifying..."
$installed = & $CursorCli --list-extensions --show-versions 2>$null | Select-String -Pattern "pp-sessions"
if ($installed) {
  Write-Output ("    OK: " + $installed)
  Write-Output "Done. Reload Cursor (Reload Window) to activate the PP Sessions panel."
} else {
  throw "pp-sessions not found in installed extensions after install"
}
