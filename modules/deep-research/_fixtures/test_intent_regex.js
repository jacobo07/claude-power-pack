// Standalone regex coverage check — escaping inside `node -e` mangles
// backslashes. Run as a real file: node test_intent_regex.js
const RESEARCH_INTENT_RE = new RegExp(
  '\\b('
  + 'investiga(?:r|cion)?|investigate'
  + '|research'
  + '|analiza(?:r)?|analyse|analyze'
  + '|compara(?:r)?|compare'
  + '|deep[-\\s]?dive'
  + '|qu[eé]\\s+opciones'
  + '|how\\s+does|how\\s+do'
  + '|mercado\\s+de'
  + '|estado\\s+del\\s+arte'
  + ')\\b',
  'i'
);

const tests = [
  ['investiga las mejores prácticas para servidor', true],
  ['research the topic of distributed databases', true],
  ['compare Paper vs Folia in production scenarios', true],
  ['What is X?', false],
  ['fix this bug in the parser', false],
  ['deep dive into Java GC tuning', true],
  ['analyze the data trends', true],
  ['qué opciones tengo para servidor Java', true],
  ['mercado de prediction markets en 2026', true],
  ['how does Velocity proxy scale', true],
  ['estado del arte de Folia regionized threading', true],
  ['just a regular question', false],
  ['can you help me write a function', false],
];

let pass = 0, fail = 0;
for (const [s, expected] of tests) {
  const got = RESEARCH_INTENT_RE.test(s);
  const ok = got === expected;
  console.log(ok ? '  PASS' : '  FAIL', JSON.stringify(s),
              'expected:', expected, 'got:', got);
  if (ok) pass++; else fail++;
}
console.log('---');
console.log('regex tests:', pass + '/' + (pass + fail), 'passed');
process.exit(fail === 0 ? 0 : 1);
