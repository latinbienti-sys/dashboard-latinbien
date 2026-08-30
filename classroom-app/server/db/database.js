'use strict';
// Base de datos SQLite usando el módulo integrado de Node 24 (node:sqlite)
const { DatabaseSync } = require('node:sqlite');
const path = require('path');
const fs = require('fs');
const bcrypt = require('bcryptjs');

const DB_PATH = path.join(__dirname, 'classroom.db');

// Crear directorio de uploads si no existe
const UPLOADS_DIR = path.join(__dirname, '..', 'uploads');
if (!fs.existsSync(UPLOADS_DIR)) {
  fs.mkdirSync(UPLOADS_DIR, { recursive: true });
}

const db = new DatabaseSync(DB_PATH);

// Habilitar foreign keys
db.exec('PRAGMA foreign_keys = ON;');

// ============================================================
// ESQUEMA DE BASE DE DATOS
// ============================================================
db.exec(`
CREATE TABLE IF NOT EXISTS users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name     TEXT NOT NULL,
  email         TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role          TEXT NOT NULL CHECK (role IN ('profesor', 'estudiante')),
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS courses (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  title       TEXT NOT NULL,
  description TEXT,
  teacher_id  INTEGER NOT NULL REFERENCES users(id),
  price       REAL NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS course_enrollments (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id   INTEGER NOT NULL REFERENCES courses(id),
  student_id  INTEGER NOT NULL REFERENCES users(id),
  enrolled_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (course_id, student_id)
);

CREATE TABLE IF NOT EXISTS materials (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id   INTEGER NOT NULL REFERENCES courses(id),
  title       TEXT NOT NULL,
  description TEXT,
  file_name   TEXT NOT NULL,
  file_path   TEXT NOT NULL,
  file_size   INTEGER NOT NULL DEFAULT 0,
  uploaded_by INTEGER NOT NULL REFERENCES users(id),
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS live_classes (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id   INTEGER NOT NULL REFERENCES courses(id),
  title       TEXT NOT NULL,
  description TEXT,
  room_name   TEXT NOT NULL,
  scheduled_at TEXT NOT NULL,
  duration_min INTEGER NOT NULL DEFAULT 60,
  created_by  INTEGER NOT NULL REFERENCES users(id),
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS grades (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id   INTEGER NOT NULL REFERENCES courses(id),
  student_id  INTEGER NOT NULL REFERENCES users(id),
  activity    TEXT NOT NULL,
  score       REAL NOT NULL CHECK (score >= 0 AND score <= 100),
  max_score   REAL NOT NULL DEFAULT 100,
  graded_by   INTEGER NOT NULL REFERENCES users(id),
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (course_id, student_id, activity)
);

CREATE TABLE IF NOT EXISTS payments (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id  INTEGER NOT NULL REFERENCES users(id),
  course_id   INTEGER NOT NULL REFERENCES courses(id),
  amount      REAL NOT NULL,
  method      TEXT NOT NULL DEFAULT 'tarjeta',
  status      TEXT NOT NULL DEFAULT 'pagado',
  reference   TEXT NOT NULL UNIQUE,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS forum_threads (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id   INTEGER NOT NULL REFERENCES courses(id),
  author_id   INTEGER NOT NULL REFERENCES users(id),
  title       TEXT NOT NULL,
  content     TEXT NOT NULL,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS forum_replies (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id   INTEGER NOT NULL REFERENCES forum_threads(id),
  author_id   INTEGER NOT NULL REFERENCES users(id),
  content     TEXT NOT NULL,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
`);

// ============================================================
// DATOS SEMILLA (solo si la base está vacía)
// ============================================================
function seedIfEmpty() {
  const userCount = db.prepare('SELECT COUNT(*) AS c FROM users').get().c;
  if (userCount > 0) return;

  console.log('🌱 Sembrando datos iniciales...');

  const passProf = bcrypt.hashSync('profesor123', 10);
  const passEst  = bcrypt.hashSync('estudiante123', 10);

  const prof = db.prepare(
    'INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)'
  ).run('Prof. María González', 'profesor@classroom.com', passProf, 'profesor');

  const est = db.prepare(
    'INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)'
  ).run('Carlos Pérez', 'estudiante@classroom.com', passEst, 'estudiante');

  // Curso de ejemplo
  const course = db.prepare(
    'INSERT INTO courses (title, description, teacher_id, price) VALUES (?, ?, ?, ?)'
  ).run(
    'Programación Web desde Cero',
    'Aprende HTML, CSS y JavaScript construyendo proyectos reales.',
    prof.lastInsertRowid,
    149.99
  );

  db.prepare('INSERT INTO course_enrollments (course_id, student_id) VALUES (?, ?)')
    .run(course.lastInsertRowid, est.lastInsertRowid);

  // Clase en vivo de ejemplo (fecha +1 día)
  const tomorrow = new Date(Date.now() + 24 * 3600 * 1000);
  const iso = tomorrow.toISOString();
  db.prepare(
    'INSERT INTO live_classes (course_id, title, description, room_name, scheduled_at, duration_min, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)'
  ).run(
    course.lastInsertRowid,
    'Clase 1: Introducción a HTML',
    'Primera clase en vivo del curso.',
    `html-intro-${Date.now()}`,
    iso,
    60,
    prof.lastInsertRowid
  );

  // Nota de ejemplo
  db.prepare(
    'INSERT INTO grades (course_id, student_id, activity, score, max_score, graded_by) VALUES (?, ?, ?, ?, ?, ?)'
  ).run(course.lastInsertRowid, est.lastInsertRowid, 'Examen 1', 92, 100, prof.lastInsertRowid);

  // Pago de ejemplo
  db.prepare(
    'INSERT INTO payments (student_id, course_id, amount, method, status, reference) VALUES (?, ?, ?, ?, ?, ?)'
  ).run(
    est.lastInsertRowid,
    course.lastInsertRowid,
    149.99,
    'tarjeta',
    'pagado',
    `PAY-${Date.now()}`
  );

  console.log('✅ Usuarios demo creados:');
  console.log('   Profesor:   profesor@classroom.com / profesor123');
  console.log('   Estudiante: estudiante@classroom.com / estudiante123');
}

seedIfEmpty();

module.exports = db;
