
\connect configuration;

-- ############################################################################
-- ##                     PARAMETER YANG BISA DI-EDIT                        ##
-- ##                    (UNTUK KONFIGURASI PERUSAHAAN)                      ##
-- ############################################################################
--
-- Berikut adalah daftar lengkap parameter yang dapat diubah oleh perusahaan
-- untuk menyesuaikan sensitivitas deteksi fraud sesuai kebijakan internal.
--
-- ============================================================================
-- RULE 006 - STRUCTURING DETECTION (Editable Parameters)
-- ============================================================================
--
-- +------------------+---------------+------------------------------------------+
-- | PARAMETER        | DEFAULT VALUE | KETERANGAN                               |
-- +------------------+---------------+------------------------------------------+
-- | maxQueryLimit    | 3             | Jumlah transaksi terakhir yang diperiksa |
-- |                  |               | untuk mencari pola nominal mirip.        |
-- |                  |               | CONTOH: Ubah ke 5 untuk memeriksa 5      |
-- |                  |               | transaksi terakhir.                      |
-- +------------------+---------------+------------------------------------------+
-- | tolerance        | 0.1           | Toleransi persentase untuk dianggap      |
-- |                  |               | "mirip". 0.1 = 10%.                      |
-- |                  |               | CONTOH: 0.05 = 5% (lebih ketat)          |
-- |                  |               |         0.2  = 20% (lebih longgar)       |
-- +------------------+---------------+------------------------------------------+
-- | bands.lowerLimit | 2             | Jumlah minimal transaksi mirip untuk     |
-- |                  |               | trigger alert.                           |
-- |                  |               | CONTOH: Ubah ke 3 agar butuh 3 transaksi |
-- |                  |               | mirip sebelum alert (lebih longgar).     |
-- +------------------+---------------+------------------------------------------+
--
-- ============================================================================
-- RULE 018 - HIGH VALUE DETECTION (Editable Parameters)
-- ============================================================================
--
-- +------------------+---------------+------------------------------------------+
-- | PARAMETER        | DEFAULT VALUE | KETERANGAN                               |
-- +------------------+---------------+------------------------------------------+
-- | maxQueryRange    | 7889229000    | Range waktu (milliseconds) untuk query   |
-- |                  |               | historical transaksi debtor.             |
-- |                  |               | 7889229000 ms = ~91 hari                 |
-- |                  |               | CONTOH: 2592000000 = 30 hari (1 bulan)   |
-- |                  |               |         31536000000 = 365 hari (1 tahun) |
-- +------------------+---------------+------------------------------------------+
-- | bands.lowerLimit | 1.5           | Multiplier dari rata-rata historical.    |
-- | (dan upperLimit) |               | 1.5 = Alert jika transaksi 1.5x lipat    |
-- |                  |               | dari rata-rata.                          |
-- |                  |               | CONTOH: 2.0 = 2x lipat (lebih longgar)   |
-- |                  |               |         1.2 = 1.2x lipat (lebih ketat)   |
-- +------------------+---------------+------------------------------------------+
--
-- ============================================================================
-- CARA MENGUBAH PARAMETER:
-- ============================================================================
--
-- 1. Edit nilai pada JSON configuration di bawah
-- 2. Jalankan script ini ke database:
--    psql -U postgres -d configuration -f setup_extra_rules.sql
-- 3. Restart container rule yang relevan:
--    docker restart tazama-rule-006-1 tazama-rule-018-1
--
-- ============================================================================
-- TIPS KONFIGURASI BERDASARKAN KEBUTUHAN:
-- ============================================================================
--
-- Untuk INDUSTRI PERBANKAN (Strict):
--   Rule 006: maxQueryLimit=5, tolerance=0.05, lowerLimit=2
--   Rule 018: maxQueryRange=30 hari, lowerLimit=1.2
--
-- Untuk E-COMMERCE (Medium):
--   Rule 006: maxQueryLimit=3, tolerance=0.1, lowerLimit=2
--   Rule 018: maxQueryRange=91 hari, lowerLimit=1.5
--
-- Untuk STARTUP / SME (Relaxed):
--   Rule 006: maxQueryLimit=3, tolerance=0.15, lowerLimit=3
--   Rule 018: maxQueryRange=180 hari, lowerLimit=2.0
--
-- ############################################################################

-- ============================================================================
-- RULE 006: STRUCTURING / SMURFING DETECTION
-- ============================================================================
--
-- FUNGSI:
--   Mendeteksi pemecahan transaksi besar menjadi transaksi kecil dengan
--   nominal mirip untuk menghindari pelaporan (threshold audit).
--
-- PARAMETER:
--   - maxQueryLimit: 3    → Jumlah transaksi terakhir yang diperiksa
--   - tolerance: 0.1      → Toleransi 10% untuk dianggap "mirip"
--
-- BANDS (Threshold):
--   - .01: upperLimit = 2 → Jika < 2 transaksi mirip = TIDAK TERDETEKSI
--   - .02: lowerLimit = 2 → Jika >= 2 transaksi mirip = 🚨 ALERT!
--
-- ============================================================================
-- CONTOH KASUS:
-- ============================================================================
--
-- 🟢 Case 1: TIDAK TERDETEKSI (Normal Transaction)
-- +----+-------------+--------+---------------+
-- | No | Tanggal     | Debtor | Amount        |
-- +----+-------------+--------+---------------+
-- | 1  | 08/12 10:00 | Ahmad  | Rp 5.000.000  |
-- | 2  | 08/12 10:05 | Ahmad  | Rp 8.500.000  |
-- | 3  | 08/12 10:10 | Ahmad  | Rp 3.200.000  |
-- +----+-------------+--------+---------------+
-- Analisis: Nominal berbeda-beda → 0 transaksi mirip
--           0 < 2 → masuk band .01 → NO ALERT
--
-- 🔴 Case 2: TERDETEKSI (Structuring Attack)
-- +----+-------------+--------+---------------+
-- | No | Tanggal     | Debtor | Amount        |
-- +----+-------------+--------+---------------+
-- | 1  | 08/12 10:00 | Budi   | Rp 9.500.000  |
-- | 2  | 08/12 10:05 | Budi   | Rp 9.500.000  |
-- | 3  | 08/12 10:10 | Budi   | Rp 9.500.000  |
-- +----+-------------+--------+---------------+
-- Analisis: 3 transaksi dengan nominal identik Rp 9.5jt
--           3 >= 2 → masuk band .02 → 🚨 STRUCTURING ALERT!
--           Pelaku memecah transaksi untuk menghindari threshold audit
--
-- 🔴 Case 3: TERDETEKSI (Dengan Toleransi 10%)
-- +----+-------------+----------+---------------+
-- | No | Tanggal     | Debtor   | Amount        |
-- +----+-------------+----------+---------------+
-- | 1  | 08/12 10:00 | Chandra  | Rp 9.500.000  |
-- | 2  | 08/12 10:05 | Chandra  | Rp 9.400.000  |
-- | 3  | 08/12 10:10 | Chandra  | Rp 9.600.000  |
-- +----+-------------+----------+---------------+
-- Analisis: Toleransi 10% dari Rp 9.5jt = Rp 950.000
--           Range "mirip": Rp 8.550.000 - Rp 10.450.000
--           Semua 3 transaksi masuk range → 3 transaksi mirip
--           3 >= 2 → 🚨 STRUCTURING ALERT!
--
-- 🟡 Case 4: Borderline (Tepat 2 Mirip)
-- +----+-------------+--------+---------------+
-- | No | Tanggal     | Debtor | Amount        |
-- +----+-------------+--------+---------------+
-- | 1  | 08/12 10:00 | Dewi   | Rp 9.500.000  |
-- | 2  | 08/12 10:05 | Dewi   | Rp 9.500.000  |
-- | 3  | 08/12 10:10 | Dewi   | Rp 1.000.000  |
-- +----+-------------+--------+---------------+
-- Analisis: 2 transaksi mirip (Rp 9.5jt), 1 berbeda (Rp 1jt)
--           2 >= 2 → 🚨 STRUCTURING ALERT!
--
-- ============================================================================

-- Delete existing rule if exists (for updates)
delete from rule where ruleid = '006@1.0.0' and tenantid = 'DEFAULT';

insert into rule (configuration) values (
'{
    "id": "006@1.0.0",
    "cfg": "1.0.0",
    "tenantId": "DEFAULT",
    "desc": "Outgoing transfer similarity - amounts",
    "config": {
      "parameters": {
        "maxQueryLimit": 5,
        "tolerance": 0.2
      },
      "exitConditions": [
        {
          "subRuleRef": ".x00",
          "reason": "Incoming transaction is unsuccessful"
        },
        {
          "subRuleRef": ".x01",
          "reason": "Insufficient transaction history"
        }
      ],
      "bands": [
        {
          "subRuleRef": ".01",
          "upperLimit": 5,
          "reason": "No similar amounts detected in the most recent transactions from the debtor"
        },
        {
          "subRuleRef": ".02",
          "lowerLimit": 5,
          "reason": "Two or more similar amounts detected in the most recent transactions from the debtor"
        }
      ]
    }
}');

-- ============================================================================
-- RULE 018: HIGH VALUE TRANSFER DETECTION
-- ============================================================================
--
-- FUNGSI:
--   Mendeteksi satu kali transaksi dengan nilai sangat besar yang
--   melampaui kebiasaan atau batas aman berdasarkan historical data.
--
-- PARAMETER:
--   - maxQueryRange: 7889229000 → Range waktu query (ms) ~91 hari
--
-- BANDS (Threshold):
--   - .01: upperLimit = 1.5 → Jika <= 1.5x rata-rata = TIDAK TERDETEKSI
--   - .02: lowerLimit = 1.5 → Jika > 1.5x rata-rata historical = 🚨 ALERT!
--
-- CATATAN PENTING:
--   Rule ini TIDAK menggunakan nilai absolut (misal: > Rp 15 juta).
--   Threshold adalah MULTIPLIER (1.5x) dari rata-rata historical debtor.
--
-- ============================================================================
-- CONTOH KASUS:
-- ============================================================================
--
-- Asumsi: Debtor "Eko" punya rata-rata historical transaksi = Rp 10.000.000
--         Threshold trigger = 1.5 x Rp 10.000.000 = Rp 15.000.000
--
-- 🟢 Case 1: TIDAK TERDETEKSI (Normal Transaction)
-- +----+-------------+--------+----------------+
-- | No | Tanggal     | Debtor | Amount         |
-- +----+-------------+--------+----------------+
-- | 1  | 08/12 10:00 | Eko    | Rp 12.000.000  |
-- +----+-------------+--------+----------------+
-- Analisis: Rp 12jt / Rp 10jt = 1.2x (ratio)
--           1.2 < 1.5 → masuk band .01 → NO ALERT
--
-- 🔴 Case 2: TERDETEKSI (High Value Transaction)
-- +----+-------------+--------+----------------+
-- | No | Tanggal     | Debtor | Amount         |
-- +----+-------------+--------+----------------+
-- | 1  | 08/12 10:00 | Eko    | Rp 20.000.000  |
-- +----+-------------+--------+----------------+
-- Analisis: Rp 20jt / Rp 10jt = 2.0x (ratio)
--           2.0 >= 1.5 → masuk band .02 → 🚨 HIGH VALUE ALERT!
--
-- 🔴 Case 3: TERDETEKSI (Whale Transaction)
-- +----+-------------+--------+------------------+
-- | No | Tanggal     | Debtor | Amount           |
-- +----+-------------+--------+------------------+
-- | 1  | 08/12 10:00 | Fajar  | Rp 500.000.000   |
-- +----+-------------+--------+------------------+
-- Asumsi: Rata-rata historical Fajar = Rp 50.000.000
-- Analisis: Rp 500jt / Rp 50jt = 10x (ratio)
--           10 >= 1.5 → masuk band .02 → 🚨 HIGH VALUE ALERT!
--
-- 🟡 Case 4: Borderline (Tepat 1.5x)
-- +----+-------------+--------+----------------+
-- | No | Tanggal     | Debtor | Amount         |
-- +----+-------------+--------+----------------+
-- | 1  | 08/12 10:00 | Gita   | Rp 15.000.000  |
-- +----+-------------+--------+----------------+
-- Asumsi: Rata-rata historical Gita = Rp 10.000.000
-- Analisis: Rp 15jt / Rp 10jt = 1.5x (ratio)
--           1.5 >= 1.5 → masuk band .02 → 🚨 HIGH VALUE ALERT!
--
-- ============================================================================
-- CARA MENGUBAH KE NILAI ABSOLUT (Jika Dibutuhkan):
-- ============================================================================
-- Tazama default tidak support nilai absolut. Untuk implementasi seperti:
-- "Semua transaksi > Rp 15 juta = High Value"
--
-- Opsi 1: Modifikasi di Application Layer (attacks.py)
--         COMPANY_HIGH_VALUE_THRESHOLD = 15000000
--
-- Opsi 2: Custom Rule Processor (membutuhkan development)
-- ============================================================================
--
-- Delete existing rule if exists (for updates)
delete from rule where ruleid = '018@1.0.0' and tenantid = 'DEFAULT';


-- ============================================================================
-- RULE 018 CONFIGURATION - INLINE PARAMETER DOCUMENTATION
-- ============================================================================
--
-- STRUKTUR JSON RULE TAZAMA:
-- ============================================================================
--
-- "id"          : ID unik rule dalam format {ruleNumber}@{version}
--                 Contoh: "018@1.0.0" = Rule 018 versi 1.0.0
--
-- "cfg"         : Version struktur konfigurasi (bukan versi rule)
--                 Digunakan untuk backward compatibility jika format berubah
--
-- "tenantId"    : Identifier tenant/organisasi yang menggunakan rule ini
--                 "DEFAULT" = berlaku untuk semua tenant
--
-- "desc"        : Deskripsi singkat fungsi rule dalam bahasa manusia
--
-- ============================================================================
-- PARAMETERS:
-- ============================================================================
--
-- "maxQueryRange" : Rentang waktu query riwayat transaksi dalam MILLISECONDS
--                   Digunakan untuk mengambil data historical debtor
--
--                   KONVERSI:
--                   - 1 detik     = 1.000 ms
--                   - 1 menit     = 60.000 ms
--                   - 1 jam       = 3.600.000 ms
--                   - 1 hari      = 86.400.000 ms
--                   - 7 hari      = 604.800.000 ms
--                   - 30 hari     = 2.592.000.000 ms  <-- DEFAULT
--                   - 91 hari     = 7.862.400.000 ms
--                   - 365 hari    = 31.536.000.000 ms
--
-- ============================================================================
-- EXIT CONDITIONS (Fast Fail):
-- ============================================================================
--
-- Kondisi dimana rule TIDAK DIEKSEKUSI dan langsung return tanpa evaluasi.
-- Ini menghemat resource karena tidak perlu memproses transaksi yang tidak relevan.
--
-- "subRuleRef"  : Kode referensi sub-rule untuk response (format: .x00, .x01, dll)
--                 Prefix "x" menandakan ini adalah exit condition (bukan band result)
--
-- "reason"      : Pesan yang dikembalikan jika exit condition terpenuhi
--
-- EXIT CONDITIONS RULE 018:
-- - .x00 : Transaksi GAGAL (bukan successful transaction) → tidak perlu diperiksa
-- - .x01 : Tidak ada riwayat transaksi → tidak bisa hitung rata-rata historical
--
-- ============================================================================
-- BANDS (Threshold Evaluation):
-- ============================================================================
--
-- Bands adalah RENTANG NILAI untuk mengevaluasi hasil perhitungan rule.
-- Rule 018 menghitung RASIO:
--
--   RASIO = (Nominal Transaksi Sekarang) / (Rata-rata Historical Debtor)
--
-- Contoh: Rata-rata historical = Rp 10.000.000
--         Transaksi sekarang   = Rp 20.000.000
--         RASIO = 20.000.000 / 10.000.000 = 2.0
--
-- "subRuleRef"  : Kode referensi hasil evaluasi (format: .01, .02, dll)
--                 Tanpa "x" menandakan ini adalah band result (bukan exit)
--
-- "upperLimit"  : BATAS ATAS rasio untuk band ini
--                 Jika rasio <= upperLimit, maka masuk band ini
--
-- "lowerLimit"  : BATAS BAWAH rasio untuk band ini
--                 Jika rasio >= lowerLimit, maka masuk band ini
--
-- "reason"      : Pesan/deskripsi hasil evaluasi
--
-- BANDS RULE 018:
-- - .01 : upperLimit = 1.5 → Rasio <= 1.5 = NORMAL (tidak alert)
--         Transaksi masih dalam batas wajar historical kondisi ini tidak terlalu penting
--
-- - .02 : lowerLimit = 1.5 → Rasio >= 1.5 = 🚨 ALERT!
--         Transaksi MELEBIHI 1.5x rata-rata historical
--         Ini adalah FRAUD INDICATOR


-- Notes : kondisi .01 memang tidak terlalu penting tetapi secara auditor sebuah transaksi harus jelas kenapa dia di nilai aman
--          dalam parameter "reason": "Outgoing transfer within historical limits" bands .01 tercatat trasnaski wajar secara historical
 ---    walaupun secara trigger thrashold ada di kondisi .02 pada kasus ini
--
-- ============================================================================

insert into rule (configuration) values (
'{
    "id": "018@1.0.0",
    "cfg": "1.0.0",
    "tenantId": "DEFAULT",
    "desc": "Exceptionally large outgoing transfer - debtor",
    "config": {
      "parameters": {
        "maxQueryRange": 2592000000
      },
      "exitConditions": [
        {
          "subRuleRef": ".x00",
          "reason": "Incoming transaction is unsuccessful"
        },
        {
          "subRuleRef": ".x01",
          "reason": "Insufficient transaction history"
        }
      ],
      "bands": [
        {
          "subRuleRef": ".01",
          "upperLimit": 1.5,
          "reason": "Outgoing transfer within historical limits"
        },
        {
          "subRuleRef": ".02",
          "lowerLimit": 1.5,
          "reason": "Exceptionally large outgoing transfer detected"
        }
      ]
    }
}');

-- ============================================================================
-- NETWORK MAP: Menghubungkan Rules ke Transaction Messages
-- ============================================================================
-- Network Map menentukan rules mana yang dijalankan untuk setiap jenis transaksi.
-- - pacs.008.001.10: Credit Transfer (uang keluar)
-- - pacs.002.001.12: Payment Status Report (konfirmasi transaksi)
--
-- Rules yang aktif untuk pacs.002:
-- - 901: Debtor Velocity Check (3+ transaksi/hari dari debtor = alert)
-- - 902: Creditor Velocity Check (3+ transaksi/hari ke creditor = alert)
-- - 006: Structuring Detection (2+ transaksi mirip = alert)
-- - 018: High Value Detection (> 1.5x rata-rata = alert)
-- ============================================================================

delete from network_map;

insert into network_map (configuration) values (
'{
  "active": true,
  "cfg": "1.0.1",
  "name": "Public Network Map with Extra Rules",
  "tenantId": "DEFAULT",
  "messages": [
    {
      "id": "008@1.0.0",
      "cfg": "1.0.0",
      "txTp": "pacs.008.001.10",
      "typologies": [
        {
          "id": "typology-processor@1.0.0",
          "cfg": "999@1.0.0",
          "tenantId": "DEFAULT",
          "rules": [
            {
              "id": "EFRuP@1.0.0",
              "cfg": "none"
            }
          ]
        }
      ]
    },
    {
      "id": "004@1.0.0",
      "cfg": "1.0.0",
      "txTp": "pacs.002.001.12",
      "typologies": [
        {
          "id": "typology-processor@1.0.0",
          "cfg": "999@1.0.0",
          "tenantId": "DEFAULT",
          "rules": [
             {
              "id": "EFRuP@1.0.0",
              "cfg": "none"
            },
            {
              "id": "901@1.0.0",
              "cfg": "1.0.0"
            },
            {
              "id": "902@1.0.0",
              "cfg": "1.0.0"
            },
            {
              "id": "006@1.0.0",
              "cfg": "1.0.0"
            },
            {
              "id": "018@1.0.0",
              "cfg": "1.0.0"
            }
          ]
        }
      ]
    }
  ]
}');
