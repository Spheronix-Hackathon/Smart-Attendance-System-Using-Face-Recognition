// Decoupled Dashboard Logic - Smart Attendance System
const API_URL = window.location.origin;
let __refreshTimer = null;

document.addEventListener('DOMContentLoaded', async () => {
    const isAdminSectionPage = window.location.pathname.includes('admin_');
    const user = isAdminSectionPage ? await Api.requireAdmin() : await Api.requireAuth();
    if (!user) return;

    window.currentUser = user;

    // Update Global UI
    const userNameElements = document.querySelectorAll('#userName');
    userNameElements.forEach(el => el.textContent = user.full_name || user.email.split('@')[0]);

    const isAdminDashboardPage = window.location.pathname.includes('admin_dashboard.html');
    const isUserPage = window.location.pathname.includes('user_dashboard.html');
    const isTeacherPage = window.location.pathname.includes('teacher_dashboard.html');

    if (isAdminDashboardPage) {
        loadAdminStats();
        loadAdminLogs();
        startPolling(() => { loadAdminStats(); loadAdminLogs(); });
    } else if (isUserPage) {
        initRealTimeClock();
        loadStudentStats();
        loadStudentHistory();
        startPolling(() => { loadStudentStats(); loadStudentHistory(); });
    } else if (isTeacherPage) {
        loadTeacherDashboardStats();
        startPolling(loadTeacherDashboardStats);
    }

    // Universal Logout
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.onclick = () => {
            localStorage.removeItem('token');
            window.location.href = 'login.html';
        };
    }
});

function startPolling(fn, interval = 15000) {
    if (__refreshTimer) clearInterval(__refreshTimer);
    __refreshTimer = setInterval(fn, interval);
}

function initRealTimeClock() {
    const clockEl = document.getElementById('digitalClock');
    if (!clockEl) return;
    
    setInterval(() => {
        const now = new Date();
        clockEl.textContent = now.toLocaleTimeString('en-US', { hour12: true, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }, 1000);
}

// --- ADMIN TELEMETRY ---
async function loadAdminStats() {
    try {
        const { resp, data: stats } = await Api.apiFetch('/admin/stats');
        if (resp.ok) {
            const nodes = {
                'activeUsers': stats.total_users || 0,
                'todayAttendance': (stats.attendance_percentage || 0) + '%'
            };
            for (const [id, val] of Object.entries(nodes)) {
                const el = document.getElementById(id);
                if (el) el.textContent = val;
            }
        }
    } catch (e) { console.error("Admin Stats Failure", e); }
}

async function loadAdminLogs() {
    try {
        const { resp: logResp, data: logs } = await Api.apiFetch('/admin/logs?limit=10');
        if (logResp.ok) {
            const tbody = document.querySelector('#logsTable tbody');
            if (tbody) {
                tbody.innerHTML = '';
                if (logs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-dim); padding: 40px;">No pipeline activity.</td></tr>';
                }
                logs.forEach(log => {
                    const tr = document.createElement('tr');
                    tr.style.borderBottom = '1px solid rgba(255,255,255,0.03)';
                    tr.innerHTML = `
                        <td style="padding: 20px 32px; font-weight: 800; color: #fff;">${log.user_name || 'NODE_UNKNOWN'}</td>
                        <td style="padding: 20px 32px; color: var(--text-dim); font-size: 0.8rem;">${log.department || 'GLOBAL'}</td>
                        <td style="padding: 20px 32px; text-align: center; font-family: var(--font-data); color: var(--text-dim); font-size: 0.75rem;">${log.timestamp}</td>
                        <td style="padding: 20px 32px; text-align: right;">
                            <span class="badge ${log.status.toLowerCase()==='success'?'badge-active':''}" style="padding: 4px 12px; border-radius: 40px; font-size: 0.6rem; letter-spacing: 1px;">
                                ${log.status.toUpperCase()}
                            </span>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        }
    } catch (e) { console.error("Admin Pipeline Failure", e); }
}

// --- STUDENT TELEMETRY ---
async function loadStudentStats() {
    try {
        const { resp, data: stats } = await Api.apiFetch('/student/stats');
        if (resp.ok) {
            window.studentAttendanceStats = stats;
            window.studentAttendanceHistory = stats.history || [];

            const nodes = {
                'daysPresent': stats.attended_days ?? ((stats.present_days || 0) + (stats.late_days || 0)),
                'daysAbsent': stats.absences || 0,
                'avgCheckIn': stats.avg_check_in || '--:--',
                'attendanceRate': (stats.attendance_percentage || 0) + '%'
            };
            for (const [id, val] of Object.entries(nodes)) {
                const el = document.getElementById(id);
                if (el) el.textContent = val;
            }
            
            // Also populate history if needed
            renderStudentHistory(stats.history || []);

            document.dispatchEvent(new CustomEvent('student-attendance-stats-loaded', { detail: stats }));
            return stats;
        }
    } catch (e) { console.error("Student Stats Failure", e); }
    return null;
}

async function loadStudentHistory() {
    // History is now included in loadStudentStats for efficiency.
    // This is kept for compatibility with current dashboard calling pattern.
    return window.studentAttendanceHistory || [];
}

function renderStudentHistory(history) {
    const tbody = document.querySelector('#historyTable tbody');
    if (tbody) {
        tbody.innerHTML = '';
        if (history.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: var(--text-dim); padding: 60px;">No personal history.</td></tr>';
            return;
        }
        history.forEach(h => {
            const tr = document.createElement('tr');
            tr.style.borderBottom = '1px solid rgba(255,255,255,0.03)';
            tr.innerHTML = `
                <td style="padding: 20px 32px; font-family: var(--font-data); color: #fff; font-size: 0.8rem;">${h.date} ${h.check_in}</td>
                <td style="padding: 20px 32px; color: var(--text-dim); font-size: 0.8rem;">${h.method === 'face' ? 'Biometric Terminal' : 'Manual Entry'}</td>
                <td style="padding: 20px 32px; text-align: right;">
                    <span class="badge ${h.status.toLowerCase()==='present'?'badge-active':''}" style="padding: 4px 12px; border-radius: 40px; font-size: 0.6rem; letter-spacing: 1px;">
                        ${h.status.toUpperCase()}
                    </span>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }
}

// --- TEACHER TELEMETRY ---
async function loadTeacherDashboardStats() {
    try {
        const { resp, data: stats } = await Api.apiFetch('/teacher/dashboard-stats');
        if (resp.ok) {
            const totalEl = document.getElementById('statTotal');
            const presentEl = document.getElementById('statPresent');
            const absentEl = document.getElementById('statAbsent');
            
            if (totalEl) totalEl.textContent = stats.total_students || 0;
            if (presentEl) presentEl.textContent = stats.present || 0;
            if (absentEl) absentEl.textContent = (stats.absent || 0) + ((stats.attendance_finalized ? stats.not_marked : 0) || 0);
        }
    } catch (e) { console.error("Teacher Stats Failure", e); }
}

// --- 3D Orb Visualization Logic ---
function createOrbViz(container, options = {}) {
    if (!container || !window.THREE || container.dataset.orbVizReady === 'true') return;
    container.dataset.orbVizReady = 'true';
    const viewport = container.parentElement && container.parentElement.clientWidth ? container.parentElement : container;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);
    renderer.domElement.style.width = '100%';
    renderer.domElement.style.height = '100%';
    renderer.domElement.style.display = 'block';

    const orbGroup = new THREE.Group();
    scene.add(orbGroup);

    const outerRadius = options.radius || 1.25;
    orbGroup.add(new THREE.Mesh(
        new THREE.IcosahedronGeometry(outerRadius, 2),
        new THREE.MeshBasicMaterial({ color: 0x00d1c7, wireframe: true, transparent: true, opacity: 0.3 })
    ));
    orbGroup.add(new THREE.Mesh(
        new THREE.IcosahedronGeometry(outerRadius * 0.8, 1),
        new THREE.MeshBasicMaterial({ color: 0x6f45ff, wireframe: true, transparent: true, opacity: 0.2 })
    ));

    function resize() {
        const width = viewport.clientWidth || container.clientWidth || 1;
        const height = viewport.clientHeight || container.clientHeight || 1;
        renderer.setSize(width, height, false);
        renderer.domElement.style.width = '100%';
        renderer.domElement.style.height = '100%';
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
    }
    resize();
    requestAnimationFrame(resize);
    window.addEventListener('resize', resize);
    camera.position.z = options.cameraZ || 4.5;

    function animate() {
        requestAnimationFrame(animate);
        orbGroup.rotation.y += 0.003;
        orbGroup.rotation.x += 0.001;
        renderer.render(scene, camera);
    }
    animate();
}

window.initVisualNode = (id, type) => {
    const el = document.getElementById(id);
    if (!el) return;
    if (type === 'admin') createOrbViz(el, { radius: 1.4, cameraZ: 4.8 });
    else if (type === 'teacher') createOrbViz(el, { radius: 1.2, cameraZ: 4.5 });
    else createOrbViz(el, { radius: 1.1, cameraZ: 4.2 });
};
