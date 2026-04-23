# ── Bank Statements  (--patch-version-folder) ────────────────────────────────
BANK_STATEMENT_PDF_VERSION = "1.7"
BANK_STATEMENT_OUTPUT_PASSWORD = "1234"

# ── EPF Statements  (--patch-metadata-folder) ────────────────────────────────
EPF_STATEMENT_PDF_VERSION = "1.4"

# ── Compression pipeline ─────────────────────────────────────────────────────
COMPRESS_PDF_VERSION = "1.7"
COMPRESS_TARGET_MAX_MB = 14.0
COMPRESS_IMAGE_QUALITIES = [75, 60, 45, 30]
COMPRESS_IMAGE_SCALES = [1.0, 0.9, 0.75, 0.5]

# ── Metadata ──────────────────────────────────────────────────────────────────
PRODUCER_NAME = "KWSP"
ICN_FIELDS_TO_STRIP = ["/ICNAppName", "/ICNAppPlatform", "/ICNAppVersion"]

# ── Flush ─────────────────────────────────────────────────────────────────────
FLUSH_FOLDERS = ["Output", "To Compress", "Compressed"]
