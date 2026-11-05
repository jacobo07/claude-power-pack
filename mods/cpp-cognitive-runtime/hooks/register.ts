import type { Register } from 'claude-code'
import {
  COMPAT, compatStatus, DEFAULT_MODES, RUNTIME_VERSION, advisoryBytes, decideSubagentAttachment, decideUnitAttachment, decideUnitSection,
  carryAdvice, decideUnitTool, gcKeptSet, imagesByUse, linkInstructionFiles, pageLines, parseWorkUnit, repoKey, rowFacts,
  PROJECT_BUDGET_CHARS, PROJECT_TOOLS, boundaryForecast, parseClassModel, projectToolOutput, stepAnomaly,
  KERNEL_CHARS, parseBreakevenModel, effectiveModes, parseReleaseId, policyGen, mainCanaryMode, decideMainLeanAttachment, pageBlocks, type BreakevenModel, type ClassModel, type ImageFact, type InstructionFileInfo, type Mode, type Modes, type WorkUnit,
} from './policy'
import { generationVerdict, parseActive, collapseDeferredNames, deferredNamesMode } from './policy'
// ICC W1: CCR_DEFERRED_NAMES ('0' off, 'enforce' applies, anything else/unset = shadow receipts only).
let deferredEnv: string | undefined
import { describeReceipt, textBytes, type DescribeSeen } from './policy'
import { decideArmBAttachment, decideSuccessorAttachment, frontierText, mdsSha, reachSummary, parseFrontierPointer, isFirstPromptCandidate, isKresumeSuccessor, shellFailed, successorMode, successorProjectMode } from './policy'
import { mainProjectMode, projectedFaultPath, safeToForget, type ForgetVerdict } from './policy'

// Tool description census (observe only): what tool.describe saw, and which tools a receipt already named.
const describeSeen: DescribeSeen = new Map()
const describeReported = new Set<string>()

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
// The open obligation of a main pane for Safe-to-Forget: the latest submitted prompt; null = none recorded (UNKNOWN).
let lastPrompt: string | null = null
// The resumed task's text; null = UNKNOWN until the capsule frontier reader lands (Phase 2). Never derived from the `/kresume` command.
let successorFrontier: string | null = null
// Benchmark arm B (CCR_A2_ARM=B): the pre-A2 successor behaviour, for the frozen A/B only.
let armB = false
// Generation awareness: the release id this process loaded, and the last (loaded>current) pair already receipted.
let loadedRelease: string | null = null
let lastGeneration: string | null = null
let skillListing = ''
let agentListing = ''
let mcpListing = ''
// Main-lean canary (v4 A7): set once at session start from CCR_MAIN_CANARY; 'off' until then, so stock text; default-on, CCR_MAIN_CANARY=0 opts out.
let canary: Mode = 'off'
// The canary session.start decided; /clear restores it (a successor under the main canary must not leave the pane 'off').
let launchCanary: Mode = 'off'
// Floor-diet canary on /kresume successors (Tranche A4): decided once, at the first main attachment, from the first prompt.
let successor = false
let successorDecision: Promise<void> | undefined
let sessionInteractive = false
let unitP: Promise<WorkUnit | null> | null = null
const agentTypes = new Map<string, string>()
// A subagent's prompt is its open obligation for Safe-to-Forget (bounded copy).
const agentPrompts = new Map<string, string>()
const receipts: Receipt[] = []
// Main-loop carry state for the epoch deopt advice: images that entered the transcript, the call count, the floor.
const hotImages = new Map<string, { tok: number; since: number; n: number }>()
let calls = 0
let floor = 0
let advised = false
// Cognitive PGO (v4 B6): the declared unit's Work-Class model, if tools/ccr_pgo.py built one; the last call's ctx.
let classModel: ClassModel | null = null
let beModel: BreakevenModel | null = null
let beLast: boolean | null = null
let prevCtx = 0
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
// Mode: modes.project, else enforce in a Work Unit session (as `unit`) and shadow elsewhere; a plain main pane is lifted to
// enforce (Phase 5, default-on since Amendment A; CCR_MAIN_PROJECT=0 switches the lift off). Outside a Work Unit every projection must pass Safe-to-Forget (durable full output
// read back, known obligation naming no omitted line, omitted proof lines hoisted); any refusal sends the whole output.
// A Work Unit keeps the B5 behaviour unchanged, so its measured receipts stay comparable.
const forgetFields = (f: ForgetVerdict) => ({ verdict: f.verdict, reason: f.reason, hoisted: f.hoisted, named: f.named })
const projectShell = async ($: any, e: any, next: any) => {
  const r: any = await next(e)
  const res = r?.result
  if (r?.deny !== undefined || !res || typeof res.stdout !== 'string' || res.isImage || res.backgroundTaskId || res.persistedOutputPath) return r
  const unit = await loadUnit($)
  let mainEnv: string | undefined
  // An env that cannot be read keeps today's mode: a failure must never turn the default-on lift on (Amendment A).
  try { mainEnv = await $.env.get('CCR_MAIN_PROJECT') } catch { mainEnv = '0' }
  const baseMode: Mode = successorProjectMode(effectiveModes(modes, compatible, !!unit).project, successor, canary, modes, !!unit)
  const mode: Mode = mainProjectMode(mainEnv, baseMode, !!unit, successor, modes, compatible, !!e.agentId)
  const lifted = mode !== baseMode // the receipt names a projection the main lift decided, never just the env value
  if (mode === 'off' || !stateDir || shellFailed(res)) return r
  const full = `${stateDir}/tool-results/${sid}/${e.tool_use_id ?? `t${Date.now()}`}.txt`
  const p = projectToolOutput(res.stdout, full, projectBudget)
  if (p.action === 'pass') return r
  const base = { ev: 'project', tool: e.tool, use: e.tool_use_id ?? null, agent: e.agentId ? agentTypes.get(e.agentId) ?? 'unknown' : null,
    kind: p.kind, bytes: p.bytes, lines: p.lines, out: p.out.length, budget: projectBudget, ...(successor ? { successor: true } : {}),
    ...(lifted ? { mainProject: true } : {}) }
  // The open obligation: a subagent's own prompt; a successor's frontier plus the latest prompt; else the latest prompt.
  const obligation = e.agentId ? agentPrompts.get(e.agentId) ?? null
    : successor ? ([successorFrontier, lastPrompt].filter(Boolean).join('\n') || null) : lastPrompt
  if (mode !== 'enforce') {
    receipt({ ...base, applied: false, ...(unit ? {} : { forget: forgetFields(safeToForget(res.stdout, p, obligation, true)), durable: null }) })
    return r
  }
  try { await $.fs.write(full, res.stdout) }
  catch (err) { receipt({ ...base, applied: false, error: String(err).slice(0, 200) }); return r } // full output not kept: send it whole
  if (unit) {
    receipt({ ...base, applied: true, path: full })
    return { result: { ...res, stdout: p.out }, ...(r.context ? { context: r.context } : {}) }
  }
  let back: string | null = null
  try { back = await $.fs.read(full) } catch { back = null } // unreadable right after the write: not durable
  const durable = back !== null && back.length === res.stdout.length && back === res.stdout
  const f = safeToForget(res.stdout, p, obligation, durable)
  if (f.verdict !== 'FORGET') { receipt({ ...base, applied: false, path: full, forget: forgetFields(f), durable }); return r }
  receipt({ ...base, applied: true, path: full, out: f.out.length, forget: forgetFields(f), durable })
  return { result: { ...res, stdout: f.out }, ...(r.context ? { context: r.context } : {}) }
}

// Page-fault counter for projected outputs: a Read or Grep of a tool-results/ file means the projection was not enough.
// Observe only: the tool runs unchanged.
const noteProjectedFault = async ($: any, e: any, next: any) => {
  const r: any = await next(e)
  const path = projectedFaultPath(stateDir, e.file_path ?? e.path ?? e.input?.file_path ?? e.input?.path)
  if (path) receipt({ ev: 'fault', kind: 'projected', tool: e.tool, path, agent: e.agentId ? agentTypes.get(e.agentId) ?? 'unknown' : null })
  return r
}

// One receipt per session says whether the first prompt marked a /kresume successor and what the canary did about it, so
// predicted-vs-realized can be audited on sessions that were NOT successors too. CCR_SUCCESSOR_CANARY=0 turns it off.
const decideSuccessor = async ($: any) => {
  if (effective('main') === 'off') return
  const unit = await loadUnit($)
  let kill: string | undefined
  try { kill = await $.env.get('CCR_SUCCESSOR_CANARY') } catch { kill = undefined } // no env access: canary stays as launched
  const mode: Mode = successorMode(canary, firstPrompt, kill, sessionInteractive, !!unit, modes, compatible)
  if (mode !== 'off') { canary = mode; successor = true }
  let gen: string | null = null
  try { gen = await policyGen(effectiveModes(modes, compatible, !!unit), kernel, canary) } catch { gen = null } // no digest: the receipt says so
  receipt({ ev: 'successor', marker: isKresumeSuccessor(firstPrompt), interactive: sessionInteractive, unit: !!unit, killed: kill === '0',
    mode, canary, policyGen: gen })
  if (successor) $.ui.status(`CCR ${RUNTIME_VERSION} successor canary:${mode}`)
  let arm: string | undefined
  try { arm = await $.env.get('CCR_A2_ARM') } catch { arm = undefined } // no env access: arm C (the default behaviour)
  armB = successor && arm === 'B'
  if (successor && !armB) await resolveFrontier($)
  if (armB) receipt({ ev: 'arm', arm: 'B' })
}

// The resumed task, from the capsule the predecessor sealed (rollover/latest/<repoKey>.json). Every failure leaves
// successorFrontier null = UNKNOWN, so the rule files stay; the receipt names which basis decided.
const resolveFrontier = async ($: any) => {
  let basis = 'unknown', capsule: string | null = null, sha: string | null = null
  try {
    let dir: string | undefined
    try { dir = await $.env.get('CPP_ROLLOVER_STATE_DIR') } catch { dir = undefined }
    if (!dir) {
      let home: string | undefined
      try { home = (await $.env.get('HOME')) ?? (await $.env.get('USERPROFILE')) } catch { home = undefined }
      if (home) dir = `${home.replace(/\\/g, '/')}/.claude/state/rollover`
    }
    if (!dir) basis = 'no-state-dir'
    else {
      const ptr = parseFrontierPointer(await $.fs.read(`${dir.replace(/\\/g, '/')}/latest/${rkey}.json`), Date.now())
      if (!ptr) basis = 'pointer-missing-or-stale'
      else {
        capsule = ptr.capsule; sha = ptr.sha256
        const bytes = await $.fs.read(ptr.capsule)
        const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(bytes))
        const got = [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, '0')).join('')
        const text = got === ptr.sha256 ? frontierText(bytes) : null
        if (got !== ptr.sha256) basis = 'hash-mismatch'
        else if (text === null) basis = 'capsule-empty'
        else { successorFrontier = text; basis = 'capsule' }
      }
    }
  } catch { basis = 'unreadable' } // no pointer / no read access: UNKNOWN
  receipt({ ev: 'frontier', frontier: { capsule, sha, basis }, bytes: successorFrontier?.length ?? 0 })
}

// One bounded read (<= ACTIVE_MAX_BYTES) of <ccr>/ACTIVE.json per prompt: a change of the (loaded>current) pair is one receipt,
// a stale pair also repaints the status line. Fails open: no file, no id, an unreadable file = no verdict.
async function noteGeneration($: { fs: { read(p: string): Promise<string> }; ui: { status(s: string): void } }): Promise<void> {
  if (!stateDir || !loadedRelease || stateDir.endsWith('/.state-dev')) return
  try {
    const v = generationVerdict(loadedRelease, parseActive(await $.fs.read(`${stateDir.replace(/\/state$/, '')}/ACTIVE.json`)))
    if (!v || v.key === lastGeneration) return
    lastGeneration = v.key
    receipt({ ev: 'generation', loaded: loadedRelease, current: v.current, stale: v.stale })
    if (v.status) $.ui.status(v.status)
  } catch { /* ACTIVE.json absent or unreadable: no verdict */ }
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
    try { kernel = (await $.fs.read(`${$.plugin.root}/kernel/HARD-RULES-DIGEST.md`)).slice(0, KERNEL_CHARS) }
    catch { kernel = null } // missing kernel: the linkers keep the full instructions
    const unit = await loadUnit($)
    // Version truth (v4 A1): the directory this process loaded and its release id, not ACTIVE.json (that is only
    // what is current now), plus the policy generation it runs and the effective mode of every surface.
    let releaseText: string | null = null
    try { releaseText = await $.fs.read(`${$.plugin.root}/RELEASE.json`) } catch { releaseText = null } // dev load: no release id
    const eff = effectiveModes(modes, compatible, !!unit)
    let canaryEnv: string | undefined
    try { canaryEnv = await $.env.get('CCR_MAIN_CANARY') } catch { canaryEnv = '0' } // no env access: fail closed, no canary
    canary = mainCanaryMode(canaryEnv, e.isInteractive === true, !!unit, modes, compatible)
    try { deferredEnv = await $.env.get('CCR_DEFERRED_NAMES') } catch { deferredEnv = '0' } // no env access: fail closed
    launchCanary = canary
    sessionInteractive = e.isInteractive === true
    let gen: string | null = null
    try { gen = await policyGen(eff, kernel, canary) } catch { gen = null } // no digest available: the receipt says so
    receipt({ ev: 'start', runtime: RUNTIME_VERSION, version, compatible, modes, repoKey: rkey, interactive: e.isInteractive, kernel: kernel?.length ?? 0, unit: unit?.cls ?? null,
      release: root, releaseId: loadedRelease = parseReleaseId(releaseText), policyGen: gen, effective: eff, workClass: unit?.cls ?? null, canary })
    // Semantic Cost Contract (v4 B4) for a declared unit: obligation, class, forecast. No model -> ADMIT_UNFORECAST:
    // the cost is unknown, and the receipt says so instead of reporting a number nobody measured.
    if (unit) {
      let text: string | null = null
      try { text = await $.fs.read(`${stateDir}/pgo/${unit.cls}.json`) } catch { text = null } // no model built for this class yet
      classModel = parseClassModel(text, unit.cls)
      let beText: string | null = null
      try { beText = await $.fs.read(`${stateDir}/pgo/${unit.cls}.breakeven.json`) } catch { beText = null } // no break-even model for this class yet
      beModel = parseBreakevenModel(beText, unit.cls)
      const fc = classModel ? boundaryForecast(classModel) : null
      receipt({ ev: 'contract', cls: unit.cls, obligation: unit.id, model_n: classModel?.n ?? 0, forecast: fc,
        step_p95: classModel?.step.p95 ?? null, verdict: classModel ? 'ADMIT' : 'ADMIT_UNFORECAST' })
    }
    // Host build outside COMPAT: every enforce is downgraded to shadow. Say so on the status line and in one receipt.
    const cs = compatStatus(version, compatible, modes)
    if (cs.shadowed) receipt({ ev: 'compat', verdict: 'SHADOW', version, compat: COMPAT, status: cs.status })
    $.ui.status(cs.status ?? (modes.main === 'off' ? 'CCR off'
      : `CCR ${RUNTIME_VERSION} sub:${effective('subagent')} main:${effective('main')}${unit ? ` unit:${unit.cls}:${effective('unit')}` : ''}${canary !== 'off' ? ` canary:${canary}` : ''}`))
    await $.tool.register({
      name: 'page',
      description: 'CPP Cognitive Runtime page fault: fetch context the runtime did not preload. kind "skills" or "agents" returns listing lines matching query; kind "mcp" returns the instructions of the MCP servers whose name matches query; kind "file" returns an instruction file by absolute path.',
      inputSchema: {
        type: 'object',
        properties: { kind: { type: 'string', enum: ['skills', 'agents', 'mcp', 'file'] }, query: { type: 'string' }, path: { type: 'string' } },
        required: ['kind'],
      },
    })
    await flush($)
    return r
  })

  on('prompt.submit', async ($, e, next) => {
    if (!firstPrompt && isFirstPromptCandidate(e.text)) firstPrompt = e.text.slice(0, 4000)
    if (typeof e.text === 'string') lastPrompt = e.text.trim() ? e.text.slice(0, 4000) : null // blank = unknown (review M1)
    await noteGeneration($)
    return next(e)
  })

  on('prompt.context', async ($, e, next) => {
    const r = await next(e)
    files = e.instructionFiles ? e.instructionFiles.map(f => ({ path: f.path, kind: f.kind, content: f.content })) : null
    if (files && !successor && effective('main') !== 'off' && !(await loadUnit($))) { // a successor links through its own frontier path
      for (const d of linkInstructionFiles(files, firstPrompt)) {
        receipt({ ev: 'link', agent: null, surface: 'instruction-file', path: d.path, bytes: d.bytes, keep: d.keep, reason: d.reason, mode: effective('main') })
      }
    }
    return r
  })

  // Tool Linker (work units only): every tool outside the class closure moves behind ToolSearch.
  on('tool.describe', async ($, e, next) => {
    const r: any = await next(e)
    if (effective('main') !== 'off' && !(e as any).agentId) {
      describeSeen.set(e.tool, { bytes: textBytes(r?.description), deferred: typeof r?.isDeferred === 'boolean' ? r.isDeferred : null,
        provider: typeof (e as any).provider === 'string' ? (e as any).provider : null })
    }
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
    if (r.agentId) { agentTypes.set(r.agentId, e.subagentType); if (typeof e.prompt === 'string') agentPrompts.set(r.agentId, e.prompt.slice(0, 4000)) }
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
    // Deltas add to what came before: the page fault answers from every delta of the session, not only the last one.
    if (!agentId && a.type === 'agent_listing_delta') agentListing = agentListing ? `${agentListing}\n${text}` : text
    if (!agentId && a.type === 'mcp_instructions_delta') mcpListing = mcpListing ? `${mcpListing}\n${text}` : text
    // Attachments arrive concurrently: every main one awaits the same decision, or the early ones pass before the mode is known.
    if (!agentId) { successorDecision ??= decideSuccessor($); await successorDecision }

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

    // Interactive or undeclared main session: shadow receipts only, unless the launch opted into the main-lean canary.
    if (effective('main') === 'off') return r
    if (a.type === 'deferred_tools_delta') {
      const dn = deferredNamesMode(deferredEnv, canary)
      const col = dn === 'off' ? null : collapseDeferredNames(text)
      if (col !== null) {
        const applied = dn === 'enforce'
        receipt({ ev: 'attach', agent: null, canary, type: a.type, origin: a.origin?.kind, bytes: text.length, out: applied ? col.length : text.length,
          lean: col.length, action: 'replace', applied, reason: 'deferred-names' })
        return applied ? { text: col } : r
      }
    }
    if (canary !== 'off') {
      const d: any = armB ? decideArmBAttachment(a.type, text, files, firstPrompt) : successor ? decideSuccessorAttachment(a.type, text, files, successorFrontier) : decideMainLeanAttachment(a.type, text)
      if (d.action !== 'keep') {
        const applied = canary === 'enforce'
        const out = d.text ?? text
        receipt({ ev: 'attach', agent: null, canary, type: a.type, origin: a.origin?.kind, hookEvent: a.origin?.event ?? null, bytes: text.length,
          out: applied ? out.length : text.length, lean: out.length, action: d.action, applied, reason: d.reason,
          ...(successor ? { successor: true, withheld: d.withheld ?? [] } : {}),
          ...(d.reach ? { reach: reachSummary(d.reach), reachEntries: d.reach, mds: await mdsSha() } : {}) })
        return applied ? { text: out } : r
      }
    }
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
    const a = carryAdvice(floor, ctx, imageTok, beModel ? { model: beModel, call: calls } : null)
    const step = prevCtx > 0 ? ctx - prevCtx : 0
    prevCtx = ctx
    receipt({ ev: 'call', agent: null, call: calls, msgs: e.messageCount, ctx, step, out: u.output_tokens ?? 0, carry: a.carry, imageTok, rotate: a.rotate })
    const dr = describeReceipt(describeSeen, describeReported) // observe only: names the tool descriptions in the prefix
    if (dr) receipt({ ...dr, call: calls })
    // Weighted break-even (v4 A4), observe only: a receipt at the first call and whenever the verdict flips; the
    // driver that owns the epoch decides, this hook never rotates.
    if (a.rotateAdvice && a.rotateAdvice.rotate !== beLast) {
      beLast = a.rotateAdvice.rotate
      receipt({ ev: 'rotate_advice', call: calls, ctx, floor, ...a.rotateAdvice, rule: 'breakeven', ratioRule: a.rotate, applied: false })
    }
    // Intra-epoch governor (v4 B6): a step above the class P95 is named at the call that pays for it first, with the
    // cost it will carry if it rides to the class's P80 length. Advice only: the driver that owns the epoch decides.
    if (classModel && step > 0) {
      const s = stepAnomaly(step, calls, classModel)
      if (s.anomaly) {
        receipt({ ev: 'anomaly', call: calls, step, p95: classModel.step.p95, ratio: s.ratio, ridesLeft: s.ridesLeft, costIfRides: s.costIfRides })
        if (stateDir) {
          try { await $.fs.write(`${stateDir}/advice/${sid}.anomaly.json`, JSON.stringify({ ts: Date.now(), sid, call: calls, step, ...s, verdict: 'INCIDENT' }, null, 1)) }
          catch (err) { receipt({ ev: 'advice.error', error: String(err).slice(0, 200) }) }
        }
      }
    }
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
    // /clear ends the session but keeps this process, and no session.start follows (receipts ff2c1af0, 2026-10-24): the next
    // conversation decides its own first prompt and successor. Restore the launch canary: under the default-on main canary a
    // successor keeps 'enforce', and forcing 'off' here would drop the main canary for the rest of the pane.
    if (successor) { successor = false; canary = launchCanary }
    firstPrompt = ''
    lastPrompt = null
    agentPrompts.clear()
    successorFrontier = null
    armB = false
    successorDecision = undefined
    skillListing = agentListing = mcpListing = ''
    files = null
    return r
  })

  // Tool Output Projection (v4 B5); the hook is projectShell above. It runs the tool through next(e), so the handler
  // fails open by replay: next(e) after a throw resolves to what the call settled to, and the command never runs twice.
  on('tool.call', { tool: 'Bash' }, projectShell).catch(($, e, next) => next(e))
  on('tool.call', { tool: 'PowerShell' }, projectShell).catch(($, e, next) => next(e))
  // Projected-output page faults (Phase 5), observe only; same fail-open-by-replay shape.
  on('tool.call', { tool: 'Read' }, noteProjectedFault).catch(($, e, next) => next(e))
  on('tool.call', { tool: 'Grep' }, noteProjectedFault).catch(($, e, next) => next(e))

  // Context page faults: what a linker withheld stays one call away, and every call is a receipt.
  on('tool.call', { tool: 'mcp__cpp-cognitive-runtime__page' }, async ($, e) => {
    const a = e as any
    let result: string
    if (a.kind === 'skills') result = pageLines(skillListing, a.query ?? '')
    else if (a.kind === 'agents') result = pageLines(agentListing, a.query ?? '')
    else if (a.kind === 'mcp') result = pageBlocks(mcpListing, a.query ?? '')
    else {
      const f = files?.find(x => x.path.toLowerCase() === String(a.path ?? '').toLowerCase())
      result = f ? f.content : `(not an instruction file of this session: ${a.path ?? ''})`
    }
    receipt({ ev: 'fault', kind: a.kind, query: a.kind === 'file' ? null : (a.query ?? ''), path: a.kind === 'file' ? a.path ?? null : null, bytes: result.length, agent: a.agentId ? agentTypes.get(a.agentId) ?? 'unknown' : null })
    return { result }
  })
}
