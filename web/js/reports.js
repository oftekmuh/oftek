/**
 * oftek - Merkezi Raporlar & Canlı Analiz Modülü
 * Hızlı dönem filtreleri (Bugün, Bu Hafta, Bu Ay, Bu Yıl), serbest tarih aralığı,
 * anlık istemci tarafı filtreleme, 5 alt sekme (Muavin Defteri dahil),
 * sayfa içi yevmiye fişi inceleme modalı ve Excel (.xlsx) dışa aktarımı.
 */

let activeReportTab = 'cash_flow';
let reportYear = '2026';
let reportStartDate = '';
let reportEndDate = '';
let reportCashAccount = '';
let reportCariTip = '';
let reportCariOnlyBalance = false;
let reportMuavinAccount = '100';
let currentReportData = null;
let currentSearchQuery = '';

// ================= SEKME & DÖNEM YÖNETİMİ =================

function setReportSubTab(tab) {
    activeReportTab = tab;
    document.querySelectorAll('.report-subtab-btn').forEach(btn => {
        if (btn.dataset.tab === tab) {
            btn.className = "report-subtab-btn px-3.5 py-1.5 rounded-xl text-xs font-bold bg-white text-slate-800 shadow-xs border border-slate-200/80 transition-all";
        } else {
            btn.className = "report-subtab-btn px-3.5 py-1.5 rounded-xl text-xs font-semibold text-slate-600 hover:text-slate-900 transition-all";
        }
    });

    const panels = ['cash_flow', 'balances', 'payroll', 'mizan', 'muavin'];
    panels.forEach(p => {
        const el = document.getElementById(`report-panel-${p}`);
        if (el) {
            if (p === tab) el.classList.remove('hidden');
            else el.classList.add('hidden');
        }
    });

    // Arama kutusunu temizle
    const searchInput = document.getElementById('rep-instant-search');
    if (searchInput) searchInput.value = '';
    currentSearchQuery = '';

    loadCurrentReport();
}

function setReportYear(yr, btn) {
    reportYear = yr;
    if (btn && btn.parentElement) {
        btn.parentElement.querySelectorAll('button').forEach(b => {
            b.className = "rep-yr-btn px-3 py-1 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900";
        });
        btn.className = "rep-yr-btn px-3 py-1 rounded-lg text-xs font-bold bg-white text-slate-800 shadow-xs";
    }
    loadCurrentReport();
}

function setReportQuickPeriod(period, btn) {
    const today = new Date();
    const pad = n => String(n).padStart(2, '0');
    const toISO = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

    if (btn && btn.parentElement) {
        btn.parentElement.querySelectorAll('.rep-quick-period-btn').forEach(b => {
            b.className = "rep-quick-period-btn px-2.5 py-1 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-200/60";
        });
        btn.className = "rep-quick-period-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-white text-slate-800 shadow-xs";
    }

    if (period === 'today') {
        reportStartDate = toISO(today);
        reportEndDate = toISO(today);
    } else if (period === 'week') {
        const day = today.getDay() || 7;
        const mon = new Date(today);
        mon.setDate(today.getDate() - day + 1);
        const sun = new Date(mon);
        sun.setDate(mon.getDate() + 6);
        reportStartDate = toISO(mon);
        reportEndDate = toISO(sun);
    } else if (period === 'month') {
        const first = new Date(today.getFullYear(), today.getMonth(), 1);
        const last = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        reportStartDate = toISO(first);
        reportEndDate = toISO(last);
    } else if (period === 'year') {
        reportStartDate = `${reportYear}-01-01`;
        reportEndDate = `${reportYear}-12-31`;
    } else if (period === 'all') {
        reportStartDate = '';
        reportEndDate = '';
    }

    const startInp = document.getElementById('rep-start-date');
    const endInp = document.getElementById('rep-end-date');
    if (startInp) startInp.value = reportStartDate;
    if (endInp) endInp.value = reportEndDate;

    loadCurrentReport();
}

function applyReportDateRange() {
    const startInp = document.getElementById('rep-start-date');
    const endInp = document.getElementById('rep-end-date');
    reportStartDate = startInp ? startInp.value : '';
    reportEndDate = endInp ? endInp.value : '';

    document.querySelectorAll('.rep-quick-period-btn').forEach(b => {
        b.className = "rep-quick-period-btn px-2.5 py-1 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-200/60";
    });

    loadCurrentReport();
}

function clearReportDateRange() {
    reportStartDate = '';
    reportEndDate = '';
    const startInp = document.getElementById('rep-start-date');
    const endInp = document.getElementById('rep-end-date');
    if (startInp) startInp.value = '';
    if (endInp) endInp.value = '';

    document.querySelectorAll('.rep-quick-period-btn').forEach(b => {
        b.className = "rep-quick-period-btn px-2.5 py-1 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-200/60";
        if (b.textContent.trim() === 'Tümü') {
            b.className = "rep-quick-period-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-white text-slate-800 shadow-xs";
        }
    });

    loadCurrentReport();
}

async function loadCurrentReport() {
    if (activeReportTab === 'cash_flow') {
        await loadCashFlowReport();
    } else if (activeReportTab === 'balances') {
        await loadBalancesReport();
    } else if (activeReportTab === 'payroll') {
        await loadPayrollReport();
    } else if (activeReportTab === 'mizan') {
        await loadReportMizan();
    } else if (activeReportTab === 'muavin') {
        await loadReportMuavin(reportMuavinAccount);
    }
}

// ================= 1. KASA & NAKİT AKIŞ RAPORU =================

function setCashFlowAccountFilter(acc, btn) {
    reportCashAccount = acc;
    if (btn && btn.parentElement) {
        btn.parentElement.querySelectorAll('.rep-cf-acc-btn').forEach(b => {
            b.className = "rep-cf-acc-btn px-3 py-1 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100";
        });
        btn.className = "rep-cf-acc-btn px-3 py-1 rounded-lg text-xs font-bold bg-slate-800 text-white shadow-xs";
    }
    loadCashFlowReport();
}

async function loadCashFlowReport() {
    try {
        let url = `/api/reports/cash-flow?yil=${reportYear}`;
        if (reportStartDate) url += `&start=${reportStartDate}`;
        if (reportEndDate) url += `&end=${reportEndDate}`;
        if (reportCashAccount) url += `&hesap=${reportCashAccount}`;

        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();
        currentReportData = { type: 'cash_flow', raw: data, rows: data.hareketler || [] };

        renderCashFlowRows(currentReportData.rows);
    } catch (e) {
        console.error('Kasa raporu yüklenemedi:', e);
    }
}

function renderCashFlowRows(rows) {
    const tbody = document.getElementById('rep-cash-table-body');
    const countEl = document.getElementById('rep-cash-count');
    if (countEl) countEl.textContent = `${rows.length} kayıt listeleniyor`;

    let totGiris = 0;
    let totCikis = 0;

    if (!tbody) return;

    if (rows.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="py-8 text-center text-slate-400 text-xs font-medium">Seçilen filtre ve kriterlere uygun hareket bulunamadı.</td></tr>';
        updateCashFlowSummaries(0, 0);
        return;
    }

    tbody.innerHTML = rows.map(r => {
        const isGiris = (r.yon === 'GIRIS' || r.borc > 0);
        const tutar = isGiris ? (r.borc || r.tutar || 0) : (r.alacak || r.tutar || 0);
        if (isGiris) totGiris += tutar;
        else totCikis += tutar;

        const displayName = r.cari_unvan || r.personel_ad || r.hesap_adi || '-';
        const displayCode = r.kaynak_hesap || r.hesap_kod || '-';

        return `
            <tr class="hover:bg-slate-50/80 transition-colors">
                <td class="py-2.5 px-4 font-medium text-slate-600">${r.tarih || '-'}</td>
                <td class="py-2.5 px-4 font-mono font-bold text-teal-700">${displayCode}</td>
                <td class="py-2.5 px-4 text-slate-800 font-semibold">${displayName}</td>
                <td class="py-2.5 px-4 text-slate-600">${r.aciklama || '-'}</td>
                <td class="py-2.5 px-4 text-right font-mono font-bold ${isGiris ? 'text-emerald-600' : 'text-slate-300'}">
                    ${isGiris ? fmt(tutar) : '-'}
                </td>
                <td class="py-2.5 px-4 text-right font-mono font-bold ${!isGiris ? 'text-rose-600' : 'text-slate-300'}">
                    ${!isGiris ? fmt(tutar) : '-'}
                </td>
            </tr>
        `;
    }).join('');

    updateCashFlowSummaries(totGiris, totCikis);
}

function updateCashFlowSummaries(inVal, outVal) {
    const sumInEl = document.getElementById('rep-cash-in');
    const sumOutEl = document.getElementById('rep-cash-out');
    const sumNetEl = document.getElementById('rep-cash-net');
    if (sumInEl) sumInEl.textContent = fmt(inVal);
    if (sumOutEl) sumOutEl.textContent = fmt(outVal);
    if (sumNetEl) sumNetEl.textContent = fmt(inVal - outVal);
}

// ================= 2. CARİ BAKİYELER RAPORU =================

function setCariReportFilter(tip, btn) {
    reportCariTip = tip;
    if (btn && btn.parentElement) {
        btn.parentElement.querySelectorAll('.rep-cari-tip-btn').forEach(b => {
            b.className = "rep-cari-tip-btn px-3 py-1 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100";
        });
        btn.className = "rep-cari-tip-btn px-3 py-1 rounded-lg text-xs font-bold bg-slate-800 text-white shadow-xs";
    }
    loadBalancesReport();
}

function toggleCariOnlyWithBalance() {
    reportCariOnlyBalance = !reportCariOnlyBalance;
    const btn = document.getElementById('rep-cari-bakiye-toggle');
    if (btn) {
        if (reportCariOnlyBalance) {
            btn.className = "px-3 py-1.5 rounded-xl border border-teal-500 bg-teal-50 text-xs font-bold text-teal-800 shadow-xs flex items-center gap-1.5";
        } else {
            btn.className = "px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 shadow-xs flex items-center gap-1.5";
        }
    }
    loadBalancesReport();
}

async function loadBalancesReport() {
    try {
        let url = `/api/reports/balances?tip=${reportCariTip}`;
        if (reportCariOnlyBalance) url += `&sadece_bakiyeli=1`;

        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();
        currentReportData = { type: 'balances', raw: data, rows: data.cariler || [] };

        renderBalancesRows(currentReportData.rows);
    } catch (e) {
        console.error('Cari bakiyeler yüklenemedi:', e);
    }
}

function renderBalancesRows(rows) {
    const tbody = document.getElementById('rep-balances-table-body');
    const countEl = document.getElementById('rep-balances-count');
    if (countEl) countEl.textContent = `${rows.length} cari listeleniyor`;

    let totAlacak = 0;
    let totBorc = 0;

    if (!tbody) return;

    if (rows.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="py-8 text-center text-slate-400 text-xs font-medium">Kayıtlı cari bakiye bulunamadı.</td></tr>';
        updateBalancesSummaries(0, 0);
        return;
    }

    tbody.innerHTML = rows.map(c => {
        totAlacak += (c.toplam_alacak || 0);
        totBorc += (c.toplam_borc || 0);
        const bakiye = c.bakiye || 0;

        return `
            <tr class="hover:bg-slate-50/80 transition-colors">
                <td class="py-2.5 px-4 font-semibold text-slate-900">${c.unvan}</td>
                <td class="py-2.5 px-4">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${c.tip === 'MUSTERI' ? 'bg-blue-50 text-blue-700' : 'bg-amber-50 text-amber-700'}">
                        ${c.tip === 'MUSTERI' ? 'Müşteri / Kurum' : 'Tedarikçi / Firma'}
                    </span>
                </td>
                <td class="py-2.5 px-4 text-right font-mono font-bold text-slate-700">${fmt(c.toplam_borc)}</td>
                <td class="py-2.5 px-4 text-right font-mono font-bold text-slate-700">${fmt(c.toplam_alacak)}</td>
                <td class="py-2.5 px-4 text-right font-mono font-bold ${bakiye > 0 ? 'text-emerald-600' : (bakiye < 0 ? 'text-rose-600' : 'text-slate-400')}">
                    ${fmt(Math.abs(bakiye))} ${bakiye >= 0 ? '(A)' : '(B)'}
                </td>
                <td class="py-2.5 px-4 text-center text-slate-500 text-xs font-medium">${c.telefon || '-'}</td>
            </tr>
        `;
    }).join('');

    updateBalancesSummaries(totAlacak, totBorc);
}

function updateBalancesSummaries(alacak, borc) {
    const sumAlacak = document.getElementById('rep-bal-alacak');
    const sumBorc = document.getElementById('rep-bal-borc');
    const sumNet = document.getElementById('rep-bal-net');
    if (sumAlacak) sumAlacak.textContent = fmt(alacak);
    if (sumBorc) sumBorc.textContent = fmt(borc);
    if (sumNet) sumNet.textContent = fmt(alacak - borc);
}

// ================= 3. PERSONEL BORDRO / HAKEDİŞ RAPORU =================

async function loadPayrollReport() {
    try {
        let url = `/api/reports/payroll?yil=${reportYear}`;
        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();
        currentReportData = { type: 'payroll', raw: data, rows: data.personeller || [] };

        renderPayrollRows(currentReportData.rows);
    } catch (e) {
        console.error('Bordro raporu yüklenemedi:', e);
    }
}

function renderPayrollRows(rows) {
    const tbody = document.getElementById('rep-payroll-table-body');
    let totHak = 0;
    let totOde = 0;

    if (!tbody) return;

    if (rows.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="py-8 text-center text-slate-400 text-xs font-medium">Bordro kaydı bulunamadı.</td></tr>';
        updatePayrollSummaries(0, 0);
        return;
    }

    tbody.innerHTML = rows.map(p => {
        totHak += (p.toplam_hakedis || 0);
        totOde += (p.toplam_odenen || 0);
        return `
            <tr class="hover:bg-slate-50/80 transition-colors">
                <td class="py-2.5 px-4 font-semibold text-slate-900">${p.ad_soyad}</td>
                <td class="py-2.5 px-4 text-slate-600 text-xs">${p.gorev || '-'}</td>
                <td class="py-2.5 px-4 text-right font-mono font-bold text-indigo-700">${fmt(p.toplam_hakedis)}</td>
                <td class="py-2.5 px-4 text-right font-mono font-bold text-emerald-600">${fmt(p.toplam_odenen)}</td>
                <td class="py-2.5 px-4 text-right font-mono font-bold ${p.kalan_bakiye > 0 ? 'text-rose-600' : 'text-slate-400'}">
                    ${fmt(p.kalan_bakiye)}
                </td>
            </tr>
        `;
    }).join('');

    updatePayrollSummaries(totHak, totOde);
}

function updatePayrollSummaries(hak, ode) {
    const sumHak = document.getElementById('rep-pay-hakedis');
    const sumOde = document.getElementById('rep-pay-odeme');
    const sumKal = document.getElementById('rep-pay-kalan');
    if (sumHak) sumHak.textContent = fmt(hak);
    if (sumOde) sumOde.textContent = fmt(ode);
    if (sumKal) sumKal.textContent = fmt(Math.max(0, hak - ode));
}

// ================= 4. MİZAN RAPORU =================

async function loadReportMizan() {
    try {
        const res = await fetch('/api/mizan');
        if (!res.ok) return;
        const rows = await res.json();
        currentReportData = { type: 'mizan', raw: rows, rows: rows };

        renderMizanRows(currentReportData.rows);
    } catch (e) {
        console.error('Mizan raporu yüklenemedi:', e);
    }
}

function renderMizanRows(rows) {
    const tbody = document.getElementById('rep-mizan-table-body');
    if (!tbody) return;

    if (rows.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="py-8 text-center text-slate-400 text-xs font-medium">Mizan kaydı bulunamadı.</td></tr>';
        updateMizanSummaries(0, 0);
        return;
    }

    let totalBorc = 0;
    let totalAlacak = 0;

    tbody.innerHTML = rows.map(r => {
        totalBorc += (r.tot_borc || 0);
        totalAlacak += (r.tot_alacak || 0);
        const bakiyeB = r.tot_borc > r.tot_alacak ? r.tot_borc - r.tot_alacak : 0;
        const bakiyeA = r.tot_alacak > r.tot_borc ? r.tot_alacak - r.tot_borc : 0;
        return `
            <tr class="hover:bg-slate-50 font-mono text-xs">
                <td class="py-2.5 px-4 font-bold text-teal-700">${r.kod}</td>
                <td class="py-2.5 px-4 font-sans text-slate-800 font-medium">${r.ad}</td>
                <td class="py-2.5 px-4 text-right">${fmt(r.tot_borc)}</td>
                <td class="py-2.5 px-4 text-right">${fmt(r.tot_alacak)}</td>
                <td class="py-2.5 px-4 text-right text-emerald-600 font-bold">${bakiyeB > 0 ? fmt(bakiyeB) : '-'}</td>
                <td class="py-2.5 px-4 text-right text-rose-600 font-bold">${bakiyeA > 0 ? fmt(bakiyeA) : '-'}</td>
                <td class="py-2.5 px-4 text-center">
                    <button type="button" onclick="openMuavinForAccount('${r.kod}')" class="px-2 py-1 rounded bg-teal-50 text-teal-700 hover:bg-teal-100 text-[10px] font-bold" title="Muavin Defterini İncele">
                        <i class="fa-solid fa-book-open"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');

    updateMizanSummaries(totalBorc, totalAlacak);
}

function updateMizanSummaries(borc, alacak) {
    const sumB = document.getElementById('rep-mizan-sum-borc');
    const sumA = document.getElementById('rep-mizan-sum-alacak');
    if (sumB) sumB.textContent = fmt(borc);
    if (sumA) sumA.textContent = fmt(alacak);
}

// ================= 5. MUAVİN DEFTERİ (HESAP EKSTRESİ & YÜRÜYEN BAKİYE) =================

function selectMuavinAccount(accKod, btn) {
    reportMuavinAccount = accKod;
    document.querySelectorAll('.rep-muavin-btn').forEach(b => {
        b.className = "rep-muavin-btn px-2.5 py-1 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100";
        if (b.textContent.trim().startsWith(accKod)) {
            b.className = "rep-muavin-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-teal-600 text-white shadow-xs";
        }
    });

    const searchInp = document.getElementById('rep-muavin-search-input');
    if (searchInp) searchInp.value = accKod;

    loadReportMuavin(accKod);
}

function submitMuavinSearch() {
    const searchInp = document.getElementById('rep-muavin-search-input');
    const val = searchInp ? searchInp.value.trim() : '';
    if (!val) {
        showToast('Lütfen bir hesap kodu girin.', 'warning');
        return;
    }
    reportMuavinAccount = val;
    loadReportMuavin(val);
}

function openMuavinForAccount(kod) {
    setReportSubTab('muavin');
    selectMuavinAccount(kod);
}

async function loadReportMuavin(accKod) {
    try {
        let url = `/api/muavin?kod=${encodeURIComponent(accKod)}`;
        if (reportStartDate) url += `&start=${reportStartDate}`;
        if (reportEndDate) url += `&end=${reportEndDate}`;

        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();
        currentReportData = { type: 'muavin', raw: data, rows: data.hareketler || [] };

        const hesap = data.hesap || { kod: accKod, ad: 'Belirtilmemiş' };
        const ozet = data.ozet || { toplam_borc: 0, toplam_alacak: 0, bakiye: 0 };

        const titleEl = document.getElementById('rep-muavin-acc-title');
        const sumBorcEl = document.getElementById('rep-muavin-tot-borc');
        const sumAlacakEl = document.getElementById('rep-muavin-tot-alacak');
        const sumBakEl = document.getElementById('rep-muavin-tot-bakiye');

        if (titleEl) titleEl.textContent = `${hesap.kod} - ${hesap.ad || 'İsimsiz Hesap'}`;
        if (sumBorcEl) sumBorcEl.textContent = fmt(ozet.toplam_borc || 0);
        if (sumAlacakEl) sumAlacakEl.textContent = fmt(ozet.toplam_alacak || 0);
        if (sumBakEl) {
            const b = ozet.bakiye || 0;
            sumBakEl.textContent = `${fmt(Math.abs(b))} ${b >= 0 ? '(B)' : '(A)'}`;
            sumBakEl.className = `text-xl font-mono font-bold mt-1 block ${b >= 0 ? 'text-emerald-600' : 'text-rose-600'}`;
        }

        renderMuavinRows(currentReportData.rows);
    } catch (e) {
        console.error('Muavin raporu yüklenemedi:', e);
    }
}

function renderMuavinRows(rows) {
    const tbody = document.getElementById('rep-muavin-table-body');
    const countEl = document.getElementById('rep-muavin-count');
    if (countEl) countEl.textContent = `${rows.length} hareket`;

    if (!tbody) return;

    if (rows.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="py-8 text-center text-slate-400 text-xs font-medium">Bu hesaba ait seçilen dönemde hareket kaydı bulunamadı.</td></tr>';
        return;
    }

    tbody.innerHTML = rows.map(r => {
        const borc = r.borc || 0;
        const alacak = r.alacak || 0;
        const yb = r.yuruyen_bakiye || 0;

        return `
            <tr class="hover:bg-slate-50/80 transition-colors">
                <td class="py-2.5 px-4 font-medium text-slate-600">${r.tarih || '-'}</td>
                <td class="py-2.5 px-4 font-mono font-bold text-teal-700">#${r.no}</td>
                <td class="py-2.5 px-4 text-slate-800 font-medium">${r.aciklama || '-'}</td>
                <td class="py-2.5 px-4 text-right font-mono font-bold ${borc > 0 ? 'text-indigo-600' : 'text-slate-300'}">
                    ${borc > 0 ? fmt(borc) : '-'}
                </td>
                <td class="py-2.5 px-4 text-right font-mono font-bold ${alacak > 0 ? 'text-rose-600' : 'text-slate-300'}">
                    ${alacak > 0 ? fmt(alacak) : '-'}
                </td>
                <td class="py-2.5 px-4 text-right font-mono font-bold ${yb >= 0 ? 'text-emerald-600' : 'text-rose-600'}">
                    ${fmt(Math.abs(yb))} ${yb >= 0 ? '(B)' : '(A)'}
                </td>
                <td class="py-2.5 px-4 text-center">
                    <button type="button" onclick="showVoucherDetailModal('${r.no}')" class="px-2.5 py-1 rounded-lg bg-teal-50 text-teal-700 hover:bg-teal-100 text-xs font-bold transition-all" title="Fişi Çift Taraflı İncele">
                        <i class="fa-solid fa-eye mr-1"></i>İncele
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

// ================= CANLI İSTEMCİ TARAFI ARAMA (CLIENT-SIDE INSTANT SEARCH) =================

function filterCurrentReportTable(query) {
    currentSearchQuery = (query || '').trim().toLowerCase();
    if (!currentReportData || !currentReportData.rows) return;

    const allRows = currentReportData.rows;
    if (!currentSearchQuery) {
        dispatchRender(currentReportData.type, allRows);
        return;
    }

    const filtered = allRows.filter(item => {
        const str = JSON.stringify(Object.values(item)).toLowerCase();
        return str.includes(currentSearchQuery);
    });

    dispatchRender(currentReportData.type, filtered);
}

function dispatchRender(type, rows) {
    if (type === 'cash_flow') renderCashFlowRows(rows);
    else if (type === 'balances') renderBalancesRows(rows);
    else if (type === 'payroll') renderPayrollRows(rows);
    else if (type === 'mizan') renderMizanRows(rows);
    else if (type === 'muavin') renderMuavinRows(rows);
}

// ================= SAYFA İÇİ YEVMİYE FİŞİ İNCELEME MODALI =================

async function showVoucherDetailModal(voucherNo) {
    if (!voucherNo) return;
    try {
        const res = await fetch(`/api/vouchers/detail?no=${encodeURIComponent(voucherNo)}`);
        if (!res.ok) {
            showToast('Fiş detayları getirilemedi.', 'error');
            return;
        }
        const data = await res.json();

        const titleEl = document.getElementById('rep-vd-title');
        const badgeEl = document.getElementById('rep-vd-badge');
        const subEl = document.getElementById('rep-vd-sub');
        const tbody = document.getElementById('rep-vd-table-body');
        const sumBorcEl = document.getElementById('rep-vd-sum-borc');
        const sumAlacakEl = document.getElementById('rep-vd-sum-alacak');
        const statusEl = document.getElementById('rep-vd-balance-status');
        const diffEl = document.getElementById('rep-vd-diff');

        if (titleEl) titleEl.textContent = `Yevmiye Fişi #${data.no}`;
        if (badgeEl) badgeEl.textContent = data.tip || 'MAHSUP';
        if (subEl) subEl.textContent = `Tarih: ${data.tarih || '-'} | Genel Açıklama: ${data.aciklama || '-'}`;

        let totBorc = 0;
        let totAlacak = 0;
        const rows = data.rows || [];

        if (tbody) {
            if (rows.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="py-6 text-center text-slate-400 text-xs">Fiş satırı bulunamadı.</td></tr>';
            } else {
                tbody.innerHTML = rows.map((r, idx) => {
                    totBorc += (r.borc || 0);
                    totAlacak += (r.alacak || 0);
                    return `
                        <tr class="hover:bg-slate-50/80 transition-colors">
                            <td class="py-2.5 px-3 text-center font-mono text-slate-400">${idx + 1}</td>
                            <td class="py-2.5 px-3 font-mono font-bold text-teal-700">${r.hesap_kod}</td>
                            <td class="py-2.5 px-3 font-medium text-slate-800">${r.hesap_ad || '-'}</td>
                            <td class="py-2.5 px-3 text-slate-600">${r.aciklama || '-'}</td>
                            <td class="py-2.5 px-3 text-right font-mono font-bold ${r.borc > 0 ? 'text-indigo-600' : 'text-slate-300'}">
                                ${r.borc > 0 ? fmt(r.borc) : '-'}
                            </td>
                            <td class="py-2.5 px-3 text-right font-mono font-bold ${r.alacak > 0 ? 'text-rose-600' : 'text-slate-300'}">
                                ${r.alacak > 0 ? fmt(r.alacak) : '-'}
                            </td>
                        </tr>
                    `;
                }).join('');
            }
        }

        if (sumBorcEl) sumBorcEl.textContent = fmt(totBorc);
        if (sumAlacakEl) sumAlacakEl.textContent = fmt(totAlacak);

        const diff = Math.abs(totBorc - totAlacak);
        if (statusEl && diffEl) {
            if (diff < 0.005) {
                statusEl.className = "p-2.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center justify-between font-semibold";
                statusEl.innerHTML = `
                    <span class="flex items-center gap-2">
                        <i class="fa-solid fa-circle-check text-emerald-600"></i>
                        <span>Çift taraflı kayıt dengededir (Borç = Alacak).</span>
                    </span>
                    <span class="font-mono font-bold">Dengede</span>
                `;
            } else {
                statusEl.className = "p-2.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between font-semibold";
                statusEl.innerHTML = `
                    <span class="flex items-center gap-2">
                        <i class="fa-solid fa-triangle-exclamation text-rose-600"></i>
                        <span>Kayıt dengede değil! Fark: ${fmt(diff)}</span>
                    </span>
                    <span class="font-mono font-bold text-rose-700">Fark: ${fmt(diff)}</span>
                `;
            }
        }

        showModal('modal-report-voucher-detail');
    } catch (e) {
        console.error('Fiş detayı gösterilemedi:', e);
        showToast('Fiş ayrıntısı yüklenemedi.', 'error');
    }
}

// ================= EXCEL (.XLSX) İNDİRME MOTORU =================

function exportReportToExcel() {
    if (!currentReportData || !currentReportData.rows) {
        showToast('İndirilecek veri bulunamadı.', 'error');
        return;
    }

    try {
        let exportRows = [];
        let fileName = 'rapor.xlsx';
        const type = currentReportData.type;

        if (type === 'cash_flow') {
            fileName = `kasa_nakit_akis_${reportYear}.xlsx`;
            exportRows = currentReportData.rows.map(r => ({
                "Tarih": r.tarih || '',
                "Hesap Kodu": r.kaynak_hesap || r.hesap_kod || '',
                "Hesap/Cari Adı": r.cari_unvan || r.personel_ad || r.hesap_adi || '',
                "Açıklama": r.aciklama || '',
                "Giriş (Borç)": (r.yon === 'GIRIS' || r.borc > 0) ? (r.borc || r.tutar || 0) : 0,
                "Çıkış (Alacak)": (r.yon === 'CIKIS' || r.alacak > 0) ? (r.alacak || r.tutar || 0) : 0
            }));
        } else if (type === 'balances') {
            fileName = `cari_bakiyeler_${new Date().toISOString().split('T')[0]}.xlsx`;
            exportRows = currentReportData.rows.map(c => ({
                "Cari Ünvan": c.unvan,
                "Tip": c.tip === 'MUSTERI' ? 'Müşteri / Kurum' : 'Tedarikçi / Firma',
                "Toplam Borç": c.toplam_borc,
                "Toplam Alacak": c.toplam_alacak,
                "Bakiye": c.bakiye,
                "Durum": c.bakiye >= 0 ? 'Alacaklı' : 'Borçlu',
                "Telefon": c.telefon || ''
            }));
        } else if (type === 'payroll') {
            fileName = `personel_bordro_${reportYear}.xlsx`;
            exportRows = currentReportData.rows.map(p => ({
                "Personel Ad Soyad": p.ad_soyad,
                "Görevi": p.gorev || '',
                "Toplam Hakediş": p.toplam_hakedis,
                "Ödenen Tutar": p.toplam_odenen,
                "Kalan Bakiye": p.kalan_bakiye
            }));
        } else if (type === 'mizan') {
            fileName = `mizan_raporu_${new Date().toISOString().split('T')[0]}.xlsx`;
            exportRows = currentReportData.rows.map(r => {
                const bakiyeB = r.tot_borc > r.tot_alacak ? r.tot_borc - r.tot_alacak : 0;
                const bakiyeA = r.tot_alacak > r.tot_borc ? r.tot_alacak - r.tot_borc : 0;
                return {
                    "Hesap Kodu": r.kod,
                    "Hesap Adı": r.ad,
                    "Borç Toplamı": r.tot_borc,
                    "Alacak Toplamı": r.tot_alacak,
                    "Borç Bakiye": bakiyeB,
                    "Alacak Bakiye": bakiyeA
                };
            });
        } else if (type === 'muavin') {
            fileName = `muavin_hesap_${reportMuavinAccount}_${new Date().toISOString().split('T')[0]}.xlsx`;
            exportRows = currentReportData.rows.map(r => ({
                "Tarih": r.tarih || '',
                "Fiş No": r.no || '',
                "Açıklama": r.aciklama || '',
                "Borç": r.borc || 0,
                "Alacak": r.alacak || 0,
                "Yürüyen Bakiye": r.yuruyen_bakiye || 0
            }));
        }

        if (exportRows.length === 0) {
            showToast('Dışa aktarılacak satır bulunamadı.', 'info');
            return;
        }

        const ws = XLSX.utils.json_to_sheet(exportRows);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Rapor");
        XLSX.writeFile(wb, fileName);
        showToast(`'${fileName}' Excel dosyası indirildi.`, 'success');
    } catch (e) {
        console.error('Excel dışa aktarım hatası:', e);
        showToast('Excel dosyası oluşturulamadı.', 'error');
    }
}
