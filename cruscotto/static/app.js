'use strict';
/* Cruscotto: pagine con ancora #/..., nessuna libreria esterna, grafici in SVG. */

// ------------------------------------------------------------------ utilità
const app = document.getElementById('app');
let giro = 0;
const vedi = (mio, ...nodi) => { if (mio === giro) app.replaceChildren(...nodi); };
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
const ESITI = { candidato: 'Candidato', da_rivedere: 'Da rivedere', scartato: 'Scartato', non_giudicato: 'Non giudicato' };
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

// ------------------------------------------------------------------ pagina Sistemi
const filtri = { esperimento: '', prodotto: '', lato: '', barre: '', esito: '', decisione_stato: '', q: '' };
let ordine = { k: 'sharpe', dir: -1 };
const RANGO_ESITO = { candidato: 0, da_rivedere: 1, scartato: 2 };
const COLONNE = [
  { k: 'nome', t: 'Nome', v: r => r.nome },
  { k: 'prodotto', t: 'Prodotto', v: r => r.prodotto },
  { k: 'lato', t: 'Lato', v: r => r.lato },
  { k: 'barre', t: 'Barre', title: 'Durata delle barre in minuti', v: r => r.barre },
  { k: 'esito', t: 'Esito', v: r => RANGO_ESITO[r.esito] ?? 9 },
  { k: 'gruppi', t: 'Gruppi', title: 'Caso o vantaggio, costi, regolarità, robustezza, rischio, portafoglio', v: null },
  { k: 'n', t: 'Trade', v: r => r.n },
  { k: 'media', t: 'Media', title: 'Profitto netto medio per trade, in escursioni medie giornaliere', v: r => r.media },
  { k: 'pf', t: 'PF', title: 'Profit factor: somma delle vincite diviso somma delle perdite', v: r => r.pf },
  { k: 'sharpe', t: 'Sharpe', title: 'Rendimento medio giornaliero diviso la sua variabilità, annualizzato', v: r => r.sharpe },
  { k: 'dsr', t: 'DSR', title: 'Deflated Sharpe ratio: probabilità che lo Sharpe sia reale dopo aver contato tutte le prove fatte', v: r => r.dsr },
  { k: 'anni_positivi', t: 'Anni +', title: 'Quota di anni chiusi in profitto', v: r => r.anni_positivi },
  { k: 'media_2019_2023', t: '2019-2023', title: 'Media per trade, in escursioni, negli ultimi cinque anni della scoperta', v: r => r.media_2019_2023 },
  { k: 'netto_euro', t: 'Netto € 1 CFD', title: 'Profitto netto 2011-2023 con 1 CFD IG per punto, in euro', v: r => r.netto_euro },
  { k: 'decisione_stato', t: 'Stato', v: r => STATI.indexOf(r.decisione_stato) },
];
async function paginaSistemi() {
  const mio = giro;
  const righe = await api('/sistemi');
  const valori = k => [...new Set(righe.map(r => r[k]))].sort();
  const conta = f => righe.filter(f).length;
  const riquadri = [['Candidati', conta(r => r.esito === 'candidato')], ['Da rivedere', conta(r => r.esito === 'da_rivedere')],
    ['Scartati', conta(r => r.esito === 'scartato')], ['In verifica', conta(r => r.decisione_stato === 'in verifica')],
    ['Live', conta(r => r.decisione_stato === 'live')]];
  const corpo = h('tbody'), conto = h('span', { class: 'muto' });
  function sel(k, et, opzioni) {
    return h('select', { onchange: ev => { filtri[k] = ev.target.value; ridisegna(); }, title: et },
      h('option', { value: '' }, et + ': tutti'), opzioni.map(([v, t]) => h('option', { value: v, selected: String(filtri[k]) === String(v) }, t)));
  }
  const q = h('input', { type: 'search', placeholder: 'Cerca per nome', value: filtri.q, oninput: ev => { filtri.q = ev.target.value; ridisegna(); } });
  const intest = h('tr', {}, COLONNE.map(c => h('th', { class: c.v ? 'ord' : '', title: c.title, onclick: c.v ? () => {
    ordine = { k: c.k, dir: ordine.k === c.k ? -ordine.dir : (c.k === 'nome' || c.k === 'prodotto' ? 1 : -1) }; ridisegna(); } : null },
    c.t + (ordine.k === c.k ? (ordine.dir > 0 ? ' ▲' : ' ▼') : ''))));
  function ridisegna() {
    const col = COLONNE.find(c => c.k === ordine.k);
    const sel_ = righe.filter(r => (!filtri.esperimento || r.esperimento === filtri.esperimento) && (!filtri.prodotto || r.prodotto === filtri.prodotto) &&
      (!filtri.lato || r.lato === filtri.lato) && (!filtri.barre || String(r.barre) === filtri.barre) && (!filtri.esito || (r.esito || 'non_giudicato') === filtri.esito) &&
      (!filtri.decisione_stato || r.decisione_stato === filtri.decisione_stato) &&
      (!filtri.q || (r.nome + ' ' + r.etichetta).toLowerCase().includes(filtri.q.toLowerCase())));
    if (col && col.v) sel_.sort((a, b) => { const x = col.v(a), y = col.v(b); return (x == null) - (y == null) || (x > y ? 1 : x < y ? -1 : 0) * ordine.dir; });
    conto.textContent = `${sel_.length} di ${righe.length}`;
    intest.replaceChildren(...COLONNE.map(c => h('th', { class: c.v ? 'ord' : '', title: c.title, onclick: c.v ? () => {
      ordine = { k: c.k, dir: ordine.k === c.k ? -ordine.dir : (c.k === 'nome' || c.k === 'prodotto' ? 1 : -1) }; ridisegna(); } : null },
      c.t + (ordine.k === c.k ? (ordine.dir > 0 ? ' ▲' : ' ▼') : ''))));
    corpo.replaceChildren(...sel_.map(r => h('tr', { class: 'clic', onclick: () => { location.hash = `#/sistemi/${r.esperimento}/${r.id}`; } },
      h('td', {}, r.nome, h('div', { class: 'muto', style: 'font-size:11px' }, r.etichetta)),
      h('td', {}, r.prodotto), h('td', {}, r.lato), h('td', {}, r.barre),
      h('td', {}, badge(r.esito)), h('td', {}, pallini(r.gruppi)),
      h('td', {}, r.n), h('td', { class: segno(r.media) }, nf(r.media, 3)), h('td', {}, nf(r.pf)), h('td', {}, nf(r.sharpe)),
      h('td', {}, nf(r.dsr, 3)), h('td', {}, pc(r.anni_positivi)), h('td', { class: segno(r.media_2019_2023) }, nf(r.media_2019_2023, 3)),
      h('td', { class: segno(r.netto_euro) }, eur(r.netto_euro)), h('td', {}, r.decisione_stato))));
  }
  vedi(mio, h('h1', {}, 'Sistemi'),
    h('div', { class: 'riquadri' }, riquadri.map(([t, n]) => h('div', { class: 'riquadro' }, h('div', { class: 'n' }, n), h('div', { class: 'et' }, t)))),
    h('div', { class: 'filtri' }, sel('esperimento', 'Esperimento', valori('esperimento').map(v => [v, v])), sel('prodotto', 'Prodotto', valori('prodotto').map(v => [v, v])),
      sel('lato', 'Lato', [['long', 'long'], ['short', 'short']]), sel('barre', 'Barre', valori('barre').map(v => [v, v + ' min'])),
      sel('esito', 'Esito', Object.entries(ESITI)), sel('decisione_stato', 'Stato', STATI.map(s => [s, s])), q, conto),
    righe.length ? h('div', { class: 'tabella-cont' }, h('table', {}, h('thead', {}, intest), corpo)) :
      h('p', { class: 'muto' }, 'Nessun candidato: lancia un esperimento e poi `esperimento arricchisci <nome>`.'));
  ridisegna();
}

// ------------------------------------------------------------------ scheda
const TAB = [['riepilogo', 'Riepilogo'], ['curva', 'Curva'], ['giudizio', 'Giudizio'], ['robustezza', 'Robustezza'],
  ['calendario', 'Calendario'], ['trade', 'Trade'], ['codice', 'Codice'], ['decisione', 'Decisione']];
async function paginaScheda(esp, id, tab) {
  const mio = giro;
  tab = tab || 'riepilogo';
  const d = await api(`/sistemi/${esp}/${id}`);
  const g = (d.scheda.giudizio || {}), ih = d.intestazione;
  const testata = h('div', { class: 'testata' },
    h('div', { class: 'titolo' }, h('a', { href: '#/sistemi' }, '← Sistemi'), h('h1', { style: 'margin:0' }, d.nome),
      badge(g.esito, g.esito ? ESITI[g.esito] : 'Non giudicato'), h('span', { class: 'muto' }, `${d.scheda.prodotto} · ${d.lato} · barre da ${ih.barre} min`)),
    h('p', { class: 'muto', style: 'margin:6px 0 0' }, d.riga.parametri ? Object.entries(d.riga.parametri).map(([k, v]) => `${k} = ${v}`).join(' · ') : ''),
    h('p', {}, h('strong', {}, 'Ipotesi: '), ih.ipotesi), h('p', { style: 'margin:4px 0 0' }, h('strong', {}, 'Meccanismo: '), ih.meccanismo),
    h('p', { class: 'muto', style: 'margin:4px 0 0' }, h('a', { href: `#/esperimenti/${esp}` }, 'Esperimento'), ` · fonte: ${ih.fonte}`));
  const gruppi = h('div', { class: 'gruppi' }, GRUPPI.map(([k, n]) => {
    const x = (g.gruppi || {})[k] || { esito: 'grigio', sintesi: 'giudizio non calcolato (esegui arricchisci)' };
    return h('div', { class: 'gruppo ' + x.esito, title: n + (x.cancello ? ' (cancello)' : '') }, h('div', { class: 'nome' }, n, ' ', badge(x.esito, x.esito)), h('div', { class: 'sintesi' }, x.sintesi));
  }));
  const nav = h('div', { class: 'schede' }, TAB.map(([k, t]) => h('a', { href: `#/sistemi/${esp}/${id}/${k}`, class: k === tab ? 'attiva' : '' }, t)));
  const f = { riepilogo, curva, giudizio, robustezza, calendario, trade, codice, decisione }[tab] || riepilogo;
  vedi(mio, testata, gruppi, nav, f(d));
}
const num = (e, v, title, cl) => h('div', { class: 'numero', title }, h('div', { class: 'v ' + (cl || '') }, v), h('div', { class: 'e' }, e));
function riepilogo(d) {
  const s = d.scheda, b = s.backtest || {}, sc = s.scheda || {}, r = s.robustezza || {}, e = r.euro || {};
  const mc = (sc['6_montecarlo'] || {}), reg = sc['3_regolarita'] || {};
  const ia = d.commento_ia;
  return h('div', {},
    h('div', { class: 'numeri' },
      num('Trade', b.n), num('Media per trade (esc.)', nf(b.media_esc, 3), 'Netto dei costi IG, in escursioni medie giornaliere', segno(b.media_esc)),
      num('Media lorda (esc.)', nf(b.lorda_esc, 3), 'Prima dei costi'), num('Profit factor', nf(b.pf)),
      num('Sharpe', nf(b.sharpe)), num('DSR', nf((sc['1_sharpe'] || {}).dsr, 3), 'Probabilità che lo Sharpe sia reale dopo tutte le prove'),
      num('PBO', nf((sc['2_pbo'] || {}).pbo, 2), 'Probabilità di sovradattamento della famiglia di prove'),
      num('CPCV mediana', nf((sc['2_cpcv'] || {}).mediana, 2), 'Sharpe mediano sulle combinazioni di anni'),
      num('CPCV 10° percentile', nf((sc['2_cpcv'] || {}).p10, 2)),
      num('Anni positivi', pc(b.anni_positivi)), num('2019-2023 (esc.)', nf(b.media_recente_esc, 3), '', segno(b.media_recente_esc)),
      num('R²', nf(reg.r2, 2), 'Quanto la curva somiglia a una retta'), num('Drawdown max (esc.)', nf(b.dd_max_esc, 1)),
      num('Tempo in mercato', pc(b.in_mercato)),
      num('Netto € 1 CFD', eur(e.profitto), 'Profitto 2011-2023 per 1 CFD IG', segno(e.profitto)), num('Drawdown € 1 CFD', eur(e.drawdown)),
      num('Trade medio €', e.trade_medio == null ? '–' : nf(e.trade_medio, 1) + ' €')),
    ia ? h('div', { class: 'ia' }, h('div', { class: 'et' }, 'Commento dell\'IA, non deterministico'),
      h('div', { class: 'muto', style: 'margin-bottom:6px' }, `Scritto il ${ia.data || 'data non indicata'} · modello ${ia.modello || 'non indicato'}`), md(ia.testo)) :
      h('div', { class: 'ia' }, h('div', { class: 'et' }, 'Commento dell\'IA, non deterministico'), h('p', { class: 'muto' }, 'Non ancora scritto.')));
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
function giudizio(d) {
  const g = d.scheda.giudizio;
  if (!g) return h('p', { class: 'muto' }, 'Giudizio non calcolato: esegui `python -m motore.cli esperimento arricchisci <nome>`.');
  const ordineG = Object.entries(g.gruppi).sort((a, b) => GRAVITA[a[1].esito] - GRAVITA[b[1].esito]);
  return h('div', {}, ordineG.map(([k, x]) => h('div', { class: 'pannello' },
    h('h3', { style: 'margin-top:0' }, x.nome, ' ', badge(x.esito, x.esito), x.cancello ? h('span', { class: 'muto' }, ' · cancello') : null),
    h('div', { class: 'tabella-cont' }, h('table', {}, h('thead', {}, h('tr', {}, ['Voce', 'Valore', 'Soglia', 'Esito', 'Cosa misura'].map((t, i) => h('th', { class: i === 4 || i === 0 ? 'sx' : '' }, t)))),
      h('tbody', {}, [...x.voci].sort((a, b) => GRAVITA[a.esito] - GRAVITA[b.esito]).map(v => h('tr', {},
        h('td', { class: 'sx' }, v.nome), h('td', {}, typeof v.valore === 'number' ? nf(v.valore, 3) : v.valore === true ? 'sì' : v.valore === false ? 'no' : '–'),
        h('td', {}, v.soglia), h('td', {}, badge(v.esito, v.esito)), h('td', { class: 'sx', style: 'white-space:normal;min-width:260px' }, v.spiegazione)))))))));
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
async function paginaEsperimenti() {
  const mio = giro;
  const l = await api('/esperimenti');
  vedi(mio, h('h1', {}, 'Esperimenti'), l.length ? h('div', { class: 'tabella-cont' }, h('table', {},
    h('thead', {}, h('tr', {}, [['Nome'], ['Lato'], ['Prodotti'], ['Barre'], ['Prove', 'Prove di questo esperimento / budget di prove ammesse per la sua scoperta'], ['PBO', 'Probabilità di sovradattamento, massimo fra le famiglie'], ['Candidati'], ['Da rivedere'], ['Scartati']].map(([t, ti]) => h('th', { title: ti }, t)))),
    h('tbody', {}, l.map(e => { const p = Object.values(e.pbo).flatMap(o => Object.values(o)).filter(x => x != null);
      return h('tr', { class: 'clic', onclick: () => { location.hash = '#/esperimenti/' + e.nome; } }, h('td', {}, e.nome), h('td', {}, e.intestazione.direzione), h('td', {}, e.intestazione.prodotti.join(', ')),
        h('td', {}, e.intestazione.barre), h('td', {}, `${e.prove.questa} / ${nf(e.prove.budget, 0)}`), h('td', {}, p.length ? nf(Math.max(...p)) : '–'),
        h('td', {}, e.esiti.candidato), h('td', {}, e.esiti.da_rivedere), h('td', {}, e.esiti.scartato)); })))) : h('p', { class: 'muto' }, 'Nessun esperimento lanciato.'));
}
async function paginaEsperimento(nome) {
  const mio = giro;
  const e = await api('/esperimenti/' + nome), ih = e.intestazione, pr = e.prove;
  vedi(mio, h('p', {}, h('a', { href: '#/esperimenti' }, '← Esperimenti')), h('h1', {}, nome),
    h('div', { class: 'pannello' }, h('p', {}, h('strong', {}, 'Ipotesi: '), ih.ipotesi), h('p', {}, h('strong', {}, 'Meccanismo: '), ih.meccanismo),
      h('p', {}, h('strong', {}, 'Fonte: '), ih.fonte), h('p', {}, h('strong', {}, 'Direzione attesa: '), ih.direzione, ` · modo ${ih.modo} · barre da ${ih.barre} min · ${ih.prodotti.join(', ')}${ih.specchio ? ' · con lo specchio' : ''}`),
      h('p', { class: 'muto' }, `Lanciato il ${ih.quando}`)),
    h('h2', {}, 'Prove sul budget'),
    h('div', { class: 'pannello' }, h('p', {}, `${pr.questa} prove in questo esperimento; ${pr.totali_registro} nel registro dopo il lancio; budget ${nf(pr.budget, 0)} (${pc(pr.totali_registro / pr.budget)}).`),
      h('div', { class: 'barra' }, h('div', { style: `width:${Math.min(100, 100 * pr.totali_registro / pr.budget)}%` }))),
    h('h2', {}, 'PBO ed effettivi per famiglia'),
    h('div', { class: 'tabella-cont' }, h('table', {}, h('thead', {}, h('tr', {}, h('th', {}, 'Famiglia'), h('th', {}, 'Prodotto'), h('th', { title: 'Probabilità di sovradattamento della selezione; soglia ' + e.soglie.pbo }, 'PBO'),
      h('th', { title: 'Numero effettivo di prove indipendenti, per il DSR' }, 'Prove effettive'))),
      h('tbody', {}, Object.entries(e.pbo).flatMap(([f, o]) => Object.entries(o).map(([p, v]) => h('tr', {}, h('td', {}, f), h('td', {}, p), h('td', { class: v != null && v < e.soglie.pbo ? 'pos' : 'neg' }, nf(v)), h('td', {}, nf(pr.n_effettivo[f], 1)))))))),
    h('h2', {}, 'Candidati'),
    h('div', { class: 'tabella-cont' }, h('table', {}, h('thead', {}, h('tr', {}, ['Id', 'Parametri', 'Esito', 'Gruppi', 'Trade', 'Media', 'Sharpe', 'DSR'].map(t => h('th', {}, t)))),
      h('tbody', {}, e.candidati.map(c => h('tr', { class: 'clic', onclick: () => { location.hash = `#/sistemi/${nome}/${c.id}`; } }, h('td', {}, c.id),
        h('td', { class: 'sx' }, Object.entries(c.parametri || {}).map(([k, v]) => `${k}=${v}`).join(', ')), h('td', {}, badge(c.esito)), h('td', {}, pallini(c.gruppi)),
        h('td', {}, c.n), h('td', {}, nf(c.media, 3)), h('td', {}, nf(c.sharpe)), h('td', {}, nf(c.dsr, 3))))))),
    h('h2', {}, 'Resoconto'), e.resoconto ? h('div', { class: 'pannello' }, md(e.resoconto)) : h('p', { class: 'muto' }, 'Nessun resoconto scritto.'));
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
const ROTTE = [[/^\/sistemi$/, paginaSistemi], [/^\/sistemi\/([^/]+)\/([^/]+)(?:\/([a-z]+))?$/, paginaScheda], [/^\/esperimenti$/, paginaEsperimenti],
  [/^\/esperimenti\/([^/]+)$/, paginaEsperimento], [/^\/registro$/, paginaRegistro], [/^\/portafoglio$/, paginaPortafoglio]];
async function render() {
  const mio = ++giro, p = decodeURIComponent(location.hash.replace(/^#/, '')) || '/sistemi';
  document.querySelectorAll('#menu a').forEach(a => a.classList.toggle('attiva', p.startsWith('/' + a.dataset.voce)));
  for (const [re, f] of ROTTE) {
    const m = p.match(re);
    if (!m) continue;
    try { await f(...m.slice(1)); } catch (e) { if (mio === giro) app.replaceChildren(h('p', { class: 'neg' }, 'Errore: ' + e.message)); }
    if (!p.includes('/sistemi/')) window.scrollTo(0, 0);
    return;
  }
  app.replaceChildren(h('p', { class: 'muto' }, 'Pagina non trovata.'));
}
function tema(t) { document.documentElement.dataset.theme = t; document.getElementById('tema').textContent = t === 'dark' ? 'Tema chiaro' : 'Tema scuro'; memo('tema', t); }
document.getElementById('tema').addEventListener('click', () => tema(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'));
tema(memo('tema') === 'light' ? 'light' : 'dark');
window.addEventListener('hashchange', render);
render();
