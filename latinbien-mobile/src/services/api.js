// ============================================================
// LatinBien Mobile — API Service (Odoo 16 JSON-RPC)
// Usa XMLHttpRequest para tener control total de cookies
// ============================================================

import { BASE_URL } from '../utils/constants';
import AsyncStorage from '@react-native-async-storage/async-storage';

let _partnerId = null;
let _sessionCookie = null;

const COOKIE_KEY = 'odoo_session_cookie';

export function setPartnerId(id) {
  _partnerId = id;
}

export async function loadSessionCookie() {
  try {
    const stored = await AsyncStorage.getItem(COOKIE_KEY);
    if (stored) _sessionCookie = stored;
  } catch (_) {}
}

/**
 * Llamada JSON-RPC usando XMLHttpRequest para acceso completo a headers
 */
function jsonRpc(endpoint, params = {}) {
  return new Promise((resolve, reject) => {
    const url = `${BASE_URL}${endpoint}`;
    const body = JSON.stringify({ jsonrpc: '2.0', method: 'call', params, id: Date.now() });

    const xhr = new XMLHttpRequest();
    xhr.open('POST', url, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.withCredentials = false; // Nosotros manejamos las cookies manualmente

    // Enviar cookie de sesión si la tenemos
    if (_sessionCookie) {
      xhr.setRequestHeader('Cookie', _sessionCookie);
    }

    xhr.onreadystatechange = async function () {
      if (xhr.readyState !== 4) return;

      if (xhr.status < 200 || xhr.status >= 300) {
        reject(new Error(`Error de conexión (${xhr.status})`));
        return;
      }

      // Capturar Set-Cookie del response headers
      const rawHeaders = xhr.getAllResponseHeaders();
      const setCookieMatch = rawHeaders.match(/set-cookie:\s*([^\r\n]+)/i);
      if (setCookieMatch) {
        const cookieVal = setCookieMatch[1];
        const sessionMatch = cookieVal.match(/session_id=[^;]+/);
        if (sessionMatch) {
          _sessionCookie = sessionMatch[0];
          try { await AsyncStorage.setItem(COOKIE_KEY, _sessionCookie); } catch (_) {}
        }
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
