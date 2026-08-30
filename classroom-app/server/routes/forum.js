'use strict';
// Rutas del foro de discusión por curso
const express = require('express');
const db = require('../db/database');
const { authRequired } = require('../middleware/auth');

const router = express.Router();

// Verifica que el usuario tenga acceso al curso (profesor dueño o estudiante inscrito)
function canAccessCourse(user, course) {
  if (user.role === 'profesor' && course.teacher_id === user.id) return true;
  if (user.role === 'estudiante') {
    return !!db.prepare(
      'SELECT 1 FROM course_enrollments WHERE course_id = ? AND student_id = ?'
    ).get(course.id, user.id);
  }
  return false;
}

// GET /api/forum/course/:courseId - hilos del curso
router.get('/course/:courseId', authRequired, (req, res) => {
  const course = db.prepare('SELECT * FROM courses WHERE id = ?').get(req.params.courseId);
  if (!course) return res.status(404).json({ error: 'Curso no encontrado.' });
  if (!canAccessCourse(req.user, course)) {
    return res.status(403).json({ error: 'No tienes acceso a este curso.' });
  }

  const threads = db.prepare(
    `SELECT t.*, u.full_name AS author_name, u.role AS author_role,
            (SELECT COUNT(*) FROM forum_replies r WHERE r.thread_id = t.id) AS reply_count
     FROM forum_threads t
     JOIN users u ON u.id = t.author_id
     WHERE t.course_id = ?
     ORDER BY t.created_at DESC`
  ).all(course.id);

  res.json({ threads });
});

// POST /api/forum/course/:courseId - crear hilo
router.post('/course/:courseId', authRequired, (req, res) => {
  const course = db.prepare('SELECT * FROM courses WHERE id = ?').get(req.params.courseId);
  if (!course) return res.status(404).json({ error: 'Curso no encontrado.' });
  if (!canAccessCourse(req.user, course)) {
    return res.status(403).json({ error: 'No tienes acceso a este curso.' });
  }

  const { title, content } = req.body || {};
  if (!title || !content) {
    return res.status(400).json({ error: 'Título y contenido son obligatorios.' });
  }

  const result = db.prepare(
    'INSERT INTO forum_threads (course_id, author_id, title, content) VALUES (?, ?, ?, ?)'
  ).run(course.id, req.user.id, title.trim(), content.trim());

  const thread = db.prepare(
    'SELECT t.*, u.full_name AS author_name, u.role AS author_role FROM forum_threads t JOIN users u ON u.id = t.author_id WHERE t.id = ?'
  ).get(result.lastInsertRowid);

  res.status(201).json({ thread });
});

// GET /api/forum/thread/:id - hilo con sus respuestas
router.get('/thread/:id', authRequired, (req, res) => {
  const thread = db.prepare(
    'SELECT t.*, u.full_name AS author_name, u.role AS author_role FROM forum_threads t JOIN users u ON u.id = t.author_id WHERE t.id = ?'
  ).get(req.params.id);
  if (!thread) return res.status(404).json({ error: 'Hilo no encontrado.' });

  const course = db.prepare('SELECT * FROM courses WHERE id = ?').get(thread.course_id);
  if (!canAccessCourse(req.user, course)) {
    return res.status(403).json({ error: 'No tienes acceso a este curso.' });
  }

  const replies = db.prepare(
    `SELECT r.*, u.full_name AS author_name, u.role AS author_role
     FROM forum_replies r JOIN users u ON u.id = r.author_id
     WHERE r.thread_id = ? ORDER BY r.created_at ASC`
  ).all(thread.id);

  res.json({ thread, replies });
});

// POST /api/forum/thread/:id/reply - responder hilo
router.post('/thread/:id/reply', authRequired, (req, res) => {
  const thread = db.prepare('SELECT * FROM forum_threads WHERE id = ?').get(req.params.id);
  if (!thread) return res.status(404).json({ error: 'Hilo no encontrado.' });

  const course = db.prepare('SELECT * FROM courses WHERE id = ?').get(thread.course_id);
  if (!canAccessCourse(req.user, course)) {
    return res.status(403).json({ error: 'No tienes acceso a este curso.' });
  }

  const { content } = req.body || {};
  if (!content) return res.status(400).json({ error: 'El contenido de la respuesta es obligatorio.' });

  const result = db.prepare(
    'INSERT INTO forum_replies (thread_id, author_id, content) VALUES (?, ?, ?)'
  ).run(thread.id, req.user.id, content.trim());

  const reply = db.prepare(
    'SELECT r.*, u.full_name AS author_name, u.role AS author_role FROM forum_replies r JOIN users u ON u.id = r.author_id WHERE r.id = ?'
  ).get(result.lastInsertRowid);

  res.status(201).json({ reply });
});

// DELETE /api/forum/thread/:id - eliminar hilo (autor o profesor del curso)
router.delete('/thread/:id', authRequired, (req, res) => {
  const thread = db.prepare('SELECT * FROM forum_threads WHERE id = ?').get(req.params.id);
  if (!thread) return res.status(404).json({ error: 'Hilo no encontrado.' });

  const course = db.prepare('SELECT * FROM courses WHERE id = ?').get(thread.course_id);
  const isAuthor = thread.author_id === req.user.id;
  const isTeacher = course && course.teacher_id === req.user.id;

  if (!isAuthor && !isTeacher) {
    return res.status(403).json({ error: 'Solo el autor o el profesor del curso pueden eliminar.' });
  }

  db.prepare('DELETE FROM forum_replies WHERE thread_id = ?').run(thread.id);
  db.prepare('DELETE FROM forum_threads WHERE id = ?').run(thread.id);
  res.json({ message: 'Hilo eliminado.' });
});

// DELETE /api/forum/reply/:id - eliminar respuesta (autor o profesor del curso)
router.delete('/reply/:id', authRequired, (req, res) => {
  const reply = db.prepare('SELECT * FROM forum_replies WHERE id = ?').get(req.params.id);
  if (!reply) return res.status(404).json({ error: 'Respuesta no encontrada.' });

  const thread = db.prepare('SELECT * FROM forum_threads WHERE id = ?').get(reply.thread_id);
  const course = thread ? db.prepare('SELECT * FROM courses WHERE id = ?').get(thread.course_id) : null;
  const isAuthor = reply.author_id === req.user.id;
  const isTeacher = course && course.teacher_id === req.user.id;

  if (!isAuthor && !isTeacher) {
    return res.status(403).json({ error: 'Solo el autor o el profesor del curso pueden eliminar.' });
  }

  db.prepare('DELETE FROM forum_replies WHERE id = ?').run(reply.id);
  res.json({ message: 'Respuesta eliminada.' });
});

module.exports = router;
