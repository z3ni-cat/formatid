"""formatid.accurate — Baca database/backup Accurate (Firebird .GBK atau .FDB).

Pola kerja (hasil RE, lihat README bagian 'Format Accurate'):
- .GBK = file backup gbak Firebird (magic XDR 00 02 04 0A) — harus di-restore dulu
- .FDB = database Firebird langsung — bisa dibaca jika daemon Firebird lokal punya akses
- Schema: introspeksi RDB$RELATIONS (RDB$SYSTEM_FLAG=0)
- SYSDBA default Accurate Desktop: password 'masterkey' (coba dulu ini)

Kebutuhan: firebird3.0-utils (gbak) + server firebird berjalan + pip fdb
"""
import os, subprocess, tempfile, shutil

try:
    import fdb
except ImportError:
    fdb = None

GBK_MAGIC = b"\x00\x02\x04\x0a"

def _check_fdb():
    if fdb is None:
        raise RuntimeError("pip install fdb dulu (driver Firebird Python)")

def read_backup(path, sysdba_password="masterkey", cleanup=True):
    """Baca .GBK (di-restore ke DB sementara) atau .FDB langsung.
    Return: dict {nama_tabel: [ {kolom: nilai}, ... ]}
    Password default Accurate: 'masterkey'. Jika gagal, coba password DB yang di-set user."""
    _check_fdb()
    path = os.path.abspath(path)
    with open(path, "rb") as f:
        magic = f.read(4)
    tmpdir = None
    dsn = path
    if magic == GBK_MAGIC:  # backup gbak -> restore dulu
        tmpdir = tempfile.mkdtemp(prefix="formatid_", dir="/tmp")
        os.chmod(tmpdir, 0o777)
        fdb_path = os.path.join(tmpdir, "restored.fdb")
        r = subprocess.run(
            ["gbak", "-c", "-REP", "-user", "SYSDBA", "-pas", sysdba_password,
             path, f"localhost:{fdb_path}"],
            capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            shutil.rmtree(tmpdir, ignore_errors=True)
            raise RuntimeError(f"Restore gagal (file corrupt / password salah?):\n{r.stderr[:300]}")
        dsn = f"localhost:{fdb_path}"
    else:  # .fdb langsung — selalu lewat daemon (embedded error ENOTDIR)
        dsn = f"localhost:{path}"
    try:
        con = fdb.connect(dsn=dsn, user="SYSDBA", password=sysdba_password)
        cur = con.cursor()
        cur.execute("""SELECT TRIM(RDB$RELATION_NAME) FROM RDB$RELATIONS
                       WHERE RDB$SYSTEM_FLAG=0 AND RDB$VIEW_BLR IS NULL ORDER BY 1""")
        tables = [r[0] for r in cur.fetchall()]
        out = {}
        for t in tables:
            cur.execute(f'SELECT * FROM "{t}"')
            cols = [d[fdb.DESCRIPTION_NAME] for d in cur.description]
            out[t] = [dict(zip(cols, row)) for row in cur.fetchall()]
        con.close()
        return out
    finally:
        if tmpdir and cleanup:
            shutil.rmtree(tmpdir, ignore_errors=True)

def to_csv(tables, outdir):
    """Simpan hasil read_backup ke file CSV per tabel. Return daftar path."""
    import csv
    os.makedirs(outdir, exist_ok=True)
    paths = []
    for name, rows in tables.items():
        p = os.path.join(outdir, f"{name}.csv")
        if not rows:
            open(p, "w").close()
            paths.append(p)
            continue
        cols = list(rows[0].keys())
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        paths.append(p)
    return paths
