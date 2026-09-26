/**
 * oftek - Ortak Excel Toplu Aktarım Modülü (imports.js)
 * Personel kartları, personel tahakkuku, yevmiye fişleri ve alacak/borç faturalarını
 * Excel (.xlsx/.xls/.csv) dosyasından okur, önizler ve aktarır.
 */

let activeImportKey = null;
let parsedImportRows = [];

// ================= HÜCRE OKUMA & DÖNÜŞTÜRME =================
function normalizeHeader(str) {
    return String(str || '')
        .replace(/İ/g, 'i').replace(/I/g, 'ı').toLowerCase()
        .replace(/ı/g, 'i').replace(/ş/g, 's').replace(/ğ/g, 'g')
        .replace(/ü/g, 'u').replace(/ö/g, 'o').replace(/ç/g, 'c')
        .replace(/[^a-z0-9]/g, '');
}

function cellText(cell) {
    if (!cell || cell.v === undefined || cell.v === null) return '';
    // Uzun tam sayılar (TC, hesap kodu) bilimsel gösterime düşmesin
    if (cell.t === 'n' && Number.isInteger(cell.v)) return String(cell.v);
    return String(cell.w !== undefined ? cell.w : cell.v).trim();
}

function cellAmount(cell) {
    if (!cell || cell.v === undefined || cell.v === null || cell.v === '') return 0;
    if (cell.t === 'n') return Math.round(cell.v * 100) / 100;
    let s = String(cell.v).replace(/₺|TL|\s/gi, '');
    if (!s) return 0;
    if (s.includes(',')) s = s.replace(/\./g, '').replace(',', '.');
    const n = parseFloat(s);
    return isNaN(n) ? NaN : Math.round(n * 100) / 100;
}

function cellDate(cell) {
    if (!cell || cell.v === undefined || cell.v === null || cell.v === '') return '';
    const pad = n => String(n).padStart(2, '0');
    if (cell.t === 'n') {
        const d = XLSX.SSF.parse_date_code(cell.v);
        if (d) return `${d.y}-${pad(d.m)}-${pad(d.d)}`;
    }
    if (cell.v instanceof Date) {
        return `${cell.v.getFullYear()}-${pad(cell.v.getMonth() + 1)}-${pad(cell.v.getDate())}`;
    }
    const s = String(cell.w !== undefined ? cell.w : cell.v).trim();
    let m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
    if (m) return `${m[1]}-${pad(m[2])}-${pad(m[3])}`;
    m = s.match(/^(\d{1,2})[./-](\d{1,2})[./-](\d{4})$/);
    if (m) return `${m[3]}-${pad(m[2])}-${pad(m[1])}`;
    return s; // Geçersiz tarih sunucu doğrulamasında satır numarasıyla raporlanır
}

function readExcelFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = e => {
            try {
                const wb = XLSX.read(new Uint8Array(e.target.result), { type: 'array' });
                const ws = wb.Sheets[wb.SheetNames[0]];
                if (!ws || !ws['!ref']) return resolve([]);
                const range = XLSX.utils.decode_range(ws['!ref']);
                const matrix = [];
                for (let r = range.s.r; r <= range.e.r; r++) {
                    const row = [];
                    for (let c = range.s.c; c <= range.e.c; c++) {
                        row.push(ws[XLSX.utils.encode_cell({ r, c })] || null);
                    }
                    row.excelRow = r + 1;
                    matrix.push(row);
                }
                resolve(matrix);
            } catch (err) {
                reject(err);
            }
        };
        reader.onerror = () => reject(reader.error);
        reader.readAsArrayBuffer(file);
    });
}

/** Başlık satırını sütun tanımlarıyla eşleştirir; başlık yoksa sütun sırasını kullanır. */
function mapExcelRows(matrix, columns) {
    if (matrix.length === 0) return [];
    const header = matrix[0].map(c => normalizeHeader(cellText(c)));
    const colIndex = {};
    columns.forEach(col => {
        const keys = [col.label, ...(col.aliases || [])].map(normalizeHeader);
        const idx = header.findIndex(h => h && keys.includes(h));
        if (idx >= 0) colIndex[col.key] = idx;
    });
    const hasHeader = Object.keys(colIndex).length > 0;
    if (!hasHeader) columns.forEach((col, i) => colIndex[col.key] = i);

    const out = [];
    for (let i = hasHeader ? 1 : 0; i < matrix.length; i++) {
        const row = matrix[i];
        if (row.every(c => cellText(c) === '')) continue;
        const obj = { satir: row.excelRow };
        columns.forEach(col => {
            const cell = colIndex[col.key] !== undefined ? row[colIndex[col.key]] : null;
            if (col.type === 'amount') obj[col.key] = cellAmount(cell);
            else if (col.type === 'date') obj[col.key] = cellDate(cell);
            else obj[col.key] = cellText(cell);
        });
        out.push(obj);
    }
    return out;
}

function importEsc(str) {
    return String(str ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function importToday() {
    return (typeof activeSession !== 'undefined' && activeSession && activeSession.tarih)
        ? activeSession.tarih : new Date().toISOString().split('T')[0];
}

async function postImport(url, payload) {
    const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || 'Aktarım sırasında hata oluştu.');
    return data;
}

function validateAmounts(rows, keys) {
    const errs = [];
    const cols = (EXCEL_IMPORTS[activeImportKey] || {}).columns || [];
    rows.forEach(r => keys.forEach(k => {
        const label = (cols.find(c => c.key === k) || {}).label || k;
        if (isNaN(r[k])) errs.push(`Excel satır ${r.satir}: '${label}' sütunundaki tutar okunamadı.`);
    }));
    return errs;
}

function invoiceColumns(cariLabel, karsiLabel, withCategory) {
    const cols = [
        { key: 'cari', label: cariLabel, aliases: ['cari', 'unvan', 'cariunvan', 'carikodu', 'musteri', 'firma', 'adsoyad'] },
        { key: 'tarih', label: 'Tarih', type: 'date', aliases: ['faturatarihi', 'belgetarihi'] },
        { key: 'belge_no', label: 'Belge No', aliases: ['faturano', 'belgeno', 'evrakno'] },
        { key: 'vade_tarihi', label: 'Vade Tarihi', type: 'date', aliases: ['vade'] },
    ];
    if (withCategory) cols.push({ key: 'kategori', label: 'Kategori', aliases: ['tur', 'alacakturu'] });
    cols.push(
        { key: 'tutar', label: 'Tutar', type: 'amount', aliases: ['toplam', 'toplamtutar', 'faturatutari'] },
        { key: 'karsi_hesap', label: karsiLabel, aliases: ['karsihesap', 'hesapkodu'] },
        { key: 'aciklama', label: 'Açıklama', aliases: ['not'] }
    );
    return cols;
}

function invoiceOptionsHtml(defaultKarsi, karsiNote, cariNote) {
    return `
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <label class="block">
                <span class="text-[11px] font-semibold text-slate-600">Varsayılan Karşı Hesap</span>
                <input type="text" id="imp-opt-karsi" value="${defaultKarsi}" class="mt-1 w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-mono outline-none focus:ring-1 focus:ring-emerald-500">
                <span class="text-[10px] text-slate-400">${karsiNote}</span>
            </label>
            <label class="flex items-start gap-2 bg-slate-50 border border-slate-200 rounded-lg p-2 cursor-pointer">
                <input type="checkbox" id="imp-opt-cari" checked class="mt-0.5 w-4 h-4 rounded">
                <span class="text-[11px] text-slate-700"><b>Bulunamayan carileri otomatik aç</b><br><span class="text-slate-400">${cariNote}</span></span>
            </label>
        </div>`;
}

function invoiceSummary(rows) {
    const errs = validateAmounts(rows, ['tutar']);
    rows.forEach(r => {
        if (!r.cari) errs.push(`Excel satır ${r.satir}: Cari unvanı boş.`);
        if (!isNaN(r.tutar) && r.tutar <= 0) errs.push(`Excel satır ${r.satir}: Tutar sıfırdan büyük olmalıdır.`);
    });
    const total = rows.reduce((s, r) => s + (r.tutar || 0), 0);
    const dates = new Set(rows.map(r => r.tarih || importToday()));
    return { errors: errs, info: `Toplam ${fmt(total)} · ${dates.size} tarih için ${dates.size} tahakkuk fişi kesilecek.` };
}

// ================= AKTARIM TANIMLARI =================
const EXCEL_IMPORTS = {
    personel: {
        title: 'Excel ile Personel Aktar',
        desc: 'Personel kartlarını toplu ekler. Aynı TC Kimlik No (yoksa aynı Ad Soyad) ile kayıtlı personelin bilgileri güncellenir. Excel\'de geçen yeni personel türleri otomatik tanımlanır.',
        submitLabel: 'Personelleri Aktar',
        columns: [
            { key: 'ad_soyad', label: 'Ad Soyad', aliases: ['adisoyadi', 'personel', 'personeladi', 'isim'] },
            { key: 'tc_kimlik', label: 'TC Kimlik No', aliases: ['tc', 'tckimlik', 'tcno', 'tckn'] },
            { key: 'telefon', label: 'Telefon', aliases: ['tel', 'gsm'] },
            { key: 'iban', label: 'IBAN' },
            { key: 'maas', label: 'Maaş', type: 'amount', aliases: ['maas', 'ucret', 'netmaas'] },
            { key: 'personel_turu', label: 'Personel Türü', aliases: ['tur', 'personelturu', 'gorev'] },
            { key: 'hesap_kodu', label: 'Hesap Kodu', aliases: ['hesap'] },
        ],
        sample: [
            ['Ahmet Yılmaz', '12345678901', '05321234567', 'TR000000000000000000000001', 25000, 'Genel Personel', '335.01'],
            ['Ayşe Demir', '10987654321', '', '', 30000.5, 'Yönetim / İdari', '335.01'],
        ],
        optionsHtml: `
            <label class="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg p-2 cursor-pointer text-[11px] text-slate-700">
                <input type="checkbox" id="imp-opt-update" checked class="w-4 h-4 rounded">
                <span><b>Mevcut personeli güncelle</b> (işaretli değilse mevcut kayıtlar atlanır)</span>
            </label>`,
        summarize(rows) {
            const errs = validateAmounts(rows, ['maas']);
            rows.forEach(r => { if (!r.ad_soyad) errs.push(`Excel satır ${r.satir}: Ad Soyad boş.`); });
            return { errors: errs, info: `${rows.length} personel kartı okundu.` };
        },
        async submit(rows) {
            const update_existing = document.getElementById('imp-opt-update')?.checked ?? true;
            const data = await postImport('/api/employees/bulk', { employees: rows, update_existing });
            if (typeof loadEmployeeTypes === 'function') loadEmployeeTypes();
            if (typeof loadEmployees === 'function') loadEmployees();
            return data.message;
        }
    },

    personel_tahakkuk: {
        title: 'Excel ile Tahakkuk Fişini Doldur',
        desc: 'Excel satırları personel tahakkuk fişine eklenir; kontrol ettikten sonra "Fişi Kaydet" ile yevmiyeye aktarırsınız. Personel, Ad Soyad veya TC Kimlik No ile eşleştirilir; tür, borç çeşidi kodu ya da adıyla yazılabilir.',
        submitLabel: 'Fişe Ekle',
        columns: [
            { key: 'personel', label: 'Personel', aliases: ['adsoyad', 'adisoyadi', 'personeladi', 'tc', 'tckimlik', 'tckimlikno', 'isim'] },
            { key: 'tur', label: 'Tür', aliases: ['borccesidi', 'tahakkukturu', 'kod'] },
            { key: 'tutar', label: 'Tutar', type: 'amount', aliases: ['toplam', 'maas', 'ucret'] },
            { key: 'aciklama', label: 'Açıklama', aliases: ['not'] },
        ],
        sample: [
            ['Ahmet Yılmaz', 'MAAS', 25000, 'Maaş Hakedişi'],
            ['12345678901', 'Fazla Mesai Ücreti', 1500, ''],
        ],
        optionsHtml: `
            <label class="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg p-2 cursor-pointer text-[11px] text-slate-700">
                <input type="checkbox" id="imp-opt-replace" checked class="w-4 h-4 rounded">
                <span><b>Fişteki mevcut satırları temizle</b> (işaretli değilse sona eklenir)</span>
            </label>`,
        async prepare() {
            if (typeof loadDebtTypes === 'function' && (!cachedDebtTypes || cachedDebtTypes.length === 0)) await loadDebtTypes();
            if (typeof loadEmployees === 'function' && (!globalEmployeesList || globalEmployeesList.length === 0)) await loadEmployees();
        },
        resolve(r) {
            const key = normalizeHeader(r.personel);
            const emp = (globalEmployeesList || []).find(e =>
                (e.tc_kimlik && String(e.tc_kimlik).trim() === r.personel) || normalizeHeader(e.ad_soyad) === key);
            const tKey = normalizeHeader(r.tur);
            const dt = (cachedDebtTypes || []).find(d => normalizeHeader(d.kod) === tKey || normalizeHeader(d.ad) === tKey)
                || (tKey ? (cachedDebtTypes || []).find(d => normalizeHeader(d.ad).startsWith(tKey)) : null);
            return { emp, tur: dt ? dt.kod : (tKey ? null : 'MAAS') };
        },
        summarize(rows) {
            const errs = validateAmounts(rows, ['tutar']);
            rows.forEach(r => {
                const { emp, tur } = this.resolve(r);
                if (!emp) errs.push(`Excel satır ${r.satir}: '${r.personel}' personel listesinde bulunamadı.`);
                if (!tur) errs.push(`Excel satır ${r.satir}: '${r.tur}' borç çeşidi tanımlı değil.`);
            });
            const total = rows.reduce((s, r) => s + (r.tutar || 0), 0);
            return { errors: errs, info: `${rows.length} tahakkuk satırı · Toplam ${fmt(total)}` };
        },
        async submit(rows) {
            const tbody = document.getElementById('emp-acc-tbody');
            if (document.getElementById('imp-opt-replace')?.checked && tbody) tbody.innerHTML = '';
            rows.forEach(r => {
                const { emp, tur } = this.resolve(r);
                addEmpAccrualRow(emp.id, importEsc(emp.ad_soyad), tur, r.tutar, importEsc(r.aciklama));
            });
            calculateEmpAccTotals();
            return `${rows.length} satır tahakkuk fişine eklendi. Kontrol edip "Fişi Kaydet" ile kaydediniz.`;
        }
    },

    fis: {
        title: 'Excel ile Yevmiye Fişi Aktar',
        desc: 'Aynı "Fiş Grup" değerine sahip satırlar tek fiş olur (boşsa tüm satırlar tek fiştir). Her fişin borç ve alacak toplamı eşit olmalıdır; hatalı fiş varsa hiçbir fiş kaydedilmez. Fiş numaraları sıradan otomatik verilir.',
        submitLabel: 'Fişleri Kaydet',
        columns: [
            { key: 'grup', label: 'Fiş Grup', aliases: ['fisno', 'fis', 'grup', 'fisgrubu'] },
            { key: 'tarih', label: 'Tarih', type: 'date', aliases: ['fistarihi'] },
            { key: 'hesap_kod', label: 'Hesap Kodu', aliases: ['hesap', 'hesapno', 'kod'] },
            { key: 'aciklama', label: 'Açıklama', aliases: ['satiraciklamasi'] },
            { key: 'borc', label: 'Borç', type: 'amount', aliases: ['borctutari'] },
            { key: 'alacak', label: 'Alacak', type: 'amount', aliases: ['alacaktutari'] },
        ],
        sample: [
            ['1', '15.01.2026', '100.01', 'Bağış tahsilatı', 1500, ''],
            ['1', '15.01.2026', '600.01', 'Bağış tahsilatı', '', 1500],
            ['2', '16.01.2026', '630.02', 'Kırtasiye gideri', 250, ''],
            ['2', '16.01.2026', '100.01', 'Kırtasiye gideri', '', 250],
        ],
        optionsHtml: `
            <div class="text-[11px] font-semibold text-slate-600 mb-1">Fiş Türü</div>
            <div id="imp-opt-tip" class="flex flex-wrap gap-1">
                ${['MAHSUP', 'TAHAKKUK', 'ACILIS', 'DUZELTME', 'KAPANIS'].map((t, i) => `
                    <button type="button" data-val="${t}" onclick="setImportVoucherType(this)" class="imp-tip-btn px-2.5 py-1 rounded-lg text-[11px] font-semibold ${i === 0 ? 'bg-amber-600 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}">${{ MAHSUP: 'Mahsup', TAHAKKUK: 'Tahakkuk', ACILIS: 'Açılış', DUZELTME: 'Düzeltme', KAPANIS: 'Kapanış' }[t]}</button>
                `).join('')}
            </div>`,
        group(rows) {
            const groups = new Map();
            rows.forEach(r => {
                const g = r.grup || '1';
                if (!groups.has(g)) groups.set(g, { grup: g, tarih: '', aciklama: '', rows: [] });
                const v = groups.get(g);
                if (!v.tarih && r.tarih) v.tarih = r.tarih;
                if (!v.aciklama && r.aciklama) v.aciklama = r.aciklama;
                v.rows.push({ hesap_kod: r.hesap_kod, aciklama: r.aciklama, borc: r.borc, alacak: r.alacak });
            });
            return [...groups.values()].map(v => ({ ...v, tarih: v.tarih || importToday() }));
        },
        summarize(rows) {
            const errs = validateAmounts(rows, ['borc', 'alacak']);
            const known = new Set((typeof globalAccountsList !== 'undefined' && globalAccountsList || []).map(a => a.kod));
            rows.forEach(r => {
                if (!r.hesap_kod) errs.push(`Excel satır ${r.satir}: Hesap kodu boş.`);
                else if (known.size && !known.has(r.hesap_kod)) errs.push(`Excel satır ${r.satir}: '${r.hesap_kod}' hesap planında yok.`);
            });
            const vouchers = this.group(rows);
            vouchers.forEach(v => {
                const b = v.rows.reduce((s, x) => s + (x.borc || 0), 0);
                const a = v.rows.reduce((s, x) => s + (x.alacak || 0), 0);
                if (Math.abs(b - a) >= 0.01) errs.push(`Fiş '${v.grup}': Borç (${fmt(b)}) ≠ Alacak (${fmt(a)}).`);
            });
            return { errors: errs, info: `${vouchers.length} fiş, ${rows.length} satır okundu.` };
        },
        async prepare() {
            if (typeof loadAccounts === 'function') await loadAccounts();
        },
        async submit(rows) {
            const tip = document.querySelector('#imp-opt-tip .bg-amber-600')?.dataset.val || 'MAHSUP';
            const data = await postImport('/api/vouchers/bulk', { tip, vouchers: this.group(rows) });
            if (typeof loadVouchers === 'function') loadVouchers();
            return data.message;
        }
    },

    alacak: {
        title: 'Excel ile Alacak Faturası Aktar',
        desc: 'Müşteri alacaklarını (satış/hakediş faturaları) toplu ekler ve her tarih için bir tahakkuk fişi keser: Borç müşterinin cari hesabı (120), Alacak karşı hesap (gelir). Kayıtlar FIFO tahsilat dağıtımında hemen kullanılabilir.',
        submitLabel: 'Alacakları Aktar',
        columns: invoiceColumns('Müşteri', 'Gelir Hesabı', true),
        sample: [
            ['Örnek Müşteri A', '01.02.2026', 'F-001', '01.03.2026', 'Kurban', 1000, '600.01', 'Hisse bedeli'],
            ['Örnek Müşteri B', '01.02.2026', 'F-002', '', 'Kermes', 500, '', ''],
        ],
        optionsHtml: invoiceOptionsHtml('600', 'Satırda "Gelir Hesabı" boşsa kullanılır.', 'Müşteri olarak açılır (120.01).'),
        summarize: invoiceSummary,
        async submit(rows) {
            const data = await postImport('/api/receivables/bulk', {
                kalemler: rows,
                karsi_hesap: document.getElementById('imp-opt-karsi')?.value.trim(),
                cari_olustur: document.getElementById('imp-opt-cari')?.checked ?? true
            });
            if (typeof loadReceivables === 'function') loadReceivables();
            return data.message + ` Fiş No: ${data.fis_nolari.map(n => '#' + n).join(', ')}`;
        }
    },

    borc: {
        title: 'Excel ile Borç Faturası Aktar',
        desc: 'Tedarikçi/firma borç faturalarını toplu ekler ve her tarih için bir tahakkuk fişi keser: Borç karşı hesap (gider/stok), Alacak firmanın cari hesabı (320).',
        submitLabel: 'Borçları Aktar',
        columns: invoiceColumns('Firma', 'Gider Hesabı', false),
        sample: [
            ['Örnek Tedarikçi Ltd.', '05.02.2026', 'A-123', '05.03.2026', 7500, '630.02', 'Malzeme alımı'],
            ['Örnek Kırtasiye', '05.02.2026', 'A-124', '', 250, '', ''],
        ],
        optionsHtml: invoiceOptionsHtml('153', 'Satırda "Gider Hesabı" boşsa kullanılır.', 'Firma olarak açılır (320.01).'),
        summarize: invoiceSummary,
        async submit(rows) {
            const data = await postImport('/api/debts/bulk', {
                kalemler: rows,
                karsi_hesap: document.getElementById('imp-opt-karsi')?.value.trim(),
                cari_olustur: document.getElementById('imp-opt-cari')?.checked ?? true
            });
            if (typeof loadDebts === 'function') loadDebts();
            return data.message + ` Fiş No: ${data.fis_nolari.map(n => '#' + n).join(', ')}`;
        }
    }
};

function setImportVoucherType(btn) {
    btn.parentElement.querySelectorAll('.imp-tip-btn').forEach(b => {
        b.className = 'imp-tip-btn px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200';
    });
    btn.className = 'imp-tip-btn px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-amber-600 text-white';
}

// ================= MODAL AKIŞI =================
async function openExcelImport(key) {
    const cfg = EXCEL_IMPORTS[key];
    if (!cfg) return;
    activeImportKey = key;
    parsedImportRows = [];

    document.getElementById('excel-imp-title').textContent = cfg.title;
    document.getElementById('excel-imp-desc').textContent = cfg.desc;
    document.getElementById('excel-imp-columns').innerHTML = cfg.columns
        .map(c => `<span class="px-1.5 py-0.5 rounded bg-white border border-slate-200 font-mono">${c.label}</span>`).join(' ');
    document.getElementById('excel-imp-options').innerHTML = cfg.optionsHtml || '';
    document.getElementById('excel-imp-submit-label').textContent = cfg.submitLabel;
    document.getElementById('excel-imp-file').value = '';
    document.getElementById('excel-imp-preview').classList.add('hidden');
    document.getElementById('excel-imp-submit').disabled = true;
    showModal('modal-excel-import');

    if (cfg.prepare) {
        try { await cfg.prepare(); } catch (e) { console.error(e); }
    }
}

function downloadExcelImportTemplate() {
    const cfg = EXCEL_IMPORTS[activeImportKey];
    if (!cfg) return;
    const ws = XLSX.utils.aoa_to_sheet([cfg.columns.map(c => c.label), ...cfg.sample]);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Sablon');
    XLSX.writeFile(wb, `ornek_${activeImportKey}.xlsx`);
    showToast('Örnek Excel şablonu indirildi.', 'success');
}

async function onExcelImportFileSelected(evt) {
    const cfg = EXCEL_IMPORTS[activeImportKey];
    const file = evt.target.files[0];
    if (!cfg || !file) return;
    try {
        const matrix = await readExcelFile(file);
        parsedImportRows = mapExcelRows(matrix, cfg.columns);
    } catch (err) {
        console.error(err);
        showToast('Excel dosyası okunurken hata oluştu: ' + err.message, 'error');
        return;
    }

    if (parsedImportRows.length === 0) {
        showToast('Excel dosyasında aktarılacak satır bulunamadı.', 'error');
        return;
    }

    const summary = cfg.summarize ? cfg.summarize(parsedImportRows) : { errors: [], info: '' };
    const cols = cfg.columns;
    document.getElementById('excel-imp-info').textContent = summary.info;
    document.getElementById('excel-imp-errors').innerHTML = summary.errors.length
        ? `<div class="bg-rose-50 border border-rose-200 text-rose-800 rounded-lg p-2 mb-2 space-y-0.5">
               <div class="font-bold">${summary.errors.length} sorun bulundu, düzeltip dosyayı tekrar seçiniz:</div>
               ${summary.errors.slice(0, 15).map(e => `<div>• ${importEsc(e)}</div>`).join('')}
               ${summary.errors.length > 15 ? `<div class="italic">... ve ${summary.errors.length - 15} sorun daha</div>` : ''}
           </div>` : '';
    document.getElementById('excel-imp-table').innerHTML = `
        <thead><tr class="text-slate-500">
            <th class="text-left px-1.5 py-1">#</th>
            ${cols.map(c => `<th class="text-left px-1.5 py-1 whitespace-nowrap">${c.label}</th>`).join('')}
        </tr></thead>
        <tbody>
            ${parsedImportRows.slice(0, 10).map(r => `
                <tr class="border-t border-slate-100">
                    <td class="px-1.5 py-1 text-slate-400">${r.satir}</td>
                    ${cols.map(c => `<td class="px-1.5 py-1 whitespace-nowrap ${c.type === 'amount' ? 'text-right' : ''}">${
                        c.type === 'amount' ? (r[c.key] ? fmt(r[c.key]) : '') : importEsc(r[c.key])}</td>`).join('')}
                </tr>`).join('')}
        </tbody>`;
    document.getElementById('excel-imp-more').textContent =
        parsedImportRows.length > 10 ? `... ve ${parsedImportRows.length - 10} satır daha` : '';
    document.getElementById('excel-imp-preview').classList.remove('hidden');
    document.getElementById('excel-imp-submit').disabled = summary.errors.length > 0;
}

async function submitExcelImport() {
    const cfg = EXCEL_IMPORTS[activeImportKey];
    if (!cfg || parsedImportRows.length === 0) return;
    const btn = document.getElementById('excel-imp-submit');
    btn.disabled = true;
    try {
        const msg = await cfg.submit(parsedImportRows);
        hideModal('modal-excel-import');
        showToast(msg, 'success');
    } catch (e) {
        console.error(e);
        showToast(e.message, 'error');
        btn.disabled = false;
    }
}
