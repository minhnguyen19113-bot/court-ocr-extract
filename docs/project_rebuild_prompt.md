# Prompt Làm Lại Dự Án Court OCR Extract Tối Giản

Copy toàn bộ prompt dưới đây cho Codex/agent khi bắt đầu làm lại dự án.

---

## Master Prompt

Bạn là coding agent phụ trách làm lại dự án OCR và bóc tách thông tin bản án tòa án Việt Nam. Hãy refactor/rebuild dự án theo hướng tối giản, dễ chạy trên Ezycloudx Windows VM, ưu tiên chất lượng output Excel và khả năng debug theo sample thật 10 PDF.

### Bối Cảnh

Người dùng chạy dự án trên Ezycloudx Windows GPU VM qua RDP. RDP không copy-paste file từ máy local sang VM được, nên workflow chuyển file phải dùng Git cho code và một kênh upload/download riêng cho PDF/output.

Dự án cũ chạy được một phần:

- Clone code lên VM bằng Git là hướng đúng.
- Upload PDF/download output bằng `transfer_server` + Cloudflare Tunnel là hướng đúng.
- Surya OCR trên Windows cần `llama-server.exe` từ llama.cpp và biến `LLAMA_CPP_BINARY`.
- Chạy sample 10 PDF trước khi chạy full là bắt buộc.
- Excel output hiện sai/thiếu nhiều vì extraction/rule/prompt chưa đủ tốt và dự án có quá nhiều phần dư.

Mục tiêu làm lại: tạo một pipeline nhỏ, rõ, dễ kiểm tra:

```text
PDF thật trên VM
-> OCR early-stop
-> text trước marker NỘI DUNG VỤ ÁN
-> local LLM extraction là extractor chính
-> validation/QA
-> Excel cuối cùng cho cán bộ tòa án
```

Không làm web demo trước. FastAPI/Streamlit để phase sau.

### Guardrails Bảo Mật

- Không commit PDF thật, output thật, OCR text thật, ảnh xử lý thật, cache model, `.env`, log nhạy cảm.
- Không in full OCR text, họ tên, địa chỉ, CCCD/CMND, tên file nhạy cảm trong terminal/log.
- Không dùng cloud LLM mặc định. Nếu có cloud adapter thì phải opt-in rõ, mặc định tắt.
- Agent không được mở/đọc/OCR/grep/parse dữ liệu thật trong các thư mục `data/raw_pdfs`, `data/private_pdfs`, `data/images`, `data/processed_images`, `data/ocr_raw`, `data/ocr_corrected`, `outputs`.
- Được tạo synthetic fixtures trong `tests/fixtures` hoặc `data/synthetic` để test code, nhưng không dùng synthetic để kết luận chất lượng cuối.
- Chất lượng cuối phải được người dùng kiểm tra bằng sample 10 PDF thật qua Excel/QA summary.

### Phần Cần Giữ

Giữ hoặc viết lại gọn các phần sau:

- Ezycloudx setup Windows.
- Transfer server upload PDF/download output qua Cloudflare Tunnel.
- OCR early-stop: chỉ OCR đến marker `NỘI DUNG VỤ ÁN` hoặc tối đa N trang.
- Surya OCR adapter.
- Local LLM adapter, ưu tiên Ollama/OpenAI-compatible local endpoint.
- Excel writer.
- QA summary không lộ dữ liệu, chỉ để debug nội bộ.
- JSON/debug artifacts chỉ được tạo khi bật debug rõ ràng, không phải output cuối.

### Phần Nên Bỏ Hoặc Đưa Sang Optional

- FastAPI demo.
- Streamlit demo.
- Remote GPU worker nếu chưa cần.
- GLiNER nếu chưa chứng minh cải thiện.
- Nhiều file config YAML dư.
- Các script debug batch cũ, bbox debug cũ, dataset correction cũ nếu không phục vụ workflow chính.
- Docker/Vast.ai workflow nếu hiện tại không dùng.
- Rule-based extractor làm extractor chính. Rule chỉ dùng để support/validation, không dùng để kết luận output cuối.

### Kiến Trúc Tối Giản Mong Muốn

Đề xuất file tree mới:

```text
court_ocr_extract/
  pyproject.toml
  README.md
  .env.example
  .gitignore
  prompts/
    extraction_prompt.vi.md
    json_repair_prompt.vi.md
  scripts/
    setup_windows.ps1
    transfer_server.py
    run_sample_windows.ps1
    run_full_windows.ps1
    check_runtime.py
    check_local_llm.py
    qa_output.py
    cleanup_sensitive_windows.ps1
  src/court_ocr_extract/
    __init__.py
    settings.py
    pdf_render.py
    image_preprocess.py
    ocr_surya.py
    early_stop.py
    local_llm.py
    extraction.py
    validation.py
    excel_writer.py
    qa.py
    transfer.py
    cli.py
  tests/
    fixtures/
    test_*.py
  docs/
    ezycloudx_runbook.md
```

Nếu giữ cấu trúc cũ, vẫn phải đạt cùng mức tối giản: một đường chạy chính, ít script, ít config.

### Output Contract

Output cuối cùng bắt buộc là **một file Excel duy nhất**. Đây là file giao cho cán bộ tòa án kiểm tra và sử dụng.

Không lưu JSON như output cuối. Nếu cần JSON kỹ thuật để debug nội bộ, phải đặt dưới chế độ opt-in như `--debug-json` hoặc `SAVE_DEBUG_JSON=true`, mặc định tắt và không dùng làm deliverable.

Excel phải có các cột chính:

```text
LOẠI ÁN
SỐ THỤ LÝ
NGÀY THỤ LÝ (DD/MM/YYYY)
QUAN HỆ PHÁP LUẬT
TƯ CÁCH TỐ TỤNG
HỌ TÊN ĐƯƠNG SỰ
NĂM SINH
CCCD
ĐỊA CHỈ
HỌ TÊN CHỦ TỌA
GHI CHÚ
```

Mỗi người tham gia tố tụng là một dòng. Field chung của vụ án được lặp lại cho từng dòng.

Thông tin kỹ thuật cần theo dõi phải được đưa vào:

- Cột `GHI CHÚ` trong Excel cho từng dòng cần review.
- Sheet phụ trong cùng file Excel, ví dụ `RUN_SUMMARY`, nếu cần thống kê batch.
- Terminal summary ngắn sau khi chạy xong.

Không tạo thêm JSON output mặc định.

### QA Output Không Lộ Dữ Liệu

Tạo lệnh:

```powershell
python -m scripts.qa_output --excel outputs\excel\sample_10.xlsx
```

QA chỉ in thống kê:

- total/success/failed.
- extractor đang dùng.
- số file marker found/not found.
- số dòng participant.
- tỷ lệ trống theo từng cột.
- số dòng review required.
- số lỗi như ngày sai định dạng, CCCD sai độ dài, role lạ, name-like phrase đáng nghi.

QA không được in họ tên, địa chỉ, CCCD, OCR text, tên file PDF thật.

### Workflow VM Tối Giản

Lệnh setup trên VM:

```powershell
cd C:\
git clone https://github.com/<user>/<repo>.git court-ocr-extract
cd C:\court-ocr-extract
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
Copy-Item .env.example .env -Force
```

Kiểm tra runtime:

```powershell
python -m scripts.check_runtime
```

Lệnh này phải kiểm tra:

- Python version.
- GPU/NVIDIA nếu có.
- Surya import được không.
- `LLAMA_CPP_BINARY` có trỏ đến `llama-server.exe` không.
- Ollama/local LLM endpoint có sẵn không nếu bật local LLM.

Upload PDF:

```powershell
python -m scripts.transfer_server --host 127.0.0.1 --port 8765 --token <token>
cloudflared tunnel --url http://127.0.0.1:8765
```

Chạy sample 10:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_sample_windows.ps1 -UseLocalLlm
```

Chạy QA từ Excel:

```powershell
python -m scripts.qa_output --excel outputs\excel\sample_10.xlsx
```

Chạy full chỉ khi sample đạt:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_full_windows.ps1 -UseLocalLlm
```

### Local LLM Là Extractor Chính

Yêu cầu:

- `-UseLocalLlm` phải bắt buộc dùng local LLM thật.
- Nếu local LLM lỗi, batch phải fail rõ, không fallback âm thầm sang rule-only.
- Rule/regex chỉ dùng để support/validate, không tự động ghi Excel như kết quả cuối khi người dùng yêu cầu LLM.
- Có smoke test local LLM bằng text nhỏ nhưng không dùng smoke test để kết luận chất lượng thật.

Prompt local LLM phải:

- Trả JSON strict cho bước parse nội bộ, không lưu JSON này như output cuối.
- Không bịa.
- Không lấy cụm trạng thái như “có mặt tại phiên tòa”, “vắng mặt”, “được triệu tập” làm tên người.
- Không trích kiểm sát viên, thư ký, hội thẩm thành đương sự.
- Tách nhiều bị cáo/bị hại thành nhiều participants.
- Có evidence ngắn cho từng field.
- Có confidence từng field.
- Nếu không thấy dữ liệu thì null.

### Thiết Kế Để Sửa Output Nhanh

Tách rõ 2 bước:

1. OCR cache:

```powershell
python -m court_ocr_extract.cli ocr --input-dir data\raw_pdfs\uploads --limit 10
```

2. Extract lại từ OCR cache:

```powershell
python -m court_ocr_extract.cli extract --ocr-cache outputs\ocr_cache --output outputs\excel\sample_10.xlsx --use-local-llm
```

Như vậy khi prompt/prompt schema sai, không cần OCR lại PDF, chỉ chạy lại extraction.

Nếu giữ CLI khác cũng được, nhưng bắt buộc có cách rerun extraction từ OCR cache.

OCR cache là artifact kỹ thuật nội bộ, không phải output giao cho người dùng cuối. Có thể xóa sau khi Excel đã được kiểm tra.

### Tiêu Chí Thành Công Trước Khi Chạy Full

Với 10 PDF thật đầu tiên:

- OCR chạy thành công ít nhất 9/10 file.
- Marker found hợp lý, hoặc nếu không found thì có warning rõ.
- Extractor trong QA là `local_llm`, không phải `rule_support`.
- Excel không còn bắt nhầm cụm trạng thái thành họ tên.
- Các field `SỐ THỤ LÝ`, `NGÀY THỤ LÝ`, `HỌ TÊN ĐƯƠNG SỰ`, `TƯ CÁCH TỐ TỤNG` không trống hàng loạt.
- `GHI CHÚ` giải thích rõ file/dòng cần review.
- Người dùng kiểm tra bằng mắt và chấp nhận sample trước khi chạy full.

### Cách Làm Việc

1. Đầu tiên audit repo hiện tại, không đọc dữ liệu thật.
2. Đề xuất folder/file nào bỏ, file nào giữ.
3. Tạo branch hoặc commit nhỏ theo từng giai đoạn.
4. Ưu tiên runnable CLI trước, web demo sau.
5. Mỗi thay đổi extraction phải có test synthetic cho parser/schema và hướng dẫn chạy trên 10 PDF thật.
6. Không báo “xong” nếu chưa có lệnh chạy sample + output Excel + QA summary từ Excel.

### Không Làm

- Không tối ưu web trước.
- Không thêm framework mới nếu không cần.
- Không dùng cloud LLM mặc định.
- Không hard-code tên người, địa chỉ, CCCD hoặc nội dung từ PDF thật vào test.
- Không in dữ liệu nhạy cảm trong terminal.
- Không chạy full batch khi sample 10 chưa đạt.

---

## Output Mong Muốn Từ Agent

Sau khi thực hiện prompt này, agent phải trả về:

1. Danh sách file đã giữ/xóa/tạo mới.
2. Lệnh setup VM ngắn nhất.
3. Lệnh upload PDF.
4. Lệnh chạy sample 10.
5. Lệnh chạy QA.
6. Lệnh chạy full.
7. Các điểm còn rủi ro hoặc cần người dùng kiểm tra bằng mắt.
