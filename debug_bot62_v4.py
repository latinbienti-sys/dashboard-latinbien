import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

code62 = """try:
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
    clear_bot = False
    
    send('DEBUG: Recibido: \"' + texto + '\"')
    
    if texto == '6':
        send('Escribe 6 seguido del nombre del producto, ej: 6 televisor')
    elif texto == '1':
        send('Excelente decision! Registrate y solicita tu Linea de Credito:\\n\\nhttps://latinbien.com/registro')
    elif texto == '2':
        send('Nuestro catalogo online se actualiza constantemente!\\n\\nExplora nuestros productos: https://latinbien.com/shop')
    elif texto == '3':
        send('Compra de contado en nuestro catalogo online:\\n\\nhttps://latinbien.com/shop')
    elif texto == '4':
        send('Perfecto! Te transfiero con un asesor.')
        clear_bot = True
    elif texto == '5':
        send('Perfecto! Te transfiero con un asesor.')
        clear_bot = True
    elif len(texto) > 2 and texto[0:1] == '6' and texto[1:2] == ' ':
        query = texto[2:].strip()
        if query:
            send('Buscando: ' + query)
        else:
            send('Escribe 6 seguido del nombre del producto, ej: 6 nevera')
    elif texto:
        texto_u = texto.upper().replace(' ', '')
        send('DEBUG: texto_u=\"' + texto_u + '\"')
        
        if texto_u.startswith('V') or texto_u.startswith('E'):
            digit_part = texto_u[1:]
            parece_cedula = digit_part.isdigit() and len(digit_part) >= 5
        else:
            parece_cedula = texto_u.isdigit() and len(texto_u) >= 5
        
        send('DEBUG: parece_cedula=' + str(parece_cedula))
        
        if not parece_cedula:
            send('Disculpa, no entendi tu solicitud. Por favor escribe tu numero de cedula.')
        else:
            cedula = texto_u
            if cedula.startswith('V') or cedula.startswith('E'):
                cedula = cedula[1:]
            cedula_v = 'V' + cedula
            send('DEBUG: Buscando vat=\"' + cedula_v + '\" o \"' + cedula + '\"')
            
            partner = env['res.partner'].search([('vat', '=', cedula_v)], limit=1)
            if not partner:
                partner = env['res.partner'].search([('vat', '=', cedula)], limit=1)
            
            if partner:
                p = partner[0]
                send('DEBUG: Partner=' + str(p.name) + ' ID=' + str(p.id))
                
                linea_activa = False
                try: linea_activa = bool(p.x_activacion_linea)
                except: send('DEBUG: No x_activacion_linea')
                
                tiene_ventas = False
                try: tiene_ventas = bool(p.sale_order_count and p.sale_order_count > 0)
                except: send('DEBUG: No sale_order_count')
                
                monto_disp = 0
                try: monto_disp = p.x_credit_limit_available or 0
                except:
                    try: monto_disp = (p.x_credit_limit_aprobado or 0) - (p.x_credit_limit_use or 0)
                    except: send('DEBUG: No credit fields')
                
                send('DEBUG: linea_activa=' + str(linea_activa) + ' ventas=' + str(tiene_ventas))
                
                if linea_activa and tiene_ventas:
                    send('DEBUG: -> RECOMPRA')
                    goto_bot = Bot.search([('name', 'ilike', '%MENU_RECOMPRA%')], limit=1)
                    send('Bienvenido ' + str(p.name) + '! Menu de Recompra')
                elif linea_activa and not tiene_ventas:
                    send('DEBUG: -> LC_APROBADA')
                    goto_bot = Bot.search([('name', 'ilike', '%MENU_LC_APROBADA%')], limit=1)
                    send('Bienvenido ' + str(p.name) + '! Menu LC Aprobada')
                else:
                    send('DEBUG: -> REGISTRADO')
                    goto_bot = Bot.search([('name', 'ilike', '%MENU_REGISTRADO%')], limit=1)
                    send('Bienvenido ' + str(p.name) + '! Menu Registrado')
                
                send('DEBUG: goto_bot=' + str(goto_bot.id if goto_bot else 'NONE'))
            else:
                send('DEBUG: Partner NO encontrado')
                send('No encontre tu cedula. Eres nuevo?')
    else:
        send('Texto vacio')
    
    if clear_bot:
        conv.write({'active_bot_id': False})
    
    if goto_bot:
        send('DEBUG: Navegando a bot ' + str(goto_bot.id))
        conv.write({'active_bot_id': goto_bot.id})
        ret = goto_bot
    else:
        ret = env['acrux.chat.bot']
except Exception as e:
    try:
        conv = mess_id.conversation_id
        m = {'ttype': 'text', 'from_me': True, 'contact_id': conv.id, 'text': 'ERROR: ' + str(e)[:300]}
        try:
            conv.send_message_bus_release(m, 'current', False)
        except:
            conv.send_message_bus_release(m, 'done')
    except:
        pass
    ret = env['acrux.chat.bot']"""

try:
    compile(code62, '<string>', 'exec')
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'write',
            'args': [[62], {'code': code62}], 'kwargs': {}
        }
    })
    if resp.json().get('result'):
        print("✅ Bot 62: DEBUG v2 instalada")
    else:
        print("❌ Error al escribir")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
