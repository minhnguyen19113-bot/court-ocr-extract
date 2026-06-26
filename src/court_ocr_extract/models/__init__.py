from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Any


@dataclass
class OcrLine:
    text: str
    page_number: int
    bbox: list[float] = field(default_factory=list)
    confidence: float | None = None


@dataclass
class OcrPage:
    page_number: int
    width: int | None = None
    height: int | None = None
    lines: list[OcrLine] = field(default_factory=list)
    text: str | None = None
    ocr_time: float | None = None
    image_path: str | None = None
    processed_image_path: str | None = None

    def __post_init__(self) -> None:
        self.lines = [line if isinstance(line, OcrLine) else OcrLine(**line) for line in self.lines]

    @property
    def page_text(self) -> str:
        if self.text is not None:
            return self.text
        return "\n".join(line.text for line in self.lines if line.text.strip())


@dataclass
class OcrDocument:
    source_file: str | None = None
    file_id: str | None = None
    pages: list[OcrPage] = field(default_factory=list)
    preprocessing_config: dict[str, Any] = field(default_factory=dict)
    stop_reason: str | None = None
    marker_found: bool = False
    marker_page: int | None = None
    marker_position: int | None = None
    marker_score: float | None = None
    pages_ocr: int = 0

    def __post_init__(self) -> None:
        self.pages = [page if isinstance(page, OcrPage) else OcrPage(**page) for page in self.pages]
        if not self.pages_ocr:
            self.pages_ocr = len(self.pages)

    @property
    def text(self) -> str:
        return "\n\n".join(page.page_text for page in self.pages if page.page_text.strip())


@dataclass
class FieldValue:
    value: str | None = None
    confidence: float | None = None
    evidence_text: str | None = None
    reasoning_brief: str | None = None
    source_method: str | None = None
    source_text: str | None = None
    source_span: tuple[int, int] | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.evidence_text is None and self.source_text is not None:
            self.evidence_text = self.source_text
        if self.source_text is None and self.evidence_text is not None:
            self.source_text = self.evidence_text
        if self.reasoning_brief is None and self.reason is not None:
            self.reasoning_brief = self.reason
        if self.reason is None and self.reasoning_brief is not None:
            self.reason = self.reasoning_brief


@dataclass
class CaseInfo:
    loai_an: str | None = None
    so_thu_ly: str | None = None
    ngay_thu_ly: str | None = None
    quan_he_phap_luat: str | None = None
    chu_toa: str | None = None
    field_metadata: dict[str, FieldValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.field_metadata = {
            key: value if isinstance(value, FieldValue) else FieldValue(**value)
            for key, value in self.field_metadata.items()
        }


@dataclass
class Participant:
    tu_cach_to_tung: str | None = None
    ho_ten: str | None = None
    nam_sinh: str | None = None
    cccd: str | None = None
    dia_chi: str | None = None
    ghi_chu: str | None = None
    raw_text: str | None = None
    field_metadata: dict[str, FieldValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.field_metadata = {
            key: value if isinstance(value, FieldValue) else FieldValue(**value)
            for key, value in self.field_metadata.items()
        }


@dataclass
class Entity:
    label: str
    text: str
    start: int | None = None
    end: int | None = None
    score: float | None = None
    source_method: str = "gliner"


@dataclass
class ExtractorOutput:
    method: str
    case_fields: dict[str, FieldValue] = field(default_factory=dict)
    participants: list[dict[str, FieldValue]] = field(default_factory=list)
    entities: list[Entity] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.case_fields = {
            key: value if isinstance(value, FieldValue) else FieldValue(**value)
            for key, value in self.case_fields.items()
        }
        self.participants = [
            {
                key: value if isinstance(value, FieldValue) else FieldValue(**value)
                for key, value in participant.items()
            }
            for participant in self.participants
        ]
        self.entities = [entity if isinstance(entity, Entity) else Entity(**entity) for entity in self.entities]


@dataclass
class ExtractionResult:
    source_file: str | None = None
    marker_found: bool = False
    marker_text: str | None = None
    marker_page: int | None = None
    text_before_marker: str | None = None
    corrected_text: str | None = None
    case_info: CaseInfo = field(default_factory=CaseInfo)
    participants: list[Participant] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_extractor_outputs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.case_info, dict):
            self.case_info = CaseInfo(**self.case_info)
        self.participants = [
            participant if isinstance(participant, Participant) else Participant(**participant)
            for participant in self.participants
        ]


@dataclass
class FileProcessMetadata:
    file_id: str
    filename: str
    path: str
    page_count: int = 0
    status: str = "pending"
    pages_ocr: int = 0
    marker_page: int | None = None
    stop_reason: str | None = None
    error: str | None = None


@dataclass
class ProcessResult:
    result: ExtractionResult
    metadata: FileProcessMetadata | None = None
    source_pdf: str | None = None
    stored_pdf: str | None = None
    ocr_raw_json: str | None = None
    corrected_text_path: str | None = None
    text_before_marker_path: str | None = None
    extraction_json: str | None = None
    excel_path: str | None = None
    bbox_debug_images: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if isinstance(self.result, dict):
            self.result = ExtractionResult(**self.result)
        if isinstance(self.metadata, dict):
            self.metadata = FileProcessMetadata(**self.metadata)

    @property
    def normalized_text_path(self) -> str | None:
        return self.corrected_text_path


def model_to_dict(model: Any) -> dict[str, Any]:
    if is_dataclass(model):
        return asdict(model)
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    if isinstance(model, dict):
        return model
    raise TypeError(f"Cannot convert {type(model)!r} to dict")


def path_to_str(path: str | Path | None) -> str | None:
    return str(path) if path is not None else None
