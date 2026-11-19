// Figma plugin: vytvoří 5 obrazovek NurseShift (wireframy).
const C = {
  bg: { r: 0.93, g: 0.95, b: 0.97 }, white: { r: 1, g: 1, b: 1 }, blue: { r: 0.15, g: 0.39, b: 0.92 },
  gray: { r: 0.9, g: 0.91, b: 0.92 }, text: { r: 0.12, g: 0.16, b: 0.22 }, day: { r: 0.99, g: 0.95, b: 0.78 },
  night: { r: 0.78, g: 0.82, b: 0.99 }, off: { r: 0.95, g: 0.96, b: 0.96 }, red: { r: 1, g: 0.89, b: 0.89 },
  green: { r: 0.86, g: 0.99, b: 0.9 }, dark: { r: 0.18, g: 0.18, b: 0.18 }, border: { r: 0.8, g: 0.84, b: 0.88 },
};

function rect(parent, x, y, w, h, fill, opts) {
  opts = opts || {};
  const r = figma.createRectangle();
  r.x = x; r.y = y; r.resize(w, h);
  r.fills = [{ type: 'SOLID', color: fill }];
  r.cornerRadius = opts.radius || 0;
  if (opts.stroke) { r.strokes = [{ type: 'SOLID', color: C.border }]; r.strokeWeight = 1; }
  parent.appendChild(r);
  return r;
}

function text(parent, str, x, y, size, color, bold) {
  const t = figma.createText();
  t.fontName = { family: 'Inter', style: bold ? 'Bold' : 'Regular' };
  t.characters = String(str);
  t.fontSize = size || 14;
  t.fills = [{ type: 'SOLID', color: color || C.text }];
  t.x = x; t.y = y;
  parent.appendChild(t);
  return t;
}

function button(parent, label, x, y, w, primary) {
  rect(parent, x, y, w, 34, primary ? C.blue : C.gray, { radius: 6 });
  text(parent, label, x + 12, y + 9, 14, primary ? C.white : C.text);
}

function frame(name, x, w, h) {
  const f = figma.createFrame();
  f.name = name; f.x = x; f.y = 0; f.resize(w, h);
  f.fills = [{ type: 'SOLID', color: C.bg }];
  figma.currentPage.appendChild(f);
  rect(f, 20, 20, w - 40, h - 40, C.white, { radius: 10, stroke: true });
  text(f, name, 40, 36, 20, C.text, true);
  return f;
}

function table(f, x, y, headers, rows, colW, cellFill) {
  const rh = 34;
  headers.forEach((h, i) => {
    rect(f, x + i * colW[i - 1 < 0 ? 0 : 0] * 0 + colW.slice(0, i).reduce((a, b) => a + b, 0), y, colW[i], rh, C.gray, { stroke: true });
    text(f, h, x + colW.slice(0, i).reduce((a, b) => a + b, 0) + 8, y + 9, 13, C.text, true);
  });
  rows.forEach((row, r) => row.forEach((cell, i) => {
    const cx = x + colW.slice(0, i).reduce((a, b) => a + b, 0);
    const fill = cellFill ? cellFill(cell, i) : C.white;
    rect(f, cx, y + rh * (r + 1), colW[i], rh, fill, { stroke: true });
    text(f, cell, cx + 8, y + rh * (r + 1) + 9, 13);
  }));
}

async function main() {
  await figma.loadFontAsync({ family: 'Inter', style: 'Regular' });
  await figma.loadFontAsync({ family: 'Inter', style: 'Bold' });
  const created = [];

  // 1. Přihlášení
  let f = frame('1. Přihlášení', 0, 480, 400);
  text(f, 'Plánování 12h směn zdravotních sester', 40, 80, 14);
  rect(f, 90, 150, 300, 56, C.dark, { radius: 6 });
  text(f, 'Přihlásit přes Microsoft', 150, 168, 16, C.white);
  text(f, 'Dev režim: výběr testovacího účtu', 120, 240, 12);
  created.push(f);

  // 2. Měsíční rozpis
  f = frame('2. Měsíční rozpis (Vrchní sestra / Admin)', 560, 1000, 520);
  button(f, '< říjen', 40, 80, 80); text(f, 'LISTOPAD 2026', 140, 88, 16, C.text, true);
  button(f, 'prosinec >', 290, 80, 100); button(f, 'Koncept v', 700, 80, 110); button(f, 'Uložit', 830, 80, 90, true);
  const days = ['Po 1', 'Út 2', 'St 3', 'Čt 4', 'Pá 5', 'So 6', 'Ne 7'];
  const rows = [
    ['Nováková 1.0', 'D', 'D', 'V', 'N', 'N', 'V', 'D'],
    ['Černá 1.0', 'D', 'D', 'V', 'V', 'N', 'N', 'V'],
    ['Procházková 1.0', 'V', 'N', 'N', 'V', 'D', 'D', 'D'],
    ['Veselá 1.0', 'N', 'V', 'D', 'D', 'V', 'N', 'N'],
    ['Horáková 1.0', 'V', 'D', 'D', 'N', 'V', 'D', 'V'],
    ['Obsazenost D/N', '3/2', '3/2', '2/2', '3/2', '3/1', '3/2', '3/2'],
  ];
  table(f, 40, 140, ['Sestra / úvazek'].concat(days), rows, [180, 90, 90, 90, 90, 90, 90, 90], (c, i) => {
    if (i === 0) return C.white;
    if (c === 'D') return C.day; if (c === 'N') return C.night; if (c === 'V') return C.off;
    return (c === '2/2' || c === '3/1') ? C.red : C.green;
  });
  text(f, 'Klik na buňku přepíná D → N → DOV → V. Červená = nedostatečná obsazenost.', 40, 440, 13);
  created.push(f);

  // 3. Pohled sestry
  f = frame('3. Pohled sestry (jen čtení)', 0, 800, 300);
  table(f, 40, 90, ['', '1', '2', '3', '4', '5'], [['Bc. Jana Nováková', 'D', 'D', 'V', 'N', 'N']], [200, 90, 90, 90, 90, 90],
    (c, i) => (c === 'D' ? C.day : c === 'N' ? C.night : c === 'V' ? C.off : C.white));
  text(f, 'Ostatní sestry jsou zobrazeny šedě, vlastní řádek zvýrazněn.', 40, 190, 13);
  created.push(f);

  // 4. Správa uživatelů
  f = frame('4. Správa uživatelů (Admin)', 880, 1000, 340);
  button(f, '+ Přidat', 860, 30, 90, true);
  table(f, 40, 90, ['Jméno', 'E-mail', 'Role', 'Úvazek', 'Aktivní'], [
    ['Bc. Jana Nováková', 'jana.novakova@nemocnice.cz', 'sestra', '1.0', 'ano'],
    ['Markéta Benešová', 'marketa.benesova@nemocnice.cz', 'sestra', '0.75', 'ano'],
    ['Mgr. Eva Dvořáková', 'eva.dvorakova@nemocnice.cz', 'vrchní sestra', '1.0', 'ano'],
  ], [220, 300, 160, 100, 100]);
  created.push(f);

  // 5. Nastavení oddělení
  f = frame('5. Nastavení oddělení', 1260, 560, 460);
  const fields = [['Délka směny (h)', '12'], ['Min. obsazenost – den', '3'], ['Min. obsazenost – noc', '2'], ['Týdenní fond (plný úvazek, h)', '37,5']];
  fields.forEach((p, i) => {
    text(f, p[0], 40, 90 + i * 64, 13);
    rect(f, 40, 112 + i * 64, 280, 30, C.off, { radius: 6, stroke: true });
    text(f, p[1], 50, 119 + i * 64, 14);
  });
  text(f, '[x] Zákaz noc → den     Max. po sobě jdoucích směn: 3', 40, 352, 13);
  button(f, 'Uložit', 40, 390, 90, true);
  created.push(f);

  figma.currentPage.selection = created;
  figma.viewport.scrollAndZoomIntoView(created);
  figma.closePlugin('NurseShift: vytvořeno 5 obrazovek.');
}

main();
