'use strict';
// Rutas de autenticación: registro, login, perfil
const express = require('express');
const bcrypt = require('bcryptjs');
const db = require('../db/database');
const { signToken, authRequired } = require('../middleware/auth');

const router = express.Router();

// POST /api/auth/register
router.post('/register', (req, res) => {
  const { full_name, email, password, role } = req.body || {};

  if (!full_name || !email || !password) {
    return res.status(400).json({ error: 'Nombre, correo y contraseña son obligatorios.' });
  }
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return res.status(400).json({ error: 'Correo electrónico no válido.' });
  }
  if (password.length < 6) {
    return res.status(400).json({ error: 'La contraseña debe tener al menos 6 caracteres.' });
  }
  const finalRole = role === 'profesor' ? 'profesor' : 'estudiante';

  const existing = db.prepare('SELECT id FROM users WHERE email = ?').get(email);
  if (existing) {
    return res.status(409).json({ error: 'Ya existe una cuenta con este correo.' });
  }

  const hash = bcrypt.hashSync(password, 10);
  const result = db.prepare(
    'INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)'
  ).run(full_name.trim(), email.toLowerCase().trim(), hash, finalRole);

  const user = db.prepare(
    'SELECT id, full_name, email, role FROM users WHERE id = ?'
  ).get(result.lastInsertRowid);

  return res.status(201).json({ token: signToken(user), user });
});

// POST /api/auth/login
router.post('/login', (req, res) => {
  const { email, password } = req.body || {};

  if (!email || !password) {
    return res.status(400).json({ error: 'Correo y contraseña son obligatorios.' });
  }

  const user = db.prepare(
    'SELECT id, full_name, email, password_hash, role FROM users WHERE email = ?'
  ).get(email.toLowerCase().trim());

  if (!user || !bcrypt.compareSync(password, user.password_hash)) {
    return res.status(401).json({ error: 'Credenciales incorrectas.' });
  }

  return res.json({
    token: signToken(user),
    user: { id: user.id, full_name: user.full_name, email: user.email, role: user.role }
  });
});

// GET /api/auth/me
router.get('/me', authRequired, (req, res) => {
  res.json({ user: req.user });
});

module.exports = router;
