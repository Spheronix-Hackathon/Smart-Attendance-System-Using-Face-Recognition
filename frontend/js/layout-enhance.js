(function () {
    function normalizePath(path) {
        return String(path || '').replace(/^\/+/, '').toLowerCase();
    }

    function highlightActiveNav() {
        const current = normalizePath(window.location.pathname.split('/').pop() || '');
        if (!current) return;

        document.querySelectorAll('.sidebar-nav li').forEach((li) => li.classList.remove('active'));

        const links = Array.from(document.querySelectorAll('.sidebar-nav a[href]'));
        const match = links.find((link) => normalizePath(link.getAttribute('href')) === current);
        if (match) {
            const li = match.closest('li');
            if (li) li.classList.add('active');
        }
    }

    function installMobileSidebarToggle() {
        const body = document.body;
        const topBar = document.querySelector('.top-bar');
        const sidebar = document.querySelector('.sidebar');
        if (!topBar || !sidebar) return;

        let toggle = topBar.querySelector('.mobile-sidebar-toggle');
        if (!toggle) {
            toggle = document.createElement('button');
            toggle.type = 'button';
            toggle.className = 'mobile-sidebar-toggle';
            toggle.setAttribute('aria-label', 'Toggle navigation');
            toggle.setAttribute('aria-expanded', 'false');
            toggle.innerHTML = '<i class="fa-solid fa-bars"></i>';
            topBar.insertBefore(toggle, topBar.firstChild);
        }

        function setOpenState(open) {
            body.classList.toggle('sidebar-open', open);
            toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
            toggle.innerHTML = open
                ? '<i class="fa-solid fa-xmark"></i>'
                : '<i class="fa-solid fa-bars"></i>';
        }

        toggle.addEventListener('click', () => {
            setOpenState(!body.classList.contains('sidebar-open'));
        });

        document.addEventListener('click', (event) => {
            if (!body.classList.contains('sidebar-open')) return;
            const target = event.target;
            if (!(target instanceof Element)) return;

            const clickInsideSidebar = target.closest('.sidebar');
            const clickOnToggle = target.closest('.mobile-sidebar-toggle');
            if (!clickInsideSidebar && !clickOnToggle) {
                setOpenState(false);
            }
        });

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') setOpenState(false);
        });

        window.addEventListener('resize', () => {
            if (window.innerWidth > 700) {
                setOpenState(false);
            }
        });
    }

    function revealPage() {
        document.body.classList.add('dashboard-page');
        window.requestAnimationFrame(() => {
            window.requestAnimationFrame(() => {
                document.body.classList.add('page-ready');
            });
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        revealPage();
        highlightActiveNav();
        installMobileSidebarToggle();
    });
})();
