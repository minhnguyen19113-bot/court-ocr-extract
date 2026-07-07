$ErrorActionPreference = "Stop"
$workspace = (Resolve-Path ".").Path
$targets = @(
  "data\raw_pdfs",
  "data\private_pdfs",
  "data\images",
  "data\processed_images",
  "data\ocr_raw",
  "data\ocr_corrected",
  "outputs"
)

foreach ($target in $targets) {
  $resolved = Resolve-Path -LiteralPath $target -ErrorAction SilentlyContinue
  if ($resolved) {
    $path = $resolved.Path
    if (-not $path.StartsWith($workspace, [System.StringComparison]::OrdinalIgnoreCase)) {
      throw "Refusing to delete outside workspace: $path"
    }
    Remove-Item -LiteralPath $path -Recurse -Force
  }
}

Write-Host "Sensitive runtime folders cleaned."
