import type { Register } from 'claude-code'

// Unit Zero probe. It exercises only the surfaces the CPP Cognitive Runtime rewrites, with the same hook shapes
// as mods/cpp-cognitive-runtime/hooks/register.ts. A mode file selects one experiment per run:
//   observe           pass everything through
//   subagent-lean     drop the instructions and skill_listing attachments on subagent requests only
//   subagent-replace  replace the subagent instructions attachment with a short marker text
//   seam              tool.call Bash: await next(e), return the tool's own result with stdout replaced
//   defer             move every tool outside CORE_TOOLS behind ToolSearch
//   section-drop      drop the `memory` prompt section
// It records identifiers and sizes only, never file or prompt content.
const OUT = 'C:/Users/User/.claude/state/ccr/uz-probe-out'
const CORE_TOOLS = new Set(['Read', 'Edit', 'Write', 'Glob', 'Grep', 'Bash', 'PowerShell', 'Agent', 'ToolSearch', 'Skill'])
const REPLACED = 'UZ-REPLACED-INSTRUCTIONS'
const PROJECTED = 'UZ-PROJECTED'

const rows: unknown[] = []
let sid = 'unknown'
let mode = 'observe'

const record = async ($: any, ev: string, data: Record<string, unknown>) => {
  rows.push({ ts: Date.now(), ev, mode, ...data })
  try {
    await $.fs.write(`${OUT}/${sid}.jsonl`, rows.map(r => JSON.stringify(r)).join('\n') + '\n')
  } catch {
    rows.push({ ts: Date.now(), ev: 'probe.write_failed' })
  }
}

const seam = async ($: any, e: any, next: any) => {
  const r: any = await next(e)
  const res = r?.result
  if (mode !== 'seam' || r?.deny !== undefined || !res || typeof res.stdout !== 'string') {
    await record($, 'tool.call', { tool: e.tool, applied: false, stdout: typeof res?.stdout === 'string' ? res.stdout.length : null })
    return r
  }
  await record($, 'tool.call', { tool: e.tool, applied: true, stdout: res.stdout.length, out: PROJECTED.length })
  return { result: { ...res, stdout: PROJECTED }, ...(r.context ? { context: r.context } : {}) }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const r = await next(e)
    sid = await $.session.id()
    try { mode = JSON.parse(await $.fs.read(`${OUT}/mode.json`)).mode ?? 'observe' } catch { mode = 'observe' }
    await record($, 'session.start', { version: await $.session.version(), interactive: e.isInteractive, tools: (await $.tool.list()).length })
    return r
  })

  on('prompt.compose', async ($, e, next) => {
    const r = await next(e)
    await record($, 'prompt.compose', { sections: r.sections.map(s => [s.id, s.scope, s.text.length]) })
    return r
  })

  on('prompt.section', async ($, e, next) => {
    const r = await next(e)
    if (r.text === null) return r
    const drop = mode === 'section-drop' && e.name === 'memory'
    await record($, 'prompt.section', { name: e.name, len: r.text.length, applied: drop })
    return drop ? { text: null } : r
  })

  on('prompt.attachment', async ($, e, next) => {
    const a = e as any
    const isSub = typeof a.agentId === 'string'
    const lean = mode === 'subagent-lean' && isSub && ['instructions', 'skill_listing'].includes(a.type)
    const repl = mode === 'subagent-replace' && isSub && a.type === 'instructions'
    const r = lean ? { text: null } : repl ? { text: REPLACED } : await next(e)
    await record($, 'prompt.attachment', { type: a.type, origin: a.origin?.kind ?? null, agent: isSub, len: a.text?.length ?? null, out: r.text?.length ?? null })
    return r
  })

  on('tool.describe', async ($, e, next) => {
    const r: any = await next(e)
    const a = e as any
    const out = mode === 'defer' && !CORE_TOOLS.has(a.tool) ? { ...r, isDeferred: true } : r
    await record($, 'tool.describe', { tool: a.tool, deferred: out.isDeferred ?? null })
    return out
  })

  on('agent.spawn', async ($, e, next) => {
    const r = await next(e)
    await record($, 'agent.spawn', { type: e.subagentType, prompt: e.prompt.length })
    return r
  })

  on('tool.call', { tool: 'Bash' }, seam).catch(($, e, next) => next(e))

  on('turn.complete', async ($, e, next) => {
    const r = await next(e)
    const a = e as any
    await record($, 'turn.complete', { agent: a.agentId ?? null, usage: a.usage })
    return r
  })
}
