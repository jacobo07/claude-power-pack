import type { Register } from 'claude-code'

// UMVM arm D probe: after turn 1, compact the main conversation with a hook-built kept-set in which every
// message is rebuilt without its handle (text, tool uses and tool-result text kept; media blocks cannot be
// expressed, so they leave). Records what the engine reports. Fixture only, never loaded on real work.
const OUT = 'C:/Users/User/.claude/state/ccr/gcprobe'
let sid = 'unknown'
let done = false
const rows: unknown[] = []
const rec = async ($: any, r: Record<string, unknown>) => {
  rows.push({ ts: Date.now(), ...r })
  await $.fs.write(`${OUT}/${sid}.jsonl`, rows.map(x => JSON.stringify(x)).join('\n') + '\n')
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const r = await next(e)
    sid = await $.session.id()
    try { done = (await $.fs.read(`${OUT}/${sid}.done`)) === '1' } catch { done = false } // first turn: no marker yet
    return r
  })

  on('session.compact', async ($, e, next) => {
    // headless sessions refuse $.session.compact(); a /compact prompt arrives here as 'manual'
    if (e.trigger !== 'plugin' && e.trigger !== 'manual') return next(e)
    const kept = e.messages.map(m => ({ role: m.role, text: m.text, toolUses: m.toolUses, toolResults: m.toolResults }))
    await rec($, { ev: 'compact.hook', before: e.messages.length, kept: kept.length, withHandle: e.messages.filter(m => m.handle).length })
    return { messages: kept }
  })

  on('turn.complete', async ($, e, next) => {
    const r = await next(e)
    if (done || (e as any).agentId) return r
    done = true
    await $.fs.write(`${OUT}/${sid}.done`, '1')
    try {
      const c: any = await $.session.compact()
      await rec($, { ev: 'compact.result', keys: Object.keys(c ?? {}), n: c?.messages?.length ?? null, before: c?.tokensBefore ?? null, after: c?.tokensAfter ?? null, skip: c?.skip ?? null })
    } catch (err) {
      await rec($, { ev: 'compact.error', error: String(err).slice(0, 300) })
    }
    return r
  })
}
