/**
 * oftek - Genel Yardımcılar, UI Araçları ve Formatlayıcılar (api.js)
 */

// Global Uygulama Durumu
let activeTab = 'dashboard';
let currentPeriodYear = '2026';
let currentPeriodMonth = ''; // Varsayılan tüm aylar açık

// Sayı / Para Formatlayıcı (12.345,67 ₺)
function fmt(n) {
    if (n === null || n === undefined || isNaN(n)) return '0,00 ₺';
    return Number(n).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' ₺';
}

// Bildirim (Toast) Mesajı Gösterici
function showToast(msg, type = 'info') {
    const el = document.getElementById('toast');
    if (!el) return;
    const msgEl = document.getElementById('toast-msg');
    if (msgEl) msgEl.innerText = msg;
    
    el.className = 'fixed bottom-5 right-5 z-50 text-white px-4 py-2.5 rounded-xl shadow-xl flex items-center gap-2 text-xs font-semibold transition-all transform duration-200';
    if (type === 'success') {
        el.classList.add('bg-emerald-600');
    } else if (type === 'error') {
        el.classList.add('bg-rose-600');
    } else {
        el.classList.add('bg-slate-800');
    }
    el.classList.remove('hidden', 'opacity-0', 'translate-y-2');
    
    setTimeout(() => {
        el.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => el.classList.add('hidden'), 200);
    }, 2800);
}

// Modal Aç / Kapat Yardımcıları
function showModal(id) {
    const m = document.getElementById(id);
    if (m) m.classList.remove('hidden');
}

function hideModal(id) {
    const m = document.getElementById(id);
    if (m) m.classList.add('hidden');
}

// Hücreler Arası Akıllı Odaklanma (Tab İlerlemesi)
function focusNextElement(currentEl) {
    const focusable = Array.from(document.querySelectorAll(
        'input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), button:not([disabled])'
    )).filter(el => {
        return el.offsetParent !== null && !el.closest('.hidden');
    });
    
    const index = focusable.indexOf(currentEl);
    if (index > -1 && index + 1 < focusable.length) {
        focusable[index + 1].focus();
        if (focusable[index + 1].select) {
            focusable[index + 1].select();
        }
    }
}
