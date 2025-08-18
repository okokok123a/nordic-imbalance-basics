import sys
import subprocess

def _run_dry(area: str) -> str:
    cmd = [
        sys.executable,
        "src/fetch_da_entsoe.py",
        "--area", area,
        "--start", "2025-05-10",
        "--end", "2025-05-13",
        "--out", f"data/DA_{area}_API.parquet",
        "--dry-run",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return r.stdout

def test_se3_dry_run_url():
    out = _run_dry("SE3")
    assert "DRY-RUN URL:" in out
    assert "documentType=A44" in out
    assert "processType=A01" in out
    assert "in_Domain=10Y1001A1001A46L" in out
    assert "periodStart=202505100000" in out
    assert "periodEnd=202505130000" in out

def test_se4_dry_run_url():
    out = _run_dry("SE4")
    assert "DRY-RUN URL:" in out
    assert "in_Domain=10Y1001A1001A47J" in out
