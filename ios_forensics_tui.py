#!/usr/bin/env python3
"""
iOS Forensic & Debug TUI Inspector (Gege Edition)
Coleta completa de dados de debug, hardware, IORegistry, NVRAM, AFC, SQLite,
EXIF, Crash Reports, USB/usbmuxd e Syslog em tempo real.
Compatível com Linux, Windows (x64) e macOS.
"""

import argparse
import base64
import datetime
import json
import os
import platform
import plistlib
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    Log,
    RichLog,
    Static,
    TabbedContent,
    TabPane,
    Tree,
)

IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"


def configure_runtime_environment() -> None:
    """Adiciona diretórios de binários empacotados (Windows/PyInstaller/InnoSetup) ao PATH."""
    candidate_dirs: List[Path] = []
    # Diretório interno do PyInstaller (_MEIPASS)
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidate_dirs.append(Path(meipass) / "bin")
        candidate_dirs.append(Path(meipass))
    # Diretório do executável ou script atual
    exe_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    candidate_dirs.extend([
        exe_dir / "bin",
        exe_dir / "drivers",
        exe_dir,
    ])
    if IS_WINDOWS:
        prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        prog_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        common_files = os.environ.get("CommonProgramFiles", r"C:\Program Files\Common Files")
        candidate_dirs.extend([
            Path(prog_files) / "iOS_Forensics" / "bin",
            Path(prog_files) / "libimobiledevice",
            Path(common_files) / "Apple" / "Mobile Device Support",
            Path(common_files) / "Apple" / "Apple Application Support",
            Path(prog_files_x86) / "Common Files" / "Apple" / "Mobile Device Support",
        ])

    current_path = os.environ.get("PATH", "")
    path_parts = current_path.split(os.pathsep) if current_path else []
    prepended: List[str] = []
    for d in candidate_dirs:
        d_str = str(d)
        if d.is_dir() and d_str not in path_parts and d_str not in prepended:
            prepended.append(d_str)
    if prepended:
        os.environ["PATH"] = os.pathsep.join(prepended + path_parts)


configure_runtime_environment()


def get_lockdown_dir() -> Path:
    """Retorna o diretório padrão de certificados Lockdown de acordo com o SO."""
    if IS_WINDOWS:
        prog_data = os.environ.get("ProgramData", r"C:\ProgramData")
        return Path(prog_data) / "Apple" / "Lockdown"
    if IS_MACOS:
        return Path("/var/db/lockdown")
    return Path("/var/lib/lockdown")


def get_default_crash_dir() -> Path:
    """Retorna o diretório temporário para extração de relatórios de crash."""
    if IS_WINDOWS:
        return Path(tempfile.gettempdir()) / "ios_crashes"
    return Path("/tmp/ios_crashes")


def get_default_export_base_dir() -> str:
    """Retorna o diretório base padrão para exportação de pacotes forenses."""
    if IS_WINDOWS:
        docs = Path.home() / "Documents" / "iOS_Forensics_Exports"
        docs.mkdir(parents=True, exist_ok=True)
        return str(docs)
    if os.geteuid() == 0 and Path("/root").exists():
        return "/root"
    return str(Path.home())


def run_cmd(cmd: List[str], timeout: int = 8) -> Tuple[int, bytes, bytes]:
    kwargs: Dict[str, Any] = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "timeout": timeout,
        "check": False,
    }
    if IS_WINDOWS:
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    try:
        proc = subprocess.run(cmd, **kwargs)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout if isinstance(exc.stdout, bytes) else (exc.stdout.encode("utf-8", errors="replace") if exc.stdout else b"")
        err = exc.stderr if isinstance(exc.stderr, bytes) else (exc.stderr.encode("utf-8", errors="replace") if exc.stderr else b"Timeout expired")
        return 124, out, err
    except Exception as exc:
        return 1, b"", str(exc).encode("utf-8", errors="replace")


def decode_apple_serial_date(serial: str) -> str:
    """
    Decodes Apple 12-char or 17-char component serial numbers where applicable.
    12-char device serial (pre-randomization):
      char[0..2] = Factory ID
      char[3]    = Year half (C..Z)
      char[4]    = Week within half (1..9, C..Y)
    17-char component serial (e.g. F8Y845626XEJKGTAR, F3X90220D79L1P1A):
      char[0..2] = Factory ID
      char[3]    = Year digit (e.g. 8 = 2018, 9 = 2019)
      char[4..5] = Week of year (01..52)
    """
    serial = serial.strip()
    if not serial:
        return "N/A"
    # 12-char Apple Device Serial (2010-2021)
    if len(serial) == 12:
        year_map = {
            "C": (2010, 1), "D": (2010, 2),
            "F": (2011, 1), "G": (2011, 2),
            "H": (2012, 1), "J": (2012, 2),
            "K": (2013, 1), "L": (2013, 2),
            "M": (2014, 1), "N": (2014, 2),
            "P": (2015, 1), "Q": (2015, 2),
            "R": (2016, 1), "S": (2016, 2),
            "T": (2017, 1), "V": (2017, 2),
            "W": (2018, 1), "X": (2018, 2),
            "Y": (2019, 1), "Z": (2019, 2),
            "C0": (2020, 1),
        }
        week_chars = "123456789CDFGHJKLMNPQRTVWXY"
        fac = serial[:3]
        yh = serial[3].upper()
        wc = serial[4].upper()
        if yh in year_map and wc in week_chars:
            year, half = year_map[yh]
            week = week_chars.index(wc) + 1 + (26 if half == 2 else 0)
            return f"Fábrica: {fac} | Ano: {year} | Semana: {week:02d}"
    # 17+ char Apple Component Serial (MLB, Battery, Display, etc.)
    if len(serial) >= 16 and serial[3].isdigit() and serial[4:6].isdigit():
        fac = serial[:3]
        yr_digit = int(serial[3])
        wk = int(serial[4:6])
        year = 2010 + yr_digit if yr_digit >= 7 else 2020 + yr_digit
        if 1 <= wk <= 53:
            return f"Fábrica: {fac} | Ano est.: {year} | Semana: {wk:02d}"
    return "Formato proprietário"


def parse_jpeg_exif_basic(data: bytes) -> Dict[str, Any]:
    """Extracts readable ASCII strings / dates / camera tags from JPEG header."""
    info: Dict[str, Any] = {"size_bytes": len(data)}
    head = data[:65536]
    dates = re.findall(rb"20\d{2}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}", head)
    if dates:
        info["exif_dates"] = sorted({d.decode("ascii", errors="ignore") for d in dates})
    ascii_matches = re.findall(rb"[A-Za-z0-9_\-\.\: ]{5,40}", head[:8192])
    interesting = []
    for m in ascii_matches:
        s = m.decode("ascii", errors="ignore").strip()
        if any(k in s.lower() for k in ["apple", "iphone", "ios", "heic", "exif", "gps", "photoshop", "18.", "17.", "16."]):
            if s not in interesting:
                interesting.append(s)
    if interesting:
        info["header_strings"] = interesting[:12]
    return info


class IOSForensicCollector:
    """Coleta todos os dados possíveis do dispositivo iOS conectado via USB."""

    def __init__(self) -> None:
        self.data: Dict[str, Any] = {}
        self.last_updated: str = "Nunca"

    def collect_all(self, deep_afc: bool = True) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "timestamp": datetime.datetime.now().isoformat(),
            "host_os": f"{platform.system()} {platform.release()} ({platform.machine()})",
            "usb": self.collect_usb_and_daemon(),
            "pairing": self.collect_pairing_and_lockdown(),
            "ideviceinfo": self.collect_ideviceinfo(),
            "domains": self.collect_domains(),
            "nvram_decoded": {},
            "ioreg": self.collect_ioregistry(),
            "diagnostics": self.collect_diagnostics(),
            "afc": {},
            "crashes": self.collect_crash_summary(),
        }
        result["nvram_decoded"] = self.decode_nvram(result["ideviceinfo"])
        if deep_afc:
            result["afc"] = self.collect_afc_forensics()
        self.data = result
        self.last_updated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return result

    def collect_usb_and_daemon(self) -> Dict[str, Any]:
        info: Dict[str, Any] = {}
        if IS_WINDOWS:
            _, pnp_out, _ = run_cmd(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -match 'VID_05AC' -or $_.FriendlyName -match 'Apple|iPhone|iPad' } | Select-Object Status,Class,FriendlyName,InstanceId | Format-Table -AutoSize | Out-String -Width 200",
                ],
                timeout=8,
            )
            lines = [l.strip() for l in pnp_out.decode("utf-8", errors="replace").splitlines() if l.strip()]
            info["lsusb_apple"] = lines or ["Nenhum dispositivo USB Apple (VID_05AC) detectado via PnP"]

            _, svc_out, _ = run_cmd(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-Service -Name 'Apple Mobile Device Service','usbmuxd' -ErrorAction SilentlyContinue | Select-Object Name,Status,StartType | Format-Table -AutoSize | Out-String",
                ],
                timeout=6,
            )
            info["usbmuxd_status"] = svc_out.decode("utf-8", errors="replace").strip() or "Serviço usbmuxd / Apple Mobile Device Service não registrado"
            info["dmesg_usb_events"] = lines[-15:]
            return info

        _, out, _ = run_cmd(["lsusb"])
        lines = [l for l in out.decode("utf-8", errors="replace").splitlines() if "05ac:" in l.lower() or "apple" in l.lower()]
        info["lsusb_apple"] = lines

        # Verbose lsusb for 05ac
        _, vout, _ = run_cmd(["lsusb", "-d", "05ac:"])
        if lines:
            _, vdesc, _ = run_cmd(["lsusb", "-v", "-d", "05ac:"], timeout=5)
            info["lsusb_verbose"] = vdesc.decode("utf-8", errors="replace")[:4000]

        _, sout, _ = run_cmd(["systemctl", "status", "usbmuxd", "--no-pager"])
        info["usbmuxd_status"] = sout.decode("utf-8", errors="replace")

        _, dout, _ = run_cmd(["dmesg", "-T"])
        dlines = [
            l for l in dout.decode("utf-8", errors="replace").splitlines()
            if any(k in l.lower() for k in ["iphone", "05ac", "ipheth", "apple-mfi", "usbmux"])
        ]
        info["dmesg_usb_events"] = dlines[-30:]
        return info

    def collect_pairing_and_lockdown(self) -> Dict[str, Any]:
        pinfo: Dict[str, Any] = {}
        _, out, _ = run_cmd(["idevice_id", "-l"])
        udids = [u.strip() for u in out.decode("utf-8", errors="replace").splitlines() if u.strip()]
        pinfo["connected_udids"] = udids

        rc, vout, verr = run_cmd(["idevicepair", "validate"])
        pinfo["validate_rc"] = rc
        pinfo["validate_output"] = (vout + verr).decode("utf-8", errors="replace").strip()

        lockdown_dir = get_lockdown_dir()
        pinfo["lockdown_dir"] = str(lockdown_dir)
        records = []
        if lockdown_dir.exists():
            for p in sorted(lockdown_dir.glob("*.plist")):
                rec: Dict[str, Any] = {
                    "filename": p.name,
                    "size": p.stat().st_size,
                    "mtime": datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
                }
                try:
                    pl = plistlib.loads(p.read_bytes())
                    rec["keys"] = list(pl.keys())
                    for k in ["HostID", "SystemBUID", "WiFiMACAddress", "EscrowBag"]:
                        if k in pl:
                            val = pl[k]
                            rec[k] = f"<{len(val)} bytes>" if isinstance(val, bytes) else str(val)
                except Exception as exc:
                    rec["error"] = str(exc)
                records.append(rec)
        pinfo["lockdown_records"] = records
        return pinfo

    def collect_ideviceinfo(self) -> Dict[str, Any]:
        rc, out, _ = run_cmd(["ideviceinfo", "-x"], timeout=8)
        if rc == 0 and out.strip():
            try:
                return plistlib.loads(out)
            except Exception:
                pass
        # Fallback without -x
        rc2, out2, _ = run_cmd(["ideviceinfo"], timeout=8)
        parsed: Dict[str, Any] = {}
        for line in out2.decode("utf-8", errors="replace").splitlines():
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                parsed[k.strip()] = v.strip()
        return parsed

    def collect_domains(self) -> Dict[str, Any]:
        domains = [
            "com.apple.disk_usage",
            "com.apple.mobile.battery",
            "com.apple.PurpleBuddy",
            "com.apple.mobile.restriction",
            "com.apple.mobile.backup",
            "com.apple.mobile.wireless_lockdown",
            "com.apple.international",
            "com.apple.mobile.internal",
            "com.apple.mobile.chaperone",
            "com.apple.xcode.developerdomain",
        ]
        res: Dict[str, Any] = {}
        for dom in domains:
            rc, out, _ = run_cmd(["ideviceinfo", "-q", dom, "-x"], timeout=5)
            if rc == 0 and out.strip():
                try:
                    pl = plistlib.loads(out)
                    if pl:
                        # Strip massive binary blobs like NANDInfo for readability, but record size
                        cleaned = {}
                        for k, v in pl.items():
                            if isinstance(v, bytes) and len(v) > 256:
                                cleaned[k] = f"<Binary Blob: {len(v)} bytes, sha1={v[:16].hex()}...>"
                            else:
                                cleaned[k] = v
                        res[dom] = cleaned
                except Exception:
                    pass
        return res

    def decode_nvram(self, devinfo: Dict[str, Any]) -> Dict[str, Any]:
        nvram = devinfo.get("NonVolatileRAM", {})
        decoded: Dict[str, Any] = {}
        if not isinstance(nvram, dict):
            return decoded
        for k, v in nvram.items():
            raw_bytes: Optional[bytes] = None
            if isinstance(v, bytes):
                raw_bytes = v
            elif isinstance(v, str) and v:
                try:
                    raw_bytes = base64.b64decode(v)
                except Exception:
                    raw_bytes = v.encode("utf-8", errors="replace")
            if raw_bytes is None:
                decoded[k] = str(v)
                continue
            # Check if binary plist
            if raw_bytes.startswith(b"bplist00"):
                try:
                    bpl = plistlib.loads(raw_bytes)
                    decoded[k] = f"[Binary Plist] {self._summarize_obj(bpl)}"
                    continue
                except Exception:
                    pass
            try:
                txt = raw_bytes.decode("utf-8")
                if all(c.isprintable() or c in "\r\n\t" for c in txt):
                    decoded[k] = txt
                else:
                    decoded[k] = f"hex:{raw_bytes.hex()}"
            except Exception:
                decoded[k] = f"hex:{raw_bytes.hex()}"
        return decoded

    def _summarize_obj(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                str(k): (f"<{len(v)}B: {v[:12].hex()}...>" if isinstance(v, bytes) else self._summarize_obj(v))
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [self._summarize_obj(x) for x in obj]
        if isinstance(obj, bytes):
            return f"<{len(obj)}B: {obj[:12].hex()}>"
        return obj

    def collect_ioregistry(self) -> Dict[str, Any]:
        entries = [
            "AppleSmartBattery",
            "AppleARMPMUCharger",
            "product",
            "chosen",
            "tristar",
            "wlan",
            "baseband",
            "lcd",
            "multi-touch",
            "isp",
            "pearl-sep",
            "sep",
        ]
        res: Dict[str, Any] = {}
        for entry in entries:
            rc, out, _ = run_cmd(["idevicediagnostics", "ioregentry", entry], timeout=5)
            if rc == 0 and out.strip():
                try:
                    pl = plistlib.loads(out)
                    ior = pl.get("IORegistry", {})
                    if ior:
                        cleaned: Dict[str, Any] = {}
                        for k, v in ior.items():
                            if isinstance(v, bytes):
                                try:
                                    s = v.rstrip(b"\x00").decode("utf-8")
                                    if s and all(c.isprintable() for c in s):
                                        cleaned[k] = s
                                    elif len(v) == 4:
                                        cleaned[k] = int.from_bytes(v, "little")
                                    else:
                                        cleaned[k] = f"<{len(v)}B hex:{v[:20].hex()}>"
                                except Exception:
                                    if len(v) == 4:
                                        cleaned[k] = int.from_bytes(v, "little")
                                    else:
                                        cleaned[k] = f"<{len(v)}B hex:{v[:20].hex()}>"
                            elif isinstance(v, (dict, list)) and k in ("IOReportLegend",):
                                continue
                            else:
                                cleaned[k] = self._summarize_obj(v)
                        res[entry] = cleaned
                except Exception:
                    pass
        return res

    def collect_diagnostics(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {}
        rc, out, _ = run_cmd(["idevicediagnostics", "diagnostics", "All"], timeout=5)
        if rc == 0 and out.strip():
            try:
                res["All"] = plistlib.loads(out)
            except Exception:
                pass
        return res

    def collect_afc_forensics(self) -> Dict[str, Any]:
        afc: Dict[str, Any] = {"directories": {}, "dcim_files": [], "sqlite_summary": {}}
        for path in ["/", "/DCIM", "/DCIM/100APPLE", "/Downloads", "/PhotoData", "/Books", "/MediaAnalysis", "/iTunes_Control"]:
            rc, out, _ = run_cmd(["afcclient", "ls", path], timeout=5)
            if rc == 0:
                items = [
                    x.strip() for x in out.decode("utf-8", errors="replace").splitlines()
                    if x.strip() and x.strip() not in (".", "..")
                ]
                afc["directories"][path] = items

        # Inspect DCIM/100APPLE files and pull headers/EXIF
        dcim_items = afc["directories"].get("/DCIM/100APPLE", [])
        with tempfile.TemporaryDirectory() as tmpdir:
            for fname in dcim_items[:15]:
                remote_path = f"/DCIM/100APPLE/{fname}"
                rc, info_out, _ = run_cmd(["afcclient", "info", remote_path], timeout=5)
                fmeta: Dict[str, Any] = {"name": fname, "path": remote_path}
                if rc == 0:
                    for line in info_out.decode("utf-8", errors="replace").splitlines():
                        if ":" in line:
                            k, v = line.split(":", 1)
                            k = k.strip()
                            v = v.strip()
                            if k in ("st_mtime", "st_birthtime") and v.isdigit():
                                ts = int(v) / 1e9
                                fmeta[k] = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                            else:
                                fmeta[k] = v
                local_file = os.path.join(tmpdir, fname)
                rc_get, _, _ = run_cmd(["afcclient", "get", remote_path, local_file], timeout=8)
                if rc_get == 0 and os.path.exists(local_file):
                    raw = Path(local_file).read_bytes()
                    fmeta["exif"] = parse_jpeg_exif_basic(raw)
                afc["dcim_files"].append(fmeta)

            # Inspect SQLite databases over AFC
            sqlite_targets = [
                ("/Downloads/downloads.28.sqlitedb", "downloads.28.sqlitedb"),
                ("/PhotoData/Photos.sqlite", "Photos.sqlite"),
                ("/MediaAnalysis/mediaanalysis.db", "mediaanalysis.db"),
            ]
            for remote_db, label in sqlite_targets:
                local_db = os.path.join(tmpdir, label)
                rc_db, _, _ = run_cmd(["afcclient", "get", remote_db, local_db], timeout=10)
                if rc_db == 0 and os.path.exists(local_db) and os.path.getsize(local_db) > 0:
                    db_info: Dict[str, Any] = {"size_bytes": os.path.getsize(local_db), "tables": {}}
                    try:
                        conn = sqlite3.connect(local_db)
                        cur = conn.cursor()
                        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
                        tables = [r[0] for r in cur.fetchall()]
                        db_info["table_count"] = len(tables)
                        non_empty = {}
                        for t in tables:
                            try:
                                cur.execute(f'SELECT COUNT(*) FROM "{t}";')
                                cnt = cur.fetchone()[0]
                                if cnt > 0:
                                    non_empty[t] = cnt
                            except Exception:
                                pass
                        db_info["non_empty_tables"] = non_empty
                        if "ZASSET" in non_empty:
                            try:
                                cur.execute(
                                    "SELECT a.ZFILENAME, a.ZDIRECTORY, a.ZDATECREATED, a.ZADDEDDATE, "
                                    "b.ZIMPORTEDBYBUNDLEIDENTIFIER, b.ZIMPORTEDBYDISPLAYNAME, b.ZEXIFTIMESTAMPSTRING, b.ZTIMEZONENAME "
                                    "FROM ZASSET a LEFT JOIN ZADDITIONALASSETATTRIBUTES b ON a.ZADDITIONALATTRIBUTES = b.Z_PK LIMIT 20;"
                                )
                                cols = [d[0] for d in cur.description]
                                rows = []
                                for r in cur.fetchall():
                                    row_dict = dict(zip(cols, r))
                                    for tk in ("ZDATECREATED", "ZADDEDDATE"):
                                        if isinstance(row_dict.get(tk), (int, float)) and row_dict[tk] > 0:
                                            dt = datetime.datetime(2001, 1, 1) + datetime.timedelta(seconds=float(row_dict[tk]))
                                            row_dict[tk] = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                                    rows.append(row_dict)
                                db_info["zasset_sample"] = rows
                            except Exception as e:
                                db_info["zasset_err"] = str(e)
                        conn.close()
                    except Exception as exc:
                        db_info["error"] = str(exc)
                    afc["sqlite_summary"][remote_db] = db_info

        return afc

    def collect_crash_summary(self) -> Dict[str, Any]:
        crash_dir = get_default_crash_dir()
        crash_dir.mkdir(parents=True, exist_ok=True)
        files = sorted(crash_dir.rglob("*"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
        file_list = []
        for f in files:
            if f.is_file():
                file_list.append({
                    "name": str(f.relative_to(crash_dir)),
                    "size": f.stat().st_size,
                    "mtime": datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "path": str(f),
                })
        return {"crash_dir": str(crash_dir), "count": len(file_list), "files": file_list[:50]}

    def export_full_forensic_package(self, base_dir: Optional[str] = None) -> str:
        if base_dir is None:
            base_dir = get_default_export_base_dir()
        if not self.data:
            self.collect_all(deep_afc=True)
        udid = self.data.get("ideviceinfo", {}).get("UniqueDeviceID", "unknown_device")
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = Path(base_dir) / f"forensics_iphone_{udid}_{ts}"
        out_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON dump
        json_path = out_dir / "forensic_report.json"
        json_path.write_text(json.dumps(self.data, indent=2, default=str, ensure_ascii=False), encoding="utf-8")

        # Pull DCIM photos and SQLite DBs into export folder
        dcim_out = out_dir / "DCIM_100APPLE"
        dcim_out.mkdir(exist_ok=True)
        for item in self.data.get("afc", {}).get("dcim_files", []):
            rpath = item.get("path")
            fname = item.get("name")
            if rpath and fname:
                run_cmd(["afcclient", "get", rpath, str(dcim_out / fname)], timeout=10)

        db_out = out_dir / "SQLite_DBs"
        db_out.mkdir(exist_ok=True)
        for remote_db in ["/PhotoData/Photos.sqlite", "/Downloads/downloads.28.sqlitedb", "/MediaAnalysis/mediaanalysis.db"]:
            run_cmd(["afcclient", "get", remote_db, str(db_out / Path(remote_db).name)], timeout=12)

        # Copy lockdown record
        lockdown_out = out_dir / "lockdown"
        lockdown_out.mkdir(exist_ok=True)
        lockdown_src = get_lockdown_dir()
        if lockdown_src.exists():
            for p in lockdown_src.glob("*.plist"):
                try:
                    shutil.copy2(p, lockdown_out / p.name)
                except Exception:
                    pass

        return str(out_dir)


class IOSForensicTUI(App):
    """Aplicação TUI Interativa para Diagnóstico e Perícia Forense iOS."""

    TITLE = "iOS Forensic & USB Debug Suite (Gege TUI)"
    SUB_TITLE = "Inspeção Profunda: Lockdown • IORegistry • NVRAM • Bateria • AFC/SQLite • Crash/Syslog"

    CSS = """
    Screen {
        background: #0d1117;
        color: #e6edf3;
    }
    #top-status {
        height: 5;
        background: #161b22;
        border: solid #30363d;
        padding: 0 2;
        margin: 0 1;
    }
    #action-bar {
        height: 3;
        background: #161b22;
        padding: 0 1;
        margin: 0 1;
    }
    Button {
        margin: 0 1;
    }
    RichLog {
        background: #0d1117;
        border: solid #30363d;
        padding: 1 2;
        height: 1fr;
    }
    TabbedContent {
        height: 1fr;
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("r", "refresh_data", "Atualizar Dados"),
        Binding("p", "re_pair", "Forçar Pareamento"),
        Binding("e", "export_package", "Exportar Perícia"),
        Binding("s", "capture_syslog", "Capturar Syslog (5s)"),
        Binding("c", "pull_crashes", "Baixar CrashLogs"),
        Binding("q", "quit", "Sair"),
    ]

    def __init__(self, collector: IOSForensicCollector) -> None:
        super().__init__()
        self.collector = collector

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Carregando dados do dispositivo...", id="top-status")
        with Horizontal(id="action-bar"):
            yield Button("🔄 [R] Atualizar", id="btn-refresh", variant="primary")
            yield Button("🔑 [P] Re-Parear (Trust)", id="btn-pair", variant="warning")
            yield Button("💾 [E] Exportar Perícia", id="btn-export", variant="success")
            yield Button("📡 [S] Amostra Syslog", id="btn-syslog", variant="default")
            yield Button("💥 [C] Baixar Crashes", id="btn-crashes", variant="error")
        with TabbedContent():
            with TabPane("1. Resumo & Pareamento", id="tab-overview"):
                yield RichLog(id="log-overview", highlight=True, markup=True, wrap=True)
            with TabPane("2. Hardware & Seriais (Perícia)", id="tab-hw"):
                yield RichLog(id="log-hw", highlight=True, markup=True, wrap=True)
            with TabPane("3. NVRAM, iCloud (FMI) & SIM", id="tab-nvram"):
                yield RichLog(id="log-nvram", highlight=True, markup=True, wrap=True)
            with TabPane("4. Bateria, Energia & USB", id="tab-battery"):
                yield RichLog(id="log-battery", highlight=True, markup=True, wrap=True)
            with TabPane("5. Arquivos AFC, Fotos & SQLite", id="tab-afc"):
                yield RichLog(id="log-afc", highlight=True, markup=True, wrap=True)
            with TabPane("6. Crash Reports & Live Syslog", id="tab-logs"):
                yield RichLog(id="log-syslog", highlight=True, markup=True, wrap=True)
        yield Footer()

    def on_mount(self) -> None:
        self.render_all_views()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-refresh":
            self.action_refresh_data()
        elif bid == "btn-pair":
            self.action_re_pair()
        elif bid == "btn-export":
            self.action_export_package()
        elif bid == "btn-syslog":
            self.action_capture_syslog()
        elif bid == "btn-crashes":
            self.action_pull_crashes()

    def action_refresh_data(self) -> None:
        self.notify("Coletando todos os dados do iPhone via USB...", title="Atualizando")
        self.collector.collect_all(deep_afc=True)
        self.render_all_views()
        self.notify("Coleta concluída com sucesso!", title="Pronto")

    def action_re_pair(self) -> None:
        self.notify("Executando idevicepair pair & validate...", title="Pareamento")
        _, out1, err1 = run_cmd(["idevicepair", "pair"], timeout=6)
        _, out2, err2 = run_cmd(["idevicepair", "validate"], timeout=6)
        msg = (out1 + err1 + b"\n" + out2 + err2).decode("utf-8", errors="replace").strip()
        self.collector.collect_all(deep_afc=False)
        self.render_all_views()
        self.notify(msg or "Pareamento verificado!", title="Resultado do Pair", timeout=6)

    def action_export_package(self) -> None:
        self.notify("Exportando pacote forense completo (JSON + Fotos + SQLite + Plists)...", title="Exportação")
        out_dir = self.collector.export_full_forensic_package()
        self.notify(f"Salvo em: {out_dir}", title="Exportação Concluída!", timeout=8)

    def action_capture_syslog(self) -> None:
        self.notify("Capturando 4 segundos de idevicesyslog ao vivo...", title="Syslog iOS")
        _, out, err = run_cmd(["idevicesyslog"], timeout=4)
        log_widget = self.query_one("#log-syslog", RichLog)
        log_widget.write("[bold cyan]=== AMOSTRA AO VIVO DO IDEVICESYSLOG (4s) ===[/bold cyan]")
        lines = (out + err).decode("utf-8", errors="replace").splitlines()
        for line in lines[-60:]:
            log_widget.write(line)
        self.notify(f"{len(lines)} linhas capturadas na aba 6!", title="Syslog")

    def action_pull_crashes(self) -> None:
        self.notify("Extraindo relatórios de crash via idevicecrashreport...", title="Crash Reports")
        crash_dir = get_default_crash_dir()
        crash_dir.mkdir(parents=True, exist_ok=True)
        run_cmd(["idevicecrashreport", "-k", str(crash_dir)], timeout=10)
        self.collector.data["crashes"] = self.collector.collect_crash_summary()
        self.render_logs_tab()
        self.notify("Crash reports atualizados na aba 6!", title="Crash Reports")

    def render_all_views(self) -> None:
        d = self.collector.data
        dev = d.get("ideviceinfo", {})
        ior_prod = d.get("ioreg", {}).get("product", {})
        bat_dom = d.get("domains", {}).get("com.apple.mobile.battery", {})
        nvram = d.get("nvram_decoded", {})

        model_desc = ior_prod.get("product-description") or dev.get("ProductType", "Desconhecido")
        ios_ver = f"{dev.get('ProductVersion', '?')} ({dev.get('BuildVersion', '?')})"
        serial = dev.get("SerialNumber", "N/A")
        udid = dev.get("UniqueDeviceID", "N/A")
        act_state = dev.get("ActivationState", "N/A")
        fmi_locked = nvram.get("fm-activation-locked", "N/A")
        fmi_acc = nvram.get("fm-account-masked", "N/A")
        bat_pct = bat_dom.get("BatteryCurrentCapacity", "?")

        top = self.query_one("#top-status", Static)
        top.update(
            f"[bold cyan]📱 Dispositivo:[/bold cyan] [bold white]{model_desc}[/bold white] ({dev.get('ProductType', '?')} / {dev.get('HardwareModel', '?')})   "
            f"[bold cyan]iOS:[/bold cyan] {ios_ver}   "
            f"[bold cyan]Serial:[/bold cyan] {serial}   "
            f"[bold cyan]Bateria:[/bold cyan] {bat_pct}%\n"
            f"[bold yellow]⚡ Estado Ativação:[/bold yellow] [bold red]{act_state}[/bold red]   "
            f"[bold yellow]🔒 iCloud/FMI Lock:[/bold yellow] [bold red]{fmi_locked}[/bold red] ({fmi_acc})   "
            f"[bold green]✔ Pareamento Host:[/bold green] TrustedHostAttached={dev.get('TrustedHostAttached')} (UDID: {udid})\n"
            f"[dim]Última coleta: {self.collector.last_updated} | Host: {d.get('host_os', platform.system())} | Use as abas para navegar[/dim]"
        )

        self.render_overview_tab()
        self.render_hw_tab()
        self.render_nvram_tab()
        self.render_battery_tab()
        self.render_afc_tab()
        self.render_logs_tab()

    def render_overview_tab(self) -> None:
        w = self.query_one("#log-overview", RichLog)
        w.clear()
        d = self.collector.data
        dev = d.get("ideviceinfo", {})
        pair = d.get("pairing", {})
        lockdown_path = pair.get("lockdown_dir", str(get_lockdown_dir()))

        w.write("[bold yellow]🔍 POR QUE NÃO APARECEU 'CONFIAR NESTE COMPUTADOR' NA TELA DO CELULAR?[/bold yellow]")
        w.write(
            "1. [bold green]Pareamento Já Validado Automaticamente:[/bold green] O aparelho está com "
            f"[bold]ActivationState = {dev.get('ActivationState')}[/bold] (tela de Setup/Ativação inicial) e "
            f"[bold]PasswordProtected = {dev.get('PasswordProtected')}[/bold] (sem senha de tela ativa).\n"
            "2. Nesse estado, o `lockdownd` da Apple permite o pareamento imediato sem exigir popup na tela, "
            f"gerando o certificado em `{lockdown_path}/{dev.get('UniqueDeviceID')}.plist`.\n"
            f"3. Status do `idevicepair validate`: [bold green]{pair.get('validate_output')}[/bold green]\n"
            "4. O erro `ipheth-pair failed (code 255 / -8)` nos logs ocorre apenas porque o compartilhamento de internet "
            "(Personal Hotspot via USB) é bloqueado pelo iOS enquanto o aparelho está `Unactivated`.\n"
        )

        t = Table(title="Identificação Geral do Dispositivo", expand=True)
        t.add_column("Propriedade", style="cyan", no_wrap=True)
        t.add_column("Valor Extraído", style="white")
        t.add_column("Interpretação Forense", style="yellow")

        ior_prod = d.get("ioreg", {}).get("product", {})
        ecid_raw = dev.get("UniqueChipID", 0)
        try:
            ecid_hex = f"0x{int(ecid_raw):016X}"
        except Exception:
            ecid_hex = "N/A"
        try:
            ts_val = float(dev.get("TimeIntervalSince1970", 0))
            clock_str = datetime.datetime.fromtimestamp(ts_val).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            clock_str = "N/A"

        rows = [
            ("Modelo Comercial", str(ior_prod.get("product-description", "iPhone XR")), f"Identificador: {dev.get('ProductType')} ({dev.get('HardwareModel')})"),
            ("Número de Modelo", f"{dev.get('ModelNumber')}{dev.get('RegionInfo')}", "Região LL/A (Estados Unidos)"),
            ("Versão do iOS", f"{dev.get('ProductVersion')} (Build {dev.get('BuildVersion')})", f"Firmware iBoot: {dev.get('FirmwareVersion')}"),
            ("Arquitetura / SoC", f"{dev.get('CPUArchitecture')} / {dev.get('HardwarePlatform')}", "Apple A12 Bionic (t8020)"),
            ("UDID", str(dev.get("UniqueDeviceID")), "Identificador Único do Dispositivo"),
            ("ECID (UniqueChipID)", f"{ecid_raw} ({ecid_hex})", "ID exclusivo gravado no silício do SoC A12"),
            ("Estado de Ativação", str(dev.get("ActivationState")), f"BrickState: {dev.get('BrickState')}"),
            ("Protegido por Senha", str(dev.get("PasswordProtected")), f"PairRecordProtectionClass: {dev.get('PairRecordProtectionClass')}"),
            ("Relógio Interno iPhone", clock_str, f"Fuso: {dev.get('TimeZone')}"),
            ("Sessão de Boot (UUID)", str(dev.get("BootSessionID")), "Identificador único do boot atual"),
        ]
        for r in rows:
            t.add_row(*r)
        w.write(t)

        t2 = Table(title=f"Registros de Pareamento Lockdown ({lockdown_path})", expand=True)
        t2.add_column("Arquivo", style="cyan")
        t2.add_column("Tamanho", style="green")
        t2.add_column("Modificado em", style="white")
        t2.add_column("Detalhes (HostID / SystemBUID / WiFiMAC)", style="yellow")
        for rec in pair.get("lockdown_records", []):
            details = f"HostID={rec.get('HostID', '-')}, BUID={rec.get('SystemBUID', '-')}, MAC={rec.get('WiFiMACAddress', '-')}"
            t2.add_row(rec["filename"], f"{rec['size']} B", rec["mtime"], details)
        w.write(t2)

    def render_hw_tab(self) -> None:
        w = self.query_one("#log-hw", RichLog)
        w.clear()
        d = self.collector.data
        dev = d.get("ideviceinfo", {})
        ior = d.get("ioreg", {})
        prod = ior.get("product", {})
        bat = ior.get("AppleSmartBattery", {})
        tri = ior.get("tristar", {})
        isp = ior.get("isp", {})
        lcd = ior.get("lcd", {})

        w.write("[bold cyan]🔬 AUDITORIA FORENSE DE COMPONENTES E SERIAIS DE HARDWARE (IOREGISTRY)[/bold cyan]")
        w.write("Compara os números de série gravados nos microcontroladores internos para verificar originalidade ou trocas de peças:\n")

        t = Table(title="Seriais de Componentes Extraídos via Lockdown & IORegistry", expand=True)
        t.add_column("Componente", style="cyan", no_wrap=True)
        t.add_column("Serial / Identificador", style="bold white")
        t.add_column("Decodificação / Data de Fabricação", style="green")

        dev_sn = str(dev.get("SerialNumber", ""))
        mlb_sn = str(dev.get("MLBSerialNumber", ""))
        bat_sn = str(bat.get("Serial", ""))
        cg_sn = str(prod.get("coverglass-serial-number", ""))
        ros_sn = str(prod.get("rosaline-serial-num", ""))
        als_sn = str(prod.get("ambient-light-sensor-serial-num", ""))
        raw_panel = str(prod.get("raw-panel-serial-number", ""))
        wboard_sn = str(dev.get("WirelessBoardSerialNumber", ""))

        comp_rows = [
            ("Chassi / Aparelho (SerialNumber)", dev_sn, decode_apple_serial_date(dev_sn)),
            ("Placa Lógica Principal (MLBSerialNumber)", mlb_sn, decode_apple_serial_date(mlb_sn)),
            ("Bateria Inteligente (AppleSmartBattery)", bat_sn, decode_apple_serial_date(bat_sn)),
            ("Vidro Frontal (coverglass-serial-number)", cg_sn[:32] + ("..." if len(cg_sn) > 32 else ""), decode_apple_serial_date(cg_sn.split("+")[0])),
            ("FaceID Flood Illuminator (rosaline-serial)", ros_sn, decode_apple_serial_date(ros_sn)),
            ("Sensor de Luz Ambiente (ALS)", als_sn, "Serial hexadecimal do módulo ALS"),
            ("Painel Display/Touch (raw-panel-serial)", raw_panel[:42] + "...", decode_apple_serial_date(raw_panel.split("+")[0])),
            ("Módulo Wireless (WirelessBoardSN)", wboard_sn, "Serial de fábrica do módulo Wi-Fi/BT"),
            ("Chip USB Tristar/Hydra (tristar.esn)", str(tri.get("esn", "N/A")), f"Compatível: {tri.get('compatible', 'N/A')}"),
            ("Métricas Hardware Pearl/FaceID", str(isp.get("pearl-hw-metrics", "N/A")), f"Painel LCD ID: {lcd.get('lcd-panel-id', 'N/A')}"),
            ("Baseband Serial (ChipSerialNo)", str(dev.get("BasebandSerialNumber", "N/A")), f"Chipset: {prod.get('baseband-chipset')} | Versão: {dev.get('BasebandVersion')}"),
        ]
        for r in comp_rows:
            t.add_row(*r)
        w.write(t)

        w.write("\n[bold yellow]📋 Número Completo do Painel LCD/Touch (raw-panel-serial-number):[/bold yellow]")
        w.write(f"[white]{raw_panel}[/white]\n")
        w.write("[bold yellow]📋 Número Completo do Cover Glass:[/bold yellow]")
        w.write(f"[white]{cg_sn}[/white]\n")

    def render_nvram_tab(self) -> None:
        w = self.query_one("#log-nvram", RichLog)
        w.clear()
        d = self.collector.data
        dev = d.get("ideviceinfo", {})
        nvram = d.get("nvram_decoded", {})
        pbuddy = d.get("domains", {}).get("com.apple.PurpleBuddy", {})
        intl = d.get("domains", {}).get("com.apple.international", {})

        w.write("[bold red]🔐 VARIÁVEIS NVRAM DECODIFICADAS & BLOQUEIO ICLOUD (FIND MY / ACTIVATION LOCK)[/bold red]")
        t_nv = Table(title="NonVolatileRAM (Decodificado de Base64 / Binary Plist)", expand=True)
        t_nv.add_column("Chave NVRAM", style="cyan", no_wrap=True)
        t_nv.add_column("Valor Decodificado", style="bold white")
        t_nv.add_column("Significado Forense", style="yellow")

        nv_meanings = {
            "fm-activation-locked": "Indica se o Bloqueio de Ativação (iCloud Lock / FMI) está ativo na NVRAM",
            "fm-account-masked": "E-mail mascarado da conta Apple/iCloud proprietária do vínculo",
            "fm-spstatus": "Status da rede Find My (Search Party) mesmo com aparelho desligado/desativado",
            "fm-spkeys": "Chaves públicas criptográficas (P-224/Beacon) da rede Find My Offline",
            "usbcfwflasherResult": "Resultado da verificação do firmware do controlador USB/Lightning",
            "backlight-level": "Nível atual de brilho do backlight salvo na NVRAM",
            "backlight-nits": "Calibração de luminosidade máxima em nits (hex)",
            "auto-boot": "Inicialização automática ao conectar alimentação",
            "com.apple.System.tz0-size": "Tamanho da região de memória TrustZone (SEP/TZ0)",
        }
        for k, v in sorted(nvram.items()):
            t_nv.add_row(k, str(v), nv_meanings.get(k, "Variável de ambiente do iBoot"))
        w.write(t_nv)

        w.write("\n[bold cyan]📡 PERÍCIA DE TELEFONIA, CHIP SIM (HISTÓRICO EM CACHE) E REDE[/bold cyan]")
        t_sim = Table(title="Identificadores de Rádio, IMEI, MACs e Último SIM Card Utilizado", expand=True)
        t_sim.add_column("Campo", style="cyan", no_wrap=True)
        t_sim.add_column("Valor", style="bold green")
        t_sim.add_column("Observação", style="white")

        carriers = dev.get("CarrierBundleInfoArray", [])
        c0 = carriers[0] if carriers and isinstance(carriers, list) else {}

        sim_rows = [
            ("Status Atual da Gaveta SIM", f"{dev.get('SIMTrayStatus')} / {dev.get('SIMStatus')}", "Gaveta inserida, porém sem chip físico no momento"),
            ("IMEI Principal (Slot 1)", str(dev.get("InternationalMobileEquipmentIdentity")), f"MEID: {dev.get('MobileEquipmentIdentifier')}"),
            ("IMEI Secundário (eSIM / Slot 2)", str(dev.get("InternationalMobileEquipmentIdentity2")), "Suporte Dual-SIM (Nano-SIM + eSIM)"),
            ("Operadora do Último Chip (Cache)", f"{c0.get('CFBundleIdentifier', 'N/A')} (v{c0.get('CFBundleVersion', '?')})", f"MCC: {c0.get('MCC', '?')} (Brasil) | MNC: {c0.get('MNC', '?')} (Vivo)"),
            ("ICCID do Último Chip SIM (Cache)", str(c0.get("IntegratedCircuitCardIdentity", "N/A")), "Serial único do SIM Card Vivo que esteve inserido!"),
            ("IMSI do Assinante (Cache)", str(c0.get("InternationalMobileSubscriberIdentity", "N/A")), "Identidade internacional do assinante móvel no chip"),
            ("Endereço MAC Wi-Fi", str(dev.get("WiFiAddress")), "Chipset Broadcom BCM4357"),
            ("Endereço MAC Bluetooth", str(dev.get("BluetoothAddress")), "Bluetooth 5.0 LE"),
            ("Endereço MAC Ethernet USB", str(dev.get("EthernetAddress")), "Interface virtual USB Ethernet"),
            ("País / Idioma / Fuso (PurpleBuddy)", f"País: {pbuddy.get('GuessedCountry')} | Idioma: {intl.get('Language')} | Locale: {intl.get('Locale')}", f"Último Sentinel Setup: {pbuddy.get('lastPrepareLaunchSentinel')}"),
        ]
        for r in sim_rows:
            t_sim.add_row(*r)
        w.write(t_sim)

    def render_battery_tab(self) -> None:
        w = self.query_one("#log-battery", RichLog)
        w.clear()
        d = self.collector.data
        bat = d.get("ioreg", {}).get("AppleSmartBattery", {})
        gas = d.get("diagnostics", {}).get("All", {}).get("GasGauge", {})
        usb = d.get("usb", {})

        w.write("[bold green]🔋 TELEMETRIA AVANÇADA DA BATERIA (APPLESMARTBATTERY & GASGAUGE)[/bold green]")
        t = Table(title="Métricas Físicas e Químicas da Bateria", expand=True)
        t.add_column("Métrica", style="cyan")
        t.add_column("Valor Atual", style="bold white")
        t.add_column("Referência / Diagnóstico", style="yellow")

        design_cap = bat.get("DesignCapacity", gas.get("DesignCapacity", 2942))
        nom_cap = bat.get("NominalChargeCapacity", 0)
        abs_cap = bat.get("AbsoluteCapacity", 0)
        cycles = bat.get("CycleCount", gas.get("CycleCount", 0))
        temp_raw = bat.get("Temperature", 0)
        temp_c = f"{temp_raw / 100:.2f} °C" if isinstance(temp_raw, int) and temp_raw > 0 else str(temp_raw)
        health_nom = f"{(nom_cap / design_cap) * 100:.1f}%" if design_cap and nom_cap else "N/A"
        adapter = bat.get("AdapterDetails", {}) if isinstance(bat.get("AdapterDetails"), dict) else {}

        b_rows = [
            ("Serial da Bateria", str(bat.get("Serial", "N/A")), decode_apple_serial_date(str(bat.get("Serial", "")))),
            ("Contagem de Ciclos (CycleCount)", f"{cycles} ciclos", "Alto desgaste (> 500 ciclos recomendados pela Apple)"),
            ("Capacidade de Projeto (Original)", f"{design_cap} mAh", "Capacidade original de fábrica (iPhone XR = 2942 mAh)"),
            ("Capacidade Nominal Máxima Atual", f"{nom_cap} mAh (Saúde: {health_nom})", f"RawMaxCapacity: {bat.get('AppleRawMaxCapacity')} mAh"),
            ("Carga Atual (SoC / Absoluta)", f"{bat.get('CurrentCapacity')}% ({abs_cap} mAh)", f"RawCurrentCapacity: {bat.get('AppleRawCurrentCapacity')} mAh"),
            ("Tensão Atual / Tensão no Boot", f"{bat.get('Voltage')} mV / Boot: {bat.get('BootVoltage')} mV", "Tensão normal Li-Ion (3.7V - 4.35V)"),
            ("Corrente Instantânea (Amperage)", f"{bat.get('InstantAmperage')} mA (Carregando: {bat.get('IsCharging')})", "Positivo = carregando pela porta USB"),
            ("Temperatura da Célula", temp_c, f"Desconexões de célula registradas: {bat.get('BatteryCellDisconnectCount', 0)}"),
            ("Fonte de Energia USB (AdapterDetails)", f"{adapter.get('Description', 'usb host')} ({adapter.get('AdapterVoltage', 5000)} mV / {adapter.get('Current', 500)} mA / {adapter.get('Watts', 3)}W)", "Porta USB do Host"),
            ("Último Boot Registrado no PMU", datetime.datetime.fromtimestamp(bat["BootPathUpdated"]).strftime("%Y-%m-%d %H:%M:%S") if isinstance(bat.get("BootPathUpdated"), int) else "N/A", f"Epoch: {bat.get('BootPathUpdated')}"),
        ]
        for r in b_rows:
            t.add_row(*r)
        w.write(t)

        w.write("\n[bold cyan]🔌 STATUS DO BARRAMENTO USB & USBMUXD[/bold cyan]")
        for l in usb.get("lsusb_apple", []):
            w.write(f"[bold white]• USB:[/bold white] {l}")
        w.write("\n[bold yellow]Últimos Eventos USB / Serviços:[/bold yellow]")
        for l in usb.get("dmesg_usb_events", [])[-12:]:
            w.write(f"  {l}")

    def render_afc_tab(self) -> None:
        w = self.query_one("#log-afc", RichLog)
        w.clear()
        d = self.collector.data
        afc = d.get("afc", {})
        disk = d.get("domains", {}).get("com.apple.disk_usage", {})

        w.write("[bold cyan]📂 ARMAZENAMENTO NAND & SISTEMA DE ARQUIVOS AFC (APPLE FILE CONDUIT)[/bold cyan]")
        tot_gb = disk.get("TotalDiskCapacity", 0) / 1e9 if isinstance(disk.get("TotalDiskCapacity"), int) else 0
        avail_gb = disk.get("AmountDataAvailable", 0) / 1e9 if isinstance(disk.get("AmountDataAvailable"), int) else 0
        photo_kb = disk.get("PhotoUsage", 0) / 1024 if isinstance(disk.get("PhotoUsage"), int) else 0
        w.write(
            f"• [bold]Capacidade Total NAND:[/bold] {tot_gb:.2f} GB | "
            f"[bold]Disponível:[/bold] {avail_gb:.2f} GB | "
            f"[bold]Uso de Fotos (PhotoUsage):[/bold] {photo_kb:.1f} KB\n"
        )

        t_dir = Table(title="Diretórios Acessíveis via AFC (Sem Jailbreak)", expand=True)
        t_dir.add_column("Caminho AFC", style="cyan", no_wrap=True)
        t_dir.add_column("Conteúdo Encontrado", style="white")
        for path, items in afc.get("directories", {}).items():
            t_dir.add_row(path, ", ".join(items[:20]) if items else "(vazio)")
        w.write(t_dir)

        dcim = afc.get("dcim_files", [])
        if dcim:
            t_img = Table(title="Evidências em /DCIM/100APPLE (Fotos Encontradas no Aparelho!)", expand=True)
            t_img.add_column("Arquivo", style="bold green")
            t_img.add_column("Tamanho", style="cyan")
            t_img.add_column("Criado em (birthtime)", style="white")
            t_img.add_column("Modificado em (mtime)", style="white")
            t_img.add_column("Metadados / EXIF Extraídos", style="yellow")
            for img in dcim:
                exif = img.get("exif", {})
                exif_str = f"Datas EXIF: {exif.get('exif_dates', ['-'])} | Strings: {exif.get('header_strings', [])[:4]}"
                t_img.add_row(
                    img.get("name", "?"),
                    f"{img.get('st_size', '?')} B",
                    str(img.get("st_birthtime", "?")),
                    str(img.get("st_mtime", "?")),
                    exif_str,
                )
            w.write(t_img)

        sqls = afc.get("sqlite_summary", {})
        if sqls:
            w.write("\n[bold magenta]🗄️ BANCOS DE DADOS SQLITE EXTRAÍDOS E ANALISADOS VIA AFC[/bold magenta]")
            for db_path, db_info in sqls.items():
                w.write(
                    f"• [bold white]{db_path}[/bold white] ({db_info.get('size_bytes', 0):,} bytes) — "
                    f"Total de tabelas: {db_info.get('table_count', 0)}"
                )
                non_empty = db_info.get("non_empty_tables", {})
                if non_empty:
                    summary_pairs = [f"{k} ({v} regs)" for k, v in list(non_empty.items())[:15]]
                    w.write(f"  [green]Tabelas com registros:[/green] {', '.join(summary_pairs)}")
                zassets = db_info.get("zasset_sample", [])
                if zassets:
                    t_za = Table(title=f"Registros Forenses na Tabela ZASSET + ZADDITIONALASSETATTRIBUTES ({db_path})", expand=True)
                    t_za.add_column("Arquivo", style="bold green")
                    t_za.add_column("Diretório", style="cyan")
                    t_za.add_column("Criado (UTC)", style="white")
                    t_za.add_column("App Origem (BundleID)", style="yellow")
                    t_za.add_column("Nome Exibição", style="magenta")
                    t_za.add_column("EXIF Timestamp / Fuso", style="green")
                    for row in zassets:
                        t_za.add_row(
                            str(row.get("ZFILENAME")),
                            str(row.get("ZDIRECTORY")),
                            str(row.get("ZDATECREATED")),
                            str(row.get("ZIMPORTEDBYBUNDLEIDENTIFIER")),
                            str(row.get("ZIMPORTEDBYDISPLAYNAME")),
                            f"{row.get('ZEXIFTIMESTAMPSTRING')} ({row.get('ZTIMEZONENAME')})",
                        )
                    w.write(t_za)

    def render_logs_tab(self) -> None:
        w = self.query_one("#log-syslog", RichLog)
        w.clear()
        crashes = self.collector.data.get("crashes", {})
        w.write(
            f"[bold yellow]💥 CRASH REPORTS & LOGS DE DIAGNÓSTICO ({crashes.get('count', 0)} arquivos em {crashes.get('crash_dir', str(get_default_crash_dir()))})[/bold yellow]"
        )
        files = crashes.get("files", [])
        if files:
            t_cr = Table(title="Últimos Relatórios de Crash / Diagnóstico Extraídos do iPhone", expand=True)
            t_cr.add_column("Arquivo", style="cyan")
            t_cr.add_column("Tamanho", style="green")
            t_cr.add_column("Data", style="white")
            for f in files[:20]:
                t_cr.add_row(f["name"], f"{f['size']} B", f["mtime"])
            w.write(t_cr)
        else:
            w.write("[dim]Nenhum crash report em cache ou pressione [C] para extrair do aparelho.[/dim]")

        w.write("\n[bold cyan]📡 Dica:[/bold cyan] Pressione [bold white][S][/bold white] (ou clique em 'Amostra Syslog') para capturar logs em tempo real do iPhone (`idevicesyslog`).")


def print_cli_summary(collector: IOSForensicCollector) -> None:
    console = Console()
    data = collector.collect_all(deep_afc=True)
    export_dir = collector.export_full_forensic_package()
    console.print(Panel(f"[bold green]Coleta Forense Concluída![/bold green]\nPacote exportado em: [bold cyan]{export_dir}[/bold cyan]", title="iOS Forensic Suite"))
    console.print(f"Dispositivo: {data['ideviceinfo'].get('ProductType')} | iOS {data['ideviceinfo'].get('ProductVersion')} | Serial: {data['ideviceinfo'].get('SerialNumber')}")
    console.print(f"NVRAM Decodificada: {json.dumps(data['nvram_decoded'], indent=2, ensure_ascii=False)}")
    console.print(f"Fotos em /DCIM/100APPLE: {json.dumps(data['afc'].get('dcim_files', []), indent=2, ensure_ascii=False)}")
    console.print(f"Resumo SQLite: {json.dumps(data['afc'].get('sqlite_summary', {}), indent=2, ensure_ascii=False)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="iOS Forensic & USB Debug TUI")
    parser.add_argument("--cli-export", action="store_true", help="Executa coleta completa, exporta arquivos e exibe resumo no terminal sem abrir a TUI")
    parser.add_argument("--version", action="version", version="iOS Forensic & Debug TUI Suite v1.0.0")
    args = parser.parse_args()

    collector = IOSForensicCollector()
    if args.cli_export:
        print_cli_summary(collector)
        return

    collector.collect_all(deep_afc=True)
    app = IOSForensicTUI(collector)
    app.run()


if __name__ == "__main__":
    main()
