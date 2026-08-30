# Honda Mérida - Chatbot Odoo v16 con ACRX Connector

## Configuración del Chatbot en Odoo 16

### Ruta de acceso
`Live Chat > Configuration > Chatbots > New`

---

## ESTRUCTURA DEL CHATBOT

### Nombre del Chatbot
`Honda Mérida - Asesor Virtual`

### Imagen del Bot
(Logo de Honda Mérida)

---

## SCRIPT - NODOS DEL CHATBOT

### NODO 0: BIENVENIDA
| Campo | Valor |
|-------|-------|
| **Step Type** | Text |
| **Message** | 🚗 *¡Bienvenido a Honda Mérida!* ✨<br>Tu próximo Honda está aquí. Soy tu asesor virtual y estoy listo para ayudarte a estrenar.<br><br>Por favor, selecciona una de las siguientes opciones escribiendo el *NÚMERO*:<br><br>1️⃣ *Modelos Nuevos 2026* (Civic, CR-V, HR-V, City, BR-V)<br>2️⃣ *Solicitar Cotización y Planes de Financiamiento* 📊<br>3️⃣ *Agendar una Prueba de Manejo* 🏁<br>4️⃣ *Autos Seminuevos Garantizados* 🚗<br>5️⃣ *Agendar Cita de Servicio / Taller* 🔧<br>6️⃣ *Hablar con un Asesor Humano* 🧑‍💼<br><br>_Escribe solo el número de la opción que deseas y te daré la información de inmediato._ |

---

### NODO 1: MENÚ PRINCIPAL
| Campo | Valor |
|-------|-------|
| **Step Type** | Question |
| **Message** | ¿Qué opción te gustaría? (1-6) |

#### Respuestas y Nodos Hijos:

| Respuesta | Step Type | Message | Nodo Hijo |
|-----------|-----------|---------|-----------|
| `1` | Text | ¡Excelente! Te muestro nuestros modelos nuevos 2026 🚗 | → Nodo 1.1 |
| `2` | Text | ¡Perfecto! Te ayudo con cotización y financiamiento 📊 | → Nodo 2.1 |
| `3` | Text | ¡Genial! Agendemos tu prueba de manejo 🏁 | → Nodo 3.1 |
| `4` | Text | ¡Tenemos excelentes opciones seminuevas! 🚗 | → Nodo 4.1 |
| `5` | Text | ¡Agendemos tu cita de servicio! 🔧 | → Nodo 5.1 |
| `6` | Text | ¡Te conectaré con un asesor humano! 🧑‍💼 | → Nodo 6.1 |

---

## NODOS HIJOS - DETALLE

### NODO 1.1: MODELOS NUEVOS 2026
| Campo | Valor |
|-------|-------|
| **Step Type** | Question |
| **Message** | ¿Qué modelo te interesa?<br><br>🅰️ **Civic** - Sedán deportivo y elegante<br>🅱️ **CR-V** - SUV familiar completa<br>🅲 **HR-V** - SUV compacto versátil<br>🅳 **City** - Sedán compacto eficiente<br>🅴 **BR-V** - SUV 7 pasajeros<br><br>Escribe la letra del modelo |

#### Respuestas:

| Respuesta | Step Type | Message |
|-----------|-----------|---------|
| `A` o `a` | Text | ¡El Civic es una excelente elección! 🚗 Es un sedán deportivo con tecnología avanzada. |
| `B` o `b` | Text | ¡La CR-V es perfecta para familias! 🚗 SUV completa y espaciosa. |
| `C` o `c` | Text | ¡El HR-V es ideal para la ciudad! 🚗 SUV compacto y versátil. |
| `D` o `d` | Text | ¡El City es eficiente y elegante! 🚗 Sedán compacto perfecto. |
| `E` o `e` | Text | ¡El BR-V es perfecto para 7 pasajeros! 🚗 SUV familiar completa. |

#### Continuación después de selección:

| Campo | Valor |
|-------|-------|
| **Step Type** | Question |
| **Message** | ¿Buscas financiamiento o pago de contado?<br><br>1️⃣ Financiamiento<br>2️⃣ Pago de contado |

#### Respuestas:

| Respuesta | Step Type | Message |
|-----------|-----------|---------|
| `1` | Text | ¡Perfecto! Tenemos planes de financiamiento desde el 10% de enganche 📊 |
| `2` | Text | ¡Excelente! El pago de contado incluye descuento especial 💰 |

#### Continuación (recopilación de datos):

| Campo | Valor |
|-------|-------|
| **Step Type** | Email |
| **Message** | Para que un asesor especializado te contacte, necesito tu correo electrónico: |

| Campo | Valor |
|-------|-------|
| **Step Type** | Free Input |
| **Message** | ¿Cuál es tu nombre completo? |

| Campo | Valor |
|-------|-------|
| **Step Type** | Free Input |
| **Message** | ¿Tu número de teléfono? |

| Campo | Valor |
|-------|-------|
| **Step Type** | Text |
| **Message** | ¡Listo! ✅ Un asesor de Honda Mérida te contactará pronto con la cotización de tu **[modelo seleccionado]**. ¡Gracias por tu preferencia! 🚗✨ |

---

### NODO 2.1: COTIZACIÓN Y FINANCIAMIENTO
| Campo | Valor |
|-------|-------|
| **Step Type** | Question |
| **Message** | ¿Qué modelo te interesa cotizar?<br><br>1️⃣ Civic<br>2️⃣ CR-V<br>3️⃣ HR-V<br>4️⃣ City<br>5️⃣ BR-V<br>6️⃣ No sé, necesito orientación |

#### Respuestas:

| Respuesta | Step Type | Message |
|-----------|-----------|---------|
| `1-5` | Text | ¡Excelente elección! Te prepararé una cotización personalizada 📊 |
| `6` | Text | ¡Sin problema! Te ayudo a elegir el modelo perfecto para ti ✨ |

#### Continuación:

| Campo | Valor |
|-------|-------|
| **Step Type** | Question |
| **Message** | ¿Qué tipo de compra prefieres?<br><br>1️⃣ Crédito directo (12-60 meses)<br>2️⃣ Contado con descuento<br>3️⃣ Leasing<br>4️⃣ PARTIPAGO |

| Campo | Valor |
|-------|-------|
| **Step Type** | Question |
| **Message** | ¿Qué enganche tienes disponible?<br><br>1️⃣ Desde 10%<br>2️⃣ Desde 20%<br>3️⃣ Desde 30% o más |

#### Recopilación de datos:

| Campo | Valor |
|-------|-------|
| **Step Type** | Email |
| **Message** | Para preparar tu cotización, necesito tu correo electrónico: |

| Campo | Valor |
|-------|-------|
| **Step Type** | Free Input |
| **Message** | ¿Tu nombre completo? |

| Campo | Valor |
|-------|-------|
| **Step Type** | Free Input |
| **Message** | ¿Tu número de teléfono? |

| Campo | Valor |
|-------|-------|
| **Step Type** | Text |
| **Message** | ¡Perfecto! 📊 Un asesor financiero de Honda Mérida te contactará con una cotización personalizada. ¡Gracias! |

---

### NODO 3.1: PRUEBA DE MANEJO
| Campo | Valor |
|-------|-------|
| **Step Type** | Question |
| **Message** | ¿Qué modelo te gustaría probar?<br><br>1️⃣ Civic 2026<br>2️⃣ CR-V 2026<br>3️⃣ HR-V 2026<br>4️⃣ City 2026<br>5️⃣ BR-V 2026 |

#### Continuación:

| Campo | Valor |
|-------|-------|
| **Step Type** | Question |
| **Message** | ¿Qué día te viene bien?<br><br>1️⃣ Lunes a Viernes<br>2️⃣ Sábado<br>3️⃣ Domingo |

| Campo | Valor |
|-------|-------|
| **Step Type** | Question |
| **Message** | ¿Qué horario prefieres?<br><br>1️⃣ Mañana (9am - 1pm)<br>2️⃣ Tarde (3pm - 7pm) |

#### Recopilación de datos:

| Campo | Valor |
|-------|-------|
| **Step Type** | Email |
| **Message** | Para agendar tu prueba, necesito tu correo electrónico: |

| Campo | Valor |
|-------|-------|
| **Step Type** | Free Input |
| **Message** | ¿Tu nombre completo? |

| Campo | Valor |
|-------|-------|
| **Step Type** | Free Input |
| **Message** | ¿Tu número de teléfono? |

| Campo | Valor |
|-------|-------|
| **Step Type** | Text |
| **Message** | ¡Genial! 🏁 Tu prueba de manejo ha sido registrada. Nuestro equipo te confirmará la cita por correo o teléfono. ¡Esperamos verte pronto! 🚗 |

---

### NODO 4.1: AUTOS SEMINUEVOS
| Campo | Valor |
|-------|-------|
| **Step Type** | Question |
| **Message** | ¿Qué tipo de vehículo buscas?<br><br>1️⃣ Sedán<br>2️⃣ SUV<br>3️⃣ Familiar<br>4️⃣ No sé, necesito ver opciones |

#### Continuación:

| Campo | Valor |
|-------|-------|
| **Step Type** | Question |
| **Message** | ¿Tienes un presupuesto en mente?<br><br>1️⃣ Menos de $200,000<br>2️⃣ $200,000 - $350,000<br>3️⃣ $350,000 - $500,000<br>4️⃣ Más de $500,000 |

| Campo | Valor |
|-------|-------|
| **Step Type** | Question |
| **Message** | ¿Buscas financiamiento o pago de contado?<br><br>1️⃣ Financiamiento<br>2️⃣ Contado |

#### Recopilación de datos:

| Campo | Valor |
|-------|-------|
| **Step Type** | Email |
| **Message** | Para mostrarte el inventario disponible, necesito tu correo electrónico: |

| Campo | Valor |
|-------|-------|
| **Step Type** | Free Input |
| **Message** | ¿Tu nombre completo? |

| Campo | Valor |
|-------|-------|
| **Step Type** | Free Input |
| **Message** | ¿Tu número de teléfono? |

| Campo | Valor |
|-------|-------|
| **Step Type** | Text |
| **Message** | ¡Excelente! 🚗 Un asesor te mostrará las opciones seminuevas que se ajustan a tus necesidades. ¡Gracias! |

---

### NODO 5.1: CITA DE SERVICIO / TALLER
| Campo | Valor |
|-------|-------|
| **Step Type** | Question |
| **Message** | ¿Qué servicio necesitas?<br><br>1️⃣ Mantenimiento preventivo<br>2️⃣ Servicio de aceite y filtros<br>3️⃣ Alineación y balanceo<br>4️⃣ Diagnóstico computarizado<br>5️⃣ Reparación de motor/transmisión<br>6️⃣ Servicio de frenos<br>7️⃣ Otro servicio |

#### Continuación:

| Campo | Valor |
|-------|-------|
| **Step Type** | Question |
| **Message** | ¿Qué día te viene bien?<br><br>1️⃣ Lunes a Viernes<br>2️⃣ Sábado |

| Campo | Valor |
|-------|-------|
| **Step Type** | Question |
| **Message** | ¿Qué horario prefieres?<br><br>1️⃣ Mañana (8am - 1pm)<br>2️⃣ Tarde (2pm - 6pm) |

#### Recopilación de datos:

| Campo | Valor |
|-------|-------|
| **Step Type** | Free Input |
| **Message** | ¿Qué modelo y año es tu Honda? (ej: CR-V 2022) |

| Campo | Valor |
|-------|-------|
| **Step Type** | Email |
| **Message** | Para confirmar tu cita, necesito tu correo electrónico: |

| Campo | Valor |
|-------|-------|
| **Step Type** | Free Input |
| **Message** | ¿Tu nombre completo? |

| Campo | Valor |
|-------|-------|
| **Step Type** | Free Input |
| **Message** | ¿Tu número de teléfono? |

| Campo | Valor |
|-------|-------|
| **Step Type** | Text |
| **Message** | ¡Perfecto! 🔧 Tu cita de servicio ha sido registrada. Recibirás confirmación por correo o teléfono. ¡Gracias! |

---

### NODO 6.1: ASESOR HUMANO
| Campo | Valor |
|-------|-------|
| **Step Type** | Question |
| **Message** | ¿Cuál es el motivo de tu consulta?<br><br>1️⃣ Compra de auto nuevo<br>2️⃣ Compra de auto seminuevo<br>3️⃣ Cotización/Financiamiento<br>4️⃣ Prueba de manejo<br>5️⃣ Servicio/Taller<br>6️⃣ Otro |

#### Recopilación de datos:

| Campo | Valor |
|-------|-------|
| **Step Type** | Email |
| **Message** | Para conectarte con un asesor, necesito tu correo electrónico: |

| Campo | Valor |
|-------|-------|
| **Step Type** | Free Input |
| **Message** | ¿Tu nombre completo? |

| Campo | Valor |
|-------|-------|
| **Step Type** | Free Input |
| **Message** | ¿Tu número de teléfono? |

#### Conexión con operador:

| Campo | Valor |
|-------|-------|
| **Step Type** | Forward to Operator |
| **Message** | Conectando con un asesor humano... |

| Campo | Valor |
|-------|-------|
| **Step Type** | Text |
| **Message** | (Si no hay operador disponible) Lo sentimos, no hay asesores disponibles en este momento. Un asesor te contactará pronto con los datos que nos proporcionaste. ¡Gracias! 🧑‍💼 |

---

## CONFIGURACIÓN DEL CANAL DE LIVE CHAT

### Ruta de acceso
`Live Chat > Configuration > Channels > New`

| Campo | Valor |
|-------|-------|
| **Channel Name** | Honda Mérida - Chatbot |
| **Chatbot** | Honda Mérida - Asesor Virtual |
| **Live Chat Button** | Open Automatically |
| **Enabled only if no operator** | ✅ (Activar) |

### Channel Rules (URL Regex):

| URL Regex | Acción |
|-----------|--------|
| `.*` | Mostrar chatbot en todas las páginas |
| `/honda.*` | Páginas de Honda |
| `/modelos.*` | Páginas de modelos |
| `/cotizacion.*` | Página de cotización |

---

## CONFIGURACIÓN ACRX CONNECTOR (WhatsApp)

### Ruta de acceso
`Settings > ChatRoom > Connectors`

### Pasos de configuración:

1. **Instalar módulo**: `whatsapp_connector` de AcruxLab
2. **Ir a**: `Settings > ChatRoom > Connectors`
3. **Seleccionar**: WhatsApp
4. **Clic en**: "Init Free Test"
5. **Escanear**: Código QR con WhatsApp
6. **Configurar Webhook**:
   - Callback URL: `https://tu-odoo.com/whatsapp/webhook`
   - Verify Token: `(generar token)`
7. **Vincular canal**: Conectar el canal de Live Chat con WhatsApp

### Configuración del chatbot en WhatsApp:

| Campo | Valor |
|-------|-------|
| **Canal** | Honda Mérida - WhatsApp |
| **Chatbot** | Honda Mérida - Asesor Virtual |
| **Activar** | ✅ |

---

## MODELOS DE PLANTILLAS (Opcional)

Si deseas usar plantillas de WhatsApp aprobadas por Meta:

### Plantilla 1: Bienvenida
```
Nombre: honda_bienvenida
Idioma: es
Categoría: MARKETING

Mensaje:
🚗 *¡Bienvenido a Honda Mérida!* ✨
Tu próximo Honda está aquí.

Selecciona una opción:
1️⃣ Modelos Nuevos 2026
2️⃣ Cotización y Financiamiento
3️⃣ Prueba de Manejo
4️⃣ Autos Seminuevos
5️⃣ Cita de Servicio
6️⃣ Asesor Humano
```

### Plantilla 2: Confirmación
```
Nombre: honda_confirmacion
Idioma: es
Categoría: UTILITY

Mensaje:
✅ *¡Gracias por contactarnos!*

Tu solicitud ha sido registrada:
👤 Nombre: {{nombre}}
📧 Correo: {{correo}}
📞 Teléfono: {{telefono}}

Un asesor de Honda Mérida te contactará pronto. 🚗
```

---

## RESUMEN DE NODOS

| Nodo | Tipo | Descripción |
|------|------|-------------|
| 0 | Text | Bienvenida |
| 1 | Question | Menú principal (1-6) |
| 1.1 | Question | Modelos nuevos + Recopilación datos |
| 2.1 | Question | Cotización + Recopilación datos |
| 3.1 | Question | Prueba de manejo + Recopilación datos |
| 4.1 | Question | Seminuevos + Recopilación datos |
| 5.1 | Question | Servicio/Taller + Recopilación datos |
| 6.1 | Question | Asesor humano + Forward to Operator |

---

## VERIFICACIÓN

Para probar el chatbot en Odoo 16:
1. Ir a `Live Chat > Configuration > Chatbots`
2. Seleccionar "Honda Mérida - Asesor Virtual"
3. Clic en **TEST**
4. Seguir el flujo del menú

---

*Documento generado para Honda Mérida - Odoo v16 con ACRX Connector*