
// ═══════════════════════════════════════════════════════════════
// DATA EMBED — inlined from dashboard_data.json
// ═══════════════════════════════════════════════════════════════
const RAW_DATA = {};


// ═══════════════════════════════════════════════════════════════
// CHART.JS DEFAULTS
// ═══════════════════════════════════════════════════════════════
Chart.defaults.color = '#8892A4';
Chart.defaults.borderColor = 'rgba(255,255,255,.06)';
Chart.defaults.font.family = "'DM Sans', system-ui, sans-serif";
Chart.defaults.font.size = 11;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.pointStyleWidth = 8;
Chart.defaults.plugins.tooltip.backgroundColor = '#1E2333';
Chart.defaults.plugins.tooltip.borderColor = 'rgba(255,255,255,.1)';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.padding = 10;
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.tooltip.titleColor = '#E8ECF4';
Chart.defaults.plugins.tooltip.bodyColor = '#8892A4';

const COLORS = {
  blue:   '#4F8EF7', purple: '#7C3AED', green:  '#10B981',
  amber:  '#F59E0B', red:    '#EF4444', orange: '#F97316',
  indigo: '#6366F1', pink:   '#EC4899', teal:   '#14B8A6',
};
const PALETTE = Object.values(COLORS);

function gradLine(ctx, color) {
  const g = ctx.createLinearGradient(0,0,0,ctx.canvas.height);
  g.addColorStop(0, color + '40');
  g.addColorStop(1, color + '00');
  return g;
}

// ═══════════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════════
const state = {
  dateMin: RAW_DATA.filters.date_min,
  dateMax: RAW_DATA.filters.date_max,
  marcas:  new Set(RAW_DATA.filters.marcas),
  combs:   new Set(RAW_DATA.filters.combustiveis),
  status:  new Set(RAW_DATA.filters.status),
};

// ═══════════════════════════════════════════════════════════════
// FILTER LOGIC
// ═══════════════════════════════════════════════════════════════
function getFiltered() {
  return RAW_DATA.raw.filter(r =>
    r.data_anuncio >= state.dateMin &&
    r.data_anuncio <= state.dateMax &&
    state.marcas.has(r.marca) &&
    state.combs.has(r.combustivel) &&
    state.status.has(r.status)
  );
}

function groupBy(arr, key) {
  return arr.reduce((acc, r) => {
    (acc[r[key]] = acc[r[key]] || []).push(r);
    return acc;
  }, {});
}

function sum(arr, key) { return arr.reduce((s,r) => s + (r[key]||0), 0); }
function avg(arr, key) { return arr.length ? sum(arr, key) / arr.length : 0; }

// ═══════════════════════════════════════════════════════════════
// KPIs
// ═══════════════════════════════════════════════════════════════
function fmtBRL(v) {
  if (v >= 1e6) return 'R$ ' + (v/1e6).toFixed(1) + 'M';
  if (v >= 1e3) return 'R$ ' + (v/1e3).toFixed(0) + 'k';
  return 'R$ ' + v.toFixed(0);
}
function fmtPct(v) { return v.toFixed(1) + '%'; }
function fmtN(v)   { return v.toLocaleString('pt-BR'); }

function updateKPIs(data) {
  const vendidos  = data.filter(r => r.status === 'Vendido');
  const disponiveis = data.filter(r => r.status === 'Disponível');
  const reservados  = data.filter(r => r.status === 'Reservado');
  const fat       = sum(vendidos, 'preco_brl');
  const ticket    = avg(vendidos, 'preco_brl');
  const conv      = data.length ? vendidos.length / data.length * 100 : 0;
  const churn     = data.length ? (data.length - vendidos.length) / data.length * 100 : 0;

  document.getElementById('kFat').textContent     = fmtBRL(fat);
  document.getElementById('kTicket').textContent  = fmtBRL(ticket);
  document.getElementById('kConv').textContent    = fmtPct(conv);
  document.getElementById('kChurn').textContent   = fmtPct(churn);
  document.getElementById('kTotal').textContent   = fmtN(data.length);
  document.getElementById('kVendidos').textContent= fmtN(vendidos.length);
  document.getElementById('kDisp').textContent    = fmtN(disponiveis.length);
  document.getElementById('kRes').textContent     = fmtN(reservados.length);
  document.getElementById('statCount').textContent= fmtN(data.length);
  document.getElementById('statPeriod').textContent= state.dateMin + ' → ' + state.dateMax;
}

// ═══════════════════════════════════════════════════════════════
// CHARTS REGISTRY
// ═══════════════════════════════════════════════════════════════
const charts = {};
function destroyChart(id) { if(charts[id]) { charts[id].destroy(); delete charts[id]; } }

// ── Volume mensal ──────────────────────────────────────────────
function updateVolume(data) {
  const byMonth = groupBy(data, 'ano_mes');
  const months  = Object.keys(byMonth).sort();
  const counts  = months.map(m => byMonth[m].length);
  // MM3
  const mm3 = counts.map((_, i) => {
    const slice = counts.slice(Math.max(0,i-2), i+1);
    return slice.reduce((a,b)=>a+b,0)/slice.length;
  });

  destroyChart('volume');
  const ctx = document.getElementById('chartVolume').getContext('2d');
  charts.volume = new Chart(ctx, {
    type:'bar',
    data:{
      labels: months,
      datasets:[
        { label:'Anúncios', data:counts, backgroundColor:COLORS.blue+'55',
          borderColor:COLORS.blue, borderWidth:1.5, borderRadius:4,
          borderSkipped:false, yAxisID:'y' },
        { label:'Média Móvel 3m', data:mm3, type:'line', borderColor:COLORS.amber,
          borderWidth:2.5, pointRadius:0, tension:.4,
          fill:false, yAxisID:'y' },
      ]
    },
    options:{ responsive:true, interaction:{mode:'index',intersect:false},
      plugins:{legend:{position:'top'}},
      scales:{
        x:{ grid:{display:false}, ticks:{maxTicksLimit:12, maxRotation:45} },
        y:{ grid:{color:'rgba(255,255,255,.04)'}, ticks:{stepSize:50} }
      }
    }
  });
}

// ── Faturamento mensal ─────────────────────────────────────────
function updateFat(data) {
  const byMonth = groupBy(data, 'ano_mes');
  const months  = Object.keys(byMonth).sort();
  const vals    = months.map(m => {
    const v = byMonth[m].filter(r=>r.status==='Vendido');
    return Math.round(sum(v,'preco_brl'));
  });

  destroyChart('fat');
  const ctx = document.getElementById('chartFat').getContext('2d');
  charts.fat = new Chart(ctx, {
    type:'line',
    data:{labels:months, datasets:[{
      label:'Faturamento R$', data:vals,
      borderColor:COLORS.green, borderWidth:2.5,
      backgroundColor: gradLine(ctx, COLORS.green),
      fill:true, tension:.4, pointRadius:3,
      pointBackgroundColor:COLORS.green,
    }]},
    options:{ responsive:true,
      plugins:{legend:{display:false},tooltip:{
        callbacks:{label:v=>'R$ '+v.raw.toLocaleString('pt-BR')}
      }},
      scales:{
        x:{grid:{display:false},ticks:{maxTicksLimit:10,maxRotation:45}},
        y:{grid:{color:'rgba(255,255,255,.04)'},
          ticks:{callback:v=>v>=1e6?'R$'+(v/1e6).toFixed(1)+'M':'R$'+(v/1e3).toFixed(0)+'k'}}
      }
    }
  });
}

// ── Ticket médio mensal ────────────────────────────────────────
function updateTicket(data) {
  const byMonth = groupBy(data, 'ano_mes');
  const months  = Object.keys(byMonth).sort();
  const ticket  = months.map(m => Math.round(avg(byMonth[m],'preco_brl')));
  const mm3 = ticket.map((_, i) => {
    const sl=ticket.slice(Math.max(0,i-2),i+1); return Math.round(sl.reduce((a,b)=>a+b,0)/sl.length);
  });
  const mm7 = ticket.map((_, i) => {
    const sl=ticket.slice(Math.max(0,i-6),i+1); return Math.round(sl.reduce((a,b)=>a+b,0)/sl.length);
  });

  destroyChart('ticket');
  const ctx = document.getElementById('chartTicket').getContext('2d');
  charts.ticket = new Chart(ctx, {
    type:'line',
    data:{labels:months, datasets:[
      { label:'Ticket Médio', data:ticket, borderColor:COLORS.purple, borderWidth:2,
        backgroundColor:gradLine(ctx,COLORS.purple), fill:true, tension:.4,
        pointRadius:2, pointBackgroundColor:COLORS.purple },
      { label:'MM 3m', data:mm3, borderColor:COLORS.amber, borderWidth:2,
        borderDash:[4,3], fill:false, tension:.4, pointRadius:0 },
      { label:'MM 7m', data:mm7, borderColor:COLORS.red+'99', borderWidth:1.5,
        borderDash:[6,4], fill:false, tension:.4, pointRadius:0 },
    ]},
    options:{ responsive:true, interaction:{mode:'index',intersect:false},
      plugins:{legend:{position:'top'}},
      scales:{
        x:{grid:{display:false},ticks:{maxTicksLimit:10,maxRotation:45}},
        y:{grid:{color:'rgba(255,255,255,.04)'},
          ticks:{callback:v=>'R$'+(v/1e3).toFixed(0)+'k'}}
      }
    }
  });
}

// ── Faturamento por Marca ──────────────────────────────────────
function updateMarca(data) {
  const byMarca = groupBy(data, 'marca');
  const marcas  = Object.keys(byMarca).sort((a,b)=>{
    const fa=sum(byMarca[a].filter(r=>r.status==='Vendido'),'preco_brl');
    const fb=sum(byMarca[b].filter(r=>r.status==='Vendido'),'preco_brl');
    return fb-fa;
  });
  const vals = marcas.map(m => Math.round(sum(byMarca[m].filter(r=>r.status==='Vendido'),'preco_brl')));

  destroyChart('marca');
  const ctx = document.getElementById('chartMarca').getContext('2d');
  charts.marca = new Chart(ctx, {
    type:'bar',
    data:{labels:marcas, datasets:[{
      label:'Faturamento R$', data:vals,
      backgroundColor:PALETTE.map(c=>c+'99'),
      borderColor:PALETTE, borderWidth:1.5, borderRadius:6, borderSkipped:false,
    }]},
    options:{ responsive:true, indexAxis:'y',
      plugins:{legend:{display:false},tooltip:{callbacks:{label:v=>'R$'+Math.round(v.raw).toLocaleString('pt-BR')}}},
      scales:{
        x:{grid:{color:'rgba(255,255,255,.04)'},
          ticks:{callback:v=>v>=1e6?'R$'+(v/1e6).toFixed(1)+'M':'R$'+(v/1e3).toFixed(0)+'k'}},
        y:{grid:{display:false}}
      }
    }
  });
}

// ── Status doughnut ────────────────────────────────────────────
function updateStatus(data) {
  const byStatus = groupBy(data, 'status');
  const labels   = Object.keys(byStatus);
  const vals     = labels.map(s => byStatus[s].length);
  const colors   = labels.map(s => ({
    'Vendido':COLORS.green,'Disponível':COLORS.blue,
    'Reservado':COLORS.amber,'Desconhecido':COLORS.teal
  }[s]||COLORS.indigo));

  destroyChart('status');
  const ctx = document.getElementById('chartStatus').getContext('2d');
  charts.status = new Chart(ctx, {
    type:'doughnut',
    data:{labels, datasets:[{data:vals, backgroundColor:colors.map(c=>c+'CC'),
      borderColor:colors, borderWidth:2, hoverOffset:8}]},
    options:{ responsive:true, cutout:'62%',
      plugins:{legend:{position:'bottom'},
        tooltip:{callbacks:{label:v=>v.label+': '+v.raw.toLocaleString('pt-BR')+
          ' ('+((v.raw/data.length)*100).toFixed(1)+'%)'}}}
      }
    }
  });
}

// ── Preço por combustível ──────────────────────────────────────
function updateComb(data) {
  const byComb = groupBy(data, 'combustivel');
  const combs  = Object.keys(byComb).sort((a,b)=>avg(byComb[b],'preco_brl')-avg(byComb[a],'preco_brl'));
  const vals   = combs.map(c => Math.round(avg(byComb[c],'preco_brl')));

  destroyChart('comb');
  const ctx = document.getElementById('chartComb').getContext('2d');
  charts.comb = new Chart(ctx, {
    type:'bar',
    data:{labels:combs, datasets:[{
      label:'Preço Médio R$', data:vals,
      backgroundColor:PALETTE.slice(0,combs.length).map(c=>c+'88'),
      borderColor:PALETTE.slice(0,combs.length), borderWidth:1.5,
      borderRadius:6, borderSkipped:false,
    }]},
    options:{ responsive:true,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:v=>'R$ '+v.raw.toLocaleString('pt-BR')}}},
      scales:{
        x:{grid:{display:false}},
        y:{grid:{color:'rgba(255,255,255,.04)'},
          ticks:{callback:v=>'R$'+(v/1e3).toFixed(0)+'k'}}
      }
    }
  });
}

// ── Taxa conversão por marca ───────────────────────────────────
function updateConvMarca(data) {
  const byMarca = groupBy(data, 'marca');
  const marcas  = Object.keys(byMarca).sort();
  const rates   = marcas.map(m => {
    const g = byMarca[m];
    return +(g.filter(r=>r.status==='Vendido').length / g.length * 100).toFixed(1);
  });

  destroyChart('convMarca');
  const ctx = document.getElementById('chartConvMarca').getContext('2d');
  charts.convMarca = new Chart(ctx, {
    type:'bar',
    data:{labels:marcas, datasets:[{
      label:'Taxa Conversão %', data:rates,
      backgroundColor:rates.map(r=>r>26?COLORS.green+'88':COLORS.amber+'88'),
      borderColor:rates.map(r=>r>26?COLORS.green:COLORS.amber),
      borderWidth:1.5, borderRadius:6, borderSkipped:false,
    }]},
    options:{ responsive:true,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:v=>v.raw.toFixed(1)+'%'}}},
      scales:{
        x:{grid:{display:false}},
        y:{grid:{color:'rgba(255,255,255,.04)'},max:100,
          ticks:{callback:v=>v+'%'}}
      }
    }
  });
}

// ── Tabela de modelos ──────────────────────────────────────────
function updateTable(data) {
  const byModelo = groupBy(data, 'marca_modelo');
  const modelos  = Object.keys(byModelo).sort((a,b)=>byModelo[b].length-byModelo[a].length).slice(0,15);
  const maxQtd   = byModelo[modelos[0]]?.length || 1;

  const tagClass = s => ({
    'Vendido':'tag-vendido','Disponível':'tag-disponivel',
    'Reservado':'tag-reservado'
  }[s]||'tag-desconhecido');

  const rows = modelos.map(m => {
    const g       = byModelo[m];
    const qtd     = g.length;
    const v       = g.filter(r=>r.status==='Vendido').length;
    const preco   = avg(g,'preco_brl');
    const conv    = (v/qtd*100).toFixed(1);
    const maisFreq= Object.entries(groupBy(g,'status')).sort((a,b)=>b[1].length-a[1].length)[0][0];
    const pct     = (qtd/maxQtd*100).toFixed(0);
    return `<tr>
      <td><b>${m}</b></td>
      <td class="mono">${qtd.toLocaleString('pt-BR')}</td>
      <td>
        <div class="progress-bar" style="width:80px">
          <div class="progress-fill" style="width:${pct}%;background:var(--accent)"></div>
        </div>
      </td>
      <td class="mono">R$ ${Math.round(preco).toLocaleString('pt-BR')}</td>
      <td class="mono">${conv}%</td>
      <td><span class="tag ${tagClass(maisFreq)}">${maisFreq}</span></td>
    </tr>`;
  }).join('');

  document.getElementById('tableModelos').innerHTML = `
    <table>
      <thead><tr>
        <th>Modelo</th><th>Anúncios</th><th>Volume</th>
        <th>Preço Médio</th><th>Conversão</th><th>Status Freq.</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

// ── RFM Grid ───────────────────────────────────────────────────
function buildRFM() {
  const segs = RAW_DATA.rfm_seg;
  const cls  = {
    'Premium':'premium','Alto Volume':'volume',
    'Econômico':'eco','Baixa Relevância':'low','Emergente':'eco'
  };
  const icons = { 'Premium':'🏆','Alto Volume':'📦','Econômico':'💚','Baixa Relevância':'⚠️','Emergente':'🚀' };
  document.getElementById('rfmGrid').innerHTML = segs.map(s => `
    <div class="rfm-card ${cls[s.segmento_rfm]||'low'}">
      <div class="rfm-seg-label">${icons[s.segmento_rfm]||''} ${s.segmento_rfm}</div>
      <div class="rfm-count">${s.n}</div>
      <div class="rfm-sub">modelos únicos</div>
      <div class="rfm-score">Score médio: ${s.score.toFixed(2)}</div>
    </div>`).join('');
}

// ═══════════════════════════════════════════════════════════════
// MASTER UPDATE
// ═══════════════════════════════════════════════════════════════
function updateAll() {
  const data = getFiltered();
  updateKPIs(data);
  updateVolume(data);
  updateFat(data);
  updateTicket(data);
  updateMarca(data);
  updateStatus(data);
  updateComb(data);
  updateConvMarca(data);
  updateTable(data);
}

// ═══════════════════════════════════════════════════════════════
// FILTER BUILDER
// ═══════════════════════════════════════════════════════════════
function buildMultiSelect(containerId, items, stateSet, onChange) {
  const el = document.getElementById(containerId);
  el.innerHTML = items.map(item => `
    <label class="multi-opt ${stateSet.has(item)?'checked':''}">
      <input type="checkbox" value="${item}" ${stateSet.has(item)?'checked':''}/>
      ${item}
    </label>`).join('');
  el.querySelectorAll('input').forEach(cb => {
    cb.addEventListener('change', e => {
      e.target.checked ? stateSet.add(e.target.value) : stateSet.delete(e.target.value);
      e.target.closest('.multi-opt').classList.toggle('checked', e.target.checked);
      onChange();
    });
  });
}

function initFilters() {
  const f = RAW_DATA.filters;
  document.getElementById('fDateMin').value = f.date_min;
  document.getElementById('fDateMax').value = f.date_max;
  document.getElementById('fDateMin').min   = f.date_min;
  document.getElementById('fDateMin').max   = f.date_max;
  document.getElementById('fDateMax').min   = f.date_min;
  document.getElementById('fDateMax').max   = f.date_max;

  document.getElementById('fDateMin').addEventListener('change', e => {
    state.dateMin = e.target.value; updateAll();
  });
  document.getElementById('fDateMax').addEventListener('change', e => {
    state.dateMax = e.target.value; updateAll();
  });

  buildMultiSelect('filterMarcas',  f.marcas,        state.marcas, updateAll);
  buildMultiSelect('filterComb',    f.combustiveis,  state.combs,  updateAll);
  buildMultiSelect('filterStatus',  f.status,        state.status, updateAll);
}

function resetFilters() {
  const f = RAW_DATA.filters;
  state.dateMin = f.date_min;
  state.dateMax = f.date_max;
  state.marcas  = new Set(f.marcas);
  state.combs   = new Set(f.combustiveis);
  state.status  = new Set(f.status);
  document.getElementById('fDateMin').value = f.date_min;
  document.getElementById('fDateMax').value = f.date_max;
  initFilters();
  updateAll();
}

// ═══════════════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════════════
initFilters();
buildRFM();
updateAll();
