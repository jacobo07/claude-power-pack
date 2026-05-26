# PowerShell @'...'@ heredoc into native exe re-tokenizes argv

**Sealed**: 2026-05-26. **Trap class**: shell-quoting cascade across all repos.

## TRAP

```powershell
& 'C:\Program Files\Git\cmd\git.exe' commit -m @'
fix(...): something

The error message was "git not recognized" -- root cause was PATH.
'@
```

Error:
```
error: pathspec 'not' did not match any file(s) known to git
error: pathspec 'recognized error message...' did not match any file(s) known to git
```

## DIAGNOSIS

PowerShell 5.1's `@'...'@` is a here-string with literal preservation
INSIDE PowerShell -- but when the string is passed as an argument to
a native executable like `git.exe`, PowerShell's native-command
argument splitter re-tokenizes the value. The double-quote characters
inside the heredoc body act as **argv delimiters** on the C runtime
side, not as literal bytes. The single `-m` argument splits into:

  -m
  fix(...): something The error message was
  git
  not
  recognized
  -- root cause was PATH.

Everything after the first inner `"` becomes positional pathspecs.
Same bug pattern hits `mix`, `gh`, `node`, any native exe that
inherits PowerShell-style argv parsing on Windows.

## FIX (the only robust pattern)

Write the commit message to a file via the Write tool (which uses
literal bytes, NEVER through PowerShell's parser), then:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' commit -F path\to\commit_msg.txt
```

`git commit -F <file>` reads the file as raw bytes -- no argv parsing,
no escape-sequence interpretation, no quote re-tokenization. Multi-
line content with inner double-quotes / backticks / dollar signs is
preserved verbatim. Delete the file after the commit succeeds.

## RECOGNITION SIGNAL

Any of these git errors when invoking from PowerShell after a heredoc
commit message:

- `error: pathspec '<random-word>' did not match`
- `fatal: bad pathspec` (when no actual pathspec was supplied)
- The first word of an inner-quoted string showing up as a pathspec.

If you see ANY of these and your `-m` arg has inner `"` characters,
the heredoc -> argv reparser is the culprit. Switch to `-F`.

## SISTER PATTERNS (same root cause family)

- `mix run -e "IO.puts \"hello\""` from PowerShell -> same reparser
  splits on the inner `"`. Use `mix run -f script.exs` instead.
- `gh issue create --title @'multi-line "with quotes"'@` -> same.
  Use `gh issue create --body-file body.md`.
- `node -e "console.log(\"x\")"` -> same. Use a `.js` file.
- Any native exe that accepts a long string arg with inner punctuation
  on Windows PowerShell -> prefer file-based input over inline.

## DOCTRINE ADDENDUM

The Windows Bash Bridge Reliability rule (2026-05-21) says "prefer
PowerShell for git/mix/gh/npm". This lesson extends it: PowerShell
is the right tool, but never pass a multi-line / quote-bearing
argument to a native exe via `@'...'@`. Use the file-based variant
of whatever flag the exe supports (`-F`, `--body-file`, `--from-file`,
script file).
