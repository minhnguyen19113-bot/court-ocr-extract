#!/usr/bin/env bash
set -euo pipefail

echo "This will remove private PDFs, rendered images, OCR raw/corrected text, and logs from this instance."
read -r -p "Type DELETE to continue: " CONFIRM
if [ "$CONFIRM" != "DELETE" ]; then
  echo "Cancelled."
  exit 0
fi

rm -rf data/private_pdfs/*
rm -rf data/raw_pdfs/*
rm -rf data/images/*
rm -rf data/processed_images/*
rm -rf data/processed/*
rm -rf data/ocr_raw/*
rm -rf data/ocr_corrected/*
rm -rf outputs/logs/*

echo "Sensitive runtime data removed. Review outputs/excel and outputs/json separately before deleting or downloading."
