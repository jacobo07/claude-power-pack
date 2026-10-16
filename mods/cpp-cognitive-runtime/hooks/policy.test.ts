import { expect, test } from 'claude-code/testing'
import {
  advisoryBytes, decideSubagentAttachment, decideUnitAttachment, decideUnitSection, decideUnitTool, linkInstructionFiles,
  carryAdvice, gcKeptSet, imageDims, imagesByUse, imageTokens, pageLines, parseWorkUnit, projectToolOutput, repoKey, rowFacts,
  subagentInstructions, boundaryForecast, parseClassModel, stepAnomaly,
} from './policy'
import { isPlannerType } from './register'

test('the spawn receipt flags a planner fan-out agent and no other type', () => {
  expect(isPlannerType('gsd-planner')).toBe(true)
  expect(isPlannerType('gsd-plan-checker')).toBe(true)
  expect(isPlannerType('gsd-executor')).toBe(false)
  expect(isPlannerType('gsd-planner-extra')).toBe(false)
  expect(isPlannerType(undefined)).toBe(false)
})

// The madzia-worker model tools/ccr_pgo.py built from post-fix attempts a6-a8 (2026-10-12).
const MADZIA = JSON.stringify({ cls: 'madzia-worker', n: 3, floor: { p50: 18938, p80: 19049.6 }, calls: { p50: 25, p80: 28.6 },
  slope: { p50: 1304.9, p80: 1453.9 }, step: { p50: 998, p95: 3621.3 } })

test('a class model is accepted only for its own class and with every field; otherwise there is no model', () => {
  expect(parseClassModel(MADZIA, 'madzia-worker')?.n).toBe(3)
  expect(parseClassModel(MADZIA, 'lobby')).toBe(null)
  expect(parseClassModel('{"cls":"madzia-worker","n":3}', 'madzia-worker')).toBe(null)
  expect(parseClassModel('not json', 'madzia-worker')).toBe(null)
  expect(parseClassModel(null, 'madzia-worker')).toBe(null)
})

test('the boundary forecast is floor rent plus implied carry, and P80 is above P50', () => {
  const f = boundaryForecast(parseClassModel(MADZIA, 'madzia-worker')!)
  expect(f.p50).toBe(Math.round(25 * 18938 + 1304.9 * 25 * 24 / 2))
  expect(f.p80 > f.p50).toBe(true)
})

test('M4: the call-2 runs-tree step is an anomaly costing ~0.3M if it rides; a normal step is not', () => {
  const m = parseClassModel(MADZIA, 'madzia-worker')!
  const dump = stepAnomaly(11213, 2, m)
  expect(dump.anomaly).toBe(true)
  expect(dump.costIfRides > 290000).toBe(true)
  expect(stepAnomaly(998, 5, m).anomaly).toBe(false)
})

// M4 shape: a recursive runs-tree listing (call 2 of a Madzia attempt), held fixed while the estate grows.
const runsTree = (attempts: number) => {
  const out: string[] = []
  for (let a = 1; a <= attempts; a++) for (const f of ['receipt.json', 'review.md', 'shot-01.png', 'shot-02.png', 'stdout.log'])
    out.push(`C:\\Users\\User\\Desktop\\KSR\\runs\\phase2\\a${a}\\${f}`)
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
  expect(p.out.includes('5\tC:/Users/User/Desktop/KSR/runs/phase2/a1')).toBe(true)
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
