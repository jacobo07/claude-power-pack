// CCR policy: pure, deterministic decisions. No engine calls here, so every rule is unit-testable
// and the hook layer stays a thin adapter.

export const RUNTIME_VERSION = '0.1.0'

// Claude Code builds whose hook semantics this release was measured against (plan section M1).
// Any other build runs observe-only: receipts, no enforcement.
export const COMPAT = ['2.1.296', '2.1.302', '2.1.310', '2.1.311', '2.1.312', '2.1.314', '2.1.316', '2.1.318']

export type Mode = 'enforce' | 'shadow' | 'off'
// main: interactive and undeclared sessions. unit: main sessions that declared a Work Unit.
// project: Tool Output Projection; unset means enforce in Work Unit sessions and shadow elsewhere.
export type Modes = { subagent: Mode; main: Mode; unit: Mode; project?: Mode }
export const DEFAULT_MODES: Modes = { subagent: 'enforce', main: 'shadow', unit: 'enforce' }

// The mode each surface actually runs at. A build outside COMPAT downgrades enforce to shadow; `off` stays off.
// project: modes.project, else `unit` in a Work Unit session and shadow elsewhere; off whenever main is off.
export type Surface = 'main' | 'subagent' | 'unit' | 'project'
export function effectiveModes(modes: Modes, compatible: boolean, hasUnit: boolean): Record<Surface, Mode> {
  const eff = (m: Mode): Mode => (compatible ? m : m === 'off' ? 'off' : 'shadow')
  const asked: Mode = modes.project ?? (hasUnit ? modes.unit : 'shadow')
  return { main: eff(modes.main), subagent: eff(modes.subagent), unit: eff(modes.unit),
    project: modes.main === 'off' || asked === 'off' ? 'off' : eff(asked) }
}

// A host build outside COMPAT silently downgrades every enforce to shadow (CLASS 0, recurred on every host auto-update).
// This is the loud half: the status line that names the build, and whether a receipt must say so. Null status = nothing
// was downgraded (covered build, or every surface is off so there was nothing to downgrade).
export function compatStatus(version: string, compatible: boolean, modes: Modes): { status: string | null; shadowed: boolean } {
  const wanted = [modes.main, modes.subagent, modes.unit, modes.project ?? 'shadow'].some(m => m === 'enforce')
  if (compatible || !wanted) return { status: null, shadowed: false }
  return { status: `CCR SHADOW: host ${version || 'unknown'} not in COMPAT`, shadowed: true }
}

// Tool description census (observe only): the ~66K first-call tokens no receipt attributed include every tool's
// description. `bytes` is the UTF-8 length of the description the host gave `tool.describe`, or null when it gave none
// (unmeasured, never 0). Input schemas are not on this surface, so they stay unattributed.
export type DescribeSeen = Map<string, { bytes: number | null; deferred: boolean | null; provider: string | null }>
export type DescribeReceipt = {
  ev: 'tools'; late: boolean; n: number; bytes: number; deferredBytes: number; unmeasured: number
  tools: { t: string; b: number | null; d: boolean | null; p: string | null }[]
}

export function textBytes(s: unknown): number | null {
  return typeof s === 'string' ? new TextEncoder().encode(s).length : null
}

// One receipt for the tools not reported yet. The first one is the session's census; a later one (`late`) is a tool that
// appeared after it, e.g. an MCP server that connected mid-session. Null when nothing is new.
export function describeReceipt(seen: DescribeSeen, reported: Set<string>): DescribeReceipt | null {
  const fresh = [...seen].filter(([name]) => !reported.has(name))
  if (fresh.length === 0) return null
  const late = reported.size > 0
  for (const [name] of fresh) reported.add(name)
  return {
    ev: 'tools', late, n: fresh.length,
    bytes: fresh.reduce((s, [, v]) => s + (v.bytes ?? 0), 0),
    deferredBytes: fresh.reduce((s, [, v]) => s + (v.deferred ? v.bytes ?? 0 : 0), 0),
    unmeasured: fresh.filter(([, v]) => v.bytes === null).length,
    tools: fresh.map(([name, v]) => ({ t: name, b: v.bytes, d: v.deferred, p: v.provider })),
  }
}

// Policy generation (A1 version truth): a short sha256 of the effective modes and the kernel text this process read.
// Two sessions with the same policyGen made the same decisions from the same inputs, whatever release they came from.
// The main-lean canary (v4 A7) moves the generation only when it runs, so every pre-A7 session keeps its id.
export async function policyGen(eff: Record<Surface, Mode>, kernel: string | null, canary: Mode = 'off'): Promise<string> {
  const surfaces = [eff.main, eff.subagent, eff.unit, eff.project, ...(canary === 'off' ? [] : [`canary:${canary}`])]
  const text = JSON.stringify(surfaces) + '\n' + (kernel ?? '')
  const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))
  return [...new Uint8Array(d)].slice(0, 6).map(b => b.toString(16).padStart(2, '0')).join('')
}

// The release id of the directory this process loaded: RELEASE.json, which tools/ccr_release.py writes into every
// release it builds. A development load (--plugin-dir on the repo) or an unreadable file has no id: null, never a guess.
export function parseReleaseId(text: string | null): string | null {
  if (!text) return null
  try {
    const o = JSON.parse(text)
    return typeof o?.release === 'string' && /^[\w.+-]+$/.test(o.release) ? o.release : null
  } catch { return null } // not JSON: no id
}

// Generation awareness (A2-14): the release this process loaded vs the one ACTIVE.json names now. A process cannot
// migrate itself: only a new process (`/restart`, `claude --resume`) loads the current release, and `/clear` never does.
export const ACTIVE_MAX_BYTES = 200
export const IMPACT_CLASSES = ['none', 'hook', 'policy', 'breaking'] as const
export type ImpactClass = (typeof IMPACT_CLASSES)[number]
export interface ActiveInfo { release: string; impact: ImpactClass | null }
export function parseActive(text: string | null): ActiveInfo | null {
  if (!text || text.length > ACTIVE_MAX_BYTES) return null // unreadable or oversized: no verdict, never a guess
  try {
    const o = JSON.parse(text)
    if (typeof o?.release !== 'string' || !/^[\w.+-]+$/.test(o.release)) return null
    const impact = IMPACT_CLASSES.includes(o.impact_class) ? (o.impact_class as ImpactClass) : null
    return { release: o.release, impact }
  } catch { return null } // not JSON: no verdict
}
export interface GenerationVerdict { stale: boolean; current: string; status: string | null; key: string }
// loaded null = a development load (no RELEASE.json): there is nothing to compare, so no verdict at all.
export function generationVerdict(loaded: string | null, active: ActiveInfo | null): GenerationVerdict | null {
  if (!loaded || !active) return null
  const stale = loaded !== active.release
  return { stale, current: active.release, status: stale ? `CCR stale: loaded ${loaded}, current ${active.release}${active.impact ? ` (${active.impact})` : ''}` : null, key: `${loaded}>${active.release}` }
}

// Subagent types that keep the skill listing: they can run skills (Skill tool in their set).
export const SKILL_CAPABLE_AGENTS = new Set(['general-purpose', 'claude', 'fork'])

// Instruction files a main session always keeps: the CLAUDE.md files (the Owner's and the project's
// constitutions) and the rule files that are themselves indexes or baselines. A file not named in
// RULE_TRIGGERS is kept too: an unknown file fails toward materialization, never away from it.
export const ALWAYS_KEEP = [/(^|[\\/])CLAUDE\.md$/i, /skill-rule-index\.md$/i, /test-plan-against-facts-in-hand\.md$/i]

// Rule files linked by Work Class: kept only when the first prompt of the session matches.
export const RULE_TRIGGERS: Record<string, RegExp> = {
  'code-review.md': /\b(review|audit|finding|pull request|PR)\b/i,
  'durable-exit-transaction.md': /\b(exit|quit|shutdown|teardown|release)\b/i,
  'effect-authority-across-transports.md': /\b(transport|client|rpc|headless|server|effect|launch|desktop|mobile)\b/i,
  'generated-content-needs-an-evidence-gate.md': /\b(generat\w*|copy|landing|product page|email|report|summary|claim)\b/i,
  'testing.md': /\b(python|pytest|test\w*|\.py)\b/i,
  'seo-geo-corpus-methodology.md': /\b(seo|geo|aio|search visibility|ranking|serp)\b/i,
}

export type InstructionFileInfo = { path: string; kind: string; content: string }
export type FileDecision = { path: string; keep: boolean; reason: string; bytes: number }

const baseName = (p: string) => p.split(/[\\/]/).pop() ?? p

export function linkInstructionFiles(files: readonly InstructionFileInfo[], firstPrompt: string): FileDecision[] {
  return files.map(f => {
    const bytes = f.content.length
    // Managed policy is the host's non-overridable floor: always linked, whatever the Work Class.
    if (/managed/i.test(f.kind)) return { path: f.path, keep: true, reason: 'managed', bytes }
    if (ALWAYS_KEEP.some(re => re.test(f.path))) return { path: f.path, keep: true, reason: 'always', bytes }
    const trigger = RULE_TRIGGERS[baseName(f.path)]
    if (!trigger) return { path: f.path, keep: true, reason: 'untriaged', bytes }
    return trigger.test(firstPrompt)
      ? { path: f.path, keep: true, reason: 'work-class', bytes }
      : { path: f.path, keep: false, reason: 'unlinked', bytes }
  })
}

export type AttachmentDecision = { action: 'keep' | 'drop' | 'replace'; reason: string; text?: string | null }

export function firstHeading(content: string): string {
  const line = content.split('\n').find(l => /^#\s/.test(l))
  return line ? line.replace(/^#\s+/, '').trim().slice(0, 90) : ''
}

// The kernel size the runtime reads (register.ts slices the digest to it). The whole replacement text stays within
// it whatever the size of the estate (v4 A4 estate gate: 10x the files must not mean 10x the bytes).
export const KERNEL_CHARS = 8000

const dirOf = (p: string) => { const i = Math.max(p.lastIndexOf('/'), p.lastIndexOf('\\')); return i > 0 ? p.slice(0, i) : p }

// One line per file while the lines fit the budget. Past it, files are named by directory (count and size), and the
// directories by their parents until the index fits: every file stays one Glob + Read away, none is named twice.
export function fileIndex(files: readonly InstructionFileInfo[], budget: number): string {
  const full = files
    .map(f => `- ${f.path} (${f.kind}, ${f.content.length} chars)${firstHeading(f.content) ? ` -- ${firstHeading(f.content)}` : ''}`)
    .join('\n')
  if (full.length <= budget) return full
  let dirs = files.map(f => ({ dir: dirOf(f.path), chars: f.content.length }))
  let text = ''
  for (let depth = 0; depth < 64; depth++) {
    const by = new Map<string, { n: number; chars: number }>()
    for (const d of dirs) { const v = by.get(d.dir) ?? { n: 0, chars: 0 }; v.n++; v.chars += d.chars; by.set(d.dir, v) }
    text = [...by].map(([d, v]) => `- ${d}/ (${v.n} files, ${v.chars} chars; Glob it for the names)`).join('\n')
    const up = dirs.map(d => ({ ...d, dir: dirOf(d.dir) }))
    if (text.length <= budget || up.every((d, i) => d.dir === dirs[i].dir)) break
    dirs = up
  }
  return text.length <= budget ? text : `- ${files.length} instruction files (${files.reduce((s, f) => s + f.content.length, 0)} chars) are on disk; Glob for them`
}

// The text a subagent reads in place of the full instruction files: the compiled HARD-RULES
// digest (the constitutional kernel, maintained by rule_compiler) plus an index of the files it did
// not receive, so a file the task turns out to need is one Read away.
export function subagentInstructions(kernel: string, files: readonly InstructionFileInfo[]): string {
  const head = [
    'Instruction files for this subagent were linked by the CPP Cognitive Runtime: the constitutional kernel is below, and',
    'the full files are not loaded. If your task touches one of them, Read it before acting. Hooks and guards still apply in full.',
    '',
    kernel.trim(),
    '',
    'Instruction files available on disk:',
  ].join('\n')
  return `${head}\n${fileIndex(files, KERNEL_CHARS - head.length - 1)}`
}

export function decideSubagentAttachment(
  type: string, agentType: string | undefined, kernel: string | null, files: readonly InstructionFileInfo[] | null,
): AttachmentDecision {
  if (type === 'instructions') {
    // Without the kernel or the file list the replacement cannot preserve what it removes: keep.
    if (!kernel || !files || files.length === 0) return { action: 'keep', reason: 'kernel-or-files-missing' }
    if (files.some(f => /managed/i.test(f.kind))) return { action: 'keep', reason: 'managed-present' }
    return { action: 'replace', reason: 'kernel+index', text: subagentInstructions(kernel, files) }
  }
  if (type === 'skill_listing') {
    if (agentType && SKILL_CAPABLE_AGENTS.has(agentType)) return { action: 'keep', reason: 'skill-capable' }
    return { action: 'drop', reason: 'agent-not-skill-capable' }
  }
  return { action: 'keep', reason: 'not-linked' }
}

// ---------------------------------------------------------------------------------------------------
// Work units: a main session whose launcher declared a bounded Work Unit (env CCR_WORK_UNIT = path of a
// JSON file {"class": "...", "id": "..."}). The launcher names the class only; the closure of each class
// (which tools stay in front, what instruction text, which listings) is the runtime's knowledge, not the
// launcher's. An interactive session never carries the variable and keeps the main tier's behaviour.
export type WorkUnit = { cls: string; id: string }
export type WorkClass = { tools: readonly string[] }

// Tools a class keeps in front. Every other tool is deferred behind ToolSearch, never removed: a tool the
// task turns out to need is one ToolSearch away, and that search is a recorded page fault.
export const WORK_CLASSES: Record<string, WorkClass> = {
  'bounded-code-worker': { tools: ['Read', 'Edit', 'Write', 'Grep', 'Glob', 'PowerShell', 'ToolSearch'] },
  'read-only-reviewer': { tools: ['Read', 'ToolSearch'] },
}

// Main-session attachments a work unit does not carry: the listings a bounded unit cannot act on (it has
// no Skill or Agent tool in front) and MCP servers' prose. Instructions are replaced, not dropped.
export const UNIT_DROPPED_ATTACHMENTS = new Set(['skill_listing', 'agent_listing_delta', 'mcp_instructions_delta'])
// Prompt sections a work unit does not carry: auto-memory (the unit's ContextImage replaces it).
export const UNIT_DROPPED_SECTIONS = new Set(['memory'])

export function parseWorkUnit(text: string | null): WorkUnit | null {
  if (!text) return null
  try {
    const o = JSON.parse(text)
    // An unknown class fails toward materialization: no unit, stock context.
    if (typeof o?.class !== 'string' || !(o.class in WORK_CLASSES)) return null
    return { cls: o.class, id: typeof o.id === 'string' ? o.id.slice(0, 120) : '' }
  } catch {
    return null // unreadable declaration: no unit
  }
}

export function decideUnitTool(tool: string, unit: WorkUnit): 'keep' | 'defer' {
  // The runtime's own page tool is how a withheld listing or file comes back: never deferred.
  if (/cpp-cognitive-runtime__page$/.test(tool) || tool === 'page') return 'keep'
  return WORK_CLASSES[unit.cls].tools.includes(tool) ? 'keep' : 'defer'
}

export function decideUnitAttachment(
  type: string, kernel: string | null, files: readonly InstructionFileInfo[] | null,
): AttachmentDecision {
  if (type === 'instructions') return decideSubagentAttachment(type, undefined, kernel, files)
  if (UNIT_DROPPED_ATTACHMENTS.has(type)) return { action: 'drop', reason: 'not-in-unit-closure' }
  return { action: 'keep', reason: 'not-linked' }
}

export function decideUnitSection(name: string): AttachmentDecision {
  return UNIT_DROPPED_SECTIONS.has(name) ? { action: 'drop', reason: 'not-in-unit-closure' } : { action: 'keep', reason: 'not-linked' }
}

// Hook-context paragraphs that declare themselves advisory are candidates for the materialization
// firewall. Main sessions measure them (shadow); nothing that blocks or denies is ever matched.
export const ADVISORY_MARK = /advisory|never blocks|ignore otherwise|unverified; ranked/i

export function advisoryBytes(text: string): number {
  return text
    .split(/\n\s*\n/)
    .filter(p => ADVISORY_MARK.test(p) && !/\b(den(y|ied)|block(ed|ing|s)?|stop)\b/i.test(p.replace(/never blocks/gi, '')))
    .reduce((n, p) => n + p.length, 0)
}

// FNV-1a 32-bit: a stable repository key with no repository content in it.
export function repoKey(root: string | null): string {
  const s = (root ?? 'no-repo').toLowerCase().replace(/\\/g, '/')
  let h = 0x811c9dc5
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i)
    h = Math.imul(h, 0x01000193) >>> 0
  }
  return h.toString(16).padStart(8, '0')
}

// Multimodal carry receipt (UMVM M1, observe only). An image block crosses the provider boundary on every
// call after it is appended, so each one is receipted by identity (hash of its bytes), size and an
// estimated token cost. The estimate is the documented w*h/750 after downscale; M2 calibrates it against usage.
const B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

export function b64Prefix(b64: string, n: number): Uint8Array {
  const out: number[] = []
  let acc = 0
  let bits = 0
  for (let i = 0; i < b64.length && out.length < n; i++) {
    const v = B64.indexOf(b64[i])
    if (v < 0) continue // padding or whitespace
    acc = (acc << 6) | v
    bits += 6
    if (bits >= 8) { bits -= 8; out.push((acc >> bits) & 0xff) }
  }
  return Uint8Array.from(out)
}

export function fnv(s: string): string {
  let h = 0x811c9dc5
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0 }
  return h.toString(16).padStart(8, '0')
}

export function imageDims(b64: string): { w: number; h: number } | null {
  const b = b64Prefix(b64, 24)
  if (b.length >= 24 && b[0] === 0x89 && b[1] === 0x50) { // PNG: IHDR width/height, big endian
    return { w: ((b[16] << 24) | (b[17] << 16) | (b[18] << 8) | b[19]) >>> 0, h: ((b[20] << 24) | (b[21] << 16) | (b[22] << 8) | b[23]) >>> 0 }
  }
  if (b.length >= 10 && b[0] === 0x47 && b[1] === 0x49) return { w: b[6] | (b[7] << 8), h: b[8] | (b[9] << 8) } // GIF
  if (b.length >= 2 && b[0] === 0xff && b[1] === 0xd8) { // JPEG: walk segments to the first SOF
    const j = b64Prefix(b64, 262144)
    let i = 2
    while (i + 9 < j.length) {
      if (j[i] !== 0xff) { i++; continue }
      const m = j[i + 1]
      if (m >= 0xc0 && m <= 0xcf && m !== 0xc4 && m !== 0xc8 && m !== 0xcc) return { w: (j[i + 7] << 8) | j[i + 8], h: (j[i + 5] << 8) | j[i + 6] }
      i += 2 + ((j[i + 2] << 8) | j[i + 3])
    }
  }
  return null
}

// Calibrated 2026-10-12 on Opus 5.5 against next-call usage (known text rows subtracted): 1033x917 est 1,264 /
// measured ~1,318; 2000x1278 est 3,408 / measured ~3,420. No 1.15 MP cap applies: the Read tool already sends
// at most 2000 px on the long edge, and the provider bills the block as sent.
export const PIXELS_PER_TOKEN = 750

export function imageTokens(w: number, h: number): number {
  return Math.ceil((w * h) / PIXELS_PER_TOKEN)
}

export type ImageFact = { hash: string; media: string | null; w: number | null; h: number | null; b64: number; tok: number | null }
// `thinking` counts visible thinking text; `sealed` counts signature / redacted bytes, the part of a carried
// thinking block no text field shows (Worker-A p4p2a3: 1.7K visible vs 129K signature chars over 38 blocks).
export type RowFacts = { text: number; thinking: number; sealed: number; images: ImageFact[] }

export function rowFacts(blocks: readonly unknown[]): RowFacts {
  const f: RowFacts = { text: 0, thinking: 0, sealed: 0, images: [] }
  const walk = (x: unknown) => {
    if (typeof x === 'string') { f.text += x.length; return }
    if (Array.isArray(x)) { x.forEach(walk); return }
    if (!x || typeof x !== 'object') return
    const o = x as Record<string, any>
    if (o.type === 'image' && typeof o.source?.data === 'string') {
      const d = imageDims(o.source.data)
      f.images.push({ hash: fnv(o.source.data), media: o.source.media_type ?? null, w: d?.w ?? null, h: d?.h ?? null, b64: o.source.data.length, tok: d ? imageTokens(d.w, d.h) : null })
      return
    }
    if (o.type === 'thinking' || o.type === 'redacted_thinking') {
      f.thinking += typeof o.thinking === 'string' ? o.thinking.length : 0
      f.sealed += (typeof o.signature === 'string' ? o.signature.length : 0) + (typeof o.data === 'string' ? o.data.length : 0)
      return
    }
    if (typeof o.text === 'string') f.text += o.text.length
    if (o.type === 'tool_use') f.text += JSON.stringify(o.input ?? {}).length
    if (o.content !== undefined) walk(o.content)
  }
  walk(blocks)
  return f
}

// Epoch deopt advice (observe only; the driver owns rotation). A call costs floor + carry; a fresh epoch costs
// floor + rehydration. Measured on Worker-A d6343597: floor 14.4K, carry grew ~2.4K/call to 60.8K, images 16.8 %
// of processed tokens and text carry ~52 %. Advice fires once the carry above the floor reaches the floor itself:
// from then on every call pays at least twice what a fresh epoch's call pays.
export const ROTATE_CARRY_RATIO = 1

export type CarryAdvice = { rotate: boolean; floor: number; ctx: number; carry: number; imageTok: number; textCarry: number
  rotateAdvice?: RotateAdvice }

export function carryAdvice(floor: number, ctx: number, imageTok: number, be?: { model: BreakevenModel; call: number } | null): CarryAdvice {
  const carry = Math.max(0, ctx - floor)
  const a: CarryAdvice = { rotate: floor > 0 && carry >= ROTATE_CARRY_RATIO * floor, floor, ctx, carry, imageTok, textCarry: Math.max(0, carry - imageTok) }
  if (be && floor > 0) a.rotateAdvice = rotateAdvice(be.model, floor, ctx, be.call)
  return a
}

// Weighted rotation break-even (v4 A4, tools/ccr_breakeven.py; observe only, nothing here rotates). A rotation pays
// once: write floor + capsule, the rehydration calls, the first call's overhead. It then saves W_READ on every token
// of carry above floor + capsule + R on each later call. With carry growing g per call the cheapest cycle rotates at
// carry X* = sqrt(2 * once * g / W_READ); it is advised only when the calls still expected exceed the payback k*.
// Measured (Linux plane GEX44, host 2.1.296): capsules of 164-564 tokens, not the 8k E1 assumed.
export const W_READ = 0.1
export const W_WRITE = 1.25
export type BreakevenModel = { cls: string; capsule: number; R: number; rehyd_cost: number; first_overhead: number
  r: number; g: number; lengths: number[] }
export type RotateAdvice = { rotate: boolean; kStar: number | null; xStar: number | null; carry: number; remaining: number }

export function parseBreakevenModel(text: string | null, cls: string): BreakevenModel | null {
  if (!text) return null
  try {
    const m = JSON.parse(text)
    const ok = m?.cls === cls && [m.capsule, m.R, m.rehyd_cost, m.first_overhead, m.r, m.g]
      .every((v: unknown) => typeof v === 'number' && Number.isFinite(v) && v >= 0)
      && Array.isArray(m.lengths) && m.lengths.length > 0 && m.lengths.every((v: unknown) => typeof v === 'number')
    return ok ? m as BreakevenModel : null
  } catch { return null } // unparseable model: no break-even advice, the carry receipt stands alone
}

// Median calls still to come for a session at `call`, over the class sessions that lasted longer.
export function expectedRemaining(call: number, lengths: readonly number[]): number {
  const rest = lengths.filter(n => n > call).map(n => n - call).sort((x, y) => x - y)
  if (!rest.length) return 0
  const h = rest.length >> 1
  return rest.length % 2 ? rest[h] : (rest[h - 1] + rest[h]) / 2
}

export function rotateAdvice(m: BreakevenModel, floor: number, ctx: number, call: number): RotateAdvice {
  const once = W_WRITE * (floor + m.capsule) + m.rehyd_cost + m.r * W_READ * m.capsule + m.first_overhead
  const carry = ctx - floor - m.capsule - m.R
  const kStar = carry > 0 ? once / (W_READ * carry) : null
  const xStar = m.g > 0 ? Math.sqrt(2 * once * m.g / W_READ) : null
  const remaining = expectedRemaining(call, m.lengths)
  return { rotate: kStar !== null && xStar !== null && carry >= xStar && remaining > kStar,
    kStar: kStar === null ? null : +kStar.toFixed(1), xStar: xStar === null ? null : Math.round(xStar), carry: Math.round(carry), remaining }
}

// Image results by the call they answer, so a compaction can name what it evicts.
export function imagesByUse(blocks: readonly unknown[]): Map<string, ImageFact[]> {
  const out = new Map<string, ImageFact[]>()
  for (const b of blocks as any[]) {
    if (b?.type !== 'tool_result' || typeof b.tool_use_id !== 'string') continue
    const imgs = rowFacts([b]).images
    if (imgs.length) out.set(b.tool_use_id, imgs)
  }
  return out
}

export function tombstone(imgs: readonly ImageFact[]): string {
  return imgs.map(i => `[CCR: image ${i.hash} (${i.w ?? '?'}x${i.h ?? '?'}, ~${i.tok ?? '?'} tok) left the context; the read succeeded `
    + `and the file is unchanged on disk. Read it again only if a later step needs the pixels.]`).join('\n')
}

type GcMessage = { role: 'user' | 'assistant'; text: string; toolUses: any[]; toolResults?: any[]; handle?: string }
export type GcPlan = { messages: GcMessage[] | null; evicted: ImageFact[]; keptWhole: number }

// Pixel GC kept-set (UMVM arm D). Messages before the live window are rebuilt without their handle, which the
// engine reads as built: text, tool uses and tool-result text stay, media blocks leave. An image result gets a
// tombstone, or the model reads the empty result as a failed read (measured 2026-10-12, sid e8238452). The last
// `keepLast` messages stay whole, and the window never starts on a tool result split from its tool use.
// No image to evict: no plan (the caller skips, the conversation stays as it is).
export function gcKeptSet(messages: readonly GcMessage[], images: ReadonlyMap<string, ImageFact[]>, keepLast: number): GcPlan {
  let cut = Math.max(0, messages.length - keepLast)
  while (cut > 0 && messages[cut]?.toolResults?.length) cut--
  const evicted: ImageFact[] = []
  const rebuilt = messages.map((m, i) => {
    if (i >= cut) return m
    const toolResults = m.toolResults?.map(r => {
      const imgs = images.get(r.tool_use_id)
      if (!imgs) return r
      evicted.push(...imgs)
      return { ...r, text: [r.text, tombstone(imgs)].filter(Boolean).join('\n') }
    })
    return { role: m.role, text: m.text, toolUses: m.toolUses, ...(toolResults ? { toolResults } : {}) }
  })
  return { messages: evicted.length ? rebuilt : null, evicted, keptWhole: messages.length - cut }
}

// Tool Output Projection (v4 B5). A shell result rides every later call of its epoch, so its cost is its size times
// its rides: M4 measured one call-2 recursive listing of a runs tree at 0.30-0.34M tok per attempt, more than all
// image carry. Over the budget, the model gets a projection plus the path of the full output, which stays on disk,
// so an under-projection is one Read or Grep away and never a loss. A listing (most lines are paths) projects to
// per-directory counts, which is what a listing is usually asked for; any other text keeps its head and tail.
export const PROJECT_BUDGET_CHARS = 8000
export const PROJECT_TOOLS = new Set(['Bash', 'PowerShell'])
const PATH_LINE = /^\s*(?:[A-Za-z]:)?[\w.~\-@+ ]*[\\/][^\t<>|"]*$/

export type Projection = { action: 'pass' | 'project'; kind: 'listing' | 'text' | null; bytes: number; lines: number; out: string }

export function projectToolOutput(text: string, fullPath: string, budget = PROJECT_BUDGET_CHARS): Projection {
  const lines = text.split('\n')
  if (text.length <= budget) return { action: 'pass', kind: null, bytes: text.length, lines: lines.length, out: text }
  const nonEmpty = lines.filter(l => l.trim())
  const pathish = nonEmpty.filter(l => PATH_LINE.test(l)).length
  const listing = nonEmpty.length >= 20 && pathish >= 0.8 * nonEmpty.length
  const note = `[CCR projected this output: ${text.length} chars, ${lines.length} lines over the ${budget}-char budget. `
    + `The full output is at ${fullPath}; Grep or Read that file for the exact lines you need.]`
  const room = Math.max(1000, budget - note.length - 200)
  let body: string
  if (listing) {
    const dirs = new Map<string, number>()
    for (const l of nonEmpty) {
      const p = l.trim().replace(/\\/g, '/')
      const d = p.includes('/') ? p.slice(0, p.lastIndexOf('/')) : '.'
      dirs.set(d, (dirs.get(d) ?? 0) + 1)
    }
    const rows = [...dirs.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    body = `${nonEmpty.length} paths in ${dirs.size} directories (entries per directory, largest first):\n`
    let shown = 0
    for (const [d, n] of rows) {
      const row = `${n}\t${d}\n`
      if (body.length + row.length > room) { body += `... ${rows.length - shown} more directories in the full output\n`; break }
      body += row
      shown++
    }
  } else {
    const half = Math.floor(room / 2)
    const omitted = text.length - 2 * half
    body = `${text.slice(0, half)}\n... [${omitted} chars omitted] ...\n${text.slice(text.length - half)}`
  }
  return { action: 'project', kind: listing ? 'listing' : 'text', bytes: text.length, lines: lines.length, out: `${note}\n${body}` }
}

// Cognitive PGO (v4 B6): a Work-Class model built by tools/ccr_pgo.py from real transcripts. Only the fields the
// hot path reads are typed; anything missing makes the model unusable, never a zero.
export type ClassModel = { cls: string; n: number; floor: { p50: number; p80: number }; calls: { p50: number; p80: number }
  slope: { p50: number; p80: number }; step: { p50: number; p95: number } }

export function parseClassModel(text: string | null, cls: string): ClassModel | null {
  if (!text) return null
  try {
    const m = JSON.parse(text)
    const ok = m?.cls === cls && m.n > 0 && [m.floor?.p50, m.floor?.p80, m.calls?.p50, m.calls?.p80, m.slope?.p50, m.slope?.p80, m.step?.p95]
      .every((v: unknown) => typeof v === 'number' && Number.isFinite(v))
    return ok ? m as ClassModel : null
  } catch { return null } // unparseable model file: no model, the boundary is unforecast
}

// processed(n) = n*floor + g*n*(n-1)/2: floor rent plus the carry the class's per-call growth implies.
export function boundaryForecast(m: ClassModel): { p50: number; p80: number; calls: number } {
  const proc = (g: number, n: number) => n * m.floor.p50 + g * n * (n - 1) / 2
  return { p50: Math.round(proc(m.slope.p50, m.calls.p50)), p80: Math.round(proc(m.slope.p80, m.calls.p80)), calls: m.calls.p50 }
}

// A step (ctx growth between two calls) above the class P95 is an anomaly; its cost is the step times the calls it
// is expected to ride. M4 measured: step 11,213 after call 2 against a P95 of 3,621, riding 30 calls = 336,390 tok.
export function stepAnomaly(step: number, call: number, m: ClassModel): { anomaly: boolean; ratio: number; ridesLeft: number; costIfRides: number } {
  const ridesLeft = Math.max(0, Math.round(m.calls.p80) - call)
  return { anomaly: m.step.p95 > 0 && step > m.step.p95, ratio: m.step.p95 > 0 ? +(step / m.step.p95).toFixed(2) : 0, ridesLeft, costIfRides: step * ridesLeft }
}

export function pageLines(listing: string, query: string, limit = 40): string {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean)
  const hits = listing.split('\n').filter(l => words.length === 0 || words.some(w => l.toLowerCase().includes(w)))
  return hits.slice(0, limit).join('\n') || '(no matching entries)'
}

// ---------------------------------------------------------------------------------------------------
// Main-lean canary (v4 A7). DEFAULT-ON (Owner D1, 2026-10-31; L5 -22.3% call-1, L6 -27.8% processed, 6/6 correct, 0 page
// faults): unset or CCR_MAIN_CANARY=1 turns it on, CCR_MAIN_CANARY=0 (or any other value) opts the pane out. Read once at
// session start, on an interactive session with no Work Unit. The A7 shadow (tools/ccr_main_shadow.py) found that dropping the listings, as unit closure
// does, would have removed a capability 19 of 50 interactive sessions later used (14 Skill, 43 Agent calls), so the
// main session keeps every name and loses only the descriptions; the full text is one page call away.
// Rollback: CCR_MAIN_CANARY=0, `ccr_release.py rollback`, or the OFF file (main off turns the canary off too).
export const MAIN_LEAN_ATTACHMENTS = new Set(['skill_listing', 'agent_listing_delta', 'mcp_instructions_delta'])

export function mainCanaryMode(env: string | undefined, interactive: boolean, hasUnit: boolean, modes: Modes, compatible: boolean): Mode {
  if ((env !== undefined && env !== '1') || !interactive || hasUnit || modes.main === 'off') return 'off'
  return compatible ? 'enforce' : 'shadow'
}

const PAGE_HINT = (kind: string) =>
  `(CPP Cognitive Runtime main canary: names only. For a description, load mcp__cpp-cognitive-runtime__page with ToolSearch and call it with kind "${kind}" and the name as query.)`

// "- name: description" becomes "- name". A name ends at the first colon followed by whitespace, so a plugin-scoped
// name (plugin:skill) stays whole. Every other line is kept. No compacted line, or no saving: keep the stock text.
// `keep` names entries whose full line stays (the always-on whitelist of the successor canary).
export function nameOnlyListing(text: string, kind: 'skills' | 'agents', keep?: ReadonlySet<string>): string | null {
  let n = 0
  const out = text.split('\n').map(l => {
    const m = /^- (\S+?):\s/.exec(l)
    if (!m || keep?.has(m[1])) return l
    n++
    return `- ${m[1]}`
  }).join('\n')
  if (n === 0) return null
  const res = `${out.trimEnd()}\n${PAGE_HINT(kind)}`
  return res.length < text.length ? res : null
}

// MCP server instructions become their headings (one per server); the servers' tools are not touched.
export function mcpHeadings(text: string): string | null {
  const heads = text.split('\n').filter(l => /^#{1,3}\s/.test(l))
  if (heads.length === 0) return null
  const res = `${heads.join('\n')}\n${PAGE_HINT('mcp')}`
  return res.length < text.length ? res : null
}

export function decideMainLeanAttachment(type: string, text: string, keepSkills?: ReadonlySet<string>): AttachmentDecision {
  if (!MAIN_LEAN_ATTACHMENTS.has(type)) return { action: 'keep', reason: 'not-linked' }
  const out = type === 'skill_listing' ? nameOnlyListing(text, 'skills', keepSkills)
    : type === 'agent_listing_delta' ? nameOnlyListing(text, 'agents') : mcpHeadings(text)
  return out === null ? { action: 'keep', reason: 'no-names-parsed' } : { action: 'replace', reason: 'main-lean', text: out }
}

// ICC W1: the deferred-tool-name list (attachment deferred_tools_delta) is the largest static source on a many-MCP
// estate (laptop recorded plane 45,603 chars: vercel 241 names, rea 207). Each `mcp__<server>__<tool>` line is collapsed
// to one line per server (count + a ToolSearch hint). Built-in deferred names and every non-name line stay verbatim, so a
// built-in tool is still listed. The tools are not removed: ToolSearch finds them by keyword or exact select.
// Kill switch CCR_DEFERRED_NAMES=0. Default shadow (receipt carries before/after chars); 'enforce' is explicit until the
// quality bench (n=10 ON/OFF) is non-inferior.
const MCP_NAME = /^mcp__(.+?)__\S+$/
export function collapseDeferredNames(text: string): string | null {
  const counts = new Map<string, number>()
  const firstAt = new Map<string, number>()
  const lines = text.split('\n')
  const out: (string | null)[] = lines.map((l, i) => {
    const m = MCP_NAME.exec(l.trim())
    if (!m) return l
    counts.set(m[1], (counts.get(m[1]) ?? 0) + 1)
    if (!firstAt.has(m[1])) firstAt.set(m[1], i)
    return null
  })
  if (counts.size === 0) return null
  for (const [server, i] of firstAt) {
    out[i] = `mcp__${server}__* (${counts.get(server)} deferred tools; find by keyword with ToolSearch, or select:mcp__${server}__<name>)`
  }
  const res = out.filter((l): l is string => l !== null).join('\n')
  return res.length < text.length ? res : null
}

export function deferredNamesMode(env: string | undefined, canary: Mode): Mode {
  if (env === '0' || canary === 'off') return 'off'
  return env === 'enforce' && canary === 'enforce' ? 'enforce' : 'shadow'
}

// The page fault for MCP instructions: the block under each heading that matches the query (all blocks if none given).
export function pageBlocks(text: string, query: string): string {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean)
  const blocks = text.split(/\n(?=#{1,3}\s)/)
  const hits = blocks.filter(b => words.length === 0 || words.some(w => (b.split('\n')[0] ?? '').toLowerCase().includes(w)))
  return hits.join('\n') || '(no matching entries)'
}

// ---------------------------------------------------------------------------------------------------
// Floor-diet canary on /kresume successors (ccr-next Tranche A4). A successor pays the first-call floor on every one of
// its calls, so the main-lean listings and the unlinked instruction files are withheld on successors only, behind `page`.
// Recognition is the START of the first prompt: the analysis class in tools/ccr_weekly_loss.py is a substring test, so it
// can over-count successors but never hide a canary. `prompt.submit` runs before the first attachment (Phase 3 receipt).
// The host submits a slash command expanded, <command-message> first and <command-name> second, so the tag may sit anywhere.
export const SUCCESSOR_MARK = /^\s*(\/|<command-(name|message)>\s*\/?)kresume\b|<command-name>\s*\/?kresume\b/i
export const isKresumeSuccessor = (prompt: string): boolean => SUCCESSOR_MARK.test(prompt.slice(0, 600))
// A /clear and its local-command caveat are submitted before the successor's own prompt (ddf628be): neither is the first prompt.
const LOCAL_RECORD = /^\s*(<local-command-(caveat|stdout|stderr)>|(<command-name>\s*)?\/clear(?![\w-]))/i
export const isFirstPromptCandidate = (text: string): boolean => !LOCAL_RECORD.test(text)

// Skills whose description line stays in a successor's listing: the ones this estate's transcripts show used 3+ times
// (GEX44 week of 2026-10-17: gsd-plan-phase 43, gsd-execute-phase 36, gsd-code-review 20, code-reviewer 19, gsd-autonomous 10,
// gsd-ui-phase 5, kclear 3, gsd-discuss-phase 3). Every other skill keeps its name and is one `page` call from its text.
export const SUCCESSOR_KEEP_SKILLS: ReadonlySet<string> = new Set([
  'gsd-plan-phase', 'gsd-execute-phase', 'gsd-code-review', 'code-reviewer', 'gsd-autonomous', 'gsd-ui-phase', 'kclear', 'gsd-discuss-phase',
])

// kill is CCR_SUCCESSOR_CANARY: '0' turns the canary off for the launch. Any other state, with a successor marker on an
// interactive session with no Work Unit and main not off, runs it (enforce on a covered build, shadow elsewhere).
export function successorCanaryMode(prompt: string, kill: string | undefined, interactive: boolean, hasUnit: boolean, modes: Modes, compatible: boolean): Mode {
  if (kill === '0' || !interactive || hasUnit || modes.main === 'off' || !isKresumeSuccessor(prompt)) return 'off'
  return compatible ? 'enforce' : 'shadow'
}

// The successor decision against the session's launch (main) canary. With no launch canary it is the successor canary, as
// before. With the main canary on (default since L8) a /kresume successor still activates -- so its frontier is resolved --
// and keeps the main canary's mode; the old gate returned 'off' there, which disabled the frontier path (GPF-L1 2026-11-02).
export function successorMode(launch: Mode, prompt: string, kill: string | undefined, interactive: boolean, hasUnit: boolean, modes: Modes, compatible: boolean): Mode {
  const s = successorCanaryMode(prompt, kill, interactive, hasUnit, modes, compatible)
  return launch === 'off' || s === 'off' ? s : launch
}

// Resumed-task frontier (Tramo A2 Phase 2). `tools/rollover.py seal` writes rollover/latest/<repoKey>.json
// {capsule, sha256, sealed_at (epoch s)}. A successor trusts it only when it is fresh, parses, and the capsule's bytes hash to
// the sealed sha256. Anything else is UNKNOWN (null) and the rule files stay.
export const FRONTIER_MAX_AGE_S = 30 * 60
export type FrontierPointer = { capsule: string; sha256: string; sealedAt: number }
export function parseFrontierPointer(text: string | null, nowMs: number): FrontierPointer | null {
  if (!text) return null
  try {
    const o = JSON.parse(text)
    if (typeof o?.capsule !== 'string' || !/^[0-9a-f]{64}$/.test(o?.sha256) || !Number.isFinite(o?.sealed_at)) return null
    const age = nowMs / 1000 - o.sealed_at
    return age >= 0 && age <= FRONTIER_MAX_AGE_S ? { capsule: o.capsule, sha256: o.sha256, sealedAt: o.sealed_at } : null
  } catch { return null } // unreadable pointer: UNKNOWN
}
// The task text rule linking runs on: obligations, summary, goal path and the session's recent writes. An empty frontier is UNKNOWN.
export function frontierText(capsuleText: string): string | null {
  try {
    const c = JSON.parse(capsuleText)
    const parts: string[] = [
      ...(Array.isArray(c?.obligations) ? c.obligations : []), typeof c?.summary === 'string' ? c.summary : '',
      typeof c?.goal?.path === 'string' ? c.goal.path : '', ...(Array.isArray(c?.writes) ? c.writes : []),
    ].filter(x => typeof x === 'string' && x.trim() !== '')
    return parts.length ? parts.join('\n') : null
  } catch { return null } // unreadable capsule: UNKNOWN
}

// Each `unlinked` file is cut out of the rendered instructions by exact content match and replaced by a one-line marker.
// A file whose content is not found exactly once stays (fail open); `always`, `managed` and `untriaged` files are never touched.
// `frontier` is the resumed task's text (obligations, summary, goal, writes), never the `/kresume` command: that command
// carries no task semantics, so linking on it withheld every rule file whatever the task (CONTROL_COMMAND_USED_AS_TASK_SEMANTICS).
// A null frontier is UNKNOWN and fails toward keeping all rules.
export function decideSuccessorInstructions(text: string, files: readonly InstructionFileInfo[] | null, frontier: string | null): AttachmentDecision & { withheld: string[] } {
  if (!files || files.length === 0) return { action: 'keep', reason: 'files-missing', withheld: [] }
  if (frontier === null) return { action: 'keep', reason: 'frontier-unknown', withheld: [] }
  let out = text
  const withheld: string[] = []
  for (const d of linkInstructionFiles(files, frontier)) {
    if (d.keep) continue
    const f = files.find(x => x.path === d.path)
    if (!f || f.content.length === 0) continue
    const at = out.indexOf(f.content)
    if (at < 0 || out.indexOf(f.content, at + 1) >= 0) continue
    out = `${out.slice(0, at)}[CCR withheld ${baseName(f.path)} (${f.content.length} chars). Read ${f.path} if the task touches it.]${out.slice(at + f.content.length)}`
    withheld.push(f.path)
  }
  if (withheld.length === 0) return { action: 'keep', reason: 'nothing-unlinked-found', withheld }
  return out.length < text.length ? { action: 'replace', reason: 'successor-unlinked', text: out, withheld } : { action: 'keep', reason: 'no-saving', withheld: [] }
}

// ---------------------------------------------------------------------------------------------------
// Capability Linker + Minimum Discoverability Signatures (Tramo A2 Phase 3). A successor listing keeps a name for every
// capability; what a name-only entry still owes the model is a way to FIND it. Each entry records how it stays reachable:
//   DETERMINISTIC_LINK       full line kept: whitelisted, linked by the frontier text, or the frontier is UNKNOWN (keep).
//   DISCOVERABILITY_SIGNATURE pilot entry reduced to `name — <mds-v1 signature>` (<= MDS_MAX chars).
//   RUNTIME_GUARD            name only; the `page` tool (and the model's own ToolSearch) is the way back.
//   NOT_REQUIRED             the line carried no description, so nothing was removed.
// Context Reachability Coverage = classified entries / entries, and must be 1 by construction (every parsed entry gets a class).
export type ReachClass = 'DETERMINISTIC_LINK' | 'DISCOVERABILITY_SIGNATURE' | 'RUNTIME_GUARD' | 'NOT_REQUIRED'
export const MDS_MAX = 72
export const MDS_SPEC = 'mds-v1|clause=(use when|use for|use this (skill )?when|use to)...first-sentence-fallback|ws-collapsed|max=72|ellipsis=…'
// Pilot set, measured: Skill/Agent tool_use counts over 14 days of this host's (GEX44) own transcripts, tools/ccr_usage_counts.py
// (phase 3 EVIDENCE). Only 9 distinct skills were used; gsd-autonomous and kclear come from the policy.ts counts above, so 11, not 12.
export const PILOT_SKILLS: ReadonlySet<string> = new Set([
  'gsd-plan-phase', 'gsd-execute-phase', 'code-reviewer', 'gsd-discuss-phase', 'gsd-code-review', 'gsd-ui-phase',
  'gsd-ai-integration-phase', 'plugin-authoring', 'claude-power-pack', 'gsd-autonomous', 'kclear',
])
export const PILOT_AGENTS: ReadonlySet<string> = new Set(['gsd-executor', 'gsd-planner', 'gsd-plan-checker', 'gsd-verifier', 'general-purpose', 'gsd-code-reviewer'])
// Frontier text -> capability. A capability whose pattern matches the resumed task keeps its full line.
export const SKILL_LINKS: Readonly<Record<string, RegExp>> = {
  'gsd-plan-phase': /plan[- ]phase|PLAN\.md|\bplanning\b/i, 'gsd-execute-phase': /execute[- ]phase|SUMMARY\.md|\bwave\b/i,
  'code-reviewer': /code[- ]review|\breview\b/i, 'gsd-code-review': /code[- ]review|REVIEW\.md/i, 'gsd-discuss-phase': /\bdiscuss|CONTEXT\.md/i,
  'gsd-ui-phase': /UI-SPEC|\bfrontend\b/i, 'gsd-ai-integration-phase': /AI-SPEC/i, 'plugin-authoring': /\bplugin\b|\bmod\b/i,
  'claude-power-pack': /power[- ]pack/i, 'gsd-autonomous': /autonomous/i, kclear: /kclear|hand-?off/i,
}
export const AGENT_LINKS: Readonly<Record<string, RegExp>> = {
  'gsd-executor': /execut|PLAN\.md/i, 'gsd-planner': /\bplan/i, 'gsd-plan-checker': /\bplan/i, 'gsd-verifier': /verif|VERIFICATION\.md/i,
  'general-purpose': /./, 'gsd-code-reviewer': /review/i,
}

// mds-v1: the description's "Use when/for ..." clause, else its first sentence; whitespace collapsed; cut at a word boundary to MDS_MAX.
export function mdsSignature(desc: string): string {
  const d = desc.replace(/\s+/g, ' ').trim()
  const clause = /\b(use when|use for|use this (?:skill )?when|use to)\b[^.]*/i.exec(d)?.[0]
  const first = clause ?? /^[^.]*/.exec(d)?.[0] ?? d
  const t = first.trim()
  if (t.length <= MDS_MAX) return t
  const cut = t.slice(0, MDS_MAX - 1)
  const sp = cut.lastIndexOf(' ')
  return `${(sp > 20 ? cut.slice(0, sp) : cut).trimEnd()}…`
}
export async function mdsSha(): Promise<string> {
  const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(MDS_SPEC))
  return [...new Uint8Array(d)].slice(0, 6).map(b => b.toString(16).padStart(2, '0')).join('')
}

export type ReachEntry = { name: string; cls: ReachClass }
// The names whose full line stays: the always-on whitelist, plus every capability the frontier links. An UNKNOWN frontier
// keeps the whole pilot set (absent is not zero: it fails toward keeping context).
export function linkedNames(frontier: string | null, links: Readonly<Record<string, RegExp>>, pilot: ReadonlySet<string>, always: ReadonlySet<string>): Set<string> {
  const keep = new Set(always)
  for (const n of pilot) if (frontier === null || links[n]?.test(frontier)) keep.add(n)
  return keep
}

export function successorListing(text: string, kind: 'skills' | 'agents', frontier: string | null): { text: string; entries: ReachEntry[] } | null {
  const pilot = kind === 'skills' ? PILOT_SKILLS : PILOT_AGENTS
  const keep = linkedNames(frontier, kind === 'skills' ? SKILL_LINKS : AGENT_LINKS, pilot, kind === 'skills' ? SUCCESSOR_KEEP_SKILLS : new Set())
  const entries: ReachEntry[] = []
  let changed = 0
  const out = text.split('\n').map(l => {
    const m = /^- (\S+?):\s+(.*)$/.exec(l)
    if (!m) {
      const bare = /^- (\S+)\s*$/.exec(l)
      if (bare) entries.push({ name: bare[1], cls: 'NOT_REQUIRED' })
      return l
    }
    if (keep.has(m[1])) { entries.push({ name: m[1], cls: 'DETERMINISTIC_LINK' }); return l }
    changed++
    if (pilot.has(m[1])) { entries.push({ name: m[1], cls: 'DISCOVERABILITY_SIGNATURE' }); return `- ${m[1]} — ${mdsSignature(m[2])}` }
    entries.push({ name: m[1], cls: 'RUNTIME_GUARD' })
    return `- ${m[1]}`
  }).join('\n')
  if (changed === 0) return null
  const res = `${out.trimEnd()}\n${PAGE_HINT(kind)}`
  return res.length < text.length ? { text: res, entries } : null
}

export function reachSummary(entries: readonly ReachEntry[]): Record<ReachClass | 'coverage', number> {
  const r = { DETERMINISTIC_LINK: 0, DISCOVERABILITY_SIGNATURE: 0, RUNTIME_GUARD: 0, NOT_REQUIRED: 0, coverage: 1 }
  for (const e of entries) r[e.cls]++
  return r
}

// Benchmark arm B (CCR_A2_ARM=B): release 82c98708 behaviour, pinned for the A/B. Rule files are linked on the first prompt (the
// `/kresume` command, which matches no trigger) and listings are the plain whitelist name-only form. Never set in production.
export function decideArmBAttachment(type: string, text: string, files: readonly InstructionFileInfo[] | null, firstPrompt: string): AttachmentDecision & { withheld?: string[] } {
  return type === 'instructions' ? decideSuccessorInstructions(text, files, firstPrompt) : decideMainLeanAttachment(type, text, SUCCESSOR_KEEP_SKILLS)
}

export function decideSuccessorAttachment(type: string, text: string, files: readonly InstructionFileInfo[] | null, frontier: string | null): AttachmentDecision & { withheld?: string[]; reach?: ReachEntry[] } {
  if (type === 'instructions') return decideSuccessorInstructions(text, files, frontier)
  if (type === 'skill_listing' || type === 'agent_listing_delta') {
    const r = successorListing(text, type === 'skill_listing' ? 'skills' : 'agents', frontier)
    return r === null ? { action: 'keep', reason: 'no-names-parsed' } : { action: 'replace', reason: 'successor-linked', text: r.text, reach: r.entries }
  }
  return decideMainLeanAttachment(type, text, SUCCESSOR_KEEP_SKILLS)
}

// Shell projection on successors (Tranche A5). A successor session has no Work Unit, so `project` is shadow there; the
// successor canary lifts it to the canary's mode, but only when the launch did not pick a project mode itself.
export function successorProjectMode(projectMode: Mode, successor: boolean, canary: Mode, modes: Modes, hasUnit: boolean): Mode {
  if (!successor || hasUnit || modes.project !== undefined || projectMode === 'off') return projectMode
  return canary
}

// A failed command's output is the evidence of the failure: it is never projected. A result that carries none of these
// fields is treated as a success (no failure signal = nothing to protect); the host's real field names are probed, not assumed.
export function shellFailed(res: { exitCode?: unknown; code?: unknown; interrupted?: unknown; isError?: unknown }): boolean {
  const n = res.exitCode ?? res.code
  return res.interrupted === true || res.isError === true || (typeof n === 'number' && n !== 0)
}

// ---------------------------------------------------------------------------------------------------
// Safe-to-Forget (ctx-rent-x Phase 5, CR-09/10/13; spec vault/specs/ccr-safe-to-forget-main.md). A projection is applied
// only when the full output is durable, the open obligation is known and names no omitted line, and every omitted proof
// line is hoisted back. Every refusal sends the whole output, so this can only ever keep MORE than projectToolOutput.
export const PROTECTED_LINE = new RegExp([
  String.raw`\b(?:FAIL\w*|ERROR|Traceback|Exception|fatal|panic)\b`,
  String.raw`\w(?:Error|Exception)\b`, // ValueError:, AssertionError, IOException (review L1)
  String.raw`\b(?:exit|rc|returncode|status)(?:\s*code)?\s*[=:]\s*-?\d+`,
  String.raw`\bverdict\s*[=:]`,
  String.raw`\b(?:PASS|FAIL|OK)\w*\s*[=:]\s*\d+`,
  String.raw`\b\d+\s*/\s*\d+\s*(?:pass|passed|ok|fail|failed)\b`,
  String.raw`^\s*\[[^\]]+ [0-9a-f]{7,40}\]`, // also "[main (root-commit) abc1234]", "[detached HEAD abc1234]" (review L2)
].join('|'), 'i')
export const HOIST_MAX_LINES = 20
export const HOIST_MAX_CHARS = 2000

// Distinctive terms of the obligation text: a token of >= 4 chars that carries a digit, `.`, `_`, `-`, a slash or an inner
// capital (file names, ids, hashes). Plain words are not terms: "the" or "carry" must not pin every output whole.
export function obligationTerms(text: string): string[] {
  const out = new Set<string>()
  for (const t of text.match(/[A-Za-z0-9_][\w.\-\/\\]*[A-Za-z0-9_]/g) ?? []) {
    if (t.length < 4) continue
    if (/[0-9._\-\/\\]/.test(t) || /[a-z][A-Z]/.test(t)) out.add(t.toLowerCase())
    if (out.size >= 200) break
  }
  return [...out]
}

export type ForgetVerdict = { verdict: 'FORGET' | 'KEEP' | 'UNKNOWN'; reason: string; out: string; hoisted: number; named: string[] }

export function safeToForget(text: string, p: Projection, obligation: string | null, durable: boolean): ForgetVerdict {
  const keep = (verdict: 'KEEP' | 'UNKNOWN', reason: string, named: string[] = []): ForgetVerdict =>
    ({ verdict, reason, out: text, hoisted: 0, named })
  if (p.action === 'pass') return keep('KEEP', 'under-budget')
  if (!durable) return keep('KEEP', 'not-durable')
  // A blank obligation (image-only prompt, empty subagent prompt) is as unknown as a missing one (review M1).
  if (obligation === null || !obligation.trim()) return keep('UNKNOWN', 'no-obligation-text')
  // An omitted line is any line of the full text whose trimmed form is not a line of the projection (a line cut at the
  // head/tail boundary counts as omitted: conservative).
  const shown = new Set(p.out.split('\n').map(l => l.trim()))
  const omitted = text.split('\n').filter(l => l.trim() && !shown.has(l.trim()))
  const terms = obligationTerms(obligation)
  const named = terms.filter(t => omitted.some(l => l.toLowerCase().includes(t)))
  if (named.length) return keep('KEEP', 'obligation-named', named.slice(0, 5))
  const proof = omitted.filter(l => PROTECTED_LINE.test(l))
  if (proof.length === 0) return { verdict: 'FORGET', reason: 'safe', out: p.out, hoisted: 0, named: [] }
  const block = proof.join('\n')
  if (proof.length > HOIST_MAX_LINES || block.length > HOIST_MAX_CHARS) return keep('KEEP', 'proof-too-large')
  return { verdict: 'FORGET', reason: 'safe-hoisted', hoisted: proof.length, named: [],
    out: `${p.out}\n[CCR kept these ${proof.length} line(s) from the omitted part: verdicts, failures, exit codes, commits]\n${block}` }
}

// Main-pane projection (Phase 5): lifts `project` to enforce on a main pane with no unit, not a successor (its own rule
// decides), no explicit modes.project, main not off. An incompatible build only observes. Default-on since Amendment A
// (Owner, 2026-11-05, n=10/arm): CCR_MAIN_PROJECT=0 is the off switch; unset or any other value lifts.
// Main loop only: a subagent's shell call keeps its base mode (the n=10 evidence measured no subagent projection; review M1).
export function mainProjectMode(env: string | undefined, projectMode: Mode, hasUnit: boolean, successor: boolean, modes: Modes, compatible: boolean, isAgent = false): Mode {
  if (env === '0' || isAgent || hasUnit || successor || modes.project !== undefined || projectMode === 'off' || modes.main === 'off') return projectMode
  return compatible ? 'enforce' : 'shadow'
}

// A Read or Grep of a projected full output is a page fault: the projection was not enough for that call.
export function projectedFaultPath(stateDir: string, path: unknown): string | null {
  if (!stateDir || typeof path !== 'string' || !path) return null
  const p = path.replace(/\\/g, '/').toLowerCase().replace(/\/+$/, '')
  const root = `${stateDir.replace(/\\/g, '/').toLowerCase().replace(/\/+$/, '')}/tool-results`
  // the store itself (a Grep over every projected output) counts too (review L5)
  return p === root || p.startsWith(`${root}/`) ? path : null
}
