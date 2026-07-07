# Model Benchmark Notes

Last updated: 2026-07-07

This document records model direction only. Phase 1B does not implement model runtime.

## OCR

- Main OCR candidate: Surya OCR.
- Output should include text, bbox, reading order, and confidence/layout metadata when available.
- Review UI must show bbox overlay on page image with corresponding text.

## Local LLM Extraction

Preferred direction:

- RTX 3090 24GB: Qwen2.5-32B-Instruct quantized, or Qwen2.5-32B through vLLM if stable.
- RTX 5060 Ti around 16GB: Qwen2.5-14B-Instruct quantized, fallback Qwen2.5-7B-Instruct.
- Temperature: `0`.
- JSON output must be strict.
- Every field must include evidence.
- No fine-tuning before benchmark and gold dataset exist.

## VLM Benchmark

Candidate order:

1. Qwen2.5-VL-7B-Instruct.
2. Qwen3-VL-8B if VM/runtime supports it.
3. Qwen3-VL-32B only if the VM is strong enough.

The VLM path must produce comparable validation, QA, and debug output to the Surya path.

## Benchmark Gates

- Local-only by default.
- No cloud API calls unless Project Owner explicitly approves.
- Compare JSON validity, evidence coverage, hallucination warnings, QA warning counts, and reviewer usability.
- Do not use synthetic fixtures to judge real quality.
