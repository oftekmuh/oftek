/**
 * oftek - Dashboard ve Günlük Kasa İşlemleri (dashboard.js)
 */

async function loadDashboard() {
    try {
        const res = await fetch('/api/dashboard');
        const data = await res.json();

        const kpiKasa = document.getElementById('kpi-kasa');
        const kpiAlacak = document.getElementById('kpi-alacak');
        const kpiBorc = document.getElementById('kpi-borc');
        const kpiPersonel = document.getElementById('kpi-personel');

        if (kpiKasa) kpiKasa.textContent = fmt(data.kasa);
        if (kpiAlacak) kpiAlacak.textContent = fmt(data.toplam_alacak);
        if (kpiBorc) kpiBorc.textContent = fmt(data.toplam_borc);
        if (kpiPersonel) kpiPersonel.textContent = fmt(data.personel_borc);

        // Canlı Günlük Hareketler (Eğer aktif gün varsa)
        if (typeof activeSession !== 'undefined' && activeSession) {
            const txRes = await fetch(`/api/daily-transactions?gun_id=${activeSession.id}`);
            const txs = await txRes.json();
            const dList = document.getElementById('dashboard-daily-list');
            if (dList) {
                if (txs.length === 0) {
                    dList.innerHTML = '<div class="text-slate-400 py-4 text-center">Bu gün henüz hareket girilmedi.</div>';
                } else {
                    dList.innerHTML = txs.slice(0, 5).map(t => {
                        const isGelir = t.islem_turu === 'ALACAK_TAHSILAT' || t.islem_turu === 'NORMAL_GELIR';
                        const unvan = t.cari_unvan || t.personel_ad_soyad || (t.islem_turu === 'NORMAL_GIDER' ? (t.kategori ? 'Gider: ' + t.kategori : 'Genel Gider') : (t.islem_turu === 'NORMAL_GELIR' ? (t.kategori ? 'Gelir: ' + t.kategori : 'Genel Gelir') : 'İşlem'));
                        return `
                        <div class="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                            <div>
                                <span class="font-semibold text-slate-800">${unvan}</span>
                                <div class="text-[10px] text-slate-400">${t.islem_turu} • ${t.aciklama || ''}</div>
                            </div>
                            <span class="font-mono font-bold ${isGelir ? 'text-emerald-600' : 'text-rose-600'}">${isGelir ? '+' : '-'}${fmt(t.tutar)}</span>
                        </div>
                    `}).join('');
                }
            }
        }

        // Son Yevmiye Fişleri
        const vList = document.getElementById('dashboard-vouchers-list');
        if (vList) {
            if (!data.recent_vouchers || data.recent_vouchers.length === 0) {
                vList.innerHTML = '<div class="text-slate-400 py-4 text-center">Henüz yevmiye fişi yok.</div>';
            } else {
                vList.innerHTML = data.recent_vouchers.map(v => `
                    <div class="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                        <div>
                            <span class="font-semibold text-slate-800">Fiş #${v.no} • ${v.tip}</span>
                            <div class="text-[10px] text-slate-400">${v.tarih} • ${v.aciklama || ''}</div>
                        </div>
                        <span class="font-mono font-bold text-slate-700">${fmt(v.toplam)}</span>
                    </div>
                `).join('');
            }
        }
    } catch (err) {
        console.error("Dashboard yüklenirken hata:", err);
    }
}

async function loadDailyTransactions() {
    const gunId = (typeof activeSession !== 'undefined' && activeSession) ? activeSession.id : '';
    const res = await fetch(`/api/daily-transactions?gun_id=${gunId}`);
    const rows = await res.json();
    const tbody = document.getElementById('daily-table-body');
    if (!tbody) return;

    if (rows.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="py-6 text-center text-slate-400">Gün içi hareket bulunamadı.</td></tr>';
        return;
    }
    tbody.innerHTML = rows.map(r => {
        const isGelir = r.islem_turu === 'ALACAK_TAHSILAT' || r.islem_turu === 'NORMAL_GELIR';
        let turBadgeClass = 'bg-rose-50 text-rose-700';
        if (r.islem_turu === 'ALACAK_TAHSILAT') turBadgeClass = 'bg-emerald-50 text-emerald-700';
        else if (r.islem_turu === 'NORMAL_GELIR') turBadgeClass = 'bg-emerald-50 text-emerald-700';
        else if (r.islem_turu === 'PERSONEL_AVANS') turBadgeClass = 'bg-amber-50 text-amber-700';
        else if (r.islem_turu === 'NORMAL_GIDER') turBadgeClass = 'bg-rose-50 text-rose-700';

        const unvan = r.cari_unvan || r.personel_ad_soyad || (r.islem_turu === 'NORMAL_GIDER' ? (r.kategori ? 'Gider: ' + r.kategori : 'Genel Gider') : (r.islem_turu === 'NORMAL_GELIR' ? (r.kategori ? 'Gelir: ' + r.kategori : 'Genel Gelir') : '-'));
        const hesapStr = r.karsi_hesap ? `${r.kaynak_hesap || '100.01'} ➔ ${r.karsi_hesap}` : (r.kaynak_hesap || '100.01');

        return `
        <tr class="hover:bg-slate-50/80">
            <td class="py-3 px-4 font-medium"><span class="px-2 py-0.5 rounded-md text-[10px] font-semibold ${turBadgeClass}">${r.islem_turu}</span></td>
            <td class="py-3 px-4 font-semibold text-slate-800">${unvan}</td>
            <td class="py-3 px-4 font-mono text-slate-500">${hesapStr}</td>
            <td class="py-3 px-4 text-slate-600">${r.aciklama || '-'}</td>
            <td class="py-3 px-4 text-right font-mono font-bold ${isGelir ? 'text-emerald-600' : 'text-rose-600'}">${isGelir ? '+' : '-'}${fmt(r.tutar)}</td>
        </tr>
    `}).join('');
}
