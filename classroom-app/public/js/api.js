'use strict';
// Helper de API para el frontend
const API = {
  base: '',

  getToken() {
    return localStorage.getItem('token');
  },

  setToken(token) {
    localStorage.setItem('token', token);
  },

  clearToken() {
    localStorage.removeItem('token');
  },

  getHeaders(includeAuth = true) {
    const headers = { 'Content-Type': 'application/json' };
    if (includeAuth) {
      const token = this.getToken();
      if (token) headers['Authorization'] = 'Bearer ' + token;
    }
    return headers;
  },

  async request(method, path, body = null, includeAuth = true) {
    const options = {
      method,
      headers: this.getHeaders(includeAuth)
    };
    if (body && !(body instanceof FormData)) {
      options.body = JSON.stringify(body);
    } else if (body instanceof FormData) {
      delete options.headers['Content-Type']; // dejar que el navegador ponga el boundary
      const token = this.getToken();
      if (token) options.headers['Authorization'] = 'Bearer ' + token;
      options.body = body;
    }

    const res = await fetch(this.base + path, options);
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      const err = new Error(data.error || 'Error de servidor');
      err.status = res.status;
      if (res.status === 401) err.unauthorized = true;
      throw err;
    }
    return data;
  },

  get(path, includeAuth = true) {
    return this.request('GET', path, null, includeAuth);
  },

  post(path, body, includeAuth = true) {
    return this.request('POST', path, body, includeAuth);
  },

  put(path, body, includeAuth = true) {
    return this.request('PUT', path, body, includeAuth);
  },

  del(path, includeAuth = true) {
    return this.request('DELETE', path, null, includeAuth);
  },

  upload(path, formData) {
    return this.request('POST', path, formData, true);
  },

  // Descarga de archivo con auth (abre en pestaña nueva)
  downloadUrl(path) {
    const token = this.getToken();
    return this.base + path + (token ? '?token=' + encodeURIComponent(token) : '');
  }
};
