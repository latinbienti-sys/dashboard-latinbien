/* ============================================================
   LatinBien App — API Wrapper para Odoo 16
   ============================================================ */

const API = (() => {
  'use strict';

  const BASE_URL = 'https://latinbien.com';
  const JSONRPC_VERSION = '2.0';
  let _requestId = 0;
  let _partnerId = null;  // Se setea desde auth.js tras login

  // ========================================================================
  //  C O R E   J S O N - R P C
  // ========================================================================

  /**
   * Llamada JSON-RPC genérica a Odoo
   */
  async function jsonRpc(endpoint, method, params = {}) {
    _requestId++;
    const url = `${BASE_URL}${endpoint}`;
    const body = JSON.stringify({
      jsonrpc: JSONRPC_VERSION,
      method: method,
      params: params,
      id: _requestId,
    });

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
      },
      credentials: 'include',
      body: body,
    });

    if (!response.ok) {
      throw new Error(`Error de conexión (HTTP ${response.status})`);
    }

    const data = await response.json();
    if (data.error) {
      const msg = data.error.data?.message || data.error.message || 'Error del servidor';
      // Limpiar mensajes técnicos de Odoo para el usuario
      const cleanMsg = msg.replace(/^Odoo Server Error\s*/i, '').trim();
      throw new Error(cleanMsg);
    }
    return data.result;
  }

  /**
   * Llamada GET simple a Odoo
   */
  async function get(endpoint) {
    const url = `${BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      credentials: 'include',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  // ========================================================================
  //  R E S O L U C I Ó N   D E   D O M I N I O S
  // ========================================================================

  /**
   * Asignar el partner_id del usuario logueado
   */
  function setPartnerId(id) {
    _partnerId = id;
  }

  /**
   * Reemplazar 'uid_in_session' con el partner_id real en un domain de Odoo
   */
  function resolveDomain(domain) {
    if (!_partnerId) return domain;
    return domain.map(cond => {
      if (!Array.isArray(cond)) return cond;
      return cond.map(val => (val === 'uid_in_session' ? _partnerId : val));
    });
  }

  /**
   * Construye kwargs para search_read con dominio resuelto automáticamente
   */
  function _buildKwargs(baseKwargs) {
    const kwargs = JSON.parse(JSON.stringify(baseKwargs));
    if (kwargs.domain) {
      kwargs.domain = resolveDomain(kwargs.domain);
    }
    if (kwargs.kwargs?.domain) {
      kwargs.kwargs.domain = resolveDomain(kwargs.kwargs.domain);
    }
    return kwargs;
  }

  // ========================================================================
  //  I M A G E N E S   (Odoo -> base64 -> data URL)
  // ========================================================================

  /**
   * Convierte el campo image_256 de Odoo (base64) a una data URL usable
   */
  function imageToDataUrl(base64Str) {
    if (!base64Str) return null;
    // Odoo a veces devuelve con o sin prefijo data:
    if (base64Str.startsWith('data:')) return base64Str;
    return `data:image/png;base64,${base64Str}`;
  }

  /**
   * Obtiene la URL directa de una imagen de producto (más confiable que base64)
   */
  function getProductImageUrl(productId) {
    return `${BASE_URL}/web/image/product.template/${productId}/image_256`;
  }

  // ========================================================================
  //  A U T E N T I C A C I Ó N
  // ========================================================================

  async function getSessionInfo() {
    return jsonRpc('/web/session/get_session_info', 'call');
  }

  async function login(login, password) {
    return jsonRpc('/web/session/authenticate', 'call', {
      db: 'latinbien',
      login: login,
      password: password,
    });
  }

  async function logout() {
    return jsonRpc('/web/session/destroy', 'call');
  }

  async function changePassword(oldPassword, newPassword) {
    return jsonRpc('/web/session/change_password', 'call', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  }

  async function signup(name, login, password) {
    // En Odoo 16 el signup web no es un JSON-RPC directo; mejor redirigir
    window.open('https://latinbien.com/web/signup', '_blank');
    return { redirect: true };
  }

  // ========================================================================
  //  C A T Á L O G O
  // ========================================================================

  async function getFeaturedProducts(limit = 20) {
    return jsonRpc('/web/dataset/call_kw/product.template', 'call',
      _buildKwargs({
        model: 'product.template',
        method: 'search_read',
        args: [],
        kwargs: {
          domain: [['sale_ok', '=', true], ['published_on_website', '=', true]],
          fields: ['id', 'name', 'list_price', 'default_code', 'image_256', 'website_url', 'categ_id'],
          limit: limit,
          order: 'write_date desc',
        },
      })
    );
  }

  async function searchProducts(query, limit = 20) {
    return jsonRpc('/web/dataset/call_kw/product.template', 'call',
      _buildKwargs({
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
          limit: limit,
        },
      })
    );
  }

  async function getCategories() {
    return jsonRpc('/web/dataset/call_kw/product.public.category', 'call',
      _buildKwargs({
        model: 'product.public.category',
        method: 'search_read',
        args: [],
        kwargs: {
          domain: [['website_published', '=', true]],
          fields: ['id', 'name', 'parent_id', 'child_id', 'image_256'],
          order: 'sequence asc',
        },
      })
    );
  }

  async function getProductsByCategory(categoryId, limit = 50) {
    return jsonRpc('/web/dataset/call_kw/product.template', 'call',
      _buildKwargs({
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
          limit: limit,
        },
      })
    );
  }

  // ========================================================================
  //  C L I E N T E S
  // ========================================================================

  async function getPartnerInfo() {
    if (!_partnerId) throw new Error('No hay sesión activa');
    return jsonRpc('/web/dataset/call_kw/res.partner', 'call',
      _buildKwargs({
        model: 'res.partner',
        method: 'search_read',
        args: [],
        kwargs: {
          domain: [['id', '=', _partnerId]],
          fields: ['id', 'name', 'email', 'phone', 'mobile', 'vat', 'credit_limit', 'total_due'],
          limit: 1,
        },
      })
    );
  }

  async function getMyOrders(limit = 20) {
    if (!_partnerId) throw new Error('No hay sesión activa');
    return jsonRpc('/web/dataset/call_kw.sale.order', 'call',
      _buildKwargs({
        model: 'sale.order',
        method: 'search_read',
        args: [],
        kwargs: {
          domain: [['partner_id', '=', _partnerId]],
          fields: ['id', 'name', 'date_order', 'amount_total', 'state', 'payment_term_id'],
          limit: limit,
          order: 'date_order desc',
        },
      })
    );
  }

  // ========================================================================
  //  L Í N E A S   D E   C R É D I T O
  // ========================================================================

  async function getCreditLines() {
    if (!_partnerId) throw new Error('No hay sesión activa');
    return jsonRpc('/web/dataset/call_kw.account.credit.line', 'call',
      _buildKwargs({
        model: 'account.credit.line',
        method: 'search_read',
        args: [],
        kwargs: {
          domain: [['partner_id', '=', _partnerId]],
          fields: ['id', 'name', 'credit_limit', 'available_credit', 'state', 'date', 'line_type'],
          order: 'date desc',
        },
      })
    );
  }

  // ========================================================================
  //  E X P O R T
  // ========================================================================

  return {
    // Core
    jsonRpc,
    get,
    setPartnerId,
    resolveDomain,
    // Utilidades de imágenes
    imageToDataUrl,
    getProductImageUrl,
    BASE_URL,
    // Auth
    getSessionInfo,
    login,
    logout,
    changePassword,
    signup,
    // Catálogo
    getFeaturedProducts,
    searchProducts,
    getCategories,
    getProductsByCategory,
    // Cliente
    getPartnerInfo,
    getMyOrders,
    // Crédito
    getCreditLines,
  };
})();
