# Gold Dataset Guide

Last updated: 2026-07-10

## Mục tiêu

Gold dataset dùng để đánh giá chất lượng thật, nhưng không được đưa vào Codex hoặc Git. Project Owner tạo, lưu, và chạy ngoài Codex trên môi trường kiểm soát.

Real manifest gợi ý: `data_private/gold/gold_manifest.jsonl`. Toàn bộ `data_private/` và `data/gold/` được guardrail coi là protected; không commit và Codex không inspect.

## Nội dung tối thiểu

| Thành phần | Ghi chú |
| --- | --- |
| PDF source | Lưu ngoài Git, không chia sẻ vào Codex. |
| Case metadata | ID nội bộ đã pseudonymize nếu cần. |
| OCR review labels | Page/line sample, text expected, bbox expected nếu có. |
| Extraction labels | Field expected, participant rows, evidence source. |
| QA expected | Warning expected, rows needing review. |

## Quy tắc bảo mật

- Không dùng tên thật, địa chỉ, CCCD/CMND, case detail thật trong issue/report gửi Codex.
- Nếu cần gửi lỗi cho Codex, tạo synthetic reproduction.
- Gold labels nên có mã case nội bộ không suy ngược được danh tính.
- Không commit PDF, OCR cache, image, Excel, QA output thật.

## Quy trình tạo gold dataset

1. Project Owner chọn sample đại diện theo loại PDF, độ dài, chất lượng scan, dấu đỏ, layout.
2. Render/OCR trên Ezycloudx ngoài Codex.
3. Reviewer gắn nhãn line/field/evidence trong file quản trị riêng.
4. Chạy evaluation script ngoài Codex.
5. Chỉ đưa summary đã redact vào repo docs nếu cần.

## Schema gợi ý cho labels

```json
{
  "case_id": "gold_001",
  "page": 1,
  "field": "participant_name",
  "expected_value": "<redacted-or-internal>",
  "evidence_line_ids": ["p001_l0001"],
  "notes": "redacted reviewer note"
}
```

## JSONL contract TOOLKIT-1

Mỗi gold record có các nhóm bắt buộc:

- Safe identity: `case_id_hash`, `file_hash`, `source_type`, `split`.
- Document: `page_count`, `document_tags`, `expected_sections`.
- Labels: `expected_fields`, `expected_participants`.
- Review: `reviewer`, `review_status`, `notes` trong `review`.

Field label dùng `expected_value` đã redact/hash, `source_page`, `source_line_ids`, `evidence_text_redacted`, và `required`. Participant không lưu tên thật; dùng `name_hash`, role, redacted fields và source references.

Prediction record ghi run/backend/model/prompt version, OCR aggregate counts, predicted sections/fields/participants, warnings và `needs_review`.

Fixture được commit:

- `tests/fixtures/gold_manifest_synthetic.jsonl`
- `tests/fixtures/prediction_manifest_synthetic.jsonl`

Trước khi dùng manifest thật ngoài Codex:

1. Project Owner review thủ công mọi value/evidence/note.
2. Chạy `scripts.check_gold_manifest` trên môi trường kiểm soát.
3. Chạy evaluation và chỉ chia sẻ aggregate report đã redact.
4. Không dùng việc guardrail pass làm bảo đảm manifest đã ẩn danh hoàn toàn.
