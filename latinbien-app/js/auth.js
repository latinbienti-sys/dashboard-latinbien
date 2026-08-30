/* ============================================================
   LatinBien App — Autenticación (Odoo Session)
   Con integración directa con API.setPartnerId()
   ============================================================ */

const AUTH = (() => {
  'use strict';

  const STORAGE_KEY = 'latinbien_session';
  let _currentUser = null;
  let _listeners = [];

  // ========================================================================
  //  I N I T   &   P E R S I S T
  // ========================================================================

  function init() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        _currentUser = JSON.parse(stored);
        // Restaurar partner_id en API
        if (_currentUser && _currentUser.partner_id) {
          API.setPartnerId(_currentUser.partner_id);
        }
      }
    } catch (e) {
      _currentUser = null;
    }
    return _currentUser;
  }

  function _persist(user) {
    const prevUser = _currentUser;
    _currentUser = user;

    if (user) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
      if (user.partner_id) {
        API.setPartnerId(user.partner_id);
      }
    } else {
      localStorage.removeItem(STORAGE_KEY);
      API.setPartnerId(null);
    }

    // Solo notificar si hubo cambio real
    const prevId = prevUser?.uid || null;
    const newId = user?.uid || null;
    if (prevId !== newId) {
      _notify(user);
    }
  }

  function _notify(user) {
    _listeners.forEach(fn => {
      try { fn(user); } catch (e) { /* ignore listener error */ }
    });
  }

  // ========================================================================
  //  P Ú B L I C A S
  // ========================================================================

  function onChange(fn) {
    _listeners.push(fn);
    return () => {
      _listeners = _listeners.filter(f => f !== fn);
    };
  }

  /**
   * Verificar si la sesión de Odoo sigue activa
   */
  async function checkSession() {
    try {
      const info = await API.getSessionInfo();
      if (info && info.uid && info.uid !== false) {
        const user = {
          uid: info.uid,
          name: info.name || 'Usuario',
          username: info.username || '',
          partner_id: info.partner_id,
          db: info.db,
          is_superuser: info.is_superuser || false,
          company_id: info.company_id,
          session_id: info.session_id || '',
        };
        _persist(user);
        return user;
      }
    } catch (e) {
      console.warn('Sesión no activa:', e.message);
    }
    _persist(null);
    return null;
  }

  /**
   * Iniciar sesión con correo y contraseña (mismo login que latinbien.com)
   */
  async function login(login, password) {
    const result = await API.login(login, password);
    if (result && result.uid) {
      const user = {
        uid: result.uid,
        name: result.name || login,
        username: result.username || login,
        partner_id: result.partner_id,
        db: result.db,
        is_superuser: result.is_superuser || false,
        company_id: result.company_id,
        session_id: result.session_id || '',
      };
      _persist(user);
      return user;
    }
    throw new Error('Credenciales inválidas. Verifica tu correo y contraseña.');
  }

  /**
   * Cerrar sesión en Odoo y limpiar localStorage
   */
  async function logout() {
    try {
      await API.logout();
    } catch (e) {
      console.warn('Error en logout API:', e.message);
    }
    _persist(null);
  }

  /**
   * Obtener usuario de la sesión actual (sin llamada API)
   */
  function getCurrentUser() {
    return _currentUser;
  }

  /**
   * ¿Hay sesión activa?
   */
  function isAuthenticated() {
    return _currentUser !== null && !!_currentUser.uid;
  }

  /**
   * Obtener partner_id del usuario logueado
   */
  function getPartnerId() {
    return _currentUser?.partner_id || null;
  }

  return {
    init,
    checkSession,
    login,
    logout,
    getCurrentUser,
    isAuthenticated,
    getPartnerId,
    onChange,
  };
})();
