import type { Register } from 'claude-code'
import {
  COMPAT, DEFAULT_MODES, RUNTIME_VERSION, advisoryBytes, decideSubagentAttachment, decideUnitAttachment, decideUnitSection,
  decideUnitTool, linkInstructionFiles, pageLines, parseWorkUnit, repoKey, type InstructionFileInfo, type Modes, type WorkUnit,
} from './policy'

// CPP Cognitive Runtime (CCR). Every optimisation hook here fails OPEN: a hook that throws or
// overruns is skipped by the engine and the stock context is sent. No hook here guards a tool,
// so none needs a refusing .catch; security stays with the settings hooks, which this never touches.

type Receipt = Record<string, unknown>

let stateDir = ''
let sid = 'unknown'
let rkey = 'no-repo'
let modes: Modes = { ...DEFAULT_MODES }
let compatible = false
let kernel: string | null = null
let files: InstructionFileInfo[] | null = null
let firstPrompt = ''
let skillListing = ''
let agentListing = ''
let unitP: Promise<WorkUnit | null> | null = null
const agentTypes = new Map<string, string>()
const receipts: Receipt[] = []

const receipt = (r: Receipt) => { receipts.push({ ts: Date.now(), sid, ...r }) }

const flush = async ($: any) => {
  if (!stateDir || receipts.length === 0) return
  const path = `${stateDir}/receipts/${rkey}/${sid}.jsonl`
  let prior = ''
  try { prior = await $.fs.read(path) } catch { prior = '' } // first flush of the session: no file yet
  const batch = receipts.splice(0).map(r => JSON.stringify(r)).join('\n') + '\n'
  await $.fs.write(path, prior + batch)
}

const effective = (m: keyof Modes) => (compatible ? modes[m] : modes[m] === 'off' ? 'off' : 'shadow')

// The Work Unit a launcher declared for this main session, read once whichever hook asks first (tool
// descriptions can be computed before session.start resolves). No variable, an unreadable file or an
// unknown class all mean "no unit": the session keeps the main tier's behaviour.
const loadUnit = ($: any): Promise<WorkUnit | null> => {
  if (!unitP) {
    unitP = (async () => {
      let path: string | undefined
      try { path = await $.env.get('CCR_WORK_UNIT') } catch { path = undefined } // no env access: no unit
      if (!path) return null
      let text: string | null = null
      try { text = await $.fs.read(path) } catch { text = null } // missing declaration file: no unit
      const u = parseWorkUnit(text)
      receipt({ ev: 'unit', declared: path, cls: u?.cls ?? null, id: u?.id ?? null, accepted: !!u })
      return u
    })()
  }
  return unitP
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const r = await next(e)
    const root = $.plugin.root.replace(/\\/g, '/')
    // The active release lives at <home>/.claude/ccr/active (tools/ccr_release.py); its state sits
    // beside it. A development load (--plugin-dir on the repo) keeps its state inside the mod, gitignored.
    stateDir = /\/ccr\/active$/.test(root) ? root.replace(/\/active$/, '/state') : `${root}/.state-dev`
    sid = await $.session.id()
    const repo = await $.session.repo()
    rkey = repoKey(repo?.root ?? null)
    const version = (await $.session.version()).version
    compatible = COMPAT.includes(version)
    if (await $.fs.exists(`${stateDir}/OFF`)) modes = { subagent: 'off', main: 'off', unit: 'off' }
    else {
      try { modes = { ...DEFAULT_MODES, ...JSON.parse(await $.fs.read(`${stateDir}/modes.json`)) } }
      catch { modes = { ...DEFAULT_MODES } } // no override file: release defaults
    }
    try { kernel = (await $.fs.read(`${$.plugin.root}/kernel/HARD-RULES-DIGEST.md`)).slice(0, 8000) }
    catch { kernel = null } // missing kernel: the linkers keep the full instructions
    const unit = await loadUnit($)
    receipt({ ev: 'start', runtime: RUNTIME_VERSION, version, compatible, modes, repoKey: rkey, interactive: e.isInteractive, kernel: kernel?.length ?? 0, unit: unit?.cls ?? null })
    $.ui.status(modes.main === 'off' ? 'CCR off'
      : `CCR ${RUNTIME_VERSION} sub:${effective('subagent')} main:${effective('main')}${unit ? ` unit:${unit.cls}:${effective('unit')}` : ''}`)
    await $.tool.register({
      name: 'page',
      description: 'CPP Cognitive Runtime page fault: fetch context the runtime did not preload. kind "skills" or "agents" returns listing lines matching query; kind "file" returns an instruction file by absolute path.',
      inputSchema: {
        type: 'object',
        properties: { kind: { type: 'string', enum: ['skills', 'agents', 'file'] }, query: { type: 'string' }, path: { type: 'string' } },
        required: ['kind'],
      },
    })
    await flush($)
    return r
  })

  on('prompt.submit', async ($, e, next) => {
    if (!firstPrompt) firstPrompt = e.text.slice(0, 4000)
    return next(e)
  })

  on('prompt.context', async ($, e, next) => {
    const r = await next(e)
    files = e.instructionFiles ? e.instructionFiles.map(f => ({ path: f.path, kind: f.kind, content: f.content })) : null
    if (files && effective('main') !== 'off' && !(await loadUnit($))) {
      for (const d of linkInstructionFiles(files, firstPrompt)) {
        receipt({ ev: 'link', agent: null, surface: 'instruction-file', path: d.path, bytes: d.bytes, keep: d.keep, reason: d.reason, mode: effective('main') })
      }
    }
    return r
  })

  // Tool Linker (work units only): every tool outside the class closure moves behind ToolSearch.
  on('tool.describe', async ($, e, next) => {
    const r: any = await next(e)
    const unit = await loadUnit($)
    const mode = effective('unit')
    if (!unit || mode === 'off' || r.isDeferred || decideUnitTool(e.tool, unit) === 'keep') return r
    const applied = mode === 'enforce'
    receipt({ ev: 'link', agent: null, surface: 'tool', tool: e.tool, bytes: r.description?.length ?? 0, keep: false, reason: 'deferred-outside-unit', applied })
    return applied ? { ...r, isDeferred: true } : r
  })

  // Memory Linker (work units only): the auto-memory section is left out; its files stay on disk.
  on('prompt.section', async ($, e, next) => {
    const r = await next(e)
    if (r.text === null) return r
    const unit = await loadUnit($)
    const mode = effective('unit')
    if (!unit || mode === 'off') return r
    const d = decideUnitSection(e.name)
    if (d.action === 'keep') return r
    const applied = mode === 'enforce'
    receipt({ ev: 'link', agent: null, surface: 'section', name: e.name, bytes: r.text.length, keep: false, reason: d.reason, applied })
    return applied ? { text: null } : r
  })

  on('agent.spawn', async ($, e, next) => {
    const r: any = await next(e)
    if (r.agentId) agentTypes.set(r.agentId, e.subagentType)
    receipt({ ev: 'spawn', agentId: r.agentId ?? null, agentType: e.subagentType, prompt: e.prompt.length, model: r.model ?? null })
    return r
  })

  on('prompt.attachment', async ($, e, next) => {
    const a = e as any
    const agentId: string | undefined = typeof a.agentId === 'string' ? a.agentId : undefined
    const r = await next(e)
    const text = r.text
    if (text === null) return r
    if (!agentId && a.type === 'skill_listing') skillListing = text
    if (!agentId && a.type === 'agent_listing_delta') agentListing = text

    if (agentId) {
      const mode = effective('subagent')
      if (mode === 'off') return r
      const agentType = agentTypes.get(agentId)
      const d = decideSubagentAttachment(a.type, agentType, kernel, files)
      const out = d.action === 'keep' ? text : d.action === 'drop' ? null : d.text ?? text
      const applied = mode === 'enforce' && d.action !== 'keep'
      receipt({ ev: 'attach', agent: agentType ?? 'unknown', type: a.type, origin: a.origin?.kind, bytes: text.length, out: applied ? (out?.length ?? 0) : text.length, action: d.action, applied, reason: d.reason })
      return applied ? { text: out } : r
    }

    // Main session that declared a Work Unit: the unit's closure is enforced.
    const unit = await loadUnit($)
    if (unit && effective('unit') !== 'off') {
      const d = decideUnitAttachment(a.type, kernel, files)
      const out = d.action === 'keep' ? text : d.action === 'drop' ? null : d.text ?? text
      const applied = effective('unit') === 'enforce' && d.action !== 'keep'
      receipt({ ev: 'attach', agent: null, unit: unit.cls, type: a.type, origin: a.origin?.kind, bytes: text.length, out: applied ? (out?.length ?? 0) : text.length, action: d.action, applied, reason: d.reason })
      return applied ? { text: out } : r
    }

    // Interactive or undeclared main session: shadow receipts only in this release.
    if (effective('main') === 'off') return r
    const adv = a.origin?.kind === 'hook' ? advisoryBytes(text) : 0
    receipt({ ev: 'attach', agent: null, type: a.type, origin: a.origin?.kind, hookEvent: a.origin?.event ?? null, bytes: text.length, advisory: adv, applied: false })
    return r
  })

  on('turn.complete', async ($, e, next) => {
    const r = await next(e)
    const a = e as any
    receipt({ ev: 'usage', agent: a.agentId ? agentTypes.get(a.agentId) ?? 'unknown' : null, usage: a.usage ?? null })
    await flush($)
    return r
  })

  on('session.end', async ($, e, next) => {
    const r = await next(e)
    receipt({ ev: 'end' })
    await flush($)
    return r
  })

  // Context page faults: what a linker withheld stays one call away, and every call is a receipt.
  on('tool.call', { tool: 'mcp__cpp-cognitive-runtime__page' }, async ($, e) => {
    const a = e as any
    let result: string
    if (a.kind === 'skills') result = pageLines(skillListing, a.query ?? '')
    else if (a.kind === 'agents') result = pageLines(agentListing, a.query ?? '')
    else {
      const f = files?.find(x => x.path.toLowerCase() === String(a.path ?? '').toLowerCase())
      result = f ? f.content : `(not an instruction file of this session: ${a.path ?? ''})`
    }
    receipt({ ev: 'fault', kind: a.kind, query: a.kind === 'file' ? null : (a.query ?? ''), path: a.kind === 'file' ? a.path ?? null : null, bytes: result.length, agent: a.agentId ? agentTypes.get(a.agentId) ?? 'unknown' : null })
    return { result }
  })
}
