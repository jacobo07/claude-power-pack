import { expect, test } from 'claude-code/testing'
import { advisoryBytes, decideSubagentAttachment, linkInstructionFiles, pageLines, repoKey, subagentInstructions } from './policy'

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
