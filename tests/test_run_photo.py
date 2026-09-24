"""The run photo: location data leaves before the card is drawn, orientation survives, the photo
never reaches --json or --push, and the privacy control still reads the card's text."""
import os
import struct
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentgrinder import photo as ph
from agentgrinder import privacy, solocard


def _seg(marker: int, payload: bytes) -> bytes:
    return bytes([0xFF, marker]) + struct.pack(">H", len(payload) + 2) + payload


def _exif(orientation: int, gps: bool = True) -> bytes:
    """Big-endian EXIF: IFD0 with Orientation and a GPS pointer, then a GPS IFD with a latitude."""
    entries = [struct.pack(">HHIHH", 0x0112, 3, 1, orientation, 0)]
    if gps:
        entries.append(struct.pack(">HHII", 0x8825, 4, 1, 8 + 2 + 12 * 2 + 4))
    ifd0 = struct.pack(">H", len(entries)) + b"".join(entries) + struct.pack(">I", 0)
    gps_ifd = struct.pack(">H", 1) + struct.pack(">HHI4s", 0x0001, 2, 2, b"N\x00\x00\x00") + struct.pack(">I", 0)
    return b"Exif\x00\x00" + b"MM\x00\x2a" + struct.pack(">I", 8) + ifd0 + gps_ifd + b"Placeville 12.34N"


def _jpeg(orientation: int = 6) -> bytes:
    return (b"\xff\xd8"
            + _seg(0xE0, b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00")
            + _seg(0xE1, _exif(orientation))
            + _seg(0xE1, b"http://ns.adobe.com/xap/1.0/\x00<x:xmpmeta>Placeville</x:xmpmeta>")
            + _seg(0xE2, b"ICC_PROFILE\x00\x01\x01colour")
            + _seg(0xED, b"Photoshop 3.0\x00IPTC city Placeville")
            + _seg(0xFE, b"taken at the desk")
            + _seg(0xDB, b"\x00" + bytes(64))
            + b"\xff\xda" + struct.pack(">H", 8) + b"\x01\x01\x00\x00\x3f\x00" + b"\x12\x34" + b"\xff\xd9")


def test_jpeg_loses_location_camera_and_comments(tmp_path):
    f = tmp_path / "room.jpg"; f.write_bytes(_jpeg())
    out = ph.load_photo(f)
    assert out.mime == "image/jpeg"
    for private in (b"Placeville", b"12.34", b"xmpmeta", b"IPTC", b"at the desk", b"\x88\x25"):
        assert private not in out.data, private
    assert set(out.removed) == {"EXIF/XMP", "IPTC", "comment"}
    # the picture itself is untouched: colour profile, tables and scan data are all still there
    assert b"ICC_PROFILE" in out.data and out.data.endswith(b"\x12\x34\xff\xd9")


def test_portrait_orientation_survives_the_strip(tmp_path):
    f = tmp_path / "room.jpg"; f.write_bytes(_jpeg(orientation=6))
    data = ph.load_photo(f).data
    # JFIF stays first, then a one-tag EXIF that says "rotate 90" and nothing else
    assert data[2:4] == b"\xff\xe0"
    app1 = data.index(b"\xff\xe1")
    assert app1 > data.index(b"JFIF")
    (length,) = struct.unpack(">H", data[app1 + 2:app1 + 4])
    assert ph._exif_orientation(data[app1 + 4:app1 + 2 + length]) == 6
    assert length == 2 + 6 + 8 + 2 + 12 + 4


def test_upright_photo_gets_no_exif_at_all(tmp_path):
    f = tmp_path / "room.jpg"; f.write_bytes(_jpeg(orientation=1))
    assert b"\xff\xe1" not in ph.load_photo(f).data


def test_png_keeps_pixels_drops_text(tmp_path):
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + b"\x00\x00\x00\x00"
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", bytes(13)) + chunk(b"tEXt", b"Location\x00Placeville")
           + chunk(b"eXIf", b"MM\x00\x2a") + chunk(b"IDAT", b"pixels") + chunk(b"IEND", b""))
    f = tmp_path / "room.png"; f.write_bytes(png)
    out = ph.load_photo(f)
    assert b"Placeville" not in out.data and b"eXIf" not in out.data
    assert b"pixels" in out.data and out.removed == ["tEXt", "eXIf"]


def test_other_formats_are_refused(tmp_path):
    f = tmp_path / "room.heic"; f.write_bytes(b"\x00\x00\x00\x18ftypheic" + bytes(40))
    with pytest.raises(ValueError, match="only JPEG and PNG"):
        ph.load_photo(f)


@pytest.fixture
def run(tmp_path):
    from agentgrinder.solo import parse_solo
    from tests.test_coach_tools import _sitting
    return parse_solo(_sitting(tmp_path)[0], athlete="t")


def test_card_puts_the_headline_on_the_photo_and_says_it_is_declared(tmp_path, run):
    f = tmp_path / "room.jpg"; f.write_bytes(_jpeg())
    src = ph.load_photo(f).data_uri()
    html = solocard.render_solo_card(run, photo_src=src)
    assert f'<figure class="photo"><img src="{src}"' in html
    assert "Photo added by you, not measured." in html
    assert html.count("<h1") == 1
    assert html.index('class="photo"') < html.index('<article class="card fc">')


def test_card_without_photo_is_unchanged(run):
    html = solocard.render_solo_card(run)
    assert 'class="photo"' not in html and "Photo added by you" not in html


def test_privacy_control_still_reads_the_card_text_when_a_photo_is_on_it(tmp_path, monkeypatch, run):
    # if the placeholder trick skipped the scan, a leak in the TEXT would pass with a photo attached
    f = tmp_path / "room.jpg"; f.write_bytes(_jpeg())
    src = ph.load_photo(f).data_uri()
    monkeypatch.setattr(privacy, "scan_html", lambda html: [("home_path", "/Users/someone/x")])
    with pytest.raises(privacy.PrivacyLeak):
        solocard.render_solo_card(run, photo_src=src)


def test_photo_never_enters_the_run_so_json_and_push_cannot_carry_it(tmp_path, run):
    import json
    from agentgrinder.push import import_url
    before = json.dumps(run, sort_keys=True, default=str)
    f = tmp_path / "room.jpg"; f.write_bytes(_jpeg())
    solocard.render_solo_card(run, photo_src=ph.load_photo(f).data_uri())
    assert json.dumps(run, sort_keys=True, default=str) == before
    assert "base64" not in import_url(run, "http://localhost:8000")
