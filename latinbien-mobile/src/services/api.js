// ============================================================
// LatinBien Mobile — API Service (Odoo 16 JSON-RPC)
// ============================================================

import { BASE_URL } from '../utils/constants';

let _partnerId = null;

/**
 * Establecer el partner_id del usuario logueado
 */
export function setPartnerId(id) {
  _partnerId = id;
}

/**
 * Llamada JSON-RPC a Odoo
 */
async function jsonRpc(endpoint, method, params = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const body = JSON.stringify({
    jsonrpc: '2.0',
    method,
    params,
    id: Date.now(),
  });

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
    },
    credentials: 'include',
    body,
  });

  if (!response.ok) {
    throw new Error(`Error de conexión (${response.status})`);
  }

  const data = await response.json();
  if (data.error) {
    const msg = data.error.data?.message || data.error.message || 'Error del servidor';
    throw new Error(msg.replace(/^Odoo Server Error\s*/i, '').trim());
  }
  return data.result;
}

// ============================================================
// AUTH
// ============================================================

export function getSessionInfo() {
  return jsonRpc('/web/session/get_session_info', 'call');
}

export function login(login, password) {
  return jsonRpc('/web/session/authenticate', 'call', {
    db: 'erp_production',
    login,
    password,
  });
}

export function logout() {
  return jsonRpc('/web/session/destroy', 'call');
}

// ============================================================
// CATÁLOGO
// ============================================================

export function getFeaturedProducts(limit = 20) {
  return jsonRpc('/web/dataset/call_kw/product.template', 'call', {
    model: 'product.template',
    method: 'search_read',
    args: [],
    kwargs: {
      domain: [['sale_ok', '=', true], ['published_on_website', '=', true]],
      fields: ['id', 'name', 'list_price', 'default_code', 'image_256', 'website_url', 'categ_id'],
      limit,
      order: 'write_date desc',
    },
  });
}

export function searchProducts(query, limit = 20) {
  return jsonRpc('/web/dataset/call_kw/product.template', 'call', {
    model: 'product.template',
    method: 'search_read',
    args: [],
    kwargs: {
      domain: [
        ['sale_ok', '=', true],
        ['published_on_website', '=', true],
        '|',
        ['name', 'ilike', query],
        ['default_code', 'ilike', query],
      ],
      fields: ['id', 'name', 'list_price', 'default_code', 'image_256', 'website_url', 'categ_id'],
      limit,
    },
  });
}

export function getCategories() {
  return jsonRpc('/web/dataset/call_kw/product.public.category', 'call', {
    model: 'product.public.category',
    method: 'search_read',
    args: [],
    kwargs: {
      domain: [['website_published', '=', true]],
      fields: ['id', 'name', 'parent_id', 'child_id'],
      order: 'sequence asc',
    },
  });
}

export function getProductsByCategory(categoryId, limit = 50) {
  return jsonRpc('/web/dataset/call_kw/product.template', 'call', {
    model: 'product.template',
    method: 'search_read',
    args: [],
    kwargs: {
      domain: [
        ['sale_ok', '=', true],
        ['published_on_website', '=', true],
        ['public_categ_ids', 'in', [categoryId]],
      ],
      fields: ['id', 'name', 'list_price', 'default_code', 'image_256', 'website_url', 'categ_id'],
      limit,
    },
  });
}

// ============================================================
// CLIENTE
// ============================================================

export function getPartnerInfo() {
  if (!_partnerId) throw new Error('No hay sesión activa');
  return jsonRpc('/web/dataset/call_kw/res.partner', 'call', {
    model: 'res.partner',
    method: 'search_read',
    args: [],
    kwargs: {
      domain: [['id', '=', _partnerId]],
      fields: ['id', 'name', 'email', 'phone', 'mobile', 'vat', 'credit_limit', 'total_due'],
      limit: 1,
    },
  });
}

export function getMyOrders(limit = 20) {
  if (!_partnerId) throw new Error('No hay sesión activa');
  return jsonRpc('/web/dataset/call_kw.sale.order', 'call', {
    model: 'sale.order',
    method: 'search_read',
    args: [],
    kwargs: {
      domain: [['partner_id', '=', _partnerId]],
      fields: ['id', 'name', 'date_order', 'amount_total', 'state', 'payment_term_id'],
      limit,
      order: 'date_order desc',
    },
  });
}

export function getCreditLines() {
  if (!_partnerId) throw new Error('No hay sesión activa');
  return jsonRpc('/web/dataset/call_kw.account.credit.line', 'call', {
    model: 'account.credit.line',
    method: 'search_read',
    args: [],
    kwargs: {
      domain: [['partner_id', '=', _partnerId]],
      fields: ['id', 'name', 'credit_limit', 'available_credit', 'state', 'date'],
      order: 'date desc',
    },
  });
}

// ============================================================
// UTILIDADES
// ============================================================

export function getProductImageUrl(productId) {
  return `${BASE_URL}/web/image/product.template/${productId}/image_256`;
}
