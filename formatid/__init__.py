"""formatid — Pustaka format file bisnis Indonesia (hasil reverse engineering).

Modul:
- formatid.dbf      : baca/tulis DBF (dBase) — format export e-SPT pajak & aplikasi legacy
- formatid.accurate : baca backup Accurate (.GBK/.FDB, Firebird) -> dict tabel
- formatid.zahir    : Zahir juga Firebird — alias dari accurate dengan catatan versi

Semua murni Python (stdlib + fdb untuk Firebird). Lisensi MIT.
"""
from . import dbf, accurate, zahir  # noqa: F401
__version__ = "0.1.0"
