PDF Processor
=============

A Python tool for batch unlocking, compressing (via iLovePDF API), and applying metadata to PDF files.
- Unlock encrypted PDFs in bulk
- Compress via iLovePDF API — same quality as the website, fully automated
- Patch PDF version to 1.4 while restoring the original producer
- Preserve original custom metadata (Creator, ICNAppName, ICNAppPlatform, ICNAppVersion, etc.)
- Apply KWSP producer metadata without additional compression
- Clean up temporary files with a single command

Prerequisites
-------------
- **Python 3.8+** (workspace uses Python 3.14)
- **Install dependencies:**
  ```powershell
  python -m pip install -r requirement.txt
  ```
- **iLovePDF API keys** (for `--compress-folder`):
  1. Register at https://developer.ilovepdf.com
  2. Copy your Public Key and Secret Key
  3. Create a `.env` file in this directory (see `.env.example`):
     ```
     ILOVEPDF_PUBLIC_KEY=your_public_key_here
     ILOVEPDF_SECRET_KEY=your_secret_key_here
     ```

Workflow: Unlock → Compress → Restore Metadata
-----------------------------------------------

### Step 1: Unlock all PDFs
Removes encryption and snapshots the original metadata of each file to `.producer_cache.json`:
- Producer string
- All docinfo fields: `Creator`, `ICNAppName`, `ICNAppPlatform`, `ICNAppVersion`, and any other custom entries

```powershell
python pdfprocessor.py Input "To Compress" --unlock-folder
```

### Step 2: Compress via iLovePDF API
Sends each PDF to the iLovePDF API and downloads the compressed result to `Compressed/`:
```powershell
python pdfprocessor.py "To Compress" Compressed --compress-folder
```
Free tier: 250 tasks/month. Files are named with a `_compress` suffix by iLovePDF.

### Step 3a: Patch Version + Restore Original Producer (recommended)
Patches PDF version to 1.4 and restores the original producer from Step 1's cache:
```powershell
python pdfprocessor.py Compressed Output --patch-version-folder
```
Filename matching strips `_compress`/`_compressed` suffix automatically.

Add `--today-dates` to stamp the current date and time as the PDF's Created and Modified dates (visible in Adobe Acrobat under File → Properties → Description):
```powershell
python pdfprocessor.py Compressed Output --patch-version-folder --today-dates
```

Add `--preserve-custom-information` to restore the original `Creator` and all custom docinfo fields (e.g. `ICNAppName`, `ICNAppPlatform`, `ICNAppVersion`) that were snapshotted during Step 1:
```powershell
python pdfprocessor.py Compressed Output --patch-version-folder --today-dates --preserve-custom-information
```

All three flags can be combined freely:
```powershell
python pdfprocessor.py Compressed Output --patch-version-folder --today-dates --preserve-custom-information
```

### Step 3b: Apply KWSP Metadata Instead
Overrides the producer with `KWSP` and patches the version — use if you want KWSP branding:
```powershell
python pdfprocessor.py Compressed Output --patch-metadata-folder
```

### Step 4: Clean Up (Optional)
Clears `Output/`, `To Compress/`, and `Compressed/` folders (preserves `Input/`):
```powershell
python pdfprocessor.py --flush
```

Single-File Operations
----------------------

**Unlock a password-protected PDF:**
```powershell
python pdfprocessor.py Input\locked.pdf Output\unlocked.pdf --unlock -u "password"
```

**Apply metadata and standard compression to a single file:**
```powershell
python pdfprocessor.py Input\example.pdf Output\final_example.pdf --apply-properties
```

**Apply metadata only (minimal recompression):**
```powershell
python pdfprocessor.py Compressed\compressed.pdf Output\final.pdf --patch-metadata-folder
```

Folder Structure
----------------
```
pdf-processer/
├── Input/                    # Original encrypted PDFs (source, not modified by flush)
├── To Compress/              # Unlocked PDFs (ready for compression)
├── Compressed/               # iLovePDF-compressed PDFs
├── Output/                   # Final output PDFs
├── .env                      # API keys (not committed to git)
├── .env.example              # Template for .env
├── .producer_cache.json      # Auto-generated: maps filenames to original producer + custom metadata
├── .temp_file_cache          # Temporary file cache (not committed to git)
├── pdfprocessor.py           # Main script
├── requirement.txt           # Python dependencies
├── .gitignore                # Excludes PDFs and secrets from version control
└── README.md                 # This file
```

Notes
-----
- **Metadata cache:** `--unlock-folder` saves `.producer_cache.json` with the original producer string plus all custom docinfo fields (`Creator`, `ICNAppName`, `ICNAppPlatform`, `ICNAppVersion`, etc.). The cache format is automatically migrated if you have an older single-producer cache file.
- **Custom metadata preservation:** `--preserve-custom-information` (used with `--patch-version-folder`) restores all cached docinfo fields after iLovePDF compression overwrites them. `Creator` is also written to the XMP stream (`xmp:CreatorTool`).
- **PDF Version:** The tool ensures files present as PDF 1.4 by disabling object streams (a PDF 1.5 feature).
- **Minimal metadata patching:** Both `--patch-version-folder` and `--patch-metadata-folder` apply changes without recompressing, preserving iLovePDF compression gains.
- **Date stamping:** `--today-dates` writes the current local date and time (including timezone) to both the PDF DocInfo and XMP metadata streams so that Adobe Acrobat displays the correct Created/Modified dates.
- **iLovePDF free tier:** 250 tasks/month. Each file = 1 task. See https://developer.ilovepdf.com/pricing for details.
- **Encryption:** Single-file unlock mode supports password-protected PDFs. Batch unlock (`--unlock-folder`) assumes no password; use single-file mode for encrypted batches.
- **.gitignore:** PDF files, `.env`, `.producer_cache.json`, and `.temp_file_cache` are excluded from version control.
