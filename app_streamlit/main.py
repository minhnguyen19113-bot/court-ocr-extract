from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st

from court_ocr_extract.config import get_settings
from court_ocr_extract.export.excel_writer import rows_from_result
from court_ocr_extract.file_utils import safe_stem, unique_path
from court_ocr_extract.models import model_to_dict
from court_ocr_extract.pipeline import process_pdf


def main() -> None:
    st.set_page_config(page_title="Court OCR Extract", layout="wide")
    settings = get_settings()

    with st.sidebar:
        mode = st.radio("Mode", ["local-only", "remote-gpu-worker"], index=0)
        max_pages = st.number_input("Max pages before marker", min_value=1, max_value=50, value=7)
        dpi = st.selectbox("DPI", [200, 300, 400, 500], index=1)
        remove_red_stamp = st.checkbox("Reduce red stamp", value=settings.enable_red_stamp_removal)
        use_local_llm = st.checkbox("Local LLM extraction", value=settings.enable_local_llm)
        use_mock_ocr = st.checkbox("Mock OCR", value=settings.enable_mock_ocr)
        force = st.checkbox("Reprocess", value=False)

    uploaded = st.file_uploader("PDF", type=["pdf"])
    if uploaded is None:
        return

    if st.button("Process", type="primary"):
        settings.enable_mock_ocr = use_mock_ocr
        settings.processing_mode = mode
        settings.use_remote_gpu_worker = mode == "remote-gpu-worker"
        upload_dir = settings.raw_pdf_dir / "streamlit_uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        target = unique_path(upload_dir, f"{safe_stem(uploaded.name)}.pdf")
        with target.open("wb") as file_handle:
            shutil.copyfileobj(uploaded, file_handle)

        with st.spinner("Processing"):
            result = process_pdf(
                target,
                dpi=int(dpi),
                max_scan_pages=int(max_pages),
                stop_on_marker=True,
                remove_red_stamp=remove_red_stamp,
                use_local_llm=use_local_llm,
                force=force,
                settings=settings,
            )
        st.session_state["result"] = result

    result = st.session_state.get("result")
    if not result:
        return

    extraction = result.result
    tabs = st.tabs(["Text", "JSON", "Table", "Downloads"])
    with tabs[0]:
        st.subheader("Before marker")
        st.text_area("Text", extraction.text_before_marker or "", height=360)
        st.subheader("Warnings")
        st.write(extraction.warnings)
    with tabs[1]:
        st.json(model_to_dict(extraction))
    with tabs[2]:
        st.dataframe(rows_from_result(extraction), use_container_width=True)
    with tabs[3]:
        if result.excel_path and Path(result.excel_path).exists():
            st.download_button(
                "Excel",
                data=Path(result.excel_path).read_bytes(),
                file_name=Path(result.excel_path).name,
            )
        if result.extraction_json and Path(result.extraction_json).exists():
            st.download_button(
                "JSON",
                data=Path(result.extraction_json).read_bytes(),
                file_name=Path(result.extraction_json).name,
            )


if __name__ == "__main__":
    main()
