# Observability Plan

Last updated: 2026-07-14

## Mục tiêu

Pipeline cần đủ quan sát để reviewer biết file nào thành công, file nào cần review, lỗi ở bước nào, nhưng không log dữ liệu thật.

## Event/metric đề xuất

| Bước | Metric an toàn |
| --- | --- |
| Render | page count, DPI, blank/rotated/cropped warning count. |
| Preprocess | transform applied, before/after artifact path, warning count. |
| OCR | pages processed, OCR line count, bbox coverage, low-confidence count. |
| Marker | marker found yes/no, marker page, missing marker count. |
| Extraction | Strategy, anchor block count/type, split warning count, validator warning count, JSON valid, participant count, missing evidence count. |
| Local LLM | Preflight, model/base URL, block ID/type, context budget, request/response status, error type và duration; không log prompt/OCR text. |
| Validation | warning code counts, evidence mismatch count. |
| Excel/QA | row count, rows needing review, output path. |

## Logging rule

- Log counts, status, warning code, safe path to controlled output.
- Không log OCR text thật, tên người, địa chỉ, CCCD/CMND, hoặc full sensitive filename.
- Lỗi exception được log bằng type/message đã kiểm tra, không dump payload.

## Artifact manifest

Mỗi run production nên có manifest riêng:

- run id.
- config hash hoặc config summary an toàn.
- backend versions.
- input count, không cần full names.
- output locations.
- warning summary.
- acceptance status.

Pre-content compare phải giữ aggregate count cho `ANCHOR_BLOCKS`, `ANCHOR_WARNINGS`, số block cần repair, số LLM call thành công/lỗi và strategy. Safe log không chứa `raw_block`, raw lines hoặc extracted values.

TOOLKIT-1 prediction manifest bổ sung safe run metadata:

- `run_id`, OCR/extractor backend và version.
- model/prompt version.
- page/line/bbox/low-confidence aggregate counts.
- warning count và `needs_review` aggregate.

Evaluation report chỉ chứa metric số và không chứa expected/predicted raw values, evidence text hoặc sensitive filenames.

## Future work

- Thêm structured JSONL safe log.
- Thêm run summary HTML không chứa OCR text đầy đủ.
- Thêm warning taxonomy ổn định cho QA.
- Thêm runtime health check cho Surya/local LLM trên Ezycloudx.
- TOOLKIT-2 nối pipeline output thật với prediction manifest trên môi trường Project Owner kiểm soát.
