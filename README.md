PDF Processor
=============

A Python tool for batch unlocking, compressing (via iLovePDF API), and applying metadata to PDF files.

- Unlock encrypted PDFs in bulk
- Compress via iLovePDF API — same quality as the website, fully automated
- Patch PDF version to 1.7 while restoring the original producer (Bank Statements)
- Patch PDF version to 1.4 while applying KWSP producer metadata (EPF Statements)
- Strip Infix Pro custom fields (ICNAppName, ICNAppPlatform, ICNAppVersion) automatically
- Encrypt output PDFs with a password and restricted permissions
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

Workflow
--------

### Step 1 — Unlock all PDFs
Removes encryption and snapshots each file's original producer to `.producer_cache.json`:
```powershell
python pdfprocessor.py Input "To Compress" --unlock-folder
```

### Step 2 — Compress via iLovePDF API
Sends each PDF to the iLovePDF API and downloads the compressed result to `Compressed/`:
```powershell
python pdfprocessor.py "To Compress" Compressed --compress-folder
```
Free tier: 250 tasks/month. iLovePDF appends a `_compress` suffix to output filenames.

---

### Step 3a — Bank Statements
Patches version to 1.7, restores the original producer, stamps today's date, and encrypts the
output — with only page extraction restricted (printing, editing, and document assembly are all allowed).
The output password is configured via `BANK_STATEMENT_OUTPUT_PASSWORD` in `services/constants.py`:
```powershell
python pdfprocessor.py Compressed Output --patch-version-folder --today-dates
```

### Step 3b — EPF Statements
Applies KWSP producer metadata only (PDF 1.4), with no recompression and no encryption:
```powershell
python pdfprocessor.py Compressed Output --patch-metadata-folder
```

---

### Step 4 — Clean Up (Optional)
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
├── .producer_cache.json      # Auto-generated: maps filenames to original producer string
├── .temp_file_cache          # Temporary file cache (not committed to git)
├── pdfprocessor.py           # Main script
├── requirement.txt           # Python dependencies
├── services/constants.py     # Configurable variables (PDF versions, password, producer, etc.)
├── .gitignore                # Excludes PDFs and secrets from version control
└── README.md                 # This file
```

Notes
-----
- **Configurable constants:** PDF versions, output password, producer name, compression settings, and flush folders are all defined in `services/constants.py` — edit that file to change behaviour without touching the processing code.
- **Metadata cache:** `--unlock-folder` saves `.producer_cache.json` with the original producer string for each file. `--patch-version-folder` uses this to restore the correct producer after iLovePDF compression overwrites it.
- **Filename matching:** `--patch-version-folder` automatically strips the `_compress`/`_compressed` suffix when looking up the producer cache.
- **ICN field stripping:** `--patch-version-folder` removes `ICNAppName`, `ICNAppPlatform`, and `ICNAppVersion` from the PDF Info dictionary (Infix Pro fields not visible in the final output).
- **PDF versions:** Bank Statements are written as PDF 1.7; EPF Statements are written as PDF 1.4. Both versions are set via `services/constants.py`.
- **Date stamping:** `--today-dates` writes the current local date and time (with timezone) to both DocInfo and XMP metadata, so Adobe Acrobat shows the correct Created/Modified dates.
- **Encryption:** Bank Statement outputs are encrypted using `BANK_STATEMENT_OUTPUT_PASSWORD` from `services/constants.py`. Only page extraction is restricted — printing, editing, form-filling, and document assembly remain fully allowed.
- **Minimal recompression:** Both `--patch-version-folder` and `--patch-metadata-folder` apply changes without recompressing, preserving iLovePDF compression gains.
- **iLovePDF free tier:** 250 tasks/month. Each file = 1 task. See https://developer.ilovepdf.com/pricing for details.
- **.gitignore:** PDF files, `.env`, `.producer_cache.json`, and `.temp_file_cache` are excluded from version control.
