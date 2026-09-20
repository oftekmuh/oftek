/**
 * oftek - Sistem & Ayarlar Yönetimi, Kurum Profili ve Kırmızı Alan
 */

// ================= KIRMIZI ALAN (DANGER ZONE) =================
function openDangerResetModal() {
    const input = document.getElementById('input-danger-confirm');
    const btn = document.getElementById('btn-danger-confirm-submit');
    if (input) input.value = '';
    if (btn) btn.disabled = true;
    showModal('modal-danger-reset');
    setTimeout(() => { if (input) input.focus(); }, 150);
}

function checkDangerResetInput() {
    const input = document.getElementById('input-danger-confirm');
    const btn = document.getElementById('btn-danger-confirm-submit');
    if (!input || !btn) return;
    const val = input.value.trim().toUpperCase();
    btn.disabled = (val !== 'SIFIRLA');
}

async function executeDatabaseReset() {
    const input = document.getElementById('input-danger-confirm');
    const val = input ? input.value.trim().toUpperCase() : '';
    if (val !== 'SIFIRLA') {
        showToast("Lütfen kutuya 'SIFIRLA' yazınız.", 'error');
        return;
    }

    try {
        const res = await fetch('/api/system/reset-database', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ onay_kodu: 'SIFIRLA' })
        });
        const data = await res.json();
        if (res.ok) {
            hideModal('modal-danger-reset');
            showToast('Tüm operasyonel veriler ve geçmiş kayıtlar sıfırlandı!', 'success');
            if (typeof checkSession === 'function') await checkSession();
            if (typeof loadDashboard === 'function') await loadDashboard();
            if (typeof loadEmployees === 'function') await loadEmployees();
            if (typeof loadDebts === 'function') await loadDebts();
            if (typeof loadReceivables === 'function') await loadReceivables();
        } else {
            showToast(data.error || 'Sıfırlama işlemi başarısız oldu.', 'error');
        }
    } catch (e) {
        console.error('Sıfırlama hatası:', e);
        showToast('Sunucu ile bağlantı kurulamadı.', 'error');
    }
}

// ================= BORÇ YÖN AYARI (AYARLAR SEKME İÇİ) =================
let settingsDebtYon = 'BORC';

function setSettingsDebtYon(yon) {
    settingsDebtYon = yon;
    const btnBorc = document.getElementById('settings-debt-yon-borc');
    const btnAlacak = document.getElementById('settings-debt-yon-alacak');
    if (btnBorc && btnAlacak) {
        if (yon === 'BORC') {
            btnBorc.className = "px-3 py-1 rounded-lg font-semibold bg-white text-slate-800 shadow-xs transition-all";
            btnAlacak.className = "px-3 py-1 rounded-lg font-semibold text-slate-600 hover:text-slate-900 transition-all";
        } else {
            btnAlacak.className = "px-3 py-1 rounded-lg font-semibold bg-white text-slate-800 shadow-xs transition-all";
            btnBorc.className = "px-3 py-1 rounded-lg font-semibold text-slate-600 hover:text-slate-900 transition-all";
        }
    }
}

// ================= KURUM / İŞLETME PROFİLİ YÖNETİMİ =================
let globalInstitutionProfile = {
    kurum_adi: 'oftek',
    kurum_turu: 'GENEL',
    para_birimi: '₺',
    vergi_no: '',
    adres: '',
    telefon: '',
    eposta: '',
    web_adresi: ''
};
let activeProfileType = 'GENEL';

function setProfileType(type) {
    activeProfileType = type;
    document.querySelectorAll('.profile-type-btn').forEach(btn => {
        if (btn.dataset.type === type) {
            btn.className = "profile-type-btn px-3 py-1 rounded-lg font-semibold bg-white text-slate-800 shadow-xs";
        } else {
            btn.className = "profile-type-btn px-3 py-1 rounded-lg font-semibold text-slate-600 hover:text-slate-900";
        }
    });
    const badge = document.getElementById('settings-profile-type-badge');
    if (badge) badge.innerText = type;
}

async function loadInstitutionProfile() {
    try {
        const res = await fetch('/api/settings/profile');
        if (!res.ok) return;
        const data = await res.json();
        if (data && data.kurum_adi) {
            globalInstitutionProfile = data;
            renderInstitutionProfile();
        }
    } catch (e) {
        console.error('Kurum profili yüklenemedi:', e);
    }
}

function renderInstitutionProfile() {
    const p = globalInstitutionProfile;
    const inputName = document.getElementById('input-profile-name');
    const inputCurr = document.getElementById('input-profile-currency');
    const inputTax = document.getElementById('input-profile-tax');
    const inputPhone = document.getElementById('input-profile-phone');
    const inputEmail = document.getElementById('input-profile-email');
    const inputWeb = document.getElementById('input-profile-web');

    if (inputName) inputName.value = p.kurum_adi || 'oftek';
    if (inputCurr) inputCurr.value = p.para_birimi || '₺';
    if (inputTax) inputTax.value = p.vergi_no || '';
    if (inputPhone) inputPhone.value = p.telefon || '';
    if (inputEmail) inputEmail.value = p.eposta || '';
    if (inputWeb) inputWeb.value = p.web_adresi || '';

    setProfileType(p.kurum_turu || 'GENEL');

    const brandHeading = document.getElementById('header-brand-title');
    if (brandHeading && p.kurum_adi) {
        brandHeading.innerText = p.kurum_adi;
    }
}

async function saveInstitutionProfile(e) {
    if (e) e.preventDefault();
    const inputName = document.getElementById('input-profile-name');
    const inputCurr = document.getElementById('input-profile-currency');
    const inputTax = document.getElementById('input-profile-tax');
    const inputPhone = document.getElementById('input-profile-phone');
    const inputEmail = document.getElementById('input-profile-email');
    const inputWeb = document.getElementById('input-profile-web');

    const kurum_adi = inputName ? inputName.value.trim() : 'oftek';
    const para_birimi = inputCurr ? (inputCurr.value.trim() || '₺') : '₺';
    const vergi_no = inputTax ? inputTax.value.trim() : '';
    const telefon = inputPhone ? inputPhone.value.trim() : '';
    const eposta = inputEmail ? inputEmail.value.trim() : '';
    const web_adresi = inputWeb ? inputWeb.value.trim() : '';

    try {
        const res = await fetch('/api/settings/profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                kurum_adi,
                kurum_turu: activeProfileType,
                para_birimi,
                vergi_no,
                telefon,
                eposta,
                web_adresi
            })
        });
        const data = await res.json();
        if (res.ok) {
            showToast('Kurum profili başarıyla kaydedildi.', 'success');
            if (data.profile) {
                globalInstitutionProfile = data.profile;
                renderInstitutionProfile();
            }
        } else {
            showToast(data.error || 'Kaydedilemedi.', 'error');
        }
    } catch (err) {
        showToast('Sunucu hatası.', 'error');
    }
}

async function loadSettingsPage() {
    try {
        await Promise.all([
            loadInstitutionProfile(),
            loadEmployeeTypes(),
            loadDebtTypes()
        ]);
        renderSettingsEmployeeTypesList();
        renderSettingsDebtTypesList();
    } catch (e) {
        console.error('Ayarlar sayfası yüklenemedi:', e);
    }
}

function renderSettingsEmployeeTypesList() {
    const listDiv = document.getElementById('settings-employee-types-list');
    const badge = document.getElementById('settings-emp-type-count-badge');
    if (!listDiv) return;

    const types = globalEmployeeTypes || [];
    if (badge) badge.innerText = `${types.length} Tür`;

    if (types.length === 0) {
        listDiv.innerHTML = '<div class="text-slate-400 py-3 text-center text-xs">Tanımlı personel türü yok.</div>';
        return;
    }

    listDiv.innerHTML = types.map(t => `
        <div class="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200 hover:bg-slate-100/70 transition-colors">
            <div class="flex items-center gap-2">
                <span class="font-semibold text-slate-800 text-xs">${t.ad}</span>
                <span class="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-200 text-slate-600 font-bold">${t.kod}</span>
            </div>
            ${t.kod !== 'GENEL' ? `
                <button type="button" onclick="deleteSettingsEmployeeType('${t.kod}', '${t.ad}')" class="text-slate-400 hover:text-rose-600 p-1.5 rounded-lg hover:bg-rose-50 transition-colors" title="Türü Kaldır">
                    <i class="fa-solid fa-trash-can text-xs"></i>
                </button>
            ` : '<span class="text-[10px] text-slate-400 italic">Temel Tür</span>'}
        </div>
    `).join('');
}

async function submitSettingsEmployeeType(e) {
    if (e) e.preventDefault();
    const input = document.getElementById('settings-new-emp-type-name');
    const ad = input ? input.value.trim() : '';
    if (!ad) return;

    try {
        const res = await fetch('/api/employee-types', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ad })
        });
        const data = await res.json();
        if (res.ok) {
            showToast(`'${ad}' personel türü eklendi.`, 'success');
            if (input) input.value = '';
            await loadEmployeeTypes();
            renderSettingsEmployeeTypesList();
        } else {
            showToast(data.error || 'Personel türü eklenemedi.', 'error');
        }
    } catch (err) {
        showToast('Sunucu hatası.', 'error');
    }
}

async function deleteSettingsEmployeeType(kod, ad) {
    if (!confirm(`'${ad}' personel türünü kaldırmak istediğinize emin misiniz?`)) return;
    try {
        const res = await fetch(`/api/employee-types?kod=${kod}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('Personel türü kaldırıldı.', 'success');
            await loadEmployeeTypes();
            renderSettingsEmployeeTypesList();
        } else {
            showToast('Tür silinemedi.', 'error');
        }
    } catch (err) {
        showToast('Sunucu hatası.', 'error');
    }
}

function renderSettingsDebtTypesList() {
    const listDiv = document.getElementById('settings-debt-types-list');
    const badge = document.getElementById('settings-debt-type-count-badge');
    if (!listDiv) return;

    const types = cachedDebtTypes || [];
    if (badge) badge.innerText = `${types.length} Çeşit`;

    if (types.length === 0) {
        listDiv.innerHTML = '<div class="text-slate-400 py-3 text-center text-xs">Tanımlı borç çeşidi bulunamadı.</div>';
        return;
    }

    listDiv.innerHTML = types.map(dt => `
        <div class="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200 hover:bg-slate-100/70 transition-colors">
            <div class="flex items-center gap-2">
                <span class="font-mono font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded text-[10px]">${dt.kod}</span>
                <span class="font-semibold text-slate-800 text-xs">${dt.ad}</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded ${dt.yon === 'BORC' ? 'bg-emerald-50 text-emerald-700 font-bold' : 'bg-rose-50 text-rose-700 font-bold'}">
                    ${dt.yon === 'BORC' ? 'Hakediş' : 'Kesinti'}
                </span>
            </div>
            <button type="button" onclick="deleteSettingsDebtType(${dt.id})" class="text-slate-400 hover:text-rose-600 p-1.5 rounded-lg hover:bg-rose-50 transition-colors" title="Çeşidi Sil">
                <i class="fa-solid fa-trash-can text-xs"></i>
            </button>
        </div>
    `).join('');
}

async function submitSettingsDebtType(e) {
    if (e) e.preventDefault();
    const inputKod = document.getElementById('settings-new-debt-kod');
    const inputAd = document.getElementById('settings-new-debt-ad');
    const kod = inputKod ? inputKod.value.trim() : '';
    const ad = inputAd ? inputAd.value.trim() : '';
    if (!kod || !ad) return;

    try {
        const res = await fetch('/api/employee-debt-types', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ kod, ad, yon: settingsDebtYon })
        });
        const data = await res.json();
        if (res.ok) {
            showToast('Borç çeşidi eklendi.', 'success');
            if (inputKod) inputKod.value = '';
            if (inputAd) inputAd.value = '';
            await loadDebtTypes();
            renderSettingsDebtTypesList();
        } else {
            showToast(data.error || 'Eklenemedi.', 'error');
        }
    } catch (err) {
        showToast('Sunucu hatası.', 'error');
    }
}

async function deleteSettingsDebtType(id) {
    if (!confirm('Bu borç çeşidini silmek istediğinize emin misiniz?')) return;
    try {
        const res = await fetch(`/api/employee-debt-types?id=${id}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('Borç çeşidi silindi.', 'success');
            await loadDebtTypes();
            renderSettingsDebtTypesList();
        } else {
            showToast('Silinemedi.', 'error');
        }
    } catch (err) {
        showToast('Sunucu hatası.', 'error');
    }
}
