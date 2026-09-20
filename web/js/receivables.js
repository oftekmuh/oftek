/**
 * oftek - Müşteri Alacakları ve Çift Modlu Tahsilat Modülü (receivables.js)
 */

let selectedCategoryFilter = '';
let currentCollectMode = 'FIFO';
let currentCustomerOpenReceivables = [];

async function loadReceivables() {
    try {
        const yil = typeof currentPeriodYear !== 'undefined' ? currentPeriodYear : new Date().getFullYear().toString();
        const ay = typeof currentPeriodMonth !== 'undefined' ? currentPeriodMonth : '';
        let url = `/api/receivables?yil=${yil}`;
        if (ay) url += `&ay=${ay}`;
        if (selectedCategoryFilter) url += `&kategori=${encodeURIComponent(selectedCategoryFilter)}`;

        const res = await fetch(url);
        const rows = await res.json();
        const tbody = document.getElementById('receivables-table-body');
        if (!tbody) return;

        if (!rows || rows.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="py-6 text-center text-slate-400">Kayıtlı alacak bulunamadı.</td></tr>';
            return;
        }
        tbody.innerHTML = rows.map(a => `
            <tr class="hover:bg-slate-50/80">
                <td class="py-3 px-4 font-semibold text-slate-900">${a.cari_unvan}</td>
                <td class="py-3 px-4"><span class="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-blue-50 text-blue-700">${a.kategori}</span></td>
                <td class="py-3 px-4 font-mono text-slate-500">${a.belge_no || '-'}</td>
                <td class="py-3 px-4 text-slate-600">${a.tarih} ${a.vade_tarihi ? `<span class="text-[10px] text-amber-500">(Vade: ${a.vade_tarihi})</span>` : ''}</td>
                <td class="py-3 px-4 text-right font-mono text-slate-800">${fmt(a.toplam_tutar)}</td>
                <td class="py-3 px-4 text-right font-mono text-emerald-600">${fmt(a.tahsil_edilen)}</td>
                <td class="py-3 px-4 text-right font-mono font-bold text-blue-600">${fmt(a.kalan_tutar)}</td>
                <td class="py-3 px-4 text-center">
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold ${a.durum === 'KAPANDI' ? 'bg-emerald-50 text-emerald-700' : a.durum === 'KISMI' ? 'bg-amber-50 text-amber-700' : 'bg-blue-50 text-blue-700'}">${a.durum}</span>
                </td>
            </tr>
        `).join('');
    } catch(e) {
        console.error("Alacaklar yüklenemedi:", e);
    }
}

function filterReceivableCategory(cat) {
    selectedCategoryFilter = cat;
    document.querySelectorAll('.cat-pill').forEach(btn => {
        btn.className = 'cat-pill px-3 py-1 rounded-lg bg-white border border-slate-200 text-slate-700 font-medium';
    });
    if (event && event.target) {
        event.target.className = 'cat-pill active px-3 py-1 rounded-lg bg-brand-600 text-white font-medium';
    }
    loadReceivables();
}

async function showAddReceivableModal() {
    if (typeof activeSession === 'undefined' || !activeSession) {
        showToast('Alacak kaydetmek için açık bir gün oturumu gereklidir.', 'error');
        return;
    }
    const searchInp = document.getElementById('rec-cari-search');
    const hiddenId = document.getElementById('rec-cari-id');
    if (searchInp) searchInp.value = '';
    if (hiddenId) hiddenId.value = '';
    showModal('modal-add-receivable');
}

async function submitAddReceivable(e) {
    if (e) e.preventDefault();
    const cari_id = document.getElementById('rec-cari-id').value;
    const kategori = document.getElementById('rec-kategori').value;
    const belge_no = document.getElementById('rec-doc-no').value.trim();
    const vade_tarihi = document.getElementById('rec-due-date').value;
    const toplam_tutar = parseFloat(document.getElementById('rec-amount').value || 0);
    const aciklama = document.getElementById('rec-desc').value.trim();

    if (!cari_id) {
        showToast('Lütfen listeden geçerli bir müşteri seçiniz.', 'error');
        return;
    }
    if (toplam_tutar <= 0) {
        showToast('Geçerli bir alacak tutarı giriniz.', 'error');
        return;
    }

    const res = await fetch('/api/receivables', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gun_id: activeSession.id, cari_id, kategori, belge_no, vade_tarihi, toplam_tutar, aciklama })
    });
    if (res.ok) {
        showToast('Alacak başarıyla kaydedildi.', 'success');
        hideModal('modal-add-receivable');
        loadReceivables();
    } else {
        showToast('Hata oluştu.', 'error');
    }
}

// Çift Modlu Tahsilat Modalı
async function showCollectModal() {
    if (typeof activeSession === 'undefined' || !activeSession) {
        showToast('Tahsilat alabilmek için açık bir gün oturumu gereklidir.', 'error');
        return;
    }
    const searchInp = document.getElementById('collect-cari-search');
    const hiddenId = document.getElementById('collect-cari-id');
    if (searchInp) searchInp.value = '';
    if (hiddenId) hiddenId.value = '';
    setCollectMode('FIFO');
    document.getElementById('collect-amount').value = '';
    document.getElementById('selective-invoices-list').innerHTML = '<div class="text-slate-400 text-center py-4">Önce müşteri seçiniz.</div>';
    showModal('modal-collect');
}

function setCollectMode(mode) {
    currentCollectMode = mode;
    const btnFifo = document.getElementById('tab-btn-fifo');
    const btnSecimli = document.getElementById('tab-btn-secimli');
    const boxFifo = document.getElementById('collect-mode-fifo-box');
    const boxSecimli = document.getElementById('collect-mode-secimli-box');

    if (!btnFifo || !btnSecimli) return;

    if (mode === 'FIFO') {
        btnFifo.className = "py-2 px-4 border-b-2 border-brand-600 text-brand-700 font-bold";
        btnSecimli.className = "py-2 px-4 border-b-2 border-transparent text-slate-500 hover:text-slate-800 font-semibold";
        if (boxFifo) boxFifo.classList.remove('hidden');
        if (boxSecimli) boxSecimli.classList.add('hidden');
    } else {
        btnSecimli.className = "py-2 px-4 border-b-2 border-brand-600 text-brand-700 font-bold";
        btnFifo.className = "py-2 px-4 border-b-2 border-transparent text-slate-500 hover:text-slate-800 font-semibold";
        if (boxFifo) boxFifo.classList.add('hidden');
        if (boxSecimli) boxSecimli.classList.remove('hidden');
        updateSelectiveCounter();
    }
}

async function onCollectCariChange(c) {
    const cariId = c ? c.id : document.getElementById('collect-cari-id').value;
    if (!cariId) return;

    const res = await fetch(`/api/receivables?cari_id=${cariId}&durum=ACIK`);
    currentCustomerOpenReceivables = await res.json();

    const container = document.getElementById('selective-invoices-list');
    if (!container) return;

    if (currentCustomerOpenReceivables.length === 0) {
        container.innerHTML = '<div class="text-slate-400 text-center py-4">Bu müşterinin açık faturası bulunmuyor.</div>';
        return;
    }

    container.innerHTML = currentCustomerOpenReceivables.map(inv => `
        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
            <div class="flex items-center justify-between">
                <span class="font-bold text-slate-800">${inv.belge_no || 'Belgesiz'} (${inv.kategori})</span>
                <span class="text-slate-500 text-[11px]">${inv.tarih}</span>
            </div>
            <div class="flex items-center justify-between text-[11px]">
                <span>Toplam: <b>${fmt(inv.toplam_tutar)}</b></span>
                <span>Açık Kalan: <b class="text-rose-600">${fmt(inv.kalan_tutar)}</b></span>
            </div>
            <div class="flex items-center gap-2 pt-1">
                <span class="text-[11px] font-semibold text-slate-600">Bu Faturaya Dağıt:</span>
                <input type="number" step="0.01" min="0" max="${inv.kalan_tutar}" data-inv-id="${inv.id}" oninput="updateSelectiveCounter()" placeholder="0.00" class="secimli-input flex-1 bg-white border border-slate-200 rounded-lg px-2 py-1 text-xs font-bold text-emerald-600 outline-none focus:ring-1 focus:ring-brand-500">
                <button type="button" onclick="fillFullInvoice(${inv.id}, ${inv.kalan_tutar})" class="px-2 py-1 bg-slate-200 hover:bg-slate-300 rounded text-[10px] font-semibold text-slate-700">Tümü</button>
            </div>
        </div>
    `).join('');

    updateSelectiveCounter();
}

function fillFullInvoice(invId, kalan) {
    const input = document.querySelector(`.secimli-input[data-inv-id="${invId}"]`);
    if (input) {
        input.value = kalan;
        updateSelectiveCounter();
    }
}

function onCollectAmountInput() {
    updateSelectiveCounter();
}

function updateSelectiveCounter() {
    const totalAmount = parseFloat(document.getElementById('collect-amount').value || 0);
    let allocated = 0;
    document.querySelectorAll('.secimli-input').forEach(inp => {
        allocated += parseFloat(inp.value || 0);
    });
    const diff = totalAmount - allocated;
    const counter = document.getElementById('selective-counter');
    if (!counter) return;

    if (diff === 0 && totalAmount > 0) {
        counter.className = "text-emerald-600 font-bold";
        counter.textContent = "✓ Tam Eşleşti (Kalan: 0.00 ₺)";
    } else if (diff < 0) {
        counter.className = "text-rose-600 font-bold";
        counter.textContent = `Fazla Dağıtıldı: ${fmt(Math.abs(diff))}`;
    } else {
        counter.className = "text-amber-600 font-bold";
        counter.textContent = `Dağıtılacak Kalan: ${fmt(diff)}`;
    }
}

async function submitCollect() {
    if (typeof activeSession === 'undefined' || !activeSession) return;
    const cari_id = document.getElementById('collect-cari-id').value;
    const kaynak_hesap = document.getElementById('collect-source').value;
    const tutar = parseFloat(document.getElementById('collect-amount').value || 0);

    if (!cari_id || tutar <= 0) {
        showToast('Lütfen geçerli müşteri ve pozitif tahsilat tutarı giriniz.', 'error');
        return;
    }

    let secimler = [];
    if (currentCollectMode === 'SECIMLI') {
        let allocated = 0;
        document.querySelectorAll('.secimli-input').forEach(inp => {
            const val = parseFloat(inp.value || 0);
            if (val > 0) {
                allocated += val;
                secimler.push({ alacak_id: parseInt(inp.dataset.invId), tutar: val });
            }
        });
        if (Math.abs(allocated - tutar) > 0.01) {
            showToast(`Dağıtılan tutar (${fmt(allocated)}) toplam tahsilata (${fmt(tutar)}) eşit olmalıdır!`, 'error');
            return;
        }
    }

    const res = await fetch('/api/receivables/collect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            gun_id: activeSession.id,
            cari_id: parseInt(cari_id),
            tutar,
            kaynak_hesap,
            mod: currentCollectMode,
            secimler,
            aciklama: `Müşteri Tahsilatı (${currentCollectMode} Modu)`
        })
    });
    const data = await res.json();
    if (res.ok) {
        showToast(`Tahsilat başarıyla tamamlandı (${currentCollectMode}).`, 'success');
        hideModal('modal-collect');
        loadReceivables();
        if (typeof loadDashboard === 'function') loadDashboard();
    } else {
        showToast(data.error || 'Tahsilat gerçekleştirilemedi.', 'error');
    }
}
