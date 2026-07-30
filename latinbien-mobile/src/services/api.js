// ============================================================
// LatinBien Mobile — API Service (Odoo 16 JSON-RPC)
// ============================================================

import { BASE_URL } from '../utils/constants';
import AsyncStorage from '@react-native-async-storage/async-storage';

let _partnerId = null;
let _sessionCookie = null;

const COOKIE_KEY = 'odoo_session_cookie';

export function setPartnerId(id) {
  _partnerId = id;
}

/**
 * Inicializar cookie de sesión desde storage
 */
export async function loadSessionCookie() {
  try {
    const stored = await AsyncStorage.getItem(COOKIE_KEY);
    if (stored) _sessionCookie = stored;
  } catch (_) {}
}

/**
 * Enviar llamada JSON-RPC a Odoo con manejo manual de cookies
 * Usa el endpoint genérico sin modelo en la URL
 */
async function jsonRpc(endpoint, params = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const body = JSON.stringify({ jsonrpc: '2.0', method: 'call', params, id: Date.now() });

  const headers = {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
  };

  // Enviar cookie de sesión manualmente
  if (_sessionCookie) {
    headers['Cookie'] = _sessionCookie;
  }

  const response = await fetch(url, {
    method: 'POST',
    headers,
    credentials: 'omit',
    body,
  });

  if (!response.ok) {
    throw new Error(`Error de conexión (${response.status})`);
  }

  // Capturar Set-Cookie de la respuesta (para login)
  let cookieStr = '';
  response.headers.forEach((value, key) => {
    if (key.toLowerCase() === 'set-cookie') {
      cookieStr = value;
    }
  });

  if (cookieStr && cookieStr.includes('session_id')) {
    const match = cookieStr.match(/session_id=[^;]+/);
    if (match) {
      _sessionCookie = match[0];
      try { await AsyncStorage.setItem(COOKIE_KEY, _sessionCookie); } catch (_) {}
    }
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
// CATÁLOGO — usando search_read (endpoint plano, más compatible)
// ============================================================

export function getFeaturedProducts(limit = 20) {
  return jsonRpc('/web/dataset/search_read', {
    model: 'product.template',
    domain: [['sale_ok', '=', true], ['published_on_website', '=', true]],
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
      ['published_on_website', '=', true],
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
    domain: [['website_published', '=', true]],
    fields: ['id', 'name', 'parent_id', 'child_id'],
    order: 'sequence asc',
  });
}

export function getProductsByCategory(categoryId, limit = 50) {
  return jsonRpc('/web/dataset/search_read', {
    model: 'product.template',
    domain: [
      ['sale_ok', '=', true],
      ['published_on_website', '=', true],
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
