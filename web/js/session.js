/**
 * oftek - Gün Oturumu ve Hızlı Kasa Fişleri (session.js)
 */

let activeSession = null;

// Aktif Gün Oturumu Kontrolü
async function checkSession() {
    try {
        const res = await fetch('/api/session/active');
        const session = await res.json();
        activeSession = session;

        const badge = document.getElementById('session-badge');
        const btnOpen = document.getElementById('btn-open-session');
        const btnClose = document.getElementById('btn-close-session');

        if (session && session.id) {
            if (badge) {
                badge.className = "inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200";
                badge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse"></span>${session.tarih} (AÇIK)`;
            }
            if (btnOpen) btnOpen.classList.add('hidden');
            if (btnClose) btnClose.classList.remove('hidden');
        } else {
            if (badge) {
                badge.className = "inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200";
                badge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-amber-500 mr-1.5"></span>GÜN KAPALI`;
            }
            if (btnOpen) btnOpen.classList.remove('hidden');
            if (btnClose) btnClose.classList.add('hidden');
        }
    } catch (e) {
        console.error("Session check error:", e);
    }
}

// Gün Açma Modalı
function showOpenSessionModal() {
    const d = document.getElementById('open-session-date');
    if (d) d.value = new Date().toISOString().split('T')[0];
    showModal('modal-open-session');
}

// Gün Açma Formu Gönderimi
async function submitOpenSession(e) {
    if (e) e.preventDefault();
    const tarih = document.getElementById('open-session-date').value;
    const notlar = document.getElementById('open-session-notes').value;

    const res = await fetch('/api/session/open', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tarih, notlar })
    });
    const data = await res.json();
    if (res.ok) {
        showToast(`Çalışma günü (#${data.id} - ${data.tarih}) başarıyla açıldı.`, 'success');
        hideModal('modal-open-session');
        await checkSession();
        if (typeof loadDashboard === 'function') loadDashboard();
    } else {
        showToast(data.error || 'Gün açılamadı.', 'error');
    }
}

// Gün Kapatma Özeti Modalı
async function showCloseSessionModal() {
    if (!activeSession) {
        showToast('Açık bir çalışma günü bulunmuyor.', 'error');
        return;
    }

    const res = await fetch(`/api/daily-transactions?gun_id=${activeSession.id}`);
    const txs = await res.json();

    const sumBox = document.getElementById('close-session-summary');
    if (sumBox) {
        sumBox.innerHTML = `
            <div class="flex justify-between"><span>Oturum Tarihi:</span><b class="text-slate-800">${activeSession.tarih}</b></div>
            <div class="flex justify-between"><span>Dönem:</span><b class="text-slate-800">${activeSession.donem_yil} / ${activeSession.donem_ay}. Ay</b></div>
            <div class="flex justify-between"><span>Gün İçi Hareket Sayısı:</span><b class="text-slate-800">${txs.length} adet</b></div>
        `;
    }
    showModal('modal-close-session');
}

// Gün Kapatma Onayı
async function submitCloseSession() {
    if (!activeSession) return;
    const res = await fetch('/api/session/close', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gun_id: activeSession.id })
    });
    const data = await res.json();
    if (res.ok) {
        showToast(`Gün kapatıldı! #${data.fis_id || '-'} no'lu yevmiye fişi oluşturuldu (${fmt(data.toplam_tutar)}).`, 'success');
        hideModal('modal-close-session');
        await checkSession();
        if (typeof loadDashboard === 'function') loadDashboard();
    } else {
        showToast(data.error || 'Gün kapatılamadı.', 'error');
    }
}

// Hızlı Gider Modalı & Gönderimi
function showQuickExpenseModal() {
    if (!activeSession) {
        showToast('Harcama/gider fişi kaydetmek için önce gün oturumu açmalısınız!', 'error');
        return;
    }
    document.getElementById('quick-expense-amount').value = '';
    document.getElementById('quick-expense-desc').value = '';
    showModal('modal-quick-expense');
}

async function submitQuickExpense(e) {
    if (e) e.preventDefault();
    const tutar = parseFloat(document.getElementById('quick-expense-amount').value || 0);
    const kaynak_hesap = document.getElementById('quick-expense-source').value;
    const karsi_hesap = document.getElementById('quick-expense-target').value;
    const kategori = document.getElementById('quick-expense-cat').value;
    const aciklama = document.getElementById('quick-expense-desc').value.trim();

    if (tutar <= 0) {
        showToast('Geçerli bir gider tutarı giriniz.', 'error');
        return;
    }

    const res = await fetch('/api/quick-expense', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            gun_id: activeSession.id,
            tutar,
            kaynak_hesap,
            karsi_hesap,
            kategori,
            aciklama
        })
    });
    const data = await res.json();
    if (res.ok) {
        showToast('Gider işlemi kaydedildi. Gün kapatıldığında yevmiye fişine eklenecektir.', 'success');
        hideModal('modal-quick-expense');
        if (typeof loadDailyTransactions === 'function') loadDailyTransactions();
        if (typeof loadDashboard === 'function') loadDashboard();
    } else {
        showToast(data.error || 'Gider kaydedilemedi.', 'error');
    }
}

// Hızlı Gelir Modalı & Gönderimi
function showQuickIncomeModal() {
    if (!activeSession) {
        showToast('Gelir fişi kaydetmek için önce gün oturumu açmalısınız!', 'error');
        return;
    }
    document.getElementById('quick-income-amount').value = '';
    document.getElementById('quick-income-desc').value = '';
    showModal('modal-quick-income');
}

async function submitQuickIncome(e) {
    if (e) e.preventDefault();
    const tutar = parseFloat(document.getElementById('quick-income-amount').value || 0);
    const kaynak_hesap = document.getElementById('quick-income-source').value;
    const karsi_hesap = document.getElementById('quick-income-target').value;
    const kategori = document.getElementById('quick-income-cat').value;
    const aciklama = document.getElementById('quick-income-desc').value.trim();

    if (tutar <= 0) {
        showToast('Geçerli bir gelir tutarı giriniz.', 'error');
        return;
    }

    const res = await fetch('/api/quick-income', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            gun_id: activeSession.id,
            tutar,
            kaynak_hesap,
            karsi_hesap,
            kategori,
            aciklama
        })
    });
    const data = await res.json();
    if (res.ok) {
        showToast('Gelir işlemi kaydedildi. Gün kapatıldığında yevmiye fişine eklenecektir.', 'success');
        hideModal('modal-quick-income');
        if (typeof loadDailyTransactions === 'function') loadDailyTransactions();
        if (typeof loadDashboard === 'function') loadDashboard();
    } else {
        showToast(data.error || 'Gelir kaydedilemedi.', 'error');
    }
}
