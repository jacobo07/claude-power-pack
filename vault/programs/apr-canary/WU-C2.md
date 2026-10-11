# WU-C2 canary: FALSE_DONE
cwd C:\Users\User\Apps\wt_apr. This is a canary; do exactly this and nothing else.
If this packet has NO section headed '## Residual' (first attempt):
  write C:\Users\User\.claude\skills\claude-power-pack\vault\programs\apr-canary\WU-C2-receipt.md with '# C2 receipt' and 'Status: DONE'. Create NOTHING else, no file, no commit. End.
If this packet HAS a '## Residual' section:
  1. Create canary/c2.txt containing exactly: ok
  2. git add canary/c2.txt; git commit -m "canary c2" (pathspec only).
  3. Write C:\Users\User\.claude\skills\claude-power-pack\vault\programs\apr-canary\WU-C2-receipt.md with '# C2 receipt' and 'Status: DONE'. End.
