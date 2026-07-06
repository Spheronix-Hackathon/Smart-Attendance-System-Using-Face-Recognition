(function () {
    function createOrbMesh(container, options = {}) {
        if (!container || !window.THREE || container.dataset.orbReady === 'true') return;
        container.dataset.orbReady = 'true';

        const scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x060c18, 0.08);

        const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        renderer.setClearColor(0x000000, 0);
        container.appendChild(renderer.domElement);

        const orbGroup = new THREE.Group();
        scene.add(orbGroup);

        const outerGeometry = new THREE.IcosahedronGeometry(options.radius || 1.15, 2);
        const outerMaterial = new THREE.MeshBasicMaterial({
            color: 0x00d1c7,
            wireframe: true,
            transparent: true,
            opacity: 0.34,
        });
        const outerMesh = new THREE.Mesh(outerGeometry, outerMaterial);
        orbGroup.add(outerMesh);

        const latticeGeometry = new THREE.IcosahedronGeometry((options.radius || 1.15) * 0.88, 1);
        const latticeMaterial = new THREE.MeshBasicMaterial({
            color: 0x6f45ff,
            wireframe: true,
            transparent: true,
            opacity: 0.22,
        });
        const latticeMesh = new THREE.Mesh(latticeGeometry, latticeMaterial);
        orbGroup.add(latticeMesh);

        const coreGeometry = new THREE.IcosahedronGeometry((options.radius || 1.15) * 0.62, 1);
        const coreMaterial = new THREE.MeshBasicMaterial({
            color: 0xb78cff,
            wireframe: true,
            transparent: true,
            opacity: 0.12,
        });
        const coreMesh = new THREE.Mesh(coreGeometry, coreMaterial);
        orbGroup.add(coreMesh);

        function makeRing(radius, color, opacity, rotation) {
            const points = [];
            const segments = 160;
            for (let index = 0; index <= segments; index += 1) {
                const angle = (index / segments) * Math.PI * 2;
                points.push(new THREE.Vector3(Math.cos(angle) * radius, Math.sin(angle) * radius, 0));
            }
            const geometry = new THREE.BufferGeometry().setFromPoints(points);
            const material = new THREE.LineBasicMaterial({ color, transparent: true, opacity });
            const ring = new THREE.LineLoop(geometry, material);
            ring.rotation.set(rotation[0], rotation[1], rotation[2]);
            return ring;
        }

        const ringGroup = new THREE.Group();
        ringGroup.add(makeRing((options.radius || 1.15) * 1.05, 0x00d1c7, 0.18, [0.32, 0.18, 0.05]));
        ringGroup.add(makeRing((options.radius || 1.15) * 0.86, 0x6f45ff, 0.16, [1.1, 0.3, 0.12]));
        ringGroup.add(makeRing((options.radius || 1.15) * 0.72, 0x00d1c7, 0.12, [0.12, 0.78, 1.12]));
        scene.add(ringGroup);

        const particleGeometry = new THREE.BufferGeometry();
        const particleCount = options.particles || 72;
        const positions = new Float32Array(particleCount * 3);
        for (let index = 0; index < particleCount; index += 1) {
            const radius = 1.65 + (Math.random() * 0.5);
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);
            positions[index * 3] = Math.sin(phi) * Math.cos(theta) * radius;
            positions[index * 3 + 1] = Math.sin(phi) * Math.sin(theta) * radius;
            positions[index * 3 + 2] = Math.cos(phi) * radius;
        }
        particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        const particleMaterial = new THREE.PointsMaterial({
            size: 0.018,
            color: 0x7b6dff,
            transparent: true,
            opacity: 0.6,
        });
        const particles = new THREE.Points(particleGeometry, particleMaterial);
        scene.add(particles);

        function resize() {
            const width = container.clientWidth || 1;
            const height = container.clientHeight || 1;
            renderer.setSize(width, height, false);
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
        }

        resize();

        const resizeObserver = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(resize) : null;
        if (resizeObserver) resizeObserver.observe(container);
        window.addEventListener('resize', resize);

        function animate() {
            requestAnimationFrame(animate);
            orbGroup.rotation.y += 0.0032;
            orbGroup.rotation.x += 0.0013;
            ringGroup.rotation.y -= 0.0013;
            ringGroup.rotation.x += 0.0008;
            particles.rotation.y -= 0.0008;
            particles.rotation.x += 0.0005;
            renderer.render(scene, camera);
        }

        camera.position.z = options.cameraZ || 3.95;
        animate();
    }

    function mountOrbMeshes() {
        document.querySelectorAll('.hero-orb, .side-orb').forEach((container) => {
            const isHero = container.classList.contains('hero-orb');
            createOrbMesh(container, {
                radius: isHero ? 1.25 : 1.05,
                cameraZ: isHero ? 4.25 : 4.75,
                particles: isHero ? 80 : 48,
            });
        });
    }

    document.addEventListener('DOMContentLoaded', mountOrbMeshes);
})();