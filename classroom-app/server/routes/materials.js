'use strict';
// Rutas de material didáctico (subida/descarga de archivos)
const express = require('express');
const path = require('path');
const fs = require('fs');
const multer = require('multer');
const db = require('../db/database');
const { authRequired, requireRole } = require('../middleware/auth');

const router = express.Router();

const UPLOADS_DIR = path.join(__dirname, '..', 'uploads');

// Configuración de multer
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, UPLOADS_DIR),
  filename: (req, file, cb) => {
    const safeName = file.originalname.replace(/[^a-zA-Z0-9._-]/g, '_');
    cb(null, `${Date.now()}-${safeName}`);
  }
});

const upload = multer({
  storage,
  limits: { fileSize: 50 * 1024 * 1024 } // 50 MB máx
});

// POST /api/materials/:courseId - subir material (solo profesor del curso)
router.post('/:courseId', authRequired, requireRole('profesor'), upload.single('file'), (req, res) => {
  const course = db.prepare('SELECT * FROM courses WHERE id = ? AND teacher_id = ?')
    .get(req.params.courseId, req.user.id);

  if (!course) {
    // Eliminar archivo subido si el curso no es válido
    if (req.file) fs.unlink(req.file.path, () => {});
    return res.status(403).json({ error: 'Curso no encontrado o no eres el profesor.' });
  }

  const { title, description } = req.body || {};

  if (!req.file) {
    return res.status(400).json({ error: 'Debes adjuntar un archivo.' });
  }

  const result = db.prepare(
    `INSERT INTO materials (course_id, title, description, file_name, file_path, file_size, uploaded_by)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  ).run(
    course.id,
    title || req.file.originalname,
    description || '',
    req.file.originalname,
    path.relative(process.cwd(), req.file.path),
    req.file.size,
    req.user.id
  );

  const material = db.prepare('SELECT * FROM materials WHERE id = ?').get(result.lastInsertRowid);
  res.status(201).json({ material });
});

// GET /api/materials/:id/download - descargar material (estudiantes inscritos o profesor)
router.get('/:id/download', authRequired, (req, res) => {
  const material = db.prepare('SELECT * FROM materials WHERE id = ?').get(req.params.id);
  if (!material) return res.status(404).json({ error: 'Material no encontrado.' });

  const course = db.prepare('SELECT * FROM courses WHERE id = ?').get(material.course_id);

  let allowed = false;
  if (req.user.role === 'profesor' && course.teacher_id === req.user.id) allowed = true;
  if (req.user.role === 'estudiante') {
    const enrolled = db.prepare(
      'SELECT 1 FROM course_enrollments WHERE course_id = ? AND student_id = ?'
    ).get(material.course_id, req.user.id);
    allowed = !!enrolled;
  }
  if (!allowed) return res.status(403).json({ error: 'No tienes acceso a este material.' });

  const fullPath = path.resolve(process.cwd(), material.file_path);
  if (!fs.existsSync(fullPath)) {
    return res.status(404).json({ error: 'El archivo ya no existe en el servidor.' });
  }

  res.download(fullPath, material.file_name);
});

// DELETE /api/materials/:id - eliminar material (solo profesor del curso)
router.delete('/:id', authRequired, requireRole('profesor'), (req, res) => {
  const material = db.prepare('SELECT * FROM materials WHERE id = ?').get(req.params.id);
  if (!material) return res.status(404).json({ error: 'Material no encontrado.' });

  const course = db.prepare('SELECT * FROM courses WHERE id = ?').get(material.course_id);
  if (!course || course.teacher_id !== req.user.id) {
    return res.status(403).json({ error: 'No eres el profesor de este curso.' });
  }

  db.prepare('DELETE FROM materials WHERE id = ?').run(material.id);
  fs.unlink(path.resolve(process.cwd(), material.file_path), () => {});
  res.json({ message: 'Material eliminado.' });
});

module.exports = router;
