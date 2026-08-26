const API_BASE_URL = 'https://livedoc-technofest-2026.onrender.com';
const TOKEN_STORAGE_KEY = 'livedoc_jwt_token';
const EMAIL_STORAGE_KEY = 'livedoc_user_email';

const form = document.getElementById("loginForm");
const togglePassword = document.getElementById("togglePassword");
const passwordInput = document.getElementById("password");
const emailInput = document.getElementById("email");
const loginBtn = document.querySelector(".login-btn");
const registerBtn = document.querySelector(".register-btn");

// Toggle Password Visibility
togglePassword.addEventListener("click", () => {
    if(passwordInput.type === "password"){
        passwordInput.type = "text";
        togglePassword.innerHTML = `<span class="material-symbols-outlined">visibility_off</span>`;
    }else{
        passwordInput.type = "password";
        togglePassword.innerHTML = `<span class="material-symbols-outlined">visibility</span>`;
    }
});

// Helper to show errors professionally (could be upgraded to a toast notification)
function showMessage(msg, isError = false) {
    // Check if error box exists, if not create it
    let msgBox = document.getElementById('form-message');
    if (!msgBox) {
        msgBox = document.createElement('div');
        msgBox.id = 'form-message';
        msgBox.style.padding = '10px';
        msgBox.style.borderRadius = '8px';
        msgBox.style.marginTop = '15px';
        msgBox.style.fontSize = '14px';
        msgBox.style.textAlign = 'center';
        form.insertBefore(msgBox, loginBtn);
    }
    
    msgBox.style.backgroundColor = isError ? '#fee2e2' : '#dcfce7';
    msgBox.style.color = isError ? '#991b1b' : '#166534';
    msgBox.textContent = msg;
}

// Disable/Enable buttons during loading
function setLoading(isLoading) {
    loginBtn.disabled = isLoading;
    registerBtn.disabled = isLoading;
    loginBtn.style.opacity = isLoading ? '0.7' : '1';
    registerBtn.style.opacity = isLoading ? '0.7' : '1';
    
    if (isLoading) {
        loginBtn.textContent = "Processing...";
    } else {
        loginBtn.textContent = "Login";
    }
}

// Central API Request Handler
async function performAuthAction(endpoint, email, password) {
    if (!email || !password) {
        showMessage("Please enter both email and password.", true);
        return;
    }

    setLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Authentication failed');
        }

        // Success - Save Token
        localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token);
        localStorage.setItem(EMAIL_STORAGE_KEY, email);
        
        showMessage(endpoint === '/login' ? "Login successful!" : "Registration successful!");
        
        // Redirect to the main dashboard page
        setTimeout(() => {
            window.location.href = "dashboard.html";
        }, 800);

    } catch (err) {
        showMessage(err.message, true);
    } finally {
        setLoading(false);
    }
}

// Handle Login Submit
form.addEventListener("submit", function(e){
    e.preventDefault();
    performAuthAction('/login', emailInput.value, passwordInput.value);
});

// Handle Register Click
registerBtn.addEventListener('click', () => {
    window.location.href = "register.html";
});