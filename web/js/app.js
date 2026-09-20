/**
 * oftek - Ana Uygulama Yönlendiricisi, Tab Navigasyonu & Başlatıcı
 */

let currentPeriodYear = '2026';
let currentPeriodMonth = ''; // Global ay kısıtı kaldırıldı, işlemler tarihe ve seçilen döneme göre çalışır

function switchTab(tabId) {
    activeTab = tabId;
    document.querySelectorAll('main > section').forEach(s => s.classList.add('hidden'));
    const target = document.getElementById('tab-' + tabId);
    if (target) target.classList.remove('hidden');

    document.querySelectorAll('.nav-link').forEach(btn => {
        if (btn.dataset.tab === tabId) {
            btn.classList.add('bg-brand-50', 'text-brand-700', 'font-semibold');
            btn.classList.remove('text-slate-700');
        } else {
            btn.classList.remove('bg-brand-50', 'text-brand-700', 'font-semibold');
            btn.classList.add('text-slate-700');
        }
    });

    if (tabId === 'dashboard' && typeof loadDashboard === 'function') loadDashboard();
    if (tabId === 'gunluk_kasa' && typeof loadDailyTransactions === 'function') loadDailyTransactions();
    if (tabId === 'cari_borclar' && typeof loadDebts === 'function') loadDebts();
    if (tabId === 'personel') { 
        if (typeof loadEmployeeTypes === 'function') loadEmployeeTypes(); 
        if (typeof loadEmployees === 'function') loadEmployees(); 
    }
    if (tabId === 'alacaklar' && typeof loadReceivables === 'function') loadReceivables();
    if (tabId === 'yevmiye' && typeof loadVouchers === 'function') loadVouchers();
    if (tabId === 'mizan' && typeof loadMizan === 'function') loadMizan();
    if (tabId === 'hesap_plani' && typeof loadAccounts === 'function') loadAccounts();
    if (tabId === 'voucher_entry' && typeof initVoucherEntryPage === 'function') initVoucherEntryPage();
    if (tabId === 'employee_accrual' && typeof initEmployeeAccrualPage === 'function') initEmployeeAccrualPage();
    if (tabId === 'raporlar' && typeof loadCurrentReport === 'function') loadCurrentReport();
    if (tabId === 'ayarlar' && typeof loadSettingsPage === 'function') loadSettingsPage();
}

function toggleSidebar() {
    const sidebar = document.getElementById('main-sidebar');
    if (!sidebar) return;
    if (sidebar.classList.contains('hidden')) {
        sidebar.classList.remove('hidden');
        sidebar.classList.add('lg:flex');
    } else {
        sidebar.classList.add('hidden');
        sidebar.classList.remove('lg:flex');
    }
}

function setPeriodYear(year) {
    currentPeriodYear = year;
    document.querySelectorAll('.period-year-btn').forEach(b => {
        if (b.id === 'btn-year-' + year) {
            b.className = "period-year-btn px-2.5 py-1 rounded-lg font-bold text-xs bg-white text-slate-800 shadow-xs";
        } else {
            b.className = "period-year-btn px-2.5 py-1 rounded-lg font-bold text-xs text-slate-600 hover:text-slate-900";
        }
    });
    onPeriodChange();
}

function onPeriodChange() {
    if (activeTab === 'dashboard' && typeof loadDashboard === 'function') loadDashboard();
    if (activeTab === 'cari_borclar' && typeof loadDebts === 'function') loadDebts();
    if (activeTab === 'personel') { 
        if (typeof loadEmployees === 'function') loadEmployees(); 
        if (typeof loadAccrualReport === 'function') loadAccrualReport(); 
    }
    if (activeTab === 'alacaklar' && typeof loadReceivables === 'function') loadReceivables();
    if (activeTab === 'raporlar' && typeof loadCurrentReport === 'function') loadCurrentReport();
}

// ================= BUTON SEGMENTLERİ SETTER FONKSİYONLARI =================
function setCollectSource(val, btn) {
    const inp = document.getElementById('collect-source');
    if (inp) inp.value = val;
    if (btn && btn.parentElement) {
        btn.parentElement.querySelectorAll('button').forEach(b => {
            b.className = "collect-src-btn flex-1 py-1 rounded-lg font-bold text-slate-600 hover:text-slate-900 text-center";
        });
        btn.className = "collect-src-btn flex-1 py-1 rounded-lg font-bold bg-white text-slate-800 shadow-xs text-center";
    }
}

function setPayDebtSource(val, btn) {
    const inp = document.getElementById('pay-debt-source');
    if (inp) inp.value = val;
    if (btn && btn.parentElement) {
        btn.parentElement.querySelectorAll('button').forEach(b => {
            b.className = "pay-debt-src-btn flex-1 py-1 rounded-lg font-bold text-slate-600 hover:text-slate-900 text-center";
        });
        btn.className = "pay-debt-src-btn flex-1 py-1 rounded-lg font-bold bg-white text-slate-800 shadow-xs text-center";
    }
}

function setPayEmpSource(val, btn) {
    const inp = document.getElementById('pay-emp-source');
    if (inp) inp.value = val;
    if (btn && btn.parentElement) {
        btn.parentElement.querySelectorAll('button').forEach(b => {
            b.className = "pay-emp-src-btn flex-1 py-1 rounded-lg font-bold text-slate-600 hover:text-slate-900 text-center";
        });
        btn.className = "pay-emp-src-btn flex-1 py-1 rounded-lg font-bold bg-white text-slate-800 shadow-xs text-center";
    }
}

function setRecKategori(val, btn) {
    const inp = document.getElementById('rec-kategori');
    if (inp) inp.value = val;
    if (btn && btn.parentElement) {
        btn.parentElement.querySelectorAll('button').forEach(b => {
            b.className = "rec-cat-btn px-2 py-1 rounded-lg text-xs font-medium bg-slate-100 text-slate-700 hover:bg-slate-200";
        });
        btn.className = "rec-cat-btn px-2 py-1 rounded-lg text-xs font-bold bg-blue-50 text-blue-700 shadow-xs";
    }
}

function setNewCariTip(val, btn) {
    const inp = document.getElementById('new-cari-tip');
    if (inp) inp.value = val;
    if (btn && btn.parentElement) {
        btn.parentElement.querySelectorAll('button').forEach(b => {
            b.className = "new-cari-tip-btn flex-1 py-1 rounded-lg font-bold text-slate-600 hover:text-slate-900 text-center";
        });
        btn.className = "new-cari-tip-btn flex-1 py-1 rounded-lg font-bold bg-white text-slate-800 shadow-xs text-center";
    }
}

function setQuickExpCat(cat, acc, btn) {
    const inpCat = document.getElementById('quick-expense-cat');
    const inpAcc = document.getElementById('quick-expense-target');
    if (inpCat) inpCat.value = cat;
    if (inpAcc) inpAcc.value = acc;
    if (btn && btn.parentElement) {
        btn.parentElement.querySelectorAll('button').forEach(b => {
            b.className = "q-exp-cat-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 text-slate-700 hover:bg-slate-200";
        });
        btn.className = "q-exp-cat-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-rose-50 text-rose-700 shadow-xs";
    }
}

function setQuickExpSource(val, btn) {
    const inp = document.getElementById('quick-expense-source');
    if (inp) inp.value = val;
    if (btn && btn.parentElement) {
        btn.parentElement.querySelectorAll('button').forEach(b => {
            b.className = "q-exp-src-btn flex-1 py-1 rounded-lg font-bold text-slate-600 hover:text-slate-900 text-center";
        });
        btn.className = "q-exp-src-btn flex-1 py-1 rounded-lg font-bold bg-white text-slate-800 shadow-xs text-center";
    }
}

function setQuickIncCat(cat, acc, btn) {
    const inpCat = document.getElementById('quick-income-cat');
    const inpAcc = document.getElementById('quick-income-target');
    if (inpCat) inpCat.value = cat;
    if (inpAcc) inpAcc.value = acc;
    if (btn && btn.parentElement) {
        btn.parentElement.querySelectorAll('button').forEach(b => {
            b.className = "q-inc-cat-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 text-slate-700 hover:bg-slate-200";
        });
        btn.className = "q-inc-cat-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-50 text-emerald-700 shadow-xs";
    }
}

function setQuickIncSource(val, btn) {
    const inp = document.getElementById('quick-income-source');
    if (inp) inp.value = val;
    if (btn && btn.parentElement) {
        btn.parentElement.querySelectorAll('button').forEach(b => {
            b.className = "q-inc-src-btn flex-1 py-1 rounded-lg font-bold text-slate-600 hover:text-slate-900 text-center";
        });
        btn.className = "q-inc-src-btn flex-1 py-1 rounded-lg font-bold bg-white text-slate-800 shadow-xs text-center";
    }
}

// ================= DOM HAZIR VE BAŞLANGIÇ =================
window.addEventListener('DOMContentLoaded', async () => {
    // 1. Güvenlik Zırhı: Kimlik doğrulama ve ilk kurulum kontrolü
    if (window.authModule && typeof window.authModule.checkStatus === 'function') {
        const isAuthed = await window.authModule.checkStatus();
        if (!isAuthed) {
            // Giriş veya ilk kurulum tamamlanana kadar diğer API çağrılarını beklet
            return;
        }
    }

    if (typeof checkSession === 'function') await checkSession();
    if (typeof loadInstitutionProfile === 'function') await loadInstitutionProfile();
    if (typeof loadEmployeeTypes === 'function') await loadEmployeeTypes();
    if (typeof loadDashboard === 'function') await loadDashboard();

    // Cari Autocomplete bağlayıcıları
    if (typeof attachCariAutocomplete === 'function') {
        attachCariAutocomplete(document.getElementById('collect-cari-search'), document.getElementById('collect-cari-id'), 'MUSTERI', typeof onCollectCariChange === 'function' ? onCollectCariChange : null);
        attachCariAutocomplete(document.getElementById('debt-cari-search'), document.getElementById('debt-cari-id'), 'FIRMA');
        attachCariAutocomplete(document.getElementById('rec-cari-search'), document.getElementById('rec-cari-id'), 'MUSTERI');
    }
});
