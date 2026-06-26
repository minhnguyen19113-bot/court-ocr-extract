# Ezycloudx Windows VM CLI Workflow

Mục tiêu: chạy pipeline OCR thật trên Ezycloudx Windows VM, không dùng Vast.ai, không phụ thuộc copy/paste qua RDP, chưa cần FastAPI/Streamlit và chưa cần Ollama ở bước đầu.

Luồng đơn giản nhất:

1. Code đi bằng private Git repo.
2. PDF đi bằng transfer server tạm thời chạy trên VM.
3. Chạy CLI sample 10 PDF.
4. Tải Excel/JSON về để kiểm tra.
5. Khi sample tốt mới chạy full batch.

## 1. Chuẩn bị Git repo trên máy local

Không commit PDF thật, output, log, model cache hoặc `.env`.

Trên máy local:

```powershell
cd "C:\Users\Duong Nguyen\Documents\Codex\2026-06-09\files-mentioned-by-the-user-06"
git status
```

Nếu `git status` báo `not a git repository`, khởi tạo repo trước:

```powershell
git init
git branch -M main
```

Kiểm tra `.gitignore` đã có các thư mục nhạy cảm:

```text
data/raw_pdfs/
data/private_pdfs/
data/images/
data/processed_images/
data/ocr_raw/
data/ocr_corrected/
outputs/
logs/
models/
.env
*.pdf
```

Tạo private repo trên GitHub/GitLab, rồi push code:

```powershell
git add .
git commit -m "Prepare Ezycloudx CLI workflow"
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```

Nếu repo đã có remote thì chỉ cần:

```powershell
git add .
git commit -m "Prepare Ezycloudx CLI workflow"
git push
```

## 2. Vào VM và cài phần mềm nền

Đăng nhập VM bằng file `.rdp`, mở PowerShell.

Kiểm tra GPU:

```powershell
nvidia-smi
```

Nếu lệnh này không chạy hoặc không thấy GPU, cần sửa image/driver trước khi chạy OCR.

Cài Git, Python và VS Code:

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.11 -e
winget install --id Microsoft.VisualStudioCode -e
```

Đóng PowerShell, mở lại PowerShell mới, kiểm tra:

```powershell
git --version
python --version
code --version
```

## 3. Clone project vào VM

```powershell
cd C:\
git clone https://github.com/<user>/<repo>.git court_ocr
cd C:\court_ocr
code .
```

Nếu private repo yêu cầu đăng nhập, Git Credential Manager sẽ mở trình duyệt hoặc hỏi token. Chỉ đăng nhập tài khoản có quyền đọc repo.

## 4. Cài môi trường Python

Trong terminal của VS Code hoặc PowerShell:

```powershell
cd C:\court_ocr
powershell -ExecutionPolicy Bypass -File .\scripts\ezycloudx_setup_windows.ps1
```

Script này:

- Tạo `.venv`.
- Cài dependency core để chạy OCR/batch.
- Tạo các thư mục `data/raw_pdfs/uploads`, `outputs/excel`, `outputs/json`.
- Copy `.env.example` thành `.env` nếu chưa có.

Mặc định không cài FastAPI/Streamlit và không cần Ollama.

## 5. Cấu hình `.env` tối thiểu

Mở:

```powershell
notepad C:\court_ocr\.env
```

Để giai đoạn đầu chạy không Ollama:

```dotenv
PROCESSING_MODE=local-only
ENABLE_LOCAL_LLM_EXTRACTION=false
ENABLE_CLOUD_LLM_EXTRACTION=false
ENABLE_MOCK_OCR=false
ENABLE_MOCK_LOCAL_LLM=false
STOP_ON_SECTION_MARKER=true
MAX_PAGES_BEFORE_CONTENT_MARKER=5
FORCE_FULL_OCR=false
ENABLE_RED_STAMP_REMOVAL=true
PERSIST_OCR_TEXT_ARTIFACTS=false
PERSIST_SENSITIVE_TEXT_IN_JSON=false
DEBUG_SENSITIVE=false
```

## 6. Upload PDF vào VM khi RDP không copy được

Chạy transfer server trên VM:

```powershell
cd C:\court_ocr
.\.venv\Scripts\Activate.ps1
python -m scripts.transfer_server --host 0.0.0.0 --port 8765 --token doi-token-rieng
```

Mở firewall Windows cho port này:

```powershell
New-NetFirewallRule -DisplayName "Court OCR Transfer 8765" -Direction Inbound -Protocol TCP -LocalPort 8765 -Action Allow
```

Nếu Ezycloudx có mục security group/firewall riêng, mở thêm TCP port `8765` trên dashboard Ezycloudx.

Trên máy local, mở trình duyệt:

```text
http://<VM_PUBLIC_IP>:8765/?token=doi-token-rieng
```

Upload:

- Chọn nhiều PDF, hoặc
- Nén nhiều PDF thành một file ZIP rồi upload ZIP.

Server sẽ lưu PDF vào:

```text
C:\court_ocr\data\raw_pdfs\uploads
```

Tên file trên VM được tự sinh dạng `uploaded_*.pdf` để tránh lộ tên file thật trong log.

## 7. Chạy thử 10 PDF

Trong PowerShell trên VM:

```powershell
cd C:\court_ocr
powershell -ExecutionPolicy Bypass -File .\scripts\ezycloudx_run_sample_windows.ps1
```

Script này chạy:

- 10 PDF đầu tiên sau khi sort tên file.
- Tối đa 5 trang trước marker.
- Dừng khi gặp marker.
- Giảm dấu mộc đỏ trên ảnh OCR phụ.
- Không dùng local LLM/Ollama mặc định.

Output chính:

```text
C:\court_ocr\outputs\excel\sample_10.xlsx
C:\court_ocr\outputs\json\batch_summary.json
```

Mở lại trang transfer server:

```text
http://<VM_PUBLIC_IP>:8765/?token=doi-token-rieng
```

Chọn `Xem output Excel/JSON` để tải kết quả về máy local.

## 8. Đánh giá sample 10 PDF

Kiểm tra trong Excel:

- Có bao nhiêu file thành công.
- Có file nào failed trong `batch_summary.json`.
- Marker `NỘI DUNG VỤ ÁN` có được phát hiện không.
- Các cột chính có đủ dùng không.
- Dòng nào cần review, lý do nằm trong cột ghi chú/cảnh báo.

Nếu OCR lỗi kỹ thuật, xử lý môi trường GPU/Surya trước.

Nếu OCR ổn nhưng thiếu field, lúc đó mới cân nhắc bật Ollama/local LLM.

## 9. Chạy toàn bộ

Khi 10 file đầu ổn:

```powershell
cd C:\court_ocr
powershell -ExecutionPolicy Bypass -File .\scripts\ezycloudx_run_full_windows.ps1
```

Output chính:

```text
C:\court_ocr\outputs\excel\full_results.xlsx
C:\court_ocr\outputs\json\batch_summary.json
```

Tải kết quả qua trang transfer server giống bước sample.

## 10. Khi nào dùng Ollama?

Không bắt buộc cho giai đoạn đầu.

Không Ollama:

- Cài ít hơn.
- Ít lỗi môi trường hơn.
- Đủ để kiểm tra OCR, marker, early-stop, Excel output.
- Bóc tách dựa trên rule/support nên có thể thiếu field khó.

Dùng Ollama:

- Hữu ích khi OCR đã ổn nhưng rule không bóc tách đủ.
- Tăng chất lượng extraction nhưng thêm một lớp cần cài và debug.

Nếu cần bật sau:

```powershell
winget install --id Ollama.Ollama -e
ollama pull qwen3:4b
ollama list
```

Sửa `.env`:

```dotenv
ENABLE_LOCAL_LLM_EXTRACTION=true
LOCAL_LLM_PROVIDER=ollama
LOCAL_LLM_MODEL_NAME=qwen3:4b
LOCAL_LLM_BASE_URL=http://127.0.0.1:11434
LOCAL_LLM_TEMPERATURE=0
```

Chạy lại sample với LLM:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\ezycloudx_run_sample_windows.ps1 -UseLocalLlm
```

## 11. Nếu không mở được port upload 8765

Ưu tiên thử mở Windows Firewall và firewall/security group của Ezycloudx.

Nếu vẫn không được, dùng phương án thay thế:

1. Nén PDF thành file ZIP có mật khẩu mạnh trên máy local.
2. Upload ZIP đó lên một nơi tạm có kiểm soát quyền truy cập.
3. Trên VM dùng trình duyệt hoặc PowerShell tải ZIP xuống.
4. Giải nén vào `C:\court_ocr\data\raw_pdfs\uploads`.
5. Xóa ZIP khỏi nơi tạm và khỏi VM sau khi chạy.

Phương án này kém riêng tư hơn transfer server trực tiếp, nên chỉ dùng khi port vào VM bị chặn.

## 12. Cleanup sau khi có kết quả

Sau khi đã tải Excel/JSON về local, nếu không cần giữ dữ liệu trên VM:

```powershell
Remove-Item -Recurse -Force C:\court_ocr\data\raw_pdfs\uploads -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force C:\court_ocr\data\images -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force C:\court_ocr\data\processed -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force C:\court_ocr\data\processed_images -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force C:\court_ocr\data\ocr_raw -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force C:\court_ocr\data\ocr_corrected -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force C:\court_ocr\data\raw_pdfs\uploads | Out-Null
```

Không bật `DEBUG_SENSITIVE=true` khi chạy dữ liệu thật.
