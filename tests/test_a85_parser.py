# tests/test_a85_parser.py
# Offline unit test for A85 XML parser

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from fetch_imbalance_entsoe import parse_a85  # type: ignore
import pandas as pd


def test_parse_a85_minimal_xml():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <GL_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0">
      <TimeSeries>
        <Period>
          <timeInterval>
            <start>2025-08-15T00:00Z</start>
            <end>2025-08-15T01:00Z</end>
          </timeInterval>
          <resolution>PT15M</resolution>
          <Point>
            <position>1</position>
            <price.amount>10.5</price.amount>
          </Point>
          <Point>
            <position>2</position>
            <price.amount>20.0</price.amount>
          </Point>
          <Point>
            <position>3</position>
            <price.amount>30.0</price.amount>
          </Point>
          <Point>
            <position>4</position>
            <price.amount>40.0</price.amount>
          </Point>
        </Period>
      </TimeSeries>
    </GL_MarketDocument>
    """
    df = parse_a85(xml)
    # shape and columns
    assert list(df.columns) == ["ts_utc", "imbalance_price_eur_mwh"]
    assert len(df) == 4
    # tz-awareness
    assert pd.DatetimeIndex(df["ts_utc"]).tz is not None
    # first two timestamps spaced by 15 minutes
    assert (df.loc[1, "ts_utc"] - df.loc[0, "ts_utc"]).total_seconds() == 900
    # values
    assert df.loc[0, "imbalance_price_eur_mwh"] == 10.5
    assert df.loc[3, "imbalance_price_eur_mwh"] == 40.0
