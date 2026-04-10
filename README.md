PDF Processor
=============

A Python tool for batch unlocking, compressing (via iLovePDF API), and applying metadata to PDF files.
- Unlock encrypted PDFs in bulk
- Compress via iLovePDF API — same quality as the website, fully automated
- Patch PDF version to 1.4 while restoring the original producer
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
Removes encryption and saves the original producer of each file to `.producer_cache.json`:
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
├── .producer_cache.json      # Auto-generated: maps filenames to original producers
├── pdfprocessor.py           # Main script
├── requirement.txt           # Python dependencies
├── .gitignore                # Excludes PDFs and secrets from version control
└── README.md                 # This file
```

Notes
-----
- **Producer cache:** `--unlock-folder` saves `.producer_cache.json`. `--patch-version-folder` reads it to restore the original producer even after iLovePDF overwrites it.
- **PDF Version:** The tool ensures files present as PDF 1.4 by disabling object streams (a PDF 1.5 feature).
- **Minimal metadata patching:** Both `--patch-version-folder` and `--patch-metadata-folder` apply changes without recompressing, preserving iLovePDF compression gains.
- **Date stamping:** `--today-dates` writes the current local date and time (including timezone) to both the PDF DocInfo and XMP metadata streams so that Adobe Acrobat displays the correct Created/Modified dates.
- **iLovePDF free tier:** 250 tasks/month. Each file = 1 task. See https://developer.ilovepdf.com/pricing for details.
- **Encryption:** Single-file unlock mode supports password-protected PDFs. Batch unlock (`--unlock-folder`) assumes no password; use single-file mode for encrypted batches.
- **.gitignore:** PDF files, `.env`, and `.producer_cache.json` are excluded from version control.
