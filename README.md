# formatid 🇮🇩

**Pustaka Python untuk membaca format file software bisnis Indonesia** — DBF (e-SPT pajak), backup Accurate & Zahir (Firebird).

## Kenapa pustaka ini ada?

Ceritanya gini: software akuntansi & pajak lokal menyimpan data dalam format yang **nggak pernah didokumentasikan resmi**. Mau narik data dari Accurate/Zahir, atau baca file e-SPT? Mau nggak mau harus bedah sendiri (reverse engineering).

Nah, hasil bedahan itu kami rangkum jadi pustaka ini — kodenya tinggal pakai, plus dokumentasi formatnya biar orang lain nggak perlu ngulang kerjaan yang sama dari nol.

Cocok buat kamu yang bikin integrasi, migrasi data, atau analisis data dari software-software tersebut.

```
pip install formatid   # (setelah publish; sementara: pip install dari repo)
```

## Isi

### `formatid.dbf` — DBF (dBase III/IV)

Format export e-SPT (pajak Indonesia); juga dipakai aplikasi FoxPro/dBase/Clipper jadul. Murni Python, tanpa dependensi.

```
from formatid import dbf

rows = dbf.read("SPT_MASA_PPN.DBF")           # -> list of dict

dbf.write("output.dbf",
          [("KODE","C",10,0), ("NILAI","N",14,2), ("TGL","D",8,0)],
          [{"KODE":"01","NILAI":1500000,"TGL":"20261017"}])
```

**Struktur formatnya** (kami rangkum dari dokumentasi publik, lalu uji sendiri):

| Bagian | Isi |
| --- | --- |
| Header 32B | versi(1B), tgl-update(3B), jumlah_record(4B LE), header_len(2B), record_len(2B) |
| Field descriptor 32B×n | nama(11B NUL-pad), tipe(1B: C/N/F/D/L/M), size(1B), desimal(1B) |
| Terminator | `0x0D` |
| Record | flag(1B: `0x20` aktif / `0x2A` terhapus) + field berurutan fixed-width |
| EOF | `0x1A` |

Beberapa hal yang kami temukan di lapangan: numeric yang kosong biasanya berisi spasi atau `***...` (asterisk-fill); tanggal disimpan sebagai string `YYYYMMDD`; field `M` (memo) tersimpan di file `.FPT` terpisah (belum didukung di v1).

### `formatid.accurate` — Accurate Desktop

Databasenya **Firebird**. File backup-nya berformat gbak (`.GBK`).

```
from formatid import accurate

tables = accurate.read_backup("BACKUP_GBK_2026.GBK")   # -> {"SI_INVOICE": [...], ...}

accurate.to_csv(tables, "hasil/")                       # 1 CSV per tabel
```

**Yang kami temukan waktu mbedah:**

- Magic number `.GBK` ternyata header XDR `00 02 04 0A` (bukan teks "Firebird" seperti dugaan awal)
- Cara restore: `gbak -c -REP -user SYSDBA -pas <pw> backup.gbk localhost:/tmp/x.fdb`
  - **Targetnya wajib diawali `localhost:`** — kalau restore langsung ke file pakai engine embedded, muncul error `ENOTDIR`
- Password SYSDBA bawaan Accurate Desktop: `masterkey` (kalau belum diganti)
- Buat baca skema: introspeksi `RDB$RELATIONS WHERE RDB$SYSTEM_FLAG=0 AND RDB$VIEW_BLR IS NULL`
- Di Debian/Ubuntu: set `DatabaseAccess = Full` di `/etc/firebird/3.0/firebird.conf` supaya restore ke `/tmp` diizinkan

### `formatid.zahir` — Zahir Accounting

Ternyata **juga Firebird** (dikonfirmasi dari FAQ resmi Zahir) — jadi pipelinenya sama persis dengan `accurate`:

```
from formatid import zahir

tables = zahir.read_backup("zahir_backup.GBK")
```

Nama tabel/skemanya beda dari Accurate, tapi introspeksi otomatisnya tetap jalan. Satu catatan: Zahir versi sangat lama (era 2000-an awal) masih pakai Paradox/BDE (`.DB`+`.PX`) — untuk itu ekspor dulu via Zahir modern, atau baca sebagai kerabat DBF.

## Testing

```
python tests/test_all.py   # DBF roundtrip + pipeline GBK (butuh firebird lokal)
```

## Catatan penting

Pustaka ini **hanya untuk membaca data milikmu sendiri** dari software yang kamu beli resmi. Nggak ada cracking proteksi, nggak ada bypass lisensi. Nama Accurate™/Zahir™ adalah merek dagang pemiliknya masing-masing; pustaka ini independen dan tidak berafiliasi dengan mereka.

## Roadmap

- Contoh file e-SPT asli buat test suite
- Reader `.FPT` (memo)
- Writer DBF buat e-SPT (import balik)
- Mapping label Indonesia untuk tabel-tabel umum Accurate/Zahir
- CLI: `formatid <file> --to csv`

## Lisensi

MIT.
