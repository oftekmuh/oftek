/**
 * oftek - Personel Tahakkuk Fişi & Borç Çeşitleri Yönetimi
 */

let currentEmpAccYear = new Date().getFullYear().toString();
let currentEmpAccMonth = (new Date().getMonth() + 1).toString();
let cachedDebtTypes = [];

function setEmpAccYear(yr) {
    currentEmpAccYear = yr;
    document.querySelectorAll('.emp-year-btn').forEach(b => {
        if (b.id === 'btn-emp-year-' + yr) {
            b.className = "emp-year-btn flex-1 py-1 rounded-lg font-bold bg-white text-slate-800 shadow-xs text-center";
        } else {
            b.className = "emp-year-btn flex-1 py-1 rounded-lg font-bold text-slate-600 hover:text-slate-900 text-center";
        }
    });
}

function toggleEmpMonthPicker() {
    const pop = document.getElementById('emp-month-picker-popover');
    if (pop) pop.classList.toggle('hidden');
}

function initEmpMonthButtons() {
    const cont = document.getElementById('emp-month-buttons-container');
    if (!cont || cont.children.length > 0) return;
    const months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
    months.forEach((m, idx) => {
        const num = idx + 1;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = `py-1 px-1 rounded-lg text-xs text-center ${num === 3 ? 'bg-indigo-50 text-indigo-700 font-bold' : 'hover:bg-slate-100 text-slate-700 font-medium'}`;
        btn.textContent = m;
        btn.onclick = () => {
            currentEmpAccMonth = String(num);
            const lbl = document.getElementById('emp-selected-month-label');
            if (lbl) lbl.textContent = `${m} (${num}. Ay)`;
            const pop = document.getElementById('emp-month-picker-popover');
            if (pop) pop.classList.add('hidden');
        };
        cont.appendChild(btn);
    });
}

function openEmployeeAccrualPage() {
    switchTab('employee_accrual');
}

async function initEmployeeAccrualPage() {
    initEmpMonthButtons();
    const today = (activeSession && activeSession.tarih) ? activeSession.tarih : new Date().toISOString().split('T')[0];
    const dateEl = document.getElementById('emp-acc-date');
    if (dateEl) dateEl.value = today;
    const descEl = document.getElementById('emp-acc-desc');
    if (descEl) descEl.value = `${currentEmpAccYear}/${String(currentEmpAccMonth).padStart(2, '0')} Personel Hakediş ve Maaş Tahakkuku`;

    await loadDebtTypes();
    if (typeof loadEmployees === 'function') await loadEmployees();

    const tbody = document.getElementById('emp-acc-tbody');
    if (tbody && tbody.children.length === 0) {
        addEmpAccrualRow();
    }
    calculateEmpAccTotals();
}

async function loadDebtTypes() {
    try {
        const res = await fetch('/api/employee-debt-types');
        if (res.ok) {
            cachedDebtTypes = await res.json();
            renderDebtTypesList();
        }
    } catch (e) { 
        console.error('Borç çeşitleri yüklenemedi:', e); 
    }
}

function addEmpAccrualRow(defaultPersonelId = '', defaultPersonelName = '', defaultTur = 'MAAS', defaultTutar = '', defaultDesc = '') {
    const tbody = document.getElementById('emp-acc-tbody');
    if (!tbody) return;
    const rowIdx = tbody.children.length + 1;

    const tr = document.createElement('tr');
    tr.className = 'hover:bg-slate-50/80 transition-colors emp-acc-row';

    let turHtml = (cachedDebtTypes || []).map(dt => {
        const isSel = dt.kod === defaultTur ? 'bg-indigo-600 text-white font-bold' : 'bg-slate-100 text-slate-700 hover:bg-slate-200';
        return `<button type="button" onclick="selectRowDebtType(this, '${dt.kod}')" class="emp-row-tur-btn px-2 py-0.5 rounded-md text-[10px] ${isSel}">${dt.ad.split(' ')[0]}</button>`;
    }).join('');

    tr.innerHTML = `
        <td class="py-2.5 px-3 text-center font-mono text-slate-400 font-semibold emp-acc-row-idx">${rowIdx}</td>
        <td class="py-1.5 px-2">
            <div class="relative">
                <input type="text" placeholder="Personel ara (Ad Soyad)..." value="${defaultPersonelName}" autocomplete="off" class="emp-acc-p-search w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-slate-800 outline-none focus:ring-1 focus:ring-indigo-500">
                <input type="hidden" class="emp-acc-p-val" value="${defaultPersonelId}">
            </div>
        </td>
        <td class="py-1.5 px-2">
            <input type="hidden" class="emp-acc-tur-val" value="${defaultTur}">
            <div class="flex flex-wrap items-center gap-1">
                ${turHtml}
            </div>
        </td>
        <td class="py-1.5 px-2">
            <input type="text" value="${defaultDesc}" placeholder="Açıklama" class="emp-acc-row-desc w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs outline-none focus:ring-1 focus:ring-indigo-500">
        </td>
        <td class="py-1.5 px-2 text-right">
            <input type="number" step="0.01" min="0" value="${defaultTutar}" placeholder="0.00" oninput="calculateEmpAccTotals()" class="emp-acc-row-amount w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-mono font-bold text-slate-900 text-right outline-none focus:ring-1 focus:ring-indigo-500">
        </td>
        <td class="py-1.5 px-2 text-center">
            <button type="button" onclick="this.closest('tr').remove(); calculateEmpAccTotals();" class="text-slate-400 hover:text-rose-600 p-1.5 rounded transition-colors">
                <i class="fa-solid fa-trash-can"></i>
            </button>
        </td>
    `;

    tbody.appendChild(tr);

    const pSearch = tr.querySelector('.emp-acc-p-search');
    const pVal = tr.querySelector('.emp-acc-p-val');
    attachEmployeeAutocomplete(pSearch, pVal, (emp) => {
        if (!tr.querySelector('.emp-acc-row-amount').value && emp.maas > 0) {
            tr.querySelector('.emp-acc-row-amount').value = emp.maas;
            calculateEmpAccTotals();
        }
    });

    calculateEmpAccTotals();
}

function selectRowDebtType(btn, kod) {
    const parent = btn.parentElement;
    parent.querySelectorAll('.emp-row-tur-btn').forEach(b => {
        b.className = 'emp-row-tur-btn px-2 py-0.5 rounded-md text-[10px] bg-slate-100 text-slate-700 hover:bg-slate-200';
    });
    btn.className = 'emp-row-tur-btn px-2 py-0.5 rounded-md text-[10px] bg-indigo-600 text-white font-bold';
    const tr = btn.closest('tr');
    tr.querySelector('.emp-acc-tur-val').value = kod;
}

function attachEmployeeAutocomplete(searchInp, hiddenValInp, onSelectCallback) {
    if (!searchInp) return;
    let listEl = null;
    let activeIdx = 0;
    let currentMatches = [];

    function closeList() {
        if (listEl) { listEl.remove(); listEl = null; }
        activeIdx = 0;
        currentMatches = [];
    }

    function renderList(emps) {
        closeList();
        currentMatches = emps || [];
        if (!emps || emps.length === 0) return;
        activeIdx = 0;

        listEl = document.createElement('div');
        listEl.className = 'absolute left-0 right-0 top-full mt-1 bg-white border border-slate-200 rounded-xl shadow-xl z-50 max-h-48 overflow-y-auto divide-y divide-slate-100 text-xs font-medium';

        emps.forEach((emp, i) => {
            const item = document.createElement('div');
            const isFirst = (i === 0);
            item.className = 'px-3 py-2 hover:bg-indigo-50 cursor-pointer flex items-center justify-between text-slate-700 emp-item ' + (isFirst ? 'bg-indigo-50/80 font-semibold' : '');
            item.dataset.index = i;
            item.innerHTML = `
                <div>
                    <span class="font-bold text-slate-900">${emp.ad_soyad}</span>
                    <span class="text-slate-400 ml-1 text-[11px]">${emp.tc_kimlik || ''}</span>
                </div>
                <div class="flex items-center gap-1.5">
                    ${isFirst ? '<span class="emp-tab-badge px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700 font-mono text-[9px] font-bold">Tab ⇥</span>' : ''}
                    <span class="font-mono text-indigo-600 font-bold">${fmt(emp.maas)}</span>
                </div>
            `;
            item.onmousedown = (e) => {
                e.preventDefault();
                chooseEmployee(emp);
            };
            listEl.appendChild(item);
        });

        searchInp.parentElement.style.position = 'relative';
        searchInp.parentElement.appendChild(listEl);
    }

    function chooseEmployee(emp) {
        hiddenValInp.value = emp.id;
        searchInp.value = emp.ad_soyad;
        closeList();
        if (onSelectCallback) onSelectCallback(emp);
        focusNextElement(searchInp);
    }

    searchInp.addEventListener('input', () => {
        const q = searchInp.value.toLowerCase().trim();
        const matches = (globalEmployeesList || []).filter(e => e.ad_soyad.toLowerCase().includes(q));
        renderList(matches);
    });

    searchInp.addEventListener('focus', () => {
        const q = searchInp.value.toLowerCase().trim();
        const matches = (globalEmployeesList || []).filter(e => !q || e.ad_soyad.toLowerCase().includes(q));
        renderList(matches);
    });

    searchInp.addEventListener('blur', () => {
        setTimeout(() => {
            if (listEl && currentMatches.length > 0 && !hiddenValInp.value && searchInp.value.trim()) {
                chooseEmployee(currentMatches[0]);
            }
            closeList();
        }, 200);
    });

    searchInp.addEventListener('keydown', (e) => {
        if (e.key === 'Tab' || e.key === 'Enter') {
            if (listEl && currentMatches.length > 0) {
                e.preventDefault();
                const idx = (activeIdx >= 0 && activeIdx < currentMatches.length) ? activeIdx : 0;
                chooseEmployee(currentMatches[idx]);
            }
            return;
        }
        if (e.key === 'ArrowDown') {
            if (!listEl) return;
            e.preventDefault();
            activeIdx = Math.min(activeIdx + 1, currentMatches.length - 1);
            updateEmpHighlight();
            return;
        }
        if (e.key === 'ArrowUp') {
            if (!listEl) return;
            e.preventDefault();
            activeIdx = Math.max(activeIdx - 1, 0);
            updateEmpHighlight();
            return;
        }
        if (e.key === 'Escape') {
            closeList();
            return;
        }
    });

    function updateEmpHighlight() {
        if (!listEl) return;
        const items = listEl.querySelectorAll('.emp-item');
        items.forEach((it, idx) => {
            const badge = it.querySelector('.emp-tab-badge');
            if (idx === activeIdx) {
                it.classList.add('bg-indigo-50/80', 'font-semibold');
                if (!badge) {
                    const badgeCont = it.querySelector('div:last-child');
                    if (badgeCont) {
                        const newB = document.createElement('span');
                        newB.className = 'emp-tab-badge px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700 font-mono text-[9px] font-bold';
                        newB.innerText = 'Tab ⇥';
                        badgeCont.prepend(newB);
                    }
                }
                it.scrollIntoView({ block: 'nearest' });
            } else {
                it.classList.remove('bg-indigo-50/80', 'font-semibold');
                if (badge) badge.remove();
            }
        });
    }
}

function populateAllEmployeesAccrual() {
    const tbody = document.getElementById('emp-acc-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (!globalEmployeesList || globalEmployeesList.length === 0) {
        showToast('Kayıtlı aktif personel bulunamadı.', 'info');
        return;
    }
    globalEmployeesList.forEach(emp => {
        addEmpAccrualRow(emp.id, emp.ad_soyad, 'MAAS', emp.maas, `${emp.ad_soyad} Maaş Hakedişi`);
    });
    calculateEmpAccTotals();
    showToast(`${globalEmployeesList.length} aktif personel tahakkuk fişine eklendi.`, 'success');
}

function calculateEmpAccTotals() {
    const rows = document.querySelectorAll('#emp-acc-tbody .emp-acc-row');
    let total = 0.0;
    rows.forEach(r => {
        const amt = parseFloat(r.querySelector('.emp-acc-row-amount')?.value || 0);
        if (amt > 0) total += amt;
    });
    const disp = document.getElementById('emp-acc-total-display');
    if (disp) disp.textContent = fmt(total);
}

async function submitEmployeeAccrualVoucher() {
    const tarih = document.getElementById('emp-acc-date').value;
    const aciklama = document.getElementById('emp-acc-desc').value.trim();
    const satirlar = [];

    document.querySelectorAll('#emp-acc-tbody .emp-acc-row').forEach(r => {
        const pid = r.querySelector('.emp-acc-p-val')?.value;
        const tur = r.querySelector('.emp-acc-tur-val')?.value || 'MAAS';
        const tutar = parseFloat(r.querySelector('.emp-acc-row-amount')?.value || 0);
        const s_desc = r.querySelector('.emp-acc-row-desc')?.value.trim();
        if (pid && tutar > 0) {
            satirlar.push({ personel_id: parseInt(pid), tur, tutar, aciklama: s_desc });
        }
    });

    if (satirlar.length === 0) {
        showToast('Tahakkuk edilecek en az bir personel satırı giriniz.', 'error');
        return;
    }

    try {
        const res = await fetch('/api/employees/accrual-voucher', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tarih,
                donem_yil: parseInt(currentEmpAccYear),
                donem_ay: parseInt(currentEmpAccMonth),
                aciklama,
                satirlar
            })
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Tahakkuk fişi kaydedilemedi.', 'error');
            return;
        }
        showToast(data.message || 'Tahakkuk fişi başarıyla oluşturuldu.', 'success');
        switchTab('personel');
        if (typeof loadEmployees === 'function') loadEmployees();
        loadAccrualReport();
    } catch(e) {
        console.error(e);
        showToast('Sunucu bağlantı hatası.', 'error');
    }
}

function showDebtTypesModal() {
    loadDebtTypes();
    showModal('modal-debt-types');
}

let newDebtTypeYon = 'BORC';
function setNewDebtTypeYon(yon) {
    newDebtTypeYon = yon;
    const btnB = document.getElementById('btn-debt-type-borc');
    const btnA = document.getElementById('btn-debt-type-alacak');
    if (btnB && btnA) {
        btnB.className = yon === 'BORC' ? 
            'debt-type-yon-btn flex-1 py-1 rounded-lg font-bold text-[10px] bg-white text-slate-800 shadow-xs text-center' : 
            'debt-type-yon-btn flex-1 py-1 rounded-lg font-bold text-[10px] text-slate-600 hover:text-slate-900 text-center';
        btnA.className = yon === 'ALACAK' ? 
            'debt-type-yon-btn flex-1 py-1 rounded-lg font-bold text-[10px] bg-white text-slate-800 shadow-xs text-center' : 
            'debt-type-yon-btn flex-1 py-1 rounded-lg font-bold text-[10px] text-slate-600 hover:text-slate-900 text-center';
    }
}

function renderDebtTypesList() {
    const cont = document.getElementById('debt-types-list-container');
    if (!cont) return;
    if (!cachedDebtTypes || cachedDebtTypes.length === 0) {
        cont.innerHTML = '<div class="py-4 text-center text-slate-400">Tanımlı borç çeşidi bulunamadı.</div>';
        return;
    }
    cont.innerHTML = cachedDebtTypes.map(dt => `
        <div class="py-2 flex items-center justify-between">
            <div>
                <span class="font-mono font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded text-[11px] mr-2">${dt.kod}</span>
                <span class="font-semibold text-slate-800">${dt.ad}</span>
                <span class="text-[10px] ml-2 px-1.5 py-0.5 rounded ${dt.yon === 'BORC' ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'} font-bold">${dt.yon === 'BORC' ? 'Hakediş' : 'Kesinti'}</span>
            </div>
            <button type="button" onclick="deleteDebtType(${dt.id})" class="text-slate-400 hover:text-rose-600 p-1"><i class="fa-solid fa-trash-can"></i></button>
        </div>
    `).join('');
}

async function submitNewDebtType(e) {
    e.preventDefault();
    const kod = document.getElementById('new-debt-type-kod').value.trim();
    const ad = document.getElementById('new-debt-type-ad').value.trim();
    try {
        const res = await fetch('/api/employee-debt-types', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ kod, ad, yon: newDebtTypeYon })
        });
        const data = await res.json();
        if (res.ok) {
            showToast('Borç çeşidi eklendi.', 'success');
            document.getElementById('new-debt-type-kod').value = '';
            document.getElementById('new-debt-type-ad').value = '';
            loadDebtTypes();
        } else {
            showToast(data.error || 'Eklenemedi.', 'error');
        }
    } catch(e) { console.error(e); }
}

async function deleteDebtType(id) {
    if (!confirm('Bu borç çeşidini silmek istediğinize emin misiniz?')) return;
    try {
        const res = await fetch(`/api/employee-debt-types?id=${id}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('Borç çeşidi silindi.', 'success');
            loadDebtTypes();
        }
    } catch(e) { console.error(e); }
}

// ================= PERSONEL TAHAKKUK RAPORU =================
let currentAccrualReportTur = 'TUMU';

function filterAccrualReportType(tur) {
    currentAccrualReportTur = tur;
    document.querySelectorAll('.acc-filter-type').forEach(b => {
        if (b.dataset.tur === tur) {
            b.className = "acc-filter-type px-2.5 py-1 rounded-lg font-semibold bg-white text-slate-800 shadow-xs";
        } else {
            b.className = "acc-filter-type px-2.5 py-1 rounded-lg font-semibold text-slate-600 hover:text-slate-900";
        }
    });
    loadAccrualReport();
}

async function loadAccrualReport() {
    try {
        const yr = typeof currentPeriodYear !== 'undefined' ? currentPeriodYear : new Date().getFullYear().toString();
        const mo = typeof currentPeriodMonth !== 'undefined' ? currentPeriodMonth : '';
        let url = `/api/employees/accrual-report?yil=${yr}`;
        if (mo) url += `&ay=${mo}`;
        if (currentAccrualReportTur && currentAccrualReportTur !== 'TUMU') url += `&tur=${currentAccrualReportTur}`;

        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();

        const cardsCont = document.getElementById('accrual-report-summary-cards');
        if (cardsCont) {
            let cardsHtml = `
                <div class="bg-indigo-50/70 p-3 rounded-xl border border-indigo-100">
                    <div class="text-[10px] text-indigo-600 font-bold uppercase">Genel Toplam Hakediş</div>
                    <div class="text-base font-mono font-bold text-indigo-900 mt-1">${fmt(data.genel_toplam)}</div>
                </div>
            `;
            for (const [turAdi, tutar] of Object.entries(data.tur_toplamlari || {})) {
                cardsHtml += `
                    <div class="bg-slate-50 p-3 rounded-xl border border-slate-200">
                        <div class="text-[10px] text-slate-500 font-semibold uppercase truncate">${turAdi}</div>
                        <div class="text-sm font-mono font-bold text-slate-800 mt-1">${fmt(tutar)}</div>
                    </div>
                `;
            }
            cardsCont.innerHTML = cardsHtml;
        }

        const tbody = document.getElementById('accrual-report-table-body');
        if (tbody) {
            if (!data.satirlar || data.satirlar.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="py-6 text-center text-slate-400">Seçilen dönem ve filtrede tahakkuk kaydı bulunamadı.</td></tr>';
                return;
            }
            tbody.innerHTML = data.satirlar.map(s => `
                <tr class="hover:bg-slate-50/80">
                    <td class="py-2.5 px-3 text-slate-600 font-medium">${s.tarih}</td>
                    <td class="py-2.5 px-3 font-semibold text-slate-900">${s.ad_soyad}</td>
                    <td class="py-2.5 px-3">
                        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-700">${s.tur_adi}</span>
                    </td>
                    <td class="py-2.5 px-3 text-slate-600">${s.aciklama || '-'}</td>
                    <td class="py-2.5 px-3 text-right font-mono font-bold text-slate-900">${fmt(s.tutar)}</td>
                    <td class="py-2.5 px-3 text-center">
                        ${s.fis_no ? `<span class="px-2 py-0.5 rounded bg-slate-100 font-mono text-[11px] font-bold text-slate-700">#${s.fis_no}</span>` : '<span class="text-slate-300">-</span>'}
                    </td>
                </tr>
            `).join('');
        }
    } catch(e) { 
        console.error(e); 
    }
}
