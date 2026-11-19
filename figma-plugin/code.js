// Figma plugin: NurseShift – obrazovky ve stejném vzhledu jako aplikace (Tailwind slate/blue/indigo).
function hex(h) { return { r: parseInt(h.slice(1, 3), 16) / 255, g: parseInt(h.slice(3, 5), 16) / 255, b: parseInt(h.slice(5, 7), 16) / 255 }; }
const K = {
  s50: '#f8fafc', s100: '#f1f5f9', s200: '#e2e8f0', s300: '#cbd5e1', s400: '#94a3b8', s500: '#64748b', s600: '#475569',
  s700: '#334155', s800: '#1e293b', s900: '#0f172a', white: '#ffffff', blue600: '#2563eb', blue500: '#3b82f6', blue300: '#93c5fd',
  blue100: '#dbeafe', blue800: '#1e40af', amber100: '#fef3c7', amber800: '#92400e', emerald100: '#d1fae5', emerald800: '#065f46',
  emerald600: '#059669', indigo600: '#4f46e5', red50: '#fef2f2', red100: '#fee2e2', red700: '#b91c1c', indigo50: '#eef2ff', sky400: '#38bdf8',
};
const W = 1480, GAP = 200;

function box(p, x, y, w, h, fill, o) {
  o = o || {};
  const r = figma.createRectangle();
  r.x = x; r.y = y; r.resize(w, h);
  r.fills = [{ type: 'SOLID', color: hex(fill) }];
  if (o.r) r.cornerRadius = o.r;
  if (o.stroke) { r.strokes = [{ type: 'SOLID', color: hex(o.stroke) }]; r.strokeWeight = 1; }
  p.appendChild(r);
  return r;
}
function txt(p, s, x, y, o) {
  o = o || {};
  const t = figma.createText();
  t.fontName = { family: 'Inter', style: o.bold ? 'Bold' : (o.semi ? 'Semi Bold' : 'Regular') };
  t.fontSize = o.size || 12;
  t.fills = [{ type: 'SOLID', color: hex(o.color || K.s800) }];
  t.characters = String(s);
  if (o.w) { t.textAutoResize = 'NONE'; t.resize(o.w, o.h || (o.size || 12) + 6); t.textAlignHorizontal = o.align || 'LEFT'; }
  t.x = x; t.y = y;
  p.appendChild(t);
  return t;
}
function btn(p, label, x, y, w, fill, color, stroke) {
  box(p, x, y, w, 30, fill, { r: 8, stroke: stroke });
  txt(p, label, x, y + 8, { w: w, align: 'CENTER', size: 12, semi: true, color: color || K.white });
}
function frame(name, idx, h) {
  const f = figma.createFrame();
  f.name = name; f.x = 0; f.y = idx * (h + GAP); f.resize(W, h);
  f.fills = [{ type: 'SOLID', color: hex(K.s100) }];
  f.clipsContent = true;
  figma.currentPage.appendChild(f);
  return f;
}
function header(f, user, tabs, active) {
  box(f, 0, 0, W, 104, K.s900);
  box(f, 24, 14, 36, 36, K.blue600, { r: 10 });
  txt(f, '♥', 24, 20, { w: 36, align: 'CENTER', size: 18, color: K.white, bold: true });
  txt(f, 'NurseShift', 72, 12, { size: 18, bold: true, color: K.white });
  box(f, 168, 15, 138, 18, '#1e3a8a', { r: 4 });
  txt(f, '12H NEPŘETRŽITÝ PROVOZ', 168, 19, { w: 138, align: 'CENTER', size: 8, bold: true, color: K.blue300 });
  txt(f, 'Plánování směn zdravotních sester • Microsoft Entra ID SSO', 72, 34, { size: 11, color: K.s400 });
  // month selector
  box(f, 560, 12, 230, 40, K.s800, { r: 12, stroke: K.s700 });
  txt(f, '‹', 570, 20, { size: 16, color: K.s300 }); txt(f, '›', 770, 20, { size: 16, color: K.s300 });
  txt(f, 'Listopad 2026 (2026-11)', 590, 25, { w: 170, align: 'CENTER', size: 12, bold: true, color: K.white });
  // account
  box(f, 900, 8, 500, 48, K.s800, { r: 12, stroke: K.s700 });
  txt(f, 'Microsoft účet nemocnice:', 936, 13, { size: 9, color: K.s400 });
  txt(f, user, 936, 28, { size: 12, semi: true, color: K.white });
  box(f, 1412, 12, 40, 40, K.s800, { r: 12, stroke: K.s700 });
  txt(f, '⟳', 1412, 20, { w: 40, align: 'CENTER', size: 16, color: K.s300 });
  box(f, 0, 62, W, 1, K.s800);
  let x = 24;
  tabs.forEach(function (t, i) {
    const w = t.length * 6.6 + 40;
    if (i === active) { box(f, x, 68, w, 36, K.s800, { r: 6 }); box(f, x, 102, w, 2, K.blue500); }
    txt(f, t, x, 80, { w: w, align: 'CENTER', size: 12, semi: true, color: i === active ? K.white : K.s400 });
    x += w + 4;
  });
}
function card(f, x, y, w, h) { return box(f, x, y, w, h, K.white, { r: 12, stroke: K.s200 }); }

const NURSES = [
  ['Bc. Jana Nováková', 1.0], ['Bc. Petra Černá', 1.0], ['Lucie Procházková', 1.0], ['Bc. Klára Veselá', 1.0],
  ['Mgr. Tereza Horáková', 1.0], ['Hana Němcová', 1.0], ['Markéta Benešová', 0.75], ['Simona Růžičková', 0.5],
];
function pattern(i, d) {
  const c = (d + i * 3) % 8;
  if (c === 0 || c === 1) return 'D';
  if (c === 2 || c === 3) return 'N';
  if (i === 1 && (d === 17 || d === 18)) return 'DOV';
  return 'V';
}
const CELL = { D: [K.amber100, K.amber800], N: [K.blue100, K.blue800], DOV: [K.emerald100, K.emerald800], V: [K.white, K.s300] };
const DOW = ['Ne', 'Po', 'Út', 'St', 'Čt', 'Pá', 'So']; // 1.11.2026 = neděle

function matrix(f, y0, readOnlyUser) {
  const x0 = 24, nameW = 230, cw = 34, days = 30, fondW = 150, rh = 44, tw = nameW + cw * days + fondW;
  card(f, x0, y0, tw, 60 + rh * (NURSES.length + 2));
  box(f, x0, y0, tw, 48, K.s100, { r: 12 });
  txt(f, 'Zaměstnanec / Úvazek', x0 + 12, y0 + 16, { size: 12, semi: true, color: K.s700 });
  for (let d = 1; d <= days; d++) {
    const dow = DOW[(d - 1) % 7], we = dow === 'So' || dow === 'Ne';
    const cx = x0 + nameW + (d - 1) * cw;
    if (we) box(f, cx, y0, cw, 48, K.s200);
    txt(f, String(d), cx, y0 + 8, { w: cw, align: 'CENTER', size: 11, bold: true, color: K.s700 });
    txt(f, dow, cx, y0 + 26, { w: cw, align: 'CENTER', size: 9, color: K.s500 });
  }
  txt(f, 'Hodiny / Fond', x0 + nameW + cw * days, y0 + 16, { w: fondW - 12, align: 'RIGHT', size: 12, semi: true, color: K.s700 });
  const dayCnt = [], nightCnt = [];
  for (let d = 0; d < days; d++) { dayCnt.push(0); nightCnt.push(0); }
  NURSES.forEach(function (n, i) {
    const y = y0 + 48 + i * rh;
    const mine = readOnlyUser === n[0];
    box(f, x0, y, tw, 1, K.s200);
    if (mine) box(f, x0 + 1, y + 1, tw - 2, rh - 1, K.indigo50);
    txt(f, n[0], x0 + 12, y + 7, { size: 12, semi: true, color: K.s800 });
    box(f, x0 + 12, y + 25, 34, 13, K.blue600, { r: 3 });
    txt(f, n[1].toFixed(2), x0 + 12, y + 26, { w: 34, align: 'CENTER', size: 8, semi: true, color: K.white });
    let hours = 0;
    for (let d = 0; d < days; d++) {
      const s = pattern(i, d); const c = CELL[s];
      if (s === 'D') { dayCnt[d]++; hours += 12; } if (s === 'N') { nightCnt[d]++; hours += 12; }
      const cx = x0 + nameW + d * cw;
      box(f, cx + 2, y + 6, cw - 4, rh - 12, c[0], { r: 4, stroke: s === 'V' ? K.s200 : undefined });
      txt(f, s === 'V' ? '' : s, cx + 2, y + 15, { w: cw - 4, align: 'CENTER', size: 10, bold: true, color: c[1] });
    }
    const fond = Math.round(160 * n[1]);
    txt(f, hours + ' / ' + fond + ' h', x0 + nameW + cw * days, y + 8, { w: fondW - 12, align: 'RIGHT', size: 12, bold: true, color: K.s800 });
    txt(f, 'rozdíl ' + (hours - fond >= 0 ? '+' : '') + (hours - fond) + ' h', x0 + nameW + cw * days, y + 25, { w: fondW - 12, align: 'RIGHT', size: 10, color: K.s500 });
  });
  const ys = y0 + 48 + NURSES.length * rh;
  [['Obsazenost – Denní (min 3)', dayCnt, 3], ['Obsazenost – Noční (min 2)', nightCnt, 2]].forEach(function (row, j) {
    const y = ys + j * rh;
    box(f, x0, y, tw, rh, K.s50); box(f, x0, y, tw, 2, K.s300);
    txt(f, row[0], x0 + 12, y + 14, { size: 11, bold: true, color: j ? '#1e1b4b' : K.blue800 });
    row[1].forEach(function (c, d) {
      const cx = x0 + nameW + d * cw; const bad = c < row[2];
      box(f, cx + 2, y + 8, cw - 4, rh - 16, bad ? K.red100 : K.emerald100, { r: 4 });
      txt(f, String(c), cx + 2, y + 15, { w: cw - 4, align: 'CENTER', size: 10, bold: true, color: bad ? K.red700 : K.emerald800 });
    });
  });
  return y0 + 60 + rh * (NURSES.length + 2);
}

async function main() {
  await figma.loadFontAsync({ family: 'Inter', style: 'Regular' });
  await figma.loadFontAsync({ family: 'Inter', style: 'Semi Bold' });
  await figma.loadFontAsync({ family: 'Inter', style: 'Bold' });
  const out = [];

  // 1. Plánovací matice – vrchní sestra
  let f = frame('1. Plánovací matice směn (Vrchní sestra)', 0, 880);
  header(f, 'Mgr. Eva Dvořáková — [Vrchní sestra] (eva.dvorakova@nemocnice.cz)', ['Plánovací matice směn', 'Preference sester', 'Výměny směn', 'Nastavení oddělení & Uživatelé'], 0);
  card(f, 24, 124, 1424, 60);
  box(f, 40, 140, 250, 28, K.s100, { r: 8 });
  txt(f, 'Stav rozpisu:', 52, 147, { size: 11, color: K.s600 });
  btn(f, 'Koncept ▾', 140, 139, 130, K.white, K.s700, K.s300);
  btn(f, 'Uložit rozpis', 1290, 139, 140, K.indigo600);
  btn(f, 'Vymazat', 1190, 139, 90, K.white, K.red700, '#fecaca');
  box(f, 24, 200, 1424, 40, K.s800, { r: 12 });
  txt(f, 'Štětec:   D (Denní 12h)    N (Noční 12h)    DOV    V (volno)        Přepínat (V → D → N → DOV)', 40, 213, { size: 11, semi: true, color: K.s300 });
  matrix(f, 260, null);
  txt(f, 'Návrh obrazovky – krok 1 (stav k 1. kontrole: ukládání/načítání rozpisu přes API)', 24, 850, { size: 11, color: K.s500 });
  out.push(f);

  // 2. Pohled sestry
  f = frame('2. Pohled sestry (jen čtení)', 1, 700);
  header(f, 'Bc. Jana Nováková — [Sestra] (jana.novakova@nemocnice.cz)', ['Plánovací matice směn', 'Moje preference a dovolená', 'Výměny směn'], 0);
  box(f, 24, 124, 1424, 40, K.blue100, { r: 12, stroke: '#bfdbfe' });
  txt(f, '🔒  Rozpis je pouze ke čtení. Vlastní řádek je zvýrazněn.', 44, 136, { size: 12, color: '#1e3a8a' });
  matrix(f, 184, 'Bc. Jana Nováková');
  out.push(f);

  // 3. Nastavení oddělení & uživatelé
  f = frame('3. Nastavení oddělení & Uživatelé (Admin)', 2, 760);
  header(f, 'Ing. Martin Svoboda — [Admin] (martin.svoboda@nemocnice.cz)', ['Plánovací matice směn', 'Preference sester', 'Výměny směn', 'Nastavení oddělení & Uživatelé'], 3);
  card(f, 24, 124, 460, 380);
  txt(f, 'Nastavení oddělení', 44, 142, { size: 16, bold: true });
  [['Délka směny (hodiny)', '12'], ['Min. obsazenost – Denní', '3'], ['Min. obsazenost – Noční', '2'], ['Týdenní fond (plný úvazek, h)', '37.5'], ['Max. po sobě jdoucích směn', '3']].forEach(function (p, i) {
    txt(f, p[0], 44, 182 + i * 56, { size: 12, semi: true, color: K.s700 });
    box(f, 44, 200 + i * 56, 420, 30, K.white, { r: 8, stroke: K.s300 });
    txt(f, p[1], 54, 208 + i * 56, { size: 12 });
  });
  btn(f, 'Uložit nastavení', 44, 470, 150, K.indigo600);
  txt(f, '☑ Zakázat noční → denní směnu', 220, 477, { size: 12, semi: true, color: K.s700 });
  card(f, 508, 124, 940, 380 + 150);
  txt(f, 'Správa uživatelů', 528, 142, { size: 16, bold: true });
  btn(f, '+ Přidat uživatele', 1280, 138, 150, K.indigo600);
  box(f, 528, 184, 900, 36, K.s100);
  [['Jméno', 0], ['Microsoft E-mail', 220], ['Role', 520], ['Úvazek', 650], ['Stav', 740], ['Akce', 830]].forEach(function (c) { txt(f, c[0], 540 + c[1], 194, { size: 11, bold: true, color: K.s600 }); });
  const us = [['Ing. Martin Svoboda', 'martin.svoboda@nemocnice.cz', 'Admin', '1.00'], ['Mgr. Eva Dvořáková', 'eva.dvorakova@nemocnice.cz', 'Vrchní sestra', '1.00'],
    ['Bc. Jana Nováková', 'jana.novakova@nemocnice.cz', 'Sestra', '1.00'], ['Bc. Petra Černá', 'petra.cerna@nemocnice.cz', 'Sestra', '1.00'],
    ['Markéta Benešová', 'marketa.benesova@nemocnice.cz', 'Sestra', '0.75'], ['Simona Růžičková', 'simona.ruzickova@nemocnice.cz', 'Sestra', '0.50']];
  us.forEach(function (u, i) {
    const y = 220 + i * 44; box(f, 528, y, 900, 1, K.s200);
    txt(f, u[0], 540, y + 14, { size: 12, semi: true }); txt(f, u[1], 760, y + 14, { size: 12, color: K.s600 });
    txt(f, u[2], 1060, y + 14, { size: 12 }); txt(f, u[3], 1190, y + 14, { size: 12 });
    box(f, 1280, y + 11, 50, 20, K.emerald100, { r: 10 }); txt(f, 'Aktivní', 1280, y + 15, { w: 50, align: 'CENTER', size: 9, bold: true, color: K.emerald800 });
    txt(f, 'Upravit   Smazat', 1340, y + 14, { size: 11, color: K.blue600 });
  });
  out.push(f);

  figma.currentPage.selection = out;
  figma.viewport.scrollAndZoomIntoView(out);
  figma.closePlugin('NurseShift: vytvořeny 3 obrazovky.');
}
main().catch(function (e) { figma.closePlugin('Chyba: ' + e.message); });
