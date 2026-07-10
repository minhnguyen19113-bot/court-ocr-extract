# Privacy Redaction Plan

Last updated: 2026-07-10

## Mục tiêu

Giảm rủi ro rò rỉ dữ liệu thật trong log, report, debug UI, Excel, Git, và trao đổi với Codex/ChatGPT.

## Dữ liệu cần bảo vệ

- PDF thật và tên file nhạy cảm.
- OCR text thật.
- Ảnh render/preprocess/bbox thật.
- Tên người, địa chỉ, số CCCD/CMND, số điện thoại, tài khoản, thông tin vụ án.
- Excel/QA/debug output thật.
- Log runtime có đường dẫn hoặc snippet dữ liệu thật.

## Quy tắc trong repo

- Guardrails chỉ báo category/count cho path nhạy cảm, không in full filename.
- `data/`, `outputs/`, `logs/`, `work/` không được Codex inspect.
- `.env` không được đọc hoặc commit.
- Cloud API chỉ opt-in, disabled default.
- Report task gửi Project Owner/ChatGPT phải redact thông tin thật.

## Redaction trong log/report

| Loại thông tin | Cách xử lý |
| --- | --- |
| File path thật | Chỉ ghi category hoặc folder tổng quát. |
| OCR text | Không in full text; chỉ ghi count, line id, warning code. |
| Tên/địa chỉ/ID | Redact hoặc dùng synthetic placeholder. |
| Error runtime | Giữ exception type và module; bỏ dữ liệu payload. |
| QA summary | Chỉ aggregate counts nếu gửi vào repo. |

## Kiểm tra trước khi commit

```powershell
.\.venv\Scripts\python -B -m scripts.check_repo_guardrails
.\.venv\Scripts\python -B -m scripts.check_architecture_guardrails
git status --short
```

Nếu có real-data artifact xuất hiện trong status, không commit và cần Project Owner xử lý ngoài Codex.

## Helper TOOLKIT-1

`src/court_ocr_extract/evaluation/privacy.py` cung cấp:

- `hash_value()` cho pseudonymous deterministic ID có optional salt.
- `looks_like_pii()` cho obvious CCCD/CMND, số điện thoại Việt Nam và email.
- `redact_common_pii()` cho redaction text nhẹ.
- `find_pii_paths()` để báo JSON path mà không echo raw value.

Giới hạn bắt buộc:

- Regex không nhận diện tên người và không bảo đảm phát hiện hết địa chỉ/case detail.
- Hash không tự biến dữ liệu thành anonymous nếu input space nhỏ hoặc salt yếu.
- Project Owner phải review thủ công trước khi lưu/chia sẻ manifest.
- Gold/prediction thật không commit; chỉ synthetic fixture được phép trong `tests/fixtures/`.
