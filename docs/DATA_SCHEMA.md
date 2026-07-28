# Data Schema

Last updated: 2026-07-17

This document records target schema expectations for rebuild planning. It does not change runtime behavior.

## OCR Cache Record

Required fields:

- `case_id`
- `source_ref` or redacted source identifier
- `backend`
- `pages`
- `created_at`
- `warnings`
- `metadata`

## OCR Page

Required fields:

- `page_number`
- `text`
- `lines`
- `width`
- `height`
- `dpi`
- `warnings`

## OCR Line

Required fields:

- `line_id`
- `page_number`
- `text`
- `bbox`
- `reading_order`
- `confidence`
- `warnings`

`bbox` should use a consistent shape such as `[x0, y0, x1, y1]` in image pixel coordinates.

## Extracted Field

Required fields:

- `name`
- `value`
- `evidence`
- `source_page`
- `source_line_ids`
- `confidence`
- `warnings`
- `needs_review`

Every non-null value must have evidence unless a reviewer-approved rule says otherwise.

## Final Excel Row

`src/court_ocr_extract/final_excel_schema.py` là nguồn canonical cho đúng 14 cột final. Sheet đầu của mọi final workbook là `FINAL_EXCEL`; mỗi entity thuộc role policy hiện hành là một dòng và case metadata được lặp lại.

Không thêm `SOURCE_CASE_ID`, `SOURCE_PAGE`, `SOURCE_LINE_IDS`, OCR/extraction confidence, evidence, technical warnings hoặc `NEEDS_REVIEW` vào `FINAL_EXCEL`. Các field này thuộc debug sheets/QA report. `DATA` và `Trich xuat` là contract lịch sử trước final-schema realignment, không còn là tên sheet final.

Dữ liệu thiếu phải để trống và giải thích bằng chuỗi phẳng trong `GHI CHÚ`; không đặt JSON blob trong final row. Row chỉ được tạo cho primary role trong `final_excel_role_policy.py`; identity dedupe là `case_id + normalized_full_name + normalized_procedural_role`.

## Other Participants Row

Sheet user-facing thứ hai là `NGUOI_THAM_GIA_KHAC`, gồm đúng tám cột:

- `LOẠI ÁN`
- `SỐ THỤ LÝ`
- `TƯ CÁCH TỐ TỤNG`
- `HỌ TÊN`
- `NGƯỜI ĐƯỢC ĐẠI DIỆN/BẢO VỆ`
- `ĐỊA CHỈ`
- `TÌNH TRẠNG THAM GIA`
- `GHI CHÚ`

Sheet này giữ support roles nhưng loại court procedural roles. `PARTICIPANTS` vẫn là debug sheet đầy đủ và không bị thay thế.

## Decision Tail Cache Record

`DecisionTailRecord` là cache schema riêng, version 1, không thay đổi `OCRCacheRecord`. Các field chính:

- `case_id`, `source_index`, `pdf_hash`, `backend`
- `pages_total`, `scanned_page_numbers`, `scan_batches`
- `heading_found`, `heading_page`, `heading_line_id`, `heading_text`
- `text`, `lines`, `warnings`, `status`, `schema_version`

Extraction charge output có đúng các key `case_charges`, `defendant_charge_map`, `charge_evidence` và `warnings`. `defendant_charge_map` dùng defendant `entity_id`, không dùng tên làm key khi entity đã tồn tại. Mỗi `ChargeEvidence` giữ `charge`, `defendant_entity_ids`, `defendant_names`, `source_region`, `page_number`, `line_ids`, `raw_text`, `match_method` và `confidence`. Charge evidence hợp lệ luôn có `source_region=decision_tail`; không có explicit verdict phrase thì danh sách/map để trống.

Mỗi defendant/participant front giữ `entity_id` và `source_region=front_pre_content`. Extraction output có `decision_tail_status` và `source_region_audit`. Audit row gồm `field_name`, `source_region`, `source_page`, `evidence_line_ids`, `allowed`, `warning`; workbook thêm `case_id` khi ghi sheet `SOURCE_REGION_AUDIT`.

Các sheet charge debug dùng schema:

- `CHARGES`: `case_id`, charge, source region/page, line IDs, match method, confidence, raw text.
- `DEFENDANT_CHARGES`: `case_id`, defendant entity ID/name, charge, mapping status/method, evidence line IDs.
- `CHARGE_WARNINGS`: warning cấp case/strategy, không thêm cột vào `FINAL_EXCEL`.

## Extraction Draft Contract

Canonical `extraction_pipeline.py` tạo draft envelope gồm:

- `case_id`
- `source_index`
- `ocr_backend`
- `extractor_backend`
- `marker_found`
- `status`
- `error`
- `payload`

`payload` hiện gồm `case`, `participants`, và `document_warnings`. Participant có `confidence`, `evidence`, và `warnings`; `needs_review` được tính bằng validation/review helper, chưa phải field persisted trực tiếp trong extraction payload. Phase 1F chỉ hợp nhất module, không đổi schema này.

## QA Report

Required metrics:

- `total_rows`
- `rows_need_review`
- `invalid_date_count`
- `invalid_id_count`
- `missing_evidence_count`
- `evidence_mismatch_count`
- `low_ocr_confidence_count`
- `duplicate_participant_count`
- `warning_counts`

The report must not include full real OCR text or unnecessary PII.

## Evaluation Manifests

Gold JSONL record:

- Safe IDs: `case_id_hash`, `file_hash`.
- Document labels: page count, tags, expected section presence/page.
- Field labels: redacted/hash value, source page/line IDs, redacted evidence, required flag.
- Participant labels: role, `name_hash`, redacted fields, source references.
- Human review status.

Prediction JSONL record:

- Run/backend/model/prompt versions.
- OCR aggregate counts.
- Predicted sections/fields/participants with evidence/source references.
- warnings và `needs_review`.

Evaluation report schema là whitelist numeric metrics trong `evaluation.metrics.METRIC_KEYS`; không chứa raw manifest values.
## Pre-content A/B schema

Schema thử nghiệm gồm `document_type`, `metadata`, `trial_panel`, `defendants`, `participants`, `evidence`, `warnings`, `needs_review` và `field_meta`. Entity giữ `raw_block`, `source_block_id`, `evidence_line_ids` và warning riêng; participant có thể có `represented_person`. Anchor output có `defendant_region` và `rejected_defendant_candidates`; extraction có thể bổ sung `rejected_defendant_entities`, `case_charges`, `defendant_charge_map` và `charge_output`. `correction_notice` dùng nhánh nhẹ `notice_number`, `notice_date`, `referenced_judgment_number`, `correction_from`, `correction_to`; không ép vào schema bản án.
