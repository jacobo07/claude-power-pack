import type { Register } from 'claude-code'
import {
  COMPAT, DEFAULT_MODES, RUNTIME_VERSION, advisoryBytes, decideSubagentAttachment, decideUnitAttachment, decideUnitSection,
  carryAdvice, decideUnitTool, gcKeptSet, imagesByUse, linkInstructionFiles, pageLines, parseWorkUnit, repoKey, rowFacts,
  PROJECT_BUDGET_CHARS, PROJECT_TOOLS, projectToolOutput,
  type ImageFact, type InstructionFileInfo, type Mode, type Modes, type WorkUnit,
} from './policy'

// CPP Cognitive Runtime (CCR). Every optimisation hook here fails OPEN: a hook that throws or
// overruns is skipped by the engine and the stock context is sent. No hook here guards a tool,
// so none needs a refusing .catch; security stays with the settings hooks, which this never touches.

type Receipt = Record<string, unknown>

let stateDir = ''
let sid = 'unknown'
let rkey = 'no-repo'
let modes: Modes = { ...DEFAULT_MODES }
let projectBudget = PROJECT_BUDGET_CHARS
let compatible = false
let kernel: string | null = null
let files: InstructionFileInfo[] | null = null
let firstPrompt = ''
let skillListing = ''
let agentListing = ''
let unitP: Promise<WorkUnit | null> | null = null
const agentTypes = new Map<string, string>()
const receipts: Receipt[] = []
// Main-loop carry state for the epoch deopt advice: images that entered the transcript, the call count, the floor.
const hotImages = new Map<string, { tok: number; since: number; n: number }>()
let calls = 0
let floor = 0
let advised = false
// Image results of the main loop by tool_use_id: what a pixel GC compaction can evict and name.
const imageUses = new Map<string, ImageFact[]>()

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

// Tool Output Projection (v4 B5): a shell result over the budget reaches the model as a projection plus the path
// of the full output. Fails open: anything unexpected, or a failed write of the full output, sends the stock result.
// Mode: modes.project, else enforce in a Work Unit session (as `unit`) and shadow elsewhere.
const projectShell = async ($: any, e: any, next: any) => {
  const r: any = await next(e)
  const res = r?.result
  if (r?.deny !== undefined || !res || typeof res.stdout !== 'string' || res.isImage || res.backgroundTaskId || res.persistedOutputPath) return r
  const unit = await loadUnit($)
  const asked: Mode = modes.project ?? (unit ? modes.unit : 'shadow')
  const mode: Mode = modes.main === 'off' || asked === 'off' ? 'off' : compatible ? asked : 'shadow'
  if (mode === 'off' || !stateDir) return r
  const full = `${stateDir}/tool-results/${sid}/${e.tool_use_id ?? `t${Date.now()}`}.txt`
  const p = projectToolOutput(res.stdout, full, projectBudget)
  if (p.action === 'pass') return r
  const base = { ev: 'project', tool: e.tool, use: e.tool_use_id ?? null, agent: e.agentId ? agentTypes.get(e.agentId) ?? 'unknown' : null,
    kind: p.kind, bytes: p.bytes, lines: p.lines, out: p.out.length, budget: projectBudget }
  if (mode !== 'enforce') { receipt({ ...base, applied: false }); return r }
  try { await $.fs.write(full, res.stdout) }
  catch (err) { receipt({ ...base, applied: false, error: String(err).slice(0, 200) }); return r } // full output not kept: send it whole
  receipt({ ...base, applied: true, path: full })
  return { result: { ...res, stdout: p.out }, ...(r.context ? { context: r.context } : {}) }
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
      try {
        const o = JSON.parse(await $.fs.read(`${stateDir}/modes.json`))
        modes = { ...DEFAULT_MODES, ...o }
        if (Number.isFinite(o.projectBudget) && o.projectBudget >= 1000) projectBudget = o.projectBudget
      }
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

  // Materialization receipt for the system prompt (observe only): the first render's sections and sizes.
  // Measured 2026-10-12: on a lean-trait render it holds no per-tool guidance, so narrowing `tools` here cuts nothing.
  let composeSeen = false
  on('prompt.compose', async ($, e, next) => {
    const r = await next(e)
    if (!composeSeen && effective('main') !== 'off') {
      composeSeen = true
      receipt({ ev: 'compose', traits: e.traits, offered: e.tools.length,
        sections: r.sections.map(s => ({ id: s.id, scope: s.scope, bytes: s.text.length })) })
    }
    return r
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

  // Carry receipt (UMVM M1, observe only): every row that will ride later calls, by door and modality.
  // Images are receipted by content hash so a re-read of the same bytes under another path is visible.
  on('session.append', async ($, e, next) => {
    const r = await next(e)
    if (effective('main') === 'off') return r
    const m = (r as any).message ?? e.message
    if (!m?.role) return r // a notice or a record with no bytes on the wire carries nothing
    try {
      const f = rowFacts(m.content ?? [])
      // a re-read of the same bytes appends another block, so a repeat adds its cost again (n counts repeats)
      if (!e.agentId) for (const i of f.images) {
        const v = hotImages.get(i.hash)
        if (v) { v.tok += i.tok ?? 0; v.n++ } else hotImages.set(i.hash, { tok: i.tok ?? 0, since: calls, n: 1 })
      }
      if (!e.agentId && f.images.length) for (const [use, imgs] of imagesByUse(m.content ?? [])) imageUses.set(use, imgs)
      receipt({ ev: 'row', agent: e.agentId ? agentTypes.get(e.agentId) ?? 'unknown' : null, door: e.door, role: m.role,
        origin: (e.origin as any)?.kind ?? null, tool: (e.origin as any)?.tool ?? null, name: m.name ?? null, text: f.text, thinking: f.thinking, sealed: f.sealed, images: f.images })
    } catch (err) {
      receipt({ ev: 'row.error', door: e.door, error: String(err).slice(0, 200) }) // the row is already stored; only the receipt is lost
    }
    return r
  })

  // Pixel GC (UMVM arm D), opt-in per launch: CCR_PIXEL_GC=0. A headless session refuses $.session.compact(), so
  // the driver sends a `/compact` turn; this hook answers it with no summarizer call. Every message is rebuilt:
  // on 2.1.296 a kept-set mixing handled and rebuilt messages was installed as a no-op (sid 074e2398, the next
  // call read the old prefix byte for byte), so a value above 0 is receipted and run as 0.
  // Unset, unreadable, or nothing to evict: the stock compaction runs (or the turn is skipped with a reason).
  on('session.compact', async ($, e, next) => {
    if (e.agentId || effective('main') === 'off' || (e.trigger !== 'manual' && e.trigger !== 'plugin')) return next(e)
    let raw: string | undefined
    try { raw = await $.env.get('CCR_PIXEL_GC') } catch { raw = undefined } // no env access: GC off
    const asked = raw === undefined ? Number.NaN : Number.parseInt(raw, 10)
    if (!(asked >= 0)) return next(e) // unset or not a count: stock compaction
    if (asked > 0) receipt({ ev: 'gc.window-unsupported', asked })
    const keep = 0
    // A /compact turn of a headless driver is a fresh process (--resume), so the append-time map is empty there:
    // the images are read back from the transcript's API form, which still carries the blocks.
    const images = new Map(imageUses)
    try {
      const api: any[] = await $.session.messages({ as: 'api' })
      for (const [use, imgs] of imagesByUse(api.flatMap(m => (Array.isArray(m.content) ? m.content : [])))) images.set(use, imgs)
    } catch (err) {
      receipt({ ev: 'gc.error', error: String(err).slice(0, 200) }) // only the append-time map is used
    }
    const plan = gcKeptSet(e.messages as any, images, keep)
    receipt({ ev: 'gc', trigger: e.trigger, before: e.messages.length, keptWhole: plan.keptWhole,
      evicted: plan.evicted.map(i => ({ hash: i.hash, tok: i.tok })), applied: !!plan.messages })
    await flush($)
    if (!plan.messages) return { skip: 'CCR pixel GC: no image outside the live window' }
    for (const i of plan.evicted) {
      const v = hotImages.get(i.hash)
      if (v) { v.tok -= i.tok ?? 0; if (--v.n <= 0) hotImages.delete(i.hash) }
    }
    return { messages: plan.messages as any }
  })

  // Per-call carry receipt and epoch deopt advice (observe only). The advice file is for the driver that owns
  // the epoch; this hook never rotates, compacts or drops anything.
  on('turn.step', async function* ($, e, next) {
    const r: any = yield* next(e) // chunks pass through untouched; only the result is read
    if (effective('main') === 'off' || !r?.usage) return r
    const u = r.usage
    const ctx = (u.input_tokens ?? 0) + (u.cache_creation_input_tokens ?? 0) + (u.cache_read_input_tokens ?? 0)
    if (e.agentId) {
      receipt({ ev: 'call', agent: agentTypes.get(e.agentId) ?? 'unknown', index: e.index, msgs: e.messageCount, ctx, out: u.output_tokens ?? 0 })
      return r
    }
    calls++
    if (floor === 0) floor = ctx
    let imageTok = 0
    for (const v of hotImages.values()) imageTok += v.tok
    const a = carryAdvice(floor, ctx, imageTok)
    receipt({ ev: 'call', agent: null, call: calls, msgs: e.messageCount, ctx, out: u.output_tokens ?? 0, carry: a.carry, imageTok, rotate: a.rotate })
    if (a.rotate && !advised && stateDir) {
      advised = true
      const images = [...hotImages.entries()].map(([hash, v]) => ({ hash, tok: v.tok, n: v.n, rides: calls - v.since }))
      try { await $.fs.write(`${stateDir}/advice/${sid}.json`, JSON.stringify({ ts: Date.now(), sid, call: calls, ...a, images }, null, 1)) }
      catch (err) { receipt({ ev: 'advice.error', error: String(err).slice(0, 200) }) }
    }
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

  // Tool Output Projection (v4 B5); the hook is projectShell above. It runs the tool through next(e), so the handler
  // fails open by replay: next(e) after a throw resolves to what the call settled to, and the command never runs twice.
  on('tool.call', { tool: 'Bash' }, projectShell).catch(($, e, next) => next(e))
  on('tool.call', { tool: 'PowerShell' }, projectShell).catch(($, e, next) => next(e))

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
