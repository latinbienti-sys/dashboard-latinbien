'use strict';
// Servidor principal de la plataforma Classroom
require('dotenv').config();
const path = require('path');
const express = require('express');
const cors = require('cors');

// Rutas
const authRoutes = require('./routes/auth');
const courseRoutes = require('./routes/courses');
const materialRoutes = require('./routes/materials');
const liveClassRoutes = require('./routes/liveClasses');
const gradeRoutes = require('./routes/grades');
const paymentRoutes = require('./routes/payments');
const forumRoutes = require('./routes/forum');

const app = express();
const PORT = process.env.PORT || 3000;

// Middlewares
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// API routes
app.use('/api/auth', authRoutes);
app.use('/api/courses', courseRoutes);
app.use('/api/materials', materialRoutes);
app.use('/api/live-classes', liveClassRoutes);
app.use('/api/grades', gradeRoutes);
app.use('/api/payments', paymentRoutes);
app.use('/api/forum', forumRoutes);

// Archivos subidos servidos estáticamente (con auth para protegerlos se usa /download)
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// Frontend estático
app.use(express.static(path.join(__dirname, '..', 'public')));

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', time: new Date().toISOString() });
});

// Manejo de errores 404 para API
app.use('/api', (req, res) => {
  res.status(404).json({ error: 'Ruta no encontrada.' });
});

// Middleware de errores
app.use((err, req, res, next) => {
  console.error('❌ Error:', err.message);
  if (err.name === 'MulterError') {
    return res.status(400).json({ error: `Error al subir archivo: ${err.message}` });
  }
  res.status(500).json({ error: 'Error interno del servidor.' });
});

app.listen(PORT, () => {
  console.log('============================================');
  console.log('🎓  PLATAFORMA CLASSROOM  🎓');
  console.log('============================================');
  console.log(`✅ Servidor en:  http://localhost:${PORT}`);
  console.log(`✅ API en:       http://localhost:${PORT}/api/health`);
  console.log('');
  console.log('👤 Usuarios demo:');
  console.log('   Profesor:   profesor@classroom.com / profesor123');
  console.log('   Estudiante: estudiante@classroom.com / estudiante123');
  console.log('============================================');
});
