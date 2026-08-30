'use strict';
// Rutas de clases en vivo (programación + sala Jitsi)
const express = require('express');
const crypto = require('crypto');
const db = require('../db/database');
const { authRequired, requireRole } = require('../middleware/auth');

const router = express.Router();

// Genera un nombre de sala único para Jitsi
function makeRoomName() {
  return `classroom-${crypto.randomBytes(6).toString('hex')}`;
}

// POST /api/live-classes - crear clase en vivo (solo profesor)
router.post('/', authRequired, requireRole('profesor'), (req, res) => {
  const { course_id, title, description, scheduled_at, duration_min } = req.body || {};

  if (!course_id || !title || !scheduled_at) {
    return res.status(400).json({ error: 'Curso, título y fecha son obligatorios.' });
  }

  const course = db.prepare('SELECT * FROM courses WHERE id = ? AND teacher_id = ?')
    .get(course_id, req.user.id);
  if (!course) {
    return res.status(403).json({ error: 'Curso no encontrado o no eres el profesor.' });
  }

  const result = db.prepare(
    `INSERT INTO live_classes (course_id, title, description, room_name, scheduled_at, duration_min, created_by)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  ).run(
    course_id,
    title.trim(),
    description || '',
    makeRoomName(),
    scheduled_at,
    parseInt(duration_min, 10) || 60,
    req.user.id
  );

  const liveClass = db.prepare('SELECT * FROM live_classes WHERE id = ?').get(result.lastInsertRowid);
  res.status(201).json({ liveClass });
});

// GET /api/live-classes/course/:courseId - clases de un curso
router.get('/course/:courseId', authRequired, (req, res) => {
  const course = db.prepare('SELECT * FROM courses WHERE id = ?').get(req.params.courseId);
  if (!course) return res.status(404).json({ error: 'Curso no encontrado.' });

  let allowed = false;
  if (req.user.role === 'profesor' && course.teacher_id === req.user.id) allowed = true;
  if (req.user.role === 'estudiante') {
    const enrolled = db.prepare(
      'SELECT 1 FROM course_enrollments WHERE course_id = ? AND student_id = ?'
    ).get(course.id, req.user.id);
    allowed = !!enrolled;
  }
  if (!allowed) return res.status(403).json({ error: 'No tienes acceso a este curso.' });

  const live_classes = db.prepare(
    'SELECT * FROM live_classes WHERE course_id = ? ORDER BY scheduled_at ASC'
  ).all(course.id);

  res.json({ live_classes });
});

// GET /api/live-classes/:id - detalle de una clase (incluye enlace de sala)
router.get('/:id', authRequired, (req, res) => {
  const liveClass = db.prepare('SELECT * FROM live_classes WHERE id = ?').get(req.params.id);
  if (!liveClass) return res.status(404).json({ error: 'Clase no encontrada.' });

  const course = db.prepare('SELECT * FROM courses WHERE id = ?').get(liveClass.course_id);

  let allowed = false;
  if (req.user.role === 'profesor' && course.teacher_id === req.user.id) allowed = true;
  if (req.user.role === 'estudiante') {
    const enrolled = db.prepare(
      'SELECT 1 FROM course_enrollments WHERE course_id = ? AND student_id = ?'
    ).get(course.id, req.user.id);
    allowed = !!enrolled;
  }
  if (!allowed) return res.status(403).json({ error: 'No tienes acceso a esta clase.' });

  res.json({ liveClass });
});

// DELETE /api/live-classes/:id - eliminar clase (solo profesor)
router.delete('/:id', authRequired, requireRole('profesor'), (req, res) => {
  const liveClass = db.prepare('SELECT * FROM live_classes WHERE id = ?').get(req.params.id);
  if (!liveClass) return res.status(404).json({ error: 'Clase no encontrada.' });

  const course = db.prepare('SELECT * FROM courses WHERE id = ?').get(liveClass.course_id);
  if (!course || course.teacher_id !== req.user.id) {
    return res.status(403).json({ error: 'No eres el profesor de este curso.' });
  }

  db.prepare('DELETE FROM live_classes WHERE id = ?').run(liveClass.id);
  res.json({ message: 'Clase eliminada.' });
});

module.exports = router;
