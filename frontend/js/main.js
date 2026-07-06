function initPreloader() {
    const preloader = document.getElementById('preloader');
    if (!preloader) return;

    window.addEventListener('load', () => {
        preloader.style.opacity = '0';
        setTimeout(() => {
            preloader.style.display = 'none';
        }, 350);
    });
}

function initHoverMotion() {
    const orb = document.querySelector('.hero-orb');
    if (!orb) return;

    window.addEventListener('mousemove', (event) => {
        const dx = (event.clientX / window.innerWidth - 0.5) * 8;
        const dy = (event.clientY / window.innerHeight - 0.5) * 8;
        orb.style.transform = `translate(${dx}px, ${dy}px)`;
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initPreloader();
    initHoverMotion();
});
