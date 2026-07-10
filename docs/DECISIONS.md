# Decisions

Last updated: 2026-07-10

| ID | Status | Decision | Reason |
| --- | --- | --- | --- |
| D-001 | Accepted | Project Owner owns direction, real-data runs, output review, and quality acceptance. | Keeps sensitive data and acceptance decisions outside Codex. |
| D-002 | Accepted | Codex is Repo Manager / Implementation Agent. | Codex manages files, docs, tests, and scoped implementation only. |
| D-003 | Accepted | ChatGPT is Architect / Reviewer / Prompt Designer. | Architectural direction is reviewed before repo changes. |
| D-004 | Accepted | Main candidate is Surya OCR + local LLM extraction. | Easier to debug with bbox, text cache, evidence, and visual QA. |
| D-005 | Accepted | VLM end-to-end is a benchmark path. | Useful for comparison, but not the only main path. |
| D-006 | Accepted | Tesseract is legacy only. | New rebuild should not default to Tesseract. Existing Tesseract code is not deleted in Phase 1A. |
| D-007 | Accepted | PaddleOCR is not part of the rebuild path. | No current repo references found in safe code/docs scan. |
| D-008 | Accepted | Cloud OCR/extraction adapters stay disabled by default. | Protects privacy and avoids accidental external data transfer. |
| D-009 | Accepted | Synthetic smoke is contract/control-flow only. | It cannot validate real court PDF OCR/extraction quality. |
| D-010 | Accepted | Every extracted field must carry evidence. | Enables anti-hallucination validation and human review. |
| D-011 | Accepted | Phase 1A must not delete or mass-move files. | Reviewer must approve cleanup before destructive changes. |
| D-012 | Accepted | Debug UI/output is mandatory at every major step. | Project Owner needs visual inspection before trusting Excel. |
| D-013 | Accepted | `src/court_ocr_extract/settings.py` is canonical rebuild config. | New defaults and Phase 1B runtime choices should live in one config source. |
| D-014 | Accepted | `src/court_ocr_extract/config.py` is legacy/compatibility config. | Older imports still need it, but new work should not expand it unless necessary. |
| D-015 | Accepted | `src/court_ocr_extract/excel_writer.py` is canonical Excel writer. | Avoid extending duplicate Excel writers before consolidation. |
| D-016 | Accepted | Main/default OCR backend name is `surya`. | Tesseract remains legacy optional; `surya_optional` is only backward compatibility. |
| D-017 | Accepted | Báo cáo cho Project Owner/ChatGPT phải dùng tiếng Việt và heading tiếng Việt. | Tránh report nửa Anh nửa Việt, giữ giao tiếp thống nhất cho reviewer. |
| D-018 | Accepted | Tên kỹ thuật chuẩn được giữ nguyên tiếng Anh trong report/docs. | File path, class, function, CLI command, env var, model name, package name, schema field không nên dịch. |
| D-019 | Accepted | Template chuẩn sau mỗi task là `# BÁO CÁO TASK` với 9 mục tiếng Việt. | Giúp các phiên Codex sau báo cáo nhất quán. |
| D-020 | Accepted | Phase 1C chỉ tạo architecture audit, repo slimming plan, và production toolkit blueprint; không xóa, archive, mass-move, hoặc push nếu chưa được yêu cầu. | Reviewer cần duyệt từng cleanup/archive slice trước khi thay đổi tracked source/docs. |
| D-021 | Accepted | Import graph và repo inventory là tín hiệu audit, không phải bằng chứng đủ để xóa file. | Module low-fan-in vẫn có thể là CLI entrypoint, compatibility path, benchmark path, hoặc runtime plugin. |
| D-022 | Accepted | `scripts.check_architecture_guardrails` là gate bắt buộc khi đụng architecture defaults, repo slimming, OCR/backend selection, cloud/default behavior, hoặc protected path policy. | Giảm nguy cơ quay lại Tesseract/cloud default, default page-limit cũ, hoặc commit real-data artifacts. |
| D-023 | Accepted | Gold dataset và real-data evaluation do Project Owner quản trị ngoài Codex/Git. | Codex chỉ dùng synthetic fixtures cho contract/control-flow và không đọc dữ liệu thật. |
| D-024 | Accepted | Phase 1D removes old app folders instead of moving them into an archive folder. | Audit found no main `src/`/CLI import dependency; Git history is the restore path and keeping archive folders would keep the repo noisy. |
| D-025 | Accepted | Phase 1E keeps `src/court_ocr_extract/excel_writer.py` as the sole Excel writer and removes `excel.py` plus `export/excel_writer.py` after caller migration. | Một canonical module loại bỏ logic/header trùng; typed-result behavior được chuyển nguyên vẹn và bảo vệ bằng synthetic contract tests. |
| D-026 | Accepted | Phase 1F uses `extraction_pipeline.py` as canonical orchestrator and `extractors/` as the only extractor-backend package. | Main CLI đã dùng contract này; chuyển typed compatibility behavior vào canonical package cho phép xóa backend/rule modules trùng mà không rewrite extraction logic lớn. |
| D-027 | Accepted | Real gold/prediction manifests remain outside Git/Codex; repo evaluation uses only redacted synthetic JSONL fixtures and aggregate reports. | Giảm rủi ro PII, giữ evaluation có thể test tự động, và tách contract verification khỏi real quality acceptance của Project Owner. |
| D-028 | Accepted | Preprocess mặc định dùng `conservative`, red seal removal trên ảnh màu và `deskew=off`; `safe` phải qua confidence/range/crop/layout guard, mọi transform phải có blank fallback. | Kết quả debug thật cho thấy auto-deskew và threshold cũ có thể làm nghiêng hoặc blank trang; ưu tiên bảo toàn nội dung trước OCR. |
| D-029 | Accepted | Preprocess v2 mặc định dùng `red_removal_mode=neutralize` và `text_enhance=light`; `white_fill`/`strong` chỉ dùng thử nghiệm, mọi stage có protection/guard/fallback. | Feedback visual thật xác nhận deskew/blank đã ổn nhưng seal còn residual và chữ hơi mờ; cần tăng chất lượng mà không xóa nét đen hoặc tạo noise giả. |
| D-030 | Accepted | Mode 3 (`inpaint`, text `medium`, profile `balanced`, deskew `off`) là candidate OCR input do Project Owner chọn; chỉ dùng khi truyền `--use-preprocessed`, chưa đổi default OCR toàn cục. | Giữ backward compatibility và tạo gate visual OCR riêng trước khi áp dụng candidate này cho pilot mặc định. |

## Pending Decisions Before Cleanup / Phase 2

- Which local model target is first for the Ezycloudx VM.
- Which Surya adapter path becomes canonical.
- Whether VLM benchmark should bridge through OCR cache or direct extraction JSON first.
