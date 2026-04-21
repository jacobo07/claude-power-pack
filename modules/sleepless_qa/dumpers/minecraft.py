"""
Minecraft runtime dumper — headless Paper server + Mineflayer bot.

Shells out to a Node-based Mineflayer bot (installed by install.sh) to run
chat/command steps against a running Paper server. Captures the bot's chat
log + a tail of the Paper server's latest.log.

Assumption: the target repo's PaperMC plugin is already built and installed
into a test server instance. The server and bot are launched as subprocesses.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from .base import ActionScript, Dumper, DumperError, EvidenceBundle

logger = logging.getLogger(__name__)

BOT_SCRIPT = r'''
const mineflayer = require('mineflayer');
const fs = require('fs');
const path = require('path');

const actionPath = process.argv[2];
const outDir = process.argv[3];
const action = JSON.parse(fs.readFileSync(actionPath, 'utf-8'));
const setup = action.setup || {};

const chatLog = [];
const events = [];

const bot = mineflayer.createBot({
  host: setup.host || 'localhost',
  port: setup.port || 25565,
  username: setup.username || 'SleeplessQA',
  version: setup.version || '1.21',
});

bot.on('spawn', async () => {
  events.push({ ts: Date.now(), kind: 'spawn' });
  for (const step of action.steps || []) {
    try {
      if (step.kind === 'chat' || step.kind === 'command') {
        const text = step.kind === 'command' ? '/' + (step.value || '') : (step.value || '');
        bot.chat(text);
      } else if (step.kind === 'wait') {
        const ms = parseInt(step.timeout_ms || 1000, 10);
        await new Promise(r => setTimeout(r, ms));
      }
    } catch (e) {
      events.push({ ts: Date.now(), kind: 'step_error', error: String(e) });
    }
    await new Promise(r => setTimeout(r, 500));
  }
  await new Promise(r => setTimeout(r, 2000));
  fs.writeFileSync(path.join(outDir, 'chat.log'), chatLog.join('\n'), 'utf-8');
  fs.writeFileSync(path.join(outDir, 'events.json'), JSON.stringify(events, null, 2), 'utf-8');
  bot.quit();
  process.exit(0);
});

bot.on('message', (msg) => {
  chatLog.push(`[${new Date().toISOString()}] ${msg.toString()}`);
});

bot.on('error', (err) => {
  events.push({ ts: Date.now(), kind: 'error', error: String(err) });
  fs.writeFileSync(path.join(outDir, 'events.json'), JSON.stringify(events, null, 2), 'utf-8');
  process.exit(2);
});

setTimeout(() => {
  events.push({ ts: Date.now(), kind: 'timeout' });
  fs.writeFileSync(path.join(outDir, 'events.json'), JSON.stringify(events, null, 2), 'utf-8');
  try { bot.quit(); } catch (e) {}
  process.exit(3);
}, parseInt(setup.overall_timeout_ms || 60000, 10));
'''


class MinecraftDumper(Dumper):
    runtime_class = "minecraft"

    def __init__(self, repo_path: Path, config: dict[str, Any], run_id: str) -> None:
        super().__init__(repo_path, config, run_id)
        self._out_dir: Path | None = None
        self._action_name: str = ""
        self._exit_code: int | None = None
        self._server_log_path: Path | None = None

    def launch(self) -> None:
        self._out_dir = Path(tempfile.mkdtemp(prefix=f"sqa-mc-{self.run_id}-"))
        mineflayer_dir = Path(
            os.path.expanduser(
                self.config.get("mineflayer_install_dir", "~/.cache/sleepless-qa/mineflayer")
            )
        )
        if not (mineflayer_dir / "node_modules" / "mineflayer").exists():
            raise DumperError(
                f"Mineflayer not installed at {mineflayer_dir}. Run vps/install.sh first."
            )
        self._mineflayer_dir = mineflayer_dir
        self._launched = True

    def trigger(self, action: ActionScript) -> None:
        if self._out_dir is None:
            raise DumperError("MinecraftDumper.trigger() before launch()")
        self._action_name = action.name

        server_log = action.setup.get("paper_log_path")
        if server_log:
            self._server_log_path = Path(os.path.expanduser(server_log))

        bot_script_path = self._out_dir / "bot.js"
        bot_script_path.write_text(BOT_SCRIPT, encoding="utf-8")
        action_json = self._out_dir / "action.json"
        action_json.write_text(action.model_dump_json(), encoding="utf-8")

        cmd = ["node", str(bot_script_path), str(action_json), str(self._out_dir)]
        timeout = int(self.config.get("subprocess_timeout_seconds", 180))
        logger.info("Launching Mineflayer bot: %s", cmd)

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self._mineflayer_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise DumperError(f"Mineflayer bot timed out after {timeout}s") from exc

        self._exit_code = result.returncode
        (self._out_dir / "bot.stdout").write_text(result.stdout or "", encoding="utf-8")
        (self._out_dir / "bot.stderr").write_text(result.stderr or "", encoding="utf-8")

    def capture(self) -> EvidenceBundle:
        if self._out_dir is None:
            raise DumperError("MinecraftDumper.capture() before trigger()")
        log_excerpts: dict[str, str] = {}
        chat_log_path = self._out_dir / "chat.log"
        if chat_log_path.exists():
            log_excerpts["bot_chat"] = chat_log_path.read_text(encoding="utf-8", errors="replace")[-16_000:]
        events_path = self._out_dir / "events.json"
        if events_path.exists():
            log_excerpts["bot_events"] = events_path.read_text(encoding="utf-8", errors="replace")

        if self._server_log_path and self._server_log_path.exists():
            try:
                tail = self._server_log_path.read_bytes()[-16_000:].decode("utf-8", "replace")
                log_excerpts["paper_latest_log"] = tail
            except OSError as exc:
                logger.warning("Could not read Paper log: %s", exc)

        return EvidenceBundle(
            run_id=self.run_id,
            runtime_class=self.runtime_class,
            action_script_name=self._action_name,
            screenshots=[],
            log_excerpts=log_excerpts,
            http_responses=[],
            exit_code=self._exit_code,
            stdout="",
            stderr="",
            metadata={
                "out_dir": str(self._out_dir),
                "mineflayer_dir": str(self._mineflayer_dir),
            },
        )

    def teardown(self) -> None:
        self._launched = False
