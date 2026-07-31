// ============================================================
// LatinBien Mobile — API Service (Odoo 16 JSON-RPC)
// Usa XMLHttpRequest con withCredentials=true para que OkHttp
// maneje las cookies automáticamente (como un navegador)
// ============================================================

import { BASE_URL } from '../utils/constants';

let _partnerId = null;

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
  });
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
  });
}

export function getCategories() {
  return jsonRpc('/web/dataset/search_read', {
    model: 'product.public.category',
    domain: [],
    fields: ['id', 'name'],
    order: 'sequence asc',
  });
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
  });
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
  });
}

export function getCreditLines() {
  if (!_partnerId) throw new Error('No hay sesión activa');
  return jsonRpc('/web/dataset/search_read', {
    model: 'account.credit.line',
    domain: [['partner_id', '=', _partnerId]],
    fields: ['id', 'name', 'credit_limit', 'available_credit', 'state', 'date'],
    order: 'date desc',
  });
}

// ============================================================
// UTILIDADES
// ============================================================

export function getProductImageUrl(productId) {
  return `${BASE_URL}/web/image/product.template/${productId}/image_256`;
}
