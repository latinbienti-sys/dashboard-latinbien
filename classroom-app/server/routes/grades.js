'use strict';
// Rutas de notas y calificaciones
const express = require('express');
const db = require('../db/database');
const { authRequired, requireRole } = require('../middleware/auth');

const router = express.Router();

// GET /api/grades/course/:courseId/student/:studentId - notas de un estudiante
// Profesor: puede consultar a cualquier estudiante de su curso
// Estudiante: solo puede consultar sus propias notas
router.get('/course/:courseId/student/:studentId', authRequired, (req, res) => {
  const courseId = Number(req.params.courseId);
  const studentId = Number(req.params.studentId);

  const course = db.prepare('SELECT * FROM courses WHERE id = ?').get(courseId);
  if (!course) return res.status(404).json({ error: 'Curso no encontrado.' });

  let allowed = false;
  if (req.user.role === 'profesor' && course.teacher_id === req.user.id) allowed = true;
  if (req.user.role === 'estudiante' && req.user.id === studentId) {
    const enrolled = db.prepare(
      'SELECT 1 FROM course_enrollments WHERE course_id = ? AND student_id = ?'
    ).get(courseId, studentId);
    allowed = !!enrolled;
  }
  if (!allowed) return res.status(403).json({ error: 'No tienes acceso a estas notas.' });

  const grades = db.prepare(
    'SELECT * FROM grades WHERE course_id = ? AND student_id = ? ORDER BY created_at DESC'
  ).all(courseId, studentId);

  res.json({ grades });
});

// POST /api/grades - registrar/actualizar nota (solo profesor)
router.post('/', authRequired, requireRole('profesor'), (req, res) => {
  const { course_id, student_id, activity, score, max_score } = req.body || {};

  if (!course_id || !student_id || !activity || score === undefined) {
    return res.status(400).json({ error: 'Curso, estudiante, actividad y nota son obligatorios.' });
  }

  const course = db.prepare('SELECT * FROM courses WHERE id = ? AND teacher_id = ?')
    .get(course_id, req.user.id);
  if (!course) {
    return res.status(403).json({ error: 'Curso no encontrado o no eres el profesor.' });
  }

  const enrolled = db.prepare(
    'SELECT 1 FROM course_enrollments WHERE course_id = ? AND student_id = ?'
  ).get(course_id, student_id);
  if (!enrolled) {
    return res.status(400).json({ error: 'El estudiante no está inscrito en este curso.' });
  }

  const finalMax = parseFloat(max_score) || 100;
  const finalScore = Math.min(Math.max(parseFloat(score), 0), finalMax);

  // Upsert: si ya existe la actividad para ese estudiante, se actualiza
  const existing = db.prepare(
    'SELECT id FROM grades WHERE course_id = ? AND student_id = ? AND activity = ?'
  ).get(course_id, student_id, activity);

  if (existing) {
    db.prepare('UPDATE grades SET score = ?, max_score = ? WHERE id = ?')
      .run(finalScore, finalMax, existing.id);
  } else {
    db.prepare(
      `INSERT INTO grades (course_id, student_id, activity, score, max_score, graded_by)
       VALUES (?, ?, ?, ?, ?, ?)`
    ).run(course_id, student_id, activity.trim(), finalScore, finalMax, req.user.id);
  }

  const grades = db.prepare(
    'SELECT * FROM grades WHERE course_id = ? AND student_id = ? ORDER BY created_at DESC'
  ).all(course_id, student_id);

  res.json({ grades, message: 'Nota registrada correctamente.' });
});

// DELETE /api/grades/:id - eliminar nota (solo profesor del curso)
router.delete('/:id', authRequired, requireRole('profesor'), (req, res) => {
  const grade = db.prepare('SELECT * FROM grades WHERE id = ?').get(req.params.id);
  if (!grade) return res.status(404).json({ error: 'Nota no encontrada.' });

  const course = db.prepare('SELECT * FROM courses WHERE id = ?').get(grade.course_id);
  if (!course || course.teacher_id !== req.user.id) {
    return res.status(403).json({ error: 'No eres el profesor de este curso.' });
  }

  db.prepare('DELETE FROM grades WHERE id = ?').run(grade.id);
  res.json({ message: 'Nota eliminada.' });
});

// GET /api/grades/my - mis notas en todos mis cursos (estudiante)
router.get('/my', authRequired, requireRole('estudiante'), (req, res) => {
  const rows = db.prepare(
    `SELECT g.*, c.title AS course_title FROM grades g
     JOIN courses c ON c.id = g.course_id
     WHERE g.student_id = ? ORDER BY g.created_at DESC`
  ).all(req.user.id);

  res.json({ grades: rows });
});

module.exports = router;
