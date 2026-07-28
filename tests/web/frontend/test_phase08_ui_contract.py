from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
WEB = ROOT / "apps" / "web"
FEATURES = WEB / "features"
COMPONENTS = WEB / "components"

EXPECTED_NAVIGATION = (
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

BUSINESS_ROUTES = (
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


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _feature_source(name: str) -> str:
    return _read(FEATURES / name / "index.tsx")


def test_sidebar_contains_exactly_ten_items() -> None:
    source = _read(WEB / "lib" / "navigation.ts")
    assert len(re.findall(r'\{\s*label:\s*"', source)) == 10


def test_sidebar_item_order_is_the_approved_order() -> None:
    source = _read(WEB / "lib" / "navigation.ts")
    positions = [source.index(f'label: "{label}"') for label, _ in EXPECTED_NAVIGATION]
    assert positions == sorted(positions)


def test_sidebar_destinations_match_the_approved_routes() -> None:
    source = _read(WEB / "lib" / "navigation.ts")
    for label, href in EXPECTED_NAVIGATION:
        assert f'label: "{label}", href: "{href}"' in source


def test_ocr_review_is_not_a_visible_navigation_item() -> None:
    source = _read(WEB / "lib" / "navigation.ts")
    assert "Kiểm tra OCR" not in source
    assert "view=ocr" not in source


def test_sidebar_uses_lucide_navigation_icons() -> None:
    source = _read(COMPONENTS / "icons.tsx")
    sidebar = _read(COMPONENTS / "sidebar.tsx")
    assert "lucide-react" in source
    assert "<NavigationIcon" in sidebar
    assert 'aria-hidden="true"' in sidebar


def test_sidebar_marks_current_route_semantically() -> None:
    source = _read(COMPONENTS / "sidebar.tsx")
    assert 'aria-current={isActive ? "page" : undefined}' in source


def test_sidebar_width_is_compact() -> None:
    css = _read(WEB / "app" / "globals.css")
    match = re.search(r"--sidebar-width:\s*(\d+)px", css)
    assert match
    assert 250 <= int(match.group(1)) <= 280


def test_brand_copy_contains_no_phase_or_technical_jargon() -> None:
    source = _read(COMPONENTS / "sidebar.tsx")
    assert "Nền tảng dữ liệu Tòa án" in source
    assert "Hồ sơ · Dữ liệu · Biểu mẫu" in source
    assert "Phase 0" not in source
    assert "OCR" not in source
    assert "synthetic" not in source


def test_top_bar_has_one_trial_badge() -> None:
    top_bar = _read(COMPONENTS / "top-bar.tsx")
    badge = _read(COMPONENTS / "environment-badge.tsx")
    assert top_bar.count("<EnvironmentBadge") == 1
    assert badge.count("Bản thử nghiệm") == 2  # visible text + accessible label


def test_top_bar_hides_local_phase_copy() -> None:
    source = _read(COMPONENTS / "top-bar.tsx")
    assert "Môi trường local" not in source
    assert "Phase 0" not in source
    assert "Chưa chính thức" not in source


def test_top_bar_user_block_is_plain_language() -> None:
    source = _read(COMPONENTS / "user-menu-placeholder.tsx")
    assert "Người dùng thử nghiệm" in source
    assert "Vai trò:" not in source


def test_notification_control_has_accessible_name() -> None:
    source = _read(COMPONENTS / "top-bar.tsx")
    assert 'aria-label="Xem thông báo"' in source
    assert "<Bell" in source


def test_primary_font_is_windows_safe_system_stack() -> None:
    css = _read(WEB / "app" / "globals.css")
    assert '"Segoe UI", "Noto Sans", Arial, sans-serif' in css
    assert "Inter" not in css
    assert "next/font" not in css


def test_body_typography_meets_vietnamese_readability_floor() -> None:
    css = _read(WEB / "app" / "globals.css")
    assert "font-size: 16px;" in css
    assert "line-height: 1.56;" in css


def test_heading_scale_is_balanced() -> None:
    css = _read(WEB / "app" / "globals.css")
    assert "font-size: clamp(38px, 3.1vw, 44px);" in css
    assert "font-size: clamp(24px, 2vw, 28px);" in css


def test_letter_spacing_is_not_excessive() -> None:
    css = _read(WEB / "app" / "globals.css")
    values = re.findall(r"letter-spacing:\s*([0-9.]+)em", css)
    assert values
    assert all(float(value) <= 0.08 for value in values)
    assert "letter-spacing: -" not in css


def test_palette_has_no_startup_gradient_or_purple_tokens() -> None:
    css = _read(WEB / "app" / "globals.css").lower()
    for token in ("gradient(", "purple", "pink", "magenta"):
        assert token not in css


def test_shadow_and_radius_remain_restrained() -> None:
    css = _read(WEB / "app" / "globals.css")
    assert "--shadow-subtle: 0 2px 8px" in css
    assert "--radius-lg: 10px" in css
    assert "0 20px" not in css


def test_dashboard_contains_exactly_four_summary_definitions() -> None:
    source = _feature_source("dashboard")
    summary_block = source.split("const SUMMARY_ITEMS =", 1)[1].split(
        "] as const;", 1
    )[0]
    assert summary_block.count("label:") == 4


def test_dashboard_uses_the_four_approved_status_labels() -> None:
    source = _feature_source("dashboard")
    for label in (
        "Hồ sơ mới tiếp nhận",
        "Đang xử lý",
        "Chờ kiểm tra",
        "Đã phê duyệt",
    ):
        assert f'label: "{label}"' in source
    assert "Chờ công bố" not in source
    assert "Biểu mẫu đã sinh" not in source


def test_dashboard_has_one_illustrative_data_note() -> None:
    source = _feature_source("dashboard")
    assert source.count("Dữ liệu minh họa") == 1
    assert "Dữ liệu tổng hợp synthetic" not in source


def test_dashboard_heading_and_description_match_approved_copy() -> None:
    source = _feature_source("dashboard")
    assert 'title="Tổng quan"' in source
    assert (
        'description="Theo dõi hồ sơ cần xử lý và các công việc đang chờ xác nhận."'
        in source
    )


def test_dashboard_has_at_most_two_secondary_sections() -> None:
    source = _feature_source("dashboard")
    assert source.count("<SectionCard") == 2
    assert 'title="Công việc cần xử lý"' in source
    assert 'title="Lối tắt"' in source


def test_dashboard_has_one_primary_action() -> None:
    source = _feature_source("dashboard")
    assert source.count("<PrimaryAction") == 1
    assert 'label="Tiếp nhận hồ sơ"' in source


def test_placeholder_pages_expose_one_primary_action_each() -> None:
    for name in (
        "intake",
        "jobs",
        "review",
        "publishing",
        "exports",
        "forms",
        "audit",
    ):
        source = _feature_source(name)
        assert source.count("actionLabel=") == 1, name
    assert _feature_source("admin").count("actionLabel=") == 2


def test_unavailable_primary_actions_are_disabled() -> None:
    for name in (
        "intake",
        "jobs",
        "review",
        "publishing",
        "exports",
        "forms",
        "audit",
        "admin",
    ):
        assert "actionDisabled" in _feature_source(name), name


def test_empty_state_explains_the_next_step() -> None:
    component = _read(COMPONENTS / "empty-state.tsx")
    module = _read(COMPONENTS / "module-page.tsx")
    assert "Bước tiếp theo:" in component
    assert "nextStep" in module


def test_forms_capability_uses_plain_vietnamese_wording() -> None:
    source = _feature_source("forms")
    assert "Chưa hỗ trợ" in source
    assert "Đang chuẩn bị" in source
    assert "Không sử dụng kết quả làm văn bản chính thức" in source
    assert "NOT_IMPLEMENTED" not in source
    assert "DECLARED" not in source
    assert "official_generation_available" not in source


def test_non_admin_feature_copy_avoids_forbidden_jargon() -> None:
    source = "\n".join(
        _feature_source(name)
        for name in (
            "dashboard",
            "intake",
            "jobs",
            "processing",
            "review",
            "publishing",
            "exports",
            "forms",
            "audit",
        )
    ).lower()
    for token in (
        "synthetic",
        "phase 0",
        "machine output",
        "adapter",
        "backend",
        "frontend",
        "json raw",
        "technical id",
        "parser",
        "pipeline",
    ):
        assert token not in source


def test_application_shell_keeps_skip_link_and_main_landmark() -> None:
    layout = _read(WEB / "app" / "layout.tsx")
    shell = _read(COMPONENTS / "app-shell.tsx")
    assert 'className="skip-link"' in layout
    assert 'href="#main-content"' in layout
    assert "<main" in shell
    assert 'id="main-content"' in shell


def test_focus_state_is_visible() -> None:
    css = _read(WEB / "app" / "globals.css")
    assert ":focus-visible" in css
    assert "outline: 3px solid var(--focus)" in css


def test_status_badges_do_not_rely_on_color_alone() -> None:
    source = _read(COMPONENTS / "status-badge.tsx")
    assert "presentation.label" in source
    assert "STATUS_ICONS" in source
    assert "aria-label={`Trạng thái:" in source


def test_all_thirteen_business_routes_still_exist() -> None:
    missing = [
        route
        for route in BUSINESS_ROUTES
        if not (WEB / "app" / route / "page.tsx").is_file()
    ]
    assert not missing


def test_api_rewrite_contract_is_unchanged() -> None:
    config = _read(WEB / "next.config.mjs")
    assert 'source: "/api/v1/:path*"' in config
    assert "destination: `${webApiOrigin}/api/v1/:path*`" in config
    assert "127.0.0.1" in config


def test_lucide_dependency_is_exact() -> None:
    package = json.loads(_read(WEB / "package.json"))
    assert package["dependencies"]["lucide-react"] == "1.27.0"


def test_no_remote_font_or_image_source_is_declared() -> None:
    source = "\n".join(
        _read(path)
        for path in (
            *sorted((WEB / "app").rglob("*.tsx")),
            *sorted(COMPONENTS.rglob("*.tsx")),
            WEB / "app" / "globals.css",
        )
    )
    assert "next/font/google" not in source
    assert "fonts.googleapis.com" not in source
    assert "fonts.gstatic.com" not in source
    assert re.search(r"<img[^>]+https?://", source, re.IGNORECASE) is None


def test_no_official_emblem_or_logo_asset_is_claimed() -> None:
    source = "\n".join(
        _read(path)
        for path in (
            *sorted((WEB / "app").rglob("*.tsx")),
            *sorted(COMPONENTS.rglob("*.tsx")),
        )
    ).lower()
    for token in ("quốc huy", "official emblem", "official-logo", "court-logo"):
        assert token not in source
