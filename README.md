# Smart Attendance System Using Face Recognition

Smart Attendance System Using Face Recognition is a full-stack attendance platform that combines face recognition, OTP verification, role-based portals, geofenced attendance capture, scheduled absence notifications, and audit logging.

## What It Includes

- Student self-registration with face capture and email OTP verification.
- Teacher attendance marking by face or manual override, scoped to the teacher's department.
- Student dashboards with attendance history, monthly calendar view, profile editing, and preference controls.
- Admin dashboards for user lifecycle management, reporting, security review, and system configuration.
- FastAPI backend served with static HTML/CSS/JS assets from the same application.
- MongoDB persistence with auto-incrementing IDs, counters, and unique indexes.
- Scheduled absence emails and security audit logs.

## Architecture

- `backend/main.py` boots FastAPI, mounts the frontend under `/static`, starts the lifespan hook, ensures indexes, and launches the absence worker.
- `backend/app/database/mongo.py` manages the async Motor client, collection indexes, and counters.
- `backend/app/routes/*.py` holds the HTTP API by role.
- `backend/app/services/*.py` contains the business logic for attendance, users, face matching, reports, email, and security logs.
- `frontend/js/*.js` contains the shared API client, auth flows, dashboard loaders, teacher tools, and student calendar logic.
- `frontend/css/*.css` provides the shared design system, auth theme, and dashboard layout system.

## Project Structure

```text
backend/
  .env.example
  main.py
  create_admin.py
  create_teachers.py
  check_db.py
  install_deps_windows.bat
  requirements.txt
  app/
    config.py
    database/
    dependencies.py
    realtime.py
    routes/
    services/
    utils/
frontend/
  index.html
  login.html
  register.html
  otp.html
  privacy_policy.html
  user_*.html
  teacher_*.html
  admin_*.html
  css/
  js/
```

## Key Pages

| Area | Pages |
| --- | --- |
| Public | `index.html`, `login.html`, `register.html`, `otp.html`, `privacy_policy.html` |
| Student | `user_dashboard.html`, `user_profile.html`, `user_settings.html` |
| Teacher | `teacher_dashboard.html`, `teacher_mark_attendance.html`, `teacher_students.html`, `teacher_view_attendance.html`, `teacher_reports.html`, `teacher_profile.html`, `teacher_settings.html` |
| Admin | `admin_dashboard.html`, `admin_users.html`, `admin_reports.html`, `admin_security.html`, `admin_settings.html`, `admin_profile.html` |

## Setup

### 1. Create a virtual environment

```bash
cd backend
py -3.11 -m venv ..\venv
..\venv\Scripts\activate
```

### 2. Install dependencies

On Windows, run the helper script:

```bash
install_deps_windows.bat
```

The script installs the base requirements and then installs `face-recognition` with `--no-deps` so dlib does not try to build from source on Windows.

Do not run `pip install face_recognition` directly on Windows. That path pulls in `dlib` source builds and usually fails unless Visual C++ build tools are already installed.

For a manual install:

```bash
pip install -r requirements.txt
pip install face-recognition==1.3.0 --no-deps
```

On non-Windows platforms, `pip install -r requirements.txt` is normally enough because the requirements file already pins the compatible `dlib`/`face-recognition` variants.

### 3. Configure environment variables

Copy [backend/.env.example](backend/.env.example) to [backend/.env](backend/.env) and update the values for your environment.

Important values:

- `SECRET_KEY`
- `MONGODB_URI`
- `MONGODB_DB`
- `FRONTEND_BASE_URL`
- `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM`
- `CAMPUS_LAT`, `CAMPUS_LON`, `MAX_DISTANCE_KM`
- `LATE_HOUR`, `LATE_MINUTE`
- `ABSENT_NOTICE_HOUR`, `ABSENT_NOTICE_MINUTE`
- `FACE_TOLERANCE`
- Optional toggles: `FACE_RECOGNITION_ENABLED`, `MFA_ENABLED`, `GEOFENCING_ENABLED`, `LOCKOUT_ENABLED`

`FRONTEND_BASE_URL` should point to the static frontend root, for example `http://127.0.0.1:8000/static`.

### 4. Create the admin account

```bash
python create_admin.py
```

### 5. Seed teacher accounts

```bash
python create_teachers.py
```

### 6. Run the API server

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open the app through FastAPI, not `file://`.

Useful entry points:

- [Landing page](http://127.0.0.1:8000/static/index.html)
- [Login page](http://127.0.0.1:8000/static/login.html)
- [Register page](http://127.0.0.1:8000/static/register.html)

## Frontend System

- `frontend/css/core.css` holds the shared color tokens, fonts, glassmorphism surface, and button styles.
- `frontend/css/style.css` styles the landing page and public-facing screens.
- `frontend/css/auth.css` styles the login, registration, and OTP flows.
- `frontend/css/dashboard.css` styles the admin, teacher, and student workspace layouts.
- `frontend/js/api.js` is the shared same-origin API client and auth helper.
- `frontend/js/auth.js` drives login, registration, camera capture, and OTP verification.
- `frontend/js/dashboard.js` loads role-aware dashboard data and polling updates.
- `frontend/js/teacher.js` handles teacher camera capture, geolocation, manual attendance, and absence dispatch.
- `frontend/js/student-dashboard.js` renders the student calendar, monthly summary, and attendance history.
- `frontend/js/auth-visuals.js` powers the animated 3D backgrounds.
- `frontend/js/main.js` contains auxiliary landing-page preloader and hover motion helpers.

## Key API Surface

### Auth and profile

- `POST /register`
- `POST /login`
- `POST /verify-otp`
- `POST /resend-otp`
- `GET /users/me`
- `PATCH /users/me`
- `POST /users/me/change-password`

### Student and attendance

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

## Operational Notes

- Student registration only accepts Gmail addresses.
- Attendance percentages use finalized days only: `Present + Late` count as attended, completed unmarked days count as absent, and pending days stay excluded until the cutoff.
- Absent notices are sent after the configured cutoff, usually `17:00 IST`.
- Admin password resets use the temporary password `SASUFR`.
- The websocket endpoint exists, but dashboards still refresh with polling as a fallback.
- Teacher attendance marking can be face-based or manual, and both are limited to the teacher's department.
- Geofencing is optional and uses the campus coordinates from `.env` or the admin settings screen.

## Development Notes

- The backend uses Motor with MongoDB and an explicit `counters` collection for application-visible IDs.
- Face matching uses `face_recognition` encodings and the configured `FACE_TOLERANCE` threshold.
- Background absence emails are triggered from the FastAPI lifespan worker once the daily cutoff has passed.
- If SMTP is not configured, email payloads fall back to console logging for local development.

For the deeper architecture write-up, see [Smart_Attendance_FullStack.md](Smart_Attendance_FullStack.md).