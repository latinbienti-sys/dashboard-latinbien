(function(){'use strict';

var COLORS = {primary:'#CC0000',bg:'#ffffff',text:'#333333',lightBg:'#f5f5f5',botMsg:'#f0f0f0',userMsg:'#CC0000',border:'#e0e0e0'};
var WA_NUMBER = '584127609024';
var HORARIO = 'Lunes a viernes: 8:00 AM - 5:00 PM\nS\u00e1bados: 8:00 AM - 12:00 PM\nTaller: Lunes a viernes 8:00 AM - 4:00 PM';
var DIRECCION = 'Av. Andr\u00e9s Bello, Local N\u00ba 1-248, Sector C\u00edvico, M\u00e9rida, Venezuela';

var MODELS = {
  city:{name:'Honda City',segment:'Sed\u00e1n',engine:'Motor a gasolina, transmisi\u00f3n autom\u00e1tica/manual seg\u00fan versi\u00f3n',features:'Carrocer\u00eda de tres vol\u00famenes, opci\u00f3n cl\u00e1sica del segmento sed\u00e1n',price:'Consultar con asesor (var\u00eda por versi\u00f3n)',note:'Ensamblado/importado desde Brasil. Entrega inmediata sujeta a disponibilidad.'},
  hrv:{name:'Honda HR-V',segment:'SUV',engine:'Motor a gasolina, transmisi\u00f3n autom\u00e1tica',features:'SUV del segmento medio, equipamiento tecnol\u00f3gico de la marca',price:'Consultar con asesor (var\u00eda por versi\u00f3n)',note:'Ensamblado/importado desde Brasil. Entrega inmediata sujeta a disponibilidad.'},
  wrv:{name:'Honda WR-V',segment:'SUV compacta',engine:'1.5L i-VTEC, 119 hp, 145 Nm, transmisi\u00f3n autom\u00e1tica CVT con paddle shifts',features:'Aire acondicionado digital delantero y trasero, pantalla multimedia de 10", tablero digital TFT de 7", cargador inal\u00e1mbrico, 6 airbags',price:'$38.600 (todos los gastos incluidos)',note:'Modelo m\u00e1s reciente (2026). Base imponible e impuestos se pagan en bol\u00edvares a la tasa oficial BCV del d\u00eda.'}
};

function modelCard(k){var m=MODELS[k];if(!m)return'';return'🚗 *'+m.name+'\nSegmento: '+m.segment+'\nMotor: '+m.engine+'\nEquipamiento: '+m.features+'\nPrecio ref.: '+m.price+'\n_'+m.note+'_';}
function waUrl(t){return'https://wa.me/'+WA_NUMBER+'?text='+encodeURIComponent(t||'');}

function createLead(d){
  if(!d.name||!d.phone)return;
  var x=new XMLHttpRequest();
  x.open('POST','/honda-simulador/proxy-odoo.php',true);
  x.setRequestHeader('Content-Type','application/json');
  x.send(JSON.stringify({source:'chatbot',nombre:d.name,telefono:d.phone,email:d.email||'',ciudad:d.city||'',modelo:d.model||d.tdModel||'',consultType:d.consultType||'',mensaje:'Lead generado via chatbot'}));
}

function escapeHtml(t){if(!t)return'';var d=document.createElement('div');d.appendChild(document.createTextNode(t));return d.innerHTML;}

var FLOW = {
  welcome:{message:'¡Hola! Soy el asistente virtual de Honda Mérida. ¿En qué te ayudo hoy?',options:[{text:'🚗 Conocer modelos',next:'chooseModel'},{text:'📅 Agendar test drive',next:'tdStep1'},{text:'💰 Financiamiento y precios',next:'financingMenu'},{text:'🔧 Servicio / postventa',next:'serviceMenu'},{text:'🕐 Horario y ubicación',next:'hoursLocation'},{text:'👤 Hablar con asesor',next:'escalate'}]},
  chooseModel:{message:'¿Cuál de nuestros modelos te interesa?',options:[{text:'City (Sedán)',next:'showCity'},{text:'HR-V (SUV)',next:'showHRV'},{text:'WR-V (SUV compacta)',next:'showWRV'},{text:'Comparar modelos',next:'compareModels'},{text:'🔙 Menú principal',next:'welcome'}]},
  showCity:{message:function(){return modelCard('city')+'\n\n¿Te gustaría que un asesor te contacte con más información?';},options:[{text:'Sí, contáctenme',next:'captureContact',data:{model:'city'}},{text:'Ver HR-V',next:'showHRV'},{text:'Ver WR-V',next:'showWRV'},{text:'🔙 Modelos',next:'chooseModel'},{text:'🔙 Menú principal',next:'welcome'}]},
  showHRV:{message:function(){return modelCard('hrv')+'\n\n¿Te gustaría que un asesor te contacte con más información?';},options:[{text:'Sí, contáctenme',next:'captureContact',data:{model:'hrv'}},{text:'Ver City',next:'showCity'},{text:'Ver WR-V',next:'showWRV'},{text:'🔙 Modelos',next:'chooseModel'},{text:'🔙 Menú principal',next:'welcome'}]},
  showWRV:{message:function(){return modelCard('wrv')+'\n\n¿Te gustaría que un asesor te contacte con más información?';},options:[{text:'Sí, contáctenme',next:'captureContact',data:{model:'wrv'}},{text:'Ver City',next:'showCity'},{text:'Ver HR-V',next:'showHRV'},{text:'🔙 Modelos',next:'chooseModel'},{text:'🔙 Menú principal',next:'welcome'}]},
  compareModels:{message:function(){var c=MODELS.city,h=MODELS.hrv,w=MODELS.wrv;return'Comparativa de modelos:\n\n🏙️ City Sedán\nSegmento: '+c.segment+'\nMotor: '+c.engine+'\nPrecio: '+c.price+'\n\n🏔️ HR-V SUV\nSegmento: '+h.segment+'\nMotor: '+h.engine+'\nPrecio: '+h.price+'\n\n🚙 WR-V SUV compacta (2026)\nSegmento: '+w.segment+'\nMotor: '+w.engine+'\nEquipamiento: '+w.features+'\nPrecio: '+w.price+'\n\n¿Quieres más información de alguno?';},options:[{text:'City',next:'showCity'},{text:'HR-V',next:'showHRV'},{text:'WR-V',next:'showWRV'},{text:'🔙 Menú principal',next:'welcome'}]},
  financingMenu:{message:'💰 Financiamiento y precios\n\nEl precio del vehículo se cotiza en dólares (USD). Los impuestos y la base imponible se cancelan en bolívares a la tasa oficial del BCV del día de la operación.\n\n¿Sobre qué tema te gustaría información?',options:[{text:'Formas de pago',next:'paymentMethods'},{text:'Crédito bancario',next:'bankCredit'},{text:'Apartado / reserva',next:'reserve'},{text:'Garantía DACO',next:'dacoWarranty'},{text:'🔙 Menú principal',next:'welcome'}]},
  paymentMethods:{message:'💰 Formas de pago aceptadas:\n\n• Transferencia bancaria\n• Efectivo en USD\n• Financiamiento bancario\n\n*Precio del vehículo en USD. Impuestos y base imponible se cancelan en bolívares a la tasa oficial BCV del día de la operación.\n\n¿Deseas que un asesor te dé más detalles?',options:[{text:'Sí, contáctenme',next:'captureContact',data:{consultType:'pago'}},{text:'🔙 Financiamiento',next:'financingMenu'},{text:'🔙 Menú principal',next:'welcome'}]},
  bankCredit:{message:'🏦 Crédito bancario:\n\nPodemos conectar contigo con nuestras financieras aliadas. Un asesor financiero te dará la información de tasas y plazos vigentes.\n\n¿Te interesa?',options:[{text:'Sí, quiero info de crédito',next:'captureContact',data:{consultType:'credito'}},{text:'🔙 Financiamiento',next:'financingMenu'},{text:'🔙 Menú principal',next:'welcome'}]},
  reserve:{message:'📋 Proceso de apartado / reserva:\n\nPuedes apartar tu vehículo con un monto a definir con el asesor.\n\n¿Te interesa apartar un vehículo?',options:[{text:'Sí, quiero apartar',next:'captureContact',data:{consultType:'reserva'}},{text:'🔙 Financiamiento',next:'financingMenu'},{text:'🔙 Menú principal',next:'welcome'}]},
  dacoWarranty:{message:'🛡️ Garantía DACO:\n\nLa venta está amparada por el Reglamento de Vehículos de Motor de DACO.\n\nPara consultas específicas sobre garantía o reclamos, un asesor puede atenderte.',options:[{text:'Hablar con asesor',next:'captureContact',data:{consultType:'daco'}},{text:'🔙 Financiamiento',next:'financingMenu'},{text:'🔙 Menú principal',next:'welcome'}]},
  tdStep1:{message:'¡Claro! Agendemos un test drive.\n\n¿Qué modelo te gustaría probar?',options:[{text:'City',next:'tdStep2',data:{tdModel:'city'}},{text:'HR-V',next:'tdStep2',data:{tdModel:'hrv'}},{text:'WR-V',next:'tdStep2',data:{tdModel:'wrv'}},{text:'🔙 Menú principal',next:'welcome'}]},
  tdStep2:{message:'¿En qué ciudad o sede te queda mejor?',options:[{text:'Mérida',next:'tdStep3'},{text:'Otra sede Honda Venezuela',next:'tdStep3'},{text:'🔙 Atrás',next:'tdStep1'}]},
  tdStep3:{message:'¿Qué día y horario prefieres para tu prueba?',options:[{text:'Esta semana en la mañana',next:'tdStep4'},{text:'Esta semana en la tarde',next:'tdStep4'},{text:'La próxima semana',next:'tdStep4'},{text:'🔙 Atrás',next:'tdStep2'}]},
  tdStep4:{message:'Para confirmar tu test drive necesito tus datos (requisito para el seguro del vehículo durante la prueba).\n\nEscribe tu nombre completo:',capture:'name',nextAfterCapture:'tdStep4Phone'},
  tdStep4Phone:{message:'Gracias. Ahora escribe tu número de teléfono (incluyendo código):',capture:'phone',nextAfterCapture:'tdStep5'},
  tdStep5:{message:function(s){return '✅ ¡Listo! Tu test drive del '+(MODELS[s.tdModel||'wrv']?.name||'')+' quedó pre-agendado.\n\nUn asesor te escribirá para confirmar la fecha y hora exacta.\n\n¿Algo más en que pueda ayudarte?';},options:[{text:'Sí, tengo otra consulta',next:'welcome'},{text:'No, gracias',next:'farewell'}],onEnter:function(s){createLead(s);}},
  serviceMenu:{message:'🔧 Servicio y postventa\n\n¿Tu consulta es sobre mantenimiento, garantía o repuestos?',options:[{text:'🛠️ Mantenimiento',next:'serviceMaintenance'},{text:'🛡️ Garantía',next:'serviceWarranty'},{text:'🔩 Repuestos',next:'serviceParts'},{text:'🔙 Menú principal',next:'welcome'}]},
  serviceMaintenance:{message:'Para sugerirte el servicio adecuado, ¿qué modelo tienes y cuántos kilómetros lleva?',capture:'maintenanceInfo',nextAfterCapture:'serviceMaintDate'},
  serviceMaintDate:{message:'¿Qué día te gustaría traer el vehículo al taller?',capture:'preferredDate',nextAfterCapture:'serviceMaintConfirm'},
  serviceMaintConfirm:{message:'✅ Hemos registrado tu solicitud de mantenimiento. El departamento de servicio te contactará para confirmar la cita.',options:[{text:'🔙 Menú principal',next:'welcome'},{text:'Finalizar',next:'farewell'}],onEnter:function(s){createLead(s);}},
  serviceWarranty:{message:'¿Cuándo compraste el vehículo y cuál es el inconveniente?',capture:'warrantyInfo',nextAfterCapture:'serviceWarrantyTransfer'},
  serviceWarrantyTransfer:{message:'Entiendo. Te conectaré con un asesor de servicio que podrá verificar tu garantía y atender tu caso.',options:[{text:'👤 Hablar con asesor',next:'escalate'},{text:'🔙 Menú principal',next:'welcome'}],onEnter:function(s){createLead(s);}},
  serviceParts:{message:'¿Qué pieza o repuesto necesitas? Indica modelo y año.',capture:'partsInfo',nextAfterCapture:'servicePartsTransfer'},
  servicePartsTransfer:{message:'Gracias. Te transferiré al departamento de repuestos para verificar disponibilidad.',options:[{text:'👤 Hablar con repuestos',next:'escalate'},{text:'🔙 Menú principal',next:'welcome'}],onEnter:function(s){createLead(s);}},
  hoursLocation:{message:'🕐 Horario de atención:\n'+HORARIO+'\n\n📍 Dirección:\n'+DIRECCION+'\n\n¿Necesitas algo más?',options:[{text:'📍 Cómo llegar (WhatsApp)',next:'openWAExternal',data:{waMsg:'Hola, quisiera la ubicación del concesionario Honda Mérida'}},{text:'🔙 Menú principal',next:'welcome'}]},
  captureContact:{message:'Para que un asesor te contacte, escribeme tu nombre completo:',capture:'name',nextAfterCapture:'capturePhone'},
  capturePhone:{message:'Gracias. Ahora tu número de teléfono (incluyendo código):',capture:'phone',nextAfterCapture:'captureCity'},
  captureCity:{message:'¿En qué ciudad de Venezuela te encuentras?',capture:'city',nextAfterCapture:'captureDone'},
  captureDone:{message:function(s){return '✅ ¡Gracias '+(s.name||'')+'! Hemos registrado tu información. Un asesor de Honda Mérida te contactará pronto.\n\n¿Hay algo más en que pueda ayudarte?';},options:[{text:'Sí, tengo otra consulta',next:'welcome'},{text:'No, gracias',next:'farewell'}],onEnter:function(s){createLead(s);}},
  escalate:{message:'Te transfiero con un asesor humano. Prefieres:',options:[{text:'💬 Hablar por WhatsApp ahora',next:'openWAExternal',data:{waMsg:'Hola, soy cliente de Honda Mérida y necesito ayuda'}},{text:'📞 Que me llamen',next:'captureContact',data:{consultType:'asesor'}},{text:'🔙 Menú principal',next:'welcome'}]},
  farewell:{message:'¡Gracias por contactar a Honda Mérida! 🚗\n\nSi necesitas algo más, estoy aquí para ayudarte.\n\n¡Que tengas un excelente día!',options:[{text:'🔙 Volver al menú',next:'welcome'}]}
};

function ChatBot(){
  var self={isOpen:false,currentNode:'welcome',capturedData:{name:'',phone:'',email:'',city:'',model:'',tdModel:'',consultType:'',maintenanceInfo:'',preferredDate:'',warrantyInfo:'',partsInfo:''},waitingForInput:false,captureField:null,nextAfterCapture:null,started:false,messages:[]};
  var el=document.getElementById('honda-chatbot');
  if(!el){el=document.createElement('div');el.id='honda-chatbot';document.body.appendChild(el);}
  el.style.cssText='position:fixed;z-index:999999;bottom:20px;left:20px;font-family:Arial,Helvetica,sans-serif;';
  self.el=el;

  function render(){
    var h='';
    if(!self.isOpen){
      h+='<button data-action="toggle" style="width:56px;height:56px;border-radius:50%;background:'+COLORS.primary+';border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(0,0,0,0.25);outline:none;" title="Abrir chat">';
      h+='<svg viewBox="0 0 24 24" style="width:28px;height:28px;fill:white"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg></button>';
    }else{
      h+='<div style="position:absolute;bottom:70px;left:0;width:360px;max-width:calc(100vw - 40px);height:500px;max-height:calc(100vh - 120px);background:'+COLORS.bg+';border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,0.2);display:flex;flex-direction:column;overflow:hidden;animation:hcbSlideUp 0.3s ease">';
      h+='<div style="padding:14px 16px;background:'+COLORS.primary+';color:white;display:flex;justify-content:space-between;align-items:center;flex-shrink:0"><span style="font-weight:bold;font-size:14px;color:white">Honda Mérida</span><button data-action="toggle" style="background:none;border:none;color:white;font-size:18px;cursor:pointer;padding:0 4px;line-height:1;">✕</button></div>';
      h+='<div class="hcb-msgs" style="flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column">';
      if(!self.messages||self.messages.length===0){
        h+='<div style="text-align:center;color:#999;padding:20px">Iniciando chat...</div>';
      }else{
        for(var i=0;i<self.messages.length;i++){
          var msg=self.messages[i];
          var ib=msg.from==='bot';
          h+='<div style="display:flex;flex-direction:column;align-items:'+(ib?'flex-start':'flex-end')+';margin-bottom:8px;width:100%">';
          h+='<div style="max-width:85%;padding:10px 14px;border-radius:'+(ib?'4px 16px 16px 4px':'16px 4px 4px 16px')+';background-color:'+(ib?COLORS.botMsg:COLORS.userMsg)+';color:'+(ib?COLORS.text:'#fff')+';font-size:13px;line-height:1.5;white-space:pre-wrap;word-break:break-word">'+escapeHtml(msg.text)+'</div>';
          if(msg.options&&msg.options.length>0){
            h+='<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:6px;width:100%">';
            for(var j=0;j<msg.options.length;j++){
              var opt=msg.options[j],od=JSON.stringify(opt).replace(/'/g,"&#39;").replace(/"/g,'&quot;');
              h+='<button data-action="option" data-opt=\''+od+'\' style="padding:6px 14px;background:#fff;color:'+COLORS.primary+';border:1.5px solid '+COLORS.primary+';border-radius:16px;cursor:pointer;font-size:12px;font-weight:bold;white-space:nowrap">'+escapeHtml(opt.text)+'</button>';
            }
            h+='</div>';
          }
          h+='</div>';
        }
      }
      if(self.waitingForInput){
        h+='<div style="display:flex;padding:8px 12px;border-top:1px solid '+COLORS.border+';background:'+COLORS.lightBg+'">';
        h+='<input class="hcb-input" type="text" placeholder="Escribe tu respuesta..." style="flex:1;border:1px solid '+COLORS.border+';border-radius:20px;padding:8px 14px;font-size:13px;outline:none" autofocus>';
        h+='<button data-action="send" style="margin-left:8px;background:'+COLORS.primary+';color:white;border:none;border-radius:20px;width:36px;height:36px;cursor:pointer;display:flex;align-items:center;justify-content:center">';
        h+='<svg viewBox="0 0 24 24" style="width:18px;height:18px;fill:white"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>';
        h+='</button></div>';
      }
      h+='</div></div>';
    }
    el.innerHTML=h;
    if(self.isOpen&&self.messages&&self.messages.length>0){
      var msgsEl=el.querySelector('.hcb-msgs');
      if(msgsEl)setTimeout(function(){msgsEl.scrollTop=msgsEl.scrollHeight;},50);
    }
    if(self.waitingForInput)setTimeout(function(){var inp=el.querySelector('.hcb-input');if(inp)inp.focus();},100);
  }

  function addBotMsg(text,opts){
    var t=typeof text==='function'?text(self.capturedData):text;
    self.messages.push({from:'bot',text:t,options:opts||null});
    render();
  }
  function addUserMsg(text){self.messages.push({from:'user',text:text});render();}

  function goTo(nodeId,data){
    if(nodeId==='openWAExternal'){
      var msg=(data&&data._waMsg)||'Hola, soy cliente de Honda Mérida';
      window.open(waUrl(msg),'_blank');
      addBotMsg('✅ WhatsApp abierto. Un asesor te atenderá.\n\n¿Necesitas algo más?',[{text:'🔙 Menú principal',next:'welcome'},{text:'Finalizar',next:'farewell'}]);
      return;
    }
    var node=FLOW[nodeId];
    if(!node){addBotMsg('Opción no disponible. Volviendo al menú principal.');node=FLOW.welcome;nodeId='welcome';}
    var nd=data||self.capturedData;
    if(node.capture){
      self.currentNode=nodeId;self.capturedData=nd;self.waitingForInput=true;self.captureField=node.capture;self.nextAfterCapture=node.nextAfterCapture||'welcome';
      addBotMsg(node.message);return;
    }
    if(node.onEnter)try{node.onEnter(nd);}catch(e){}
    self.currentNode=nodeId;self.capturedData=nd;self.waitingForInput=false;self.captureField=null;self.nextAfterCapture=null;
    addBotMsg(node.message,node.options||null);
  }

  el.addEventListener('click',function(e){
    var btn=e.target.closest('button');
    if(!btn)return;
    var action=btn.getAttribute('data-action');
    if(action==='toggle'){self.isOpen=!self.isOpen;render();if(self.isOpen&&!self.started){self.started=true;self.messages=[];setTimeout(function(){goTo('welcome',{});},300);}}
    else if(action==='option'){
      var optData=btn.getAttribute('data-opt');
      if(!optData)return;
      try{
        var opt=JSON.parse(optData);
        var data=Object.assign({},self.capturedData,opt.data||{});
        if(opt.data&&opt.data.waMsg)data._waMsg=opt.data.waMsg;
        addUserMsg(opt.text);
        setTimeout(function(){goTo(opt.next,data);},300);
      }catch(e){}
    }
    else if(action==='send'){
      var inp=el.querySelector('.hcb-input');
      if(!inp||!inp.value.trim())return;
      var val=inp.value.trim(),field=self.captureField,next=self.nextAfterCapture;
      addUserMsg(val);
      var nd=Object.assign({},self.capturedData);
      nd[field]=val;
      self.capturedData=nd;self.waitingForInput=false;self.captureField=null;self.nextAfterCapture=null;
      setTimeout(function(){goTo(next,nd);},300);
    }
  });

  el.addEventListener('keydown',function(e){
    if(e.key==='Enter'){
      var inp=el.querySelector('.hcb-input');
      if(inp&&inp===document.activeElement){
        e.preventDefault();
        var sendBtn=el.querySelector('[data-action="send"]');
        if(sendBtn)sendBtn.click();
      }
    }
  });

  render();
}

function init(){
  ChatBot();
  if(!document.getElementById('hcb-style')){
    var st=document.createElement('style');
    st.id='hcb-style';
    st.textContent='@keyframes hcbSlideUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}';
    document.head.appendChild(st);
  }
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);
else init();

})();