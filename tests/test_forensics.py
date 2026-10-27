import base64
import os
import plistlib
import sqlite3
from pathlib import Path
from unittest.mock import patch

from ios_forensics_tui import (
    IOSForensicCollector,
    configure_runtime_environment,
    decode_apple_serial_date,
    get_default_crash_dir,
    get_default_export_base_dir,
    get_lockdown_dir,
    parse_jpeg_exif_basic,
    print_cli_summary,
    run_cmd,
)


def test_decode_apple_serial_12char() -> None:
    # 12-char device serial (e.g. F2LX12345678 -> Factory F2L, X = 2018 H2, 1 = week 27)
    res = decode_apple_serial_date("F2LX12345678")
    assert "Fábrica: F2L" in res
    assert "Ano: 2018" in res


def test_decode_apple_serial_17char() -> None:
    # 17-char component serial (MLB/Battery)
    res = decode_apple_serial_date("F8Y845626XEJKGTAR")
    assert "Fábrica: F8Y" in res
    assert "2018" in res
    assert "Semana: 45" in res


def test_decode_apple_serial_empty_or_proprietary() -> None:
    assert decode_apple_serial_date("") == "N/A"
    assert decode_apple_serial_date("RANDOMSERIAL10") == "Formato proprietário"


def test_parse_jpeg_exif_basic() -> None:
    sample = b"\xff\xd8\xff\xe1Apple iPhone XR 2024:10:15 14:22:33 iOS 17.5"
    res = parse_jpeg_exif_basic(sample)
    assert res["size_bytes"] == len(sample)
    assert "2024:10:15 14:22:33" in res.get("exif_dates", [])
    assert any("Apple" in s for s in res.get("header_strings", []))


def test_decode_nvram_base64_and_bplist() -> None:
    collector = IOSForensicCollector()
    bplist_bytes = plistlib.dumps({"status": "active", "blob": b"\x01\x02\x03\x04"}, fmt=plistlib.FMT_BINARY)
    fake_devinfo = {
        "NonVolatileRAM": {
            "auto-boot": base64.b64encode(b"true").decode("ascii"),
            "fm-spstatus": bplist_bytes,
            "raw-hex": b"\xff\x00\xfe",
        }
    }
    decoded = collector.decode_nvram(fake_devinfo)
    assert decoded["auto-boot"] == "true"
    assert "[Binary Plist]" in decoded["fm-spstatus"]
    assert decoded["raw-hex"] == "hex:ff00fe"


def test_cross_platform_paths() -> None:
    assert isinstance(get_lockdown_dir(), Path)
    assert isinstance(get_default_crash_dir(), Path)
    export_base = get_default_export_base_dir()
    assert isinstance(export_base, str)
    assert len(export_base) > 0


def test_configure_runtime_environment() -> None:
    configure_runtime_environment()
    assert "PATH" in os.environ


def test_run_cmd_success_and_failures() -> None:
    code, stdout, _stderr = run_cmd(["echo", "ios_forensics"])
    assert code == 0
    assert b"ios_forensics" in stdout

    # Test timeout
    code_t, _out_t, _err_t = run_cmd(["sleep", "2"], timeout=1)
    assert code_t == 124

    # Test missing command
    code_m, _out_m, _err_m = run_cmd(["non_existent_binary_12345"])
    assert code_m == 1


def test_collect_pairing_and_lockdown_with_tempdir(tmp_path: Path) -> None:
    collector = IOSForensicCollector()
    lockdown_dir = tmp_path / "lockdown"
    lockdown_dir.mkdir()
    plist_file = lockdown_dir / "test_udid.plist"
    plist_content = {"HostID": "test-host-id-1234", "SystemBUID": "test-buid-5678"}
    plist_file.write_bytes(plistlib.dumps(plist_content))

    with patch("ios_forensics_tui.get_lockdown_dir", return_value=lockdown_dir), \
         patch("ios_forensics_tui.run_cmd", return_value=(0, b"test_udid\n", b"")):
        pinfo = collector.collect_pairing_and_lockdown()
        assert "test_udid" in pinfo["connected_udids"]
        assert len(pinfo["lockdown_records"]) == 1
        assert pinfo["lockdown_records"][0]["filename"] == "test_udid.plist"
        assert pinfo["lockdown_records"][0]["HostID"] == "test-host-id-1234"


def test_collect_ideviceinfo_and_domains() -> None:
    collector = IOSForensicCollector()
    sample_plist = plistlib.dumps({"ProductType": "iPhone11,8", "SerialNumber": "F2LX12345678"})
    with patch("ios_forensics_tui.run_cmd", return_value=(0, sample_plist, b"")):
        info = collector.collect_ideviceinfo()
        assert info.get("ProductType") == "iPhone11,8"

        domains = collector.collect_domains()
        assert "com.apple.disk_usage" in domains


def test_collect_afc_and_sqlite(tmp_path: Path) -> None:
    collector = IOSForensicCollector()
    db_file = tmp_path / "Photos.sqlite"
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("CREATE TABLE ZASSET (Z_PK INTEGER PRIMARY KEY, ZFILENAME TEXT, ZDIRECTORY TEXT, ZDATECREATED REAL, ZADDEDDATE REAL);")
    cur.execute("CREATE TABLE ZADDITIONALASSETATTRIBUTES (Z_PK INTEGER PRIMARY KEY, ZIMPORTEDBYBUNDLEIDENTIFIER TEXT, ZIMPORTEDBYDISPLAYNAME TEXT, ZEXIFTIMESTAMPSTRING TEXT, ZTIMEZONENAME TEXT);")
    cur.execute("INSERT INTO ZASSET VALUES (1, 'IMG_0001.JPG', '100APPLE', 700000000.0, 700000000.0);")
    cur.execute("INSERT INTO ZADDITIONALASSETATTRIBUTES VALUES (1, 'com.apple.camera', 'Camera', '2023:03:08 12:00:00', 'UTC');")
    conn.commit()
    conn.close()

    def mock_run_cmd(cmd: list[str], timeout: int = 8) -> tuple[int, bytes, bytes]:
        if "afcclient" in cmd and "ls" in cmd:
            return 0, b"IMG_0001.JPG\n", b""
        if "afcclient" in cmd and "info" in cmd:
            return 0, b"st_mtime: 1678276800000000000\nst_birthtime: 1678276800000000000\n", b""
        if "afcclient" in cmd and "get" in cmd:
            target = cmd[-1]
            if target.endswith((".sqlite", ".sqlitedb", ".db")):
                Path(target).write_bytes(db_file.read_bytes())
                return 0, b"", b""
            Path(target).write_bytes(b"\xff\xd8\xff\xe1Apple Test Photo 2024:01:01 10:00:00")
            return 0, b"", b""
        return 0, b"", b""

    with patch("ios_forensics_tui.run_cmd", side_effect=mock_run_cmd):
        afc = collector.collect_afc_forensics()
        assert "/DCIM" in afc["directories"]
        assert len(afc["dcim_files"]) > 0
        assert len(afc["sqlite_summary"]) > 0


def test_export_full_forensic_package(tmp_path: Path) -> None:
    collector = IOSForensicCollector()
    collector.data = {
        "timestamp": "2024-01-01T00:00:00",
        "ideviceinfo": {"UniqueDeviceID": "test_udid_12345", "ProductType": "iPhone11,8"},
        "afc": {"dcim_files": []},
    }

    def mock_run_cmd(cmd: list[str], timeout: int = 8) -> tuple[int, bytes, bytes]:
        return 0, b"", b""

    with patch("ios_forensics_tui.run_cmd", side_effect=mock_run_cmd):
        out_dir_str = collector.export_full_forensic_package(base_dir=str(tmp_path))
        out_dir = Path(out_dir_str)
        assert out_dir.exists()
        assert (out_dir / "forensic_report.json").exists()
        assert (out_dir / "manifest_sha256.txt").exists()

        manifest_content = (out_dir / "manifest_sha256.txt").read_text(encoding="utf-8")
        assert "forensic_report.json" in manifest_content


def test_print_cli_summary() -> None:
    collector = IOSForensicCollector()
    with patch.object(collector, "collect_all", return_value={
        "ideviceinfo": {"ProductType": "iPhone11,8", "ProductVersion": "17.5", "SerialNumber": "F2LX12345678"},
        "nvram_decoded": {},
        "afc": {"dcim_files": [], "sqlite_summary": {}},
    }), patch.object(collector, "export_full_forensic_package", return_value="/tmp/test_export"):
        print_cli_summary(collector)
