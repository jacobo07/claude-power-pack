import { expect, test } from 'claude-code/testing'
import {
  advisoryBytes, decideSubagentAttachment, decideUnitAttachment, decideUnitSection, decideUnitTool, linkInstructionFiles,
  carryAdvice, gcKeptSet, imageDims, imagesByUse, imageTokens, pageLines, parseWorkUnit, projectToolOutput, repoKey, rowFacts,
  subagentInstructions, boundaryForecast, parseClassModel, stepAnomaly, mainCanaryMode, successorMode, DEFAULT_MODES,
  safeToForget, obligationTerms, mainProjectMode, projectedFaultPath, HOIST_MAX_LINES, collapseDeferredNames, deferredNamesMode,
} from './policy'

// ICC W1: deferred tool names collapse to one line per server; built-ins and prose stay; no mcp name = no change.
const DEFERRED = ['The following deferred tools are now available via ToolSearch.', 'CronCreate', 'WebSearch',
  ...Array.from({ length: 30 }, (_, i) => `mcp__vercel__list_resource_number_${i}`),
  ...Array.from({ length: 10 }, (_, i) => `mcp__claude_ai_Gmail__message_operation_${i}`)].join('\n')
test('deferred names: mcp tools collapse per server with count + ToolSearch hint, built-ins and prose stay', () => {
  const out = collapseDeferredNames(DEFERRED)!
  expect(out).toContain('CronCreate')
  expect(out).toContain('WebSearch')
  expect(out).toContain('The following deferred tools')
  expect(out).toContain('mcp__vercel__* (30 deferred tools')
  expect(out).toContain('mcp__claude_ai_Gmail__* (10 deferred tools')
  expect(out).not.toContain('list_resource_number_7')
  expect(out.length).toBeLessThan(DEFERRED.length)
})
test('deferred names: nothing to collapse, or no saving, keeps stock text', () => {
  expect(collapseDeferredNames('CronCreate\nWebSearch')).toBeNull()
  expect(collapseDeferredNames('mcp__a__b')).toBeNull() // the summary line is longer than the one name
})
test('deferred names mode: shadow by default, enforce only when asked on an enforcing canary, kill switch wins', () => {
  expect(deferredNamesMode(undefined, 'enforce')).toBe('shadow')
  expect(deferredNamesMode('enforce', 'enforce')).toBe('enforce')
  expect(deferredNamesMode('enforce', 'shadow')).toBe('shadow')
  expect(deferredNamesMode('0', 'enforce')).toBe('off')
  expect(deferredNamesMode('enforce', 'off')).toBe('off')
})

// Safe-to-Forget (Phase 5; spec vault/specs/ccr-safe-to-forget-main.md). A 600-line log with one buried verdict line.
const LOG = (buried: string) => {
  const rows: string[] = []
  for (let i = 0; i < 600; i++) rows.push(i === 300 ? buried : `step ${i} processed record ok ${'.'.repeat(40)}`)
  return rows.join('\n')
}

test('safe-to-forget: a buried verdict line is hoisted back into the projection (FORGET safe-hoisted)', () => {
  const text = LOG('FLOOR verdict=MATERIAL_RISE exit=1 reason=material_rise')
  const p = projectToolOutput(text, '/s/full.txt', 8000)
  expect(p.out.includes('verdict=MATERIAL_RISE')).toBe(false) // the bare projection loses it
  const f = safeToForget(text, p, 'what did the gate say?', true)
  expect(f.verdict).toBe('FORGET')
  expect(f.reason).toBe('safe-hoisted')
  expect(f.hoisted).toBe(1)
  expect(f.out.includes('FLOOR verdict=MATERIAL_RISE exit=1')).toBe(true)
  expect(f.out.length < text.length / 2).toBe(true)
})

test('safe-to-forget: nothing protected and nothing named -> FORGET with the plain projection', () => {
  const text = LOG('step 300 processed record ok')
  const p = projectToolOutput(text, '/s/full.txt', 8000)
  const f = safeToForget(text, p, 'carry on', true)
  expect(f.verdict).toBe('FORGET')
  expect(f.reason).toBe('safe')
  expect(f.out).toBe(p.out)
})

test('safe-to-forget refuses: not durable, no obligation text, a named omitted line, too much proof, under budget', () => {
  const text = LOG('wrote vault/programs/ctx-rent-x/phase5.json')
  const p = projectToolOutput(text, '/s/full.txt', 8000)
  expect(safeToForget(text, p, 'x', false)).toEqual({ verdict: 'KEEP', reason: 'not-durable', out: text, hoisted: 0, named: [] })
  const u = safeToForget(text, p, null, true)
  expect(u.verdict).toBe('UNKNOWN'); expect(u.reason).toBe('no-obligation-text'); expect(u.out).toBe(text)
  const n = safeToForget(text, p, 'did it write vault/programs/ctx-rent-x/phase5.json?', true)
  expect(n.verdict).toBe('KEEP'); expect(n.reason).toBe('obligation-named'); expect(n.out).toBe(text)
  expect(n.named).toEqual(['vault/programs/ctx-rent-x/phase5.json'])
  const many = Array.from({ length: 600 }, (_, i) => (i > 100 && i < 100 + HOIST_MAX_LINES + 10 ? `FAIL case ${i}` : `ok ${i} ${'.'.repeat(40)}`)).join('\n')
  const pm = projectToolOutput(many, '/s/full.txt', 8000)
  const k = safeToForget(many, pm, 'run it', true)
  expect(k.verdict).toBe('KEEP'); expect(k.reason).toBe('proof-too-large'); expect(k.out).toBe(many)
  const small = projectToolOutput('ok', '/s/t.txt')
  expect(safeToForget('ok', small, 'x', true).reason).toBe('under-budget')
  // review M1: a blank obligation is unknown, never "nothing named"
  for (const blank of ['', '   \n ']) {
    const b = safeToForget(text, p, blank, true)
    expect(b.verdict).toBe('UNKNOWN'); expect(b.out).toBe(text)
  }
})

test('safe-to-forget: exception-type and root-commit lines are proof; a listing projection is judged too', () => {
  for (const line of ['ValueError: shard 19 checksum mismatch', 'AssertionError', '[main (root-commit) 953af53] init', '[detached HEAD abc1234] wip']) {
    const text = LOG(line)
    const f = safeToForget(text, projectToolOutput(text, '/s/full.txt', 8000), 'go', true)
    expect(f.reason).toBe('safe-hoisted'); expect(f.out.includes(line)).toBe(true)
  }
  const tree = runsTree(400)
  const pl = projectToolOutput(tree, '/s/full.txt', 8000)
  expect(safeToForget(tree, pl, 'list the runs', true).verdict).toBe('FORGET')
  expect(safeToForget(tree, pl, 'look at runs\\phase2\\a17\\review.md', true).reason).toBe('obligation-named')
})

test('obligation terms are distinctive tokens only: ids, paths, hashes, camelCase; never plain words', () => {
  expect(obligationTerms('carry on with the plan please')).toEqual([])
  expect(obligationTerms('fix CR-09 in done_gate.py at 953af539 via safeToForget')).toEqual(['cr-09', 'done_gate.py', '953af539', 'safetoforget'])
})

test('main projection mode: default-on (Amendment A), CCR_MAIN_PROJECT=0 is the off switch; enforces only on a compatible unit-less non-successor main pane', () => {
  const m = { ...DEFAULT_MODES }
  expect(mainProjectMode('1', 'shadow', false, false, m, true)).toBe('enforce')
  expect(mainProjectMode(undefined, 'shadow', false, false, m, true)).toBe('enforce') // unset = on since Amendment A
  expect(mainProjectMode('', 'shadow', false, false, m, true)).toBe('enforce')
  expect(mainProjectMode('0', 'shadow', false, false, m, true)).toBe('shadow') // the off switch keeps today's mode
  expect(mainProjectMode('0', 'enforce', false, false, m, true)).toBe('enforce')
  expect(mainProjectMode(undefined, 'shadow', false, false, m, false)).toBe('shadow') // default-on still only observes on an incompatible build
  expect(mainProjectMode(undefined, 'shadow', false, true, m, true)).toBe('shadow') // nor touches a successor
  expect(mainProjectMode(undefined, 'shadow', true, false, m, true)).toBe('shadow') // nor a unit
  expect(mainProjectMode(undefined, 'shadow', false, false, m, true, true)).toBe('shadow') // nor a subagent's shell call (review M1)
  expect(mainProjectMode('1', 'shadow', false, false, m, true, true)).toBe('shadow') // not even with the env on
  expect(mainProjectMode(undefined, 'shadow', false, false, m, true, false)).toBe('enforce') // the main loop is lifted
  expect(mainProjectMode('1', 'enforce', true, false, m, true)).toBe('enforce') // unit: its own rule
  expect(mainProjectMode('1', 'shadow', false, true, m, true)).toBe('shadow') // successor: its own rule
  expect(mainProjectMode('1', 'shadow', false, false, m, false)).toBe('shadow') // incompatible build observes
  expect(mainProjectMode('1', 'shadow', false, false, { ...m, project: 'shadow' }, true)).toBe('shadow') // explicit modes.project wins
  expect(mainProjectMode('1', 'off', false, false, { ...m, main: 'off' }, true)).toBe('off')
  expect(mainProjectMode('1', 'shadow', false, false, { ...m, main: 'off' }, true)).toBe('shadow') // main off alone blocks the lift (review L3)
})

test('a Read/Grep of a projected full output is a page fault; any other path is not', () => {
  expect(projectedFaultPath('C:/Users/U/.claude/ccr/state', 'C:\\Users\\U\\.claude\\ccr\\state\\tool-results\\s1\\t1.txt')).toBe('C:\\Users\\U\\.claude\\ccr\\state\\tool-results\\s1\\t1.txt')
  expect(projectedFaultPath('C:/Users/U/.claude/ccr/state', 'C:/Users/U/.claude/ccr/state/tool-results')).toBe('C:/Users/U/.claude/ccr/state/tool-results') // review L5
  expect(projectedFaultPath('C:/Users/U/.claude/ccr/state', 'C:/Users/U/.claude/ccr/state/tool-results-old/x.txt')).toBe(null)
  expect(projectedFaultPath('C:/Users/U/.claude/ccr/state', 'C:/repo/tool-results/x.txt')).toBe(null)
  expect(projectedFaultPath('', 'C:/Users/U/.claude/ccr/state/tool-results/x.txt')).toBe(null)
  expect(projectedFaultPath('C:/s', undefined)).toBe(null)
})
// isPlannerType (dc4bf2b4) is not in the live release 0.1.0-b15bfc3d that 35776051 synced register.ts to; its test lives
// with that branch. Importing it here made this whole file fail to load, so no test in it ran.

// The worker-a model tools/ccr_pgo.py built from post-fix attempts a6-a8 (2026-10-12).
const WORKER_A = JSON.stringify({ cls: 'worker-a', n: 3, floor: { p50: 18938, p80: 19049.6 }, calls: { p50: 25, p80: 28.6 },
  slope: { p50: 1304.9, p80: 1453.9 }, step: { p50: 998, p95: 3621.3 } })

test('a class model is accepted only for its own class and with every field; otherwise there is no model', () => {
  expect(parseClassModel(WORKER_A, 'worker-a')?.n).toBe(3)
  expect(parseClassModel(WORKER_A, 'lobby')).toBe(null)
  expect(parseClassModel('{"cls":"worker-a","n":3}', 'worker-a')).toBe(null)
  expect(parseClassModel('not json', 'worker-a')).toBe(null)
  expect(parseClassModel(null, 'worker-a')).toBe(null)
})

test('the boundary forecast is floor rent plus implied carry, and P80 is above P50', () => {
  const f = boundaryForecast(parseClassModel(WORKER_A, 'worker-a')!)
  expect(f.p50).toBe(Math.round(25 * 18938 + 1304.9 * 25 * 24 / 2))
  expect(f.p80 > f.p50).toBe(true)
})

test('M4: the call-2 runs-tree step is an anomaly costing ~0.3M if it rides; a normal step is not', () => {
  const m = parseClassModel(WORKER_A, 'worker-a')!
  const dump = stepAnomaly(11213, 2, m)
  expect(dump.anomaly).toBe(true)
  expect(dump.costIfRides > 290000).toBe(true)
  expect(stepAnomaly(998, 5, m).anomaly).toBe(false)
})

// M4 shape: a recursive runs-tree listing (call 2 of a Worker-A attempt), held fixed while the estate grows.
const runsTree = (attempts: number) => {
  const out: string[] = []
  for (let a = 1; a <= attempts; a++) for (const f of ['receipt.json', 'review.md', 'shot-01.png', 'shot-02.png', 'stdout.log'])
    out.push(`C:\\Users\\dev\\Desktop\\proj\\runs\\phase2\\a${a}\\${f}`)
  return out.join('\n')
}

test('a small shell result passes untouched (no projection below the budget)', () => {
  const p = projectToolOutput('ok\n3 files changed', '/s/t.txt')
  expect(p.action).toBe('pass')
  expect(p.out).toBe('ok\n3 files changed')
})

test('a large listing projects to per-directory counts plus the full-output path, inside the budget', () => {
  const text = runsTree(400)
  const p = projectToolOutput(text, '/s/full.txt', 8000)
  expect(p.action).toBe('project')
  expect(p.kind).toBe('listing')
  expect(p.out.length <= 8000).toBe(true)
  expect(p.out.includes('/s/full.txt')).toBe(true)
  expect(p.out.includes('5\tC:/Users/dev/Desktop/proj/runs/phase2/a1')).toBe(true)
})

test('M4 elasticity: model-facing size stays bounded while the runs estate grows 10 -> 10,000 attempts', () => {
  const sizes = [10, 100, 1000, 10000].map(n => projectToolOutput(runsTree(n), '/s/full.txt', 8000).out.length)
  for (const s of sizes) expect(s <= 8000).toBe(true)
  // 1,000x more estate, the projection grows by less than the budget itself (raw grows ~1000x)
  expect(sizes[3] - sizes[1] <= 8000).toBe(true)
  expect(runsTree(10000).length > 100 * 8000).toBe(true)
})

test('non-listing text keeps head and tail and names how much was omitted', () => {
  const text = 'HEAD-MARK\n' + 'x'.repeat(50000) + '\nTAIL-MARK'
  const p = projectToolOutput(text, '/s/full.txt', 8000)
  expect(p.kind).toBe('text')
  expect(p.out.includes('HEAD-MARK')).toBe(true)
  expect(p.out.includes('TAIL-MARK')).toBe(true)
  expect(p.out.includes('chars omitted')).toBe(true)
  expect(p.out.length <= 8000).toBe(true)
})

const B = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
const b64 = (bytes: number[]) => {
  let s = ''
  for (let i = 0; i < bytes.length; i += 3) {
    const n = (bytes[i] << 16) | ((bytes[i + 1] ?? 0) << 8) | (bytes[i + 2] ?? 0)
    s += B[(n >> 18) & 63] + B[(n >> 12) & 63] + (i + 1 < bytes.length ? B[(n >> 6) & 63] : '=') + (i + 2 < bytes.length ? B[n & 63] : '=')
  }
  return s
}
const be32 = (v: number) => [(v >>> 24) & 255, (v >>> 16) & 255, (v >>> 8) & 255, v & 255]
const png = (w: number, h: number) => b64([0x89, 0x50, 0x4e, 0x47, 13, 10, 26, 10, 0, 0, 0, 13, 0x49, 0x48, 0x44, 0x52, ...be32(w), ...be32(h), 8, 6, 0, 0, 0])
// JPEG with an APP0 segment before SOF0, so the walker must skip a segment to reach the size
const jpeg = (w: number, h: number) => b64([0xff, 0xd8, 0xff, 0xe0, 0, 4, 0, 0, 0xff, 0xc0, 0, 11, 8, h >> 8, h & 255, w >> 8, w & 255, 3, 0, 0, 0])

test('image dimensions are read from PNG and JPEG headers; anything else is unknown, not zero', () => {
  expect(imageDims(png(1920, 1080))).toEqual({ w: 1920, h: 1080 })
  expect(imageDims(jpeg(640, 480))).toEqual({ w: 640, h: 480 })
  expect(imageDims(b64([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]))).toBe(null)
})

test('image tokens are w*h/750 of the block as sent, with no megapixel cap (calibrated on Opus 5.5)', () => {
  expect(imageTokens(750, 100)).toBe(100)
  expect(imageTokens(2000, 1278)).toBe(3408) // measured ~3,420 from next-call usage
})

test('rotate advice fires once carry above the floor reaches the floor, and splits image from text carry', () => {
  expect(carryAdvice(14400, 28000, 3000).rotate).toBe(false)
  const a = carryAdvice(14400, 28800, 3000)
  expect(a.rotate).toBe(true)
  expect(a.carry).toBe(14400)
  expect(a.textCarry).toBe(11400)
  expect(carryAdvice(0, 50000, 0).rotate).toBe(false) // no floor measured yet: no advice
})

test('pixel GC rebuilds messages before the window with a tombstone and keeps the window whole', () => {
  // Arrange: an image read early, then a later read still in the live window
  const img = { type: 'image', source: { type: 'base64', media_type: 'image/png', data: png(1500, 1000) } }
  const images = imagesByUse([{ type: 'tool_result', tool_use_id: 'u1', content: [img] }])
  const use = (id: string) => ({ role: 'assistant' as const, text: '', toolUses: [{ tool_use_id: id, tool: 'Read', input: {} }], handle: `a-${id}` })
  const res = (id: string) => ({ role: 'user' as const, text: '', toolUses: [], toolResults: [{ tool_use_id: id, text: '', isError: false }], handle: `r-${id}` })
  const msgs = [{ role: 'user' as const, text: 'go', toolUses: [], handle: 'p' }, use('u1'), res('u1'), use('u2'), res('u2')]
  // Act
  const plan = gcKeptSet(msgs, images, 2)
  // Assert: the window moved back off the tool result, so u2's call and result stay whole together
  expect(plan.keptWhole).toBe(2)
  expect(plan.evicted.map(i => i.tok)).toEqual([2000])
  expect(plan.messages![2].handle).toBeUndefined()
  expect(plan.messages![2].toolResults![0].text).toContain('the read succeeded')
  expect(plan.messages![3].handle).toBe('a-u2')
  expect(plan.messages![4].handle).toBe('r-u2')
})

test('pixel GC has no plan when nothing before the window carries an image', () => {
  const msgs = [{ role: 'user' as const, text: 'go', toolUses: [], handle: 'p' }]
  expect(gcKeptSet(msgs, new Map(), 2).messages).toBe(null)
})

test('a tool_result row is split into text bytes and hashed images; the same bytes hash the same', () => {
  const img = { type: 'image', source: { type: 'base64', media_type: 'image/png', data: png(800, 600) } }
  const f = rowFacts([{ type: 'tool_result', tool_use_id: 't1', content: [{ type: 'text', text: 'abcd' }, img, img] }])
  expect(f.text).toBe(4)
  expect(f.images.length).toBe(2)
  expect(f.images[0].hash).toBe(f.images[1].hash)
  expect(f.images[0].tok).toBe(640)
  expect(rowFacts([{ type: 'text', text: 'hello' }]).images).toEqual([])
})

test('thinking is counted apart from text, and its sealed signature bytes are counted, not dropped', () => {
  const f = rowFacts([{ type: 'thinking', thinking: 'abc', signature: 'x'.repeat(40) }, { type: 'redacted_thinking', data: 'y'.repeat(7) }, { type: 'text', text: 'hi' }])
  expect(f.thinking).toBe(3)
  expect(f.sealed).toBe(47)
  expect(f.text).toBe(2)
})

const file = (path: string, kind = 'user', content = '# Title\nbody') => ({ path, kind, content })

test('a rule file with no Work-Class match is unlinked; the same file is linked when the prompt matches', () => {
  // Arrange
  const files = [file('C:/u/.claude/rules/seo-geo-corpus-methodology.md')]
  // Act
  const cold = linkInstructionFiles(files, 'fix the build script')
  const warm = linkInstructionFiles(files, 'plan the SEO audit for the landing')
  // Assert
  expect(cold[0].keep).toBe(false)
  expect(cold[0].reason).toBe('unlinked')
  expect(warm[0].keep).toBe(true)
  expect(warm[0].reason).toBe('work-class')
})

test('CLAUDE.md files, index rules, managed files and untriaged files are always linked', () => {
  const d = linkInstructionFiles([
    file('C:/u/.claude/CLAUDE.md'),
    file('C:/u/.claude/rules/skill-rule-index.md'),
    file('C:/org/policy.md', 'managed'),
    file('C:/u/.claude/rules/brand-new-rule.md'),
  ], '')
  expect(d.map(x => x.keep)).toEqual([true, true, true, true])
  expect(d.map(x => x.reason)).toEqual(['always', 'always', 'managed', 'untriaged'])
})

test('subagent instructions are replaced by kernel + index, and every file is named in the index', () => {
  const files = [file('C:/u/.claude/CLAUDE.md', 'user', '# Global\nx'), file('C:/repo/CLAUDE.md', 'project', 'no heading')]
  const d = decideSubagentAttachment('instructions', 'Explore', '# HARD-RULES DIGEST\nrow', files)
  expect(d.action).toBe('replace')
  expect(d.text).toContain('# HARD-RULES DIGEST')
  expect(d.text).toContain('C:/u/.claude/CLAUDE.md (user, 10 chars) -- Global')
  expect(d.text).toContain('C:/repo/CLAUDE.md (project')
})

test('without a kernel, without the file list, or with a managed file present, subagent instructions are kept', () => {
  const files = [file('C:/u/.claude/CLAUDE.md')]
  expect(decideSubagentAttachment('instructions', 'Explore', null, files).action).toBe('keep')
  expect(decideSubagentAttachment('instructions', 'Explore', 'k', null).action).toBe('keep')
  expect(decideSubagentAttachment('instructions', 'Explore', 'k', [...files, file('C:/org/p.md', 'managed')]).action).toBe('keep')
})

test('the skill listing is dropped for agents that cannot run skills and kept for those that can', () => {
  expect(decideSubagentAttachment('skill_listing', 'Explore', 'k', []).action).toBe('drop')
  expect(decideSubagentAttachment('skill_listing', undefined, 'k', []).action).toBe('drop')
  expect(decideSubagentAttachment('skill_listing', 'general-purpose', 'k', []).action).toBe('keep')
  expect(decideSubagentAttachment('environment', 'Explore', 'k', []).action).toBe('keep')
})

test('advisory bytes count self-declared advisory paragraphs and never a paragraph that blocks', () => {
  const advisory = 'SKILL ADVISOR (advisory only): consider x'
  const blocking = 'Guard (advisory header) -- this call is BLOCKED until y'
  expect(advisoryBytes(`${advisory}\n\nplain text`)).toBe(advisory.length)
  expect(advisoryBytes(blocking)).toBe(0)
  const selfLabelled = 'Cross-project baseline (advisory — never blocks): seen in 49 projects'
  expect(advisoryBytes(selfLabelled)).toBe(selfLabelled.length)
  expect(advisoryBytes(`${selfLabelled}; this call is denied`)).toBe(0)
})

test('repo keys are stable, case- and separator-insensitive, and carry no path text', () => {
  const a = repoKey('C:\\Users\\U\\Repo')
  expect(a).toBe(repoKey('c:/users/u/repo'))
  expect(a).not.toBe(repoKey('C:/Users/U/Other'))
  expect(a).toMatch(/^[0-9a-f]{8}$/)
  expect(repoKey(null)).toBe(repoKey('no-repo'))
})

test('page lines return matching listing entries and say so when nothing matches', () => {
  const listing = '- pdf: read pdfs\n- docx: word files\n- xlsx: sheets'
  expect(pageLines(listing, 'word')).toBe('- docx: word files')
  expect(pageLines(listing, 'zzz')).toBe('(no matching entries)')
  expect(subagentInstructions('k', []).length).toBeGreaterThan(0)
})

test('a work unit is accepted only for a known class; anything else means no unit (stock context)', () => {
  // Arrange / Act / Assert
  expect(parseWorkUnit('{"class":"bounded-code-worker","id":"p4p2a1"}')).toEqual({ cls: 'bounded-code-worker', id: 'p4p2a1' })
  expect(parseWorkUnit('{"class":"root-shell"}')).toBe(null)
  expect(parseWorkUnit('not json')).toBe(null)
  expect(parseWorkUnit(null)).toBe(null)
  expect(parseWorkUnit('{"id":"x"}')).toBe(null)
})

test('a unit defers tools outside its class closure and keeps those inside, and the page tool always', () => {
  const worker = { cls: 'bounded-code-worker', id: '' }
  const reviewer = { cls: 'read-only-reviewer', id: '' }
  expect(decideUnitTool('Agent', worker)).toBe('defer')
  expect(decideUnitTool('WebFetch', worker)).toBe('defer')
  expect(decideUnitTool('Edit', worker)).toBe('keep')
  expect(decideUnitTool('ToolSearch', worker)).toBe('keep')
  expect(decideUnitTool('Edit', reviewer)).toBe('defer')
  expect(decideUnitTool('Read', reviewer)).toBe('keep')
  expect(decideUnitTool('mcp__cpp-cognitive-runtime__page', reviewer)).toBe('keep')
})

test('a unit drops listings it cannot act on, replaces instructions with kernel + index, keeps the rest', () => {
  const files = [file('C:/u/.claude/CLAUDE.md', 'user', '# Global\nx')]
  expect(decideUnitAttachment('skill_listing', 'k', files).action).toBe('drop')
  expect(decideUnitAttachment('agent_listing_delta', 'k', files).action).toBe('drop')
  expect(decideUnitAttachment('mcp_instructions_delta', 'k', files).action).toBe('drop')
  const ins = decideUnitAttachment('instructions', '# HARD-RULES DIGEST', files)
  expect(ins.action).toBe('replace')
  expect(ins.text).toContain('C:/u/.claude/CLAUDE.md')
  // controls: no kernel or a managed file keeps the instructions; unlisted attachments are untouched
  expect(decideUnitAttachment('instructions', null, files).action).toBe('keep')
  expect(decideUnitAttachment('instructions', 'k', [...files, file('C:/org/p.md', 'managed')]).action).toBe('keep')
  expect(decideUnitAttachment('deferred_tools_delta', 'k', files).action).toBe('keep')
  expect(decideUnitAttachment('hook_additional_context', 'k', files).action).toBe('keep')
})

test('a unit leaves the memory section out and keeps every other section', () => {
  expect(decideUnitSection('memory').action).toBe('drop')
  expect(decideUnitSection('env_info_simple').action).toBe('keep')
})

test('main-lean canary: default-on on an interactive, unit-less session; CCR_MAIN_CANARY=0 opts out', () => {
  const m = { ...DEFAULT_MODES }
  expect(mainCanaryMode('1', true, false, m, true)).toBe('enforce')
  expect(mainCanaryMode(undefined, true, false, m, true)).toBe('enforce')
  expect(mainCanaryMode(undefined, false, false, m, true)).toBe('off')
  expect(mainCanaryMode(undefined, true, true, m, true)).toBe('off')
  expect(mainCanaryMode('0', true, false, m, true)).toBe('off')
  expect(mainCanaryMode('true', true, false, m, true)).toBe('off')
  expect(mainCanaryMode('1', false, false, m, true)).toBe('off')
  expect(mainCanaryMode('1', true, true, m, true)).toBe('off')
})

test('main-lean canary: an incompatible build only observes, and the main kill switch wins', () => {
  expect(mainCanaryMode('1', true, false, { ...DEFAULT_MODES }, false)).toBe('shadow')
  expect(mainCanaryMode('1', true, false, { ...DEFAULT_MODES, main: 'off' }, true)).toBe('off')
})

// GPF-L1 2026-11-02: with the main canary default-on (L8), the old gate `canary === 'off' ? successor : 'off'` never let a
// /kresume successor activate, so resolveFrontier never ran (laptop smoke S1, real pane fd4ffce8: marker:true mode:"off").
test('a /kresume successor activates under the default-on main canary and keeps the main mode; no marker stays off', () => {
  const m = { ...DEFAULT_MODES }
  const kresume = '<command-name>/kresume</command-name>'
  expect(successorMode('enforce', kresume, undefined, true, false, m, true)).toBe('enforce')
  expect(successorMode('shadow', kresume, undefined, true, false, m, false)).toBe('shadow')
  expect(successorMode('off', kresume, undefined, true, false, m, true)).toBe('enforce')
  expect(successorMode('enforce', 'reply OK', undefined, true, false, m, true)).toBe('off')
  expect(successorMode('enforce', kresume, '0', true, false, m, true)).toBe('off')
  expect(successorMode('enforce', kresume, undefined, true, true, m, true)).toBe('off')
  expect(successorMode('enforce', kresume, undefined, false, false, m, true)).toBe('off')
})
