/* Embudo de Ventas - app.js
   Frontend local. Lee el JSON embebido (#data) como base historica y lo
   actualiza en vivo desde cache_live.json (escrito por sync_live.py),
   sin consultar Odoo desde el navegador. */
var D = JSON.parse(document.getElementById('data').textContent);
var uids = D.execs.map(function(e){ return e.uid; });

/* ---------------------------- configuracion (config.js) ------------------ */
function cfg(k, d){ return (typeof CONFIG !== 'undefined' && CONFIG[k] !== undefined) ? CONFIG[k] : d; }
function pad(n){ return (n<10?'0':'')+n; }
function hoyISO(){ var h = new Date(); return h.getFullYear()+'-'+pad(h.getMonth()+1)+'-'+pad(h.getDate()); }

/* Fecha corte maxima: CONFIG.MAX_FECHA_CORTE ('auto' = dia 03 del mes
   actual, o 'YYYY-MM-DD') y sobreescribible por URL ?corte=YYYY-MM-DD */
function fechaCorte(){
  var c = cfg('MAX_FECHA_CORTE', 'auto');
  var m = /[?&]corte=(\d{4}-\d{2}-\d{2})/.exec(location.search || '');
  if(m) c = m[1];
  if(!c || c === 'auto'){
    var h = new Date();
    c = h.getFullYear()+'-'+pad(h.getMonth()+1)+'-03';
  }
  if(c > hoyISO()) c = hoyISO();
  return c;
}

/* ------------------------------- utilidades ------------------------------ */
function esc(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function dinero(n){ n = Math.round(Number(n)||0); return n.toLocaleString('en-US'); }
function cierreStage(){ var cs=null; (D.stages||[]).forEach(function(s){ if(s.toLowerCase().indexOf('cierre')>=0) cs=s; }); return cs; }
function diasInRange(a,b){ return (D.dias||[]).filter(function(d){ return d>=a && d<=b; }); }
function diasDelMes(ym){ return (D.dias||[]).filter(function(d){ return d.indexOf(ym)===0; }); }
function sumDia(daysArr,uid){ var o={c:0,t:0,s:0,a:0}; daysArr.forEach(function(ds){ var dd=(D.daily[ds]||{})[uid]; if(dd){ o.c+=dd.c; o.t+=dd.t; o.s+=dd.s; o.a+=dd.a; } }); return o; }
function sumMov(daysArr,uid,stage){ var n=0; daysArr.forEach(function(ds){ var mm=(D.moves[ds]||{})[uid]||{}; n += mm[stage]||0; }); return n; }
function sumVen(daysArr,uid){ var n=0; daysArr.forEach(function(ds){ var vv=(D.ventas[ds]||{})[uid]||0; n+=vv; }); return n; }
function logrado(uid,stage,daysArr){
  if(stage==='Contacto Tienda') return sumDia(daysArr,uid).s;
  if(stage==='Seguimiento whatsapp Corporativo') return sumDia(daysArr,uid).a;
  return sumMov(daysArr,uid,stage);
}

/* Meta diaria por ejecutivo para los semaforos:
   CONFIG.META_DIA_TOTAL si esta definida, si no la suma de meta_diaria. */
function metaDiaTotal(){
  var m = Number(cfg('META_DIA_TOTAL', 0)) || 0;
  if(m > 0) return m;
  var t = 0, md = D.meta_diaria || {};
  Object.keys(md).forEach(function(k){ t += Number(md[k]) || 0; });
  return t;
}

/* Semaforo: verde = meta lograda, amarillo = gestion parcial, rojo = sin actividad */
function semHtml(total, meta){
  total = Number(total) || 0; meta = Number(meta) || 0;
  var pct = meta > 0 ? Math.round(total/meta*100) : (total > 0 ? 100 : 0);
  var cls, txt;
  if(!(total > 0)){ cls = 'rojo'; txt = 'Sin actividad'; }
  else if(meta <= 0){ cls = 'verde'; txt = 'Con actividad'; }
  else if(total >= meta){ cls = 'verde'; txt = 'Meta lograda'; }
  else { cls = 'amarillo'; txt = 'Parcial ' + pct + '%'; }
  return '<span class="sem"><i class="punto '+cls+'"></i>'+txt+'</span>';
}

var estado = { desde:'', hasta:'' };

/* ------------------------- tablas del rango activo ------------------------ */
function renderDaily(){
  var days = diasInRange(estado.desde, estado.hasta);
  var filas = D.execs.map(function(e){
    var x = sumDia(days, e.uid), tot = x.c+x.t+x.s;
    return '<tr><td>'+esc(e.nombre)+'</td><td class="num">'+x.c+'</td><td class="num">'+x.t+'</td>'+
           '<td class="num">'+x.a+'</td><td class="num">'+x.s+'</td><td class="num">'+tot+'</td></tr>';
  }).join('');
  var tv={c:0,t:0,s:0,a:0};
  D.execs.forEach(function(e){ var x=sumDia(days,e.uid); tv.c+=x.c; tv.t+=x.t; tv.s+=x.s; tv.a+=x.a; });
  document.getElementById('tbody-daily').innerHTML = filas +
    '<tr class="total"><td>Total</td><td class="num">'+tv.c+'</td><td class="num">'+tv.t+'</td>'+
    '<td class="num">'+tv.a+'</td><td class="num">'+tv.s+'</td><td class="num">'+(tv.c+tv.t+tv.s)+'</td></tr>';
}

/* Gestion diaria de ejecutivos con semaforo (dia seleccionado) */
function renderDiaGestion(){
  var tb = document.getElementById('tbody-dia-gestion');
  if(!tb) return;
  var inp = document.getElementById('dia-gestion');
  var dia = (inp && inp.value) || estado.hasta;
  var meta = metaDiaTotal();
  var filas = D.execs.map(function(e){
    var x = sumDia([dia], e.uid), tot = x.c+x.t+x.s;
    var pct = meta > 0 ? Math.round(tot/meta*100) : (tot > 0 ? 100 : 0);
    return '<tr><td>'+esc(e.nombre)+'</td><td class="num">'+x.c+'</td><td class="num">'+x.t+
      '</td><td class="num">'+x.a+'</td><td class="num">'+x.s+'</td>'+
      '<td class="num"><b>'+tot+'</b></td><td class="num">'+pct+'%</td>'+
      '<td>'+semHtml(tot, meta)+'</td></tr>';
  }).join('');
  var tv={c:0,t:0,s:0,a:0};
  D.execs.forEach(function(e){ var x=sumDia([dia],e.uid); tv.c+=x.c; tv.t+=x.t; tv.s+=x.s; tv.a+=x.a; });
  var ttot = tv.c+tv.t+tv.s;
  tb.innerHTML = filas +
    '<tr class="total"><td>Total '+esc(dia||'')+'</td><td class="num">'+tv.c+'</td>'+
    '<td class="num">'+tv.t+'</td><td class="num">'+tv.a+'</td><td class="num">'+tv.s+'</td>'+
    '<td class="num">'+ttot+'</td><td class="num">'+(meta>0?Math.round(ttot/meta*100):0)+'%</td>'+
    '<td>'+semHtml(ttot, meta)+'</td></tr>';
  var nota = document.getElementById('meta-dia-nota');
  if(nota) nota.innerHTML = 'D&iacute;a: <b>'+esc(dia||'-')+'</b> &middot; Meta diaria por ejecutivo: <b>'+
    meta+'</b> (CONFIG.META_DIA_TOTAL o suma de metas del embudo).';
}

function renderFunnel(){
  var days = diasInRange(estado.desde, estado.hasta);
  document.getElementById('funnel-rango').innerHTML = estado.desde + ' a ' + estado.hasta;
  var stages = D.stages||[];
  var maxf = 1;
  var rows = D.execs.map(function(e){
    var row = {nombre:e.nombre};
    stages.forEach(function(st){ row[st] = logrado(e.uid,st,days)||0; });
    stages.forEach(function(st){ if(row[st]>maxf) maxf=row[st]; });
    return row;
  });
  var totals = {}; stages.forEach(function(s){ totals[s]=0; });
  rows.forEach(function(r){ stages.forEach(function(st){ totals[st]+=r[st]; }); });
  document.getElementById('thead-funnel').innerHTML = '<tr><th>Ejecutivo</th>'+
    stages.map(function(s){ return '<th>'+esc(s)+'</th>'; }).join('')+'</tr>';
  document.getElementById('tbody-funnel').innerHTML = rows.map(function(r){
    var celdas = stages.map(function(s){
      var v=r[s]||0, an=Math.round(v/maxf*100);
      return '<td class="num"><div class="bar-fondo"><i style="width:'+an+'%">&nbsp;'+v+'</i></div></td>';
    }).join('');
    return '<tr><td>'+esc(r.nombre)+'</td>'+celdas+'</tr>';
  }).join('') + '<tr class="total"><td>Total</td>'+
    stages.map(function(s){ return '<td class="num">'+totals[s]+'</td>'; }).join('')+'</tr>';
}

function renderGestion(){
  var days = diasInRange(estado.desde, estado.hasta), nd = days.length;
  var stages = D.stages||[];
  var meta = {}; stages.forEach(function(s){ meta[s]=Math.round((D.meta_diaria[s]||0)*nd); });
  var filas = D.execs.map(function(e){
    var celdas = stages.map(function(s){
      var lo = logrado(e.uid,s,days)||0, pe = Math.max(0, meta[s]-lo), ok = lo>=meta[s];
      var color = ok ? '#1e8e5a' : '#0f3b6e';
      return '<td class="num"><b style="color:'+color+'">'+lo+'</b><div class="nota" style="font-size:10px">pend '+pe+'</div></td>';
    }).join('');
    return '<tr><td>'+esc(e.nombre)+'</td>'+celdas+'</tr>';
  }).join('');
  var tot={meta:0,log:0};
  document.getElementById('thead-gestion').innerHTML =
    '<tr><th>Ejecutivo</th>'+stages.map(function(s){return '<th>'+esc(s)+'</th>';}).join('')+'</tr>'+
    '<tr class="total"><th>Meta del rango ('+nd+' d&iacute;as)</th>'+
    stages.map(function(s){ tot.meta += meta[s]; return '<th class="num">'+meta[s]+'</th>'; }).join('')+'</tr>';
  document.getElementById('tbody-gestion').innerHTML = filas;
  var totlog = stages.map(function(s){
    var t=0; D.execs.forEach(function(e){ t += logrado(e.uid,s,days)||0; }); return '<td class="num">'+t+'</td>';
  }).join('');
  document.getElementById('tfoot-gestion').innerHTML = '<tr class="total"><td>Total logrado</td>'+totlog+'</tr>';
  var ym = estado.hasta.slice(0,7), md = diasDelMes(ym);
  var fecha = new Date(estado.hasta.slice(0,4), +estado.hasta.slice(5,7)-1, 1).toLocaleDateString('es', {month:'long', year:'numeric'});
  var vLog=0; D.execs.forEach(function(e){ vLog += sumVen(md,e.uid); });
  var vMeta = Math.round(D.sales_meta||0), vPend = Math.max(0, vMeta-vLog);
  document.getElementById('gestion-venta').innerHTML =
    'Venta del mes (<b>'+fecha+'</b>): <b>US$'+dinero(vLog)+'</b> &middot; Meta: US$'+dinero(vMeta)+
    ' &middot; Pendiente: US$'+dinero(vPend);
}

function renderCierre(){
  var days = diasInRange(estado.desde, estado.hasta);
  var cs = cierreStage();
  var filas = D.execs.map(function(e){
    var x = sumDia(days,e.uid);
    var venta = sumVen(days,e.uid), cierres = cs ? (sumMov(days,e.uid,cs)||0) : 0;
    return '<tr><td>'+esc(e.nombre)+'</td><td class="num">'+x.c+'</td><td class="num">'+x.t+'</td>'+
           '<td class="num">'+x.s+'</td><td class="num"><b style="color:'+(cierres?'#1e8e5a':'#0f3b6e')+'">'+cierres+'</b></td>'+
           '<td class="num"><b>US$'+dinero(venta)+'</b></td></tr>';
  }).join('');
  var tv={p:0,a:0,s:0,ci:0,v:0};
  D.execs.forEach(function(e){ var x=sumDia(days,e.uid); tv.p+=x.c; tv.a+=x.t; tv.s+=x.s;
      var ci = cs ? (sumMov(days,e.uid,cs)||0) : 0; tv.ci+=ci; tv.v+=sumVen(days,e.uid); });
  document.getElementById('tbody-cierre').innerHTML = filas +
    '<tr class="total"><td>Total</td><td class="num">'+tv.p+'</td><td class="num">'+tv.a+'</td>'+
    '<td class="num">'+tv.s+'</td><td class="num">'+tv.ci+'</td><td class="num">US$'+dinero(tv.v)+'</td></tr>';
  document.getElementById('cierre-nota').innerHTML =
    'Resultado del <b>'+estado.desde+'</b> al <b>'+estado.hasta+'</b>: prospectaron <b>'+tv.p+'</b>, '+
    'atendieron <b>'+tv.a+'</b>, cerraron <b>'+tv.ci+'</b>.';
}

function renderHistorico(nombre){
  var hd = document.getElementById('hist-desde').value || estado.desde;
  var hh = document.getElementById('hist-hasta').value || estado.hasta;
  var days = diasInRange(hd, hh);
  var uid = null;
  D.execs.forEach(function(e){ if(e.nombre===nombre) uid=e.uid; });
  var meta = metaDiaTotal();
  var ss = days.map(function(ds){
    var p=0,a=0,ci=0,v=0,act=0;
    if(uid!==null){
      var x = sumDia([ds],uid);
      p=x.c; a=x.t; ci=cierreStage()?(sumMov([ds],uid,cierreStage())||0):0; v=sumVen([ds],uid);
      act=x.c+x.t+x.s;
    } else {
      D.execs.forEach(function(e){
        var x=sumDia([ds],e.uid);
        p+=x.c; a+=x.t; ci+=cierreStage()?(sumMov([ds],e.uid,cierreStage())||0):0; v+=sumVen([ds],e.uid);
        act+=x.c+x.t+x.s;
      });
    }
    return {ds:ds, p:p, a:a, c:ci, v:v, act:act};
  });
  document.getElementById('tbody-historico').innerHTML = ss.map(function(x){
    return '<tr><td>'+x.ds+'</td><td class="num">'+x.p+'</td><td class="num">'+x.a+'</td>'+
           '<td class="num">'+x.c+'</td><td class="num">'+dinero(x.v)+'</td>'+
           '<td>'+semHtml(x.act, meta)+'</td></tr>';
  }).join('') || '<tr><td colspan="6" class="nota">Sin d&iacute;as en el rango seleccionado.</td></tr>';
  var tp=0,ta=0,tc=0,tv=0,tact=0;
  ss.forEach(function(x){ tp+=x.p; ta+=x.a; tc+=x.c; tv+=x.v; tact+=x.act; });
  document.getElementById('tbody-historico').insertAdjacentHTML('beforeend',
    '<tr class="total"><td>Total</td><td class="num">'+tp+'</td><td class="num">'+ta+'</td>'+
    '<td class="num">'+tc+'</td><td class="num">'+dinero(tv)+'</td>'+
    '<td>'+semHtml(tact, meta*ss.length)+'</td></tr>');
}

function renderVista(){
  var ym = estado.hasta.slice(0,7);
  var days = diasDelMes(ym);
  var stages = D.stages||[];
  function vrow(e){
    var funnel = {};
    stages.forEach(function(st){ funnel[st] = logrado(e.uid,st,days)||0; });
    var serie = days.map(function(ds){ var x=sumDia([ds],e.uid); return x.c+x.t+x.s; });
    return {nombre:e.nombre, funnel:funnel, serie:serie, venta:sumVen(days,e.uid)};
  }
  var rows = D.execs.map(vrow);
  var global = {nombre:'GLOBAL', funnel:{}, serie:[], venta:0};
  stages.forEach(function(st){ global.funnel[st]=0; rows.forEach(function(r){ global.funnel[st]+=r.funnel[st]; }); });
  for(var i=0;i<days.length;i++){ global.serie[i]=0; rows.forEach(function(r){ global.serie[i]+=r.serie[i]||0; }); }
  rows.forEach(function(r){ global.venta += r.venta; });
  var items = [global].concat(rows);
  var maxf=1, maxd=1;
  items.forEach(function(x){ stages.forEach(function(st){ if(x.funnel[st]>maxf) maxf=x.funnel[st]; }); x.serie.forEach(function(v){ if(v>maxd) maxd=v; }); });
  var fecha = new Date(estado.hasta.slice(0,4), +estado.hasta.slice(5,7)-1, 1).toLocaleDateString('es', {month:'long', year:'numeric'});
  var metaV = Math.round(D.sales_meta||0);
  var filasTodo = rows.map(function(r){
    var celdas = stages.map(function(st){ return '<td class="num">'+(r.funnel[st]||0)+'</td>'; }).join('');
    return '<tr><td>'+esc(r.nombre)+'</td>'+celdas+'<td class="num">US$'+dinero(r.venta)+'</td></tr>';
  }).join('');
  var totFilas = stages.map(function(st){
    var n=0; rows.forEach(function(r){ n += r.funnel[st]||0; }); return '<td class="num">'+n+'</td>';
  }).join('');
  var totVentas = 0; rows.forEach(function(r){ totVentas += r.venta; });
  var thTodo = stages.map(function(s){ return '<th class="num">'+esc(s)+'</th>'; }).join('')+'<th class="num">Venta mes</th>';
  var todosHtml = '<div style="overflow-x:auto"><table><thead><tr><th>Todos los ejecutivos</th>'+thTodo+'</tr></thead>'+
    '<tbody>'+filasTodo+'<tr class="total"><td>Total</td>'+totFilas+'<td class="num">US$'+dinero(totVentas)+'</td></tr></tbody></table></div>';
  document.getElementById('pestanas').innerHTML = items.map(function(x,i){
    return '<button data-i="'+i+'" class="'+(i?'':'activa')+'">'+esc(x.nombre)+'</button>';
  }).join('');
  document.getElementById('panel-vista').innerHTML = items.map(function(x,i){
    var celdas = stages.map(function(st){
      var v=x.funnel[st]||0, an=Math.round(v/maxf*100);
      return '<td class="num"><div class="bar-fondo"><i style="width:'+an+'%">&nbsp;'+v+'</i></div></td>';
    }).join('');
    var cols = x.serie.map(function(v,di){
      var hh=Math.max(3, Math.round(v/maxd*95));
      return '<div class="col"><b>'+v+'</b><i style="height:'+hh+'px"></i><span>'+(di+1)+'</span></div>';
    }).join('');
    var pend = Math.max(0, metaV-x.venta);
    return '<div class="vista-panel" data-i="'+i+'"'+(i?' hidden':'')+'>'+
      '<p class="nota"><b>Informe del mes '+esc(fecha)+'</b> &mdash; '+esc(x.nombre)+'</p>'+
      (i==='0' || i===0 ? todosHtml : '')+
      '<div style="overflow-x:auto"><table><thead><tr><th>Flujo (embudo del mes)</th>'+
      stages.map(function(s){ return '<th class="num">'+esc(s)+'</th>'; }).join('')+'</tr></thead>'+
      '<tbody><tr><td>'+esc(x.nombre)+'</td>'+celdas+'</tr></tbody></table></div>'+
      '<p class="nota">Venta mensual: <b>US$'+dinero(x.venta)+'</b> &middot; Meta: US$'+dinero(metaV)+
      ' &middot; Pendiente: US$'+dinero(pend)+'</p>'+
      '<p class="nota">Atenci&oacute;n diaria del mes (creados + atendidos + contacto tienda)</p>'+
      '<div class="graf-dia">'+cols+'</div></div>';
  }).join('');
  Array.prototype.forEach.call(document.querySelectorAll('#pestanas button'), function(b){ b.onclick = tabClick; });
}
function tabClick(){
  var bts = document.querySelectorAll('#pestanas button');
  bts.forEach(function(b){ b.classList.remove('activa'); });
  this.classList.add('activa');
  Array.prototype.forEach.call(document.querySelectorAll('#panel-vista .vista-panel'), function(p){
    p.hidden = String(p.getAttribute('data-i')) !== this.getAttribute('data-i');
  }, this);
}

function renderLineaCredito(){
  var lc = D.linea_credito || {team:[], rows:[], totals:{por_etapa:{}}, detalle:[], dias:[], por_dia:{}, detalle_dia:{}};
  var th = document.getElementById('thead-lc'), tb = document.getElementById('tbody-lc');
  var thd = document.getElementById('thead-lc-det'), tbd = document.getElementById('tbody-lc-det');
  var stages = ['total','gestionados'].concat(Object.keys(lc.totals.por_etapa||{}));
  th.innerHTML = '<tr><th>Ejecutivo (asesor L&iacute;nea de Cr&eacute;dito)</th>'+
    stages.map(function(s){ return '<th class="num">'+esc(s)+'</th>'; }).join('')+'</tr>';
  tb.innerHTML = lc.rows.map(function(r){
    var por = r.por_etapa||{}, nm = r.norm;
    lc.team.forEach(function(t){ if(t.norm===r.norm) nm = t.nombre; });
    var celdas = stages.map(function(s){
      var v = s==='total' ? r.total : s==='gestionados' ? r.gestionados : (por[s]||0);
      return '<td class="num">'+v+'</td>';
    }).join('');
    return '<tr><td>'+esc(nm)+'</td>'+celdas+'</tr>';
  }).join('');
  var tt = lc.totals, tpor = tt.por_etapa||{};
  var tot = stages.map(function(s){
    var v = s==='total' ? tt.total : s==='gestionados' ? tt.gestionados : (tpor[s]||0);
    return '<td class="num">'+v+'</td>';
  }).join('');
  tb.insertAdjacentHTML('beforeend', '<tr class="total"><td>Total</td>'+tot+'</tr>');
  thd.innerHTML = '<tr><th>Contacto</th><th>Ejecutivo</th><th>Etapa actual del lead</th></tr>';
  tbd.innerHTML = (lc.detalle||[]).map(function(x){
    return '<tr><td>'+esc(x.nombre)+'</td><td>'+esc(x.asesor)+'</td><td>'+esc(x.etapa)+'</td></tr>';
  }).join('') || '<tr><td colspan="3" class="nota">Sin contactos CREDIMOTOS gestionados en el equipo L&iacute;nea de Cr&eacute;dito.</td></tr>';

  var inp = document.getElementById('lc-dia');
  if(inp && !inp.value){
    var hoy = hoyISO();
    inp.value = (lc.dias||[]).indexOf(hoy)>=0 ? hoy : (lc.dias||[]).slice(-1)[0] || hoy;
  }
  renderLcDia(inp ? inp.value : '');
}

function renderLcDia(dia){
  var lc = D.linea_credito || {};
  var stages = lc.stages || [];
  var th = document.getElementById('thead-lc-dia'), tb = document.getElementById('tbody-lc-dia');
  var thd = document.getElementById('thead-lc-diadet'), tbd = document.getElementById('tbody-lc-diadet');
  if(!th) return;
  var metaLc = Number(cfg('META_LC_DIA', 5)) || 0;
  var porDia = (lc.por_dia||{})[dia] || {};
  th.innerHTML = '<tr><th>Gestionados el '+esc(dia||'-')+'</th>'+
    stages.map(function(s){ return '<th class="num">'+esc(s)+'</th>'; }).join('')+
    '<th class="num">Sin clasificar</th><th class="num">Total</th><th>Sem&aacute;foro</th></tr>';
  if(!dia || !Object.keys(porDia).length){
    tb.innerHTML = '<tr><td colspan="'+(stages.length+4)+'" class="nota">Sin gestiones CREDIMOTOS ese d&iacute;a. '+
      'D&iacute;as con datos: '+esc((lc.dias||[]).join(', ')||'ninguno')+'.</td></tr>';
    thd.innerHTML=''; tbd.innerHTML=''; return;
  }
  var tot = {}, totSin = 0, totTotal = 0;
  tb.innerHTML = (lc.team||[]).map(function(t){
    var por = porDia[t.norm]||{};
    var vals = stages.map(function(s){ return por[s]||0; });
    var suma = vals.reduce(function(a,b){ return a+b; },0);
    var total = por._total||0;
    var sin = Math.max(0, total-suma);
    stages.forEach(function(s,i){ tot[s]=(tot[s]||0)+vals[i]; });
    totSin += sin; totTotal += total;
    return '<tr><td>'+esc(t.nombre)+'</td>'+
      vals.map(function(v){ return '<td class="num">'+v+'</td>'; }).join('')+
      '<td class="num">'+sin+'</td><td class="num">'+total+'</td>'+
      '<td>'+semHtml(total, metaLc)+'</td></tr>';
  }).join('');
  tb.insertAdjacentHTML('beforeend','<tr class="total"><td>Total</td>'+
    stages.map(function(s){ return '<td class="num">'+(tot[s]||0)+'</td>'; }).join('')+
    '<td class="num">'+totSin+'</td><td class="num">'+totTotal+'</td>'+
    '<td>'+semHtml(totTotal, metaLc*((lc.team||[]).length||1))+'</td></tr>');
  var det = (lc.detalle_dia||{})[dia] || [];
  thd.innerHTML = '<tr><th>Contacto</th><th>Ejecutivo</th><th>Etapa</th></tr>';
  tbd.innerHTML = det.map(function(x){
    return '<tr><td>'+esc(x.nombre)+'</td><td>'+esc(x.asesor)+'</td><td>'+esc(x.etapa)+'</td></tr>';
  }).join('');
}

/* ------------------------- tiempo real (cache_live) ---------------------- */
var ultimaSync = null, fallos = 0, syncIniciada = false;

function aplicarLive(L){
  if(!L || !L.dias) return;
  var nuevosDias = false;
  L.dias.forEach(function(d){
    if(typeof d === 'string' && D.dias.indexOf(d) < 0){ D.dias.push(d); nuevosDias = true; }
  });
  if(nuevosDias) D.dias.sort();
  (L.execs||[]).forEach(function(e){
    if(!e || e.uid == null) return;
    var uid = String(e.uid);
    var nombre = String(e.nombre || '').trim();
    var excluido = (cfg('EXCLUIR_EJECUTIVOS', []) || []).some(function(x){
      return String(x).trim() === uid || String(x).trim() === nombre;
    });
    if(excluido) return;
    var existe = D.execs.some(function(x){ return String(x.uid) === uid; });
    if(!existe) D.execs.push({uid: uid, nombre: e.nombre || ('UID '+uid)});
  });
  ['daily','moves','ventas'].forEach(function(k){
    var src = L[k] || {}, dst = D[k] = (D[k] || {});
    Object.keys(src).forEach(function(dia){ dst[dia] = src[dia]; });
  });
  if(L.linea_credito){
    var lcl = L.linea_credito;
    var lc = D.linea_credito = (D.linea_credito || {});
    lc.por_dia = lc.por_dia || {}; lc.detalle_dia = lc.detalle_dia || {};
    lc.dias = lc.dias || []; lc.stages = lc.stages || [];
    Object.keys(lcl.por_dia||{}).forEach(function(dia){ lc.por_dia[dia] = lcl.por_dia[dia]; });
    Object.keys(lcl.detalle_dia||{}).forEach(function(dia){ lc.detalle_dia[dia] = lcl.detalle_dia[dia]; });
    (lcl.dias||[]).forEach(function(d){ if(lc.dias.indexOf(d) < 0) lc.dias.push(d); });
    lc.dias.sort();
    (lcl.stages||[]).forEach(function(s){ if(lc.stages.indexOf(s) < 0) lc.stages.push(s); });
  }
  uids = D.execs.map(function(e){ return e.uid; });
  refrescarOpcionesHist();
}

function refrescarOpcionesHist(){
  if(!selHist) return;
  var actual = selHist.value || 'GLOBAL';
  selHist.innerHTML = '<option value="GLOBAL">GLOBAL</option>' +
    D.execs.map(function(e){ return '<option value="'+esc(e.nombre)+'">'+esc(e.nombre)+'</option>'; }).join('');
  selHist.value = actual;
  if(selHist.value !== actual) selHist.value = 'GLOBAL';
}

function haceTexto(iso){
  if(!iso) return '';
  var t = Date.parse(String(iso).replace('Z','+00:00'));
  if(isNaN(t)) return '';
  var min = Math.floor((Date.now() - t) / 60000);
  if(min < 1) return 'hace instantes';
  if(min === 1) return 'hace 1 minuto';
  if(min < 60) return 'hace ' + min + ' minutos';
  var h = Math.floor(min / 60);
  return 'hace ' + h + (h === 1 ? ' hora' : ' horas');
}

function pintarBadge(){
  var b = document.getElementById('badge-sync');
  if(!b) return;
  if(ultimaSync){
    b.className = 'badge-sync ' + (fallos ? 'warn' : 'ok');
    b.textContent = 'Última sincronización: ' + haceTexto(ultimaSync) +
      (fallos ? ' · reintentando…' : '');
  } else if(fallos > 0){
    b.className = 'badge-sync warn';
    b.textContent = 'Sin cache_live.json — ejecute dashboard.bat';
  } else {
    b.className = 'badge-sync espera';
    b.textContent = 'Conectando con el caché local…';
  }
}

function cargarLive(){
  syncIniciada = true;
  return fetch('cache_live.json', {cache: 'no-store'})
    .then(function(r){ if(!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(function(L){
      fallos = 0;
      ultimaSync = (L && L.generado) || null;
      try { aplicarLive(L); } catch(e){ console.warn('aplicarLive:', e); }
      todo();
      pintarBadge();
    })
    .catch(function(){ fallos++; pintarBadge(); });
}

function iniciarTiempoReal(){
  cargarLive();
  var seg = Number(cfg('AUTO_REFRESH_SEG', 60)) || 60;
  setInterval(cargarLive, seg * 1000);
  setInterval(pintarBadge, 30000);
}

/* ------------------------------- refresco total -------------------------- */
function todo(){
  renderDaily();
  renderDiaGestion();
  renderFunnel();
  renderGestion();
  renderCierre();
  renderHistorico(selHist ? selHist.value : 'GLOBAL');
  renderVista();
  renderLineaCredito();
}

/* --------------------------------- arranque ------------------------------ */
var selHist = null;
document.addEventListener('DOMContentLoaded', function(){
  var fd = document.getElementById('fecha-desde'), fh = document.getElementById('fecha-hasta');
  var ULT = D.dias[D.dias.length-1], PRI = D.dias[0];
  /* Fecha corte: el selector "Hasta" (y "Desde") no puede superar MAX_FECHA_CORTE */
  var corte = fechaCorte();
  var maxSel = (ULT < corte ? ULT : corte);
  if(maxSel < PRI) maxSel = ULT;
  fd.min = fh.min = PRI;
  fd.max = fh.max = maxSel;
  estado.desde = estado.hasta = maxSel;
  fd.value = fh.value = maxSel;
  document.getElementById('rango-datos').textContent =
    PRI + ' a ' + ULT + ' · corte ' + maxSel + ' (MAX_FECHA_CORTE)';

  selHist = document.getElementById('sel-hist');
  refrescarOpcionesHist();

  var hds = document.getElementById('hist-desde'), hhs = document.getElementById('hist-hasta');
  hds.min = hhs.min = PRI; hds.max = hhs.max = ULT;
  hds.value = PRI; hhs.value = ULT;
  document.getElementById('btn-hist-filtrar').onclick = function(){ renderHistorico(selHist.value); };
  hds.onchange = function(){ renderHistorico(selHist.value); };
  hhs.onchange = function(){ renderHistorico(selHist.value); };

  /* Gestion diaria de ejecutivos (semaforo): hasta el dia de hoy (en vivo) */
  var dg = document.getElementById('dia-gestion');
  if(dg){
    dg.min = PRI; dg.max = hoyISO();
    dg.value = estado.hasta;
    dg.onchange = function(){ renderDiaGestion(); };
    document.getElementById('btn-dia-gestion').onclick = function(){ renderDiaGestion(); };
  }

  var lcDia = document.getElementById('lc-dia');
  lcDia.max = hoyISO();
  document.getElementById('btn-lc-dia').onclick = function(){ renderLcDia(lcDia.value); };
  document.getElementById('btn-lc-hoy').onclick = function(){
    lcDia.value = hoyISO(); renderLcDia(lcDia.value);
  };
  document.getElementById('btn-lc-todo').onclick = function(){
    var ds = (D.linea_credito||{}).dias||[];
    lcDia.value = ds.length ? ds[ds.length-1] : ''; renderLcDia(lcDia.value);
  };
  lcDia.onchange = function(){ renderLcDia(lcDia.value); };

  /* Aplicar rango: recalcula TODAS las tablas al instante (sin recargar),
     incluida la gestion diaria CREDIMOTOS y la de ejecutivos. */
  function aplicarRango(){
    if(fd.value>fh.value){ var t=fd.value; fd.value=fh.value; fh.value=t; }
    estado.desde = fd.value; estado.hasta = fh.value;
    if(dg) dg.value = estado.hasta;
    lcDia.value = estado.hasta;
    todo();
  }
  document.getElementById('btn-ver').onclick = aplicarRango;
  fd.onchange = function(){ if(fd.value>fh.value) fh.value=fd.value; aplicarRango(); };
  fh.onchange = function(){ if(fh.value<fd.value) fd.value=fh.value; aplicarRango(); };

  todo();
  pintarBadge();
  iniciarTiempoReal();
});
