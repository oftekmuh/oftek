/**
 * oftek - Kimlik Doğrulama & Oturum Yönetimi (web/js/auth.js)
 * İlk kurulum sihirbazı, güvenli giriş (login), oturum denetimi ve şifre değiştirme.
 */

const authModule = {
    tokenKey: 'oftek_session_token',

    getToken() {
        return localStorage.getItem(this.tokenKey) || sessionStorage.getItem(this.tokenKey) || '';
    },

    setToken(token, remember = true) {
        if (!token) return;
        if (remember) {
            localStorage.setItem(this.tokenKey, token);
        } else {
            sessionStorage.setItem(this.tokenKey, token);
        }
        // Çerez olarak da kaydet (same-site lax)
        document.cookie = `oftek_token=${token}; path=/; max-age=2592000; SameSite=Lax`;
    },

    clearToken() {
        localStorage.removeItem(this.tokenKey);
        sessionStorage.removeItem(this.tokenKey);
        document.cookie = 'oftek_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    },

    async checkStatus() {
        try {
            const token = this.getToken();
            const res = await fetch('/api/auth/status', {
                headers: {
                    'X-Session-Token': token
                }
            });
            const data = await res.json();
            
            if (data.setup_required) {
                // İlk kurulum gerekiyor
                this.showSetupModal();
                return false;
            }

            if (!data.authenticated) {
                // Giriş yapılması gerekiyor
                this.clearToken();
                this.showLoginModal();
                return false;
            }

            // Başarılı oturum
            this.updateHeaderUser(data.user);
            this.hideAllAuthModals();
            return true;
        } catch (err) {
            console.error('Auth status check error:', err);
            this.showLoginModal();
            return false;
        }
    },

    showSetupModal() {
        document.getElementById('modal-auth-login')?.classList.add('hidden');
        document.getElementById('modal-auth-setup')?.classList.remove('hidden');
        document.getElementById('setup-username')?.focus();
    },

    showLoginModal() {
        document.getElementById('modal-auth-setup')?.classList.add('hidden');
        document.getElementById('modal-auth-login')?.classList.remove('hidden');
        document.getElementById('login-username')?.focus();
        this.updateHeaderUser(null);
    },

    hideAllAuthModals() {
        document.getElementById('modal-auth-setup')?.classList.add('hidden');
        document.getElementById('modal-auth-login')?.classList.remove('hidden');
        document.getElementById('modal-auth-login')?.classList.add('hidden');
    },

    updateHeaderUser(user) {
        const userBadge = document.getElementById('header-user-badge');
        const usernameEl = document.getElementById('header-username');
        const logoutBtn = document.getElementById('btn-logout');

        if (user && user.kullanici_adi) {
            if (usernameEl) usernameEl.textContent = user.ad_soyad || user.kullanici_adi;
            if (userBadge) userBadge.classList.remove('hidden');
            if (logoutBtn) logoutBtn.classList.remove('hidden');
        } else {
            if (userBadge) userBadge.classList.add('hidden');
            if (logoutBtn) logoutBtn.classList.add('hidden');
        }
    },

    async submitSetup(e) {
        if (e) e.preventDefault();
        const username = document.getElementById('setup-username')?.value.trim();
        const fullName = document.getElementById('setup-fullname')?.value.trim() || 'Yönetici';
        const password = document.getElementById('setup-password')?.value;
        const passwordConfirm = document.getElementById('setup-password-confirm')?.value;
        const alertEl = document.getElementById('setup-alert');

        if (!username || username.length < 3) {
            this.showAlert(alertEl, 'Kullanıcı adı en az 3 karakter olmalıdır.');
            return;
        }
        if (!password || password.length < 4) {
            this.showAlert(alertEl, 'Şifre en az 4 karakter olmalıdır.');
            return;
        }
        if (password !== passwordConfirm) {
            this.showAlert(alertEl, 'Girdiğiniz şifreler birbiriyle uyuşmuyor.');
            return;
        }

        try {
            const res = await fetch('/api/auth/setup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    kullanici_adi: username,
                    ad_soyad: fullName,
                    sifre: password
                })
            });
            const data = await res.json();
            if (!res.ok || !data.success) {
                this.showAlert(alertEl, data.message || 'Kurulum başarısız.');
                return;
            }

            this.setToken(data.token, true);
            this.hideAllAuthModals();
            this.updateHeaderUser(data.user);
            showToast('Yönetici hesabı başarıyla oluşturuldu! Hoş geldiniz.');
            if (window.app && typeof window.app.init === 'function') {
                window.app.init();
            } else {
                window.location.reload();
            }
        } catch (err) {
            this.showAlert(alertEl, 'Sunucu bağlantı hatası.');
        }
    },

    async submitLogin(e) {
        if (e) e.preventDefault();
        const username = document.getElementById('login-username')?.value.trim();
        const password = document.getElementById('login-password')?.value;
        const remember = document.getElementById('login-remember')?.checked ?? true;
        const alertEl = document.getElementById('login-alert');

        if (!username || !password) {
            this.showAlert(alertEl, 'Lütfen kullanıcı adı ve şifrenizi giriniz.');
            return;
        }

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    kullanici_adi: username,
                    sifre: password
                })
            });
            const data = await res.json();
            if (!res.ok || !data.success) {
                this.showAlert(alertEl, data.message || 'Kullanıcı adı veya şifre hatalı.');
                return;
            }

            this.setToken(data.token, remember);
            this.hideAllAuthModals();
            this.updateHeaderUser(data.user);
            showToast(`Hoş geldiniz, ${data.user.ad_soyad || data.user.kullanici_adi}!`);
            
            // Verileri yükle
            if (typeof loadDashboard === 'function') loadDashboard();
            if (typeof checkDaySession === 'function') checkDaySession();
        } catch (err) {
            this.showAlert(alertEl, 'Giriş yapılırken sunucu hatası oluştu.');
        }
    },

    async logout() {
        const token = this.getToken();
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'X-Session-Token': token
                }
            });
        } catch (e) {
            // sessiz geç
        }
        this.clearToken();
        showToast('Oturum kapatıldı.');
        this.showLoginModal();
    },

    async changePassword(e) {
        if (e) e.preventDefault();
        const oldPwd = document.getElementById('chg-old-password')?.value;
        const newPwd = document.getElementById('chg-new-password')?.value;
        const newPwdConfirm = document.getElementById('chg-new-password-confirm')?.value;

        if (!oldPwd) {
            showToast('Lütfen mevcut şifrenizi giriniz.', 'error');
            return;
        }
        if (!newPwd || newPwd.length < 4) {
            showToast('Yeni şifre en az 4 karakter olmalıdır.', 'error');
            return;
        }
        if (newPwd !== newPwdConfirm) {
            showToast('Yeni şifreler birbiriyle uyuşmuyor.', 'error');
            return;
        }

        try {
            const token = this.getToken();
            const res = await fetch('/api/auth/change-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Session-Token': token
                },
                body: JSON.stringify({
                    eski_sifre: oldPwd,
                    yeni_sifre: newPwd
                })
            });
            const data = await res.json();
            if (!res.ok || !data.success) {
                showToast(data.message || 'Şifre değiştirilemedi.', 'error');
                return;
            }

            showToast(data.message || 'Şifreniz değiştirildi. Lütfen tekrar giriş yapınız.');
            document.getElementById('form-change-password')?.reset();
            this.clearToken();
            this.showLoginModal();
        } catch (err) {
            showToast('Sunucu bağlantı hatası.', 'error');
        }
    },

    showAlert(el, msg) {
        if (!el) return;
        el.textContent = msg;
        el.classList.remove('hidden');
    },

    hideAlert(el) {
        if (!el) return;
        el.classList.add('hidden');
    }
};

window.authModule = authModule;
