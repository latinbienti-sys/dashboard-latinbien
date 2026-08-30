'use strict';
/* ============================================================
   ClassRoom - Lógica del frontend
   ============================================================ */

let currentUser = null;
let currentCourseId = null; // curso seleccionado en Material/Clases/Notas

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d)) return '';
  return d.toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatDateTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d)) return '';
  return d.toLocaleString('es-ES', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}

function formatMoney(n) {
  return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(n || 0);
}

function toast(msg, type = 'success') {
  const el = $('#toast');
  el.textContent = msg;
  el.className = 'toast show ' + type;
  setTimeout(() => { el.className = 'toast ' + type; }, 3000);
}

function showError(msg) {
  const el = $('#auth-error');
  if (el) { el.textContent = msg; el.style.display = 'block'; }
}

function hideError() {
  const el = $('#auth-error');
  if (el) el.style.display = 'none';
}

/* ============================================================
   AUTENTICACIÓN
   ============================================================ */

function showAuthScreen() {
  $('#auth-screen').style.display = 'flex';
  $('#app-screen').style.display = 'none';
}

function showAppScreen() {
  $('#auth-screen').style.display = 'none';
  $('#app-screen').style.display = 'flex';
}

function setUserInfo(user) {
  currentUser = user;
  $('#user-name').textContent = user.full_name;
  $('#user-avatar').textContent = user.role === 'profesor' ? '👨‍🏫' : '👨‍🎓';
  const roleEl = $('#user-role');
  roleEl.textContent = user.role;
  roleEl.className = 'badge ' + (user.role === 'profesor' ? 'badge-blue' : 'badge-green');
}

async function handleLogin(email, password) {
  try {
    const data = await API.post('/api/auth/login', { email, password });
    API.setToken(data.token);
    setUserInfo(data.user);
    showAppScreen();
    navigate('dashboard');
    toast('¡Bienvenido, ' + data.user.full_name + '! 👋');
  } catch (e) {
    showError(e.message);
  }
}

async function handleRegister(full_name, email, password, role) {
  try {
    const data = await API.post('/api/auth/register', { full_name, email, password, role });
    API.setToken(data.token);
    setUserInfo(data.user);
    showAppScreen();
    navigate('dashboard');
    toast('¡Cuenta creada! Bienvenido 🎉');
  } catch (e) {
    showError(e.message);
  }
}

function logout() {
  API.clearToken();
  currentUser = null;
  showAuthScreen();
}

/* ============================================================
   NAVEGACIÓN
   ============================================================ */

function navigate(view) {
  $$('.nav-link').forEach((l) => l.classList.remove('active'));
  const link = document.querySelector(`.nav-link[data-view="${view}"]`);
  if (link) link.classList.add('active');

  $$('.view').forEach((v) => (v.style.display = 'none'));
  const target = $('#view-' + view);
  target.style.display = 'block';

  const titles = {
    dashboard: 'Dashboard',
    courses: 'Cursos',
    materials: 'Material de Estudio',
    live: 'Clases en Vivo',
    grades: 'Notas y Calificaciones',
    payments: 'Pagos',
    forum: 'Foro de Discusión'
  };
  $('#view-title').textContent = titles[view] || 'ClassRoom';

  switch (view) {
    case 'dashboard': renderDashboard(); break;
    case 'courses': renderCourses(); break;
    case 'materials': renderMaterials(); break;
    case 'live': renderLive(); break;
    case 'grades': renderGrades(); break;
    case 'payments': renderPayments(); break;
    case 'forum': renderForum(); break;
  }
}

/* ============================================================
   MODAL
   ============================================================ */

function openModal(html) {
  $('#modal-content').innerHTML = html;
  $('#modal-overlay').style.display = 'flex';
}

function closeModal() {
  $('#modal-overlay').style.display = 'none';
}

/* ============================================================
   DASHBOARD
   ============================================================ */

async function renderDashboard() {
  const el = $('#view-dashboard');
  if (currentUser.role === 'profesor') {
    await renderDashboardProfesor(el);
  } else {
    await renderDashboardEstudiante(el);
  }
}

async function renderDashboardProfesor(el) {
  try {
    const data = await API.get('/api/courses');
    const courses = data.courses || [];

    // Obtener estudiantes e ingresos por curso
    let totalStudents = 0;
    let totalRevenue = 0;
    const stats = await Promise.all(courses.map(async (c) => {
      try {
        const students = await API.get(`/api/courses/${c.id}/students`);
        const pays = await API.get(`/api/payments/course/${c.id}`);
        const sCount = (students.students || []).length;
        const rev = pays.total || 0;
        totalStudents += sCount;
        totalRevenue += rev;
        return { id: c.id, sCount, rev };
      } catch (e) { return { id: c.id, sCount: 0, rev: 0 }; }
    }));

    const html = `
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-icon">📚</div>
          <div class="stat-value">${courses.length}</div>
          <div class="stat-label">Mis cursos</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">👨‍🎓</div>
          <div class="stat-value">${totalStudents}</div>
          <div class="stat-label">Estudiantes totales</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">💵</div>
          <div class="stat-value">${formatMoney(totalRevenue)}</div>
          <div class="stat-label">Ingresos por pagos</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">🏆</div>
          <div class="stat-value">${stats.reduce((a, s) => a + s.sCount, 0)}</div>
          <div class="stat-label">Matrículas</div>
        </div>
      </div>
      <div class="card">
        <div class="card-title">📚 Mis cursos</div>
        ${courses.length === 0
          ? '<div class="empty-state"><div class="empty-icon">📚</div><p>Aún no tienes cursos. Crea el primero.</p><button class="btn btn-primary mt-16" onclick="openCreateCourseModal()">+ Crear curso</button></div>'
          : `<div class="grid">${courses.map((c) => `
              <div class="course-card">
                <h3>${escapeHtml(c.title)}</h3>
                <p>${escapeHtml(c.description || 'Sin descripción')}</p>
                <div class="course-meta">
                  <span class="badge badge-blue">${formatMoney(c.price)}</span>
                </div>
                <div class="course-actions">
                  <button class="btn btn-outline btn-sm" onclick="goCourse('${c.id}')">Ver curso</button>
                </div>
              </div>`).join('')}
            </div>
            <button class="btn btn-primary mt-16" onclick="openCreateCourseModal()">+ Nuevo curso</button>`}
      </div>`;
    el.innerHTML = html;
  } catch (e) {
    el.innerHTML = `<div class="alert alert-error">${escapeHtml(e.message)}</div>`;
  }
}

async function renderDashboardEstudiante(el) {
  try {
    const [coursesData, gradesData, paymentsData] = await Promise.all([
      API.get('/api/courses'),
      API.get('/api/grades/my'),
      API.get('/api/payments/my')
    ]);
    const courses = coursesData.courses || [];
    const grades = gradesData.grades || [];
    const payments = paymentsData.payments || [];

    // Promedio de notas
    const pct = grades.map((g) => (g.score / g.max_score) * 100);
    const avg = pct.length ? (pct.reduce((a, b) => a + b, 0) / pct.length).toFixed(1) : '—';

    // Próximas clases
    let nextClass = null;
    try {
      for (const c of courses) {
        const live = await API.get(`/api/live-classes/course/${c.id}`);
        const upcoming = (live.live_classes || []).filter((lc) => new Date(lc.scheduled_at) > new Date());
        if (upcoming.length) {
          const first = upcoming.sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))[0];
          if (!nextClass || new Date(first.scheduled_at) < new Date(nextClass.scheduled_at)) {
            nextClass = { ...first, course_title: c.title };
          }
        }
      }
    } catch (e) { /* ignorar */ }

    const totalSpent = payments.reduce((a, p) => a + p.amount, 0);

    const html = `
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-icon">📚</div>
          <div class="stat-value">${courses.length}</div>
          <div class="stat-label">Cursos inscritos</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">📝</div>
          <div class="stat-value">${avg}%</div>
          <div class="stat-label">Promedio de notas</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">💳</div>
          <div class="stat-value">${formatMoney(totalSpent)}</div>
          <div class="stat-label">Inversión en educación</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">🎥</div>
          <div class="stat-value">${nextClass ? 'Próxima' : '—'}</div>
          <div class="stat-label">${nextClass ? formatDateTime(nextClass.scheduled_at) : 'Sin clases próximas'}</div>
        </div>
      </div>
      <div class="card">
        <div class="card-title">📚 Mis cursos</div>
        ${courses.length === 0
          ? '<div class="empty-state"><div class="empty-icon">📚</div><p>No estás inscrito en ningún curso.</p><button class="btn btn-primary mt-16" onclick="navigate(\'courses\')">Ver catálogo</button></div>'
          : `<div class="grid">${courses.map((c) => `
              <div class="course-card">
                <h3>${escapeHtml(c.title)}</h3>
                <p>${escapeHtml(c.description || '')}</p>
                <div class="course-meta">
                  <span class="badge badge-green">👨‍🏫 ${escapeHtml(c.teacher_name || '')}</span>
                </div>
                <div class="course-actions">
                  <button class="btn btn-outline btn-sm" onclick="goCourse('${c.id}')">Ver curso</button>
                </div>
              </div>`).join('')}
            </div>`}
      </div>`;
    el.innerHTML = html;
  } catch (e) {
    el.innerHTML = `<div class="alert alert-error">${escapeHtml(e.message)}</div>`;
  }
}

/* ============================================================
   CURSOS
   ============================================================ */

async function renderCourses() {
  const el = $('#view-courses');
  try {
    if (currentUser.role === 'profesor') {
      const data = await API.get('/api/courses');
      const courses = data.courses || [];
      el.innerHTML = `
        <div class="card">
          <div class="card-title">📚 Mis cursos</div>
          ${courses.length === 0
            ? '<div class="empty-state"><p>Aún no tienes cursos.</p></div>'
            : `<div class="grid">${courses.map((c) => `
                <div class="course-card">
                  <h3>${escapeHtml(c.title)}</h3>
                  <p>${escapeHtml(c.description || '')}</p>
                  <div class="course-meta"><span class="badge badge-blue">${formatMoney(c.price)}</span></div>
                  <div class="course-actions">
                    <button class="btn btn-outline btn-sm" onclick="goCourse('${c.id}')">Gestionar</button>
                  </div>
                </div>`).join('')}
              </div>`}
          <button class="btn btn-primary mt-16" onclick="openCreateCourseModal()">+ Crear curso</button>
        </div>`;
    } else {
      // Estudiante: catálogo + mis cursos
      const [mine, catalog] = await Promise.all([
        API.get('/api/courses'),
        API.get('/api/courses/catalog')
      ]);
      const myIds = new Set((mine.courses || []).map((c) => c.id));
      const catalogCourses = (catalog.courses || []).filter((c) => !myIds.has(c.id));

      el.innerHTML = `
        <div class="card">
          <div class="card-title">🗂️ Catálogo de cursos disponibles</div>
          ${catalogCourses.length === 0
            ? '<div class="empty-state"><div class="empty-icon">📚</div><p>Ya estás inscrito en todos los cursos disponibles.</p></div>'
            : `<div class="grid">${catalogCourses.map((c) => `
                <div class="course-card">
                  <h3>${escapeHtml(c.title)}</h3>
                  <p>${escapeHtml(c.description || '')}</p>
                  <div class="course-meta">
                    <span class="badge badge-green">👨‍🏫 ${escapeHtml(c.teacher_name || '')}</span>
                    <span class="badge badge-blue">${formatMoney(c.price)}</span>
                  </div>
                  <div class="course-actions">
                    <button class="btn btn-primary btn-sm" onclick="openPayModal(${c.id}, '${escapeHtml(c.title)}', ${c.price})">💳 Inscribirme y pagar</button>
                  </div>
                </div>`).join('')}
              </div>`}
        </div>
        <div class="card mt-16">
          <div class="card-title">✅ Mis cursos</div>
          ${(mine.courses || []).length === 0
            ? '<div class="empty-state"><p>No estás inscrito en ningún curso aún.</p></div>'
            : `<div class="grid">${(mine.courses || []).map((c) => `
                <div class="course-card">
                  <h3>${escapeHtml(c.title)}</h3>
                  <p>${escapeHtml(c.description || '')}</p>
                  <div class="course-meta"><span class="badge badge-green">👨‍🏫 ${escapeHtml(c.teacher_name || '')}</span></div>
                  <div class="course-actions">
                    <button class="btn btn-outline btn-sm" onclick="goCourse('${c.id}')">Entrar</button>
                  </div>
                </div>`).join('')}
              </div>`}
        </div>`;
    }
  } catch (e) {
    el.innerHTML = `<div class="alert alert-error">${escapeHtml(e.message)}</div>`;
  }
}

function openCreateCourseModal() {
  openModal(`
    <h3 style="margin-bottom:16px;">📚 Crear nuevo curso</h3>
    <form id="create-course-form">
      <div class="form-group">
        <label>Título del curso *</label>
        <input type="text" id="cc-title" required placeholder="Ej: Introducción a Python" />
      </div>
      <div class="form-group">
        <label>Descripción</label>
        <textarea id="cc-description" rows="3" placeholder="¿Qué aprenderán los estudiantes?"></textarea>
      </div>
      <div class="form-group">
        <label>Precio (MXN)</label>
        <input type="number" id="cc-price" step="0.01" min="0" value="99" />
      </div>
      <button type="submit" class="btn btn-primary btn-block">Crear curso</button>
    </form>
  `);
  $('#create-course-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      await API.post('/api/courses', {
        title: $('#cc-title').value,
        description: $('#cc-description').value,
        price: parseFloat($('#cc-price').value) || 0
      });
      closeModal();
      toast('Curso creado exitosamente 🎉');
      renderCourses();
    } catch (err) {
      toast(err.message, 'error');
    }
  });
}

function goCourse(courseId) {
  currentCourseId = Number(courseId);
  // Mostrar vista de detalle del curso
  openCourseDetail(courseId);
}

async function openCourseDetail(courseId) {
  try {
    const data = await API.get(`/api/courses/${courseId}`);
    const { course, materials, live_classes } = data;

    let html = `
      <div class="flex-between" style="margin-bottom:16px;">
        <h3>${escapeHtml(course.title)}</h3>
        <button class="btn btn-ghost btn-sm" onclick="closeModal()">Cerrar</button>
      </div>
      <p class="text-muted mb-16">${escapeHtml(course.description || '')}</p>
      <div class="flex mb-16">
        <span class="badge badge-blue">${formatMoney(course.price)}</span>
        <span class="badge badge-green">👨‍🏫 ${escapeHtml(course.teacher_name || '')}</span>
      </div>
      <div class="flex" style="flex-wrap:wrap; margin-bottom:16px;">
        ${currentUser.role === 'profesor'
          ? `<button class="btn btn-outline btn-sm" onclick="openUploadMaterialModal(${course.id})">📎 Subir material</button>
             <button class="btn btn-outline btn-sm" onclick="openCreateClassModal(${course.id})">🎥 Programar clase</button>
             <button class="btn btn-outline btn-sm" onclick="openGradeStudentsModal(${course.id})">📝 Notas</button>`
          : `<button class="btn btn-outline btn-sm" onclick="navigate('materials'); goMaterialsCourse(${course.id})">📎 Ver material</button>
             <button class="btn btn-outline btn-sm" onclick="navigate('live'); goLiveCourse(${course.id})">🎥 Ver clases</button>
             <button class="btn btn-outline btn-sm" onclick="navigate('grades'); goGradesCourse(${course.id})">📝 Mis notas</button>`}
      </div>`;

    if (materials.length) {
      html += `<div class="card-title" style="margin-top:16px;">📎 Material (${materials.length})</div>`;
      html += materials.map((m) => `
        <div class="list-item">
          <div class="item-icon">📄</div>
          <div class="item-body">
            <div class="item-title">${escapeHtml(m.title)}</div>
            <div class="item-sub">${escapeHtml(m.file_name)} · ${(m.file_size / 1024).toFixed(0)} KB</div>
          </div>
          <div class="item-actions">
            <button class="btn btn-primary btn-sm" onclick="downloadMaterial(${m.id})">⬇️ Descargar</button>
          </div>
        </div>`).join('');
    }

    if (live_classes.length) {
      html += `<div class="card-title" style="margin-top:16px;">🎥 Clases programadas (${live_classes.length})</div>`;
      html += live_classes.map((lc) => `
        <div class="list-item">
          <div class="item-icon">🎥</div>
          <div class="item-body">
            <div class="item-title">${escapeHtml(lc.title)}</div>
            <div class="item-sub">${formatDateTime(lc.scheduled_at)} · ${lc.duration_min} min</div>
          </div>
          <div class="item-actions">
            <button class="btn btn-success btn-sm" onclick="joinLiveClass(${lc.id})">▶️ Entrar</button>
          </div>
        </div>`).join('');
    }

    openModal(html);
  } catch (e) {
    toast(e.message, 'error');
  }
}

/* ============================================================
   MATERIAL
   ============================================================ */

async function renderMaterials() {
  const el = $('#view-materials');
  try {
    const data = await API.get('/api/courses');
    const courses = data.courses || [];

    if (courses.length === 0) {
      el.innerHTML = `<div class="empty-state"><div class="empty-icon">📎</div><p>No tienes cursos para ver material.</p></div>`;
      return;
    }

    const cards = await Promise.all(courses.map(async (c) => {
      try {
        const det = await API.get(`/api/courses/${c.id}`);
        const mats = (det.materials || []).map((m) => `
          <div class="list-item">
            <div class="item-icon">📄</div>
            <div class="item-body">
              <div class="item-title">${escapeHtml(m.title)}</div>
              <div class="item-sub">${escapeHtml(m.file_name)} · ${(m.file_size / 1024).toFixed(0)} KB · ${formatDate(m.created_at)}</div>
            </div>
            <div class="item-actions">
              <button class="btn btn-primary btn-sm" onclick="downloadMaterial(${m.id})">⬇️</button>
              ${currentUser.role === 'profesor' ? `<button class="btn btn-danger btn-sm" onclick="deleteMaterial(${m.id})">🗑️</button>` : ''}
            </div>
          </div>`).join('');
        return `
          <div class="card">
            <div class="card-title">${escapeHtml(c.title)}
              ${currentUser.role === 'profesor' ? `<button class="btn btn-outline btn-sm" onclick="openUploadMaterialModal(${c.id})">+ Subir</button>` : ''}
            </div>
            ${mats || '<div class="text-muted text-small">Sin material aún.</div>'}
          </div>`;
      } catch (e) {
        return `<div class="card"><div class="card-title">${escapeHtml(c.title)}</div><div class="text-muted text-small">No disponible.</div></div>`;
      }
    }));

    el.innerHTML = cards.join('');
  } catch (e) {
    el.innerHTML = `<div class="alert alert-error">${escapeHtml(e.message)}</div>`;
  }
}

function openUploadMaterialModal(courseId) {
  openModal(`
    <h3 style="margin-bottom:16px;">📎 Subir material</h3>
    <form id="upload-material-form" enctype="multipart/form-data">
      <div class="form-group">
        <label>Título</label>
        <input type="text" id="um-title" placeholder="Nombre del material" />
      </div>
      <div class="form-group">
        <label>Descripción</label>
        <input type="text" id="um-description" placeholder="Descripción corta" />
      </div>
      <div class="form-group">
        <label>Archivo *</label>
        <input type="file" id="um-file" required />
      </div>
      <button type="submit" class="btn btn-primary btn-block">Subir material</button>
    </form>
  `);
  $('#upload-material-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData();
    fd.append('title', $('#um-title').value);
    fd.append('description', $('#um-description').value);
    fd.append('file', $('#um-file').files[0]);
    try {
      await API.upload(`/api/materials/${courseId}`, fd);
      closeModal();
      toast('Material subido exitosamente 📎');
      renderMaterials();
    } catch (err) {
      toast(err.message, 'error');
    }
  });
}

function downloadMaterial(id) {
  // Descargar con fetch para incluir el token
  fetch(`/api/materials/${id}/download?token=${encodeURIComponent(API.getToken())}`)
    .then(async (res) => {
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || 'Error al descargar');
      }
      const blob = await res.blob();
      const disp = res.headers.get('Content-Disposition') || '';
      const match = disp.match(/filename="?([^"]+)"?/i);
      const filename = match ? match[1] : 'material';
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    })
    .catch((err) => toast(err.message, 'error'));
}

async function deleteMaterial(id) {
  if (!confirm('¿Eliminar este material?')) return;
  try {
    await API.del(`/api/materials/${id}`);
    toast('Material eliminado 🗑️');
    renderMaterials();
  } catch (e) {
    toast(e.message, 'error');
  }
}

/* ============================================================
   CLASES EN VIVO
   ============================================================ */

async function renderLive() {
  const el = $('#view-live');
  try {
    const data = await API.get('/api/courses');
    const courses = data.courses || [];

    if (courses.length === 0) {
      el.innerHTML = `<div class="empty-state"><div class="empty-icon">🎥</div><p>No tienes cursos con clases en vivo.</p></div>`;
      return;
    }

    const cards = await Promise.all(courses.map(async (c) => {
      try {
        const det = await API.get(`/api/courses/${c.id}`);
        const classes = (det.live_classes || []).map((lc) => {
          const start = new Date(lc.scheduled_at);
          const end = new Date(start.getTime() + (lc.duration_min || 60) * 60000);
          const now = new Date();
          let state = 'upcoming';
          if (now >= start && now <= end) state = 'live';
          else if (now > end) state = 'ended';
          const label = state === 'live' ? '🔴 EN VIVO' : state === 'ended' ? 'Finalizada' : 'Programada';
          const badge = state === 'live' ? 'badge-red' : state === 'ended' ? 'badge-gray' : 'badge-warning';
          return `
            <div class="card live-class-card ${state}">
              <div class="flex-between">
                <h3 style="font-size:15px;">${escapeHtml(lc.title)}</h3>
                <span class="badge ${badge}">${label}</span>
              </div>
              <p class="text-muted text-small mt-8">${escapeHtml(lc.description || '')}</p>
              <p class="text-muted text-small mt-8">🕐 ${formatDateTime(lc.scheduled_at)} · ${lc.duration_min} min</p>
              <div class="flex mt-16">
                ${state === 'live' ? `<button class="btn btn-success" onclick="joinLiveClass(${lc.id})">▶️ Unirse ahora</button>` : ''}
                ${currentUser.role === 'profesor' ? `<button class="btn btn-danger btn-sm" onclick="deleteLiveClass(${lc.id})">🗑️</button>` : ''}
              </div>
            </div>`;
        }).join('');
        return `
          <div class="card">
            <div class="card-title">${escapeHtml(c.title)}
              ${currentUser.role === 'profesor' ? `<button class="btn btn-outline btn-sm" onclick="openCreateClassModal(${c.id})">+ Programar</button>` : ''}
            </div>
            ${classes || '<div class="text-muted text-small">Sin clases programadas.</div>'}
          </div>`;
      } catch (e) {
        return `<div class="card"><div class="card-title">${escapeHtml(c.title)}</div><div class="text-muted text-small">No disponible.</div></div>`;
      }
    }));

    el.innerHTML = cards.join('');
  } catch (e) {
    el.innerHTML = `<div class="alert alert-error">${escapeHtml(e.message)}</div>`;
  }
}

function openCreateClassModal(courseId) {
  // Fecha mínima: ahora
  const min = new Date(Date.now() + 60000).toISOString().slice(0, 16);
  openModal(`
    <h3 style="margin-bottom:16px;">🎥 Programar clase en vivo</h3>
    <form id="create-class-form">
      <div class="form-group">
        <label>Título de la clase *</label>
        <input type="text" id="cl-title" required placeholder="Ej: Clase 3 - Variables en JavaScript" />
      </div>
      <div class="form-group">
        <label>Descripción</label>
        <textarea id="cl-description" rows="2" placeholder="Temas a cubrir"></textarea>
      </div>
      <div class="form-group">
        <label>Fecha y hora *</label>
        <input type="datetime-local" id="cl-scheduled" min="${min}" required />
      </div>
      <div class="form-group">
        <label>Duración (minutos)</label>
        <input type="number" id="cl-duration" min="15" max="480" value="60" />
      </div>
      <button type="submit" class="btn btn-primary btn-block">Programar clase</button>
    </form>
  `);
  $('#create-class-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const local = $('#cl-scheduled').value;
    const iso = local ? new Date(local).toISOString() : null;
    try {
      await API.post('/api/live-classes', {
        course_id: courseId,
        title: $('#cl-title').value,
        description: $('#cl-description').value,
        scheduled_at: iso,
        duration_min: parseInt($('#cl-duration').value, 10) || 60
      });
      closeModal();
      toast('Clase programada 🎥');
      renderLive();
    } catch (err) {
      toast(err.message, 'error');
    }
  });
}

async function deleteLiveClass(id) {
  if (!confirm('¿Eliminar esta clase?')) return;
  try {
    await API.del(`/api/live-classes/${id}`);
    toast('Clase eliminada 🗑️');
    renderLive();
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function joinLiveClass(id) {
  try {
    const data = await API.get(`/api/live-classes/${id}`);
    const lc = data.liveClass;
    const start = new Date(lc.scheduled_at);
    const end = new Date(start.getTime() + (lc.duration_min || 60) * 60000);
    const now = new Date();
    if (now < new Date(start.getTime() - 30 * 60000)) {
      toast('Esta clase aún no comienza. Se habilitará 30 min antes.', 'error');
      return;
    }
    if (now > end) {
      toast('Esta clase ya finalizó.', 'error');
      return;
    }
    openModal(`
      <h3 style="margin-bottom:16px;">🎥 ${escapeHtml(lc.title)}</h3>
      <div class="flex-between mb-16">
        <span class="badge badge-red">🔴 En vivo</span>
        <span class="badge badge-blue">${formatDateTime(lc.scheduled_at)}</span>
      </div>
      <div class="jitsi-container" id="jitsi-container">
        <div style="display:flex;align-items:center;justify-content:center;height:100%;color:#fff;flex-direction:column;gap:8px;">
          <p>Cargando sala de video…</p>
          <p class="text-small">(Jitsi Meet externo: ${escapeHtml(lc.room_name)})</p>
        </div>
      </div>
      <div class="flex mt-16">
        <a class="btn btn-success btn-block" href="https://meet.jit.si/${encodeURIComponent(lc.room_name)}" target="_blank" rel="noopener">▶️ Abrir en Jitsi Meet</a>
      </div>
    `);
    // Cargar Jitsi si está disponible
    if (typeof JitsiMeetExternalAPI === 'function') {
      try {
        new JitsiMeetExternalAPI('meet.jit.si', {
          roomName: lc.room_name,
          width: '100%',
          height: '100%',
          userInfo: { displayName: currentUser.full_name }
        });
      } catch (e) {
        toast('No se pudo cargar Jitsi, usa el botón "Abrir en Jitsi Meet"', 'error');
      }
    }
  } catch (e) {
    toast(e.message, 'error');
  }
}

/* ============================================================
   NOTAS
   ============================================================ */

async function renderGrades() {
  const el = $('#view-grades');
  try {
    if (currentUser.role === 'profesor') {
      const data = await API.get('/api/courses');
      const courses = data.courses || [];
      if (courses.length === 0) {
        el.innerHTML = `<div class="empty-state"><div class="empty-icon">📝</div><p>No tienes cursos para calificar.</p></div>`;
        return;
      }
      const cards = await Promise.all(courses.map(async (c) => {
        try {
          const students = await API.get(`/api/courses/${c.id}/students`);
          const sList = (students.students || []).map((s) => `
            <div class="flex-between" style="border:1px solid var(--gray-200);border-radius:8px;padding:10px;margin-bottom:8px;">
              <div>
                <strong style="font-size:14px;">${escapeHtml(s.full_name)}</strong>
                <div class="text-muted text-small">${escapeHtml(s.email)}</div>
              </div>
              <button class="btn btn-outline btn-sm" onclick="openStudentGrades(${c.id}, ${s.id}, '${escapeHtml(s.full_name)}')">📝 Calificar</button>
            </div>`).join('');
          return `<div class="card">
            <div class="card-title">${escapeHtml(c.title)}</div>
            ${sList || '<div class="text-muted text-small">Sin estudiantes inscritos.</div>'}
          </div>`;
        } catch (e) {
          return `<div class="card"><div class="card-title">${escapeHtml(c.title)}</div><div class="text-muted text-small">No disponible.</div></div>`;
        }
      }));
      el.innerHTML = cards.join('');
    } else {
      const data = await API.get('/api/grades/my');
      const grades = data.grades || [];
      const byCourse = {};
      grades.forEach((g) => {
        if (!byCourse[g.course_title]) byCourse[g.course_title] = [];
        byCourse[g.course_title].push(g);
      });
      const coursesList = Object.entries(byCourse);
      if (coursesList.length === 0) {
        el.innerHTML = `<div class="empty-state"><div class="empty-icon">📝</div><p>Aún no tienes calificaciones registradas.</p></div>`;
        return;
      }
      el.innerHTML = coursesList.map(([title, list]) => {
        const pct = list.map((g) => (g.score / g.max_score) * 100);
        const avg = pct.length ? (pct.reduce((a, b) => a + b, 0) / pct.length).toFixed(1) : '—';
        return `
          <div class="card">
            <div class="card-title flex-between">
              <span>${escapeHtml(title)}</span>
              <span class="badge ${parseFloat(avg) >= 60 ? 'badge-green' : 'badge-red'}">Promedio: ${avg}%</span>
            </div>
            <div class="table-wrapper">
              <table>
                <thead><tr><th>Actividad</th><th>Nota</th><th>Calificación</th><th>Fecha</th></tr></thead>
                <tbody>
                  ${list.map((g) => {
                    const p = (g.score / g.max_score) * 100;
                    return `<tr>
                      <td>${escapeHtml(g.activity)}</td>
                      <td><strong>${g.score}</strong> / ${g.max_score}</td>
                      <td><span class="badge ${p >= 60 ? 'badge-green' : 'badge-red'}">${p.toFixed(1)}%</span></td>
                      <td class="text-muted">${formatDate(g.created_at)}</td>
                    </tr>`;
                  }).join('')}
                </tbody>
              </table>
            </div>
          </div>`;
      }).join('');
    }
  } catch (e) {
    el.innerHTML = `<div class="alert alert-error">${escapeHtml(e.message)}</div>`;
  }
}

async function openStudentGrades(courseId, studentId, studentName) {
  try {
    const data = await API.get(`/api/grades/course/${courseId}/student/${studentId}`);
    const grades = data.grades || [];
    openModal(`
      <h3 style="margin-bottom:16px;">📝 Calificar: ${studentName}</h3>
      <form id="grade-form">
        <div class="form-group">
          <label>Actividad *</label>
          <input type="text" id="gr-activity" required placeholder="Ej: Examen parcial 2" />
        </div>
        <div class="flex">
          <div class="form-group" style="flex:1;">
            <label>Nota obtenida *</label>
            <input type="number" id="gr-score" min="0" step="0.1" required placeholder="0-100" />
          </div>
          <div class="form-group" style="flex:1;">
            <label>Nota máxima</label>
            <input type="number" id="gr-max" min="1" value="100" step="0.1" />
          </div>
        </div>
        <button type="submit" class="btn btn-primary btn-block">Guardar nota</button>
      </form>
      <div class="card-title" style="margin-top:20px;">Notas registradas</div>
      ${grades.length === 0
        ? '<div class="text-muted text-small">Sin notas registradas.</div>'
        : `<div class="table-wrapper"><table>
            <thead><tr><th>Actividad</th><th>Nota</th><th></th></tr></thead>
            <tbody>${grades.map((g) => `<tr>
              <td>${escapeHtml(g.activity)}</td>
              <td><strong>${g.score}</strong> / ${g.max_score}</td>
              <td><button class="btn btn-danger btn-sm" onclick="deleteGrade(${g.id})">🗑️</button></td>
            </tr>`).join('')}</tbody>
          </table></div>`}
    `);
    $('#grade-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await API.post('/api/grades', {
          course_id: courseId,
          student_id: studentId,
          activity: $('#gr-activity').value,
          score: parseFloat($('#gr-score').value),
          max_score: parseFloat($('#gr-max').value) || 100
        });
        toast('Nota guardada ✅');
        openStudentGrades(courseId, studentId, studentName);
      } catch (err) {
        toast(err.message, 'error');
      }
    });
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function deleteGrade(id) {
  if (!confirm('¿Eliminar esta nota?')) return;
  try {
    await API.del(`/api/grades/${id}`);
    toast('Nota eliminada 🗑️');
    renderGrades();
  } catch (e) {
    toast(e.message, 'error');
  }
}

/* ============================================================
   PAGOS
   ============================================================ */

async function renderPayments() {
  const el = $('#view-payments');
  try {
    if (currentUser.role === 'estudiante') {
      const data = await API.get('/api/payments/my');
      const payments = data.payments || [];
      const total = payments.reduce((a, p) => a + p.amount, 0);
      el.innerHTML = `
        <div class="stat-grid">
          <div class="stat-card">
            <div class="stat-icon">💳</div>
            <div class="stat-value">${payments.length}</div>
            <div class="stat-label">Pagos realizados</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">💰</div>
            <div class="stat-value">${formatMoney(total)}</div>
            <div class="stat-label">Total invertido</div>
          </div>
        </div>
        <div class="card">
          <div class="card-title">🧾 Historial de pagos</div>
          ${payments.length === 0
            ? '<div class="empty-state"><div class="empty-icon">💳</div><p>Aún no has realizado pagos.</p><button class="btn btn-primary mt-16" onclick="navigate(\'courses\')">Ver catálogo</button></div>'
            : `<div class="table-wrapper"><table>
                <thead><tr><th>Referencia</th><th>Curso</th><th>Monto</th><th>Método</th><th>Estado</th><th>Fecha</th></tr></thead>
                <tbody>${payments.map((p) => `
                  <tr>
                    <td class="text-muted">${escapeHtml(p.reference)}</td>
                    <td><strong>${escapeHtml(p.course_title)}</strong></td>
                    <td>${formatMoney(p.amount)}</td>
                    <td>${escapeHtml(p.method)}</td>
                    <td><span class="badge badge-green">${escapeHtml(p.status)}</span></td>
                    <td class="text-muted">${formatDateTime(p.created_at)}</td>
                  </tr>`).join('')}
                </tbody>
              </table></div>`}
        </div>`;
    } else {
      const data = await API.get('/api/courses');
      const courses = data.courses || [];
      if (courses.length === 0) {
        el.innerHTML = `<div class="empty-state"><div class="empty-icon">💳</div><p>No tienes cursos para consultar pagos.</p></div>`;
        return;
      }
      const cards = await Promise.all(courses.map(async (c) => {
        try {
          const pays = await API.get(`/api/payments/course/${c.id}`);
          const list = (pays.payments || []).map((p) => `
            <div class="list-item">
              <div class="item-icon">👨‍🎓</div>
              <div class="item-body">
                <div class="item-title">${escapeHtml(p.student_name)}</div>
                <div class="item-sub">${escapeHtml(p.reference)} · ${formatDateTime(p.created_at)}</div>
              </div>
              <div class="item-actions">
                <span class="badge badge-green">${formatMoney(p.amount)}</span>
              </div>
            </div>`).join('');
          return `<div class="card">
            <div class="card-title flex-between">
              <span>${escapeHtml(c.title)}</span>
              <span class="badge badge-blue">Total: ${formatMoney(pays.total || 0)}</span>
            </div>
            ${list || '<div class="text-muted text-small">Sin pagos registrados.</div>'}
          </div>`;
        } catch (e) {
          return `<div class="card"><div class="card-title">${escapeHtml(c.title)}</div><div class="text-muted text-small">No disponible.</div></div>`;
        }
      }));
      el.innerHTML = cards.join('');
    }
  } catch (e) {
    el.innerHTML = `<div class="alert alert-error">${escapeHtml(e.message)}</div>`;
  }
}

function openPayModal(courseId, courseTitle, price) {
  openModal(`
    <h3 style="margin-bottom:16px;">💳 Inscribirse al curso</h3>
    <div class="alert alert-info">Vas a inscribirte en: <strong>${courseTitle}</strong></div>
    <div class="flex-between mb-16" style="padding:14px;background:var(--gray-50);border-radius:8px;">
      <span>Precio del curso</span>
      <strong style="font-size:20px;">${formatMoney(price)}</strong>
    </div>
    <form id="pay-form">
      <div class="form-group">
        <label>Método de pago</label>
        <select id="pay-method">
          <option value="tarjeta">💳 Tarjeta de crédito/débito</option>
          <option value="transferencia">🏦 Transferencia bancaria</option>
          <option value="paypal">🅿️ PayPal</option>
        </select>
      </div>
      <div class="alert alert-warning" style="background:var(--warning-light);color:var(--warning);border-radius:8px;padding:10px;font-size:13px;margin-bottom:16px;">
        ⚠️ Pago simulado: no se realizará un cargo real. Al confirmar, quedarás inscrito.
      </div>
      <button type="submit" class="btn btn-success btn-block">✅ Confirmar pago de ${formatMoney(price)}</button>
    </form>
  `);
  $('#pay-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      const res = await API.post('/api/payments', {
        course_id: courseId,
        method: $('#pay-method').value
      });
      closeModal();
      toast(res.message || 'Pago exitoso 🎉');
      renderCourses();
      renderDashboard();
    } catch (err) {
      toast(err.message, 'error');
    }
  });
}

/* ============================================================
   FORO DE DISCUSIÓN
   ============================================================ */

async function renderForum() {
  const el = $('#view-forum');
  try {
    const data = await API.get('/api/courses');
    const courses = data.courses || [];

    if (courses.length === 0) {
      el.innerHTML = `<div class="empty-state"><div class="empty-icon">💬</div><p>No tienes cursos con foro. Inscríbete o crea un curso primero.</p></div>`;
      return;
    }

    const cards = await Promise.all(courses.map(async (c) => {
      try {
        const forum = await API.get(`/api/forum/course/${c.id}`);
        const threads = (forum.threads || []).map((t) => `
          <div class="list-item">
            <div class="item-icon">💬</div>
            <div class="item-body">
              <div class="item-title">${escapeHtml(t.title)}</div>
              <div class="item-sub">👤 ${escapeHtml(t.author_name)} (${t.author_role === 'profesor' ? 'Profesor' : 'Estudiante'}) · 💬 ${t.reply_count} respuestas · ${formatDate(t.created_at)}</div>
            </div>
            <div class="item-actions">
              <button class="btn btn-outline btn-sm" onclick="openThread(${t.id})">Ver</button>
              ${t.author_id === currentUser.id || currentUser.role === 'profesor'
                ? `<button class="btn btn-danger btn-sm" onclick="deleteThread(${t.id})">🗑️</button>`
                : ''}
            </div>
          </div>`).join('');
        return `
          <div class="card">
            <div class="card-title">${escapeHtml(c.title)}
              <button class="btn btn-primary btn-sm" onclick="openCreateThreadModal(${c.id})">+ Nuevo hilo</button>
            </div>
            ${threads || '<div class="text-muted text-small">Aún no hay discusiones. ¡Crea la primera!</div>'}
          </div>`;
      } catch (e) {
        return `<div class="card"><div class="card-title">${escapeHtml(c.title)}</div><div class="text-muted text-small">Foro no disponible.</div></div>`;
      }
    }));

    el.innerHTML = cards.join('');
  } catch (e) {
    el.innerHTML = `<div class="alert alert-error">${escapeHtml(e.message)}</div>`;
  }
}

function openCreateThreadModal(courseId) {
  openModal(`
    <h3 style="margin-bottom:16px;">💬 Crear nuevo hilo</h3>
    <form id="create-thread-form">
      <div class="form-group">
        <label>Título *</label>
        <input type="text" id="ft-title" required placeholder="Ej: ¿Alguien me ayuda con el ejercicio 3?" />
      </div>
      <div class="form-group">
        <label>Contenido *</label>
        <textarea id="ft-content" rows="5" required placeholder="Describe tu duda o tema de discusión..."></textarea>
      </div>
      <button type="submit" class="btn btn-primary btn-block">Publicar hilo</button>
    </form>
  `);
  $('#create-thread-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      await API.post(`/api/forum/course/${courseId}`, {
        title: $('#ft-title').value,
        content: $('#ft-content').value
      });
      closeModal();
      toast('Hilo publicado 💬');
      renderForum();
    } catch (err) {
      toast(err.message, 'error');
    }
  });
}

async function openThread(threadId) {
  try {
    const data = await API.get(`/api/forum/thread/${threadId}`);
    const { thread, replies } = data;

    const html = `
      <div class="flex-between" style="margin-bottom:16px;">
        <h3 style="font-size:18px;">${escapeHtml(thread.title)}</h3>
        <button class="btn btn-ghost btn-sm" onclick="closeModal()">Cerrar</button>
      </div>
      <div class="alert alert-info">
        <strong>👤 ${escapeHtml(thread.author_name)}</strong>
        <span class="text-muted"> (${thread.author_role === 'profesor' ? 'Profesor' : 'Estudiante'}) · ${formatDateTime(thread.created_at)}</span>
        <div style="margin-top:10px; white-space:pre-wrap;">${escapeHtml(thread.content)}</div>
      </div>
      <div class="card-title" style="margin-top:20px;">Respuestas (${replies.length})</div>
      ${replies.length === 0
        ? '<div class="text-muted text-small">Sin respuestas aún. ¡Sé el primero en responder!</div>'
        : replies.map((r) => `
            <div class="list-item" style="align-items:flex-start;">
              <div class="item-icon">${r.author_role === 'profesor' ? '👨‍🏫' : '👨‍🎓'}</div>
              <div class="item-body">
                <div class="item-title">${escapeHtml(r.author_name)} <span class="text-muted text-small">· ${formatDateTime(r.created_at)}</span></div>
                <div style="white-space:pre-wrap; font-size:14px; margin-top:6px;">${escapeHtml(r.content)}</div>
              </div>
              ${r.author_id === currentUser.id || currentUser.role === 'profesor'
                ? `<div class="item-actions"><button class="btn btn-danger btn-sm" onclick="deleteReply(${r.id}, ${threadId})">🗑️</button></div>`
                : ''}
            </div>`).join('')}
      <form id="reply-form" class="mt-16">
        <div class="form-group">
          <label>Tu respuesta</label>
          <textarea id="reply-content" rows="3" required placeholder="Escribe tu respuesta..."></textarea>
        </div>
        <button type="submit" class="btn btn-primary btn-block">Responder</button>
      </form>
    `;
    openModal(html);

    $('#reply-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await API.post(`/api/forum/thread/${threadId}/reply`, {
          content: $('#reply-content').value
        });
        toast('Respuesta publicada ✅');
        openThread(threadId);
      } catch (err) {
        toast(err.message, 'error');
      }
    });
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function deleteThread(id) {
  if (!confirm('¿Eliminar este hilo y todas sus respuestas?')) return;
  try {
    await API.del(`/api/forum/thread/${id}`);
    toast('Hilo eliminado 🗑️');
    renderForum();
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function deleteReply(id, threadId) {
  if (!confirm('¿Eliminar esta respuesta?')) return;
  try {
    await API.del(`/api/forum/reply/${id}`);
    toast('Respuesta eliminada 🗑️');
    openThread(threadId);
  } catch (e) {
    toast(e.message, 'error');
  }
}

/* ============================================================
   INIT
   ============================================================ */

function init() {
  // Login form
  $('#login-form').addEventListener('submit', (e) => {
    e.preventDefault();
    hideError();
    handleLogin($('#login-email').value, $('#login-password').value);
  });

  // Register form
  $('#register-form').addEventListener('submit', (e) => {
    e.preventDefault();
    hideError();
    const role = document.querySelector('input[name="role"]:checked').value;
    handleRegister($('#reg-name').value, $('#reg-email').value, $('#reg-password').value, role);
  });

  // Switchers
  $('#show-register').addEventListener('click', (e) => {
    e.preventDefault();
    hideError();
    $('#login-form').style.display = 'none';
    $('#register-form').style.display = 'block';
  });
  $('#show-login').addEventListener('click', (e) => {
    e.preventDefault();
    hideError();
    $('#register-form').style.display = 'none';
    $('#login-form').style.display = 'block';
  });

  // Demo buttons
  $$('.demo-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      hideError();
      handleLogin(btn.dataset.email, btn.dataset.pass);
    });
  });

  // Navigation
  $$('.nav-link').forEach((link) => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      navigate(link.dataset.view);
    });
  });

  // Logout
  $('#btn-logout').addEventListener('click', logout);

  // Modal close
  $('#modal-close').addEventListener('click', closeModal);
  $('#modal-overlay').addEventListener('click', (e) => {
    if (e.target === $('#modal-overlay')) closeModal();
  });

  // Comprobar sesión previa
  const token = API.getToken();
  if (token) {
    API.get('/api/auth/me')
      .then((data) => {
        setUserInfo(data.user);
        showAppScreen();
        navigate('dashboard');
      })
      .catch(() => {
        API.clearToken();
        showAuthScreen();
      });
  } else {
    showAuthScreen();
  }
}

document.addEventListener('DOMContentLoaded', init);
