'use strict';
/* Cruscotto: pagine con ancora #/..., nessuna libreria esterna, grafici in SVG. */

// ------------------------------------------------------------------ utilità
const app = document.getElementById('app');
let giro = 0;
const vedi = (mio, ...nodi) => { if (mio === giro) app.replaceChildren(...nodi.filter(n => n != null && n !== false)); };
function h(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === 'class') e.className = v;
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v === true ? '' : v);
  }
  for (const c of kids.flat(Infinity)) if (c != null && c !== false) e.append(c);
  return e;
}
const NS = 'http://www.w3.org/2000/svg';
function sv(tag, attrs, ...kids) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs || {})) e.setAttribute(k, v);
  for (const c of kids.flat(Infinity)) if (c != null) e.append(c);
  return e;
}
const nf = (x, d = 2) => x == null || Number.isNaN(x) ? '–' : Number(x).toLocaleString('it-IT', { minimumFractionDigits: d, maximumFractionDigits: d });
const pc = x => x == null ? '–' : nf(x * 100, 0) + '%';
const eur = x => x == null ? '–' : nf(x, 0) + ' €';
const segno = x => x == null ? '' : x > 0 ? 'pos' : x < 0 ? 'neg' : '';
const sigla = (t, spiegazione) => h('span', { class: 'sigla', title: spiegazione, style: 'border-bottom:1px dotted var(--muto);cursor:help' }, t);
async function api(p, opt) {
  const r = await fetch('/api' + p, opt);
  const j = await r.json();
  if (!r.ok) throw new Error(j.errore || r.status);
  return j;
}
function memo(chiave, valore) {         // preferenze di vista: se il browser non salva, si va avanti senza
  try { if (valore === undefined) return localStorage.getItem(chiave); localStorage.setItem(chiave, valore); } catch (e) { return null; }
}

const GRUPPI = [['caso', 'Caso o vantaggio'], ['costi', 'Costi e fattibilità'], ['regolarita', 'Regolarità'],
  ['robustezza', 'Robustezza'], ['rischio', 'Rischio'], ['portafoglio', 'Portafoglio']];
const ESITI = { candidato: 'Candidato', scartato: 'Scartato', non_giudicato: 'Non giudicato' };
const STATI = ['da guardare', 'da approfondire', 'in verifica', 'live', 'scartato'];
const GRAVITA = { rosso: 0, giallo: 1, grigio: 2, verde: 3, info: 4 };
const badge = (esito, testo) => h('span', { class: 'badge ' + (esito || 'non_giudicato') }, testo || ESITI[esito] || ESITI.non_giudicato);
const pallini = (g, nomi) => h('span', { class: 'pallini' }, GRUPPI.map(([k, n]) =>
  h('span', { class: 'pallino ' + ((g || {})[k] || 'grigio'), title: `${n}: ${(g || {})[k] || 'non calcolato'}` })));

// ------------------------------------------------------------------ grafici SVG
function assiX(date, W, m, h0) {
  const out = []; let ult = null;
  date.forEach((d, i) => { const a = d.slice(0, 4); if (a !== ult && (+a % 2 === 1 || date.length < 800)) out.push([i, a]); ult = a; });
  return out;
}
function bellaScala(lo, hi, n = 4) {
  if (lo === hi) { lo -= 1; hi += 1; }
  const passo0 = (hi - lo) / n, mag = Math.pow(10, Math.floor(Math.log10(passo0)));
  const passo = [1, 2, 2.5, 5, 10].map(x => x * mag).find(x => x >= passo0);
  const a = Math.floor(lo / passo) * passo, b = Math.ceil(hi / passo) * passo, t = [];
  for (let v = a; v <= b + passo / 2; v += passo) t.push(v);
  return { a, b, t };
}
/* Linee e bande su un asse di date. serie: [{y, colore, area}], banda: {p5, p50, p95, passo} */
function grafico({ date, serie, banda, altezza = 260, fmt = v => nf(v, 1), etichetta = 'valore' }) {
  const cont = h('div', { class: 'grafico' });
  const tip = h('div', { class: 'tip' });
  function disegna() {
    const W = cont.clientWidth || 900, H = altezza, m = { l: 56, r: 12, t: 10, b: 22 };
    const vals = serie.flatMap(s => s.y).concat(banda ? banda.p5.concat(banda.p95) : []);
    const sc = bellaScala(Math.min(...vals, 0), Math.max(...vals, 0));
    const n = date.length, X = i => m.l + (W - m.l - m.r) * i / (n - 1), Y = v => m.t + (H - m.t - m.b) * (1 - (v - sc.a) / (sc.b - sc.a));
    const svg = sv('svg', { viewBox: `0 0 ${W} ${H}`, height: H });
    const assi = sv('g', { class: 'assi' });
    sc.t.forEach(v => assi.append(sv('line', { x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v) }), sv('text', { x: m.l - 6, y: Y(v) + 4, 'text-anchor': 'end' }, fmt(v))));
    assiX(date, W, m).forEach(([i, a]) => assi.append(sv('text', { x: X(i), y: H - 6, 'text-anchor': 'middle' }, a)));
    svg.append(assi);
    if (banda) {
      const pts = banda.p5.map((_, k) => Math.min(k * banda.passo, n - 1));
      const alto = pts.map((i, k) => `${X(i)},${Y(banda.p95[k])}`), basso = pts.map((i, k) => `${X(i)},${Y(banda.p5[k])}`).reverse();
      svg.append(sv('polygon', { points: alto.concat(basso).join(' '), style: 'fill:var(--accento);opacity:.16' }),
        sv('polyline', { points: pts.map((i, k) => `${X(i)},${Y(banda.p50[k])}`).join(' '), style: 'fill:none;stroke:var(--accento);stroke-width:1;stroke-dasharray:4 3;opacity:.7' }));
    }
    serie.forEach(s => {
      const pts = s.y.map((v, i) => `${X(i)},${Y(v)}`).join(' ');
      if (s.area) svg.append(sv('polygon', { points: `${X(0)},${Y(0)} ${pts} ${X(n - 1)},${Y(0)}`, style: `fill:${s.colore};opacity:.35` }));
      svg.append(sv('polyline', { points: pts, style: `fill:none;stroke:${s.colore};stroke-width:1.6` }));
    });
    const riga = sv('line', { y1: m.t, y2: H - m.b, style: 'stroke:var(--muto);stroke-width:1;display:none' });
    const area = sv('rect', { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, style: 'fill:transparent' });
    area.addEventListener('pointermove', ev => {
      const r = svg.getBoundingClientRect(), x = (ev.clientX - r.left) * W / r.width;
      const i = Math.max(0, Math.min(n - 1, Math.round((x - m.l) / (W - m.l - m.r) * (n - 1))));
      riga.setAttribute('x1', X(i)); riga.setAttribute('x2', X(i)); riga.style.display = '';
      tip.textContent = `${date[i]}: ` + serie.map(s => fmt(s.y[i])).join(' / ');
      tip.style.display = 'block'; tip.style.left = Math.min(X(i) + 10, W - 190) + 'px'; tip.style.top = '8px';
    });
    area.addEventListener('pointerleave', () => { riga.style.display = 'none'; tip.style.display = 'none'; });
    svg.append(riga, area);
    cont.replaceChildren(svg, tip);
  }
  let ultima = 0;
  new ResizeObserver(() => { if (cont.clientWidth && cont.clientWidth !== ultima) { ultima = cont.clientWidth; requestAnimationFrame(disegna); } }).observe(cont);
  return cont;
}
function barreGrafico(etichette, valori, fmt = v => nf(v, 1)) {
  const cont = h('div', { class: 'grafico' });
  function disegna() {
    const W = cont.clientWidth || 900, H = 200, m = { l: 56, r: 12, t: 14, b: 22 };
    const sc = bellaScala(Math.min(...valori, 0), Math.max(...valori, 0), 4), Y = v => m.t + (H - m.t - m.b) * (1 - (v - sc.a) / (sc.b - sc.a));
    const w = (W - m.l - m.r) / valori.length, svg = sv('svg', { viewBox: `0 0 ${W} ${H}`, height: H }), assi = sv('g', { class: 'assi' });
    sc.t.forEach(v => assi.append(sv('line', { x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v) }), sv('text', { x: m.l - 6, y: Y(v) + 4, 'text-anchor': 'end' }, fmt(v))));
    svg.append(assi);
    valori.forEach((v, i) => {
      const x = m.l + i * w + w * 0.15, y0 = Y(0), y1 = Y(v);
      const r = sv('rect', { x, y: Math.min(y0, y1), width: w * 0.7, height: Math.max(1, Math.abs(y0 - y1)), style: `fill:var(${v >= 0 ? '--verde' : '--rosso'})` });
      r.append(sv('title', {}, `${etichette[i]}: ${fmt(v)}`));
      svg.append(r, sv('text', { x: x + w * 0.35, y: H - 6, 'text-anchor': 'middle', style: 'fill:var(--muto);font-size:11px' }, etichette[i]));
    });
    cont.replaceChildren(svg);
  }
  let ultima = 0;
  new ResizeObserver(() => { if (cont.clientWidth && cont.clientWidth !== ultima) { ultima = cont.clientWidth; requestAnimationFrame(disegna); } }).observe(cont);
  return cont;
}

// ------------------------------------------------------------------ testo markdown semplice (tutto escapato)
const esc = t => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const inl = t => esc(t).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/\*([^*]+)\*/g, '<em>$1</em>');
function md(src) {
  const righe = src.split('\n'), out = []; let i = 0;
  while (i < righe.length) {
    const r = righe[i];
    if (!r.trim()) { i++; continue; }
    const t = r.match(/^(#{1,4})\s+(.*)/);
    if (t) { const n = Math.min(4, t[1].length + 1); out.push(`<h${n}>${inl(t[2])}</h${n}>`); i++; continue; }
    if (r.trim().startsWith('|')) {
      const tab = []; while (i < righe.length && righe[i].trim().startsWith('|')) tab.push(righe[i++]);
      const celle = l => l.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim());
      const corpo = tab.filter(l => !/^\s*\|[\s:|-]+\|\s*$/.test(l));
      out.push('<table><thead><tr>' + celle(corpo[0]).map(c => `<th>${inl(c)}</th>`).join('') + '</tr></thead><tbody>' +
        corpo.slice(1).map(l => '<tr>' + celle(l).map(c => `<td>${inl(c)}</td>`).join('') + '</tr>').join('') + '</tbody></table>');
      continue;
    }
    if (/^\s*[-*]\s+/.test(r)) {
      const v = []; while (i < righe.length && /^\s*[-*]\s+/.test(righe[i])) v.push(righe[i++].replace(/^\s*[-*]\s+/, ''));
      out.push('<ul>' + v.map(x => `<li>${inl(x)}</li>`).join('') + '</ul>'); continue;
    }
    const p = []; while (i < righe.length && righe[i].trim() && !/^(#|\||\s*[-*]\s)/.test(righe[i])) p.push(righe[i++]);
    out.push(`<p>${inl(p.join(' '))}</p>`);
  }
  const d = h('div', { class: 'testo-md' }); d.innerHTML = out.join(''); return d;
}

// ------------------------------------------------------------------ curva a tre fasce
const FASCE = { antico: ['Prima del 2011', 'var(--f-ind)', 'Prima'], indietro: ["Holdout all'indietro", 'var(--f-ind)', 'Prima'], vicino: ['2011-2013', 'var(--f-vic)', '11-13'],
  scoperta: ['In-sample', 'var(--f-in)', 'In'], avanti: ['Fuori campione', 'var(--f-out)', 'Fuori'] };
const mese = d => { const [a, m] = d.split('-'); return ['gen', 'feb', 'mar', 'apr', 'mag', 'giu', 'lug', 'ago', 'set', 'ott', 'nov', 'dic'][+m - 1] + ' ' + a; };
/* Curva netta quasi quadrata (1:1,2) con una fascia di colore per periodo e il drawdown sotto in piccolo.
   c: {date, cum, dd, segmenti: [[periodo, da, a]]}. */
function curvaQuadrata(c, fmt) {
  const W = 520, H = 440, HD = 96, m = { l: 62, r: 10, t: 10, b: 40 }, n = c.cum.length;
  const X = i => m.l + (W - m.l - m.r) * i / (n - 1);
  const rifv = (c.rif || []).filter(v => v != null);
  const sc = bellaScala(Math.min(...c.cum, ...rifv, 0), Math.max(...c.cum, ...rifv, 0), 5), Y = v => m.t + (H - m.t - m.b) * (1 - (v - sc.a) / (sc.b - sc.a));
  const svg = sv('svg', { viewBox: `0 0 ${W} ${H}`, class: 'quadrata', role: 'img', 'aria-label': 'Curva netta cumulata' });
  const assi = sv('g', { class: 'assi' });
  c.segmenti.forEach(([p, i0, i1]) => svg.append(sv('rect', { x: X(i0), y: m.t, width: Math.max(1, X(i1) - X(i0)), height: H - m.t - m.b, style: `fill:${FASCE[p][1]};opacity:.13` })));
  // anni del walk-forward della procedura: fuori campione della procedura dentro la scoperta
  (c.anni_wf || []).forEach(a => {
    const idx = c.date.map((d, i) => d.startsWith(String(a)) ? i : -1).filter(i => i >= 0);
    if (idx.length) svg.append(sv('rect', { x: X(idx[0]), y: m.t, width: Math.max(1, X(idx[idx.length - 1]) - X(idx[0])), height: 8, style: 'fill:var(--f-wf);opacity:.8' }));
  });
  sc.t.forEach(v => assi.append(sv('line', { x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v) }), sv('text', { x: m.l - 6, y: Y(v) + 4, 'text-anchor': 'end' }, fmt(v))));
  svg.append(assi);
  if (rifv.length) {          // riferimento D2: la stessa finestra in tutti i giorni, sugli stessi trade
    const pts = []; c.rif.forEach((v, i) => { if (v != null) pts.push(`${X(i)},${Y(v)}`); });
    svg.append(sv('polyline', { points: pts.join(' '), style: 'fill:none;stroke:var(--muto);stroke-width:1.2;stroke-dasharray:4 3' }));
  }
  c.segmenti.forEach(([p, i0, i1]) => {
    const j0 = Math.max(0, i0 - 1);          // il tratto parte dal punto precedente, così le fasce si toccano senza buchi
    svg.append(sv('polyline', { points: c.cum.slice(j0, i1 + 1).map((v, k) => `${X(j0 + k)},${Y(v)}`).join(' '), style: `fill:none;stroke:${FASCE[p][1]};stroke-width:1.8` }));
    const xm = (X(i0) + X(i1)) / 2, w = X(i1) - X(i0), nome = w > 110 ? FASCE[p][0] : (w > 38 ? FASCE[p][2] : '');
    if (nome) svg.append(sv('text', { x: xm, y: H - 22, 'text-anchor': 'middle', style: `fill:${FASCE[p][1]};font-size:12px;font-weight:600` }, nome));
    svg.append(sv('text', { x: xm, y: H - 7, 'text-anchor': 'middle', style: 'fill:var(--muto);font-size:10.5px' }, w > 130 ? `${mese(c.date[i0])} – ${mese(c.date[i1])}` : `${c.date[i0].slice(0, 4)}–${c.date[i1].slice(0, 4)}`));
  });
  const riga = sv('line', { y1: m.t, y2: H - m.b, style: 'stroke:var(--muto);stroke-width:1;display:none' }), tip = h('div', { class: 'tip' });
  const area = sv('rect', { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, style: 'fill:transparent' });
  area.addEventListener('pointermove', ev => {
    const r = svg.getBoundingClientRect(), x = (ev.clientX - r.left) * W / r.width, i = Math.max(0, Math.min(n - 1, Math.round((x - m.l) / (W - m.l - m.r) * (n - 1))));
    riga.setAttribute('x1', X(i)); riga.setAttribute('x2', X(i)); riga.style.display = '';
    tip.textContent = `${c.date[i]}: ${fmt(c.cum[i])}` + (c.rif && c.rif[i] != null ? ` · riferimento ${fmt(c.rif[i])}` : ''); tip.style.display = 'block'; tip.style.left = Math.min(Math.max(8, X(i) * r.width / W + 10), r.width - 150) + 'px'; tip.style.top = '8px';
  });
  area.addEventListener('pointerleave', () => { riga.style.display = 'none'; tip.style.display = 'none'; });
  svg.append(riga, area);
  // drawdown: stessa scala orizzontale, in piccolo
  const dsv = sv('svg', { viewBox: `0 0 ${W} ${HD}`, class: 'quadrata', role: 'img', 'aria-label': 'Drawdown' });
  const mn = Math.min(...c.dd, -1e-9), YD = v => 14 + (HD - 22) * (v / mn);
  c.segmenti.forEach(([p, i0, i1]) => dsv.append(sv('rect', { x: X(i0), y: 0, width: Math.max(1, X(i1) - X(i0)), height: HD - 8, style: `fill:${FASCE[p][1]};opacity:.13` })));
  dsv.append(sv('polygon', { points: `${X(0)},14 ` + c.dd.map((v, i) => `${X(i)},${YD(v)}`).join(' ') + ` ${X(n - 1)},14`, style: 'fill:var(--rosso);opacity:.4' }),
    sv('text', { x: m.l - 6, y: 12, 'text-anchor': 'end', style: 'fill:var(--muto);font-size:11px' }, '0'),
    sv('text', { x: m.l - 6, y: YD(mn) + 4, 'text-anchor': 'end', style: 'fill:var(--muto);font-size:11px' }, fmt(mn)),
    sv('text', { x: m.l + 4, y: HD - 12, style: 'fill:var(--muto);font-size:11px' }, 'Drawdown'));
  return h('div', { class: 'grafico curva-q' }, svg, tip, dsv);
}
/* Grafico piccolo e quadrato della riga dell'elenco: stessa curva, un colore per periodo. */
function miniGrafico(mini, S = 56) {
  const svg = sv('svg', { viewBox: `0 0 ${S} ${S}`, class: 'mini', width: S, height: S });
  if (!mini || !mini.y || mini.y.length < 2) return svg;
  const y = mini.y, lo = Math.min(...y, 0), hi = Math.max(...y, 0), n = y.length;
  const X = i => 2 + (S - 4) * i / (n - 1), Y = v => 2 + (S - 4) * (1 - (v - lo) / ((hi - lo) || 1));
  svg.append(sv('line', { x1: 2, x2: S - 2, y1: Y(0), y2: Y(0), style: 'stroke:var(--bordo);stroke-width:1' }));
  (mini.segmenti || [['scoperta', 0, n - 1]]).forEach(([p, i0, i1]) => {
    const j0 = Math.max(0, i0 - 1);
    svg.append(sv('polyline', { points: y.slice(j0, i1 + 1).map((v, k) => `${X(j0 + k)},${Y(v)}`).join(' '), style: `fill:none;stroke:${(FASCE[p] || FASCE.scoperta)[1]};stroke-width:1.5` }));
  });
  return svg;
}
const legendaFasce = c => h('div', { class: 'legenda' }, c.segmenti.map(([p, i0, i1]) => h('span', {}, h('i', { style: `background:${FASCE[p][1]}` }),
  `${FASCE[p][0]} ${c.date[i0]} → ${c.date[i1]}`)));

// ------------------------------------------------------------------ pagina Sistemi
const filtri = { esperimento: '', prodotto: '', lato: '', q: '', scartati: false };
let ordine = { k: 'guadagno', dir: -1 };
const soglia = (S, ore) => { for (const [fino, e] of (S.guadagno_euro || [])) if (fino == null || ore <= fino) return e; return null; };
const colore = ok => ok == null ? '' : ok ? 'pos' : 'neg';
const COLONNE = [
  { k: 'mini', t: '', v: null },
  { k: 'nome', t: 'Nome', v: r => r.nome },
  { k: 'prodotto', t: 'Prodotto', v: r => r.prodotto },
  { k: 'lato', t: 'Lato', v: r => r.lato },
  { k: 'guadagno', t: '€ a trade', title: 'Guadagno medio netto per trade con 1 CFD IG', v: r => (r.misure || {}).guadagno_medio },
  { k: 'dd', t: 'Drawdown €', title: 'Drawdown massimo della curva netta, 1 CFD IG', v: r => (r.misure || {}).drawdown },
  { k: 'costi', t: 'Lordo / costi', title: 'Guadagno lordo diviso spread e costo notturno', v: r => (r.misure || {}).rapporto_costi },
  { k: 'ore', t: 'Ore in mercato', title: 'Durata media di un trade, in ore', v: r => (r.misure || {}).ore_medie },
  { k: 'r2', t: 'R²', title: 'Quanto la curva netta somiglia a una retta', v: r => (r.misure || {}).r2 },
  { k: 'tanno', t: 'Trade / anno', v: r => (r.misure || {}).trade_anno },
  { k: 'oos', t: 'Fuori campione €/trade', title: 'Guadagno medio a trade nella prova finale', v: r => (r.fuori_campione || {}).guadagno_medio },
  { k: 'esito', t: 'Esito', v: r => r.esito === 'candidato' ? 0 : 1 },
];

// ------------------------------------------------------------------ scheda
const sezione = (titolo, costruisci, nota) => {
  let fatto = false;
  const corpo = h('div', { class: 'sez-corpo' });
  const d = h('details', { class: 'sezione' }, h('summary', {}, titolo, nota ? h('span', { class: 'muto' }, ' · ' + nota) : null), corpo);
  d.addEventListener('toggle', () => { if (d.open && !fatto) { fatto = true; corpo.append(costruisci()); } });
  return d;
};
const voceF = (g, nome) => [...(g.filtri || []), ...(g.statistico || [])].find(v => v.nome === nome);
const colEsito = e => e === 'verde' || e === 'rosso' || e === 'giallo' ? e : '';
function grande(etichetta, valore, sogliaTesto, esito, sotto, title) {
  return h('div', { class: 'num6 ' + colEsito(esito), title }, h('div', { class: 'et' }, etichetta), h('div', { class: 'gr' }, valore),
    h('div', { class: 'so' }, sogliaTesto), sotto ? h('div', { class: 'su' }, sotto) : null);
}
async function paginaScheda(esp, id) {
  const mio = giro;
  const d = await api(`/sistemi/${esp}/${id}`);
  const sc = d.scheda, g = sc.giudizio || {}, ih = d.intestazione, m = sc.misure || {}, S = d.soglie || {}, pf = sc.prova_finale;
  const testata = h('div', { class: 'testata' },
    h('div', { class: 'titolo' }, h('a', { href: '#/ricerche' }, '← Ricerche'), h('h1', { style: 'margin:0' }, d.nome),
      badge(g.esito, g.esito ? ESITI[g.esito] : 'Non giudicato'), h('span', { class: 'muto' }, `${sc.prodotto} · ${d.lato} · barre da ${ih.barre} min`)),
    h('p', { class: 'muto', style: 'margin:6px 0 0' }, d.riga.parametri ? Object.entries(d.riga.parametri).map(([k, v]) => `${k} = ${v}`).join(' · ') : ''));
  // curva: tutto il tempo se ci sono i dati in euro, altrimenti la sola scoperta in escursioni
  let cv = d.completa, fmt = v => nf(v, 0) + ' €';
  if (!cv && d.curva) { const e = d.curva.esc; cv = { date: d.curva.date, cum: e.cum, dd: e.dd, segmenti: [['scoperta', 0, e.cum.length - 1]] }; fmt = v => nf(v, 1); }
  const sinistra = h('div', { class: 'col-curva' }, cv ? [h('div', { class: 'titolo-fig' }, d.completa ? 'Profitto netto cumulato, 1 CFD IG' : 'Profitto netto cumulato, escursioni medie'),
    curvaQuadrata(cv, fmt), legendaFasce(cv)] : h('p', { class: 'muto' }, 'Curva giornaliera non disponibile.'));
  // sei numeri
  const fGm = voceF(g, 'Guadagno medio per trade'), fTa = voceF(g, 'Trade l\'anno'), fR2 = voceF(g, 'Regolarità della curva (R²)');
  const rc = m.rapporto_costi, esitoCosti = rc == null ? null : rc >= S.rapporto_costi ? 'verde' : rc >= 2 ? 'giallo' : 'rosso';
  const sgGm = m.ore_medie == null ? null : soglia(S, m.ore_medie);
  const destra = h('div', { class: 'col-num' },
    h('div', { class: 'sei' },
      grande('Guadagno medio a trade', m.guadagno_medio == null ? '–' : nf(m.guadagno_medio, 1) + ' €', sgGm == null ? 'soglia: dipende dalla durata' : `soglia ${sgGm} € (trade di ${nf(m.ore_medie, 1)} ore)`, fGm && fGm.esito, '1 CFD IG, al netto di spread e notte', 'Guadagno medio netto per trade con 1 CFD IG'),
      grande('Drawdown massimo', m.drawdown == null ? '–' : eur(m.drawdown), 'nessuna soglia', null, m.utile == null ? '' : `utile ${eur(m.utile)} · utile / drawdown ${nf(m.utile_su_dd, 1)}`, 'Discesa massima della curva netta, 1 CFD IG'),
      grande('Lordo / costi', nf(rc, 1), `riferimento ${S.rapporto_costi || 3}`, esitoCosti, m.costo_medio == null ? '' : `lordo ${nf(m.lordo_medio, 1)} € · costi ${nf(m.costo_medio, 1)} € a trade`, 'Quante volte il guadagno lordo copre spread e costo notturno'),
      grande('Tempo in mercato', m.ore_medie == null ? '–' : nf(m.ore_medie, 1) + ' ore', 'nessuna soglia', null, m.in_mercato == null ? 'ore medie per trade' : `ore medie per trade · ${pc(m.in_mercato)} del tempo`, 'Ogni posizione aperta blocca margine'),
      grande('Regolarità (R²)', nf(m.r2), `soglia ${S.r2 == null ? '–' : nf(S.r2)}`, fR2 && fR2.esito, m.anni_positivi == null ? '' : `anni positivi ${pc(m.anni_positivi)} (soglia ${pc(S.anni_positivi)})`, 'Quanto la curva netta somiglia a una retta'),
      grande('Trade l\'anno', nf(m.trade_anno, 0), `soglia ${S.trade_anno == null ? '–' : nf(S.trade_anno, 0)}`, fTa && fTa.esito, m.n == null ? '' : `${m.n} trade in 13 anni`, 'Numero medio di trade in un anno')),
    h('div', { class: 'fuori' }, h('strong', {}, 'Fuori campione '), pf && pf.avanti ? [`(${pf.avanti.da} → ${pf.avanti.a}): ${pf.avanti.n} trade · utile `, h('span', { class: segno(pf.avanti.utile) }, eur(pf.avanti.utile)),
      ` · guadagno medio ${nf(pf.avanti.guadagno_medio, 1)} € a trade` + (m.guadagno_medio ? ` (${pc(pf.avanti.guadagno_medio / m.guadagno_medio)} di quello in-sample)` : '') + (pf.gia_usata ? ' · prova già usata' : '')] :
      pf ? 'nessun trade nel periodo di prova.' : (g.passa_scoperta === false ? 'non eseguita: il sistema non ha passato i filtri sulla scoperta.' : 'non eseguita.')));
  const ia = d.commento_ia;
  const esito = h('div', { class: 'esito-riga ' + (g.esito || '') }, badge(g.esito, g.esito ? ESITI[g.esito] : 'Non giudicato'),
    h('span', {}, g.motivo || 'Giudizio non calcolato: esegui `python -m motore.cli esperimento arricchisci <nome>`.'));
  const iaBox = h('div', { class: 'ia' }, h('div', { class: 'et' }, 'Commento dell\'IA, non deterministico'),
    ia ? [h('div', { class: 'muto', style: 'margin-bottom:6px' }, `Scritto il ${ia.data || 'data non indicata'} · modello ${ia.modello || 'non indicato'}`), md(ia.testo)] : h('p', { class: 'muto' }, 'Non ancora scritto.'));
  vedi(mio, testata, h('div', { class: 'prima-vista' }, sinistra, destra), esito, iaBox,
    sezione('Ipotesi e fonte', () => h('div', {}, h('p', {}, h('strong', {}, 'Ipotesi: '), ih.ipotesi), h('p', {}, h('strong', {}, 'Meccanismo: '), ih.meccanismo),
      h('p', { class: 'muto' }, h('a', { href: `#/esperimenti/${esp}` }, 'Esperimento'), ` · fonte: ${ih.fonte}`))),
    sezione('Altri numeri', () => riepilogo(d)),
    sezione('Curva, Monte Carlo e anni', () => curva(d)),
    sezione('Giudizio: filtri, cancello e gruppi', () => giudizio(d)),
    sezione('Robustezza', () => robustezza(d)),
    sezione('Calendario', () => calendario(d)),
    sezione('Trade', () => trade(d)),
    sezione('Codice ProRealCode', () => codice(d)),
    sezione('Decisione e verifica su ProRealTime', () => decisione(d), d.decisione.stato));
}
const num = (e, v, title, cl) => h('div', { class: 'numero', title }, h('div', { class: 'v ' + (cl || '') }, v), h('div', { class: 'e' }, e));
function riepilogo(d) {
  const s = d.scheda, b = s.backtest || {}, sc = s.scheda || {}, r = s.robustezza || {}, e = r.euro || {};
  return h('div', { class: 'numeri' },
    num('Trade', b.n), num('Media per trade (esc.)', nf(b.media_esc, 3), 'Netto dei costi IG, in escursioni medie giornaliere', segno(b.media_esc)),
    num('Media lorda (esc.)', nf(b.lorda_esc, 3), 'Prima dei costi'), num('Profit factor', nf(b.pf)),
    num('Sharpe', nf(b.sharpe)), num('DSR', nf((sc['1_sharpe'] || {}).dsr, 3), 'Probabilità che lo Sharpe sia reale dopo tutte le prove'),
    num('PBO', nf((sc['2_pbo'] || {}).pbo, 2), 'Probabilità di sovradattamento della famiglia di prove'),
    num('CPCV mediana', nf((sc['2_cpcv'] || {}).mediana, 2), 'Sharpe mediano sulle combinazioni di anni'),
    num('CPCV 10° percentile', nf((sc['2_cpcv'] || {}).p10, 2)),
    num('2019-2023 (esc.)', nf(b.media_recente_esc, 3), '', segno(b.media_recente_esc)),
    num('Drawdown max (esc.)', nf(b.dd_max_esc, 1)),
    num('Netto € 1 CFD', eur(e.profitto), 'Profitto 2011-2023 per 1 CFD IG', segno(e.profitto)), num('Drawdown € 1 CFD', eur(e.drawdown)),
    num('Trade medio €', e.trade_medio == null ? '–' : nf(e.trade_medio, 1) + ' €'));
}
let unitaCurva = 'esc';
function curva(d) {
  const c = d.curva;
  if (!c) return h('p', { class: 'muto' }, 'Curva giornaliera non disponibile.');
  const u = c.unita.includes(unitaCurva) ? unitaCurva : 'esc', x = c[u];
  const fmt = u === 'eur' ? v => nf(v, 0) + ' €' : v => nf(v, 1);
  const cont = h('div');
  const bott = c.unita.length > 1 ? h('div', { class: 'filtri' }, c.unita.map(k => h('button', { class: k === u ? 'primario' : '', onclick: () => { unitaCurva = k; cont.replaceWith(curva(d)); } },
    k === 'eur' ? '€ con 1 CFD IG' : 'Escursioni medie'))) : null;
  const anni = [...new Set(c.date.map(t => t.slice(0, 4)))], fine = a => { let k = -1; c.date.forEach((t, i) => { if (t.slice(0, 4) <= a) k = i; }); return k; };
  const perAnno = anni.map((a, i) => x.cum[fine(a)] - (i ? x.cum[fine(anni[i - 1])] : 0));
  const mcs = ((d.scheda.scheda || {})['6_montecarlo']) || null;
  cont.append(bott, h('h3', {}, 'Profitto netto cumulato'),
    grafico({ date: c.date, serie: [{ y: x.cum, colore: 'var(--accento)' }], banda: x.mc, fmt }),
    x.mc ? h('p', { class: 'muto' }, `Fascia: dal 5° al 95° percentile di ${x.mc.percorsi} simulazioni a blocchi di ${x.mc.blocco} giorni; linea tratteggiata: mediana.`) : null,
    h('h3', {}, 'Drawdown'), grafico({ date: c.date, serie: [{ y: x.dd, colore: 'var(--rosso)', area: true }], fmt, altezza: 160 }),
    h('h3', {}, 'Risultato per anno'), barreGrafico(anni, perAnno, fmt),
    mcs && mcs.blocchi ? h('div', { class: 'tabella-cont', style: 'margin-top:12px' }, h('table', {},
      h('thead', {}, h('tr', {}, h('th', {}, 'Monte Carlo (escursioni)'), ['5°', '50°', '95°'].map(p => h('th', {}, p + ' percentile')))),
      h('tbody', {}, [['Drawdown a blocchi', mcs.blocchi.drawdown], ['Drawdown rimescolato', (mcs.rimescolato_giorni || {}).drawdown],
        ['Peggior serie di perdite a blocchi', mcs.blocchi.serie_perdite]].map(([n, v]) => h('tr', {}, h('td', {}, n), ['p5', 'p50', 'p95'].map(k => h('td', {}, v ? nf(v[k], 1) : '–'))))))) : null);
  return cont;
}
function tabellaVoci(titolo, voci, nota) {
  return h('div', { class: 'pannello' }, h('h3', { style: 'margin-top:0' }, titolo), nota ? h('p', { class: 'muto' }, nota) : null,
    h('div', { class: 'tabella-cont' }, h('table', {}, h('thead', {}, h('tr', {}, ['Voce', 'Valore', 'Soglia', 'Esito', 'Cosa misura'].map((t, i) => h('th', { class: i === 4 || i === 0 ? 'sx' : '' }, t)))),
      h('tbody', {}, [...voci].sort((a, b) => GRAVITA[a.esito] - GRAVITA[b.esito]).map(v => h('tr', {},
        h('td', { class: 'sx' }, v.nome), h('td', {}, typeof v.valore === 'number' ? nf(v.valore, 3) : v.valore === true ? 'sì' : v.valore === false ? 'no' : '–'),
        h('td', {}, v.soglia), h('td', {}, badge(v.esito, v.esito)), h('td', { class: 'sx', style: 'white-space:normal;min-width:260px' }, v.spiegazione)))))));
}
function giudizio(d) {
  const g = d.scheda.giudizio;
  if (!g) return h('p', { class: 'muto' }, 'Giudizio non calcolato: esegui `python -m motore.cli esperimento arricchisci <nome>`.');
  const ordineG = Object.entries(g.gruppi).sort((a, b) => GRAVITA[a[1].esito] - GRAVITA[b[1].esito]);
  return h('div', {},
    h('p', {}, h('strong', {}, 'Esito: '), badge(g.esito), ' ', g.motivo),
    g.filtri ? tabellaVoci('Filtri di Andrea', g.filtri, 'Chi non li passa è scartato.') : null,
    g.statistico ? tabellaVoci('Cancello statistico', g.statistico) : null,
    g.prova_finale ? tabellaVoci('Prova finale', g.prova_finale, 'Si fa una volta sola, solo per chi ha passato i filtri e il cancello sulla scoperta.') : null,
    h('h3', {}, 'Dettaglio per gruppo (non decide l\'esito)'),
    h('div', { class: 'gruppi' }, ordineG.map(([k, x]) => h('div', { class: 'gruppo ' + x.esito }, h('div', { class: 'nome' }, x.nome, ' ', badge(x.esito, x.esito)), h('div', { class: 'sintesi' }, x.sintesi)))),
    ordineG.map(([k, x]) => tabellaVoci(x.nome, x.voci)));
}
function robustezza(d) {
  const r = d.scheda.robustezza;
  if (!r) return h('p', { class: 'muto' }, 'Robustezza non calcolata: esegui `esperimento arricchisci`.');
  const righe = [['Candidato (costi normali)', r.base], ['Costi doppi', r.costi_doppi]];
  if (r.ingresso_spostato) righe.push(['Ingresso 15 minuti prima', r.ingresso_spostato.meno_15], ['Ingresso 15 minuti dopo', r.ingresso_spostato.piu_15]);
  righe.push(['Specchio (altro lato)', r.specchio]);
  if (r.gemello) righe.push([`Gemello ${r.gemello.prodotto}`, r.gemello]);
  const v = r.vicini, rg = r.regimi;
  return h('div', {},
    h('h3', {}, 'Confronto delle varianti'),
    h('div', { class: 'tabella-cont' }, h('table', {}, h('thead', {}, h('tr', {}, [['Variante'], ['Trade'], ['Media (esc.)', 'Netto per trade in escursioni'], ['PF', 'Profit factor'], ['Sharpe'], ['Anni +', 'Quota di anni positivi'], ['2019-2023']].map(([t, ti]) => h('th', { title: ti }, t)))),
      h('tbody', {}, righe.map(([n, x]) => h('tr', {}, h('td', {}, n), h('td', {}, x.n), h('td', { class: segno(x.media_esc) }, nf(x.media_esc, 3)), h('td', {}, nf(x.pf)),
        h('td', {}, nf(x.sharpe)), h('td', {}, pc(x.anni_positivi)), h('td', { class: segno(x.media_recente_esc) }, nf(x.media_recente_esc, 3))))))),
    r.ingresso_spostato ? null : h('p', { class: 'muto' }, 'Ingresso spostato: non calcolato (solo con barre fino a 15 minuti).'),
    r.gemello ? null : h('p', { class: 'muto' }, 'Gemello: nessun prodotto gemello con costi nel catalogo.'),
    h('h3', {}, 'Finestre di 12 mesi (passo di 3 mesi)'),
    h('div', { class: 'finestre' }, (r.finestre_12_mesi || []).map(f => h('div', { class: 'finestra ' + (f.n === 0 ? 'grigio' : f.profitto > 0 ? 'verde' : 'rosso'),
      title: `${f.da} / ${f.a}: ${nf(f.profitto, 1)} escursioni, ${f.n} trade` }))),
    h('p', { class: 'muto' }, 'Verde: profitto netto positivo nella finestra; rosso: negativo; grigio: nessun trade.'),
    h('h3', {}, 'Combinazioni vicine'),
    v ? h('div', {}, h('p', {}, `Sharpe del candidato ${nf(v.sharpe_candidato)}; mediana dei ${v.n} vicini ${nf(v.mediana)}; rapporto ${nf(v.rapporto)} `, badge(v.stabile ? 'verde' : 'giallo', v.stabile ? 'zona stabile' : 'zona poco stabile'), h('span', { class: 'muto' }, ' (stabile da 0,70)')),
      h('div', { class: 'tabella-cont' }, h('table', {}, h('thead', {}, h('tr', {}, h('th', {}, 'Parametri'), h('th', {}, 'Sharpe'))),
        h('tbody', {}, v.vicini.map(x => h('tr', {}, h('td', {}, Object.entries(x.parametri).map(([k, q]) => `${k}=${q}`).join(', ')), h('td', {}, nf(x.sharpe)))))))) :
      h('p', { class: 'muto' }, 'Nessun vicino nel registro.'),
    h('h3', {}, 'Regimi di volatilità'),
    rg ? h('p', {}, `Mediana dell'escursione media: ${nf(rg.mediana_esc, 1)} punti. Giorni sopra la mediana: ${rg.sopra.n} trade, media ${nf(rg.sopra.media, 3)}. Giorni sotto: ${rg.sotto.n} trade, media ${nf(rg.sotto.media, 3)}.`) :
      h('p', { class: 'muto' }, 'Non calcolati.'));
}
function calendario(d) {
  const c = (d.scheda.robustezza || {}).calendario;
  if (!c || !Object.keys(c).length) return h('p', { class: 'muto' }, 'Calendario non disponibile.');
  const mesi = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic'];
  const mx = Math.max(...Object.values(c).flatMap(a => Object.values(a).map(Math.abs)), 1e-9);
  const colore = v => v == null ? '' : `background:rgba(${v >= 0 ? '47,178,106' : '229,83,75'},${Math.min(.85, .12 + .73 * Math.abs(v) / mx)})`;
  return h('div', {}, h('p', { class: 'muto' }, 'Profitto netto per mese di uscita, in escursioni medie giornaliere.'),
    h('div', { class: 'tabella-cont' }, h('table', { class: 'cal' }, h('thead', {}, h('tr', {}, h('th', {}, 'Anno'), mesi.map(m => h('th', {}, m)), h('th', {}, 'Anno'))),
      h('tbody', {}, Object.keys(c).sort().map(a => { const tot = Object.values(c[a]).reduce((x, y) => x + y, 0);
        return h('tr', {}, h('td', {}, a), mesi.map((_, i) => { const v = c[a][i + 1]; return h('td', { style: colore(v), title: v == null ? 'nessun trade' : nf(v, 2) }, v == null ? '' : nf(v, 1)); }),
          h('td', { style: colore(tot) + ';font-weight:600' }, nf(tot, 1))); })))));
}
let paginaTrade = 0;
function trade(d) {
  const t = d.trade;
  if (!t) return h('p', { class: 'muto' }, 'Elenco dei trade non disponibile.');
  const ix = k => t.colonne.indexOf(k), righe = t.righe, n = righe.length, PAG = 50;
  const col = k => righe.map(r => r[ix(k)]);
  const netto = col('netto'), lordo = col('lordo'), vinc = netto.filter(x => x > 0), per = netto.filter(x => x < 0);
  const somma = a => a.reduce((x, y) => x + y, 0), pf = somma(per) ? somma(vinc) / -somma(per) : null;
  const motivi = {}; if (ix('motivo') >= 0) col('motivo').forEach(m => { motivi[m] = (motivi[m] || 0) + 1; });
  const punti = ix('punti') >= 0 ? col('punti') : null;
  const corpo = h('tbody'), info = h('span', { class: 'muto' });
  paginaTrade = Math.min(paginaTrade, Math.floor((n - 1) / PAG));
  const cont = h('div', {}, h('div', { class: 'numeri' }, num('Trade', n), num('Vincenti', pc(vinc.length / n)), num('Media netta (esc.)', nf(somma(netto) / n, 3), '', segno(somma(netto))),
    num('Media lorda (esc.)', nf(somma(lordo) / n, 3)), num('Profit factor', nf(pf)), num('Vincita media (esc.)', nf(vinc.length ? somma(vinc) / vinc.length : null, 3)),
    num('Perdita media (esc.)', nf(per.length ? somma(per) / per.length : null, 3)), num('Durata media (barre)', nf(somma(col('barre')) / n, 1)),
    punti ? num('Media netta (punti)', nf(somma(punti) / n, 2)) : null, ...Object.entries(motivi).map(([m, k]) => num('Uscita: ' + m, k))));
  function mostra() {
    corpo.replaceChildren(...righe.slice(paginaTrade * PAG, paginaTrade * PAG + PAG).map(r => h('tr', {}, t.colonne.map((c, i) =>
      h('td', { class: (c === 'netto' || c === 'punti' || c === 'lordo') ? segno(r[i]) : (c === 'ingresso' || c === 'uscita' || c === 'motivo' ? 'sx' : '') },
        typeof r[i] === 'number' ? nf(r[i], c === 'barre' ? 0 : 3) : r[i])))));
    info.textContent = `${paginaTrade * PAG + 1}-${Math.min(n, paginaTrade * PAG + PAG)} di ${n}`;
  }
  const mover = k => () => { paginaTrade = Math.max(0, Math.min(Math.floor((n - 1) / PAG), paginaTrade + k)); mostra(); };
  cont.append(h('h3', {}, 'Elenco'), h('div', { class: 'riga-pag' }, h('button', { onclick: mover(-1) }, '← Prima'), h('button', { onclick: mover(1) }, 'Dopo →'), info),
    h('div', { class: 'tabella-cont' }, h('table', {}, h('thead', {}, h('tr', {}, t.colonne.map(c => h('th', { class: ['ingresso', 'uscita', 'motivo'].includes(c) ? 'sx' : '',
      title: { lordo: 'Prima dei costi, in escursioni', netto: 'Dopo i costi, in escursioni', punti: 'Netto in punti di prezzo', barre: 'Barre tenute in posizione' }[c] }, c)))), corpo)));
  mostra();
  return cont;
}
function codice(d) {
  const c = d.codice;
  if (!c) return h('p', { class: 'muto' }, 'Codice non disponibile: esegui `esperimento arricchisci`.');
  const nome = `${d.esperimento}-${d.id}.prc`, stato = h('span', { class: 'muto' });
  function copia() {
    const fine = ok => { stato.textContent = ok ? 'Copiato.' : 'Copia non riuscita: seleziona il testo a mano.'; };
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(c.codice).then(() => fine(true), () => fine(false));
    else { const t = h('textarea', { style: 'position:fixed;opacity:0' }); t.value = c.codice; document.body.append(t); t.select(); let ok = false; try { ok = document.execCommand('copy'); } catch (e) { /* niente */ } t.remove(); fine(ok); }
  }
  function scarica() {
    const a = h('a', { href: URL.createObjectURL(new Blob([c.codice], { type: 'text/plain;charset=utf-8' })), download: nome });
    document.body.append(a); a.click(); a.remove();
  }
  return h('div', {},
    c.completo === false ? h('div', { class: 'avviso' }, 'Traduzione incompleta: ', (c.da_tradurre || []).join(', '), '. Cerca i commenti `// DA TRADURRE` nel codice.') : null,
    h('div', { class: 'riga-pag' }, h('button', { class: 'primario', onclick: copia }, 'Copia'), h('button', { onclick: scarica }, 'Scarica .prc'), stato),
    h('p', { class: 'muto' }, 'Console di gestione con Aggressivita = 0 (stesso rischio in euro per ogni trade). Stop e target in punti, fissati con l\'escursione della barra di decisione.'),
    h('pre', { class: 'codice' }, c.codice));
}
function decisione(d) {
  const x = d.decisione, v = x.verifica;
  const stato = h('select', {}, STATI.map(s => h('option', { value: s, selected: s === x.stato }, s)));
  const nota = h('textarea', {}, x.nota);
  const data = h('input', { type: 'date', value: v.data });
  const esito = h('select', {}, [['', '—'], ['confermata', 'confermata'], ['non confermata', 'non confermata'], ['inconcludente', 'inconcludente']].map(([k, t]) => h('option', { value: k, selected: k === v.esito }, t)));
  const note = h('textarea', {}, v.note), msg = h('span', { class: 'muto' }, x.aggiornato ? `Ultimo salvataggio: ${x.aggiornato}` : '');
  async function salva() {
    try {
      const r = await api(`/sistemi/${d.esperimento}/${d.id}/decisione`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stato: stato.value, nota: nota.value, verifica: { data: data.value, esito: esito.value, note: note.value } }) });
      msg.textContent = `Salvato (${r.aggiornato}).`; msg.className = 'pos';
    } catch (e) { msg.textContent = 'Errore: ' + e.message; msg.className = 'neg'; }
  }
  return h('div', { class: 'cols' },
    h('div', { class: 'pannello' }, h('h3', { style: 'margin-top:0' }, 'Decisione'), h('div', { class: 'campo' }, h('label', {}, 'Stato'), stato), h('div', { class: 'campo' }, h('label', {}, 'Nota'), nota)),
    h('div', { class: 'pannello' }, h('h3', { style: 'margin-top:0' }, 'Verifica su ProRealTime'), h('div', { class: 'campo' }, h('label', {}, 'Data della prova'), data),
      h('div', { class: 'campo' }, h('label', {}, 'Esito'), esito), h('div', { class: 'campo' }, h('label', {}, 'Note'), note)),
    h('div', {}, h('button', { class: 'primario', onclick: salva }, 'Salva'), ' ', msg));
}

// ------------------------------------------------------------------ esperimenti
async function paginaEsperimento(nome) {
  const mio = giro;
  const e = await api('/esperimenti/' + nome), ih = e.intestazione, pr = e.prove, sg = e.soglie;
  const imbuto = pr.dopo_filtri == null ? null : [['Prove', pr.questa], ['Dopo i filtri di Andrea', pr.dopo_filtri], ['Dopo DSR e PBO', pr.dopo_cancello], ['Candidati dopo la prova finale', e.esiti.candidato]];
  vedi(mio, h('p', {}, h('a', { href: '#/ricerche' }, '← Ricerche')), h('h1', {}, nome),
    h('div', { class: 'pannello' }, h('p', {}, h('strong', {}, 'Ipotesi: '), ih.ipotesi), h('p', {}, h('strong', {}, 'Meccanismo: '), ih.meccanismo),
      h('p', {}, h('strong', {}, 'Fonte: '), ih.fonte), h('p', {}, h('strong', {}, 'Direzione attesa: '), ih.direzione, ` · modo ${ih.modo} · barre da ${ih.barre} min · ${ih.prodotti.join(', ')}${ih.specchio ? ' · con lo specchio' : ''}`),
      h('p', { class: 'muto' }, `Lanciato il ${ih.quando}`)),
    h('h2', {}, 'Prove sul budget'),
    h('div', { class: 'pannello' }, h('p', {}, `${pr.questa} prove in questo esperimento; ${pr.totali_registro} nel registro dopo il lancio; budget ${nf(pr.budget, 0)} (${pc(pr.totali_registro / pr.budget)}).` +
      (pr.sr_minimo != null ? ` Con ${pr.totali_registro} prove serve uno Sharpe di almeno ${nf(pr.sr_minimo)}; l'esperimento cerca ${nf(pr.sr_obiettivo)}.` : '')),
      h('div', { class: 'barra' }, h('div', { style: `width:${Math.min(100, 100 * pr.totali_registro / pr.budget)}%` }))),
    imbuto ? h('div', {}, h('h2', {}, 'Dove si sono fermate le prove'),
      h('div', { class: 'imbuto' }, imbuto.map(([t, n]) => h('div', { class: 'riquadro' }, h('div', { class: 'n' }, n), h('div', { class: 'et' }, t)))),
      pr.scartate_per && Object.keys(pr.scartate_per).length ? h('div', { class: 'tabella-cont', style: 'margin-top:10px' }, h('table', {}, h('thead', {}, h('tr', {}, h('th', {}, 'Scartate per'), h('th', {}, 'Prove'))),
        h('tbody', {}, Object.entries(pr.scartate_per).sort((a, b) => b[1] - a[1]).map(([t, n]) => h('tr', {}, h('td', {}, t), h('td', {}, n)))))) : null,
      e.tempi ? h('p', { class: 'muto' }, 'Tempi (secondi): ' + Object.entries(e.tempi).map(([k, v]) => `${k.replace(/_/g, ' ')} ${nf(v, 1)}`).join(' · ')) : null) : null,
    h('h2', {}, 'PBO ed effettivi per famiglia'),
    h('div', { class: 'tabella-cont' }, h('table', {}, h('thead', {}, h('tr', {}, h('th', {}, 'Famiglia'), h('th', {}, 'Prodotto'), h('th', { title: 'Probabilità di sovradattamento della selezione; soglia ' + sg.pbo }, 'PBO'),
      h('th', { title: 'Numero effettivo di prove indipendenti, per il DSR' }, 'Prove effettive'))),
      h('tbody', {}, Object.entries(e.pbo).flatMap(([f, o]) => Object.entries(o).map(([p, v]) => h('tr', {}, h('td', {}, f), h('td', {}, p), h('td', { class: v != null && v < sg.pbo ? 'pos' : 'neg' }, nf(v)), h('td', {}, nf(pr.n_effettivo[f], 1)))))))),
    h('h2', {}, 'Sistemi di questo esperimento'),
    e.candidati.length ? h('div', { class: 'tabella-cont' }, h('table', {}, h('thead', {}, h('tr', {}, ['Id', 'Parametri', 'Esito', 'Motivo', 'Trade', '€ a trade'].map(t => h('th', {}, t)))),
      h('tbody', {}, e.candidati.map(c => h('tr', { class: 'clic', onclick: () => { location.hash = `#/sistemi/${nome}/${c.id}`; } }, h('td', {}, c.id),
        h('td', { class: 'sx' }, Object.entries(c.parametri || {}).map(([k, v]) => `${k}=${v}`).join(', ')), h('td', {}, badge(c.esito)), h('td', { class: 'sx' }, c.motivo || ''),
        h('td', {}, c.n), h('td', {}, c.misure && c.misure.guadagno_medio != null ? nf(c.misure.guadagno_medio, 1) + ' €' : '–')))))) : h('p', { class: 'muto' }, 'Nessuna prova ha passato i filtri e il cancello statistico: nessun sistema da mostrare.'),
    h('h2', {}, 'Resoconto'), e.resoconto ? h('div', { class: 'pannello' }, md(e.resoconto)) : h('p', { class: 'muto' }, 'Nessun resoconto scritto.'));
}

// ------------------------------------------------------------------ ricerche
const LIVELLI = { L0: 'Regola semplice', L2: 'Ingresso aggiunto', L3: 'Uscita' };
const nE = (x, d = 1) => x == null ? '–' : nf(x, d) + ' €';
const dataIt = q => q ? new Date(q).toLocaleString('it-IT', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '–';
async function paginaRicerche() {
  const mio = giro;
  const l = await api('/ricerche');
  const riga = r => {
    const vai = () => { location.hash = r.formato === 'esperimento' ? '#/esperimenti/' + r.nome : r.formato === 'campagna' ? '#/campagne/' + r.nome : '#/ricerche/' + r.nome; };
    const stato = r.formato === 'campagna' && r.stato === 'in corso' ? h('span', { class: 'badge giallo' }, `in corso · ${r.ricerche_finite} di ${r.ricerche} ricerche`)
      : r.stato === 'in corso' ? h('span', { class: 'badge giallo' }, `in corso · ${r.prove || 0} prove`) : r.stato === 'fallita' ? h('span', { class: 'badge rosso' }, 'fallita')
      : r.candidati ? h('span', { class: 'badge candidato' }, `${r.candidati} da provare`) : h('span', { class: 'badge non_giudicato' }, 'nessun sistema');
    return h('tr', { class: 'clic', onclick: vai }, h('td', { class: 'sx desc' }, h('strong', {}, r.nome), h('div', { class: 'muto' }, r.formato === 'campagna' ? `campagna di ${r.ricerche} ricerche · ` + (r.ipotesi || '').slice(0, 90) + '…' : r.formato === 'esperimento' ? 'formato precedente: solo ampiezza, in-sample 2011-2023' : (r.ipotesi || '').slice(0, 110) + ((r.ipotesi || '').length > 110 ? '…' : ''))),
      h('td', {}, dataIt(r.quando)), h('td', { class: 'desc' }, r.prodotto ? `${r.prodotto} · ${r.barre} min` : '–'), h('td', {}, r.ampiezza == null ? '–' : nf(r.ampiezza, 0)), h('td', {}, r.radici ?? '–'), h('td', {}, r.prove == null ? '–' : nf(r.prove, 0)), h('td', {}, stato));
  };
  vedi(mio, h('h1', {}, 'Ricerche'),
    h('p', { class: 'muto' }, 'Ogni ricerca prova molte regole semplici, approfondisce le migliori e mostra solo i sistemi che superano tutti i filtri. Come funziona: ', h('a', { href: '#/come-funziona' }, 'qui'), '.'),
    l.length ? h('div', { class: 'tabella-cont' }, h('table', {}, h('thead', {}, h('tr', {}, [['Ricerca', 'sx'], ['Lanciata'], ['Prodotto'], ['Regole semplici'], ['Radici approfondite'], ['Prove totali'], ['Risultato']].map(([t, c]) => h('th', { class: c || null }, t)))),
      h('tbody', {}, l.map(riga)))) : h('p', { class: 'muto' }, 'Nessuna ricerca. Comando: python -m motore.albero lancia esperimenti/<nome>.json'));
}
const STRATI_NOME = { forza: 'Forza bruta', filtro1: 'Filtro 1', molt1: 'Moltiplicazione 1', filtro2: 'Filtro 2', molt2: 'Moltiplicazione 2', filtro3: 'Filtro 3: i finali',
  ampiezza: 'Regole provate', L0: 'Primo setaccio', radici: 'Radici scelte', L1: 'Controllo della radice', L2: 'Ingressi', L3: 'Uscite', L4: 'Verifica', finale: 'Da provare su ProRealTime' };
const STRATI_COL = { forza: 'var(--f-wf)', filtro1: 'var(--f-in)', molt1: 'var(--f-wf)', filtro2: 'var(--f-in)', molt2: 'var(--f-wf)', filtro3: 'var(--f-in)', ampiezza: 'var(--f-in)', L0: 'var(--f-in)', radici: 'var(--f-in)', L1: 'var(--f-vic)', L2: 'var(--f-vic)', L3: 'var(--f-vic)', L4: 'var(--f-wf)', finale: 'var(--f-out)' };
/* Imbuto: una riga per strato, barra lunga in proporzione (scala logaritmica) al numero di regole che lo passano. */
function imbutoSVG(imb) {
  const W = 640, RH = 34, H = imb.length * RH + 6, max = Math.log10(Math.max(...imb.map(x => x.n || 1)) + 1), L = 190, BW = W - L - 150;
  const svg = sv('svg', { viewBox: `0 0 ${W} ${H}`, class: 'imbuto-svg', role: 'img', 'aria-label': 'Quante regole passano ogni strato' });
  imb.forEach((x, k) => {
    const y = 4 + k * RH, w = x.n ? Math.max(4, BW * Math.log10(x.n + 1) / max) : 0, cx = L + BW / 2;
    svg.append(sv('text', { x: L - 12, y: y + RH / 2 + 4, 'text-anchor': 'end', style: 'fill:var(--testo);font-size:13px' }, STRATI_NOME[x.strato] || x.nome));
    svg.append(sv('rect', { x: cx - BW / 2, y: y + 5, width: BW, height: RH - 10, rx: 4, style: 'fill:var(--bordo);opacity:.35' }));
    if (w) svg.append(sv('rect', { x: cx - w / 2, y: y + 5, width: w, height: RH - 10, rx: 4, style: `fill:${STRATI_COL[x.strato] || 'var(--f-in)'}` }, sv('title', {}, x.nome)));
    svg.append(sv('text', { x: L + BW + 12, y: y + RH / 2 + 5, style: `font-size:15px;font-weight:700;fill:${x.n ? 'var(--testo)' : 'var(--rosso)'}` }, nf(x.n, 0)));
    if (x.provati != null) svg.append(sv('text', { x: L + BW + 12 + 9 * String(x.n).length, y: y + RH / 2 + 5, style: 'font-size:11px;fill:var(--muto)' }, x.tipo === 'filtra' ? ` scelte fra ${nf(x.provati, 0)} che passano` : ` su ${nf(x.provati, 0)} provate`));
  });
  return svg;
}
const MOTIVI_CHIARI = [[/^Batte la ricerca sul rumore/, 'la ricerca sul rumore fa altrettanto bene'], [/^Pronto|^Guadagno medio in euro/, 'guadagnano troppo poco a trade, anche tenendo solo i trade migliori'], [/^t del guadagno/, 'guadagno medio non distinguibile dal caso'],
  [/^Trade l'anno/, "troppo pochi trade l'anno"], [/^Mediana fuori campione/, 'perdono sugli anni lasciati fuori'], [/^Gemello/, "perdono sull'Euro Stoxx con la stessa regola"],
  [/^Metà/, 'perdono in una delle due metà del periodo'], [/^Segnale|^D1|^D2/, "il guadagno viene dall'ora o dalla salita del DAX, non dalla regola"],
  [/^Batte i filtri/, 'non battono i filtri a caso'], [/^Migliora il genitore|^Soglie vicine|^I trade tolti/, 'non migliorano davvero la regola di partenza'],
  [/^Utile\/drawdown/, "l'uscita non migliora utile/drawdown"], [/^Scelta fra/, 'la scelta non regge sugli anni lasciati fuori'],
  [/^Costi doppi/, 'non reggono costi doppi'], [/^DSR/, 'non reggono il conto di tutte le prove fatte'], [/^Walk-forward/, 'la ricerca rifatta anno per anno non guadagna abbastanza'],
  [/^Regolarità|^Anni positivi/, 'curva poco regolare']];
const motivoChiaro = m => { if (!m) return ''; const x = MOTIVI_CHIARI.find(([re]) => re.test(m)); return x ? x[1] : m.split(':')[0]; };
function perche(a) {
  const conta = {};
  a.nodi.filter(n => n.esito === 'scartato').forEach(n => { const k = motivoChiaro(n.motivo); conta[k] = (conta[k] || 0) + 1; });
  (a.cicli || []).forEach(c => Object.entries(c.motivi || {}).forEach(([m, n]) => { conta[m] = (conta[m] || 0) + n; }));
  const fin = {};
  a.foglie.filter(f => f.esito !== 'candidato').forEach(f => (f.porte || []).filter(p => p.esito === 'rosso' || p.esito === 'grigio')
    .forEach(p => { const k = motivoChiaro(p.nome); fin[k] = (fin[k] || 0) + 1; }));
  const righe = Object.entries(conta).sort((x, y) => y[1] - x[1]).slice(0, 4);
  const righeF = Object.entries(fin).sort((x, y) => y[1] - x[1]);
  if (righeF.length) return h('div', {}, h('div', { class: 'et' }, 'Perché si fermano'), h('ul', { class: 'perche' }, righe.map(([t, n]) => h('li', {}, h('strong', {}, nf(n, 0)), ' ', t))),
    h('div', { class: 'et' }, `I ${a.foglie.length} sistemi finali`), h('ul', { class: 'perche' }, righeF.map(([t, n]) => h('li', {}, h('strong', {}, String(n)), ' ', t))));
  return righe.length ? h('div', {}, h('div', { class: 'et' }, 'Perché si fermano'), h('ul', { class: 'perche' }, righe.map(([t, n]) => h('li', {}, h('strong', {}, nf(n, 0)), ' ', t)))) : null;
}
function vicini(a) {
  const l0 = a.nodi.filter(n => n.livello === 'L0').sort((x, y) => (y.misure.M || 0) - (x.misure.M || 0)).slice(0, 10);
  return h('div', { class: 'tabella-cont' }, h('table', {}, h('thead', {}, h('tr', {}, [['', ''], ['Regola', 'sx'], ['€ a trade', '', 'Con la volatilità di oggi, 1 CFD IG, netto'], ['Trade l\'anno'], ['Margine', '', 'Utile annuo diviso il guadagno di 12 trade alla soglia: serve almeno 1,5 per sperare che un filtro porti la regola sopra i 20 €'], ['t', '', 'Quanto il guadagno medio è lontano dal caso: serve almeno 2'], ['Dove si ferma', 'sx']].map(([t, c, ti]) => h('th', { class: c || null, title: ti || null }, t)))),
    h('tbody', {}, l0.map(n => { const m = n.misure; return h('tr', {}, h('td', {}, miniGrafico({ y: n.mini })), h('td', { class: 'sx' }, n.etichetta), h('td', {}, nE(m.euro_oggi)), h('td', {}, nf(m.trade_anno, 0)),
      h('td', { class: (m.M || 0) >= 1.5 ? 'pos' : 'neg' }, nf(m.M, 2)), h('td', { class: (m.t || 0) >= 2 ? 'pos' : 'neg' }, nf(m.t, 1)), h('td', { class: 'sx muto' }, n.motivo ? motivoChiaro(n.motivo) : (n.scelta === 'radice' ? 'scelta come radice' : n.scelta || ''))); }))));
}
function codiceFoglia(f) {
  const c = f.prorealcode;
  if (!c) return h('p', { class: 'muto' }, 'Codice non generato.');
  const pre = h('pre', { class: 'codice' }, c.codice);
  const nome = (f.etichetta || 'sistema').replace(/[^A-Za-z0-9]+/g, '-').slice(0, 40) + '.txt';
  return h('div', {}, h('div', { class: 'filtri' },
    h('button', { type: 'button', onclick: () => { navigator.clipboard && navigator.clipboard.writeText(c.codice); } }, 'Copia'),
    h('a', { href: URL.createObjectURL(new Blob([c.codice], { type: 'text/plain' })), download: nome }, 'Scarica .txt'),
    c.completo ? null : h('span', { class: 'neg' }, 'Da completare a mano: ' + c.da_tradurre.join(', '))), pre);
}
function diarioLista(dia) {
  return h('ol', { class: 'diario' }, (dia || []).map(d => h('li', {}, h('span', { class: 'muto' }, dataIt(d.quando).slice(11) + ' · '), h('strong', {}, d.fase), ' — ', d.testo,
    d.prove != null ? h('span', { class: 'muto' }, ` (prove fatte: ${d.prove})`) : null)));
}
function ramiTabella(a) {
  const figli = {}; a.nodi.forEach(n => { (figli[n.genitore] = figli[n.genitore] || []).push(n); });
  const scelte = {}; (a.livelli || []).forEach(l => { scelte[l.genitore + l.livello] = l; });
  const righe = [];
  const visita = (n, prof) => {
    righe.push(...rigaNodo(n, prof));
    ['L2', 'L3'].forEach(lv => {
      const ff = (figli[n.id] || []).filter(x => x.livello === lv);
      if (!ff.length) return;
      const s = scelte[n.id + lv];
      if (s) righe.push(h('tr', { class: 'nota-livello' }, h('td', {}), h('td', { colspan: 9, class: 'sx muto', style: `padding-left:${8 + (prof + 1) * 22}px` },
        `${lv === 'L2' ? 'Ingressi' : 'Uscite'} provati: ${ff.length}. La scelta fra loro, rifatta su 45 divisioni degli anni, guadagna fuori campione ${nf(s.mediana * a.euro_per_escursione_oggi, 1)} € a trade (mediana)`)));
      ff.forEach(x => visita(x, prof + 1));
    });
  };
  a.nodi.filter(n => n.livello === 'L0' && (n.livello1 || !n.ampiezza)).forEach(r => visita(r, 0));
  if (!righe.length) return h('p', { class: 'muto' }, 'Nessuna radice approfondita.');
  return h('div', {}, h('div', { class: 'tabella-cont' }, h('table', { class: 'albero' }, h('thead', {}, h('tr', {}, [['', ''], ['Regola', '', 'sx'], ['€ a trade', 'Guadagno medio netto con la volatilità di oggi; G = quante volte copre la soglia per la sua durata'], ['Trade l\'anno', ''],
    ['t', 'Guadagno medio diviso il suo errore'], ['R²', 'Regolarità della curva'], ['Drawdown', 'In euro di oggi'], ['Segnale isolato', 'Guadagno a trade meno la stessa finestra in tutti i giorni'], ['Esito', ''], ['Prima porta non superata', '', 'sx']].map(([t, ti, cl]) => h('th', { title: ti || null, class: cl || null }, t)))),
    h('tbody', {}, righe))), h('p', { class: 'muto' }, 'Clic su una riga per vedere tutte le porte.'));
}
async function paginaRicerca(nome) {
  const mio = giro;
  const a = await api('/ricerche/' + nome);
  if (a.in_corso) {
    const pc_ = a.budget ? Math.min(100, 100 * (a.prove || 0) / a.budget) : 0;
    vedi(mio, h('p', {}, h('a', { href: '#/ricerche' }, '← Ricerche')), h('h1', {}, nome),
      h('div', { class: 'pannello' }, h('p', {}, h('strong', {}, a.stato === 'fallita' ? 'Ricerca fallita: ' + (a.errore || '') : `In corso dal ${dataIt(a.inizio)}: ${a.prove || 0} prove su un massimo di ${a.budget}`)),
        h('div', { class: 'barra' }, h('div', { style: `width:${pc_}%` })), h('p', { class: 'muto' }, a.fase || '')),
      h('h2', {}, 'Diario'), diarioLista(a.diario));
    if (a.stato === 'in corso') setTimeout(() => { if (mio === giro) render(); }, 3000);
    return;
  }
  const ih = a.intestazione, cand = a.foglie.filter(f => f.esito === 'candidato'), altre = a.foglie.filter(f => f.esito !== 'candidato');
  const risultato = cand.length ? h('p', { class: 'grande-esito pos' }, `${cand.length} ${cand.length === 1 ? 'sistema da provare' : 'sistemi da provare'} su ProRealTime.`)
    : h('p', { class: 'grande-esito' }, 'Nessun sistema da provare su ProRealTime.');
  vedi(mio, h('p', {}, h('a', { href: '#/ricerche' }, '← Ricerche')), h('h1', {}, nome),
    h('p', { class: 'muto' }, `${ih.prodotto} ${ih.barre} min · lanciata il ${dataIt(a.quando)} · ${nf(a.prove, 0)} prove in ${nf(a.durata_s, 0)} secondi · in-sample ${a.anni[0]}-${a.anni[1]} · euro di oggi: 1 escursione = ${nf(a.euro_per_escursione_oggi, 0)} €`),
    h('div', { class: 'pannello' }, risultato, h('div', { class: 'imbuto-riga' }, a.imbuto ? imbutoSVG(a.imbuto) : null, perche(a)),
      h('p', { class: 'muto' }, 'La lunghezza delle barre è in scala logaritmica. ', h('a', { href: '#/come-funziona' }, 'Cosa fa ogni strato'))),
    a.walkforward_ricerca ? wfGrafico(a) : null,
    a.rumore ? rumoreGrafico(a.rumore) : null,
    cand.length ? h('div', {}, h('h2', {}, 'Da provare su ProRealTime'), listaFoglie(a, cand)) : null,
    altre.length ? h('div', {}, h('h2', {}, cand.length ? 'Gli altri sistemi finali, scartati' : 'I sistemi finali, scartati dalla verifica'), listaFoglie(a, altre)) : null,
    !a.foglie.length ? h('div', {}, h('h2', {}, 'Le regole arrivate più vicine'), h('p', { class: 'muto' }, 'Le dieci con il margine più alto. Nessuna arriva in fondo; servono a capire quanto manca.'), vicini(a)) : null,
    h('h2', {}, 'Dettagli'),
    sezione('Diario della ricerca', () => diarioLista(a.diario)),
    a.cicli ? sezione('Cosa è passato da ogni filtro', () => h('div', {}, a.cicli.map(c => h('div', {}, h('h3', {}, `${STRATI_NOME[c.strato] || c.nome}: ${c.semi} scelte su ${nf(c.n, 0)} che passano`),
      c.motivi && Object.keys(c.motivi).length ? h('p', { class: 'muto' }, 'Scartate: ' + Object.entries(c.motivi).map(([m, n]) => `${nf(n, 0)} ${m}`).join(' · ')) : null,
      tabellaRegole(c.migliori))))) : null,
    sezione('Radici approfondite e loro rami', () => ramiTabella(a)),
    a.walkforward_ricerca ? sezione('Walk-forward dell\'intera ricerca', () => h('table', {}, h('thead', {}, h('tr', {}, ['Anno', 'Cosa avrebbe scelto la ricerca con gli anni prima', 'Trade', 'Esc. a trade'].map(t => h('th', {}, t)))),
      h('tbody', {}, a.walkforward_ricerca.anni.map(r => h('tr', {}, h('td', {}, r.anno), h('td', { class: 'sx' }, r.etichetta), h('td', {}, r.n), h('td', { class: segno(r.media_esc) }, nf(r.media_esc, 3))))))) : null,
    sezione('Ipotesi e ingressi dichiarati prima', () => h('div', {}, h('p', {}, h('strong', {}, 'Ipotesi: '), ih.ipotesi), h('p', {}, h('strong', {}, 'Meccanismo: '), ih.meccanismo),
      h('ul', {}, (ih.ingressi || []).map(ip => h('li', {}, h('strong', {}, ip.nome), ` (${ip.grandezza} ${ip.op} ${ip.soglie.join(' / ')}): ${ip.meccanismo}`))))),
    a.cicli ? null : sezione('Tutte le regole semplici provate', () => tutteRegole(a), `${a.nodi.filter(n => n.livello === 'L0').length}`));
}
/* Lista compatta dei sistemi finali: una riga per sistema con la curva quadrata piccola e le metriche principali;
   clic sulla riga per aprire la scheda completa sotto. */
function miniDaCurva(c) {
  if (!c || !c.cum) return null;
  const n = c.cum.length, idx = [...new Set(Array.from({ length: 70 }, (_, i) => Math.round(i * (n - 1) / 69)))];
  const pos = idx.map(i => i);
  const seg = (c.segmenti || []).map(([p, i0, i1]) => [p, pos.findIndex(i => i >= i0), Math.max(0, pos.findIndex(i => i >= i1))]);
  return { y: idx.map(i => c.cum[i]), segmenti: seg.map(([p, a, b]) => [p, a < 0 ? 0 : a, b < 0 ? idx.length - 1 : b]) };
}
const BREVI = [[/^Batte la ricerca sul rumore/, 'rumore'], [/^DSR/, 'conto delle prove'], [/^Walk-forward/, 'anno per anno'], [/^Gemello/, 'Euro Stoxx'], [/^Guadagno medio/, '€ a trade'], [/^Trade l/, 'pochi trade'],
  [/^Regolarità/, 'curva'], [/^Anni positivi/, 'anni positivi'], [/^Costi doppi/, 'costi doppi'], [/^Segnale|^D1|^D2/, 'segnale isolato'], [/^t del/, 'caso'], [/^Utile fuori|^Guadagno medio fuori|^Fuori campione/, '2024-2025']];
const breve = n => { const x = BREVI.find(([re]) => re.test(n)); return x ? x[1] : n; };
function listaFoglie(a, foglie) {
  const col = [['', ''], ['Sistema', 'sx'], ['€ a trade', '', 'Guadagno medio netto con la volatilità del 2023, 1 CFD IG; in verde se supera la soglia per la sua durata'],
    ['Trade l’anno'], ['Ore', '', 'Ore medie in posizione'], ['R²', '', 'Regolarità della curva'], ['Drawdown', '', 'In euro di oggi'], ['Utile/DD'],
    ['t', '', 'Quanto il guadagno medio è lontano dal caso'], ['Rumore', '', 'Quota di ricerche sul rumore che producono un finale migliore di questo: serve al massimo 5%'], ['Anno per anno', '', 'Ricerca rifatta con i soli anni precedenti: quanto vale fuori campione rispetto all\'in-sample (serve almeno 0,5)'], ['Esito', 'sx']];
  const righe = [];
  foglie.forEach(f => {
    const m = f.misure_minuto || {}, ko = [...(f.porte || []), ...(f.voci_prova_finale || [])].filter(p => p.esito === 'rosso' || p.esito === 'grigio').map(p => breve(p.nome));
    const det = h('tr', { class: 'dettaglio', style: 'display:none' }, h('td', { colspan: col.length }));
    let aperta = false;
    const riga = h('tr', { class: 'clic', onclick: () => { aperta = !aperta; det.style.display = aperta ? '' : 'none'; if (aperta && !det.firstChild.firstChild) det.firstChild.append(schedaFoglia(a, f)); } },
      h('td', { class: 'mini-td' }, miniGrafico(miniDaCurva(f.curva), 64)),
      h('td', { class: 'sx desc' }, f.etichetta),
      h('td', { class: (m.G || 0) >= 1 ? 'pos' : 'neg' }, nE(m.euro_oggi)),
      h('td', { class: (m.trade_anno || 0) >= 8 ? '' : 'neg' }, nf(m.trade_anno, 0)), h('td', {}, nf(m.ore_medie, 1)),
      h('td', { class: (m.r2 || 0) >= 0.85 ? '' : 'neg' }, nf(m.r2, 2)), h('td', {}, nE(m.dd_euro_oggi, 0)), h('td', {}, nf(m.utile_su_dd, 1)), h('td', {}, nf(m.t, 1)),
      (() => { const pr = (f.porte || []).find(p => p.nome.startsWith('Batte la ricerca sul rumore')); return h('td', { class: pr ? (pr.esito === 'verde' ? 'pos' : 'neg') : '' }, pr && pr.valore != null ? pc(pr.valore) : '–'); })(),
      h('td', { class: (f.efficienza_wf ?? -1) >= 0.5 ? 'pos' : 'neg' }, nf(f.efficienza_wf, 2)),
      h('td', { class: 'sx esito-td', title: f.motivo || '' }, badge(f.esito), ' ', h('span', { class: 'muto' }, f.esito === 'candidato' ? '' : ko.join(', '))));
    righe.push(riga, det);
  });
  return h('div', {}, h('div', { class: 'tabella-cont' }, h('table', { class: 'compatta' }, h('thead', {}, h('tr', {}, col.map(([t, c, ti]) => h('th', { class: c || null, title: ti || null }, t)))),
    h('tbody', {}, righe))), h('p', { class: 'muto' }, 'Clic su un sistema per la scheda completa: curva grande, sette numeri, porte e codice ProRealCode.'));
}
/* La ricerca rifatta anno per anno: una barra per anno con il guadagno medio a trade dei finali scelti con gli anni prima. */
function wfGrafico(a) {
  const wf = a.walkforward_ricerca, e = a.euro_per_escursione_oggi || 0;
  const anni = wf.anni.filter(r => r.media_esc != null);
  if (!anni.length) return null;
  const W = 560, H = 170, m = { l: 46, r: 10, t: 14, b: 34 }, v = anni.map(r => r.media_esc * e);
  const lo = Math.min(0, ...v), hi = Math.max(0, ...v), Y = x => m.t + (H - m.t - m.b) * (1 - (x - lo) / ((hi - lo) || 1)), bw = (W - m.l - m.r) / anni.length;
  const svg = sv('svg', { viewBox: `0 0 ${W} ${H}`, class: 'wf-svg', role: 'img', 'aria-label': 'Guadagno medio a trade fuori campione, anno per anno' });
  svg.append(sv('line', { x1: m.l, x2: W - m.r, y1: Y(0), y2: Y(0), style: 'stroke:var(--bordo)' }), sv('text', { x: m.l - 6, y: Y(0) + 4, 'text-anchor': 'end', style: 'font-size:11px;fill:var(--muto)' }, '0 €'));
  anni.forEach((r, i) => {
    const x = m.l + i * bw + bw * 0.18, y = Y(Math.max(0, v[i])), hh = Math.abs(Y(v[i]) - Y(0));
    svg.append(sv('rect', { x, y, width: bw * 0.64, height: Math.max(1, hh), rx: 2, style: `fill:${v[i] >= 0 ? 'var(--verde)' : 'var(--rosso)'}` }, sv('title', {}, `${r.anno}: ${nf(v[i], 1)} € a trade su ${r.n} trade · ${r.etichetta}`)),
      sv('text', { x: x + bw * 0.32, y: H - m.b + 14, 'text-anchor': 'middle', style: 'font-size:11px;fill:var(--testo)' }, String(r.anno)),
      sv('text', { x: x + bw * 0.32, y: H - m.b + 27, 'text-anchor': 'middle', style: 'font-size:10px;fill:var(--muto)' }, `${nf(v[i], 0)} €`));
  });
  const tot = wf.media_esc == null ? null : wf.media_esc * e;
  const ins = a.foglie && a.foglie.length ? a.foglie.reduce((x, f) => x + ((f.misure_minuto || {}).euro_oggi || 0), 0) / a.foglie.length : null;
  return h('div', { class: 'pannello wf-box' }, h('div', {}, h('div', { class: 'et' }, 'La stessa ricerca rifatta anno per anno, con i soli anni prima'),
    h('p', { class: 'muto' }, `Ogni anno dal 2017 la ricerca intera si rifà con gli anni precedenti e i finali che sceglie si guardano nell'anno dopo, che non hanno visto. In tutto ${wf.n} trade, ${tot == null ? '–' : nf(tot, 1) + ' €'} a trade` +
      (ins != null ? `, contro ${nf(ins, 0)} € a trade in media dei finali in-sample.` : '.'))), svg);
}
/* Prova sul rumore: per ogni ricerca sul rumore il punteggio del finale migliore (pallini grigi), e i finali veri (barre). */
function rumoreGrafico(r) {
  const giri = r.giri || [], veri = r.finali_veri || [];
  if (!giri.length) return null;
  const W = 560, H = 120, m = { l: 12, r: 12, t: 16, b: 30 };
  const tutti = [...giri.map(g => g.migliore), ...veri.map(v => v.punteggio)], hi = Math.max(...tutti, 0.01);
  const X = v => m.l + (W - m.l - m.r) * v / hi;
  const svg = sv('svg', { viewBox: `0 0 ${W} ${H}`, class: 'wf-svg', role: 'img', 'aria-label': 'Punteggi dei finali: veri e sul rumore' });
  svg.append(sv('line', { x1: m.l, x2: W - m.r, y1: H - m.b, y2: H - m.b, style: 'stroke:var(--bordo)' }));
  giri.forEach((g, i) => svg.append(sv('circle', { cx: X(g.migliore), cy: H - m.b - 8 - (i % 5) * 7, r: 3.2, style: 'fill:var(--muto);opacity:.75' }, sv('title', {}, `rumore: finale migliore ${nf(g.migliore, 2)}, ${g.finali} finali`))));
  veri.forEach(v => svg.append(sv('line', { x1: X(v.punteggio), x2: X(v.punteggio), y1: m.t, y2: H - m.b, style: `stroke:${v.p <= 0.05 ? 'var(--verde)' : 'var(--f-wf)'};stroke-width:2` }, sv('title', {}, `${v.etichetta}: punteggio ${nf(v.punteggio, 2)}, il rumore fa meglio nel ${pc(v.p)} dei casi`))));
  svg.append(sv('text', { x: m.l, y: H - 10, style: 'font-size:11px;fill:var(--muto)' }, '0'), sv('text', { x: W - m.r, y: H - 10, 'text-anchor': 'end', style: 'font-size:11px;fill:var(--muto)' }, `punteggio ${nf(hi, 2)}`));
  const battono = veri.filter(v => v.p <= 0.05).length, conFinali = giri.filter(g => g.finali > 0).length;
  return h('div', { class: 'pannello wf-box' }, h('div', {}, h('div', { class: 'et' }, `Prova sul rumore: la stessa ricerca ${giri.length} volte con le condizioni slegate dai risultati`),
    h('p', { class: 'muto' }, `Pallini grigi: il finale migliore di ogni ricerca sul rumore (${conFinali} su ${giri.length} trovano dei finali). Linee: i finali veri, in verde quelli che il rumore batte al massimo nel 5% dei casi: ${battono} su ${veri.length}. Il punteggio è guadagno rispetto alla soglia × regolarità × distanza dal caso.`)), svg);
}
/* Campagna: avanzamento, tutte le ricerche, tutti i finali in una tabella. */
const NOMI_PRODOTTI = { EC: 'EUR/USD', AD: 'AUD/USD', BP: 'GBP/USD', JY: 'USD/JPY rovesciato', CD: 'USD/CAD rovesciato', SF: 'USD/CHF rovesciato', NE1: 'NZD/USD', FDAX: 'DAX', FESX: 'Euro Stoxx' };
const nomeProd = p => NOMI_PRODOTTI[p] ? `${NOMI_PRODOTTI[p]}` : p;
async function paginaCampagna(nome) {
  const mio = giro;
  const c = await api('/campagne/' + nome), ih = c.intestazione, r = c.ricerche;
  const finite = r.filter(x => x.stato === 'finita').length;
  const ric = h('div', { class: 'tabella-cont' }, h('table', { class: 'compatta' }, h('thead', {}, h('tr', {}, [['Ricerca', 'sx'], ['Stato'], ['Forza bruta'], ['Finali'], ['Anno per anno', '', 'Guadagno a trade dei finali scelti ogni anno con i soli anni prima'], ['Rumore', '', 'Punteggio del finale migliore sul rumore e di quello vero'], ['Da provare']].map(([t, cl, ti]) => h('th', { class: cl || null, title: ti || null }, t)))),
    h('tbody', {}, r.map(x => h('tr', { class: x.stato === 'finita' ? 'clic' : '', onclick: () => { if (x.stato === 'finita') location.hash = '#/ricerche/' + x.nome; } },
      h('td', { class: 'sx' }, `${nomeProd(x.prodotto)} · ${x.lato > 0 ? 'long' : 'short'} · ${x.barre} min`), h('td', {}, x.stato === 'finita' ? 'finita' : x.stato === 'in corso' ? h('span', { title: x.fase || '' }, 'in corso') : x.stato === 'fallita' ? h('span', { class: 'neg', title: x.errore || '' }, 'fallita') : h('span', { class: 'muto' }, 'da fare')),
      h('td', {}, x.forza_bruta == null ? '–' : nf(x.forza_bruta, 0)), h('td', {}, x.finali ?? '–'), h('td', { class: segno(x.wf_euro) }, x.wf_euro == null ? '–' : nE(x.wf_euro)),
      h('td', {}, x.rumore_migliore == null ? '–' : `${nf(x.vero_migliore, 2)} contro ${nf(x.rumore_migliore, 2)}`), h('td', { class: x.candidati ? 'pos' : '' }, x.candidati ?? '–'))))));
  let finali = null;
  if (c.righe) {
    const l = c.righe.filter(x => x.sistema).sort((a, b) => (b.esito === 'candidato') - (a.esito === 'candidato') || (a.p_rumore ?? 1) - (b.p_rumore ?? 1) || (b.euro_oggi || 0) - (a.euro_oggi || 0));
    finali = h('div', { class: 'tabella-cont' }, h('table', { class: 'compatta' }, h('thead', {}, h('tr', {}, [['', ''], ['Sistema', 'sx'], ['Prodotto'], ['€ a trade'], ['Trade l’anno'], ['R²'], ['t'], ['Rumore', '', 'Quota di ricerche sul rumore con un finale migliore'], ['Altre valute', '', 'Su quante delle altre valute della campagna la stessa regola guadagna, negli stessi anni'], ['Anno per anno'], ['Esito', 'sx']].map(([t, cl, ti]) => h('th', { class: cl || null, title: ti || null }, t)))),
      h('tbody', {}, l.map(x => h('tr', { class: 'clic', onclick: () => { location.hash = '#/ricerche/' + x.ricerca; } }, h('td', { class: 'mini-td' }, miniGrafico({ y: x.mini }, 48)),
        h('td', { class: 'sx desc' }, x.sistema), h('td', {}, `${nomeProd(x.prodotto)} ${x.barre}m`), h('td', {}, nE(x.euro_oggi)), h('td', { class: (x.trade_anno || 0) >= 8 ? '' : 'neg' }, nf(x.trade_anno, 0)), h('td', {}, nf(x.r2, 2)), h('td', {}, nf(x.t, 1)),
        h('td', { class: x.p_rumore == null ? '' : x.p_rumore <= 0.05 ? 'pos' : 'neg' }, x.p_rumore == null ? '–' : pc(x.p_rumore)), h('td', { class: x.conferme >= Math.ceil(x.su / 2) ? 'pos' : '' }, `${x.conferme} su ${x.su}`),
        h('td', { class: (x.efficienza_wf ?? -1) >= 0.5 ? 'pos' : 'neg' }, nf(x.efficienza_wf, 2)), h('td', { class: 'sx esito-td' }, badge(x.esito)))))));
  }
  vedi(mio, h('p', {}, h('a', { href: '#/ricerche' }, '← Ricerche')), h('h1', {}, nome),
    h('p', { class: 'muto' }, `${ih.prodotti.map(nomeProd).join(', ')} · ${ih.lati.map(l => l > 0 ? 'long' : 'short').join(' e ')} · barre da ${ih.barre.join(' e ')} minuti · prova sul rumore ${(ih.rumore || {}).ripetizioni || 0} volte · ${finite} di ${r.length} ricerche finite`),
    h('div', { class: 'barra' }, h('div', { style: `width:${100 * finite / r.length}%` })),
    ih.prodotti.some(p => /rovesciato/.test(NOMI_PRODOTTI[p] || '')) ? h('p', { class: 'muto' }, 'USD/JPY e USD/CAD nei dati sono quotati al contrario di IG (yen per dollaro, dollari per dollaro canadese): un long su questi dati è uno short su IG con le condizioni speculari; il codice ProRealCode lo scrive già così.') : null,
    finali ? h('div', {}, h('h2', {}, 'Tutti i finali della campagna'), finali) : h('p', { class: 'muto' }, 'La tabella con tutti i finali compare a campagna finita.'),
    h('h2', {}, 'Le ricerche'), ric);
  if (finite < r.length) setTimeout(() => { if (mio === giro) render(); }, 15000);
}
function tabellaRegole(l) {
  return h('div', { class: 'tabella-cont' }, h('table', {}, h('thead', {}, h('tr', {}, [['', ''], ['Regola', 'sx'], ['€ a trade', '', 'Con la volatilità di oggi, 1 CFD IG, netto'], ['Trade l’anno'], ['Ore'], ['t'], ['R²'], ['Batte il caso', '', 'Quota di filtri a caso che toglierebbero la stessa quota di trade al genitore e farebbero peggio']].map(([t, c, ti]) => h('th', { class: c || null, title: ti || null }, t)))),
    h('tbody', {}, l.map(r => h('tr', {}, h('td', {}, miniGrafico({ y: r.mini })), h('td', { class: 'sx desc' }, r.etichetta), h('td', { class: (r.G || 0) >= 1 ? 'pos' : '' }, nE(r.euro_oggi)),
      h('td', {}, nf(r.trade_anno, 0)), h('td', {}, nf(r.ore, 1)), h('td', {}, nf(r.t, 1)), h('td', {}, nf(r.r2, 2)), h('td', {}, r.quantile == null ? '–' : pc(r.quantile)))))));
}
function tutteRegole(a) {
  let n_ = 60;
  const box = h('div', {});
  const disegna = () => {
    const l0 = a.nodi.filter(n => n.livello === 'L0').sort((x, y) => (y.misure.M || 0) - (x.misure.M || 0));
    box.replaceChildren(h('div', { class: 'tabella-cont' }, h('table', {}, h('thead', {}, h('tr', {}, ['', 'Regola', '€ a trade', 'Trade l\'anno', 'Margine', 't', 'Esito'].map((t, i) => h('th', { class: i === 1 || i === 6 ? 'sx' : null }, t)))),
      h('tbody', {}, l0.slice(0, n_).map(n => h('tr', {}, h('td', {}, miniGrafico({ y: n.mini })), h('td', { class: 'sx' }, n.etichetta), h('td', {}, nE(n.misure.euro_oggi)), h('td', {}, nf(n.misure.trade_anno, 0)),
        h('td', {}, nf(n.misure.M, 2)), h('td', {}, nf(n.misure.t, 1)), h('td', { class: 'sx muto' }, n.motivo ? motivoChiaro(n.motivo) : n.scelta || '')))))),
      n_ < l0.length ? h('button', { type: 'button', onclick: () => { n_ = l0.length; disegna(); } }, `Mostra tutte (${l0.length})`) : null);
  };
  disegna();
  return box;
}
function porteTabella(porte) {
  return h('table', { class: 'porte' }, h('tbody', {}, porte.map(p => h('tr', {}, h('td', {}, h('span', { class: 'pallino ' + p.esito })), h('td', { class: 'sx' }, p.nome),
    h('td', {}, typeof p.valore === 'number' ? nf(p.valore, Math.abs(p.valore) >= 10 ? 1 : 3) : (p.valore ?? '–')), h('td', { class: 'sx muto' }, p.soglia)))));
}
function rigaNodo(n, prof) {
  const m = n.misure || {}, d = n.differenziale || {}, aperta = h('tr', { class: 'dettaglio', style: 'display:none' }, h('td', { colspan: 10 },
    h('div', { class: 'dett-nodo' }, porteTabella(n.porte || []),
      h('div', { class: 'muto' }, [`Condizioni: ${(n.regola.cond || []).map(c => `${c[0]} ${c[1]} ${c[2]}`).join(' e ') || 'nessuna'}`,
        ` · uscita ${Object.entries(n.regola.uscita || {}).filter(([, v]) => v != null).map(([k, v]) => `${k} ${v}`).join(', ')}${n.regola.stop ? ` · stop ${n.regola.stop} escursioni` : ''}`,
        h('br'), `Segnale meno la deriva (D1) ${nf(d.D1, 3)} esc. (t ${nf(d.t_D1, 1)}) · meno la stessa finestra (D2) ${nf(d.D2, 3)} esc. (t ${nf(d.t_D2, 1)}) · `,
        `migliore del ${d.D3_quantile == null ? '–' : pc(d.D3_quantile)} dei sottoinsiemi casuali della finestra · quanto segue il DAX giorno per giorno ${nf(d.beta, 2)}`,
        n.filtri_casuali ? [h('br'), `Tiene il ${pc(n.filtri_casuali.quota_tenuta)} dei trade del genitore; batte il ${pc(n.filtri_casuali.quantile)} dei filtri casuali; i trade tolti fanno ${nf(n.filtri_casuali.resto_media, 3)} esc. a trade`] : null,
        h('br'), `Fuori campione CPCV del nodo: mediana ${nf(n.cpcv && n.cpcv.mediana, 3)} esc. a trade, 10° percentile ${nf(n.cpcv && n.cpcv.p10, 3)}`]))));
  const riga = h('tr', { class: 'clic ' + (n.esito === 'scartato' ? 'spento' : ''), onclick: () => { aperta.style.display = aperta.style.display ? '' : 'none'; } },
    h('td', {}, miniGrafico({ y: n.mini })),
    h('td', { class: 'sx', style: `padding-left:${8 + prof * 22}px` }, prof ? '↳ ' : '', h('strong', {}, n.etichetta), h('div', { class: 'muto' }, LIVELLI[n.livello] || n.livello)),
    h('td', { class: (m.G || 0) >= 1 ? 'pos' : '' }, nE(m.euro_oggi), h('div', { class: 'muto' }, `G ${nf(m.G, 2)}`)),
    h('td', {}, nf(m.trade_anno, 0)), h('td', {}, nf(m.t, 1)), h('td', {}, nf(m.r2, 2)), h('td', {}, nE(m.dd_euro_oggi, 0)),
    h('td', { class: segno(d.D2) }, d.D2_euro == null ? '–' : nE(d.D2_euro), h('div', { class: 'muto' }, d.quota_D2 == null ? '' : `${pc(d.quota_D2)} del lordo`)),
    h('td', {}, badge(n.esito === 'scartato' ? 'scartato' : 'candidato', n.esito === 'pronto' ? 'pronto' : n.esito === 'scartato' ? 'scartato' : 'passa')),
    h('td', { class: 'sx muto' }, n.motivo || ''));
  return [riga, aperta];
}
function settimoNumero(f) {
  const d = f.differenziale || {}, ok = (f.porte || []).filter(p => p.nome.includes('D2') || p.nome.includes('D1'));
  const es = ok.length ? (ok.every(p => p.esito === 'verde') ? 'verde' : 'rosso') : null;
  return grande('Segnale isolato', d.D2_euro == null ? '–' : nE(d.D2_euro), `soglia: almeno metà del lordo, t >= 2`, es,
    d.quota_D2 == null ? '' : `${pc(d.quota_D2)} del lordo · t ${nf(d.t_D2, 1)}`, 'Guadagno a trade meno quello della stessa finestra in tutti i giorni (euro di oggi)');
}
function schedaFoglia(a, f) {
  const m = f.misure_minuto || {}, c = f.curva, pf = f.prova_finale;
  const dd = []; let pk = -Infinity; c.cum.forEach(v => { pk = Math.max(pk, v, 0); dd.push(v - pk); });
  const cv = { ...c, dd }, fmt = v => nf(v, 0) + ' €';
  const porta = nome => (f.porte || []).find(p => p.nome.startsWith(nome));
  const es = p => p ? p.esito : null;
  const sinistra = h('div', { class: 'col-curva' }, h('div', { class: 'titolo-fig' }, 'Profitto netto cumulato, 1 CFD IG, in euro di oggi'), curvaQuadrata(cv, fmt), legendaFasce(cv),
    h('div', { class: 'legenda' }, h('span', {}, h('i', { style: 'background:var(--muto)' }), 'tratteggio: stessa finestra in tutti i giorni (riferimento)'),
      c.anni_wf && c.anni_wf.length ? h('span', {}, h('i', { style: 'background:var(--f-wf)' }), `barra in alto: anni del walk-forward ${c.anni_wf[0]}-${c.anni_wf[c.anni_wf.length - 1]}`) : null));
  const destra = h('div', { class: 'col-num' }, h('div', { class: 'sei' },
    grande('Guadagno medio a trade', nE(m.euro_oggi), `soglia ${m.richiesto} € (trade di ${nf(m.ore_medie, 1)} ore)`, es(porta('Guadagno medio')), `storico ${nE(m.euro_storico)} · 1 CFD IG, netto`, 'Guadagno medio con la volatilità del 2023'),
    grande('Drawdown massimo', nE(m.dd_euro_oggi, 0), 'nessuna soglia', null, `utile / drawdown ${nf(m.utile_su_dd, 1)}`, 'In euro di oggi'),
    grande('Lordo / costi', m.costo_euro_oggi ? nf((m.euro_oggi + m.costo_euro_oggi) / m.costo_euro_oggi, 1) : '–', 'riferimento 3', null, `costi ${nE(m.costo_euro_oggi)} a trade`, 'Quante volte il lordo copre spread e notte'),
    grande('Tempo in mercato', nf(m.ore_medie, 1) + ' ore', 'nessuna soglia', null, 'ore medie per trade', 'Ogni posizione aperta blocca margine'),
    grande('Regolarità (R²)', nf(m.r2), 'soglia 0,85', es(porta('Regolarità')), `anni positivi ${pc(m.anni_positivi)}`, 'Quanto la curva somiglia a una retta'),
    grande('Trade l\'anno', nf(m.trade_anno, 0), `soglia 8 e t >= 2 (t ${nf(m.t, 1)})`, es(porta('Trade l')), `${m.n} trade in ${a.anni[1] - a.anni[0] + 1} anni`, 'Numero medio di trade in un anno'),
    settimoNumero(f)),
    h('div', { class: 'fuori' }, h('strong', {}, 'Fuori campione 2024-2025: '), pf && pf.avanti ? [`${pf.avanti.n} trade · utile `, h('span', { class: segno(pf.avanti.utile) }, eur(pf.avanti.utile)),
      ` · ${nf(pf.avanti.guadagno_medio, 1)} € a trade`] : 'non eseguito: la foglia non ha passato le porte della scoperta.'),
    h('div', { class: 'fuori' }, h('strong', {}, 'Walk-forward della procedura: '), `${f.walkforward.n} trade, ${nf(f.walkforward.media_esc, 3)} esc. a trade, efficienza ${nf(f.efficienza_wf, 2)} (soglia 0,5)`));
  return h('div', { class: 'foglia' }, h('h3', {}, f.etichetta, ' ', badge(f.esito), h('span', { class: 'muto' }, ' ' + f.motivo)),
    h('div', { class: 'prima-vista' }, sinistra, destra),
    sezione('Codice ProRealCode', () => codiceFoglia(f)),
    sezione('Tutte le porte della verifica', () => h('div', {}, porteTabella(f.porte), f.voci_prova_finale ? porteTabella(f.voci_prova_finale) : null)),
    sezione('Anni del walk-forward', () => h('table', {}, h('thead', {}, h('tr', {}, ['Anno', 'Scelta della procedura con gli anni precedenti', 'Trade', 'Esc. a trade'].map(t => h('th', {}, t)))),
      h('tbody', {}, f.walkforward.anni.map(r => h('tr', {}, h('td', {}, r.anno), h('td', { class: 'sx' }, r.etichetta), h('td', {}, r.n), h('td', { class: segno(r.media_esc) }, nf(r.media_esc, 3))))))));
}
// ------------------------------------------------------------------ come funziona
/* Disegni piccoli, uno per strato. Colori dai token del tema. */
const D = { W: 360, H: 170 };
const tela = () => sv('svg', { viewBox: `0 0 ${D.W} ${D.H}`, class: 'disegno', role: 'img' });
const tx = (x, y, t, st = '') => sv('text', { x, y, style: 'font-size:11px;fill:var(--muto);' + st }, t);
const curvaPunti = (f, x0, x1, y0, n = 60) => Array.from({ length: n }, (_, i) => { const u = i / (n - 1); return `${x0 + (x1 - x0) * u},${y0 - f(u)}`; }).join(' ');
const rumore = (seme) => { let s = seme; return () => { s = (s * 9301 + 49297) % 233280; return s / 233280 - 0.5; }; };
function disegnoAmpiezza() {
  const g = tela(), R = rumore(3);
  for (let i = 0; i < 15; i++) for (let j = 0; j < 9; j++) {
    const v = R(), forte = v > 0.47, medio = v > 0.38;
    g.append(sv('rect', { x: 40 + i * 19, y: 14 + j * 14, width: 15, height: 11, rx: 2, style: `fill:${forte ? 'var(--f-in)' : 'var(--bordo)'};opacity:${forte ? 1 : medio ? .7 : .35}` }));
  }
  g.append(tx(40, 158, "ora d'ingresso: 166 →"), tx(4, 14, 'pattern'), tx(4, 26, '50 ↓'), tx(222, 158, '× 8 uscite = 66.400'));
  return g;
}
function disegnoL0() {
  const g = tela(), X0 = 130, K = 4;          // 4 pixel per euro
  const bar = (y, eu, col, et, val) => g.append(sv('rect', { x: X0, y, width: eu * K, height: 20, rx: 3, style: `fill:${col}` }), tx(4, y + 14, et, 'fill:var(--testo)'), tx(X0 + eu * K + 6, y + 14, val, 'fill:var(--testo)'));
  g.append(sv('line', { x1: X0 + 20 * K, x2: X0 + 20 * K, y1: 14, y2: 100, style: 'stroke:var(--rosso);stroke-dasharray:4 3' }), tx(X0 + 20 * K - 26, 12, 'soglia 20 €', 'fill:var(--rosso)'));
  bar(24, 3.8, 'var(--f-in)', 'guadagno a trade', '3,8 €');
  bar(64, 41, 'var(--f-vic)', 'margine', '41 €');
  g.append(tx(4, 128, "Esempio: 130 trade l'anno a 3,8 € = 494 € l'anno."), tx(4, 144, 'Se un filtro tenesse solo i 12 migliori: 494 / 12 = 41 € a trade,'), tx(4, 160, "sopra 1,5 volte la soglia: c'è margine, la regola passa."));
  return g;
}
function disegnoRadici() {
  const g = tela();
  g.append(sv('polyline', { points: curvaPunti(u => 100 * u + 8 * Math.sin(u * 20), 20, 340, 140), style: 'fill:none;stroke:var(--f-in);stroke-width:2' }));
  g.append(sv('polyline', { points: curvaPunti(u => 96 * u + 9 * Math.sin(u * 20 + .3), 20, 340, 140), style: 'fill:none;stroke:var(--muto);stroke-width:1.5;stroke-dasharray:4 3' }));
  g.append(sv('polyline', { points: curvaPunti(u => 70 * u + 14 * Math.sin(u * 7 + 2), 20, 340, 150), style: 'fill:none;stroke:var(--f-vic);stroke-width:2' }));
  g.append(tx(220, 24, 'tenuta'), tx(220, 38, 'simile alla prima: saltata', ''), tx(250, 98, 'diversa: tenuta'));
  return g;
}
function disegnoL1() {
  const g = tela();
  g.append(sv('polygon', { points: curvaPunti(u => 110 * u + 6 * Math.sin(u * 18), 20, 340, 145) + ' ' + curvaPunti(u => 45 * (1 - u), 340, 20, 145), style: 'fill:var(--f-vic);opacity:.18' }));
  g.append(sv('polyline', { points: curvaPunti(u => 110 * u + 6 * Math.sin(u * 18), 20, 340, 145), style: 'fill:none;stroke:var(--f-in);stroke-width:2' }));
  g.append(sv('polyline', { points: curvaPunti(u => 45 * u, 20, 340, 145), style: 'fill:none;stroke:var(--muto);stroke-width:1.5;stroke-dasharray:4 3' }));
  g.append(tx(230, 30, 'il sistema'), tx(230, 118, 'stessa ora, tutti i giorni'), tx(150, 80, 'segnale isolato', 'fill:var(--f-vic);font-weight:600'));
  return g;
}
function disegnoL2() {
  const g = tela();
  for (let i = 0; i < 30; i++) { const x = (i - 15) / 5, hh = 110 * Math.exp(-x * x / 2); g.append(sv('rect', { x: 20 + i * 9, y: 140 - hh, width: 8, height: hh, style: `fill:${i >= 25 ? 'var(--rosso)' : 'var(--bordo)'};opacity:${i >= 25 ? .5 : .8}` })); }
  g.append(sv('line', { x1: 320, x2: 320, y1: 20, y2: 140, style: 'stroke:var(--f-vic);stroke-width:3' }), tx(258, 16, 'il filtro provato', 'fill:var(--f-vic);font-weight:600'),
    tx(20, 158, '1.000 filtri a caso che tolgono gli stessi trade'), tx(245, 150, 'oltre il 95%', 'fill:var(--rosso)'));
  return g;
}
function disegnoL3() {
  const g = tela();
  g.append(sv('line', { x1: 20, x2: 340, y1: 70, y2: 70, style: 'stroke:var(--bordo)' }), tx(4, 66, 'ingresso'));
  g.append(sv('polyline', { points: curvaPunti(u => -20 * Math.sin(u * 5) + 60 * u * u, 20, 340, 70), style: 'fill:none;stroke:var(--f-in);stroke-width:2' }));
  g.append(sv('line', { x1: 20, x2: 340, y1: 110, y2: 110, style: 'stroke:var(--rosso);stroke-dasharray:4 3' }), tx(250, 126, 'stop sotto il fondo dei vincenti', 'fill:var(--rosso)'));
  [[120, '17:30'], [230, '21:55'], [330, 'domani']].forEach(([x, t]) => g.append(sv('line', { x1: x, x2: x, y1: 20, y2: 140, style: 'stroke:var(--f-vic);stroke-dasharray:2 3' }), tx(x - 14, 155, t)));
  return g;
}
function disegnoL4() {
  const g = tela();
  ['ricalcolo minuto per minuto', 'costi IG raddoppiati', 'stessa regola sull\'Euro Stoxx', 'conta tutte le prove fatte (DSR)', 'ricerca rifatta anno per anno', 'curva regolare, anni positivi'].forEach((t, i) => {
    const y = 20 + i * 24;
    g.append(sv('circle', { cx: 24, cy: y, r: 8, style: 'fill:var(--f-wf)' }), sv('text', { x: 20, y: y + 4, style: 'font-size:11px;fill:#000;font-weight:700' }, '✓'), tx(40, y + 4, t, 'fill:var(--testo);font-size:12px'));
  });
  return g;
}
function disegnoFinale() {
  const g = tela(), parti = [['2008-10', 14, 'var(--f-ind)', 'conta poco'], ['2011-13', 14, 'var(--f-vic)', 'non deve perdere'], ['2014-2023: ricerca', 46, 'var(--f-in)', ''], ['2024-25', 10, 'var(--f-out)', 'decide'], ['ProRealTime', 16, 'var(--muto)', 'tu']];
  let x = 10;
  parti.forEach(([t, w, c, sotto]) => { const ww = w * 3.4; g.append(sv('rect', { x, y: 50, width: ww - 3, height: 34, rx: 3, style: `fill:${c};opacity:.85` }), tx(x + 3, 44, t, 'fill:var(--testo)'), tx(x + 3, 102, sotto)); x += ww; });
  return g;
}
function disegnoMoltiplica(etichette) {
  const g = tela(), x0 = 40, y0 = 85;
  g.append(sv('circle', { cx: x0, cy: y0, r: 10, style: 'fill:var(--f-in)' }), tx(x0 - 14, y0 + 28, 'seme'));
  etichette.forEach((e, i) => {
    const y = 14 + i * (140 / (etichette.length - 1)), forte = e[1];
    g.append(sv('line', { x1: x0 + 10, y1: y0, x2: 200, y2: y, style: `stroke:${forte ? 'var(--f-wf)' : 'var(--bordo)'};stroke-width:${forte ? 2 : 1}` }),
      sv('circle', { cx: 204, cy: y, r: 5, style: `fill:${forte ? 'var(--f-wf)' : 'var(--bordo)'}` }), tx(214, y + 4, e[0], forte ? 'fill:var(--testo)' : ''));
  });
  return g;
}
function disegnoFiltro() {
  const g = tela();
  for (let i = 0; i < 40; i++) { const x = 20 + (i % 20) * 16, y = 30 + Math.floor(i / 20) * 26, ok = [3, 11, 17, 26, 34].includes(i); g.append(sv('circle', { cx: x, cy: y, r: 6, style: `fill:${ok ? 'var(--f-in)' : 'var(--bordo)'};opacity:${ok ? 1 : .6}` })); }
  g.append(sv('path', { d: 'M20 95 L340 95 L230 130 L130 130 Z', style: 'fill:var(--bordo);opacity:.5' }));
  [150, 180, 210].forEach(x => g.append(sv('circle', { cx: x, cy: 150, r: 6, style: 'fill:var(--f-in)' })));
  g.append(tx(250, 155, 'semi diversi fra loro'));
  return g;
}
const STRATI = [
  { id: 'forza', titolo: 'Forza bruta', sotto: 'ora × uscita × pattern', disegno: disegnoAmpiezza,
    cosa: 'Prova tutte le combinazioni: ogni ora d\'ingresso (ogni 5 minuti), ogni uscita, nessun pattern o un pattern di struttura del prezzo.',
    filtro: ['Nessun filtro: ogni regola è una prova e conta nel totale', 'Sul DAX a 5 minuti: 166 orari × 8 uscite × 50 = 66.400 regole in circa 15 secondi'],
    perche: 'Trovare gli orari e le situazioni in cui il DAX tende a salire, senza scegliere a occhio.' },
  { id: 'filtro1', titolo: 'Filtro 1', sotto: 'i semi', disegno: disegnoL0,
    cosa: 'Tiene le regole che guadagnano già abbastanza a trade o che possono arrivarci con un filtro, e fra queste sceglie i semi diversi fra loro.',
    filtro: ['Guadagno sopra la soglia (20/30/50 € per durata) o margine almeno 1', 'Guadagno lontano dal caso (t almeno 2), almeno 8 trade l\'anno', 'Positiva sugli anni lasciati fuori e in entrambe le metà del periodo', 'Una regola che guadagna negli stessi giorni di un seme già scelto (correlazione oltre 0,9) è un doppione'],
    perche: 'Un filtro toglie trade, non ne aggiunge: se il margine non c\'è, nessuna combinazione lo crea.' },
  { id: 'molt1', titolo: 'Moltiplicazione 1', sotto: '+ un pattern o un indicatore', disegno: () => disegnoMoltiplica([['+ ieri giornata interna', 0], ['+ sopra media 50 giorni', 1], ['+ RSI 14 sopra 70', 0], ['+ barra verde', 0], ['+ ADX sotto 20', 1], ['+ gap in giù', 0]]),
    cosa: 'Ogni seme si combina con ogni altro pattern di struttura e con indicatori e candele sulle barre: da un seme nascono decine di regole.',
    filtro: ['Nessun filtro: ogni combinazione è una prova'],
    perche: 'Due condizioni insieme possono isolare i giorni giusti meglio di una sola.' },
  { id: 'filtro2', titolo: 'Filtro 2', sotto: 'meglio del genitore e del caso', disegno: disegnoL2,
    cosa: 'Le combinazioni restano solo se il pattern aggiunto sa qualcosa: confrontate con il seme da cui vengono e con filtri a caso.',
    filtro: ['Le porte del filtro 1, con margine almeno 1,5', 'Batte il 95% dei filtri a caso che tolgono la stessa quota di trade', 'Migliora il seme in almeno 2 terzi del periodo su 3', 'I trade tolti vanno peggio di quelli tenuti'],
    perche: 'Scegliere i giorni migliori fra tanti riesce anche a caso: serve battere il caso.' },
  { id: 'molt2', titolo: 'Moltiplicazione 2', sotto: 'regime, calendario, uscite, orari', disegno: () => disegnoMoltiplica([['+ periodo agitato', 0], ['+ non venerdì', 1], ['+ fine mese', 0], ['altre 7 uscite', 0], ['15 e 30 minuti prima', 1], ['15 e 30 minuti dopo', 0]]),
    cosa: 'I semi rimasti si combinano con i filtri di regime e di calendario e si provano con le altre uscite e con l\'ingresso spostato.',
    filtro: ['Nessun filtro: ogni variante è una prova'],
    perche: 'Le uscite e i filtri di contorno si provano solo su regole che hanno già superato due filtri.' },
  { id: 'filtro3', titolo: 'Filtro 3', sotto: 'i finali, diversi', disegno: disegnoFiltro,
    cosa: 'Sceglie i finali: le regole migliori fra semi e varianti, diverse fra loro.',
    filtro: ['Filtri a caso battuti al 99% per il terzo pattern', 'Una variante di uscita o di orario deve fare meglio della regola da cui viene', 'Correlazione fra finali sotto 0,7'],
    perche: 'Pochi sistemi diversi valgono più di molte varianti dello stesso.' },
  { id: 'L1', titolo: 'Ricalcolo esatto', sotto: 'una posizione alla volta, gemello, segnale', disegno: disegnoL1,
    cosa: 'I finali si ricalcolano con il motore che segue ProRealTime (una posizione alla volta) e si controlla da dove viene il guadagno.',
    filtro: ['Stessa regola sull\'Euro Stoxx: deve guadagnare anche lì', 'Positiva in entrambe le metà del periodo', 'Segnale isolato: almeno metà del guadagno non viene dall\'ora né dalla salita del DAX'],
    perche: 'Un long sul DAX guadagna anche solo perché il DAX nel lungo periodo sale.' },
  { id: 'L3', titolo: 'Uscite', sotto: 'stop dai trade', disegno: disegnoL3,
    cosa: 'Prova uno stop messo appena sotto il punto più basso toccato dai trade vincenti e due stop tondi.',
    filtro: ['Utile / drawdown migliore di prima'], perche: 'Lo stop si legge dai trade, non si cerca provando tutti i valori.' },
  { id: 'L4', titolo: 'Verifica', sotto: 'si paga il conto delle prove', disegno: disegnoL4,
    cosa: 'Controlli che non scelgono niente: confermano o scartano.',
    filtro: ['Ricalcolo minuto per minuto e costi IG doppi', 'DSR: probabilità che il risultato regga dopo tutte le prove fatte (contate come gruppi indipendenti)', 'La ricerca intera rifatta anno per anno con i soli anni precedenti deve guadagnare almeno metà', 'Filtri di Andrea: soglia in euro, curva regolare, 70% di anni positivi'],
    perche: 'Con decine di migliaia di prove qualcosa di bello esce sempre per caso: qui si vede se è caso.' },
  { id: 'finale', titolo: 'Prova finale', sotto: 'anni mai guardati', disegno: disegnoFinale,
    cosa: 'Una volta sola, sui sistemi che hanno passato tutto, si guardano gli anni tenuti da parte.',
    filtro: ['2024-2025: utile positivo e almeno metà del guadagno a trade dell\'in-sample', '2011-2013: non deve perdere né andare in modo disastroso', 'Prima del 2011: scarta solo se disastroso'],
    perche: 'Il futuro recente conta più del passato lontano: il mercato cambia.' },
];
function libreriaPattern(lista) {
  const per = {}; lista.forEach(p => { (per[p.categoria] = per[p.categoria] || []).push(p); });
  const STRATO = { 1: 'forza bruta e moltiplicazione 1', 2: 'moltiplicazione 1', 3: 'moltiplicazione 2' };
  return h('div', { class: 'cf-libreria' }, Object.entries(per).map(([cat, ps]) => h('div', {}, h('h4', {}, `${cat} `, h('span', { class: 'muto' }, `· ${ps.length} · ${STRATO[ps[0].strato]}`)),
    h('ul', {}, ps.map(p => h('li', { title: `${p.condizione[0]} ${p.condizione[1]} ${p.condizione[2]}` }, p.nome))))));
}
async function paginaComeFunziona() {
  const mio = giro;
  let imb = null, nomeRic = null, libreria = null;
  try {
    const l = (await api('/ricerche')).filter(r => r.formato === 'ricerca' && r.stato === 'finita' && r.ampiezza);
    for (const r of l) { const d = await api('/ricerche/' + r.nome); if (d.cicli) { nomeRic = r.nome; imb = d.imbuto; libreria = d.pattern; break; } }
  } catch (e) { /* senza ricerche la pagina si mostra lo stesso */ }
  const conta = {}; (imb || []).forEach(x => { conta[x.strato] = x; });
  let sel = memo('strato') || 'forza';
  const pannello = h('div', { class: 'cf-pannello' });
  const chips = h('div', { class: 'cf-percorso' });
  const mostra = id => {
    sel = id; memo('strato', id);
    const s = STRATI.find(x => x.id === id);
    chips.querySelectorAll('button').forEach(b => b.classList.toggle('sel', b.dataset.id === id));
    const c = conta[id];
    pannello.replaceChildren(h('div', { class: 'cf-disegno' }, s.disegno()),
      h('div', { class: 'cf-testo' }, h('h3', {}, s.titolo), h('p', {}, s.cosa), h('div', { class: 'et' }, 'Il filtro'), h('ul', {}, s.filtro.map(f => h('li', {}, f))),
        h('p', { class: 'muto' }, s.perche),
        c ? h('p', { class: 'cf-numero' }, `Nella ricerca ${nomeRic}: `, h('strong', {}, String(c.n)), c.provati != null ? ` su ${c.provati} provati` : '', ` · ${c.nome.toLowerCase()}`) : null));
  };
  STRATI.forEach((s, k) => {
    if (k) chips.append(h('span', { class: 'freccia' }, '→'));
    const c = conta[s.id];
    chips.append(h('button', { type: 'button', 'data-id': s.id, class: /^(forza|molt)/.test(s.id) ? 'molt' : '', onclick: () => mostra(s.id) }, h('strong', {}, s.titolo), h('span', {}, s.sotto), c ? h('em', {}, nf(c.n, 0)) : null));
  });
  mostra(STRATI.some(x => x.id === sel) ? sel : 'forza');
  const periodi = h('div', { class: 'cf-periodi' }, [['2008-2010', 'f-ind', 'fuori campione lontano', 'scarta solo se disastroso', 3],
    ['2011-2013', 'f-vic', 'fuori campione vicino', 'scarta se perde o è disastroso', 3], ['2014-2023', 'f-in', 'in-sample: tutta la ricerca', 'diviso in 10 anni: si sceglie su 8, si misura sui 2 lasciati fuori, in tutti i 45 modi', 10],
    ['2024 – mag 2025', 'f-out', 'prova finale', 'decide, una volta sola', 1.5], ['da nov 2025', 'muto', 'ProRealTime', 'il tuo fuori campione', 2.5]].map(([a, c, t, d, w]) =>
    h('div', { style: `flex:${w}` }, h('div', { class: 'cf-blocco', style: `background:var(--${c})` }, a), h('strong', {}, t), h('div', { class: 'muto' }, d))));
  const cpcv = h('div', { class: 'cf-cpcv' }, Array.from({ length: 10 }, (_, i) => h('span', { class: i === 2 || i === 7 ? 'test' : '' }, String(2014 + i))));
  let giroC = 0;
  const anima = setInterval(() => { if (!document.body.contains(cpcv)) return clearInterval(anima); giroC++; const a = giroC % 10, b = (giroC * 3 + 4) % 10 === a ? (a + 5) % 10 : (giroC * 3 + 4) % 10; [...cpcv.children].forEach((x, i) => x.classList.toggle('test', i === a || i === b)); }, 1400);
  vedi(mio, h('h1', {}, 'Come funziona'),
    h('p', { class: 'muto' }, 'Una ricerca alterna moltiplicazioni (arancio: si provano tutte le combinazioni) e filtri (blu: restano solo le migliori e diverse fra loro), poi ricalcola i finali in modo esatto e li verifica. Clic su uno strato.'),
    chips, pannello,
    libreria ? h('div', {}, h('h2', {}, `I pattern: ${libreria.length}, dalle tue librerie riordinate`),
      h('p', { class: 'muto' }, 'Ogni pattern è una domanda sul mercato con una soglia tonda in escursioni medie giornaliere (non in % del prezzo). Passa il mouse su un nome per vedere la condizione.'), libreriaPattern(libreria)) : null,
    h('h2', {}, 'Quali anni servono a cosa'), periodi,
    h('div', { class: 'cf-riga' }, h('div', {}, h('h3', {}, 'Anni lasciati fuori, a turno'), h('p', { class: 'muto' }, 'Dentro il 2014-2023 ogni scelta si fa su 8 anni e si misura sui 2 lasciati fuori (in arancio), cambiando coppia 45 volte. Conta il risultato sugli anni lasciati fuori.'), cpcv),
      h('div', {}, h('h3', {}, 'Euro di oggi'), h('p', { class: 'muto' }, 'Il DAX del 2017 si muoveva di 115 punti al giorno, quello del 2023 di 190. I guadagni si misurano in "giornate medie" e si riportano in euro con la volatilità del 2023, così un trade del 2017 pesa come uno di oggi.'))),
    h('h2', {}, 'Cosa vedi alla fine'),
    h('p', { class: 'muto' }, 'Nella pagina della ricerca: l\'imbuto con quanti passano ogni strato e, sotto, solo i sistemi da provare su ProRealTime. Per ognuno: la curva quadrata con gli anni colorati e la linea tratteggiata della stessa ora in tutti i giorni, sette numeri (guadagno a trade, drawdown, lordo/costi, ore in mercato, regolarità, trade l\'anno, segnale isolato) e il codice ProRealCode da copiare. Tutto il resto è chiuso in sezioni da aprire.'));
}

// ------------------------------------------------------------------ registro e portafoglio
let famigliaRegistro = '';
async function paginaRegistro() {
  const mio = giro;
  const r = await api('/registro' + (famigliaRegistro ? '?famiglia=' + encodeURIComponent(famigliaRegistro) : '')), c = r.conteggio;
  const sel = h('select', { onchange: ev => { famigliaRegistro = ev.target.value; paginaRegistro(); } }, h('option', { value: '' }, 'Famiglia: tutte'),
    r.famiglie.map(f => h('option', { value: f, selected: f === famigliaRegistro }, f)));
  vedi(mio, h('h1', {}, 'Registro dei tentativi'), h('div', { class: 'filtri' }, sel,
    h('span', { class: 'muto' }, `${c.n_prove} prove · prove effettive ${nf(c.n_effettivo_autovalori, 1)} (autovalori) / ${c.n_effettivo_cluster ?? '–'} (gruppi) · varianza degli Sharpe ${nf(c.var_sharpe, 3)}`)),
    h('div', { class: 'tabella-cont' }, h('table', {}, h('thead', {}, h('tr', {}, ['Id', 'Quando', 'Esperimento', 'Famiglia', 'Prodotto', 'Parametri', 'Sharpe', 'Giorni'].map((t, i) => h('th', { class: i < 6 ? 'sx' : '' }, t)))),
      h('tbody', {}, r.tentativi.map(t => h('tr', {}, h('td', { class: 'sx' }, t.id), h('td', { class: 'sx' }, t.quando.replace('T', ' ').slice(0, 16)), h('td', { class: 'sx' }, t.esperimento),
        h('td', { class: 'sx' }, t.famiglia), h('td', { class: 'sx' }, t.prodotto), h('td', { class: 'sx' }, Object.entries(t.parametri).map(([k, v]) => `${k}=${v}`).join(', ')),
        h('td', {}, nf(t.sharpe)), h('td', {}, t.giorni)))))));
}
function paginaPortafoglio() {
  app.replaceChildren(h('h1', {}, 'Portafoglio'), h('div', { class: 'pannello' },
    h('p', {}, 'Pagina in attesa dei dati. Serve la lista dei trade (data e ora di ingresso e uscita, esito) di ciascun sistema già in produzione, esportata da ProRealTime.'),
    h('p', {}, 'Con quelle liste si calcolano la sovrapposizione dei drawdown, la correlazione nei giorni peggiori, il calendario dell\'esposizione e il contributo di ogni candidato al CDaR del portafoglio; il gruppo "Portafoglio" delle schede resta grigio finché mancano.')));
}

// ------------------------------------------------------------------ router
const ROTTE = [[/^\/ricerche$/, paginaRicerche], [/^\/ricerche\/([^/]+)$/, paginaRicerca], [/^\/come-funziona$/, paginaComeFunziona], [/^\/campagne\/([^/]+)$/, paginaCampagna],
  [/^\/sistemi\/([^/]+)\/([^/]+)(?:\/[a-z]+)?$/, paginaScheda], [/^\/esperimenti\/([^/]+)$/, paginaEsperimento],
  [/^\/registro$/, paginaRegistro], [/^\/portafoglio$/, paginaPortafoglio]];
async function render() {
  const mio = ++giro, p = decodeURIComponent(location.hash.replace(/^#/, '')) || '/ricerche';
  document.querySelectorAll('#menu a').forEach(a => a.classList.toggle('attiva', p.startsWith('/' + a.dataset.voce) || (a.dataset.voce === 'ricerche' && /^\/(sistemi|esperimenti)/.test(p))));
  for (const [re, f] of ROTTE) {
    const m = p.match(re);
    if (!m) continue;
    try { await f(...m.slice(1)); } catch (e) { if (mio === giro) app.replaceChildren(h('p', { class: 'neg' }, 'Errore: ' + e.message)); }
    if (!p.includes('/sistemi/') && !p.startsWith('/ricerche/')) window.scrollTo(0, 0);
    return;
  }
  app.replaceChildren(h('p', { class: 'muto' }, 'Pagina non trovata.'));
}
function tema(t) { document.documentElement.dataset.theme = t; document.getElementById('tema').textContent = t === 'dark' ? 'Tema chiaro' : 'Tema scuro'; memo('tema', t); }
document.getElementById('tema').addEventListener('click', () => tema(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'));
tema(memo('tema') === 'light' ? 'light' : 'dark');
window.addEventListener('hashchange', render);
api('/versione').then(v => { const el = document.getElementById('versione'); if (el && v.commit) el.textContent = `Fafnir2 · versione ${v.commit} del ${dataIt(v.quando).slice(0, 10)}`; if (el) el.title = v.titolo || ''; }).catch(() => {});
render();
