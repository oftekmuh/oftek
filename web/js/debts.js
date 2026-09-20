/**
 * oftek - Cari Firma ve Borç Takip Modülü (debts.js)
 */

async function loadDebts() {
    try {
        const yil = typeof currentPeriodYear !== 'undefined' ? currentPeriodYear : '2026';
        const ay = typeof currentPeriodMonth !== 'undefined' ? currentPeriodMonth : '';
        let url = `/api/debts?yil=${yil}`;
        if (ay) url += `&ay=${ay}`;

        const res = await fetch(url);
        const rows = await res.json();
        const tbody = document.getElementById('debts-table-body');
        if (!tbody) return;

        if (!rows || rows.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="py-6 text-center text-slate-400">Kayıtlı borç faturası bulunamadı.</td></tr>';
            return;
        }
        tbody.innerHTML = rows.map(b => `
            <tr class="hover:bg-slate-50/80">
                <td class="py-3 px-4 font-semibold text-slate-900">${b.cari_unvan}</td>
                <td class="py-3 px-4 font-mono text-slate-500">${b.belge_no || '-'}</td>
                <td class="py-3 px-4 text-slate-600">${b.tarih} ${b.vade_tarihi ? `<span class="text-[10px] text-rose-500">(Vade: ${b.vade_tarihi})</span>` : ''}</td>
                <td class="py-3 px-4 text-right font-mono text-slate-800">${fmt(b.toplam_tutar)}</td>
                <td class="py-3 px-4 text-right font-mono text-emerald-600">${fmt(b.odenen_tutar)}</td>
                <td class="py-3 px-4 text-right font-mono font-bold text-rose-600">${fmt(b.kalan_tutar)}</td>
                <td class="py-3 px-4 text-center">
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold ${b.durum === 'KAPANDI' ? 'bg-emerald-50 text-emerald-700' : b.durum === 'KISMI' ? 'bg-amber-50 text-amber-700' : 'bg-rose-50 text-rose-700'}">${b.durum}</span>
                </td>
                <td class="py-3 px-4 text-center">
                    ${b.kalan_tutar > 0 ? `<button onclick="openPayDebtModal(${b.id}, '${b.cari_unvan}', ${b.kalan_tutar})" class="px-2.5 py-1 rounded-lg bg-rose-50 text-rose-700 hover:bg-rose-100 font-semibold text-[11px]">Ödeme Yap</button>` : '<span class="text-slate-400 text-[11px]">Ödendi</span>'}
                </td>
            </tr>
        `).join('');
    } catch (e) {
        console.error("Borçlar yüklenemedi:", e);
    }
}

async function showAddCompanyModal() {
    showModal('modal-add-company');
}

async function submitAddCari(e) {
    if (e) e.preventDefault();
    const tip = document.getElementById('new-cari-tip').value;
    const unvan = document.getElementById('new-cari-unvan').value.trim();
    const yetkili = document.getElementById('new-cari-yetkili').value.trim();
    const telefon = document.getElementById('new-cari-tel').value.trim();

    if (!unvan) {
        showToast('Lütfen unvan giriniz.', 'error');
        return;
    }

    const res = await fetch('/api/cariler', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tip, unvan, yetkili, telefon })
    });
    if (res.ok) {
        showToast('Cari kartı başarıyla kaydedildi.', 'success');
        hideModal('modal-add-company');
        document.getElementById('new-cari-unvan').value = '';
        document.getElementById('new-cari-yetkili').value = '';
        document.getElementById('new-cari-tel').value = '';
    } else {
        showToast('Cari kaydedilemedi.', 'error');
    }
}

async function showAddDebtModal() {
    if (typeof activeSession === 'undefined' || !activeSession) {
        showToast('Borç faturası eklemek için önce bir gün oturumu açmalısınız!', 'error');
        return;
    }
    const searchInp = document.getElementById('debt-cari-search');
    const hiddenId = document.getElementById('debt-cari-id');
    if (searchInp) searchInp.value = '';
    if (hiddenId) hiddenId.value = '';
    showModal('modal-add-debt');
}

async function submitAddDebt(e) {
    if (e) e.preventDefault();
    const cari_id = document.getElementById('debt-cari-id').value;
    const belge_no = document.getElementById('debt-doc-no').value.trim();
    const vade_tarihi = document.getElementById('debt-due-date').value;
    const toplam_tutar = parseFloat(document.getElementById('debt-amount').value || 0);
    const aciklama = document.getElementById('debt-desc').value.trim();

    if (!cari_id) {
        showToast('Lütfen listeden geçerli bir firma seçiniz.', 'error');
        return;
    }
    if (toplam_tutar <= 0) {
        showToast('Geçerli bir fatura tutarı giriniz.', 'error');
        return;
    }

    const res = await fetch('/api/debts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gun_id: activeSession.id, cari_id, belge_no, vade_tarihi, toplam_tutar, aciklama })
    });
    if (res.ok) {
        showToast('Borç faturası kaydedildi.', 'success');
        hideModal('modal-add-debt');
        loadDebts();
    } else {
        showToast('Fatura kaydedilemedi.', 'error');
    }
}

function openPayDebtModal(borcId, unvan, kalan) {
    if (typeof activeSession === 'undefined' || !activeSession) {
        showToast('Ödeme yapabilmek için açık bir gün oturumu gereklidir.', 'error');
        return;
    }
    document.getElementById('pay-debt-id').value = borcId;
    document.getElementById('pay-debt-amount').value = kalan;
    document.getElementById('pay-debt-amount').max = kalan;
    document.getElementById('pay-debt-info').textContent = `${unvan} firmasına kalan açık borç: ${fmt(kalan)}`;
    showModal('modal-pay-debt');
}

async function submitPayDebt(e) {
    if (e) e.preventDefault();
    const borc_id = document.getElementById('pay-debt-id').value;
    const tutar = parseFloat(document.getElementById('pay-debt-amount').value || 0);
    const kaynak_hesap = document.getElementById('pay-debt-source').value;
    const aciklama = document.getElementById('pay-debt-desc').value.trim();

    if (tutar <= 0) {
        showToast('Geçerli bir ödeme tutarı giriniz.', 'error');
        return;
    }

    const res = await fetch('/api/debts/pay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gun_id: activeSession.id, borc_id, tutar, kaynak_hesap, aciklama })
    });
    const data = await res.json();
    if (res.ok) {
        showToast('Ödeme başarıyla işlendi.', 'success');
        hideModal('modal-pay-debt');
        loadDebts();
    } else {
        showToast(data.error || 'Ödeme yapılamadı.', 'error');
    }
}

// Cari Otomatik Tamamlama Motoru
function attachCariAutocomplete(searchInp, hiddenValInp, typeFilter, onSelectCallback) {
    if (!searchInp) return;
    let listEl = null;
    let activeIdx = 0;
    let currentMatches = [];

    function closeList() {
        if (listEl) { listEl.remove(); listEl = null; }
        activeIdx = 0;
        currentMatches = [];
    }

    async function fetchAndRender(q) {
        closeList();
        try {
            const endpoint = typeFilter === 'MUSTERI' ? '/api/customers' : typeFilter === 'FIRMA' ? '/api/companies' : '/api/companies';
            const res = await fetch(endpoint);
            const list = await res.json();
            const filtered = (list || []).filter(c => !q || c.unvan.toLowerCase().includes(q));
            currentMatches = filtered;
            if (filtered.length === 0) return;
            activeIdx = 0;

            listEl = document.createElement('div');
            listEl.className = 'absolute left-0 right-0 top-full mt-1 bg-white border border-slate-200 rounded-xl shadow-xl z-50 max-h-48 overflow-y-auto divide-y divide-slate-100 text-xs font-medium';

            filtered.forEach((c, i) => {
                const item = document.createElement('div');
                const isFirst = (i === 0);
                item.className = 'px-3 py-2 hover:bg-brand-50 cursor-pointer flex items-center justify-between text-slate-700 cari-item ' + (isFirst ? 'bg-brand-50/80 font-semibold' : '');
                item.dataset.index = i;
                item.innerHTML = `
                    <div>
                        <span class="font-bold text-slate-900">${c.unvan}</span>
                        ${c.yetkili ? `<span class="text-slate-400 ml-1 text-[11px]">(${c.yetkili})</span>` : ''}
                    </div>
                    <div class="flex items-center gap-1.5">
                        ${isFirst ? '<span class="cari-tab-badge px-1.5 py-0.5 rounded bg-brand-100 text-brand-700 font-mono text-[9px] font-bold">Tab ⇥</span>' : ''}
                        <span class="font-mono text-slate-500 font-bold">${fmt(c.bakiye || 0)}</span>
                    </div>
                `;
                item.onmousedown = (e) => {
                    e.preventDefault();
                    chooseCari(c);
                };
                listEl.appendChild(item);
            });

            searchInp.parentElement.style.position = 'relative';
            searchInp.parentElement.appendChild(listEl);
        } catch(e) { console.error(e); }
    }

    function chooseCari(c) {
        hiddenValInp.value = c.id;
        searchInp.value = c.unvan;
        closeList();
        if (onSelectCallback) onSelectCallback(c);
        focusNextElement(searchInp);
    }

    searchInp.addEventListener('input', () => {
        fetchAndRender(searchInp.value.toLowerCase().trim());
    });

    searchInp.addEventListener('focus', () => {
        fetchAndRender(searchInp.value.toLowerCase().trim());
    });

    searchInp.addEventListener('blur', () => {
        setTimeout(() => {
            if (listEl && currentMatches.length > 0 && !hiddenValInp.value && searchInp.value.trim()) {
                chooseCari(currentMatches[0]);
            }
            closeList();
        }, 200);
    });

    searchInp.addEventListener('keydown', (e) => {
        if (e.key === 'Tab' || e.key === 'Enter') {
            if (listEl && currentMatches.length > 0) {
                e.preventDefault();
                const idx = (activeIdx >= 0 && activeIdx < currentMatches.length) ? activeIdx : 0;
                chooseCari(currentMatches[idx]);
            }
            return;
        }
        if (e.key === 'ArrowDown') {
            if (!listEl) return;
            e.preventDefault();
            activeIdx = Math.min(activeIdx + 1, currentMatches.length - 1);
            updateCariHighlight();
            return;
        }
        if (e.key === 'ArrowUp') {
            if (!listEl) return;
            e.preventDefault();
            activeIdx = Math.max(activeIdx - 1, 0);
            updateCariHighlight();
            return;
        }
        if (e.key === 'Escape') {
            closeList();
        }
    });

    function updateCariHighlight() {
        if (!listEl) return;
        const items = listEl.querySelectorAll('.cari-item');
        items.forEach((item, idx) => {
            const isMatch = (idx === activeIdx);
            item.classList.toggle('bg-brand-50', isMatch);
            item.classList.toggle('font-semibold', isMatch);
            let badge = item.querySelector('.cari-tab-badge');
            if (isMatch) {
                if (!badge) {
                    const badgeSpan = document.createElement('span');
                    badgeSpan.className = 'cari-tab-badge px-1.5 py-0.5 rounded bg-brand-100 text-brand-700 font-mono text-[9px] font-bold';
                    badgeSpan.textContent = 'Tab ⇥';
                    const rightBox = item.children[1];
                    if (rightBox) rightBox.insertBefore(badgeSpan, rightBox.firstChild);
                }
            } else if (badge) {
                badge.remove();
            }
        });
    }
}
