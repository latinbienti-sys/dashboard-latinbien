'use strict';
// Rutas de pagos (simulados)
const express = require('express');
const crypto = require('crypto');
const db = require('../db/database');
const { authRequired, requireRole } = require('../middleware/auth');

const router = express.Router();

// POST /api/payments - registrar pago (estudiante se inscribe y paga)
router.post('/', authRequired, requireRole('estudiante'), (req, res) => {
  const { course_id, method } = req.body || {};

  if (!course_id) {
    return res.status(400).json({ error: 'El curso es obligatorio.' });
  }

  const course = db.prepare('SELECT * FROM courses WHERE id = ?').get(course_id);
  if (!course) return res.status(404).json({ error: 'Curso no encontrado.' });

  const alreadyEnrolled = db.prepare(
    'SELECT 1 FROM course_enrollments WHERE course_id = ? AND student_id = ?'
  ).get(course_id, req.user.id);
  if (alreadyEnrolled) {
    return res.status(409).json({ error: 'Ya estás inscrito y has pagado este curso.' });
  }

  // Generar referencia única
  const reference = `PAY-${Date.now()}-${crypto.randomBytes(4).toString('hex').toUpperCase()}`;
  const finalMethod = ['tarjeta', 'transferencia', 'paypal'].includes(method) ? method : 'tarjeta';

  const result = db.prepare(
    `INSERT INTO payments (student_id, course_id, amount, method, status, reference)
     VALUES (?, ?, ?, ?, 'pagado', ?)`
  ).run(req.user.id, course_id, course.price, finalMethod, reference);

  // Inscribir automáticamente al estudiante
  db.prepare('INSERT INTO course_enrollments (course_id, student_id) VALUES (?, ?)')
    .run(course_id, req.user.id);

  const payment = db.prepare(
    'SELECT p.*, c.title AS course_title FROM payments p JOIN courses c ON c.id = p.course_id WHERE p.id = ?'
  ).get(result.lastInsertRowid);

  res.status(201).json({ payment, message: 'Pago registrado e inscripción completada.' });
});

// GET /api/payments/my - historial de pagos del estudiante
router.get('/my', authRequired, requireRole('estudiante'), (req, res) => {
  const payments = db.prepare(
    `SELECT p.*, c.title AS course_title FROM payments p
     JOIN courses c ON c.id = p.course_id
     WHERE p.student_id = ? ORDER BY p.created_at DESC`
  ).all(req.user.id);

  res.json({ payments });
});

// GET /api/payments/course/:courseId - pagos de un curso (profesor)
router.get('/course/:courseId', authRequired, requireRole('profesor'), (req, res) => {
  const course = db.prepare('SELECT * FROM courses WHERE id = ? AND teacher_id = ?')
    .get(req.params.courseId, req.user.id);
  if (!course) return res.status(404).json({ error: 'Curso no encontrado o no eres el profesor.' });

  const payments = db.prepare(
    `SELECT p.*, u.full_name AS student_name FROM payments p
     JOIN users u ON u.id = p.student_id
     WHERE p.course_id = ? ORDER BY p.created_at DESC`
  ).all(course.id);

  const total = payments.reduce((acc, p) => acc + p.amount, 0);

  res.json({ payments, total, course });
});

module.exports = router;
