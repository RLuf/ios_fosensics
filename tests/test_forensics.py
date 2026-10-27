import base64
import plistlib
from pathlib import Path

from ios_forensics_tui import (
    IOSForensicCollector,
    decode_apple_serial_date,
    get_default_crash_dir,
    get_lockdown_dir,
    parse_jpeg_exif_basic,
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
