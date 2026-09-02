'use strict';
// Rutas de cursos e inscripciones
const express = require('express');
const db = require('../db/database');
const { authRequired, requireRole } = require('../middleware/auth');

const router = express.Router();

// GET /api/courses - lista de cursos según rol
router.get('/', authRequired, (req, res) => {
  if (req.user.role === 'profesor') {
    const courses = db.prepare(
      'SELECT c.*, u.full_name AS teacher_name FROM courses c JOIN users u ON u.id = c.teacher_id WHERE c.teacher_id = ? ORDER BY c.created_at DESC'
    ).all(req.user.id);
    return res.json({ courses });
  }

  // Estudiante: cursos en los que está inscrito
  const courses = db.prepare(
    `SELECT c.*, u.full_name AS teacher_name,
            (SELECT COUNT(*) FROM course_enrollments ce WHERE ce.course_id = c.id) AS student_count
     FROM courses c
     JOIN users u ON u.id = c.teacher_id
     JOIN course_enrollments ce ON ce.course_id = c.id
     WHERE ce.student_id = ?
     ORDER BY c.created_at DESC`
  ).all(req.user.id);
  return res.json({ courses });
});

// GET /api/courses/catalog - catálogo de cursos disponibles (estudiante)
router.get('/catalog', authRequired, requireRole('estudiante'), (req, res) => {
  const courses = db.prepare(
    `SELECT c.*, u.full_name AS teacher_name,
            (SELECT COUNT(*) FROM course_enrollments ce WHERE ce.course_id = c.id) AS student_count,
            EXISTS(SELECT 1 FROM course_enrollments ce2 WHERE ce2.course_id = c.id AND ce2.student_id = ?) AS enrolled
     FROM courses c JOIN users u ON u.id = c.teacher_id
     ORDER BY c.created_at DESC`
  ).all(req.user.id);
  return res.json({ courses });
});

// POST /api/courses - crear curso (solo profesor)
router.post('/', authRequired, requireRole('profesor'), (req, res) => {
  const { title, description, price } = req.body || {};
  if (!title) return res.status(400).json({ error: 'El título es obligatorio.' });

  const result = db.prepare(
    'INSERT INTO courses (title, description, teacher_id, price) VALUES (?, ?, ?, ?)'
  ).run(title.trim(), description || '', req.user.id, parseFloat(price) || 0);

  const course = db.prepare('SELECT * FROM courses WHERE id = ?').get(result.lastInsertRowid);
  res.status(201).json({ course });
});

// GET /api/courses/:id - detalle del curso
router.get('/:id', authRequired, (req, res) => {
  const course = db.prepare(
    'SELECT c.*, u.full_name AS teacher_name FROM courses c JOIN users u ON u.id = c.teacher_id WHERE c.id = ?'
  ).get(req.params.id);

  if (!course) return res.status(404).json({ error: 'Curso no encontrado.' });

  // ¿Es profesor dueño del curso o estudiante inscrito?
  if (req.user.role === 'profesor' && course.teacher_id !== req.user.id) {
    return res.status(403).json({ error: 'No tienes acceso a este curso.' });
  }
  if (req.user.role === 'estudiante') {
    const enrolled = db.prepare(
      'SELECT 1 FROM course_enrollments WHERE course_id = ? AND student_id = ?'
    ).get(course.id, req.user.id);
    if (!enrolled) return res.status(403).json({ error: 'Debes inscribirte al curso.' });
  }

  // Materiales y clases del curso
  const materials = db.prepare(
    'SELECT m.*, u.full_name AS uploaded_by_name FROM materials m JOIN users u ON u.id = m.uploaded_by WHERE m.course_id = ? ORDER BY m.created_at DESC'
  ).all(course.id);

  const live_classes = db.prepare(
    'SELECT * FROM live_classes WHERE course_id = ? ORDER BY scheduled_at ASC'
  ).all(course.id);

  res.json({ course, materials, live_classes });
});

// POST /api/courses/:id/enroll - inscribirse (estudiante)
router.post('/:id/enroll', authRequired, requireRole('estudiante'), (req, res) => {
  const course = db.prepare('SELECT * FROM courses WHERE id = ?').get(req.params.id);
  if (!course) return res.status(404).json({ error: 'Curso no encontrado.' });

  const already = db.prepare(
    'SELECT 1 FROM course_enrollments WHERE course_id = ? AND student_id = ?'
  ).get(course.id, req.user.id);
  if (already) return res.status(409).json({ error: 'Ya estás inscrito en este curso.' });

  db.prepare('INSERT INTO course_enrollments (course_id, student_id) VALUES (?, ?)')
    .run(course.id, req.user.id);

  res.status(201).json({ message: 'Inscripción exitosa.' });
});

// GET /api/courses/:id/students - estudiantes de un curso (profesor)
router.get('/:id/students', authRequired, requireRole('profesor'), (req, res) => {
  const course = db.prepare('SELECT * FROM courses WHERE id = ? AND teacher_id = ?')
    .get(req.params.id, req.user.id);
  if (!course) return res.status(404).json({ error: 'Curso no encontrado o no eres el profesor.' });

  const students = db.prepare(
    `SELECT u.id, u.full_name, u.email, ce.enrolled_at FROM course_enrollments ce
     JOIN users u ON u.id = ce.student_id
     WHERE ce.course_id = ? ORDER BY u.full_name`
  ).all(course.id);

  res.json({ students });
});

module.exports = router;
