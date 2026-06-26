from __future__ import annotations

from court_ocr_extract.models import Entity, ExtractorOutput


class GLiNERExtractor:
    method = "gliner"

    def __init__(self, settings) -> None:
        self.settings = settings
        self._model = None

    def extract(self, text: str) -> ExtractorOutput:
        if not getattr(self.settings, "enable_gliner", False):
            return ExtractorOutput(method=self.method)
        if getattr(self.settings, "enable_mock_gliner", False):
            return ExtractorOutput(method=self.method, entities=[])

        try:
            from gliner import GLiNER
        except Exception as exc:
            return ExtractorOutput(method=self.method, warnings=[f"GLiNER chưa sẵn sàng: {exc}"])

        if self._model is None:
            self._model = GLiNER.from_pretrained(self.settings.gliner_model)

        labels = [
            "person_name",
            "birth_year",
            "identity_number",
            "address",
            "role",
            "case_number",
            "judge_name",
            "charge_or_legal_relation",
        ]
        predictions = self._model.predict_entities(text, labels, threshold=0.35)
        entities = [
            Entity(
                label=str(item.get("label")),
                text=str(item.get("text")),
                start=item.get("start"),
                end=item.get("end"),
                score=item.get("score"),
                source_method=self.method,
            )
            for item in predictions
        ]
        return ExtractorOutput(method=self.method, entities=entities)
