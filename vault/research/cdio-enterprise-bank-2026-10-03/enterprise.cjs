// Enterprise-systematic reference bank: density + structure of the primary data table,
// plus the controls and actions on the same page. Usage: node enterprise.cjs <outdir> <name=url>...
// Every colour goes through a canvas so oklch/lab come back as sRGB bytes.
const { chromium } = require("@playwright/test");
const fs = require("fs");
const path = require("path");

const OUT = process.argv[2];
// Each target is name=url or name=url|css-selector-of-the-component-table.
const TARGETS = process.argv.slice(3).map((a) => { const i = a.indexOf("="); const [u, sel] = a.slice(i + 1).split("|"); return [a.slice(0, i), u, sel || null]; });

function inPage(SEL) {
  const cv = document.createElement("canvas"); cv.width = cv.height = 1;
  const cx = cv.getContext("2d", { willReadFrequently: true });
  const rgba = (s) => { cx.clearRect(0, 0, 1, 1); cx.fillStyle = "rgba(0,0,0,0)"; cx.fillStyle = s; cx.fillRect(0, 0, 1, 1); const d = cx.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; };
  const over = (fg, bg) => [0, 1, 2].map((i) => fg[i] * fg[3] + bg[i] * (1 - fg[3])).concat(1);
  const lum = (c) => { const f = (x) => { x /= 255; return x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  const ratio = (a, b) => { const [h, l] = [lum(a), lum(b)].sort((x, y) => y - x); return +((h + 0.05) / (l + 0.05)).toFixed(2); };
  const hex = (c) => "#" + c.slice(0, 3).map((x) => Math.round(x).toString(16).padStart(2, "0")).join("");
  const sat = (c) => { const [r, g, b] = c.slice(0, 3).map((x) => x / 255); const mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2; return mx === mn ? 0 : (mx - mn) / (1 - Math.abs(2 * l - 1)); };
  const median = (xs) => { const s = xs.filter((x) => Number.isFinite(x)).sort((a, b) => a - b); return s.length ? s[Math.floor(s.length / 2)] : null; };
  function effBg(el) {
    const stack = [];
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      const c = rgba(getComputedStyle(n).backgroundColor);
      if (c[3] > 0) { stack.push(c); if (c[3] >= 1) break; }
    }
    let base = [255, 255, 255, 1];
    for (let i = stack.length - 1; i >= 0; i--) base = over(stack[i], base);
    return base;
  }
  const vis = (el) => { const r = el.getBoundingClientRect(), cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && cs.visibility !== "hidden" && cs.display !== "none"; };

  // Search the document and any same-origin iframes (Storybook, demo frames).
  const docs = [document];
  for (const f of document.querySelectorAll("iframe")) { try { if (f.contentDocument && f.contentDocument.body) docs.push(f.contentDocument); } catch (e) { /* cross-origin frame: not measurable, counted below */ } }
  const deep = (root, sel, out = []) => {
    out.push(...root.querySelectorAll(sel));
    for (const el of root.querySelectorAll("*")) if (el.shadowRoot) deep(el.shadowRoot, sel, out);
    return out;
  };
  const q = (sel) => docs.flatMap((d) => deep(d, sel));
  // "first:<sel>" keeps document order (the basic demo), otherwise the largest match wins.
  const FIRST = !!SEL && SEL.startsWith("first:");
  const S = FIRST ? SEL.slice(6) : SEL;
  // A row laid out with display:contents has no box of its own; its height is its cells'.
  const rowH = (r) => { const b = r.getBoundingClientRect().height; return b || Math.max(0, ...[...r.children].map((c) => c.getBoundingClientRect().height)); };

  const tables = q(S || "table, [role=grid], [role=table], [role=treegrid]").filter(vis)
    .map((t) => ({ t, a: t.getBoundingClientRect().width * t.getBoundingClientRect().height }))
    .sort((x, y) => (FIRST ? 0 : y.a - x.a));
  let table = null;
  if (tables.length) {
    const t = tables[0].t;
    const tr = t.getBoundingClientRect();
    // Web-component tables (UI5) keep rows as custom elements in light DOM.
    let rows = [...t.querySelectorAll("tr, [role=row]")].filter((r) => rowH(r) > 0);
    if (!rows.length) rows = [...t.querySelectorAll("*")].filter((e) => /-(header-)?row$/i.test(e.tagName) && rowH(e) > 0);
    // A header row holds column headers and no data cells. A body row may lead with a row
    // header (<th scope=row>, Primer), so "contains a th" is not the test.
    const isHead = (r) => !!r.closest("thead") || (r.querySelector("th:not([scope=row]), [role=columnheader]") !== null
      && r.querySelector("td, [role=gridcell], [role=cell], th[scope=row], [role=rowheader]") === null);
    const head = rows.filter(isHead), body = rows.filter((r) => !isHead(r));
    const cellOf = (r) => r.querySelector("td, [role=gridcell], [role=cell]") || r.firstElementChild;
    const bodyCells = body.map(cellOf).filter(Boolean);
    const tBg = effBg(t);
    const rowBgs = new Map();
    for (const r of body.slice(0, 20)) { const k = hex(effBg(cellOf(r) || r)); rowBgs.set(k, (rowBgs.get(k) || 0) + 1); }
    const divs = [];
    for (const c of bodyCells.slice(0, 20)) {
      for (const el of [c, c.parentElement]) {
        const cs = getComputedStyle(el);
        if (parseFloat(cs.borderBottomWidth) > 0 && cs.borderBottomStyle !== "none") { const bc = rgba(cs.borderBottomColor); if (bc[3] > 0) { const comp = over(bc, effBg(el)); divs.push({ c: hex(comp), r: ratio(comp, effBg(el)), w: cs.borderBottomWidth }); break; } }
      }
    }
    const hc = head.length ? (head[0].querySelector("th, [role=columnheader]") || head[0]) : null;
    const hcs = hc ? getComputedStyle(hc) : null;
    const bcs = bodyCells[0] ? getComputedStyle(bodyCells[0]) : null;
    const host = t.closest("[class]");
    table = {
      count: tables.length, width: Math.round(tr.width), bodyRows: body.length, headRows: head.length,
      bodyRowH: median(body.map(rowH)),
      headRowH: median(head.map(rowH)),
      cellFont: bcs && bcs.fontSize, cellLine: bcs && bcs.lineHeight, cellPadL: bcs && bcs.paddingLeft, cellWeight: bcs && bcs.fontWeight,
      cellInk: bodyCells[0] ? hex(over(rgba(bcs.color), effBg(bodyCells[0]))) : null,
      cellInkRatio: bodyCells[0] ? ratio(over(rgba(bcs.color), effBg(bodyCells[0])), effBg(bodyCells[0])) : null,
      headFont: hcs && hcs.fontSize, headWeight: hcs && hcs.fontWeight, headTransform: hcs && hcs.textTransform,
      headBg: hc ? hex(effBg(hc)) : null, headBgVsTable: hc ? ratio(effBg(hc), tBg) : null,
      tableBg: hex(tBg), rowBgs: [...rowBgs.entries()], dividers: divs.slice(0, 3),
      radius: host ? getComputedStyle(host).borderTopLeftRadius : null,
      sample: (bodyCells[0] && bodyCells[0].innerText || "").trim().slice(0, 30),
    };
  }

  const ctl = q("input:not([type=hidden]):not([type=checkbox]):not([type=radio]), select, textarea").filter(vis);
  const controls = ctl.slice(0, 30).map((el) => {
    const cs = getComputedStyle(el), bg = effBg(el.parentElement || el);
    let border = null;
    if (parseFloat(cs.borderBottomWidth) > 0 && cs.borderBottomStyle !== "none") { const comp = over(rgba(cs.borderBottomColor), bg); border = { c: hex(comp), r: ratio(comp, bg), top: cs.borderTopWidth, bottom: cs.borderBottomWidth }; }
    return { h: Math.round(el.getBoundingClientRect().height), radius: cs.borderTopLeftRadius, font: cs.fontSize, fill: hex(effBg(el)), border };
  });

  const acts = q("button, a[role=button], [role=button]").filter(vis).map((el) => {
    const cs = getComputedStyle(el), own = rgba(cs.backgroundColor), r = el.getBoundingClientRect();
    return { label: (el.innerText || el.getAttribute("aria-label") || "").trim().slice(0, 24), h: Math.round(r.height), fill: own[3] > 0.9 ? hex(own) : null, sat: own[3] > 0.9 ? +sat(own).toFixed(2) : 0, radius: cs.borderTopLeftRadius, font: cs.fontSize, weight: cs.fontWeight };
  });
  const filled = acts.filter((a) => a.fill && a.sat > 0.3);
  const accents = new Map(); for (const a of filled) accents.set(a.fill, (accents.get(a.fill) || 0) + 1);

  const fonts = new Map();
  for (const el of q("body, td, th, button, input, h1, h2")) { const ff = getComputedStyle(el).fontFamily.split(",")[0].replace(/["']/g, "").trim(); fonts.set(ff, (fonts.get(ff) || 0) + 1); }
  return {
    frames: docs.length, crossOriginFrames: document.querySelectorAll("iframe").length - (docs.length - 1),
    ground: hex(effBg(document.body)), table, controls,
    controlH: median(controls.map((c) => c.h)), controlRadius: median(controls.map((c) => parseFloat(c.radius))),
    actionH: median(acts.map((a) => a.h)), actionRadius: median(acts.map((a) => parseFloat(a.radius))),
    accentFills: [...accents.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5), actions: acts.length,
    fonts: [...fonts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3),
  };
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const results = {};
  for (const [name, url, sel] of TARGETS) {
    const ctx = await browser.newContext({ colorScheme: "light", viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    try {
      const resp = await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
      await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
      await page.waitForTimeout(4000);
      await page.screenshot({ path: path.join(OUT, name + ".png") });
      let m = null;
      for (const fr of page.frames()) {
        let r;
        try { r = await fr.evaluate(inPage, sel); } catch (e) { continue; }
        const rows = (x) => (x && x.table && x.table.bodyRows) || 0;
        if (!m || rows(r) > rows(m)) m = { ...r, frameUrl: fr.url().slice(0, 120) };
      }
      results[name] = { url, sel, finalUrl: page.url(), status: resp ? resp.status() : null, title: (await page.title()).slice(0, 80), ...m };
      const t = m.table;
      console.log("ok", name, resp && resp.status(), t ? `rows=${t.bodyRows} rowH=${t.bodyRowH} font=${t.cellFont}` : "NO TABLE", `ctlH=${m.controlH}`);
    } catch (e) {
      results[name] = { url, error: String(e).slice(0, 300) };
      console.log("err", name, String(e).split("\n")[0].slice(0, 140));
    }
    await ctx.close();
  }
  await browser.close();
  fs.writeFileSync(path.join(OUT, "measure.json"), JSON.stringify(results, null, 1));
})();
