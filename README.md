# formatid 🇮🇩

**Pustaka Python format file bisnis Indonesia** — hasil reverse engineering, terdokumentasi, teruji. Untuk developer/engineer yang bikin integrasi, migrasi data, atau analisis data dari software bisnis lokal.

```
pip install formatid   # (setelah publish; sementara: pip install dari repo)
```

## Kenapa ada?

Software akuntansi & pajak Indonesia menyimpan data dalam format yang **tidak pernah didokumentasikan resmi**. Siapa pun yang pernah mencoba mengambil data dari Accurate/Zahir atau membaca file e-SPT harus reverse engineering sendiri. Pustaka ini merangkum hasil RE itu jadi kode yang bisa langsung dipakai + dokumentasi formatnya.

## Isi

### `formatid.dbf` — DBF (dBase III/IV)
Format export e-SPT (Pajak Indonesia), aplikasi FoxPro/dBase/Clipper legacy. Pure Python, tanpa dependensi.

```python
from formatid import dbf

rows = dbf.read("SPT_MASA_PPN.DBF")           # -> list of dict
dbf.write("output.dbf",
          [("KODE","C",10,0), ("NILAI","N",14,2), ("TGL","D",8,0)],
          [{"KODE":"01","NILAI":1500000,"TGL":"20261017"}])
```

**Struktur format** (terdokumentasi publik, kami rangkum + uji):
| Bagian | Isi |
|---|---|
| Header 32B | versi(1B), tgl-update(3B), jumlah_record(4B LE), header_len(2B), record_len(2B) |
| Field descriptor 32B×n | nama(11B NUL-pad), tipe(1B: C/N/F/D/L/M), size(1B), desimal(1B) |
| Terminator | `0x0D` |
| Record | flag(1B: `0x20` aktif / `0x2A` terhapus) + field berurutan fixed-width |
| EOF | `0x1A` |

Catatan lapangan: numeric kosong = spasi atau `***...` (asterisk-fill); date = `YYYYMMDD` string; field `M` (memo) tersimpan di file `.FPT` terpisah (belum didukung v1).

### `formatid.accurate` — Accurate Desktop
Database = **Firebird**. Backup = file gbak `.GBK`.

```python
from formatid import accurate

tables = accurate.read_backup("BACKUP_GBK_2026.GBK")   # -> {"SI_INVOICE": [...], ...}
accurate.to_csv(tables, "hasil/")                       # 1 CSV per tabel
```

**Temuan RE:**
- Magic `.GBK` = XDR header `00 02 04 0A` (bukan teks "Firebird")
- Restore: `gbak -c -REP -user SYSDBA -pas <pw> backup.gbk localhost:/tmp/x.fdb`
  - **Target WAJIB diawali `localhost:`** — engine embedded menghasilkan `ENOTDIR` saat membuat file
- Password SYSDBA default Accurate Desktop: `masterkey` (bila tidak diganti)
- Schema: introspeksi `RDB$RELATIONS WHERE RDB$SYSTEM_FLAG=0 AND RDB$VIEW_BLR IS NULL`
- Debian/Ubuntu: set `DatabaseAccess = Full` di `/etc/firebird/3.0/firebird.conf` agar restore ke `/tmp` diizinkan

### `formatid.zahir` — Zahir Accounting
**Juga Firebird** (dikonfirmasi FAQ resmi Zahir) → pipeline sama dengan `accurate`:

```python
from formatid import zahir
tables = zahir.read_backup("zahir_backup.GBK")
```
Nama tabel/skema berbeda dari Accurate — introspeksi otomatis tetap bekerja. Zahir era sangat lama (2000-an awal) memakai Paradox/BDE (`.DB`+`.PX`) — ekspor dulu via Zahir modern, atau baca dengan kerabat DBF.

## Testing

```bash
python tests/test_all.py   # DBF roundtrip + pipeline GBK (butuh firebird lokal)
```

## Garis batas

Pustaka ini hanya **membaca data milik Anda sendiri** dari software yang Anda beli. Tidak melakukan cracking proteksi, tidak melewati lisensi. Nama Accurate™/Zahir™ adalah merek pemiliknya; pustaka ini independen & tidak berafiliasi.

## Roadmap
- [ ] Contoh file e-SPT asli untuk test suite
- [ ] `.FPT` memo reader
- [ ] Writer DBF untuk e-SPT (import balik)
- [ ] Mapping label Indonesia untuk tabel Accurate/Zahir umum
- [ ] CLI `formatid <file> --to csv`

## Lisensi
MIT.
