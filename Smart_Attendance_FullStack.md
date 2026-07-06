# Smart Attendance System Using Face Recognition - Full-Stack Architecture Notes

## Overview

Smart Attendance System Using Face Recognition is a FastAPI and MongoDB attendance system with a vanilla JavaScript frontend. It supports biometric enrollment, OTP verification, teacher-led attendance capture, student self-service pages, admin reporting, and security auditing.

The system is organized around a small set of clear runtime boundaries:

- `main.py` owns application startup, static file hosting, background work, and the websocket endpoint.
- Route modules expose role-specific APIs.
- Service modules implement the actual business logic.
- Frontend pages are static HTML files backed by shared JS and CSS assets.

## Runtime Flow

1. The browser opens a page under `/static/...`, which is served by `backend/main.py`.
2. `main.py` runs its lifespan hook, ensures collection indexes, backfills missing IDs, and starts the absence-notice worker.
3. The frontend calls the FastAPI API through `frontend/js/api.js`, which injects the JWT token from localStorage when present.
4. Authenticated pages call `/users/me` first, then route the user to the correct role-specific screen.
5. Teacher attendance and student dashboards refresh by polling, while the websocket endpoint remains available as a connection layer.
6. Attendance finalization and absent notifications are evaluated from the configured cutoff time in IST.

## Backend Modules

| File | Responsibility |
| --- | --- |
| `backend/main.py` | FastAPI bootstrap, CORS, static mounts, favicon, health endpoint, websocket endpoint, lifespan worker |
| `backend/app/config.py` | Loads `.env` values into the `Settings` dataclass |
| `backend/app/database/mongo.py` | Motor client, counters, index creation, ID backfill |
| `backend/app/dependencies.py` | JWT authentication dependency and role guard |
| `backend/app/routes/auth.py` | Registration, login, OTP verification, password changes, profile updates |
| `backend/app/routes/attendance.py` | Student attendance stats and history |
| `backend/app/routes/teacher.py` | Department stats, attendance marking, exports, absent notifications |
| `backend/app/routes/student.py` | Student attendance summary |
| `backend/app/routes/admin.py` | Admin stats, user lifecycle, config, logs, reports, exports |
| `backend/app/services/user_service.py` | User creation, profile updates, password management, admin actions |
| `backend/app/services/attendance_service.py` | Attendance calculations, geofencing, marking, absent notices, report rows |
| `backend/app/services/face_service.py` | Face decoding, encoding extraction, similarity matching |
| `backend/app/services/email_service.py` | SMTP delivery and fallback console logging |
| `backend/app/services/report_service.py` | Excel and PDF export generation |
| `backend/app/services/security_service.py` | Security event logging and retrieval |
| `backend/app/realtime.py` | Websocket connection manager scaffold |
| `backend/app/utils/security.py` | Password hashing, JWT helper, OTP hashing |
| `backend/app/utils/geo.py` | Haversine distance and geofence checks |
| `backend/app/utils/time.py` | IST time helpers and date/time formatting |

## API Surface by Role

### Auth and profile

- `POST /register`
- `POST /login`
- `POST /verify-otp`
- `POST /resend-otp`
- `GET /users/me`
- `PATCH /users/me`
- `POST /users/me/change-password`

### Student

- `GET /student/stats`
- `GET /attendance/me/stats`
- `GET /attendance/me/history`

### Teacher

- `GET /teacher/dashboard-stats`
- `GET /teacher/department/stats`
- `GET /teacher/attendance/today`
- `POST /teacher/notifications/absent`
- `GET /teacher/department/students`
- `POST /teacher/mark-attendance`
- `POST /teacher/mark-attendance/manual/{student_id}`
- `GET /teacher/attendance/export`
- `GET /teacher/reports/export`

### Admin

- `GET /admin/stats`
- `GET /admin/users`
- `POST /admin/teachers`
- `POST /admin/accounts`
- `PATCH /admin/users/{user_id}`
- `POST /admin/users/{user_id}/set-active`
- `POST /admin/users/{user_id}/reset-password`
- `DELETE /admin/users/{user_id}`
- `GET /admin/config`
- `PATCH /admin/config`
- `GET /admin/security-logs`
- `GET /admin/logs`
- `GET /admin/attendance/export`
- `GET /admin/reports/export`
- `GET /admin/reports/weekly`
- `GET /admin/reports/punctuality`
- `GET /admin/reports/users-status`
- `GET /admin/reports/faculty`
- `GET /admin/locations`
- `GET /admin/reports/monthly-summary`
- `GET /admin/reports/attendance.csv`

### System

- `GET /`
- `GET /health`
- `WS /ws`

## Data Model

### `users`

Important fields stored on each account include:

- `id` - application-visible numeric ID from the counters collection.
- `full_name`, `email`, `roll_number`, `department`, `role`.
- `hashed_password`, `is_active`, `is_verified`, `is_admin`.
- `face_encoding`, `face_image` for student enrollment.
- `otp_hash`, `otp_expires_at` for registration verification.
- `preferences` for profile/settings sync.
- `blocked_reason` and `last_login_at` when applicable.

### `attendance`

Attendance records store:

- `id`, `user_id`, `date`, `check_in`, `status`.
- `marked_by_user_id`, `method`, `latitude`, `longitude`.
- `created_at`, `updated_at`.

### `security_logs`

Security records store:

- `id`, `event_type`, `severity`, `details`, `metadata`.
- `user_id`, `target_user_id`, `admin_user_id`.
- `ip_address`, `user_agent`, `created_at`.

### `config` and `counters`

- `config` stores the global admin-controlled security and geofence settings.
- `counters` stores the next sequence values for `users`, `attendance`, and `security_logs`.

## Business Rules

### Registration

- Registration only accepts Gmail addresses.
- Students must capture a single face image during enrollment.
- `face_service.extract_encoding()` rejects images with no face or multiple faces.
- Duplicate face detection compares the new encoding against all active student face encodings.
- If a duplicate is found, the existing account is suspended, the attempt is rejected, and a critical security log is written with `old_account` and `present_account` metadata.

### Authentication

- Login requires a valid password and a verified account.
- JWT tokens carry the email in the `sub` claim.
- Admins can create teacher and admin accounts from the control panel.
- Admin password confirmation is required for destructive or privileged actions.

### Attendance

- Teachers mark attendance only for students in their own department.
- Face-based marking uses `face_recognition` encodings and the configured tolerance.
- Manual marking is available as a department-scoped override.
- Geofencing is optional and uses Haversine distance against the campus coordinates.
- Attendance finalization depends on the configured absent-notice cutoff time.

### Reporting

- Student attendance percentage counts only finalized days.
- `Present` and `Late` count as attended.
- Completed unmarked days count as absent after the cutoff.
- Pending days remain pending until the day is finalized.
- Report exports support Excel and PDF output.

### Security and Notifications

- Absence notifications are sent after the cutoff time and logged to `security_logs`.
- Admin config updates are tracked with a warning-level security event.
- Password change notifications and registration success emails are sent through the email service.
- If SMTP is not configured, the email service logs the message body instead of failing silently.

## Frontend Surface

### Public pages

- `index.html` is the landing page.
- `login.html` handles login.
- `register.html` is the 3-step enrollment flow.
- `otp.html` is the standalone OTP verification page.
- `privacy_policy.html` documents the data handling policy.

### Student pages

- `user_dashboard.html` shows attendance metrics, a month calendar, and history.
- `user_profile.html` lets the student update visible identity fields and print an ID card.
- `user_settings.html` lets the student manage preferences and change the password.

### Teacher pages

- `teacher_dashboard.html` shows department totals, live today rows, and absence dispatch.
- `teacher_mark_attendance.html` performs face capture and manual override.
- `teacher_students.html` lists department students.
- `teacher_view_attendance.html` shows the department attendance timeline.
- `teacher_reports.html` exports reports and sends absent notifications.
- `teacher_profile.html` edits the faculty profile.
- `teacher_settings.html` manages password and live preference sync.

### Admin pages

- `admin_dashboard.html` shows system KPIs and recent logs.
- `admin_users.html` manages users and account creation.
- `admin_reports.html` provides charts, monthly summaries, and export controls.
- `admin_security.html` shows live threat metrics, policy toggles, duplicate review, and audit logs.
- `admin_settings.html` edits global settings, geofence parameters, and notification cutoffs.
- `admin_profile.html` edits admin profile details and password.

## Frontend Scripts and Styles

Active scripts in the inspected pages:

- `frontend/js/api.js` - shared API helper and auth wrapper.
- `frontend/js/auth.js` - login, register, OTP, and camera capture logic.
- `frontend/js/dashboard.js` - role-aware dashboard loading and polling.
- `frontend/js/teacher.js` - teacher camera, geolocation, attendance marking, and absent dispatch.
- `frontend/js/student-dashboard.js` - monthly attendance calendar and summary rendering.
- `frontend/js/auth-visuals.js` - animated 3D backgrounds for auth and landing pages.

Auxiliary files present in the repository:

- `frontend/js/main.js` - landing-page preloader and hover motion helper.
- `frontend/js/layout-enhance.js` - shared layout helper for active nav and mobile sidebar behavior.

Shared CSS files:

- `frontend/css/core.css` - design tokens and shared components.
- `frontend/css/style.css` - landing and public page styling.
- `frontend/css/auth.css` - auth page styling.
- `frontend/css/dashboard.css` - dashboard layouts, cards, tables, and admin/teacher/student shells.

## Setup and Maintenance Notes

- Use `install_deps_windows.bat` on Windows to avoid a local dlib build.
- `create_admin.py` seeds or updates the system administrator account.
- `create_teachers.py` seeds teacher accounts for the sample departments.
- `check_db.py` is a quick MongoDB inspection helper for config and security logs.
- `test_import.py` checks the Python dependency stack.
- `test_register.py` is a basic registration request smoke test.
- `backend/.env.example` documents the runtime configuration keys used by the current code.

## Design and UX System

- The landing page uses a deep-space background with animated orbs and rings.
- The auth pages use the glassmorphic two-column shell and the 3-step enrollment wizard.
- The dashboards share a stable sidebar/top-bar/page-stack layout.
- Teacher and admin screens emphasize telemetry, charts, and dense operational cards.
- Student screens emphasize a calendar-first attendance view and editable identity profile.

## Notes on Realtime

The websocket endpoint and connection manager are present, and the teacher dashboard is prepared to react to `attendance_marked` events. In the current code, the practical refresh path is still polling, so the UI remains current even without push events.

## Deployment Boundary

The application is intended to be served from the FastAPI backend. Do not open the HTML files directly from disk; open them through `http://127.0.0.1:8000/static/...` so browser requests can reach the API.