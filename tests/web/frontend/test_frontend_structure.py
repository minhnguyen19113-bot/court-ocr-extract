from __future__ import annotations

import json
import re
from pathlib import Path

from court_ocr_extract.final_excel_schema import FINAL_EXCEL_COLUMNS


ROOT = Path(__file__).resolve().parents[3]
WEB = ROOT / "apps" / "web"

REQUIRED_ROUTES = (
    "dashboard",
    "intake",
    "jobs",
    "jobs/[jobId]",
    "review",
    "review/[reviewId]",
    "publishing",
    "exports",
    "forms",
    "forms/[formId]",
    "audit",
    "admin",
    "help",
)

SIDEBAR_ITEMS = (
    ("Tổng quan", "/dashboard"),
    ("Tiếp nhận hồ sơ", "/intake"),
    ("Xử lý hồ sơ", "/jobs"),
    ("Kiểm tra dữ liệu", "/review"),
    ("Phê duyệt", "/publishing"),
    ("Kết quả và xuất file", "/exports"),
    ("Biểu mẫu", "/forms"),
    ("Nhật ký", "/audit"),
    ("Quản trị hệ thống", "/admin"),
    ("Hướng dẫn sử dụng", "/help"),
)

GENERATED_FRONTEND_DIRECTORIES = {"node_modules", ".next", "coverage"}


def _source_files() -> list[Path]:
    return sorted(
        path
        for path in (*WEB.rglob("*.ts"), *WEB.rglob("*.tsx"))
        if not GENERATED_FRONTEND_DIRECTORIES.intersection(
            path.relative_to(WEB).parts
        )
    )


def _read_sources(paths: list[Path] | None = None) -> str:
    return "\n".join(
        path.read_text(encoding="utf-8") for path in (paths or _source_files())
    )


def test_package_versions_are_exact_and_never_latest() -> None:
    package = json.loads((WEB / "package.json").read_text(encoding="utf-8"))
    dependencies = {
        **package.get("dependencies", {}),
        **package.get("devDependencies", {}),
    }

    assert dependencies
    for name, version in dependencies.items():
        assert version != "latest", name
        assert re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", version), (
            name,
            version,
        )
    assert package["packageManager"] == "npm@11.16.0"
    assert package["engines"]["node"] == "^20.19.0 || ^22.13.0 || >=24"
    assert package["engines"]["npm"] == ">=11.16.0"
    assert package["scripts"]["test"] == "vitest run"
    assert package["scripts"]["typecheck"] == "tsc --noEmit"
    assert package["scripts"]["lint"] == "eslint . --max-warnings=0"


def test_required_application_shell_and_route_files_exist() -> None:
    required_files = {
        WEB / "app" / "layout.tsx",
        WEB / "components" / "app-shell.tsx",
        WEB / "components" / "sidebar.tsx",
        WEB / "components" / "status-badge.tsx",
        WEB / "lib" / "api" / "system.ts",
    }
    required_files.update(WEB / "app" / route / "page.tsx" for route in REQUIRED_ROUTES)

    assert not {path.relative_to(ROOT) for path in required_files if not path.is_file()}


def test_sidebar_has_all_ten_labels_and_destinations() -> None:
    source = (WEB / "lib" / "navigation.ts").read_text(encoding="utf-8")

    assert len(re.findall(r"""label:\s*["']""", source)) == 10
    for label, route in SIDEBAR_ITEMS:
        assert label in source
        assert route in source
    assert "Kiểm tra OCR" not in source


def test_frontend_does_not_duplicate_backend_schema_or_import_parsers() -> None:
    source_by_file = {
        path: path.read_text(encoding="utf-8") for path in _source_files()
    }
    forbidden = (
        "data/raw_pdfs",
        "data/private_pdfs",
        "outputs/",
        "node:fs",
        'from "fs"',
        "court_ocr_extract",
        "sentence_parser",
        "charge_parser",
        "extractors/",
    )

    for path, source in source_by_file.items():
        assert not all(column in source for column in FINAL_EXCEL_COLUMNS), path
        for token in forbidden:
            assert token not in source, (path, token)


def test_api_clients_use_only_the_v1_http_contract() -> None:
    api_files = sorted((WEB / "lib" / "api").glob("*.ts"))
    source = _read_sources(api_files)

    assert api_files
    assert "/api/v1" in source
    for match in re.findall(r'["\'](/api/[^"\']+)', source):
        assert match == "/api/v1" or match.startswith("/api/v1/"), match

    non_api_sources = [
        path
        for path in _source_files()
        if "tests" not in path.parts and (WEB / "lib" / "api") not in path.parents
    ]
    assert not [
        path.relative_to(ROOT)
        for path in non_api_sources
        if re.search(r"\bfetch\s*\(", path.read_text(encoding="utf-8"))
    ]


def test_local_api_rewrite_uses_server_side_loopback_origin() -> None:
    config = (WEB / "next.config.mjs").read_text(encoding="utf-8")
    client = (WEB / "lib" / "api" / "client.ts").read_text(encoding="utf-8")
    environment = (ROOT / ".env.web.example").read_text(encoding="utf-8")

    assert 'process.env.WEB_API_ORIGIN ?? "http://127.0.0.1:8000"' in config
    assert 'source: "/api/v1/:path*"' in config
    assert "destination: `${webApiOrigin}/api/v1/:path*`" in config
    assert "NEXT_PUBLIC_WEB_API_ORIGIN" not in config
    assert "NEXT_PUBLIC_API_BASE_URL" in client
    assert "FRONTEND_API_BASE_URL" not in client
    assert "WEB_API_ORIGIN=http://127.0.0.1:8000" in environment
    assert "NEXT_PUBLIC_API_BASE_URL=/api/v1" in environment


def test_forms_page_exposes_plain_language_capability_warnings() -> None:
    form_sources = [
        path
        for path in _source_files()
        if "forms" in path.parts or path.name in {"FormCapabilities.tsx", "FormsPage.tsx"}
    ]
    source = _read_sources(form_sources)

    assert "NOT_IMPLEMENTED" not in source
    assert "DECLARED" not in source
    assert re.search(r"chưa hỗ trợ|đang chuẩn bị", source, re.IGNORECASE)
    assert re.search(r"loại bỏ.{0,80}hướng dẫn", source, re.IGNORECASE | re.DOTALL)


def test_navigation_and_focus_accessibility_foundation() -> None:
    shell_source = _read_sources(
        [
            WEB / "components" / "app-shell.tsx",
            WEB / "components" / "sidebar.tsx",
            WEB / "components" / "status-badge.tsx",
        ]
    )
    css_source = _read_sources(sorted(WEB.rglob("*.css")))

    assert "<nav" in shell_source
    assert "aria-label" in shell_source
    assert "<main" in shell_source
    assert ":focus-visible" in css_source
