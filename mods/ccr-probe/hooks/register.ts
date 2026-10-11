import type { Register } from 'claude-code'

// M1 probe. Records engine identifiers and sizes (never file or prompt content) so the
// capability matrix rests on runtime evidence. A mode file selects one experiment per run:
//   observe       pass everything through
//   subagent-lean drop the instruction-file and listing attachments on subagent requests only
//   defer         move every tool outside CORE_TOOLS behind ToolSearch
//   compact       after the first main turn, compact with a hook-built kept-set (no summarizer)
const OUT = 'C:/Users/User/.claude/state/ccr/probe'
const CORE_TOOLS = new Set(['Read', 'Edit', 'Write', 'Glob', 'Grep', 'Bash', 'PowerShell', 'Agent', 'ToolSearch', 'Skill'])

const rows: unknown[] = []
let sid = 'unknown'
let mode = 'observe'
let compacted = false

const record = async ($: any, ev: string, data: Record<string, unknown>) => {
  rows.push({ ts: Date.now(), ev, mode, ...data })
  try {
    await $.fs.write(`${OUT}/${sid}.jsonl`, rows.map(r => JSON.stringify(r)).join('\n') + '\n')
  } catch {
    rows.push({ ts: Date.now(), ev: 'probe.write_failed' })
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const r = await next(e)
    sid = await $.session.id()
    try { mode = JSON.parse(await $.fs.read(`${OUT}/mode.json`)).mode ?? 'observe' } catch { mode = 'observe' }
    let policyKeys: unknown = null
    try { policyKeys = Object.keys((await $.settings.read({ source: 'policy' })) ?? {}) } catch (err) { policyKeys = String(err) }
    await record($, 'session.start', {
      version: await $.session.version(), repo: await $.session.repo(), root: await $.session.root(),
      interactive: e.isInteractive, policyKeys, tools: (await $.tool.list()).map((t: any) => t.name),
    })
    return r
  })

  on('prompt.compose', async ($, e, next) => {
    const r = await next(e)
    await record($, 'prompt.compose', { model: e.model, tools: e.tools.length, sections: r.sections.map(s => [s.id, s.scope, s.text.length]) })
    return r
  })

  on('prompt.context', async ($, e, next) => {
    const r = await next(e)
    await record($, 'prompt.context', { blocks: r.blocks.map(b => [b.name, b.text.length]), files: (e.instructionFiles ?? []).map(f => [f.path, f.kind, f.content.length]) })
    return r
  })

  on('prompt.attachment', async ($, e, next) => {
    const a = e as any
    const isSub = typeof a.agentId === 'string'
    const lean = mode === 'subagent-lean' && isSub && ['instructions', 'skill_listing'].includes(a.type)
    const r = lean ? { text: null } : await next(e)
    await record($, 'prompt.attachment', { type: a.type, origin: a.origin, agent: isSub, len: a.text?.length ?? null, out: r.text?.length ?? null })
    return r
  })

  on('tool.describe', async ($, e, next) => {
    const r: any = await next(e)
    const a = e as any
    const out = mode === 'defer' && !CORE_TOOLS.has(a.tool) ? { ...r, isDeferred: true } : r
    await record($, 'tool.describe', { tool: a.tool, provider: a.provider, len: r.description?.length ?? null, deferred: out.isDeferred ?? null })
    return out
  })

  on('skill.prompt', async ($, e, next) => {
    const r = await next(e)
    await record($, 'skill.prompt', { skill: e.skill, len: r.text.length })
    return r
  })

  on('agent.spawn', async ($, e, next) => {
    const r = await next(e)
    await record($, 'agent.spawn', { type: e.subagentType, prompt: e.prompt.length, model: (r as any).model ?? null })
    return r
  })

  on('session.append', async ($, e, next) => {
    const r = await next(e)
    const a = e as any
    const c = a.message?.content
    await record($, 'session.append', { door: a.door, type: a.message?.type, size: typeof c === 'string' ? c.length : JSON.stringify(c ?? '').length })
    return r
  })

  on('session.compact', async ($, e, next) => {
    if (mode === 'compact' && e.trigger === 'plugin') {
      // kept-set built by the hook: the last two messages with their engine handles, no summarizer
      const kept = e.messages.slice(-2)
      await record($, 'session.compact', { trigger: e.trigger, before: e.messages.length, kept: kept.length, path: 'hook' })
      return { messages: kept }
    }
    const r: any = await next(e)
    await record($, 'session.compact', { trigger: e.trigger, before: e.messages.length, path: 'core', after: r.messages?.length ?? null, skip: r.skip ?? null })
    return r
  })

  on('turn.complete', async ($, e, next) => {
    const r = await next(e)
    const a = e as any
    await record($, 'turn.complete', { agent: a.agentId ?? null, usage: a.usage })
    if (mode === 'compact' && !compacted && !a.agentId) {
      compacted = true
      const c: any = await $.session.compact()
      await record($, 'compact.result', { keys: Object.keys(c ?? {}), n: c?.messages?.length ?? null, before: c?.tokensBefore ?? null, after: c?.tokensAfter ?? null, usage: c?.usage ?? null, skip: c?.skip ?? null })
    }
    return r
  })

  on('session.measure', async ($, e, next) => {
    const r = await next(e)
    await record($, 'session.measure', { context: e.context, changed: e.changed })
    return r
  })
}
