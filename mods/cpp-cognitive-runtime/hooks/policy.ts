// CCR policy: pure, deterministic decisions. No engine calls here, so every rule is unit-testable
// and the hook layer stays a thin adapter.

export const RUNTIME_VERSION = '0.1.0'

// Claude Code builds whose hook semantics this release was measured against (plan section M1).
// Any other build runs observe-only: receipts, no enforcement.
export const COMPAT = ['2.1.296']

export type Mode = 'enforce' | 'shadow' | 'off'
// main: interactive and undeclared sessions. unit: main sessions that declared a Work Unit.
export type Modes = { subagent: Mode; main: Mode; unit: Mode }
export const DEFAULT_MODES: Modes = { subagent: 'enforce', main: 'shadow', unit: 'enforce' }

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

// The text a subagent reads in place of the full instruction files: the compiled HARD-RULES
// digest (the constitutional kernel, maintained by rule_compiler) plus one line per file it did
// not receive, so a file the task turns out to need is one Read away.
export function subagentInstructions(kernel: string, files: readonly InstructionFileInfo[]): string {
  const index = files
    .map(f => `- ${f.path} (${f.kind}, ${f.content.length} chars)${firstHeading(f.content) ? ` -- ${firstHeading(f.content)}` : ''}`)
    .join('\n')
  return [
    'Instruction files for this subagent were linked by the CPP Cognitive Runtime: the constitutional kernel is below, and',
    'the full files are not loaded. If your task touches one of them, Read it before acting. Hooks and guards still apply in full.',
    '',
    kernel.trim(),
    '',
    'Instruction files available on disk:',
    index,
  ].join('\n')
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

export function pageLines(listing: string, query: string, limit = 40): string {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean)
  const hits = listing.split('\n').filter(l => words.length === 0 || words.some(w => l.toLowerCase().includes(w)))
  return hits.slice(0, limit).join('\n') || '(no matching entries)'
}
