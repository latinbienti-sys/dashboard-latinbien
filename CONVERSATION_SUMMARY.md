# Summary

## Objective
- En el conector comercial (connector 2), campaña **CrédiMoto** como **pregunta proactiva**: tras el 1er mensaje del cliente, el bot pregunta "¿Deseas información sobre las motos de Latinbien?". 
  - Si responde **SÍ** → activa el menú de opciones de moto (1-5).
  - Si responde **NO** (o salir/volver/comercial) → **NO** pide validar cédula; en su lugar avisa al cliente "pronto será atendido por nuestros asesores" y **envía un WhatsApp al asesor al número 424-7035927** (= `584247035927` con código VE) usando el patrón probado de los bots de asesoría.

## Important Details
- Autenticación Odoo: `https://latinbien.com/web/session/authenticate`, db=`erp_production`, login=`latinbienti@latinbien.com`, password=`z+cakaSe2805*`. API=`https://latinbien.com/web/dataset/call_kw`, modelo=`acrux.chat.bot`.
- Árbol moto (3 bots, hijos del catcher raíz 61):
  - **130** `#MOTO_CATCHER_61` (hijo 61, catch-all seq1, hijos=[131]): envía la pregunta y `goto_and_wait '#MOTO_MENU'`. Texto actual: "🏍️ ¿Deseas información sobre las motos de Latinbien? Responde SÍ para ver las opciones o NO para la atención comercial habitual." (sin "CrédiMoto").
  - **131** `#MOTO_MENU` (hijo 130, contenedor, hijos=[134]).
  - **134** `#MOTO_BRANCH` (hijo 131, catch-all): handler. 
    - `salir`/`volver`/`comercial`/`no`/`nada`/`nop`/`ningun` → función `_salir()`: notifica al asesor vía `env['acrux.chat.conversation']` (search/create del número `584247035927`) + `send_message_bus_release(...)` (mismo patrón que bots 97-100 `RECOMPRA_ASESOR`/`LC_ASESOR`/`REG_ASESOR`/`NR_ASESOR`), y responde al cliente "🤝 Pronto serás atendido por uno de nuestros asesores. Te contactaremos a la brevedad." (NO `goto #VALIDAR_CEDULA`).
    - `menu` o afirmativo → muestra menú de opciones (1 Requisitos, 2 Catálogo, 3 Seguimiento, 4 Entrega, 5 Ubicación).
    - Rama por número (1-5) o palabra → responde esa rama + `goto_and_wait '#MOTO_MENU'` (permanece en modo moto).
- Patrón de envío a número externo (confirmado en bots asesor 84/97-100): `Conv.search([('connector_id','=',2),('number','=',num)]); si no existe Conv.conversation_create(...); msg={'ttype':'text','from_me':True,'contact_id':conv.id,'text':...}; conv.send_message_bus_release(msg, status)`. El número del asesor debe incluir código de país: `424-7035927` → `584247035927`.
- El 1er mensaje del cliente lo maneja el bot raíz 61; la pregunta de moto aparece en el **2º mensaje** (limitación del motor: los hijos del root se evalúan desde el 2º mensaje).
- Se ELIMINARON los bots 126-129 (campaña vieja por keyword en menús). Bot 130 reutilizado de intento anterior.

## Work State
### Completed
- Pregunta sin "CrédiMoto": "¿Deseas información sobre las motos de Latinbien?".
- Rama NO → avisa al cliente y notifica por WhatsApp al asesor `584247035927` (usa `send_message_bus_release`, patrón validado en bots de asesoría existentes). Sin validación de cédula.
- Código verificado en Odoo (130 y 134) y ejecutado localmente con mocks: la rama NO corre el notify y devuelve 1 acción (mensaje al cliente) sin errores; SÍ/menú/ramas funcionan.
- Simulación/prueba local OK. Pendiente prueba en caliente real (WhatsApp).

### Active
- (none)

### Blocked
- (none)

## Next Move
1. **Prueba en caliente (WhatsApp real)**: escribir al comercial; en el 2º mensaje debe aparecer la pregunta. Responder NO → verificar que el cliente recibe "pronto será atendido por nuestros asesores" y que el número 424-7035927 recibe el aviso del bot (esto resuelve el "y no ocurre nada" previo).
2. Detalle opcional: el header del menú y los textos de rama aún contienen "CrédiMoto" (nombre del producto). El usuario pidió quitarlo solo de la pregunta; si quiere quitarlo también del menú/ramas, se ajusta `resp_menu`/`resp_*`.
3. Opcional: hacer que la pregunta aparezca en el 1er mensaje (editando el `code` del bot raíz 61) o que no interrumpa si el cliente manda su cédula como 2º mensaje (detección de cédula en bot 130).

## Relevant Files
- `C:\Users\yarleyc\Documents\New OpenCode Project\add_moto_question.py`: crea/reutiliza el árbol proactivo (130/131/134) con la rama NO → aviso a asesor 584247035927; idempotente. Ya ejecutado.
- `C:\Users\yarleyc\Documents\New OpenCode Project\add_moto_campaign.py` / `add_moto_root.py`: intentos anteriores (no usados).
- `C:\Users\yarleyc\Documents\New OpenCode Project\Bot_source.py`: fuente de `acrux.chat.bot` (acciones `send_text`/`goto_and_wait`/`next`/`create`/`send`; `env` disponible en eval context).
- `C:\Users\yarleyc\Documents\New OpenCode Project\CONVERSATION_SUMMARY.md`: este resumen.
