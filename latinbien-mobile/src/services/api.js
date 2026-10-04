// ============================================================
// LatinBien Mobile — API Service (Odoo 16 JSON-RPC)
// Usa XMLHttpRequest con withCredentials=true para que OkHttp
// maneje las cookies automáticamente (como un navegador)
// ============================================================

import { BASE_URL } from '../utils/constants';

let _partnerId = null;

/**
 * Normaliza la respuesta de search_read a un ARRAY siempre.
 * Odoo puede devolver: [ {...}, {...} ]  ó  { records: [...], length: N }
 * Sin esta normalización, `productos.slice()` reventaba (pantalla blanca).
 */
function asArray(result) {
  if (result == null) return [];
  if (Array.isArray(result)) return result;
  if (Array.isArray(result.records)) return result.records;
  if (Array.isArray(result.data)) return result.data;
  return [];
}

export function setPartnerId(id) {
  _partnerId = id;
}

/**
 * Llamada JSON-RPC — withCredentials=true para cookies automáticas
 */
function jsonRpc(endpoint, params = {}) {
  return new Promise((resolve, reject) => {
    const url = `${BASE_URL}${endpoint}`;
    const body = JSON.stringify({ jsonrpc: '2.0', method: 'call', params, id: Date.now() });

    const xhr = new XMLHttpRequest();
    xhr.open('POST', url, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.withCredentials = true; // OkHttp maneja cookies automáticamente

    xhr.onreadystatechange = function () {
      if (xhr.readyState !== 4) return;

      if (xhr.status < 200 || xhr.status >= 300) {
        reject(new Error(`Error de conexión (${xhr.status})`));
        return;
      }

      try {
        const data = JSON.parse(xhr.responseText);
        if (data.error) {
          const msg = data.error.data?.message || data.error.message || 'Error del servidor';
          reject(new Error(msg.replace(/^Odoo Server Error\s*/i, '').trim()));
        } else {
          resolve(data.result);
        }
      } catch (e) {
        reject(new Error('Respuesta inválida del servidor'));
      }
    };

    xhr.onerror = () => reject(new Error('Error de red'));
    xhr.send(body);
  });
}

// ============================================================
// AUTH
// ============================================================

export function getSessionInfo() {
  return jsonRpc('/web/session/get_session_info');
}

export function login(login, password) {
  return jsonRpc('/web/session/authenticate', {
    db: 'erp_production',
    login,
    password,
  });
}

export function logout() {
  return jsonRpc('/web/session/destroy');
}

// ============================================================
// CATÁLOGO
// ============================================================

export function getFeaturedProducts(limit = 20) {
  return jsonRpc('/web/dataset/search_read', {
    model: 'product.template',
    domain: [['sale_ok', '=', true]],
    fields: ['id', 'name', 'list_price', 'default_code', 'image_256', 'website_url', 'categ_id'],
    limit,
    order: 'write_date desc',
  }).then(asArray);
}

export function searchProducts(query, limit = 20) {
  return jsonRpc('/web/dataset/search_read', {
    model: 'product.template',
    domain: [
      ['sale_ok', '=', true],
      '|',
      ['name', 'ilike', query],
      ['default_code', 'ilike', query],
    ],
    fields: ['id', 'name', 'list_price', 'default_code', 'image_256', 'website_url', 'categ_id'],
    limit,
  }).then(asArray);
}

export function getCategories() {
  return jsonRpc('/web/dataset/search_read', {
    model: 'product.public.category',
    domain: [],
    fields: ['id', 'name'],
    order: 'sequence asc',
  }).then(asArray);
}

export function getProductsByCategory(categoryId, limit = 50) {
  return jsonRpc('/web/dataset/search_read', {
    model: 'product.template',
    domain: [
      ['sale_ok', '=', true],
      ['public_categ_ids', 'in', [categoryId]],
    ],
    fields: ['id', 'name', 'list_price', 'default_code', 'image_256', 'website_url', 'categ_id'],
    limit,
  }).then(asArray);
}

// ============================================================
// CLIENTE
// ============================================================

export function getPartnerInfo() {
  if (!_partnerId) throw new Error('No hay sesión activa');
  return jsonRpc('/web/dataset/search_read', {
    model: 'res.partner',
    domain: [['id', '=', _partnerId]],
    fields: ['id', 'name', 'email', 'phone', 'mobile', 'vat', 'credit_limit', 'total_due'],
    limit: 1,
  });
}

export function getMyOrders(limit = 20) {
  if (!_partnerId) throw new Error('No hay sesión activa');
  return jsonRpc('/web/dataset/search_read', {
    model: 'sale.order',
    domain: [['partner_id', '=', _partnerId]],
    fields: ['id', 'name', 'date_order', 'amount_total', 'state', 'payment_term_id'],
    limit,
    order: 'date_order desc',
  }).then(asArray);
}

export function getCreditLines() {
  if (!_partnerId) throw new Error('No hay sesión activa');
  return jsonRpc('/web/dataset/search_read', {
    model: 'account.credit.line',
    domain: [['partner_id', '=', _partnerId]],
    fields: ['id', 'name', 'credit_limit', 'available_credit', 'state', 'date'],
    order: 'date desc',
  }).then(asArray);
}

// ============================================================
// PAGOS — pasarelas del ERP (payment.provider)
// Odoo 16 + "Payment Engine" custom: `payment.acquirer` fue
// renombrado a `payment.provider`. Usar /payment/pay del servidor,
// nunca llamar al banco desde la app.
// ============================================================

export const PROVIDER_BDV = 'bdv';
export const PROVIDER_BNC = 'bnc';

/** Pasarelas habilitadas, en el mismo orden que muestra el carrito web. */
export function getPaymentProviders() {
  return jsonRpc('/web/dataset/search_read', {
    model: 'payment.provider',
    domain: [['state', '=', 'enabled']],
    fields: ['id', 'display_name', 'code', 'state', 'journal_id', 'sequence'],
    order: 'sequence,id',
  }).then(asArray);
}

/**
 * Facturas del cliente con saldo pendiente.
 * El grupo Portal solo tiene lectura sobre account.move, asi que
 * la app nunca crea facturas: solo lista las que Odoo ya emitio.
 */
export function getMyUnpaidInvoices(limit = 30) {
  if (!_partnerId) throw new Error('No hay sesión activa');
  return jsonRpc('/web/dataset/search_read', {
    model: 'account.move',
    domain: [
      ['partner_id', '=', _partnerId],
      ['move_type', '=', 'out_invoice'],
      ['state', '=', 'posted'],
      ['amount_residual', '>', 0],
    ],
    fields: [
      'id', 'name', 'invoice_date_due', 'amount_total',
      'amount_residual', 'currency_id', 'payment_state', 'access_token',
    ],
    limit,
    order: 'invoice_date_due asc',
  }).then(asArray);
}

/** Historial de pagos del cliente contra las pasarelas del ERP. */
export function getMyPaymentTransactions(limit = 20) {
  if (!_partnerId) throw new Error('No hay sesión activa');
  return jsonRpc('/web/dataset/search_read', {
    model: 'payment.transaction',
    domain: [['partner_id', '=', _partnerId]],
    fields: ['id', 'reference', 'state', 'amount', 'provider_id', 'create_date'],
    limit,
    order: 'id desc',
  }).then(asArray);
}

/**
 * Construye la URL que abre el servidor para cobrar una factura.
 * El `access_token` evita que el cliente tenga que loguearse otra
 * vez en el navegador: con el token, Odoo autoriza la factura.
 *
 * Importante: NO se mandan credenciales del banco desde la app.
 * `pass_bdv` / `user_bdv` viven unicamente en Odoo.
 */
export function buildInvoicePaymentUrl({ invoiceId, amount, providerId, providerCode = PROVIDER_BDV, currencyId = 2, accessToken }) {
  const params = [
    'reference_model=account.move',
    `reference_id=${encodeURIComponent(invoiceId)}`,
    `amount=${encodeURIComponent(amount)}`,
    `currency_id=${encodeURIComponent(currencyId)}`,
  ];
  if (providerId) params.push(`provider_id=${encodeURIComponent(providerId)}`);
  params.push(`provider_code=${encodeURIComponent(providerCode)}`);
  if (accessToken) params.push(`access_token=${encodeURIComponent(accessToken)}`);
  return `${BASE_URL}/payment/pay?${params.join('&')}`;
}

/** Texto legible del estado de pago de una factura. */
export function paymentStateLabel(paymentState) {
  switch (paymentState) {
    case 'paid':
      return 'Pagada';
    case 'partial':
      return 'Pago parcial';
    case 'reversed':
      return 'Revertida';
    case 'in_payment':
      return 'En proceso';
    default:
      return 'Pendiente';
  }
}

// ============================================================
// UTILIDADES
// ============================================================

export function getProductImageUrl(productId) {
  return `${BASE_URL}/web/image/product.template/${productId}/image_256`;
}

// ============================================================
// PLANES DE PAGO (endpoint real del sitio)
// ============================================================

/**
 * Obtiene datos de precio y cuota administrativa de un producto.
 * Endpoint real: /product/search/plans  (recibe product_id = template id)
 * Devuelve { id, name, description, list_price, cuota_administrativa }
 */
export function getProductPlans(productId) {
  return jsonRpc('/product/search/plans', {
    product_id: parseInt(productId, 10),
  });
}
