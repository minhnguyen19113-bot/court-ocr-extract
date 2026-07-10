# Gold Dataset Guide

Last updated: 2026-07-08

## Mục tiêu

Gold dataset dùng để đánh giá chất lượng thật, nhưng không được đưa vào Codex hoặc Git. Project Owner tạo, lưu, và chạy ngoài Codex trên môi trường kiểm soát.

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
