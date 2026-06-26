# Workflow OCR early-stop

Pipeline không OCR toàn bộ PDF theo mặc định. Mỗi file được render và OCR từng trang từ đầu tài liệu cho tới khi tìm thấy marker `NỘI DUNG VỤ ÁN` hoặc vượt `MAX_PAGES_BEFORE_CONTENT_MARKER`.

```mermaid
flowchart TD
    A["PDF input"] --> B["Validate PDF"]
    B --> C["Early-stop loop"]
    C --> D["Render page"]
    D --> E["OCR helper image"]
    E --> F["Reduce red stamp"]
    F --> G["Preprocess"]
    G --> H["Surya/Mock OCR"]
    H --> I["Append text + save page OCR JSON"]
    I --> J{"Fuzzy marker found?"}
    J -- "No, under limit" --> D
    J -- "No, over limit" --> K["Stop + review_required"]
    J -- "Yes" --> L["Stop + keep text before marker"]
    K --> M["Normalize/correct OCR text"]
    L --> M
    M --> N["Local LLM extraction"]
    M --> O["Heuristic/NER support"]
    N --> P["Merge + validate confidence"]
    O --> P
    P --> Q["Export JSON/Excel"]
    Q --> R["Human review"]
```

Nhánh triển khai:

- Ezycloudx full-runtime: CLI, FastAPI hoặc Streamlit chạy trực tiếp trên Ezycloudx để máy local không xử lý OCR/model nặng.
- Ezycloudx remote worker: local UI/API điều khiển workflow; Ezycloudx chỉ chạy `/ocr-page`, `/extract`, `/cleanup` qua SSH tunnel hoặc endpoint riêng có token.
- Jupyter chỉ là công cụ debug tùy chọn, không phải workflow chính.

Mermaid nguồn nằm ở `docs/workflow.mmd`.
