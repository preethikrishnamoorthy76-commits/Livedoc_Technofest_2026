const API_BASE_URL = 'http://127.0.0.1:8000';
const TOKEN_STORAGE_KEY = 'livedoc_jwt_token';
const EMAIL_STORAGE_KEY = 'livedoc_user_email';

const form = document.getElementById('registerForm');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const confirmPasswordInput = document.getElementById('confirmPassword');
const submitBtn = document.querySelector('.login-btn');
const backToLoginBtn = document.getElementById('backToLogin');
const togglePasswordBtn = document.getElementById('togglePassword');
const toggleConfirmPasswordBtn = document.getElementById('toggleConfirmPassword');

function showMessage(msg, isError = false) {
    let msgBox = document.getElementById('form-message');
    if (!msgBox) {
        msgBox = document.createElement('div');
        msgBox.id = 'form-message';
        msgBox.style.padding = '10px';
        msgBox.style.borderRadius = '8px';
        msgBox.style.marginTop = '15px';
        msgBox.style.fontSize = '14px';
        msgBox.style.textAlign = 'center';
        form.insertBefore(msgBox, submitBtn);
    }

    msgBox.style.backgroundColor = isError ? '#fee2e2' : '#dcfce7';
    msgBox.style.color = isError ? '#991b1b' : '#166534';
    msgBox.textContent = msg;
}

function setLoading(isLoading) {
    submitBtn.disabled = isLoading;
    backToLoginBtn.disabled = isLoading;
    submitBtn.style.opacity = isLoading ? '0.7' : '1';
    backToLoginBtn.style.opacity = isLoading ? '0.7' : '1';
    submitBtn.textContent = isLoading ? 'Creating Account...' : 'Create Account';
}

function togglePasswordVisibility(inputEl, btnEl) {
    if (inputEl.type === 'password') {
        inputEl.type = 'text';
        btnEl.innerHTML = '<span class="material-symbols-outlined">visibility_off</span>';
    } else {
        inputEl.type = 'password';
        btnEl.innerHTML = '<span class="material-symbols-outlined">visibility</span>';
    }
}

togglePasswordBtn.addEventListener('click', () => {
    togglePasswordVisibility(passwordInput, togglePasswordBtn);
});

toggleConfirmPasswordBtn.addEventListener('click', () => {
    togglePasswordVisibility(confirmPasswordInput, toggleConfirmPasswordBtn);
});

backToLoginBtn.addEventListener('click', () => {
    window.location.href = 'index.html';
});

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = emailInput.value.trim();
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;

    if (!email || !password || !confirmPassword) {
        showMessage('Please fill all fields.', true);
        return;
    }

    if (password !== confirmPassword) {
        showMessage('Password and confirm password do not match.', true);
        return;
    }

    if (password.length < 8) {
        showMessage('Password must be at least 8 characters.', true);
        return;
    }

    setLoading(true);
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Registration failed');
        }

        localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token);
        localStorage.setItem(EMAIL_STORAGE_KEY, email);

        showMessage('Registration successful! Redirecting...');
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 800);
    } catch (err) {
        showMessage(err.message, true);
    } finally {
        setLoading(false);
    }
});
