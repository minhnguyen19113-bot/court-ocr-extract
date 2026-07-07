# Current Rebuild Direction

This repository is now driven by the real-data pilot workflow:

```text
real court PDFs uploaded by the user
-> step-by-step visual QA
-> OCR cache
-> extraction preview
-> Excel
-> QA from Excel
-> full run only after user acceptance
```

Do not use fake data to judge OCR or extraction quality. Automated unit tests may use minimal non-real contract fixtures only to verify schema/control-flow, never to decide whether the pipeline is good enough for court data.

Codex must not open, read, OCR, parse, summarize, or quote real PDFs or derived real-data artifacts. The user runs the pilot/full workflows directly on the VM or local machine.

Primary commands are documented in `README.md`, `docs/ezycloudx_runbook.md`, and `docs/visual_qa_guide.md`.
