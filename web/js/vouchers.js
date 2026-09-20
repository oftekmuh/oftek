/**
 * oftek - Yevmiye Fiş Girişi & Autocomplete Motoru
 * (Modal Fişi, Tam Sayfa Fişi, Akıllı Kısayollar ve Otomatik Tamamlama)
 */

let cachedDescriptions = [];

async function loadVoucherDescriptions() {
    try {
        const res = await fetch('/api/vouchers/descriptions');
        if (res.ok) {
            const data = await res.json();
            cachedDescriptions = data.descriptions || [];
        }
    } catch(e) { 
        console.error('Açıklamalar yüklenirken hata:', e); 
    }
}

function attachDescriptionAutocomplete(inputEl, onSelectCallback) {
    if (!inputEl) return;
    let listEl = null;
    let currentMatches = [];
    let activeIdx = 0;

    function showList(items) {
        closeList();
        currentMatches = items || [];
        if (!items || items.length === 0) return;
        activeIdx = 0;

        listEl = document.createElement('div');
        listEl.className = 'absolute left-0 right-0 top-full mt-1 bg-white border border-slate-200 rounded-xl shadow-xl z-50 max-h-48 overflow-y-auto divide-y divide-slate-100 text-xs font-normal';

        items.forEach((text, i) => {
            const item = document.createElement('div');
            const isFirst = (i === 0);
            item.className = 'px-3 py-2 hover:bg-slate-50 cursor-pointer flex items-center justify-between text-slate-700 desc-item ' + (isFirst ? 'bg-slate-100 font-semibold' : '');
            item.dataset.index = i;
            item.innerHTML = `
                <span class="truncate">${text}</span>
                ${isFirst ? '<span class="desc-tab-badge px-1.5 py-0.5 rounded bg-slate-200 text-slate-700 font-mono text-[9px] font-bold shrink-0 ml-2">Tab ⇥</span>' : ''}
            `;
            item.onmousedown = (e) => {
                e.preventDefault();
                chooseDesc(text);
            };
            listEl.appendChild(item);
        });

        inputEl.parentElement.style.position = 'relative';
        inputEl.parentElement.appendChild(listEl);
    }

    function chooseDesc(text) {
        inputEl.value = text;
        closeList();
        if (onSelectCallback) {
            onSelectCallback(text);
        } else {
            focusNextElement(inputEl);
        }
    }

    function closeList() {
        if (listEl) { listEl.remove(); listEl = null; }
        activeIdx = 0;
        currentMatches = [];
    }

    inputEl.addEventListener('focus', () => {
        const val = inputEl.value.toLowerCase().trim();
        const filtered = cachedDescriptions.filter(d => !val || d.toLowerCase().includes(val)).slice(0, 10);
        showList(filtered);
    });

    inputEl.addEventListener('input', () => {
        const val = inputEl.value.toLowerCase().trim();
        const filtered = cachedDescriptions.filter(d => d.toLowerCase().includes(val)).slice(0, 10);
        showList(filtered);
    });

    inputEl.addEventListener('blur', () => {
        setTimeout(() => {
            if (listEl && currentMatches.length > 0 && !inputEl.value.trim()) {
                chooseDesc(currentMatches[0]);
            }
            closeList();
        }, 200);
    });

    inputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Tab' || e.key === 'Enter') {
            if (listEl && currentMatches.length > 0) {
                e.preventDefault();
                const idx = (activeIdx >= 0 && activeIdx < currentMatches.length) ? activeIdx : 0;
                chooseDesc(currentMatches[idx]);
            }
            return;
        }
        if (e.key === 'ArrowDown') {
            if (!listEl) return;
            e.preventDefault();
            const items = listEl.querySelectorAll('.desc-item');
            activeIdx = Math.min(activeIdx + 1, items.length - 1);
            updateDescHighlight(items);
            return;
        }
        if (e.key === 'ArrowUp') {
            if (!listEl) return;
            e.preventDefault();
            const items = listEl.querySelectorAll('.desc-item');
            activeIdx = Math.max(activeIdx - 1, 0);
            updateDescHighlight(items);
            return;
        }
        if (e.key === 'Escape') {
            closeList();
            return;
        }
    });

    function updateDescHighlight(items) {
        items.forEach((it, idx) => {
            const badge = it.querySelector('.desc-tab-badge');
            if (idx === activeIdx) {
                it.classList.add('bg-slate-100', 'font-semibold');
                if (!badge) {
                    const newB = document.createElement('span');
                    newB.className = 'desc-tab-badge px-1.5 py-0.5 rounded bg-slate-200 text-slate-700 font-mono text-[9px] font-bold shrink-0 ml-2';
                    newB.innerText = 'Tab ⇥';
                    it.appendChild(newB);
                }
                it.scrollIntoView({ block: 'nearest' });
            } else {
                it.classList.remove('bg-slate-100', 'font-semibold');
                if (badge) badge.remove();
            }
        });
    }
}

function attachAccountAutocomplete(searchInp, hiddenValInp, onSelectCallback) {
    if (!searchInp) return;
    let listEl = null;
    let activeIdx = 0;
    let currentMatches = [];

    function closeList() {
        if (listEl) { listEl.remove(); listEl = null; }
        activeIdx = 0;
        currentMatches = [];
    }

    function renderList(accounts) {
        closeList();
        currentMatches = accounts || [];
        if (!accounts || accounts.length === 0) return;
        activeIdx = 0;

        listEl = document.createElement('div');
        listEl.className = 'absolute left-0 right-0 top-full mt-1 bg-white border border-slate-200 rounded-xl shadow-xl z-50 max-h-56 overflow-y-auto divide-y divide-slate-100 text-xs font-medium';

        accounts.forEach((acc, i) => {
            const item = document.createElement('div');
            const isFirst = (i === 0);
            item.className = 'px-3 py-2 hover:bg-amber-50 cursor-pointer flex items-center justify-between text-slate-700 acc-item ' + (isFirst ? 'bg-amber-100/90 font-semibold' : '');
            item.dataset.index = i;
            item.innerHTML = `
                <div class="flex items-center gap-1.5">
                    <span class="font-mono font-bold text-amber-900">${acc.kod}</span>
                    <span class="text-slate-800">${acc.ad}</span>
                </div>
                <div class="flex items-center gap-1.5 shrink-0">
                    ${isFirst ? '<span class="tab-badge px-1.5 py-0.5 rounded bg-amber-200/80 text-amber-900 font-mono text-[9px] font-bold">Tab ⇥</span>' : ''}
                    <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 font-semibold">${acc.karakter || 'AKTİF'}</span>
                </div>
            `;
            item.onmousedown = (e) => {
                e.preventDefault();
                chooseAccount(acc);
            };
            listEl.appendChild(item);
        });

        searchInp.parentElement.style.position = 'relative';
        searchInp.parentElement.appendChild(listEl);
    }

    function chooseAccount(acc) {
        hiddenValInp.value = acc.kod;
        searchInp.value = `${acc.kod} - ${acc.ad}`;
        closeList();
        if (onSelectCallback) {
            onSelectCallback(acc);
        } else {
            focusNextElement(searchInp);
        }
    }

    searchInp.addEventListener('input', () => {
        const q = searchInp.value.toLowerCase().trim();
        const matches = (globalAccountsList || []).filter(a => 
            a.kod.toLowerCase().includes(q) || a.ad.toLowerCase().includes(q)
        ).slice(0, 15);
        renderList(matches);
    });

    searchInp.addEventListener('focus', () => {
        const q = searchInp.value.toLowerCase().trim();
        const matches = (globalAccountsList || []).filter(a => 
            !q || a.kod.toLowerCase().includes(q) || a.ad.toLowerCase().includes(q)
        ).slice(0, 15);
        renderList(matches);
    });

    searchInp.addEventListener('blur', () => {
        setTimeout(() => {
            if (listEl && currentMatches.length > 0 && !hiddenValInp.value && searchInp.value.trim()) {
                chooseAccount(currentMatches[0]);
            }
            closeList();
        }, 200);
    });

    searchInp.addEventListener('keydown', (e) => {
        if (e.key === 'Tab' || e.key === 'Enter') {
            if (listEl && currentMatches.length > 0) {
                e.preventDefault();
                const idx = (activeIdx >= 0 && activeIdx < currentMatches.length) ? activeIdx : 0;
                chooseAccount(currentMatches[idx]);
            }
            return;
        }
        if (e.key === 'ArrowDown') {
            if (!listEl) return;
            e.preventDefault();
            const items = listEl.querySelectorAll('.acc-item');
            activeIdx = Math.min(activeIdx + 1, items.length - 1);
            updateHighlight(items);
            return;
        }
        if (e.key === 'ArrowUp') {
            if (!listEl) return;
            e.preventDefault();
            const items = listEl.querySelectorAll('.acc-item');
            activeIdx = Math.max(activeIdx - 1, 0);
            updateHighlight(items);
            return;
        }
        if (e.key === 'Escape') {
            closeList();
            return;
        }
    });

    function updateHighlight(items) {
        items.forEach((it, idx) => {
            const badge = it.querySelector('.tab-badge');
            if (idx === activeIdx) {
                it.classList.add('bg-amber-100/90', 'font-semibold');
                if (!badge) {
                    const badgeCont = it.querySelector('div:last-child');
                    if (badgeCont) {
                        const newB = document.createElement('span');
                        newB.className = 'tab-badge px-1.5 py-0.5 rounded bg-amber-200/80 text-amber-900 font-mono text-[9px] font-bold';
                        newB.innerText = 'Tab ⇥';
                        badgeCont.prepend(newB);
                    }
                }
                it.scrollIntoView({ block: 'nearest' });
            } else {
                it.classList.remove('bg-amber-100/90', 'font-semibold');
                if (badge) badge.remove();
            }
        });
    }
}

// ================= MODAL FİŞ GİRİŞİ =================
async function openVoucherEntryModal() {
    await loadAccounts();
    try {
        const res = await fetch('/api/vouchers/next-no');
        const data = await res.json();
        document.getElementById('v-entry-no').value = data.next_no || 1;
    } catch(e) {
        document.getElementById('v-entry-no').value = 1;
    }

    const today = (activeSession && activeSession.tarih) ? activeSession.tarih : new Date().toISOString().split('T')[0];
    document.getElementById('v-entry-date').value = today;
    document.getElementById('v-entry-desc').value = '';

    const tbody = document.getElementById('v-entry-tbody');
    tbody.innerHTML = '';

    addVoucherEntryRow('770.02', '', '', '');
    addVoucherEntryRow('100.01', '', '', '');

    calculateVoucherTotals();
    showModal('modal-voucher-entry');
}

function addVoucherEntryRow(defaultKod = '', defaultDesc = '', defaultBorc = '', defaultAlacak = '') {
    const tbody = document.getElementById('v-entry-tbody');
    if (!tbody) return;
    const rowIdx = tbody.children.length + 1;

    const tr = document.createElement('tr');
    tr.className = 'hover:bg-slate-50/80 transition-colors v-entry-row';

    tr.innerHTML = `
        <td class="py-2 px-2.5 text-center font-mono text-slate-400 font-semibold v-row-idx">${rowIdx}</td>
        <td class="py-1.5 px-2">
            <div class="relative">
                <input type="text" placeholder="Hesap ara..." class="v-input-acc w-full bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs font-semibold text-slate-800 outline-none focus:ring-1 focus:ring-brand-500">
                <input type="hidden" class="v-input-acc-val" value="${defaultKod}">
            </div>
        </td>
        <td class="py-1.5 px-2">
            <input type="text" value="${defaultDesc}" placeholder="Satır açıklaması" class="v-input-desc w-full bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs outline-none focus:ring-1 focus:ring-brand-500">
        </td>
        <td class="py-1.5 px-2 text-right">
            <input type="number" step="0.01" min="0" value="${defaultBorc}" placeholder="0.00" oninput="onVoucherRowAmountInput(this, 'borc')" class="v-input-borc w-full bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs font-mono font-bold text-slate-900 text-right outline-none focus:ring-1 focus:ring-brand-500">
        </td>
        <td class="py-1.5 px-2 text-right">
            <input type="number" step="0.01" min="0" value="${defaultAlacak}" placeholder="0.00" oninput="onVoucherRowAmountInput(this, 'alacak')" class="v-input-alacak w-full bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs font-mono font-bold text-slate-900 text-right outline-none focus:ring-1 focus:ring-brand-500">
        </td>
        <td class="py-1.5 px-2 text-center">
            <button type="button" onclick="removeVoucherEntryRow(this)" title="Satırı Sil" class="text-slate-400 hover:text-rose-600 p-1 rounded transition-colors">
                <i class="fa-solid fa-trash-can"></i>
            </button>
        </td>
    `;

    tbody.appendChild(tr);
    const searchInp = tr.querySelector('.v-input-acc');
    const valInp = tr.querySelector('.v-input-acc-val');
    if (defaultKod) {
        const found = (globalAccountsList || []).find(a => a.kod === defaultKod);
        searchInp.value = found ? `${found.kod} - ${found.ad}` : defaultKod;
    }
    attachAccountAutocomplete(searchInp, valInp);

    reindexVoucherRows();
    calculateVoucherTotals();
}

function onVoucherRowAmountInput(inputEl, type) {
    const tr = inputEl.closest('tr');
    const borcInp = tr.querySelector('.v-input-borc');
    const alacakInp = tr.querySelector('.v-input-alacak');

    const val = parseFloat(inputEl.value || 0);
    if (val > 0) {
        if (type === 'borc' && alacakInp.value) alacakInp.value = '';
        if (type === 'alacak' && borcInp.value) borcInp.value = '';
    }

    calculateVoucherTotals();
}

function removeVoucherEntryRow(btn) {
    const tbody = document.getElementById('v-entry-tbody');
    if (tbody.children.length <= 2) {
        showToast('Yevmiye fişinde en az 2 satır (Borç ve Alacak) bulunmalıdır.', 'error');
        return;
    }
    const tr = btn.closest('tr');
    tr.remove();
    reindexVoucherRows();
    calculateVoucherTotals();
}

function reindexVoucherRows() {
    const rows = document.querySelectorAll('#v-entry-tbody .v-entry-row');
    rows.forEach((r, idx) => {
        const idxEl = r.querySelector('.v-row-idx');
        if (idxEl) idxEl.textContent = idx + 1;
    });
}

function calculateVoucherTotals() {
    const rows = document.querySelectorAll('#v-entry-tbody .v-entry-row');
    let totBorc = 0.0;
    let totAlacak = 0.0;

    rows.forEach(r => {
        const bVal = parseFloat(r.querySelector('.v-input-borc')?.value || 0);
        const aVal = parseFloat(r.querySelector('.v-input-alacak')?.value || 0);
        if (bVal > 0) totBorc += bVal;
        if (aVal > 0) totAlacak += aVal;
    });

    const sumBorcEl = document.getElementById('v-sum-borc');
    const sumAlacakEl = document.getElementById('v-sum-alacak');
    if (sumBorcEl) sumBorcEl.textContent = fmt(totBorc);
    if (sumAlacakEl) sumAlacakEl.textContent = fmt(totAlacak);

    const diff = Math.abs(totBorc - totAlacak);
    const badge = document.getElementById('v-balance-badge');
    const saveBtn = document.getElementById('btn-save-voucher');

    if (!badge || !saveBtn) return;

    if (totBorc > 0 && diff < 0.01) {
        badge.className = "px-2.5 py-1 rounded-full font-bold text-[11px] bg-emerald-100 text-emerald-800 flex items-center gap-1";
        badge.innerHTML = '<i class="fa-solid fa-check"></i> Fiş Dengeli (0.00 ₺)';
        saveBtn.disabled = false;
    } else {
        badge.className = "px-2.5 py-1 rounded-full font-bold text-[11px] bg-rose-100 text-rose-800 flex items-center gap-1";
        badge.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Fark: ${fmt(diff)}`;
        saveBtn.disabled = true;
    }
}

async function submitVoucherEntry() {
    const no = parseInt(document.getElementById('v-entry-no').value);
    const tarih = document.getElementById('v-entry-date').value;
    const tip = document.getElementById('v-entry-type')?.value || 'MAHSUP';
    const aciklama = document.getElementById('v-entry-desc').value.trim();

    if (!no || !tarih) {
        showToast('Fiş numarası ve tarihi zorunludur.', 'error');
        return;
    }

    const rows = [];
    document.querySelectorAll('#v-entry-tbody .v-entry-row').forEach(r => {
        const hkod = r.querySelector('.v-input-acc-val')?.value.trim();
        const desc = r.querySelector('.v-input-desc')?.value.trim();
        const b = parseFloat(r.querySelector('.v-input-borc')?.value || 0);
        const a = parseFloat(r.querySelector('.v-input-alacak')?.value || 0);
        if (hkod && (b > 0 || a > 0)) {
            rows.push({ hesap_kod: hkod, aciklama: desc, borc: b, alacak: a });
        }
    });

    if (rows.length < 2) {
        showToast('En az 2 geçerli satır girilmelidir.', 'error');
        return;
    }

    try {
        const res = await fetch('/api/vouchers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ no, tarih, tip, aciklama, rows })
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Fiş kaydedilemedi.', 'error');
            return;
        }

        showToast(data.message || 'Yevmiye Fişi başarıyla kaydedildi.', 'success');
        hideModal('modal-voucher-entry');
        if (typeof loadYevmiye === 'function') loadYevmiye();
    } catch(e) {
        console.error(e);
        showToast('Sunucu bağlantı hatası.', 'error');
    }
}

// ================= TAM SAYFA YEVMİYE FİŞİ GİRİŞİ =================
let currentVoucherPageType = 'MAHSUP';

function setVoucherPageType(type) {
    currentVoucherPageType = type;
    document.querySelectorAll('.v-page-type-btn').forEach(btn => {
        if (btn.dataset.type === type) {
            btn.className = "v-page-type-btn flex-1 py-1 rounded-lg font-bold text-[11px] bg-white text-slate-800 shadow-xs text-center";
        } else {
            btn.className = "v-page-type-btn flex-1 py-1 rounded-lg font-bold text-[11px] text-slate-600 hover:text-slate-900 text-center";
        }
    });
}

function openVoucherEntryPage() {
    switchTab('voucher_entry');
}

async function initVoucherEntryPage() {
    try {
        const res = await fetch('/api/vouchers/next-no');
        const data = await res.json();
        const noEl = document.getElementById('v-page-no');
        if (noEl) noEl.value = data.next_no || 1;
    } catch (e) {
        const noEl = document.getElementById('v-page-no');
        if (noEl) noEl.value = 1;
    }

    const today = (activeSession && activeSession.tarih) ? activeSession.tarih : new Date().toISOString().split('T')[0];
    const dateEl = document.getElementById('v-page-date');
    if (dateEl) dateEl.value = today;
    setVoucherPageType('MAHSUP');

    if (typeof loadAccounts === 'function') await loadAccounts();
    await loadVoucherDescriptions();
    attachDescriptionAutocomplete(document.getElementById('v-page-desc'));

    const tbody = document.getElementById('v-page-tbody');
    if (tbody && tbody.children.length === 0) {
        addVoucherPageRow();
    }
    calculateVoucherPageTotals();
}

function addVoucherPageRow(defaultKod = '', defaultAd = '', defaultDesc = '', defaultBorc = '', defaultAlacak = '') {
    const tbody = document.getElementById('v-page-tbody');
    if (!tbody) return;
    const rowIdx = tbody.children.length + 1;

    const tr = document.createElement('tr');
    tr.className = 'hover:bg-slate-50/80 transition-colors v-page-row';

    tr.innerHTML = `
        <td class="py-2.5 px-3 text-center font-mono text-slate-400 font-semibold v-page-row-idx">${rowIdx}</td>
        <td class="py-1.5 px-2">
            <div class="relative">
                <input type="text" placeholder="Hesap ara (Örn: 100 veya Kasa)..." autocomplete="off" class="v-acc-search w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-slate-800 outline-none focus:ring-1 focus:ring-amber-500">
                <input type="hidden" class="v-acc-val" value="${defaultKod}">
            </div>
        </td>
        <td class="py-1.5 px-2">
            <div class="relative">
                <input type="text" value="${defaultDesc}" placeholder="Satır açıklaması" autocomplete="off" class="v-desc-search w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs outline-none focus:ring-1 focus:ring-amber-500">
            </div>
        </td>
        <td class="py-1.5 px-2 text-right">
            <input type="number" step="0.01" min="0" value="${defaultBorc}" placeholder="0.00" oninput="onVoucherPageAmountInput(this, 'borc')" class="v-page-borc w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-mono font-bold text-slate-900 text-right outline-none focus:ring-1 focus:ring-amber-500">
        </td>
        <td class="py-1.5 px-2 text-right">
            <input type="number" step="0.01" min="0" value="${defaultAlacak}" placeholder="0.00" oninput="onVoucherPageAmountInput(this, 'alacak')" class="v-page-alacak w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-mono font-bold text-slate-900 text-right outline-none focus:ring-1 focus:ring-amber-500">
        </td>
        <td class="py-1.5 px-2 text-center">
            <button type="button" onclick="removeVoucherPageRow(this)" title="Satırı Sil" class="text-slate-400 hover:text-rose-600 p-1.5 rounded transition-colors">
                <i class="fa-solid fa-trash-can"></i>
            </button>
        </td>
    `;

    tbody.appendChild(tr);

    const searchInp = tr.querySelector('.v-acc-search');
    const valInp = tr.querySelector('.v-acc-val');
    const descInp = tr.querySelector('.v-desc-search');
    const alacakInp = tr.querySelector('.v-page-alacak');

    if (defaultKod) {
        searchInp.value = defaultAd ? `${defaultKod} - ${defaultAd}` : defaultKod;
    }

    attachAccountAutocomplete(searchInp, valInp, () => {
        descInp.focus();
    });

    attachDescriptionAutocomplete(descInp, () => {
        const borcInp = tr.querySelector('.v-page-borc');
        if (borcInp) borcInp.focus();
    });

    alacakInp.addEventListener('keydown', function(e) {
        if (e.key === 'Tab' && !e.shiftKey) {
            const allRows = document.querySelectorAll('#v-page-tbody .v-page-row');
            if (allRows[allRows.length - 1] === tr) {
                e.preventDefault();
                addVoucherPageRow();
                const newRows = document.querySelectorAll('#v-page-tbody .v-page-row');
                const lastSearch = newRows[newRows.length - 1].querySelector('.v-acc-search');
                if (lastSearch) lastSearch.focus();
            }
        }
    });

    reindexVoucherPageRows();
    calculateVoucherPageTotals();
}

function onVoucherPageAmountInput(inputEl, type) {
    const tr = inputEl.closest('tr');
    const borcInp = tr.querySelector('.v-page-borc');
    const alacakInp = tr.querySelector('.v-page-alacak');

    const val = parseFloat(inputEl.value || 0);
    if (val > 0) {
        if (type === 'borc' && alacakInp.value) alacakInp.value = '';
        if (type === 'alacak' && borcInp.value) borcInp.value = '';
    }
    calculateVoucherPageTotals();
}

function removeVoucherPageRow(btn) {
    const tbody = document.getElementById('v-page-tbody');
    if (tbody.children.length <= 1) {
        showToast('Yevmiye fişinde en az 1 satır bulunmalıdır.', 'info');
        return;
    }
    btn.closest('tr').remove();
    reindexVoucherPageRows();
    calculateVoucherPageTotals();
}

function reindexVoucherPageRows() {
    const rows = document.querySelectorAll('#v-page-tbody .v-page-row');
    rows.forEach((r, idx) => {
        const idxEl = r.querySelector('.v-page-row-idx');
        if (idxEl) idxEl.textContent = idx + 1;
    });
    const cnt = document.getElementById('v-page-row-count');
    if (cnt) cnt.textContent = `${rows.length} Satır`;
}

function calculateVoucherPageTotals() {
    const rows = document.querySelectorAll('#v-page-tbody .v-page-row');
    let totBorc = 0.0;
    let totAlacak = 0.0;

    rows.forEach(r => {
        const b = parseFloat(r.querySelector('.v-page-borc')?.value || 0);
        const a = parseFloat(r.querySelector('.v-page-alacak')?.value || 0);
        if (b > 0) totBorc += b;
        if (a > 0) totAlacak += a;
    });

    totBorc = Math.round(totBorc * 100) / 100;
    totAlacak = Math.round(totAlacak * 100) / 100;
    const diff = Math.round(Math.abs(totBorc - totAlacak) * 100) / 100;

    const bEl = document.getElementById('v-page-sum-borc');
    const aEl = document.getElementById('v-page-sum-alacak');
    if (bEl) bEl.textContent = fmt(totBorc);
    if (aEl) aEl.textContent = fmt(totAlacak);

    const badge = document.getElementById('v-page-balance-badge');
    const saveBtn = document.getElementById('btn-page-save-voucher');
    if (!badge || !saveBtn) return;

    if (totBorc > 0 && diff === 0) {
        badge.className = "px-3 py-1.5 rounded-full font-bold text-xs bg-emerald-100 text-emerald-800 flex items-center gap-1";
        badge.innerHTML = `<i class="fa-solid fa-check"></i> Fiş Dengeli (0.00 ₺)`;
        saveBtn.disabled = false;
    } else {
        badge.className = "px-3 py-1.5 rounded-full font-bold text-xs bg-rose-100 text-rose-800 flex items-center gap-1";
        badge.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Fark: ${fmt(diff)}`;
        saveBtn.disabled = true;
    }
}

function balanceVoucherWithCash() {
    const rows = document.querySelectorAll('#v-page-tbody .v-page-row');
    let totBorc = 0.0;
    let totAlacak = 0.0;

    rows.forEach(r => {
        const b = parseFloat(r.querySelector('.v-page-borc')?.value || 0);
        const a = parseFloat(r.querySelector('.v-page-alacak')?.value || 0);
        if (b > 0) totBorc += b;
        if (a > 0) totAlacak += a;
    });

    const diff = Math.round(Math.abs(totBorc - totAlacak) * 100) / 100;
    if (diff <= 0.005) {
        showToast('Fiş zaten dengeli durumda.', 'info');
        return;
    }

    const genelDesc = document.getElementById('v-page-desc').value.trim() || 'Nakit Kasa Denkleştirme';
    if (totBorc > totAlacak) {
        addVoucherPageRow('100.01', 'Merkez TL Kasası', genelDesc, '', diff.toFixed(2));
    } else {
        addVoucherPageRow('100.01', 'Merkez TL Kasası', genelDesc, diff.toFixed(2), '');
    }

    showToast(`Kalan ${fmt(diff)} fark 100.01 Kasaya eklenerek fiş dengelendi.`, 'success');
}

function copyPreviousRowToActive() {
    const activeEl = document.activeElement;
    if (!activeEl) return;
    const tr = activeEl.closest('.v-page-row');
    if (!tr) return;
    const prevTr = tr.previousElementSibling;
    if (!prevTr || !prevTr.classList.contains('v-page-row')) {
        showToast('Kopyalanacak üst satır bulunamadı.', 'info');
        return;
    }

    const prevAccKod = prevTr.querySelector('.v-acc-val')?.value || '';
    const prevAccTxt = prevTr.querySelector('.v-acc-search')?.value || '';
    const prevDesc = prevTr.querySelector('.v-desc-search')?.value || '';

    tr.querySelector('.v-acc-val').value = prevAccKod;
    tr.querySelector('.v-acc-search').value = prevAccTxt;
    tr.querySelector('.v-desc-search').value = prevDesc;

    showToast('Üst satırdaki hesap ve açıklama kopyalandı.', 'info');
}

document.addEventListener('keydown', function(e) {
    if (typeof activeTab !== 'undefined' && activeTab !== 'voucher_entry') return;

    if ((e.ctrlKey || e.metaKey) && (e.key.toLowerCase() === 'k' || e.key.toLowerCase() === 'b')) {
        e.preventDefault();
        balanceVoucherWithCash();
    } else if ((e.ctrlKey || e.metaKey) && (e.key.toLowerCase() === 'd' || e.key === "'")) {
        e.preventDefault();
        copyPreviousRowToActive();
    } else if (e.key === 'F2') {
        e.preventDefault();
        addVoucherPageRow();
        const rows = document.querySelectorAll('#v-page-tbody .v-page-row');
        const lastSearch = rows[rows.length - 1].querySelector('.v-acc-search');
        if (lastSearch) lastSearch.focus();
    } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        const saveBtn = document.getElementById('btn-page-save-voucher');
        if (saveBtn && !saveBtn.disabled) {
            submitVoucherPage();
        }
    }
});

async function submitVoucherPage() {
    const no = document.getElementById('v-page-no').value;
    const tarih = document.getElementById('v-page-date').value;
    const desc = document.getElementById('v-page-desc').value.trim();
    const rows = [];

    document.querySelectorAll('#v-page-tbody .v-page-row').forEach(tr => {
        const hkod = tr.querySelector('.v-acc-val')?.value.trim();
        const s_desc = tr.querySelector('.v-desc-search')?.value.trim();
        const b = parseFloat(tr.querySelector('.v-page-borc')?.value || 0);
        const a = parseFloat(tr.querySelector('.v-page-alacak')?.value || 0);
        if (hkod && (b > 0 || a > 0)) {
            rows.push({ hesap_kod: hkod, aciklama: s_desc, borc: b, alacak: a });
        }
    });

    if (rows.length < 2) {
        showToast('En az 2 geçerli satır girilmelidir.', 'error');
        return;
    }

    try {
        const res = await fetch('/api/vouchers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ no, tarih, tip: currentVoucherPageType, aciklama: desc, rows })
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Fiş kaydedilemedi.', 'error');
            return;
        }

        showToast(data.message || 'Yevmiye Fişi başarıyla kaydedildi.', 'success');
        clearVoucherEntryPage();
        switchTab('yevmiye');
    } catch(e) {
        console.error(e);
        showToast('Sunucu hatası oluştu.', 'error');
    }
}

function clearVoucherEntryPage() {
    const descEl = document.getElementById('v-page-desc');
    if (descEl) descEl.value = '';
    const tbody = document.getElementById('v-page-tbody');
    if (tbody) tbody.innerHTML = '';
    initVoucherEntryPage();
}
