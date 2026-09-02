'use strict';
// Middleware de autenticación JWT y autorización por roles
const jwt = require('jsonwebtoken');
const db = require('../db/database');

const JWT_SECRET = process.env.JWT_SECRET || 'classroom-app-secret-key-dev';

function signToken(user) {
  return jwt.sign(
    { id: user.id, role: user.role },
    JWT_SECRET,
    { expiresIn: '7d' }
  );
}

// Verifica que exista un token válido y adjunta req.user
function authRequired(req, res, next) {
  const header = req.headers.authorization || '';
  let token = header.startsWith('Bearer ') ? header.slice(7) : null;

  // Permitir token vía query string (para descargas de archivos)
  if (!token && req.query && req.query.token) {
    token = req.query.token;
  }

  if (!token) {
    return res.status(401).json({ error: 'No autorizado: falta token.' });
  }

  try {
    const payload = jwt.verify(token, JWT_SECRET);
    const user = db.prepare(
      'SELECT id, full_name, email, role FROM users WHERE id = ?'
    ).get(payload.id);

    if (!user) {
      return res.status(401).json({ error: 'Usuario no encontrado.' });
    }
    req.user = user;
    next();
  } catch (err) {
    return res.status(401).json({ error: 'Token inválido o expirado.' });
  }
}

// Verifica que el rol del usuario esté en la lista permitida
function requireRole(...roles) {
  return (req, res, next) => {
    if (!req.user) return res.status(401).json({ error: 'No autorizado.' });
    if (!roles.includes(req.user.role)) {
      return res.status(403).json({ error: `Acción restringida: requiere rol ${roles.join(' o ')}.` });
    }
    next();
  };
}

module.exports = { signToken, authRequired, requireRole, JWT_SECRET };
