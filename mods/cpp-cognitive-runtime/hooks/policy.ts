// CCR policy: pure, deterministic decisions. No engine calls here, so every rule is unit-testable
// and the hook layer stays a thin adapter.

export const RUNTIME_VERSION = '0.1.0'

// Claude Code builds whose hook semantics this release was measured against (plan section M1).
// Any other build runs observe-only: receipts, no enforcement.
export const COMPAT = ['2.1.296']

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

// Policy generation (A1 version truth): a short sha256 of the effective modes and the kernel text this process read.
// Two sessions with the same policyGen made the same decisions from the same inputs, whatever release they came from.
export async function policyGen(eff: Record<Surface, Mode>, kernel: string | null): Promise<string> {
  const text = JSON.stringify([eff.main, eff.subagent, eff.unit, eff.project]) + '\n' + (kernel ?? '')
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
// thinking block no text field shows (Madzia p4p2a3: 1.7K visible vs 129K signature chars over 38 blocks).
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
// floor + rehydration. Measured on Madzia d6343597: floor 14.4K, carry grew ~2.4K/call to 60.8K, images 16.8 %
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
