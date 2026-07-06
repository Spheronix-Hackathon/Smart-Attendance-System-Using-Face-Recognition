const TEACHER_API_BASE = window.location.origin;
let teacherWs = null;
let teacherPollTimer = null;
let teacherWsConnected = false;
let teacherLocation = null;
const ABSENT_NOTICES_CUTOFF_MINUTES = 17 * 60;

function isAbsentNotificationAvailable(now = new Date()) {
    return (now.getHours() * 60 + now.getMinutes()) >= ABSENT_NOTICES_CUTOFF_MINUTES;
}

function updateAbsentNotificationButtons() {
    const enabled = isAbsentNotificationAvailable();
    const title = enabled
        ? 'Send absent notifications for finalized attendance.'
        : 'Available after 17:00 when attendance is finalized.';

    document.querySelectorAll('#notifyBtn, #notifyAbsentBtn').forEach((button) => {
        button.disabled = !enabled;
        button.setAttribute('aria-disabled', String(!enabled));
        button.setAttribute('title', title);
        button.style.opacity = enabled ? '' : '0.55';
        button.style.cursor = enabled ? '' : 'not-allowed';
    });
}

function teacherStatusClass(status) {
    const s = String(status || '').toLowerCase();
    if (s === 'present') return 'status-chip status-present';
    if (s === 'late') return 'status-chip status-late';
    if (s === 'absent') return 'status-chip status-absent';
    if (s === 'pending' || s === 'not marked') return 'status-chip status-pending';
    return 'status-chip status-notmarked';
}

async function ensureTeacher() {
    if (window.Api && !Api.ensureHttp('http://127.0.0.1:8000/static/teacher_dashboard.html')) return null;
    const user = window.Api ? await Api.requireAuth() : null;
    if (!user) return null;

    const role = (user.role || '').toLowerCase();
    if (!user.is_admin && role !== 'teacher') {
        alert('Access denied: teacher or admin only.');
        window.location.href = 'user_dashboard.html';
        return null;
    }
    return user;
}

async function fetchJson(path, options = {}) {
    if (window.Api) {
        const { resp, data } = await Api.apiFetch(path, options);
        if (!resp.ok) throw new Error(data?.detail || 'Request failed');
        return data;
    }

    const token = localStorage.getItem('token');
    const resp = await fetch(`${TEACHER_API_BASE}${path}`, {
        ...options,
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data?.detail || 'Request failed');
    return data;
}

async function resolveTeacherLocation() {
    if (!navigator.geolocation) {
        throw new Error('Geolocation is not supported by this browser.');
    }

    return await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                teacherLocation = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                };
                resolve(teacherLocation);
            },
            () => reject(new Error('Location access is required to mark attendance within campus.')),
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
    });
}

async function loadTeacherDashboard() {
    const user = await ensureTeacher();
    if (!user) return;

    const meta = document.getElementById('teacherMeta');
    if (meta) meta.textContent = `Department: ${user.department || 'All'}`;

    const stats = await fetchJson('/teacher/dashboard-stats', { method: 'GET' });
    const today = await fetchJson('/teacher/attendance/today', { method: 'GET' });

    const setStat = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val ?? 0;
    };

    setStat('statTotal', stats.total_students);
    setStat('statPresent', stats.present);
    setStat('statLate', stats.late);
    setStat('statAbsent', (stats.absent ?? 0) + ((stats.attendance_finalized ? stats.not_marked : 0) ?? 0));

    const tbody = document.querySelector('#teacherTodayTable tbody');
    if (tbody) {
        tbody.innerHTML = '';
        if (!today.length) {
            tbody.innerHTML = '<tr><td colspan="4">No students found for this department.</td></tr>';
        } else {
            today.forEach((r) => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${r.roll_number || '-'}</td>
                    <td>${r.full_name || r.email}</td>
                    <td><span class="${teacherStatusClass(r.status)}">${r.status || 'Not Marked'}</span></td>
                    <td>${r.check_in || '-'}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    }

}

function ensureRealtimeUpdates() {
    if (teacherWs || teacherWsConnected) return;

    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    teacherWs = new WebSocket(`${wsScheme}://${window.location.host}/ws`);

    teacherWs.onopen = () => {
        teacherWsConnected = true;
        if (teacherPollTimer) {
            clearInterval(teacherPollTimer);
            teacherPollTimer = null;
        }
    };

    teacherWs.onmessage = (e) => {
        try {
            const payload = JSON.parse(e.data);
            if (payload.event === 'attendance_marked') {
                loadTeacherDashboard().catch(() => {});
            }
        } catch {
            // Ignore malformed events.
        }
    };

    teacherWs.onclose = () => {
        teacherWsConnected = false;
        teacherWs = null;
        // Fallback polling when websocket is unavailable.
        if (!teacherPollTimer) {
            teacherPollTimer = setInterval(() => {
                loadTeacherDashboard().catch(() => {});
            }, 10000);
        }
    };

    teacherWs.onerror = () => {
        teacherWsConnected = false;
    };
}

async function loadDepartmentStudents() {
    try {
        const students = await fetchJson('/teacher/department/students?unmarked_only=true', { method: 'GET' });
        const select = document.getElementById('m_studentSelect');
        if (select) {
            select.innerHTML = '<option value="">-- SELECT IDENTITY --</option>';
            students.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s.id;
                opt.textContent = `${s.full_name || s.email} (${s.roll_number})`;
                select.appendChild(opt);
            });
        }
    } catch (err) {
        console.error("Failed to load department students:", err);
    }
}

async function setupTeacherMarkPage() {
    const user = await ensureTeacher();
    if (!user) return;

    // Head Sync
    const deptBadge = document.getElementById('teacherDept');
    if (deptBadge) deptBadge.textContent = `DEPT: ${user.department || 'GLOBAL'}`;

    // Load Dropdown
    await loadDepartmentStudents();

    const video = document.getElementById('video');
    const placeholder = document.getElementById('cameraPlaceholder');
    const statusDot = document.getElementById('scannerStatusDot');
    const statusText = document.getElementById('scannerStatusText');
    
    // Canvas for capture
    const canvas = document.createElement('canvas');
    
    const startBtn = document.getElementById('startBtn');
    const captureBtn = document.getElementById('captureBtn');
    
    const manualBtn = document.getElementById('manualMarkBtn');
    const manualStudent = document.getElementById('m_studentSelect');
    const statusMsg = document.getElementById('m_statusMsg');
    
    startBtn.addEventListener('click', async () => {
        if (video.srcObject) {
            // Stop Camera
            const stream = video.srcObject;
            const tracks = stream.getTracks();
            tracks.forEach(track => track.stop());
            video.srcObject = null;
            video.style.display = 'none';
            if (placeholder) placeholder.style.display = 'block';
            
            if (statusDot) {
                statusDot.classList.remove('active');
                if (statusText) statusText.textContent = 'INITIALIZING_STANDBY...';
            }
            
            startBtn.innerHTML = '<i class="fa-solid fa-video"></i> ACTIVATE_CAMERA';
            startBtn.style.borderColor = 'var(--glass-border)';
            startBtn.style.color = '#fff';
            return;
        }

        try {
            startBtn.disabled = true;
            startBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Initializing...';
            
            const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
            video.srcObject = stream;
            video.style.display = 'block';
            if (placeholder) placeholder.style.display = 'none';
            
            if (statusDot) {
                statusDot.classList.add('active');
                if (statusText) statusText.textContent = 'SYSTEM_READY: BIOMETRIC_FEED_ACTIVE';
            }
            
            startBtn.disabled = false;
            startBtn.innerHTML = '<i class="fa-solid fa-video-slash"></i> DEACTIVATE_CAMERA';
            startBtn.style.borderColor = '#ef4444';
            startBtn.style.color = '#ef4444';
        } catch (err) {
            console.error("Camera Error:", err);
            alert("Camera Access Denied: " + err.message);
            startBtn.disabled = false;
            startBtn.innerHTML = '<i class="fa-solid fa-video"></i> ACTIVATE_CAMERA';
        }
    });

    captureBtn.addEventListener('click', async () => {
        if (!video.srcObject) {
            alert("Please start the camera first.");
            return;
        }

        captureBtn.disabled = true;
        const originalText = captureBtn.innerHTML;
        captureBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
        
        try {
            if (!teacherLocation) {
                try { await resolveTeacherLocation(); } catch (locErr) { console.warn(locErr); }
            }
            
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            const image = canvas.toDataURL('image/jpeg', 0.9);
            
            const data = await fetchJson('/teacher/mark-attendance', {
                method: 'POST',
                body: { 
                    image, 
                    latitude: teacherLocation?.latitude, 
                    longitude: teacherLocation?.longitude 
                }
            });

            // Update session log
            const logTbody = document.querySelector('#historyTable tbody'); // Using historyTable if it exists here
            const counter = document.getElementById('scanCounter');
            if (counter && data.students) {
                const currentCount = parseInt(counter.textContent.split(': ')[1] || 0);
                const newlyMarked = data.students.filter(s => s.status !== 'Already Recorded').length;
                counter.textContent = `COUNT: ${currentCount + newlyMarked}`;
            }

            if (data.students) {
                const initialMsg = document.getElementById('initialLogMsg');
                const logContainer = document.getElementById('scanLogContainer');
                
                if (initialMsg) initialMsg.remove();
                
                let sessionTable = document.getElementById('sessionLogs');
                if (!sessionTable && logContainer) {
                    logContainer.innerHTML = '<table style="width:100%; font-size:0.7rem; border-collapse:collapse;" id="sessionLogs"><tbody></tbody></table>';
                    sessionTable = document.getElementById('sessionLogs');
                }
                
                const sessionTbody = sessionTable ? sessionTable.querySelector('tbody') : null;
                if (sessionTbody) {
                    data.students.forEach(s => {
                        const tr = document.createElement('tr');
                        tr.style.borderBottom = '1px solid rgba(255,255,255,0.02)';
                        const isDuplicate = s.status === 'Already Recorded';
                        tr.innerHTML = `
                            <td style="padding:8px 0; font-weight:800; color:#fff;">${s.student_name}</td>
                            <td style="padding:8px 0; text-align:right;"><span class="badge ${isDuplicate ? 'badge-neutral' : 'badge-active'}">${s.status}</span></td>
                        `;
                        sessionTbody.insertBefore(tr, sessionTbody.firstChild);
                    });
                    
                    // Remove matched students from manual dropdown
                    data.students.forEach(s => {
                        const opt = document.querySelector(`#m_studentSelect option[value="${s.student_id}"]`);
                        if (opt) opt.remove();
                    });
                }
            }

            alert(data.message);

        } catch (err) {
            alert("SCAN_ERROR: " + err.message);
        } finally {
            captureBtn.disabled = false;
            captureBtn.innerHTML = originalText;
        }
    });

    if (manualBtn) {
        // Status Selection Logic (Internal)
        const statusBtns = document.querySelectorAll('.status-btn');
        statusBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                statusBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        manualBtn.addEventListener('click', async () => {
            const studentId = manualStudent.value;
            if (!studentId) {
                if (statusMsg) statusMsg.textContent = 'Please select a student first.';
                return;
            }

            const activeStatusBtn = document.querySelector('.status-btn.active');
            const status = activeStatusBtn ? activeStatusBtn.getAttribute('data-status') || activeStatusBtn.textContent.trim() : 'present';

            manualBtn.disabled = true;
            const originalText = manualBtn.innerHTML;
            manualBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Submitting...';
            
            try {
                if (!teacherLocation) {
                    try { await resolveTeacherLocation(); } catch (locErr) {}
                }
                
                const data = await fetchJson(`/teacher/mark-attendance/manual/${studentId}`, {
                    method: 'POST',
                    body: { 
                        status: status.charAt(0).toUpperCase() + status.slice(1).toLowerCase(), 
                        latitude: teacherLocation?.latitude, 
                        longitude: teacherLocation?.longitude 
                    }
                });

                if (statusMsg) {
                    statusMsg.textContent = data.message;
                    statusMsg.style.color = "var(--secondary)";
                }
                alert(data.message || 'Attendance marked successfully.');
                
                // Remove marked student from manual dropdown
                const opt = document.querySelector(`#m_studentSelect option[value="${studentId}"]`);
                if (opt) opt.remove();
                
                loadTeacherDashboard().catch(() => {});

            } catch (err) {
                if (statusMsg) {
                    statusMsg.textContent = err.message;
                    statusMsg.style.color = "#ff4d4d";
                }
                alert("Manual Entry Failed: " + err.message);
            } finally {
                manualBtn.disabled = false;
                manualBtn.innerHTML = originalText;
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    updateAbsentNotificationButtons();
    setInterval(updateAbsentNotificationButtons, 60000);

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            if (window.Api) Api.setToken(null);
            else localStorage.removeItem('token');
            window.location.href = 'login.html';
        });
    }

    if (window.location.pathname.includes('teacher_dashboard.html')) {
        loadTeacherDashboard().catch((err) => {
            console.error(err);
            alert(err.message || 'Failed to load teacher dashboard');
        });
        ensureRealtimeUpdates();
    }

    if (window.location.pathname.includes('teacher_mark_attendance.html')) {
        setupTeacherMarkPage().catch((err) => {
            console.error(err);
            const statusMsg = document.getElementById('statusMsg');
            if (statusMsg) statusMsg.textContent = err.message || 'Failed to initialize scanner';
        });
    }
});
