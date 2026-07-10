from pathlib import Path

from scripts.check_architecture_guardrails import find_synthetic_manifest_pii
from scripts.check_gold_manifest import main as check_main
from scripts.check_repo_guardrails import classify_sensitive_paths
from scripts.evaluate_gold_manifest import main as evaluate_main


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_evaluation_scripts_run_synthetic_fixtures_safely(tmp_path, capsys) -> None:
    gold = FIXTURES / "gold_manifest_synthetic.jsonl"
    predictions = FIXTURES / "prediction_manifest_synthetic.jsonl"
    output = tmp_path / "evaluation_report.json"

    assert check_main(["--gold", str(gold)]) == 0
    assert evaluate_main(
        [
            "--gold",
            str(gold),
            "--predictions",
            str(predictions),
            "--output",
            str(output),
        ]
    ) == 0

    terminal_output = capsys.readouterr().out
    report_text = output.read_text(encoding="utf-8")
    assert "Gold manifest: PASS" in terminal_output
    assert "redacted_case_number" not in terminal_output
    assert "redacted_case_number" not in report_text
    assert '"cases_total": 1' in report_text


def test_real_gold_paths_are_protected() -> None:
    counts = classify_sensitive_paths(
        [
            "data_private/gold/gold_manifest.jsonl",
            "data/gold/gold_manifest.jsonl",
            "custom/gold_manifest.jsonl",
        ]
    )

    assert counts["protected:data_private"] == 1
    assert counts["protected:data/gold"] == 1
    assert counts["evaluation_manifest_outside_tests"] == 1


def test_architecture_guardrail_finds_pii_in_synthetic_manifest(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "tests/fixtures"
    fixture_dir.mkdir(parents=True)
    (fixture_dir / "gold_manifest_synthetic.jsonl").write_text(
        '{"review": {"notes": "contact@example.com"}}\n',
        encoding="utf-8",
    )

    findings = find_synthetic_manifest_pii(tmp_path)

    assert findings == ["tests/fixtures/gold_manifest_synthetic.jsonl: 1"]
