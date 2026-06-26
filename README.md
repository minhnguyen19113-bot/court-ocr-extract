# Court OCR Extract

Pipeline OCR và bóc tách dữ liệu bản án tòa án Việt Nam theo hướng local-first, early-stop và an toàn dữ liệu.

## Hướng chạy chính hiện tại

Giai đoạn đang ưu tiên là chạy CLI trên Ezycloudx Windows VM:

1. Đưa code lên private Git repo, rồi clone vào VM.
2. Upload PDF vào VM qua `scripts.transfer_server`, không phụ thuộc copy/paste RDP.
3. Chạy thử 10 PDF bằng CLI.
4. Kiểm tra Excel/JSON trong `outputs/`.
5. Nếu kết quả ổn, chạy toàn bộ batch.

FastAPI/Streamlit tạm thời không phải đường chính. Web demo đã được tách sang dependency optional.

## Cài đặt trên VM

Trong PowerShell trên VM:

```powershell
cd C:\
git clone https://github.com/<user>/<repo>.git court_ocr
cd C:\court_ocr
powershell -ExecutionPolicy Bypass -File .\scripts\ezycloudx_setup_windows.ps1
```

Nếu thư mục local chưa phải Git repo, chạy `git init` và push lên private repo trước. Xem chi tiết trong `docs/ezycloudx_setup.md`.

Mặc định không cần Ollama. `.env.example` đang để:

```dotenv
ENABLE_LOCAL_LLM_EXTRACTION=false
ENABLE_CLOUD_LLM_EXTRACTION=false
```

## Upload PDF khi RDP không copy được

Trên VM:

```powershell
cd C:\court_ocr
.\.venv\Scripts\Activate.ps1
python -m scripts.transfer_server --host 0.0.0.0 --port 8765 --token doi-token-rieng
```

Nếu Windows Firewall chưa mở port:

```powershell
New-NetFirewallRule -DisplayName "Court OCR Transfer 8765" -Direction Inbound -Protocol TCP -LocalPort 8765 -Action Allow
```

Trên máy local, mở:

```text
http://<VM_PUBLIC_IP>:8765/?token=doi-token-rieng
```

Chọn nhiều PDF hoặc một file ZIP chứa PDF. File upload vào VM sẽ được lưu dưới tên tự sinh trong `data/raw_pdfs/uploads`.

## Chạy thử 10 PDF

Trong PowerShell trên VM:

```powershell
cd C:\court_ocr
powershell -ExecutionPolicy Bypass -File .\scripts\ezycloudx_run_sample_windows.ps1
```

Kết quả chính:

```text
outputs\excel\sample_10.xlsx
outputs\json\batch_summary.json
```

Mở lại trang transfer server, vào `Outputs` để tải Excel/JSON về máy local.

## Chạy toàn bộ

Sau khi sample 10 PDF đủ tốt:

```powershell
cd C:\court_ocr
powershell -ExecutionPolicy Bypass -File .\scripts\ezycloudx_run_full_windows.ps1
```

Kết quả chính:

```text
outputs\excel\full_results.xlsx
outputs\json\batch_summary.json
```

## Khi nào cần Ollama?

Không bắt buộc ở bước đầu. Sample không LLM chỉ nên dùng để kiểm tra OCR, marker, cache và luồng Excel/JSON. Nếu Excel thiếu nhiều field hoặc bắt nhầm cụm không phải tên người, đó là giới hạn dự kiến của rule/regex.

Để đánh giá chất lượng bóc tách thật, cài Ollama/Qwen và chạy lại với:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\ezycloudx_run_sample_windows.ps1 -UseLocalLlm
```

Khi bật LLM, cấu hình `.env` ví dụ:

```dotenv
ENABLE_LOCAL_LLM_EXTRACTION=true
LOCAL_LLM_PROVIDER=ollama
LOCAL_LLM_MODEL_NAME=qwen3:4b
LOCAL_LLM_BASE_URL=http://127.0.0.1:11434
LOCAL_LLM_TEMPERATURE=0
```

## Cài web demo sau này

Khi pipeline CLI đã ổn và cần quay lại FastAPI/Streamlit:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[web]"
```

FastAPI:

```powershell
uvicorn app_fastapi.main:app --host 0.0.0.0 --port 8000
```

Streamlit:

```powershell
streamlit run app_streamlit\main.py --server.address 0.0.0.0 --server.port 8501
```

## Bảo mật dữ liệu

- Không commit PDF thật, `.env`, `outputs/`, cache, model hoặc log.
- Không bật `DEBUG_SENSITIVE=true` khi chạy dữ liệu thật.
- Không bật cloud LLM mặc định.
- PDF gốc không bị chỉnh sửa; ảnh trung gian và output có thể xóa sau khi tải Excel/JSON về.
