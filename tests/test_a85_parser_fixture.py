# uses the offline sample at tests/fixtures/a85_sample.xml
import sys, pathlib

# make src/ importable when pytest runs from repo root
sys.path.append("src")

from a85_parser import parse_a85_xml  # noqa: E402


def test_parse_sample_fixture():
    xml_path = pathlib.Path("tests/fixtures/a85_sample.xml")
    xml_text = xml_path.read_text(encoding="utf-8")

    df = parse_a85_xml(xml_text)

    assert df.shape == (4, 3)
    assert list(df["price_eur_mwh"]) == [35.12, 40.0, -5.0, 55.25]
    assert str(df["ts_utc"].iloc[0]) == "2025-01-10 00:00:00+00:00"
    assert str(df["ts_utc"].iloc[-1]) == "2025-01-10 00:45:00+00:00"
