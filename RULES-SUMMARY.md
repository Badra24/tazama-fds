# Tazama FDS - Ringkasan Rules untuk Tim Bisnis

## Rules yang Aktif

| Rule ID | Nama | Fungsi | Kapan Trigger Alert? |
|---------|------|--------|---------------------|
| **901** | Debtor Velocity | Deteksi pengirim yang transfer terlalu sering | ≥ 3 transfer dari pengirim yang sama dalam 24 jam |
| **902** | Creditor Velocity | Deteksi penerima yang menerima terlalu sering | ≥ 3 transfer ke penerima yang sama dalam 24 jam |
| **006** | Structuring | Deteksi pemecahan transaksi besar | ≥ 5 transaksi dengan nominal mirip (toleransi 20%) |
| **018** | High Value | Deteksi transaksi di luar kebiasaan | Nominal ≥ 1.5x rata-rata 30 hari terakhir |
| **EFRuP** | Event Flow | Validasi dan kontrol alur | Block/override berdasarkan konfigurasi |

---

## Detail Setiap Rule

### 🔴 Rule 901 - Debtor Velocity (Kecepatan Pengirim)

**Tujuan:** Mendeteksi akun yang mengirim uang dalam frekuensi tidak wajar.

**Contoh Kasus:**
- Budi transfer 5x dalam 1 jam → **🚨 ALERT** (potensi money laundering)
- Ani transfer 1x sehari → ✅ Normal

**Parameter:**
- Window waktu: 24 jam
- Threshold: 3 transaksi

---

### 🔴 Rule 902 - Creditor Velocity (Kecepatan Penerima)

**Tujuan:** Mendeteksi akun yang menerima uang dalam frekuensi tidak wajar.

**Contoh Kasus:**
- Akun X menerima 10 transfer dalam 1 jam → **🚨 ALERT** (potensi mule account)
- Akun Y menerima 2 transfer per hari → ✅ Normal

**Parameter:**
- Window waktu: 24 jam
- Threshold: 3 transaksi

---

### 🟡 Rule 006 - Structuring Detection (Deteksi Pemecahan)

**Tujuan:** Mendeteksi upaya memecah transaksi besar untuk menghindari pelaporan.

**Contoh Kasus:**
- Candra kirim: Rp 9.5jt, Rp 9.4jt, Rp 9.6jt, Rp 9.5jt, Rp 9.3jt → **🚨 ALERT** (5 transaksi mirip)
- Dedi kirim: Rp 5jt, Rp 10jt, Rp 3jt → ✅ Normal (nominal berbeda)

**Parameter:**
- Jumlah transaksi diperiksa: 5 terakhir
- Toleransi "mirip": 20%
- Threshold: 5 transaksi mirip

---

### 🟠 Rule 018 - High Value Detection (Transaksi Besar)

**Tujuan:** Mendeteksi transaksi yang melebihi kebiasaan pengirim.

**Contoh Kasus:**
- Eko rata-rata kirim Rp 10jt/bulan, tiba-tiba kirim Rp 50jt → **🚨 ALERT** (5x rata-rata)
- Fani rata-rata Rp 10jt, kirim Rp 12jt → ✅ Normal (1.2x, masih wajar)

**Parameter:**
- Historical range: 30 hari
- Threshold: 1.5x rata-rata

---

## Output Sistem

Setiap transaksi akan menghasilkan salah satu status:

| Status | Keterangan | Aksi |
|--------|------------|------|
| **ALRT** | Alert - Terdeteksi mencurigakan | Perlu review manual |
| **NALT** | No Alert - Normal | Tidak ada aksi |

---

## Contoh Skenario Bisnis

### Skenario 1: Money Laundering via Velocity
```
Attacker mengirim 40 transaksi kecil dalam 1 jam.
→ Rule 901 trigger di transaksi ke-3
→ 38 transaksi di-ALERT
→ Tim AML menerima notifikasi untuk investigasi
```

### Skenario 2: Structuring untuk Bypass Threshold
```
Pelaku ingin transfer Rp 100jt tapi threshold pelaporan Rp 50jt.
Dia pecah jadi: Rp 9.5jt x 10 transaksi.
→ Rule 006 mendeteksi 10 nominal mirip
→ ALERT dikirim ke dashboard
```

### Skenario 3: Account Takeover
```
Akun yang biasanya transfer Rp 1jt tiba-tiba transfer Rp 500jt.
→ Rule 018 mendeteksi 500x dari rata-rata
→ ALERT dengan severity tinggi
```

---

*Dokumen ini untuk keperluan internal Tim Bisnis/Compliance*
*Last Updated: 17 Desember 2025*
