from pathlib import Path

from court_ocr_extract.evaluation.report import build_safe_report, write_report


def test_report_whitelists_metrics_and_never_writes_raw_values(tmp_path: Path) -> None:
    metrics = {
        "cases_total": 1,
        "field_exact_match_rate": 1.0,
        "raw_expected_value": "private_raw_value",
    }

    report = build_safe_report(metrics)
    json_path = write_report(report, tmp_path / "report.json")
    markdown_path = write_report(report, tmp_path / "report.md")

    assert "raw_expected_value" not in report
    assert "private_raw_value" not in json_path.read_text(encoding="utf-8")
    assert "private_raw_value" not in markdown_path.read_text(encoding="utf-8")
    assert "field_exact_match_rate" in json_path.read_text(encoding="utf-8")
