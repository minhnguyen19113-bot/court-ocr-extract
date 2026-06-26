from scripts.qa_batch_output import summarize_batch


def test_summarize_batch_outputs_counts_not_values():
    summary = {
        "total": 1,
        "success": 1,
        "failed": 0,
        "skipped": 0,
        "results": [
            {
                "marker_found": True,
                "case_info": {
                    "loai_an": "Synthetic Case",
                    "so_thu_ly": None,
                    "ngay_thu_ly": None,
                    "quan_he_phap_luat": None,
                    "chu_toa": None,
                },
                "participants": [
                    {
                        "tu_cach_to_tung": "Synthetic Role",
                        "ho_ten": "co mat tai phien toa",
                        "nam_sinh": "not-year",
                        "cccd": "123",
                        "dia_chi": None,
                    }
                ],
                "warnings": ["Thiếu thông tin chung: SỐ THỤ LÝ"],
                "metadata": {"review_required": True, "primary_extractor": "heuristic_support"},
            }
        ],
    }

    report = summarize_batch(summary)

    assert report["batch"]["success"] == 1
    assert report["case_fields"]["SO_THU_LY"]["empty"] == 1
    assert report["participant_fields"]["HO_TEN"]["non_empty"] == 1
    assert report["extractors"]["heuristic_support"] == 1
    assert report["suspicious_counts"]["suspicious_name_like_phrase"] == 1
    assert "co mat tai phien toa" not in str(report)
