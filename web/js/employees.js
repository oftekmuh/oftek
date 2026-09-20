/**
 * oftek - Personel Yönetimi ve Dinamik Ek Bilgiler Modülü (employees.js)
 */

let globalEmployeesList = [];
let globalEmployeeTypes = [];
let currentEmployeeTypeFilter = 'ALL';

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

async function loadEmployeeTypes() {
    try {
        const res = await fetch('/api/employee-types');
        if (!res.ok) return;
        globalEmployeeTypes = await res.json();
        renderEmployeeTypeFilters();
        renderNewEmployeeTypePills();
    } catch (e) {
        console.error('Personel türleri yüklenemedi:', e);
    }
}

function renderEmployeeTypeFilters() {
    const container = document.getElementById('employee-type-filters');
    if (!container) return;
    
    let html = `
        <button type="button" onclick="setEmployeeTypeFilter('ALL')" class="emp-filter-btn px-2.5 py-1 rounded-xl text-xs font-semibold transition-all ${currentEmployeeTypeFilter === 'ALL' ? 'bg-indigo-600 text-white shadow-xs' : 'bg-slate-100 hover:bg-slate-200 text-slate-600'}">
            Tümü (${globalEmployeesList ? globalEmployeesList.length : 0})
        </button>
    `;

    (globalEmployeeTypes || []).forEach(t => {
        const count = (globalEmployeesList || []).filter(e => e.personel_turu_kod === t.kod).length;
        const isActive = currentEmployeeTypeFilter === t.kod;
        html += `
            <button type="button" onclick="setEmployeeTypeFilter('${t.kod}')" class="emp-filter-btn px-2.5 py-1 rounded-xl text-xs font-semibold transition-all ${isActive ? 'bg-indigo-600 text-white shadow-xs' : 'bg-slate-100 hover:bg-slate-200 text-slate-600'}">
                ${t.ad} <span class="opacity-70 text-[10px]">(${count})</span>
            </button>
        `;
    });
    container.innerHTML = html;
}

function setEmployeeTypeFilter(kod) {
    currentEmployeeTypeFilter = kod;
    renderEmployeeTypeFilters();
    renderEmployeesTable();
}

function renderNewEmployeeTypePills(selectedKod = 'GENEL') {
    const container = document.getElementById('new-emp-type-pills');
    if (!container) return;
    const hiddenInput = document.getElementById('new-emp-type-code');
    if (hiddenInput) hiddenInput.value = selectedKod;

    container.innerHTML = (globalEmployeeTypes || []).map(t => {
        const isSel = t.kod === selectedKod;
        return `
            <button type="button" onclick="selectNewEmpType('${t.kod}', this)" class="new-emp-type-btn px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${isSel ? 'bg-indigo-600 text-white shadow-xs' : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'}">
                ${t.ad}
            </button>
        `;
    }).join('');
}

function selectNewEmpType(kod, btn) {
    const hiddenInput = document.getElementById('new-emp-type-code');
    if (hiddenInput) hiddenInput.value = kod;
    const container = document.getElementById('new-emp-type-pills');
    if (container) {
        container.querySelectorAll('.new-emp-type-btn').forEach(b => {
            b.className = 'new-emp-type-btn px-3 py-1.5 rounded-lg text-xs font-semibold transition-all bg-white text-slate-700 hover:bg-slate-100 border border-slate-200';
        });
    }
    btn.className = 'new-emp-type-btn px-3 py-1.5 rounded-lg text-xs font-semibold transition-all bg-indigo-600 text-white shadow-xs';
}

function showEmployeeTypesModal() {
    renderEmployeeTypesList();
    showModal('modal-employee-types');
}

function renderEmployeeTypesList() {
    const listDiv = document.getElementById('employee-types-list');
    if (!listDiv) return;
    if (!globalEmployeeTypes || globalEmployeeTypes.length === 0) {
        listDiv.innerHTML = '<div class="text-slate-400 py-2 text-center">Tanımlı personel türü yok.</div>';
        return;
    }
    listDiv.innerHTML = globalEmployeeTypes.map(t => `
        <div class="flex items-center justify-between p-2 rounded-xl bg-slate-50 border border-slate-200 hover:bg-slate-100/70 transition-colors">
            <div class="flex items-center gap-2">
                <span class="font-semibold text-slate-800">${t.ad}</span>
                <span class="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-200 text-slate-600 font-bold">${t.kod}</span>
            </div>
            ${t.kod !== 'GENEL' ? `
                <button type="button" onclick="deleteEmployeeType('${t.kod}', '${t.ad}')" class="text-rose-500 hover:text-rose-700 p-1 rounded hover:bg-rose-50" title="Türü Kaldır">
                    <i class="fa-solid fa-trash-can text-xs"></i>
                </button>
            ` : '<span class="text-[10px] text-slate-400 italic">Temel Tür</span>'}
        </div>
    `).join('');
}

async function submitNewEmployeeType(e) {
    if (e) e.preventDefault();
    const input = document.getElementById('new-emp-type-name');
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
            showToast(`'${ad}' türü eklendi.`, 'success');
            if (input) input.value = '';
            await loadEmployeeTypes();
            renderEmployeeTypesList();
        } else {
            showToast(data.error || 'Personel türü eklenemedi.', 'error');
        }
    } catch (err) {
        showToast('Sunucu hatası.', 'error');
    }
}

async function deleteEmployeeType(kod, ad) {
    if (!confirm(`'${ad}' personel türünü kaldırmak istediğinize emin misiniz?`)) return;
    try {
        const res = await fetch(`/api/employee-types?kod=${kod}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('Personel türü kaldırıldı.', 'success');
            await loadEmployeeTypes();
            renderEmployeeTypesList();
        } else {
            showToast('Tür silinemedi.', 'error');
        }
    } catch (err) {
        showToast('Sunucu hatası.', 'error');
    }
}

function addEmpCustomFieldRow(baslik = '', veri_tipi = 'METIN', deger = '') {
    const container = document.getElementById('emp-custom-fields-container');
    if (!container) return;

    const row = document.createElement('div');
    row.className = 'custom-field-row flex items-center gap-2 p-2 bg-slate-50 border border-slate-200 rounded-xl';
    row.innerHTML = `
        <input type="text" class="custom-field-title flex-1 bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs outline-none focus:ring-2 focus:ring-indigo-500" placeholder="Başlık (Örn: Kan Grubu)" value="${escapeHtml(baslik)}">
        
        <div class="flex rounded-lg border border-slate-200 overflow-hidden text-[11px] font-semibold shrink-0 bg-white">
            <button type="button" onclick="setRowFieldType(this, 'METIN')" class="field-type-btn px-2 py-1 transition-colors ${veri_tipi === 'METIN' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-50'}">Metin</button>
            <button type="button" onclick="setRowFieldType(this, 'SAYI')" class="field-type-btn px-2 py-1 transition-colors ${veri_tipi === 'SAYI' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-50'}">Sayı</button>
            <button type="button" onclick="setRowFieldType(this, 'TARIH')" class="field-type-btn px-2 py-1 transition-colors ${veri_tipi === 'TARIH' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-50'}">Tarih</button>
        </div>
        <input type="hidden" class="custom-field-type" value="${veri_tipi}">

        <input type="${veri_tipi === 'SAYI' ? 'number' : (veri_tipi === 'TARIH' ? 'date' : 'text')}" class="custom-field-value flex-1 bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs outline-none focus:ring-2 focus:ring-indigo-500" placeholder="Değer" value="${escapeHtml(deger)}">
        
        <button type="button" onclick="this.closest('.custom-field-row').remove()" class="text-slate-400 hover:text-rose-600 p-1 rounded transition-colors shrink-0" title="Alanı Sil">
            <i class="fa-solid fa-trash-can text-xs"></i>
        </button>
    `;
    container.appendChild(row);
}

function setRowFieldType(btn, type) {
    const parentGroup = btn.parentElement;
    const row = btn.closest('.custom-field-row');
    const typeInput = row.querySelector('.custom-field-type');
    const valInput = row.querySelector('.custom-field-value');

    parentGroup.querySelectorAll('.field-type-btn').forEach(b => {
        b.className = 'field-type-btn px-2 py-1 transition-colors text-slate-600 hover:bg-slate-50';
    });
    btn.className = 'field-type-btn px-2 py-1 transition-colors bg-indigo-600 text-white';

    typeInput.value = type;
    if (type === 'SAYI') {
        valInput.type = 'number';
        valInput.placeholder = 'Sayısal değer';
    } else if (type === 'TARIH') {
        valInput.type = 'date';
        valInput.placeholder = 'YYYY-AA-GG';
    } else {
        valInput.type = 'text';
        valInput.placeholder = 'Değer';
    }
}

async function loadEmployees() {
    try {
        const yil = typeof currentPeriodYear !== 'undefined' ? currentPeriodYear : new Date().getFullYear().toString();
        const ay = typeof currentPeriodMonth !== 'undefined' ? currentPeriodMonth : '';
        let url = `/api/employees?yil=${yil}`;
        if (ay) url += `&ay=${ay}`;

        const res = await fetch(url);
        const employees = await res.json();
        globalEmployeesList = employees || [];
        renderEmployeesTable();
        renderEmployeeTypeFilters();
        if (typeof loadAccrualReport === 'function') loadAccrualReport();
    } catch(e) {
        console.error("Personeller yüklenemedi:", e);
    }
}

function renderEmployeesTable() {
    const tbody = document.getElementById('employees-table-body');
    if (!tbody) return;

    let filtered = globalEmployeesList || [];
    if (currentEmployeeTypeFilter !== 'ALL') {
        filtered = filtered.filter(e => e.personel_turu_kod === currentEmployeeTypeFilter);
    }

    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="py-6 text-center text-slate-400">Kayıtlı personel bulunamadı.</td></tr>';
        return;
    }

    tbody.innerHTML = filtered.map(emp => {
        let customBadges = '';
        if (emp.ek_bilgiler && emp.ek_bilgiler.length > 0) {
            customBadges = `
                <div class="flex flex-wrap gap-1 mt-1.5">
                    ${emp.ek_bilgiler.map(eb => `
                        <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-slate-100 text-slate-700 text-[10px] border border-slate-200/60">
                            <span class="text-slate-400 font-medium">${eb.baslik}:</span>
                            <span class="font-bold text-slate-800">${eb.deger}</span>
                        </span>
                    `).join('')}
                </div>
            `;
        }

        return `
            <tr class="hover:bg-slate-50/80">
                <td class="py-3 px-4">
                    <div class="flex items-center gap-2">
                        <span class="font-semibold text-slate-900 text-xs">${emp.ad_soyad}</span>
                        <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-100">${emp.personel_turu_ad || 'Genel Personel'}</span>
                    </div>
                    ${emp.tc_kimlik ? `<div class="text-[10px] text-slate-400 mt-0.5"><i class="fa-solid fa-id-card mr-1"></i>TC: ${emp.tc_kimlik} ${emp.telefon ? ' • Tel: ' + emp.telefon : ''}</div>` : ''}
                    ${customBadges}
                </td>
                <td class="py-3 px-4 font-mono text-indigo-600 font-semibold">${fmt(emp.maas)}</td>
                <td class="py-3 px-4 text-right font-mono text-slate-800">${fmt(emp.donem_hakedis)}</td>
                <td class="py-3 px-4 text-right font-mono text-emerald-600">${fmt(emp.donem_odenen)}</td>
                <td class="py-3 px-4 text-right font-mono font-bold text-amber-600">${fmt(emp.anlik_borc)}</td>
                <td class="py-3 px-4 text-center space-x-1.5">
                    <button onclick="openPayEmployeeModal(${emp.id}, '${emp.ad_soyad}', ${emp.anlik_borc})" class="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-semibold text-[11px]">Ödeme Yap</button>
                    <button onclick="openEmpAccrualModal(${emp.id}, '${emp.ad_soyad}')" class="px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-semibold text-[11px]">Hakediş</button>
                    <button onclick="deleteEmployee(${emp.id}, '${emp.ad_soyad}')" title="Personeli Sil" class="px-2.5 py-1 rounded-lg bg-rose-50 text-rose-700 hover:bg-rose-100 font-semibold text-[11px]"><i class="fa-solid fa-trash-can mr-1"></i>Sil</button>
                </td>
            </tr>
        `;
    }).join('');
}

function showAddEmployeeModal() {
    renderNewEmployeeTypePills('GENEL');
    const customFields = document.getElementById('emp-custom-fields-container');
    if (customFields) customFields.innerHTML = '';
    showModal('modal-add-employee');
}

async function submitAddEmployee(e) {
    if (e) e.preventDefault();
    const ad_soyad = document.getElementById('new-emp-name').value.trim();
    const tc_kimlik = document.getElementById('new-emp-tc').value.trim();
    const telefon = document.getElementById('new-emp-phone') ? document.getElementById('new-emp-phone').value.trim() : '';
    const maas = parseFloat(document.getElementById('new-emp-salary').value || 0);
    const iban = document.getElementById('new-emp-iban').value.trim();
    const personel_turu_kod = document.getElementById('new-emp-type-code') ? document.getElementById('new-emp-type-code').value : 'GENEL';

    const ek_bilgiler = [];
    document.querySelectorAll('#emp-custom-fields-container .custom-field-row').forEach(row => {
        const baslikInput = row.querySelector('.custom-field-title');
        const typeInput = row.querySelector('.custom-field-type');
        const valInput = row.querySelector('.custom-field-value');
        if (baslikInput && baslikInput.value.trim()) {
            ek_bilgiler.push({
                baslik: baslikInput.value.trim(),
                veri_tipi: typeInput ? typeInput.value : 'METIN',
                deger: valInput ? valInput.value.trim() : ''
            });
        }
    });

    const res = await fetch('/api/employees', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ad_soyad, tc_kimlik, telefon, maas, iban, personel_turu_kod, ek_bilgiler })
    });
    if (res.ok) {
        showToast('Personel kartı eklendi.', 'success');
        hideModal('modal-add-employee');
        e.target.reset();
        await loadEmployees();
    } else {
        const data = await res.json();
        showToast(data.error || 'Hata oluştu.', 'error');
    }
}

async function accrueCurrentMonthSalaries() {
    if (typeof activeSession === 'undefined' || !activeSession) {
        showToast('Maaş tahakkuk ettirmek için açık bir gün oturumu gereklidir.', 'error');
        return;
    }
    const yil = parseInt(currentPeriodYear);
    const ayVal = currentPeriodMonth;
    const ay = ayVal ? parseInt(ayVal) : activeSession.donem_ay;

    const res = await fetch('/api/employees/accrue-month', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gun_id: activeSession.id, donem_yil: yil, donem_ay: ay })
    });
    const data = await res.json();
    if (res.ok) {
        showToast(`${yil}/${ay}. Ay için ${data.created_count} personele maaş tahakkuk ettirildi (${data.skipped_count} personel önceden tahakkuklu olduğundan atlandı).`, 'success');
        loadEmployees();
    } else {
        showToast(data.error || 'Maaş tahakkuku yapılamadı.', 'error');
    }
}

function openPayEmployeeModal(id, ad, borc) {
    if (typeof activeSession === 'undefined' || !activeSession) {
        showToast('Ödeme yapabilmek için açık bir gün oturumu gereklidir.', 'error');
        return;
    }
    document.getElementById('pay-emp-id').value = id;
    document.getElementById('pay-emp-amount').value = borc > 0 ? borc : '';
    document.getElementById('pay-emp-info').textContent = `${ad} personeline kalan net borç: ${fmt(borc)}`;
    showModal('modal-pay-employee');
}

async function submitPayEmployee(e) {
    if (e) e.preventDefault();
    const personel_id = document.getElementById('pay-emp-id').value;
    const tutar = document.getElementById('pay-emp-amount').value;
    const kaynak_hesap = document.getElementById('pay-emp-source').value;
    const aciklama = document.getElementById('pay-emp-desc').value;

    const res = await fetch('/api/employees/pay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gun_id: activeSession.id, personel_id, tutar, kaynak_hesap, aciklama })
    });
    if (res.ok) {
        showToast('Personel ödemesi kaydedildi.', 'success');
        hideModal('modal-pay-employee');
        loadEmployees();
    } else {
        showToast('Hata oluştu.', 'error');
    }
}

function openEmpAccrualModal(id, ad) {
    if (typeof activeSession === 'undefined' || !activeSession) {
        showToast('Tahakkuk eklemek için açık bir gün oturumu gereklidir.', 'error');
        return;
    }
    document.getElementById('accrual-emp-id').value = id;
    document.getElementById('accrual-emp-info').textContent = `${ad} personeline hakediş ekle`;
    showModal('modal-emp-accrual');
}

async function submitEmpAccrual(e) {
    if (e) e.preventDefault();
    const personel_id = document.getElementById('accrual-emp-id').value;
    const tur = document.getElementById('accrual-tur').value;
    const tutar = document.getElementById('accrual-amount').value;
    const aciklama = document.getElementById('accrual-desc').value;

    const res = await fetch('/api/employees/accrual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gun_id: activeSession.id, personel_id, tur, tutar, aciklama })
    });
    if (res.ok) {
        showToast('Hakediş tahakkuk ettirildi.', 'success');
        hideModal('modal-emp-accrual');
        loadEmployees();
    } else {
        showToast('Hata oluştu.', 'error');
    }
}

async function deleteEmployee(empId, empName) {
    if (!confirm(`'${empName}' adlı personeli silmek istediğinize emin misiniz?`)) return;
    try {
        const res = await fetch(`/api/employees?id=${empId}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('Personel başarıyla silindi.', 'success');
            await loadEmployees();
        } else {
            const data = await res.json();
            showToast(data.error || 'Personel silinemedi.', 'error');
        }
    } catch (err) {
        showToast('Sunucu hatası.', 'error');
    }
}
