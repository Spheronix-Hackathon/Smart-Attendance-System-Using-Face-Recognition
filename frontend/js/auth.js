const API_URL = window.location.origin;

const safeStorage = {
    setItem: (key, value) => {
        try {
            localStorage.setItem(key, value);
        } catch {
            // no-op
        }
    },
    getItem: (key) => {
        try {
            return localStorage.getItem(key);
        } catch {
            return null;
        }
    }
};

// --- AUTH LOG VERSION: 1.2 ---

function showError(id, message) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = message;
    el.style.display = 'block';
}

function showErrorWithAction(id, message, actionText, actionFn) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = `${message} <button type="button" class="error-action-btn" style="background: var(--accent); color: #000; border: none; padding: 4px 12px; border-radius: 4px; margin-left: 10px; font-size: 0.7rem; font-weight: 900; cursor: pointer; transition: 0.3s; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0, 209, 199, 0.2);"> ${actionText} </button>`;
    el.style.display = 'block';
    const btn = el.querySelector('.error-action-btn');
    if (btn) btn.onclick = actionFn;
}

function hideError(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
    initLogin();
    initRegister();
    initOtp();
});

function initLogin() {
    const loginForm = document.getElementById('loginForm');
    if (!loginForm) return;

    const forgotLink = loginForm.querySelector('a[href="#"]');
    if (forgotLink) {
        forgotLink.addEventListener('click', (event) => {
            event.preventDefault();
            alert('Password can only be reset by Admin. Please contact your administrator.');
        });
    }

    const manualVerifyLink = document.getElementById('manualVerifyLink');
    if (manualVerifyLink) {
        manualVerifyLink.addEventListener('click', (e) => {
            e.preventDefault();
            const email = prompt("Please enter the email address you registered with:");
            if (email && email.trim()) {
                if (!email.trim().toLowerCase().endsWith('@gmail.com')) {
                    alert('Only @gmail.com addresses are permitted.');
                    return;
                }
                safeStorage.setItem('pendingEmail', email.trim());
                window.location.href = `register.html?verify=true&email=${encodeURIComponent(email.trim())}`;
            }
        });
    }

    // Password Toggle
    const togglePassword = loginForm.querySelector('#togglePassword');
    const passwordInput = loginForm.querySelector('#password');
    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', () => {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            togglePassword.classList.toggle('fa-eye');
            togglePassword.classList.toggle('fa-eye-slash');
        });
    }

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError('loginError');

        const email = document.getElementById('email')?.value?.trim();
        const password = document.getElementById('password')?.value;

        try {
            const response = await fetch(`${API_URL}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (!response.ok) {
                if (data.detail && (data.detail.includes('Account verification is required') || data.detail.includes('Account unverified'))) {
                    safeStorage.setItem('pendingEmail', email);
                    showErrorWithAction('loginError', data.detail, 'VERIFY_NOW', () => {
                        window.location.href = 'register.html?verify=true';
                    });
                    return;
                }
                showError('loginError', data.detail || 'Login failed');
                return;
            }

            safeStorage.setItem('token', data.access_token);

            const meResponse = await fetch(`${API_URL}/users/me`, {
                headers: { 'Authorization': `Bearer ${data.access_token}` }
            });

            if (!meResponse.ok) {
                window.location.href = 'user_dashboard.html';
                return;
            }

            const me = await meResponse.json();
            const role = String(me.role || '').toLowerCase();

            if (me.is_admin || role === 'admin') {
                window.location.href = 'admin_dashboard.html';
            } else if (role === 'teacher') {
                window.location.href = 'teacher_dashboard.html';
            } else {
                window.location.href = 'user_dashboard.html';
            }
        } catch {
            showError('loginError', 'Network error. Please try again.');
        }
    });
}

function initRegister() {
    const registerForm = document.getElementById('registrationForm');
    if (!registerForm) return;

    const step1 = document.getElementById('registrationStep1');
    const step2 = document.getElementById('registrationStep2');
    const step3 = document.getElementById('registrationStep3');

    const step1Circle = document.getElementById('step1Circle');
    const step2Circle = document.getElementById('step2Circle');
    const step3Circle = document.getElementById('step3Circle');

    const stepLine1 = document.getElementById('stepLine1');
    const stepLine2 = document.getElementById('stepLine2');

    const nextBtn = document.getElementById('nextToStep2');
    const backBtn = document.getElementById('backToStep1');
    const startCameraBtn = document.getElementById('startCameraBtn');
    const captureBtn = document.getElementById('captureBtn');
    const submitBtn = document.getElementById('submitRegistration');
    const verifyOtpBtn = document.getElementById('verifyOtpBtn');
    const resendOtpBtn = document.getElementById('resendOtpBtn');

    const video = document.getElementById('cameraPreview');
    const facePreview = document.getElementById('facePreview');
    const canvas = document.getElementById('faceCanvas');
    const faceImageInput = document.getElementById('faceImage');
    const cameraPlaceholder = document.getElementById('cameraPlaceholder');
    const displayEmail = document.getElementById('displayEmail');
    const otpTimer = document.getElementById('otpTimer');

    const sideTitle = document.getElementById('sideTitle');
    const sideDesc = document.getElementById('sideDesc');
    const sideFeatures = document.getElementById('sideFeatures');

    let stream = null;
    let currentStep = 1;
    let faceRecognitionAvailable = true;

    function setFaceRecognitionUnavailable(message) {
        faceRecognitionAvailable = false;
        if (nextBtn) nextBtn.disabled = true;
        if (startCameraBtn) startCameraBtn.disabled = true;
        if (captureBtn) captureBtn.disabled = true;
        if (submitBtn) submitBtn.disabled = true;
        if (cameraPlaceholder) {
            cameraPlaceholder.innerHTML = '<div style="text-align:center;padding:24px;line-height:1.6"><strong>Face recognition unavailable</strong><br><span style="font-size:0.92rem;opacity:0.85">' + message + '</span></div>';
            cameraPlaceholder.style.display = 'grid';
        }
        if (sideTitle) sideTitle.textContent = 'Face recognition unavailable';
        if (sideDesc) sideDesc.textContent = 'Install the Windows face-recognition dependencies before registering a student account.';
        if (sideFeatures) {
            sideFeatures.innerHTML = `
                <div class="feature-pill"><i class="fa-solid fa-triangle-exclamation"></i> Windows setup required</div>
                <div class="feature-pill"><i class="fa-solid fa-check"></i> Use install_deps_windows.bat</div>
                <div class="feature-pill"><i class="fa-solid fa-check"></i> Then refresh the page</div>
            `;
        }
        showError('registrationError', message);
    }

    async function loadFaceRecognitionStatus() {
        try {
            const response = await fetch(`${API_URL}/health`);
            if (!response.ok) return;

            const health = await response.json();
            if (health.face_recognition_available === false) {
                const detail = health.face_recognition_error
                    ? `Face recognition is unavailable: ${health.face_recognition_error}. Run backend\\install_deps_windows.bat or install face-recognition==1.3.0 --no-deps, then refresh this page.`
                    : 'Face recognition is unavailable in this environment. Run backend\\install_deps_windows.bat or install face-recognition==1.3.0 --no-deps, then refresh this page.';
                setFaceRecognitionUnavailable(detail);
            }
        } catch {
            // Leave the registration flow unchanged if the health check is unreachable.
        }
    }

    // Password Toggle
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');
    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', () => {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            togglePassword.classList.toggle('fa-eye');
            togglePassword.classList.toggle('fa-eye-slash');
        });
    }

    loadFaceRecognitionStatus();

    function stopCamera() {
        console.log("Stopping camera...");
        if (stream) {
            stream.getTracks().forEach(track => {
                track.stop();
                track.enabled = false;
            });
            stream = null;
        }
        if (video) {
            video.srcObject = null;
            video.style.display = 'none';
        }
        if (cameraPlaceholder) {
            cameraPlaceholder.style.display = 'grid';
            cameraPlaceholder.style.opacity = '1';
        }
        if (startCameraBtn) {
            startCameraBtn.innerHTML = '<i class="fa-solid fa-video"></i> Start Camera';
            startCameraBtn.style.background = ''; // Reset to default
        }
    }

    async function startCamera() {
        if (stream) {
            stopCamera();
            return;
        }
        console.log("Starting camera...");
        try {
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: { ideal: 640 }, height: { ideal: 480 } } 
            });
            
            if (video) {
                video.srcObject = stream;
                video.style.display = 'block';
                video.style.opacity = '1';
            }
            
            if (facePreview) facePreview.style.display = 'none';
            if (cameraPlaceholder) cameraPlaceholder.style.display = 'none';
            
            if (startCameraBtn) {
                startCameraBtn.innerHTML = '<i class="fa-solid fa-stop"></i> Stop Camera';
                startCameraBtn.style.background = 'rgba(255, 90, 111, 0.15)'; // Subtle red for active state
            }
        } catch (err) {
            console.error("Camera error:", err);
            alert("Camera access denied or device not found. Please check permissions.");
        }
    }

    function setStep(step) {
        currentStep = step;
        hideError('registrationError');
        hideError('otpError');

        // Update Sidebar
        if (step === 3) {
            sideTitle.textContent = "Secure Verification";
            sideDesc.textContent = "Two-factor authentication adds an extra layer of security to your account";
            sideFeatures.innerHTML = `
                <div class="feature-pill"><i class="fa-solid fa-check"></i> End-to-end encrypted</div>
                <div class="feature-pill"><i class="fa-solid fa-check"></i> Time-limited codes</div>
                <div class="feature-pill"><i class="fa-solid fa-check"></i> Biometric backup</div>
            `;
        } else {
            sideTitle.textContent = "Join the System";
            sideDesc.textContent = "Register your face for secure, instant attendance tracking powered by AI";
            sideFeatures.innerHTML = `
                <div class="feature-pill"><i class="fa-solid fa-check"></i> AI Face Recognition</div>
                <div class="feature-pill"><i class="fa-solid fa-check"></i> Secure Registration</div>
                <div class="feature-pill"><i class="fa-solid fa-check"></i> Instant Verification</div>
            `;
        }

        // Toggle Panels
        step1.classList.toggle('hidden', step !== 1);
        step2.classList.toggle('hidden', step !== 2);
        step3.classList.toggle('hidden', step !== 3);

        // Update Stepper UI
        step1Circle.classList.toggle('active', step >= 1);
        step2Circle.classList.toggle('active', step >= 2);
        step3Circle.classList.toggle('active', step >= 3);

        if (stepLine1) stepLine1.style.background = step >= 2 ? 'var(--accent)' : 'var(--glass-border)';
        if (stepLine2) stepLine2.style.background = step >= 3 ? 'var(--accent)' : 'var(--glass-border)';

        if (step !== 2) stopCamera();
    }

    // --- AUTO-RESUME VERIFICATION ---
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('verify') === 'true') {
        const urlEmail = urlParams.get('email');
        if (urlEmail) {
            safeStorage.setItem('pendingEmail', urlEmail);
        }
        
        const email = safeStorage.getItem('pendingEmail');
        if (email) {
            if (displayEmail) displayEmail.textContent = email;
            // Delay slightly to ensure DOM is ready
            setTimeout(async () => {
                setStep(3);
                
                // Automatically request a new OTP so the user actually receives an email
                try {
                    await fetch(`${API_URL}/resend-otp`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email })
                    });
                } catch (e) {
                    console.error("Auto-OTP request failed", e);
                }
                
                startOtpTimer();
            }, 100);
        }
    }

    startCameraBtn?.addEventListener('click', startCamera);

    nextBtn?.addEventListener('click', () => {
        const fields = ['fullName', 'rollNumber', 'email', 'department', 'password'];
        for (let f of fields) {
            if (!document.getElementById(f).value.trim()) {
                showError('registrationError', 'Please fill all fields.');
                return;
            }
        }
        setStep(2);
    });

    backBtn?.addEventListener('click', () => setStep(1));

    captureBtn?.addEventListener('click', () => {
        if (!stream || !video.videoWidth) {
            alert("Please start the camera first.");
            return;
        }
        
        console.log("Capturing photo...");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        
        const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
        faceImageInput.value = dataUrl;
        
        // --- UI TRANSITION ---
        if (facePreview) {
            facePreview.src = dataUrl;
            facePreview.style.display = 'block';
            facePreview.style.opacity = '1';
        }
        if (video) {
            video.style.display = 'none';
        }
        
        // Turn off camera hardware
        stopCamera();
        
        captureBtn.innerHTML = '<i class="fa-solid fa-camera-retro"></i> Re-capture';
    });

    submitBtn?.addEventListener('click', async () => {
        if (!faceRecognitionAvailable) {
            showError('registrationError', 'Face recognition is unavailable. Fix the backend dependency installation first.');
            return;
        }
        if (!faceImageInput.value) {
            showError('registrationError', 'Please capture your face first.');
            return;
        }

        const payload = {
            full_name: document.getElementById('fullName').value.trim(),
            roll_number: document.getElementById('rollNumber').value.trim(),
            email: document.getElementById('email').value.trim(),
            department: document.getElementById('department').value.trim(),
            password: document.getElementById('password').value,
            face_image: faceImageInput.value
        };

        if (payload.password.length < 6) {
            showError('registrationError', 'Password must be at least 6 characters.');
            return;
        }

        if (!payload.email.toLowerCase().endsWith('@gmail.com')) {
            showError('registrationError', 'Only @gmail.com addresses are permitted.');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';

        try {
            const res = await fetch(`${API_URL}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (!res.ok) {
                let errorMsg = 'Registration failed';
                if (data.detail) {
                    if (data.detail.includes('already registered')) {
                        safeStorage.setItem('pendingEmail', payload.email);
                        showErrorWithAction('registrationError', data.detail, 'VERIFY_ACCOUNT', () => {
                            if (displayEmail) displayEmail.textContent = payload.email;
                            setStep(3);
                            startOtpTimer();
                        });
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = 'Create Account <i class="fa-solid fa-check"></i>';
                        return;
                    }
                    if (Array.isArray(data.detail)) {
                        errorMsg = data.detail.map(e => `${e.loc[e.loc.length - 1]}: ${e.msg}`).join(', ');
                    } else {
                        errorMsg = data.detail;
                    }
                }
                showError('registrationError', errorMsg);
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Create Account <i class="fa-solid fa-check"></i>';
                return;
            }

            safeStorage.setItem('pendingEmail', payload.email);
            if (displayEmail) displayEmail.textContent = payload.email;
            setStep(3);
            startOtpTimer();
        } catch (err) {
            showError('registrationError', 'Network error.');
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Create Account <i class="fa-solid fa-check"></i>';
        }
    });

    function startOtpTimer() {
        let timeLeft = 120;
        const timerTask = setInterval(() => {
            if (timeLeft <= 0) {
                clearInterval(timerTask);
                otpTimer.textContent = "Expired";
            } else {
                const mins = Math.floor(timeLeft / 60);
                const secs = timeLeft % 60;
                otpTimer.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
                timeLeft--;
            }
        }, 1000);
    }

    verifyOtpBtn?.addEventListener('click', async () => {
        const otp = document.getElementById('otpCode').value.trim();
        const email = safeStorage.getItem('pendingEmail');

        if (otp.length !== 6) {
            showError('otpError', 'Please enter a 6-digit OTP.');
            return;
        }

        verifyOtpBtn.disabled = true;
        verifyOtpBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifying...';

        try {
            const res = await fetch(`${API_URL}/verify-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, otp })
            });
            if (!res.ok) {
                const data = await res.json();
                showError('otpError', data.detail || 'Invalid OTP');
                verifyOtpBtn.disabled = false;
                verifyOtpBtn.innerHTML = 'Verify Code <i class="fa-solid fa-check-double"></i>';
                return;
            }

            alert("Registration Complete! Redirecting to login...");
            window.location.href = 'login.html';
        } catch (err) {
            showError('otpError', 'Network error.');
            verifyOtpBtn.disabled = false;
        }
    });

    resendOtpBtn?.addEventListener('click', async () => {
        const email = safeStorage.getItem('pendingEmail');
        try {
            const response = await fetch(`${API_URL}/resend-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const data = await response.json();
            if (!response.ok) {
                showError('otpError', data.detail || data.message || 'Failed to resend OTP.');
                return;
            }
            if (data.already_verified) {
                alert(data.message || 'Account is already verified. Redirecting to login...');
                window.location.href = 'login.html';
                return;
            }
            alert(data.message || 'OTP has been resent.');
            startOtpTimer();
        } catch (err) {
            alert('Failed to resend OTP.');
        }
    });
}

function initOtp() {
    const otpForm = document.getElementById('otpForm');
    if (!otpForm) return;

    const otpInput = document.querySelector('.otp-field');

    otpInput?.addEventListener('input', () => {
        otpInput.value = otpInput.value.replace(/\D/g, '').slice(0, 6);
    });

    otpForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        hideError('otpError');
        const otpSuccess = document.getElementById('otpSuccess');
        if (otpSuccess) otpSuccess.style.display = 'none';

        const email = safeStorage.getItem('pendingEmail');
        if (!email) {
            showError('otpError', 'No pending registration found. Please register first.');
            return;
        }

        const otp = otpInput?.value?.trim() || '';
        if (otp.length !== 6) {
            showError('otpError', 'Please enter the 6-digit code.');
            return;
        }

        try {
            const response = await fetch(`${API_URL}/verify-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, otp })
            });
            const data = await response.json();

            if (!response.ok) {
                showError('otpError', data.detail || 'Invalid OTP');
                return;
            }

            if (otpSuccess) {
                otpSuccess.textContent = 'Verification successful. Redirecting to login...';
                otpSuccess.style.display = 'block';
            }
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 1000);
        } catch {
            showError('otpError', 'Network error. Please try again.');
        }
    });

    const resendBtn = document.getElementById('resendOtp');
    resendBtn?.addEventListener('click', async () => {
        const email = safeStorage.getItem('pendingEmail');
        if (!email) {
            showError('otpError', 'No pending registration found.');
            return;
        }

        try {
            const response = await fetch(`${API_URL}/resend-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const data = await response.json();
            if (!response.ok) {
                showError('otpError', data.detail || 'Failed to resend OTP');
                return;
            }
            if (data.already_verified) {
                alert(data.message || 'Account is already verified. Redirecting to login...');
                window.location.href = 'login.html';
                return;
            }
            alert(data.message || 'OTP resent successfully. Please check your email.');
        } catch {
            showError('otpError', 'Network error while resending OTP.');
        }
    });
}
