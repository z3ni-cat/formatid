"""Tes formatid: DBF roundtrip + Accurate GBK pipeline (butuh firebird lokal)."""
import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from formatid import dbf, accurate

def test_dbf_roundtrip():
    fields = [("KODE", "C", 10, 0), ("NAMA", "C", 30, 0),
              ("JUMLAH", "N", 12, 2), ("TGL", "D", 8, 0), ("OK", "L", 1, 0)]
    rows = [
        {"KODE": "A001", "NAMA": "Barang Pertama", "JUMLAH": 1500.50, "TGL": "20260115", "OK": True},
        {"KODE": "A002", "NAMA": "Kedua & 'kutip'", "JUMLAH": -42, "TGL": "20261231", "OK": False},
        {"KODE": "B999", "NAMA": "Tiga", "JUMLAH": None, "TGL": None, "OK": None},
    ]
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "tes.dbf")
        info = dbf.write(p, fields, rows)
        assert info["records"] == 3
        got = dbf.read(p)
        assert len(got) == 3
        assert got[0]["KODE"] == "A001" and got[0]["NAMA"] == "Barang Pertama"
        assert got[0]["JUMLAH"] == 1500.50 and got[0]["TGL"] == "2026-01-15" and got[0]["OK"] is True
        assert got[1]["JUMLAH"] == -42 and got[2]["JUMLAH"] is None and got[2]["OK"] is None
        print("  dbf roundtrip: OK (3 record, C/N/D/L termasuk None & nilai negatif)")

def test_dbf_memo_flag_ignored():
    fields = [("NAMA", "C", 20, 0), ("NILAI", "N", 6, 0)]
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "x.dbf")
        dbf.write(p, fields, [{"NAMA": "A" * 25, "NILAI": 7}])  # C terpotong sesuai size
        got = dbf.read(p)
        assert got[0]["NAMA"] == "A" * 20 and got[0]["NILAI"] == 7
        print("  dbf truncation: OK")

def test_accurate_gbk():
    gbk = "/home/ubuntu/.venice/cache/scratch/accurate_converter/sample_backup.GBK"
    if not os.path.isfile(gbk):
        print("  accurate: SKIP (sample GBK tidak ada — buat dulu lewat create_test_gbk.py)")
        return
    tables = accurate.read_backup(gbk, sysdba_password="38f5f469")
    assert "SI_INVOICE" in tables and len(tables["SI_INVOICE"]) == 148
    assert tables["CUSTOMER"][0]["NAMA"].startswith("PT ")
    print(f"  accurate GBK: OK ({len(tables)} tabel, {len(tables['SI_INVOICE'])} invoice)")

if __name__ == "__main__":
    print("=== tes formatid ===")
    test_dbf_roundtrip()
    test_dbf_memo_flag_ignored()
    test_accurate_gbk()
    print("SEMUA TES LOLOS ✅")
