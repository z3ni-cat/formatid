"""formatid.zahir — Baca database Zahir Accounting.

Temuan RE: Zahir Desktop memakai Firebird (sama dengan Accurate) —
lihat FAQ resmi Zahir ("What database is used in Zahir software? Zahir is using
Firebird database."). Maka pipeline-nya identik dengan formatid.accurate:

- backup Zahir (.GBK/.FBK) -> formatid.accurate.read_backup()
- schema tabel Zahir berbeda nama dari Accurate — introspeksi tetap otomatis.

Catatan versi: Zahir versi lama (era 2000-an) memakai Paradox/BDE (.DB + .PX +
.MB) — untuk itu pakai formatid.dbf (kerabat dekat dBase) setelah tabelnya
diekspor, atau konversi dulu via Zahir versi baru.
"""
from .accurate import read_backup, to_csv  # noqa: F401 — pipeline sama
