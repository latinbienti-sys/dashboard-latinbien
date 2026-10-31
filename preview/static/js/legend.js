// Honda Legend - Planes de Financiamiento
// Agrega leyenda informativa debajo del selector de plazo en el simulador
(function(){
  function addLegend(){
    if(document.getElementById('honda-plazo-legend')) return;
    var plazoLabel = null;
    document.querySelectorAll('label, span, div, p').forEach(function(el){
      if(el.textContent.indexOf('Plazo de Financiamiento') !== -1) plazoLabel = el;
    });
    if(!plazoLabel) return;
    var container = plazoLabel.closest('div[class]');
    if(!container) return;
    var parent = container.parentElement;
    if(!parent) return;
    var legend = document.createElement('div');
    legend.id = 'honda-plazo-legend';
    legend.style.cssText = 'margin-top:12px;padding:12px 14px;border-radius:10px;background:linear-gradient(135deg,#f8fafc,#eff6ff);border:1px solid #dbeafe;font-family:inherit;';
    legend.innerHTML = '<div style="font-weight:600;color:#1e40af;font-size:13px;margin-bottom:6px;">\u{1F4A1} Planes de Financiamiento</div><div style="display:flex;flex-direction:column;gap:5px;font-size:12px;color:#475569;"><div style="display:flex;align-items:center;gap:8px;"><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#9ca3af;flex-shrink:0;"></span><span>12 y 24 meses \u2014 Inicial 50% del valor del veh\u00EDculo</span></div><div style="display:flex;align-items:center;gap:8px;"><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#CC0000;flex-shrink:0;"></span><span>36 y 48 meses \u2014 Inicial 30% del valor del veh\u00EDculo</span></div></div>';
    parent.insertBefore(legend, container.nextSibling);
  }
  var tries = 0;
  var iv = setInterval(function(){
    tries++;
    addLegend();
    if(tries > 60) clearInterval(iv);
  }, 500);
})();
