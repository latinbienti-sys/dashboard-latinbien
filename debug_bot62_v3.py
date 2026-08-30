import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Simple debug version - just echoes what it receives
code62_debug = """try:
    texto = (mess_id.text or '').strip()
    conv = mess_id.conversation_id
    Bot = env['acrux.chat.bot']
    
    def send(txt):
        m = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': txt}
        try:
            conv.send_message_bus_release(m, 'current', False)
        except:
            try:
                conv.send_message_bus_release(m, 'done')
            except:
                pass
    
    goto_bot = False
    
    # Primero siempre enviar un debug
    send('DEBUG: Recibido: "' + texto + '" (' + str(len(texto)) + ' chars)')
    
    if texto == '6':
        send('Opcion 6: buscar producto')
    elif texto == '1':
        send('Opcion 1: registrarme')
    elif texto == '2':
        send('Opcion 2: ver catalogo')
    elif texto == '3':
        send('Opcion 3: compra contado')
    elif texto == '4':
        send('Opcion 4: reportar problema')
        conv.write({'active_bot_id': False})
    elif texto == '5':
        send('Opcion 5: hablar con asesor')
        conv.write({'active_bot_id': False})
    elif len(texto) > 2 and texto[0:1] == '6' and texto[1:2] == ' ':
        send('Busqueda: ' + texto[2:].strip())
    elif texto:
        texto_u = texto.upper().replace(' ', '')
        send('DEBUG: texto_u="' + texto_u + '"')
        if texto_u.startswith('V') or texto_u.startswith('E'):
            digit_part = texto_u[1:]
            parece_cedula = digit_part.isdigit() and len(digit_part) >= 5
            send('DEBUG: Empieza con V/E, digit_part="' + digit_part + '", isdigit=' + str(digit_part.isdigit()) + ', len=' + str(len(digit_part)))
        else:
            parece_cedula = texto_u.isdigit() and len(texto_u) >= 5
            send('DEBUG: No empieza con V/E, isdigit=' + str(texto_u.isdigit()) + ', len=' + str(len(texto_u)))
        
        send('DEBUG: parece_cedula=' + str(parece_cedula))
        
        if not parece_cedula:
            send('Disculpa, no entendi tu solicitud.')
        else:
            cedula = texto_u
            if cedula.startswith('V') or cedula.startswith('E'):
                cedula = cedula[1:]
            cedula_v = 'V' + cedula
            send('DEBUG: Buscando partner con vat="' + cedula_v + '" o "' + cedula + '"')
            
            partner = env['res.partner'].search([('vat', '=', cedula_v)], limit=1)
            if not partner:
                partner = env['res.partner'].search([('vat', '=', cedula)], limit=1)
            
            if partner:
                p = partner[0]
                send('DEBUG: Partner encontrado: ' + str(p.name) + ' (ID=' + str(p.id) + ')')
                
                linea_activa = False
                try: linea_activa = bool(p.x_activacion_linea)
                except: send('DEBUG: Error leyendo x_activacion_linea')
                
                tiene_ventas = False
                try: tiene_ventas = bool(p.sale_order_count and p.sale_order_count > 0)
                except: send('DEBUG: Error leyendo sale_order_count')
                
                monto_disp = 0
                try: monto_disp = p.x_credit_limit_available or 0
                except:
                    try: monto_disp = (p.x_credit_limit_aprobado or 0) - (p.x_credit_limit_use or 0)
                    except: send('DEBUG: Error leyendo credit limits')
                
                send('DEBUG: linea_activa=' + str(linea_activa) + ' tiene_ventas=' + str(tiene_ventas) + ' monto_disp=' + str(monto_disp))
                
                if linea_activa and tiene_ventas:
                    send('DEBUG: CASO RECOMPRA')
                    msg = 'Hola ' + str(p.name) + '! Menu Recompra'
                    send(msg)
                    goto_bot = Bot.search([('name', 'ilike', '%MENU_RECOMPRA%')], limit=1)
                elif linea_activa and not tiene_ventas:
                    send('DEBUG: CASO LC APROBADA')
                    msg = 'Hola ' + str(p.name) + '! Menu LC Aprobada'
                    send(msg)
                    goto_bot = Bot.search([('name', 'ilike', '%MENU_LC_APROBADA%')], limit=1)
                else:
                    send('DEBUG: CASO REGISTRADO')
                    msg = 'Hola ' + str(p.name) + '! Menu Registrado'
                    send(msg)
                    goto_bot = Bot.search([('name', 'ilike', '%MENU_REGISTRADO%')], limit=1)
                
                send('DEBUG: goto_bot encontrado=' + str(bool(goto_bot)) + ' ID=' + str(goto_bot.id if goto_bot else 'N/A'))
                if goto_bot:
                    conv.write({'active_bot_id': goto_bot.id})
                    ret = goto_bot
                else:
                    ret = env['acrux.chat.bot']
            else:
                send('DEBUG: Partner NO encontrado')
                send('No encontre tu cedula. Eres nuevo?')
                ret = env['acrux.chat.bot']
    else:
        send('Texto vacio')
        ret = env['acrux.chat.bot']
    
    # Default ret if not set in branches above
    try:
        ret
    except NameError:
        ret = env['acrux.chat.bot']
    
    if goto_bot:
        conv.write({'active_bot_id': goto_bot.id})
        ret = goto_bot
    
except Exception as e:
    try:
        conv = mess_id.conversation_id
        send('ERROR: ' + str(e)[:200])
    except:
        pass
    ret = env['acrux.chat.bot']"""

try:
    compile(code62_debug, '<string>', 'exec')
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[62], {'code': code62_debug}], 'kwargs': {}
        }
    })
    if resp.json().get('result'):
        print("✅ Bot 62: version DEBUG instalada")
    else:
        print("❌ Error al escribir")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
