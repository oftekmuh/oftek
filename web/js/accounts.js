/**
 * oftek - Hesap Planı, Mizan ve Excel İçe Aktarımı
 */

let globalAccountsList = [];

async function loadAccounts() {
    try {
        const res = await fetch('/api/accounts');
        const rows = await res.json();
        if (!res.ok || !Array.isArray(rows)) {
            throw new Error((rows && rows.error) || `Sunucu yanıtı: ${res.status}`);
        }
        globalAccountsList = rows;
        const tbody = document.getElementById('accounts-table-body');
        if (!tbody) return;
        tbody.innerHTML = rows.map(r => `
            <tr class="hover:bg-slate-50 font-mono">
                <td class="py-2 px-4 font-bold text-indigo-600">${r.kod}</td>
                <td class="py-2 px-4 font-sans text-slate-800">${r.ad}</td>
                <td class="py-2 px-4 text-center"><span class="px-2 py-0.5 rounded text-[10px] ${r.karakter === 'AKTIF' ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}">${r.karakter}</span></td>
            </tr>
        `).join('');
    } catch(e) {
        console.error('Hesaplar yüklenirken hata:', e);
    }
}

async function loadMizan() {
    try {
        const res = await fetch('/api/mizan');
        const rows = await res.json();
        const tbody = document.getElementById('mizan-table-body');
        if (!tbody) return;
        tbody.innerHTML = rows.map(r => {
            const bakiyeB = r.tot_borc > r.tot_alacak ? r.tot_borc - r.tot_alacak : 0;
            const bakiyeA = r.tot_alacak > r.tot_borc ? r.tot_alacak - r.tot_borc : 0;
            return `
                <tr class="hover:bg-slate-50 font-mono">
                    <td class="py-2.5 px-4 font-bold text-indigo-600">${r.kod}</td>
                    <td class="py-2.5 px-4 font-sans text-slate-800">${r.ad}</td>
                    <td class="py-2.5 px-4 text-right">${fmt(r.tot_borc)}</td>
                    <td class="py-2.5 px-4 text-right">${fmt(r.tot_alacak)}</td>
                    <td class="py-2.5 px-4 text-right text-emerald-600 font-bold">${bakiyeB > 0 ? fmt(bakiyeB) : '-'}</td>
                    <td class="py-2.5 px-4 text-right text-rose-600 font-bold">${bakiyeA > 0 ? fmt(bakiyeA) : '-'}</td>
                </tr>
            `;
        }).join('');
    } catch(e) {
        console.error('Mizan yüklenirken hata:', e);
    }
}

let parsedImportAccounts = [];

function showAccountImportModal() {
    parsedImportAccounts = [];
    const fileInp = document.getElementById('excel-file-input');
    if (fileInp) fileInp.value = '';
    const previewBox = document.getElementById('import-preview-box');
    if (previewBox) previewBox.classList.add('hidden');
    const submitBtn = document.getElementById('btn-submit-import');
    if (submitBtn) submitBtn.disabled = true;
    showModal('modal-import-accounts');
}

function downloadAccountExcelTemplate() {
    const data = [
        ["Hesap Kodu", "Hesap Adı", "Karakter"],
        ["100", "KASA", "AKTIF"],
        ["100.01", "Merkez TL Kasası", "AKTIF"],
        ["102", "BANKALAR", "AKTIF"],
        ["102.01", "Banka Vadesiz TL", "AKTIF"],
        ["120", "ALICILAR", "AKTIF"],
        ["120.01", "Müşteriler / Kurumlar", "AKTIF"],
        ["320", "SATICILAR", "PASIF"],
        ["320.01", "Tedarikçiler / Firmalar", "PASIF"],
        ["335", "PERSONELE BORÇLAR", "PASIF"],
        ["335.01", "Personele Net Maaş Borçları", "PASIF"],
        ["600", "YURTİÇİ SATIŞLAR", "PASIF"],
        ["770", "GENEL YÖNETİM GİDERLERİ", "AKTIF"]
    ];
    const ws = XLSX.utils.aoa_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "HesapPlani");
    XLSX.writeFile(wb, "ornek_hesap_plani.xlsx");
    showToast("Örnek Excel şablonu indirildi.", "success");
}

function onAccountExcelFileSelected(evt) {
    const file = evt.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, { type: 'array' });
            const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
            const rows = XLSX.utils.sheet_to_json(firstSheet, { header: 1, raw: false, defval: '' });

            parsedImportAccounts = [];
            const startIndex = (rows[0] && isNaN(String(rows[0][0]).charAt(0))) ? 1 : 0;

            for (let i = startIndex; i < rows.length; i++) {
                const r = rows[i];
                if (r && r[0] && r[1]) {
                    const kod = String(r[0]).trim();
                    const ad = String(r[1]).trim();
                    let karakter = r[2] ? String(r[2]).trim().toUpperCase() : 'AKTIF';
                    if (!['AKTIF', 'PASIF'].includes(karakter)) karakter = 'AKTIF';
                    parsedImportAccounts.push({ kod, ad, karakter });
                }
            }

            if (parsedImportAccounts.length === 0) {
                showToast("Excel dosyasında geçerli hesap bulunamadı! İlk 2 sütunun Hesap Kodu ve Hesap Adı olduğundan emin olunuz.", "error");
                return;
            }

            const countEl = document.getElementById('import-preview-count');
            if (countEl) countEl.textContent = parsedImportAccounts.length;
            const previewList = document.getElementById('import-preview-list');
            if (previewList) {
                previewList.innerHTML = parsedImportAccounts.slice(0, 8).map(a => `
                    <div class="flex justify-between py-1 border-b border-slate-100">
                        <span class="font-bold text-indigo-600">${a.kod}</span>
                        <span class="text-slate-800">${a.ad}</span>
                        <span class="text-slate-400 text-[10px]">${a.karakter}</span>
                    </div>
                `).join('') + (parsedImportAccounts.length > 8 ? `<div class="text-center text-slate-400 pt-1 italic">... ve ${parsedImportAccounts.length - 8} hesap daha</div>` : '');
            }

            const previewBox = document.getElementById('import-preview-box');
            if (previewBox) previewBox.classList.remove('hidden');
            const submitBtn = document.getElementById('btn-submit-import');
            if (submitBtn) submitBtn.disabled = false;
            showToast(`${parsedImportAccounts.length} hesap başarıyla okundu.`, "success");
        } catch (err) {
            console.error(err);
            showToast("Excel dosyası okunurken hata oluştu: " + err.message, "error");
        }
    };
    reader.readAsArrayBuffer(file);
}

async function submitAccountImport() {
    if (parsedImportAccounts.length === 0) return;
    const clearFirst = document.getElementById('import-clear-first')?.checked || false;

    try {
        const res = await fetch('/api/accounts/bulk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ accounts: parsedImportAccounts, clear_first: clearFirst })
        });
        const data = await res.json();
        if (res.ok) {
            showToast(data.message || 'Hesaplar başarıyla aktarıldı.', 'success');
            hideModal('modal-import-accounts');
            switchTab('hesap_plani');
        } else {
            showToast(data.error || 'Aktarım sırasında hata oluştu.', 'error');
        }
    } catch (e) {
        console.error(e);
        showToast('Sunucu hatası oluştu.', 'error');
    }
}
