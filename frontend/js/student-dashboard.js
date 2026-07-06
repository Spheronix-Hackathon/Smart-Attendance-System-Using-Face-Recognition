(function () {
    const state = {
        stats: null,
        history: [],
    };

    function pad(value) {
        return String(value).padStart(2, '0');
    }

    function currentMonthValue(date = new Date()) {
        return `${date.getFullYear()}-${pad(date.getMonth() + 1)}`;
    }

    function normalizeStatus(status) {
        return String(status || '').trim().toLowerCase();
    }

    function parseDateOnly(value) {
        if (!value) return null;
        const datePart = String(value).slice(0, 10);
        const [year, month, day] = datePart.split('-').map(Number);
        if (!year || !month || !day) return null;
        return new Date(year, month - 1, day);
    }

    function formatDateOnly(date) {
        return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
    }

    function todayDateOnly() {
        const date = new Date();
        date.setHours(0, 0, 0, 0);
        return date;
    }

    function compareDates(left, right) {
        return left.getTime() - right.getTime();
    }

    function maxDate(left, right) {
        return compareDates(left, right) >= 0 ? left : right;
    }

    function minDate(left, right) {
        return compareDates(left, right) <= 0 ? left : right;
    }

    function addDays(date, days) {
        const clone = new Date(date);
        clone.setDate(clone.getDate() + days);
        return clone;
    }

    function diffDaysInclusive(startDate, endDate) {
        if (compareDates(endDate, startDate) < 0) return 0;
        const milliseconds = endDate.getTime() - startDate.getTime();
        return Math.floor(milliseconds / 86400000) + 1;
    }

    function monthLabel(monthValue) {
        const [year, month] = monthValue.split('-').map(Number);
        if (!year || !month) return '--';
        return new Date(year, month - 1, 1).toLocaleString('en-US', {
            month: 'long',
            year: 'numeric',
        });
    }

    function yearFromMonth(monthValue) {
        const year = Number(String(monthValue || '').slice(0, 4));
        return Number.isFinite(year) && year > 0 ? year : new Date().getFullYear();
    }

    function daysInMonth(monthValue) {
        const [year, month] = monthValue.split('-').map(Number);
        if (!year || !month) return 0;
        return new Date(year, month, 0).getDate();
    }

    function isCurrentVisibleMonth(date, monthValue) {
        const [year, month] = monthValue.split('-').map(Number);
        return (
            year === date.getFullYear() &&
            month === date.getMonth() + 1
        );
    }

    function startOfMonth(monthValue) {
        const [year, month] = monthValue.split('-').map(Number);
        return new Date(year, month - 1, 1);
    }

    function endOfMonth(monthValue) {
        const [year, month] = monthValue.split('-').map(Number);
        return new Date(year, month, 0);
    }

    function startOfYear(yearValue) {
        return new Date(Number(yearValue), 0, 1);
    }

    function endOfYear(yearValue) {
        return new Date(Number(yearValue), 11, 31);
    }

    function getRecordMap(history) {
        const map = new Map();
        for (const record of history) {
            if (record && record.date) {
                map.set(String(record.date).slice(0, 10), record);
            }
        }
        return map;
    }

    function getBaselineDate(history = []) {
        const fromStats = parseDateOnly(state.stats?.calculation_start_date);
        if (fromStats) return fromStats;

        const fromUser = parseDateOnly(window.currentUser?.created_at);
        if (fromUser) return fromUser;

        const sorted = history
            .map((record) => parseDateOnly(record.date))
            .filter(Boolean)
            .sort((left, right) => compareDates(left, right));
        if (sorted.length) return sorted[0];

        return todayDateOnly();
    }

    function getFinalizedThroughDate(history = []) {
        const fromStats = parseDateOnly(state.stats?.calculation_through_date);
        if (fromStats) return fromStats;

        const today = todayDateOnly();
        const todayKey = formatDateOnly(today);
        const hasTodayRecord = history.some((record) => String(record?.date || '').slice(0, 10) === todayKey);
        if (hasTodayRecord) return today;
        return today;
    }

    function buildPeriodSummary(history, periodStart, periodEnd, baselineDate, finalizedThroughDate) {
        const start = maxDate(periodStart, baselineDate);
        const end = minDate(periodEnd, finalizedThroughDate);
        const recordMap = getRecordMap(history);

        let present = 0;
        let late = 0;
        let absent = 0;

        if (compareDates(end, start) >= 0) {
            for (let current = new Date(start); compareDates(current, end) <= 0; current = addDays(current, 1)) {
                const record = recordMap.get(formatDateOnly(current));
                const status = normalizeStatus(record?.status);

                if (status === 'present') {
                    present += 1;
                } else if (status === 'late') {
                    late += 1;
                } else {
                    absent += 1;
                }
            }
        }

        const attended = present + late;
        const marked = present + late + absent;
        const percentage = marked > 0 ? Math.round((attended / marked) * 1000) / 10 : 0;
        const pending = compareDates(periodEnd, finalizedThroughDate) > 0
            ? diffDaysInclusive(maxDate(maxDate(addDays(finalizedThroughDate, 1), periodStart), baselineDate), periodEnd)
            : 0;

        return {
            present,
            late,
            absent,
            attended,
            marked,
            pending,
            percentage,
            recordCount: marked,
        };
    }

    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    function setHTML(id, value) {
        const el = document.getElementById(id);
        if (el) el.innerHTML = value;
    }

    function renderCalendar(monthValue, history, baselineDate, finalizedThroughDate) {
        const grid = document.getElementById('attendanceCalendarGrid');
        if (!grid) return;

        const [year, month] = monthValue.split('-').map(Number);
        if (!year || !month) {
            grid.innerHTML = '';
            return;
        }

        const firstDay = new Date(year, month - 1, 1);
        const totalDays = new Date(year, month, 0).getDate();
        const offset = firstDay.getDay();
        const today = todayDateOnly();
        const recordsByDate = getRecordMap(history);

        grid.innerHTML = '';

        for (let index = 0; index < offset; index += 1) {
            const emptyCell = document.createElement('div');
            emptyCell.className = 'calendar-day is-empty';
            grid.appendChild(emptyCell);
        }

        for (let day = 1; day <= totalDays; day += 1) {
            const date = new Date(year, month - 1, day);
            date.setHours(0, 0, 0, 0);
            const dateKey = `${monthValue}-${pad(day)}`;
            const record = recordsByDate.get(dateKey) || null;
            const normalized = normalizeStatus(record?.status);
            const isBeforeBaseline = compareDates(date, baselineDate) < 0;
            const isFuture = compareDates(date, today) > 0;
            const isPending = compareDates(date, finalizedThroughDate) > 0 && compareDates(date, today) <= 0;

            let cellStatus = 'unmarked';
            let statusLabel = 'Unmarked';
            let meta = 'No attendance recorded yet';

            if (isBeforeBaseline) {
                cellStatus = 'empty';
                statusLabel = 'Pre-Enrollment';
                meta = 'Before enrollment';
            } else if (isFuture) {
                cellStatus = 'future';
                statusLabel = 'Upcoming';
                meta = 'Awaiting class day';
            } else if (record) {
                if (normalized === 'present') {
                    cellStatus = 'present';
                    statusLabel = 'Present';
                    meta = `${String(record.check_in || '--:--').slice(0, 5)} • ${record.method === 'face' ? 'Biometric' : 'Manual'}`;
                } else if (normalized === 'late') {
                    cellStatus = 'late';
                    statusLabel = 'Late';
                    meta = `${String(record.check_in || '--:--').slice(0, 5)} • ${record.method === 'face' ? 'Biometric' : 'Manual'}`;
                } else if (normalized === 'absent') {
                    cellStatus = 'absent';
                    statusLabel = 'Absent';
                    meta = 'Marked absent';
                }
            } else if (isPending) {
                cellStatus = 'pending';
                statusLabel = 'Pending';
                meta = 'Not finalized';
            } else {
                cellStatus = 'absent';
                statusLabel = 'Absent';
                meta = 'No record, counted absent';
            }

            const cell = document.createElement('div');
            cell.className = `calendar-day is-${cellStatus}`;
            cell.title = `${date.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' })} • ${statusLabel}`;
            cell.innerHTML = `
                <div class="calendar-day-number">${day}</div>
                <div class="calendar-day-status">${statusLabel}</div>
                <div class="calendar-day-meta">${meta}</div>
            `;
            grid.appendChild(cell);
        }
    }

    function renderSummaryCard(prefix, summary, labelPrefix, label) {
        setText(`${labelPrefix}AttendancePercent`, `${summary.percentage.toFixed(1)}%`);
        setText(`${labelPrefix}PeriodLabel`, labelPrefix === 'year' ? `Year ${label}` : label);
        setHTML(
            `${labelPrefix}FormulaText`,
            summary.marked > 0
                ? `<strong>${label} Attendance</strong> uses <strong>(${summary.attended} attended) / (${summary.marked} finalized days) × 100</strong>. Absent includes teacher-marked absences plus any completed unmarked days. Pending days are not counted yet.`
                : `<strong>${label} Attendance</strong> has no finalized days yet. The percentage stays at 0% until a day is completed or attendance is recorded.`
        );
        setText(`${labelPrefix}PresentCount`, summary.present);
        setText(`${labelPrefix}LateCount`, summary.late);
        setText(`${labelPrefix}AbsentCount`, summary.absent);
        setText(`${labelPrefix}AttendedCount`, summary.attended);
        setText(`${labelPrefix}MarkedCount`, summary.marked);
        setText(`${labelPrefix}PendingCount`, summary.pending);
    }

    function renderStudentAttendance() {
        if (!state.stats && !window.studentAttendanceStats) {
            return;
        }

        const monthInput = document.getElementById('attendanceMonthPicker');
        if (!monthInput) return;

        const monthValue = monthInput.value || currentMonthValue();
        const yearValue = yearFromMonth(monthValue);
        const history = state.history || [];
        const baselineDate = getBaselineDate(history);
        const finalizedThroughDate = getFinalizedThroughDate(history);
        const monthSummary = buildPeriodSummary(history, startOfMonth(monthValue), endOfMonth(monthValue), baselineDate, finalizedThroughDate);
        const yearPrefix = String(yearValue);
        const yearSummary = buildPeriodSummary(history, startOfYear(yearValue), endOfYear(yearValue), baselineDate, finalizedThroughDate);

        setText('attendanceCalendarMonthLabel', monthLabel(monthValue));
        setText('attendanceCalendarYearLabel', String(yearValue));
        setText('attendanceCalculationNote', `Present and Late count as attended. Absent includes teacher-marked absences and completed unmarked days. Pending days are visible in gray until the school day is finalized. Calculation window: ${formatDateOnly(baselineDate)} to ${formatDateOnly(finalizedThroughDate)}.`);

        renderCalendar(monthValue, history, baselineDate, finalizedThroughDate);
        renderSummaryCard(monthValue, monthSummary, 'month', monthLabel(monthValue));
        renderSummaryCard(yearPrefix, yearSummary, 'year', String(yearValue));
    }

    function applyStudentStats(stats) {
        state.stats = stats || null;
        state.history = Array.isArray(stats?.history) ? stats.history : (Array.isArray(window.studentAttendanceHistory) ? window.studentAttendanceHistory : []);
        renderStudentAttendance();
    }

    document.addEventListener('student-attendance-stats-loaded', (event) => {
        applyStudentStats(event.detail || window.studentAttendanceStats || null);
    });

    document.addEventListener('DOMContentLoaded', () => {
        const monthInput = document.getElementById('attendanceMonthPicker');
        if (monthInput && !monthInput.value) {
            monthInput.value = currentMonthValue();
        }

        monthInput?.addEventListener('change', () => {
            renderStudentAttendance();
        });

        if (window.studentAttendanceStats || window.studentAttendanceHistory) {
            applyStudentStats(window.studentAttendanceStats || { history: window.studentAttendanceHistory || [] });
        }

        renderStudentAttendance();
    });
})();
