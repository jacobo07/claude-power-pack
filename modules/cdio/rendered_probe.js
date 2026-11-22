// CDIO rendered-page probe (CANDIDATE, warning-only). Evaluated inside a real browser page;
// returns plain JSON for modules/cdio/rendered_checks.py. It measures what the page RENDERS,
// not what its source declares (a structural check cannot see repetition or monotony).
//
// Facts collected, nothing judged here:
//   art       every visible <img> under <main> (or <body>) and every inline svg[data-art-kind]:
//             file stem (hash suffixes dropped), object-position, rendered size, svg?, data-art-kind
//   sections  top-level sections: ground luminance (first opaque background up the tree),
//             column count of the first child grid, whether the section shows media
//   declaresProvenance  true when the page uses the data-art-kind convention at all
(() => {
  const root = document.querySelector('main') || document.body;
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden';
  };
  const stem = (src) => (src || '').split('#')[0].split('?')[0].split('/').pop().split('.')[0];

  const art = [];
  for (const img of root.querySelectorAll('img')) {
    if (!visible(img)) continue;
    const src = img.currentSrc || img.src || '';
    const r = img.getBoundingClientRect();
    art.push({
      file: stem(src),
      position: getComputedStyle(img).objectPosition,
      w: Math.round(r.width),
      h: Math.round(r.height),
      svg: /\.svg($|[?#])/i.test(src),
      kind: img.getAttribute('data-art-kind'),
    });
  }
  for (const svg of root.querySelectorAll('svg[data-art-kind]')) {
    if (!visible(svg)) continue;
    const r = svg.getBoundingClientRect();
    art.push({
      file: `inline:${svg.getAttribute('class') || 'svg'}`,
      position: 'n/a',
      w: Math.round(r.width),
      h: Math.round(r.height),
      svg: true,
      kind: svg.getAttribute('data-art-kind'),
    });
  }

  const rgb = (css) => (css.match(/[\d.]+/g) || []).map(Number);
  const ground = (el) => {
    for (let n = el; n; n = n.parentElement) {
      const c = rgb(getComputedStyle(n).backgroundColor);
      if (c.length === 3 || (c.length >= 4 && c[3] > 0)) return c.slice(0, 3);
    }
    return [255, 255, 255];
  };
  const luminance = ([r, g, b]) => {
    const f = (v) => ((v /= 255) <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  let blocks = [...root.querySelectorAll('section')].filter((s) => !s.parentElement.closest('section') && visible(s));
  if (blocks.length < 2) blocks = [...root.children].filter(visible);
  const sections = blocks.map((s, i) => {
    const first = s.firstElementChild || s;
    const st = getComputedStyle(first);
    const cols = st.display.includes('grid') ? st.gridTemplateColumns.split(' ').filter(Boolean).length : 1;
    return {
      label: s.getAttribute('aria-labelledby') || s.id || `${s.tagName.toLowerCase()}#${i}`,
      luminance: Number(luminance(ground(s)).toFixed(3)),
      cols,
      media: !!s.querySelector('img, picture, video, svg[data-art-kind]'),
      height: Math.round(s.getBoundingClientRect().height),
    };
  });

  return {
    url: location.href,
    viewport: window.innerWidth,
    declaresProvenance: !!document.querySelector('[data-art-kind]'),
    art,
    sections,
  };
})()
