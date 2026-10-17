"""formatid.dbf — Pembaca & Penulis DBF (dBase III/IV) pure-Python.
Dipakai untuk file export/import e-SPT (Pajak Indonesia) dan aplikasi legacy lain.

Format (dBase III+, terdokumentasi publik):
  Header 32 byte: versi(1) tanggal_yymmdd(3) jumlah_record(4 LE) panjang_header(2 LE)
                  panjang_record(2 LE) reserved(20)
  Field descriptor 32 byte per field: nama(11, NUL-padded) tipe(1) displacement(4)
                  ukuran(1) desimal(1) reserved(14)
  Terminator header: 0x0D
  Record: flag_hapus(1 byte: 0x20=aktif, 0x2A=terhapus) + data field berurutan
  EOF: 0x1A
Tipe field: C=char, N=numeric, F=float, D=date 'YYYYMMDD', L=logical 'Y/N/T/F', M=memo(tdk didukung v1)
"""
import struct
from datetime import date

class DbfError(Exception):
    pass

def _parse_header(data):
    if len(data) < 32:
        raise DbfError("File terlalu pendek bukan DBF")
    version = data[0]
    if version not in (0x02, 0x03, 0x04, 0x30, 0x31, 0x32, 0x43, 0x63, 0x83, 0x8B, 0xCB, 0xF5, 0xFB):
        raise DbfError(f"Byte versi DBF tak dikenal: 0x{version:02x}")
    yy, mm, dd = data[1], data[2], data[3]
    try:
        updated = date(1900 + yy, mm, dd).isoformat()
    except ValueError:
        updated = None
    n_records = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    fields = []
    pos = 32
    while pos + 32 <= header_len - 1:
        fd = data[pos:pos + 32]
        if fd[0] == 0x0D:
            break
        name = fd[:11].split(b"\x00")[0].decode("ascii", "replace").strip()
        ftype = chr(fd[11])
        size = fd[16]
        dec = fd[17]
        fields.append({"name": name, "type": ftype, "size": size, "decimals": dec})
        pos += 32
    if not fields:
        raise DbfError("Tidak ada field descriptor")
    return {"version": version, "updated": updated, "n_records": n_records,
            "record_len": record_len, "fields": fields}

def _decode_field(raw, f):
    t = f["type"]
    s = raw.decode("latin-1").strip()
    if t == "C":
        return s
    if t == "N" or t == "F":
        if not s or set(s) <= {"*"}:  # kosong / asterisk-fill = null (konvensi dBase)
            return None
        try:
            return float(s) if f["decimals"] else int(s)
        except ValueError:
            return s
    if t == "D":
        if len(s) != 8 or not s.isdigit():
            return s
        try:
            return date(int(s[:4]), int(s[4:6]), int(s[6:8])).isoformat()
        except ValueError:
            return s
    if t == "L":
        return {"Y": True, "T": True, "N": False, "F": False}.get(s.upper(), None) if s else None
    if t == "M":
        return f"<memo:{s}>"
    return s

def read(path, encoding="latin-1", with_deleted=False):
    """Baca file DBF -> list of dict. Records terhapus disertakan hanya jika with_deleted."""
    with open(path, "rb") as f:
        data = f.read()
    hdr = _parse_header(data)
    rec_len = hdr["record_len"]
    offset = hdr and struct.unpack("<H", data[8:10])[0]
    fields = hdr["fields"]
    rows = []
    for i in range(hdr["n_records"]):
        base = offset + i * rec_len
        if base + rec_len > len(data):
            break  # file terpotong — ambil yang utuh saja
        rec = data[base:base + rec_len]
        flag = rec[0]
        if flag == 0x1A:
            break
        if flag == 0x2A and not with_deleted:
            continue
        row, pos = {}, 1
        for f in fields:
            raw = rec[pos:pos + f["size"]]
            row[f["name"]] = _decode_field(raw, f)
            pos += f["size"]
        row["_deleted"] = (flag == 0x2A)
        rows.append(row)
    return rows

def write(path, field_defs, rows, encoding="latin-1"):
    """Tulis DBF. field_defs: list of (nama, tipe, ukuran, desimal).
    tipe: C/N/F/D/L. Nilai tanggal pakai 'YYYYMMDD' atau objek date."""
    n_fields = len(field_defs)
    header_len = 32 + 32 * n_fields + 1
    record_len = 1 + sum(f[2] for f in field_defs)
    today = date.today()
    hdr = bytearray(32)
    hdr[0] = 0x03
    hdr[1], hdr[2], hdr[3] = today.year - 1900, today.month, today.day
    struct.pack_into("<I", hdr, 4, len(rows))
    struct.pack_into("<H", hdr, 8, header_len)
    struct.pack_into("<H", hdr, 10, record_len)
    desc = bytearray()
    for name, ftype, size, dec in field_defs:
        assert len(name) <= 10, f"nama field >10 char: {name}"
        assert ftype in "CNFDL", f"tipe tak didukung: {ftype} (M/memo belum)"
        d = bytearray(32)
        d[:len(name)] = name.encode("ascii")
        d[11] = ord(ftype)
        d[16] = size
        d[17] = dec
        desc += d
    out = bytes(hdr) + bytes(desc) + b"\x0D"
    for row in rows:
        rec = bytearray(b" ")  # flag: aktif
        for name, ftype, size, dec in field_defs:
            v = row.get(name)
            if ftype == "C":
                b = ("" if v is None else str(v)).encode(encoding)[:size]
                b = b.ljust(size)
            elif ftype == "N" or ftype == "F":
                if v is None:
                    b = b"*" * size
                else:
                    num = float(v) if dec else int(v)
                    b = f"{num:.{dec}f}".encode() if dec else str(num).encode()
                    b = b.rjust(size)
                    if len(b) > size:
                        b = b[-size:]
            elif ftype == "D":
                if isinstance(v, date):
                    v = v.strftime("%Y%m%d")
                b = (v or "").encode()[:8].ljust(8, b" ")
            elif ftype == "L":
                b = (b"Y" if v else b"N") if v is not None else b"?"
            else:
                b = b" " * size
            rec += b
        out += bytes(rec)
    out += b"\x1A"
    with open(path, "wb") as f:
        f.write(out)
    return {"records": len(rows), "record_len": record_len, "header_len": header_len}
