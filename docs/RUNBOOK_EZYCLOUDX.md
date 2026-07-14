# Ezycloudx Runbook

## Local LLM 3B: preflight và context budget

Runtime mặc định đã xác nhận cho RTX 5060 Ti 16GB là `Qwen/Qwen2.5-3B-Instruct` với `max_model_len=8192`; không dùng Qwen2.5-7B full bf16 làm default vì không còn đủ KV cache sau khi load model. Thiết lập session:

```powershell
$env:LOCAL_LLM_PROVIDER = "vllm"
$env:LOCAL_LLM_BASE_URL = "http://127.0.0.1:8000/v1"
$env:LOCAL_LLM_MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"
$env:LOCAL_LLM_CONTEXT_WINDOW = "8192"
$env:LOCAL_LLM_MAX_OUTPUT_TOKENS = "1024"
$env:LOCAL_LLM_MAX_INPUT_TOKENS = "6000"
$env:LOCAL_LLM_MAX_INPUT_CHARS = "22000"
$env:LOCAL_LLM_ENABLE_CHUNKED_EXTRACTION = "true"
```

Chạy preflight thật trước compare; script gọi `/models` rồi một `/chat/completions` nhỏ và không in API key:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.check_llm_backend
```

Sau khi `ok=true`, chạy một case:

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli compare-pre-content `
  --input-dir data\test_pdfs\pre_content_9 `
  --ocr-cache-dir outputs\ocr_cache_pre_content_early_stop_9 `
  --output-dir outputs\pre_content_rule_anchor_check_1 `
  --strategies rule_anchor_only,rule_then_llm_per_block `
  --require-llm --limit 1 --open
```

Không gửi toàn bộ pre-content trong một prompt. Nhánh mới parse metadata/trial panel bằng rule, chỉ gọi LLM cho từng defendant/participant block cần repair; mỗi call bị cap 6000 ký tự và 512 output token. `--allow-llm-failure` chỉ dùng khi cần report strategy không chạy; mặc định và `--require-llm` đều fail-fast trước case khi preflight lỗi.

## OCR pre-content dừng sớm tại marker

Command `ocr` mặc định scan từng page và dừng sau page chứa `NỘI DUNG VỤ ÁN`. Không truyền `--max-pages` thì OCR tiếp tục đến marker hoặc hết file; không còn giới hạn ngầm 7 page. Predictor/vLLM được khởi tạo một lần và giữ warm giữa các page. Batch mặc định là 1 để dừng chính xác.

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli ocr `
  --input-dir data\test_pdfs\pre_content_9 `
  --limit 1 `
  --cache-dir outputs\ocr_cache_pre_content_early_stop_1 `
  --ocr-backend surya `
  --debug-visual `
  --use-preprocessed `
  --deskew off `
  --red-seal-removal on `
  --red-removal-mode inpaint `
  --text-enhance medium `
  --preprocess-profile balanced `
  --stamp-suppression balanced `
  --stamp-erase-mode mask `
  --ocr-stamp-filter balanced `
  --surya-docker-binary "C:\court-ocr-extract\tools\docker.cmd" `
  --surya-startup-timeout-seconds 900
```

Cache phải có `metadata.marker`, `metadata.early_stop`, `pages_total` và `text_before_marker`. Muốn OCR toàn bộ file, truyền `--full-document`; khi đó marker không trim text và không kích hoạt early-stop. Có thể tăng `--ocr-page-batch-size`, nhưng batch lớn có thể OCR thừa page sau marker.

## Cấu hình Surya/vLLM đã xác nhận trên Windows VM

Project Owner đã xác nhận OCR page 1 chạy thành công với Docker shim không có khoảng trắng và vLLM container được giữ warm. Đây là runtime recipe chuẩn cho Windows/Ezycloudx; kết quả chất lượng OCR vẫn cần human review.

```powershell
cd C:\court-ocr-extract
.\scripts\setup_surya_windows_runtime.ps1
```

Script tạo local shim `C:\court-ocr-extract\tools\docker.cmd`, set env trong session hiện tại và in lệnh runtime/OCR tiếp theo. Dùng `-PersistUserEnvironment` nếu muốn lưu env ở User scope. Script không tự chạy Docker hoặc OCR.

Thiết lập tương đương:

```powershell
$env:SURYA_INFERENCE_BACKEND = "vllm"
$env:SURYA_INFERENCE_KEEP_ALIVE = "1"
$env:SURYA_DOCKER_BINARY = "C:\court-ocr-extract\tools\docker.cmd"
$env:DOCKER_BINARY = "C:\court-ocr-extract\tools\docker.cmd"
$env:DOCKER_HOST = "npipe:////./pipe/docker_engine"
```

Không stop container `surya-vllm-*` sau khi đã warm. Cold start đầu tiên có thể tạo container sau mốc 300 giây, vì vậy OCR page 1 dùng timeout 900 giây. Nếu Windows Firewall hoặc Docker hỏi quyền network trên VM, allow cả Private và Public.

Kết luận vận hành: lỗi đã quan sát thuộc Surya/vLLM cold start, không thuộc preprocess/stamp. Safe OCR mode bắt buộc truyền `--stamp-erase-mode mask`; không dùng component/object erase làm mode vận hành mặc định vì có thể xóa chữ thật.

## Kiểm tra Surya runtime bắt buộc

Chạy hai lệnh sau trước pilot OCR:

```powershell
.\.venv\Scripts\python.exe -B -m scripts.check_surya_runtime_backend
.\.venv\Scripts\python.exe -B -m scripts.check_surya_runtime_backend --check-gpu-container
```

Lệnh thứ hai phải trả `gpu_container.checked=true` và `gpu_container.ok=true`. Nếu `checked=false` hoặc `ok=false`, không chạy OCR. Có thể điều chỉnh bằng `--gpu-container-timeout-seconds 180`, `--gpu-test-image` và `--surya-docker-binary`.

`debug-ocr-review` và `ocr` chạy preflight nhẹ mặc định gồm Docker resolver, `docker --version`, `docker info`, Surya version và API. Chỉ dùng `--skip-surya-runtime-preflight` khi chẩn đoán có chủ đích. GPU smoke trong OCR chỉ chạy khi có `--surya-runtime-check-gpu-container`.

Lệnh page 1 an toàn dùng `--stamp-suppression balanced --stamp-erase-mode mask --ocr-stamp-filter balanced`, `--surya-runtime-check-gpu-container` và `--surya-startup-timeout-seconds 900`. Khi lỗi hoặc timeout, xem `surya_runtime_preflight.json` và `<case>/surya_runtime_diagnostics.json` trước khi chạy lại.

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli debug-ocr-review `
  --input data\raw_pdfs\pilot_one `
  --limit 1 `
  --review-sample-size 1 `
  --ocr-backend surya `
  --pages 1 `
  --use-preprocessed `
  --deskew off `
  --red-seal-removal on `
  --red-removal-mode inpaint `
  --text-enhance medium `
  --preprocess-profile balanced `
  --stamp-suppression balanced `
  --stamp-erase-mode mask `
  --ocr-stamp-filter balanced `
  --surya-docker-binary "C:\court-ocr-extract\tools\docker.cmd" `
  --surya-runtime-check-gpu-container `
  --surya-startup-timeout-seconds 900 `
  --output outputs\debug_visual_ocr_safe_mask_page1 `
  --open
```

Last updated: 2026-07-14

Đây là target rebuild runbook sau Phase 1B default cleanup và Phase 2A Surya adapter fix.

## Safety

- Do not upload real data through Git.
- Keep real PDFs and derived outputs on the VM or user-controlled storage.
- Treat rendered images, OCR cache, extraction drafts, Excel files, and debug UI as sensitive derived artifacts.
- Cloud APIs are disabled by default.

## Runtime Checks To Keep

The runbook should include checks for:

- Python environment.
- GPU availability.
- CUDA/torch compatibility.
- Surya install/import.
- vLLM or Ollama local endpoint.
- Local Qwen model availability.
- Disk space for rendered images and debug artifacts.
- Transfer server bound to safe interface.

## Pilot Workflow Gate

The Project Owner runs real-data pilot/full workflows outside Codex. Codex can write commands and scripts, but must not execute real-data OCR or inspect real outputs.

## Target Commands

Surya + local LLM target checks:

```powershell
python -m scripts.check_runtime --ocr-backend surya --extractor local_llm
.\.venv\Scripts\python -m scripts.check_ocr_backend --backend surya
python -m scripts.check_extractor --backend local_llm
```

## Pilot 1 PDF Full-Document Review

Project Owner đặt đúng 1 PDF cần pilot vào folder `data\raw_pdfs\pilot_one`. Các command debug/render/preprocess mặc định chạy toàn bộ trang nếu không truyền `--pages`; muốn giới hạn thì truyền rõ `--pages 1-3`.

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli debug-render `
  --input data\raw_pdfs\pilot_one `
  --limit 1 `
  --review-sample-size 1 `
  --output outputs\debug_visual `
  --open
```

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli debug-preprocess `
  --input data\raw_pdfs\pilot_one `
  --limit 1 `
  --review-sample-size 1 `
  --deskew off `
  --red-seal-removal on `
  --red-removal-mode neutralize `
  --text-enhance light `
  --preprocess-profile conservative `
  --output outputs\debug_visual_preprocess_v2 `
  --open
```

Project Owner phải kiểm tra original/red mask/black-text protection/seal removed/text enhanced/final và warnings của toàn bộ trang trước OCR. Nếu `neutralize` còn red residual, so sánh với `inpaint`:

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli debug-preprocess `
  --input data\raw_pdfs\pilot_one `
  --limit 1 `
  --review-sample-size 1 `
  --deskew off `
  --red-seal-removal on `
  --red-removal-mode inpaint `
  --text-enhance light `
  --preprocess-profile conservative `
  --output outputs\debug_visual_preprocess_inpaint `
  --open
```

Nếu chữ vẫn mờ sau khi seal đã sạch, thử text medium riêng:

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli debug-preprocess `
  --input data\raw_pdfs\pilot_one `
  --limit 1 `
  --review-sample-size 1 `
  --deskew off `
  --red-seal-removal on `
  --red-removal-mode inpaint `
  --text-enhance medium `
  --preprocess-profile balanced `
  --output outputs\debug_visual_preprocess_medium `
  --open
```

`white_fill`, `text-enhance=strong`, và `deskew=force` chỉ dùng thử nghiệm có visual review; không dùng làm default production.

## OCR trên Mode 3 đã chọn

`debug-preprocess` chỉ review preprocess; muốn Surya thực sự nhận final image phải dùng `debug-ocr-review --use-preprocessed`:

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli debug-ocr-review `
  --input data\raw_pdfs\pilot_one `
  --limit 1 `
  --review-sample-size 1 `
  --ocr-backend surya `
  --full-document `
  --use-preprocessed `
  --deskew off `
  --red-seal-removal on `
  --red-removal-mode inpaint `
  --text-enhance medium `
  --preprocess-profile balanced `
  --output outputs\debug_visual_ocr_mode3 `
  --open
```

Sau khi visual OCR review đạt, tạo cache Mode 3 bằng:

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli ocr `
  --input-dir data\raw_pdfs\pilot_one `
  --limit 1 `
  --cache-dir outputs\ocr_cache `
  --ocr-backend surya `
  --full-document `
  --debug-visual `
  --use-preprocessed `
  --deskew off `
  --red-seal-removal on `
  --red-removal-mode inpaint `
  --text-enhance medium `
  --preprocess-profile balanced
```

Không có `--use-preprocessed`, OCR vẫn dùng rendered original. Reviewer phải kiểm tra `ocr_input_source`, `preprocess/` artifacts và `ocr_surya/page_NNN_ocr_input.png` trước khi chấp nhận cache.

OCR review toàn bộ file phải dùng `--full-document` để không cắt theo `settings.max_pages_before_marker` và không dừng/truncate tại marker nội dung.

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli debug-ocr-review `
  --input data\raw_pdfs\pilot_one `
  --limit 1 `
  --review-sample-size 1 `
  --ocr-backend surya `
  --full-document `
  --output outputs\debug_visual `
  --open
```

OCR cache toàn bộ file cũng dùng `--full-document`; command này không chạy extraction/LLM/Excel.

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli ocr `
  --input-dir data\raw_pdfs\pilot_one `
  --limit 1 `
  --cache-dir outputs\ocr_cache `
  --ocr-backend surya `
  --full-document `
  --debug-visual
```

Nếu thiếu Surya hoặc VM đã drift lên 0.21.x, reinstall đúng pin:

```powershell
.\.venv\Scripts\python.exe -m pip uninstall -y surya-ocr
.\.venv\Scripts\python.exe -m pip install -e ".[dev,ocr]"
.\.venv\Scripts\python.exe -m pip show surya-ocr
.\.venv\Scripts\python.exe -B -m scripts.check_ocr_backend --backend surya
```

Main path vẫn pin `surya-ocr==0.20.0`; guard sẽ fail trước import/runtime nếu version sai. Trên Windows VM đã xác nhận, package/API được hỗ trợ chạy qua vLLM/Docker với shim path không có khoảng trắng, `SURYA_INFERENCE_KEEP_ALIVE=1` và timeout cold start 900 giây.

Command target để review OCR:

```powershell
python -m court_ocr_extract.cli debug-ocr-review --input data\raw_pdfs\uploads --limit 5 --review-sample-size 5 --ocr-backend surya --full-document --output outputs\debug_visual --open
```

Project Owner chạy command này trên Ezycloudx với PDF thật. Codex không được chạy hoặc inspect real-data outputs.

Target pilot:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_sample_windows.ps1 -OcrBackend surya -Extractor local_llm -DebugVisual -ReviewSampleSize 5 -ReviewMode mixed
```

Target full run after Project Owner acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_full_windows.ps1 -OcrBackend surya -Extractor local_llm -ReviewSampleSize 10 -ReviewMode mixed -AcceptedSample10
```

Phase 2A đã wire `SuryaOCRBackend` cho API `surya-ocr 0.20.0` qua `RecognitionPredictor(..., full_page=True)`. Dependency đã pin exact; nếu check báo version sai, reinstall project extras, không fallback sang Tesseract và không cài Surya không version.

## VLM Benchmark

The VLM benchmark path must stay separate until it produces comparable validation, QA, and debug output. Treat VLM commands as target/planned unless the VM runtime has been explicitly checked.

## Troubleshooting Topics

- Surya runtime/model load failure.
- Local LLM endpoint unavailable.
- Strict JSON parsing failure.
- Evidence mismatch.
- Low OCR confidence.
- Debug UI artifact missing.
- Transfer server exposure and cleanup.
## Kiem tra Surya Windows runtime

Khong sua `.venv\Lib\site-packages` thu cong. Project tu resolve Docker qua `SURYA_DOCKER_BINARY`, `DOCKER_BINARY`, PATH hoac Docker Desktop path.

```powershell
.\.venv\Scripts\python.exe -B -m scripts.check_surya_runtime_backend
.\.venv\Scripts\python.exe -B -m scripts.check_surya_runtime_backend --check-gpu-container
```

OCR review Mode 3 nen dung suppression/filter balanced. Kiem tra raw, filtered, excluded lines, suppression mask va OCR input trong HTML review. Neu balanced con doc dau moc, review aggressive rieng; khong auto-correct ten nguoi hay noi dung bang heuristic.
## Chạy pre-content rule anchor trên VM

Đặt PDF local tại `data\test_pdfs\pre_content_9` và dùng OCR cache early-stop đã duyệt. Chạy 1 case trước:

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli compare-pre-content `
  --input-dir data\test_pdfs\pre_content_9 `
  --ocr-cache-dir outputs\ocr_cache_pre_content_early_stop_9 `
  --output-dir outputs\pre_content_rule_anchor_check_1 `
  --strategies rule_anchor_only,rule_then_llm_per_block `
  --require-llm `
  --limit 1 `
  --open
```

Review `ANCHOR_BLOCKS`, `ANCHOR_WARNINGS`, judgment date, trial panel, defendant/participant roles, validator warnings và `LLM_STATUS`. Chỉ khi case đầu đạt mới đổi output thành `outputs\pre_content_rule_anchor_check_3` và `--limit 3`. Không commit PDF/output; correction notice phải xuất hiện trong `DOC_ROUTER` nhưng không tính như judgment benchmark. Muốn đối chiếu lịch sử mới truyền rõ `--strategies hybrid_rule_llm,llm_only`.

Sau khi case đầu đạt, chạy 3 case:

```powershell
.\.venv\Scripts\python.exe -m court_ocr_extract.cli compare-pre-content `
  --input-dir data\test_pdfs\pre_content_9 `
  --ocr-cache-dir outputs\ocr_cache_pre_content_early_stop_9 `
  --output-dir outputs\pre_content_rule_anchor_check_3 `
  --strategies rule_anchor_only,rule_then_llm_per_block `
  --require-llm `
  --limit 3 `
  --open
```
## Review stamp object erase

`red_mask` chỉ chứng minh detector đã bắt pixel đỏ; residual xám vẫn có thể còn ngoài mask. Component/object erase chỉ dành cho thử nghiệm visual có chủ đích, không phải mode vận hành mặc định. Safe OCR phải dùng `--stamp-suppression balanced --stamp-erase-mode mask --ocr-stamp-filter balanced` để giảm nguy cơ xóa chữ thật.

Luôn so sánh `red_mask`, `stamp_object_mask`, `stamp_object_erased`, `ocr_input_stamp_suppressed` và `final_preprocessed`. Khi stamp overlap chữ thật, không chấp nhận output tự động nếu chưa human review.
## Kiểm final preprocess candidate

Trong review mới, kiểm `object_seed_mask` có phủ dấu ngang chính và seal mép phải hay không. So sánh trực tiếp `stamp_object_erased` với `final_preprocessed`; metadata `final_selected_stage` phải giải thích ảnh nào được chọn. `candidate_scores` phải cho thấy candidate làm residual đậm lại hoặc mất chữ bị loại. OCR review phải ghi cùng `ocr_input_source_stage`.
