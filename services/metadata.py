import os
import sys
import glob
from datetime import datetime

from pikepdf import Pdf, String

from .utils import get_size_mb, ensure_pdf_header, load_producer_cache


def _pdf_date_string(dt: datetime) -> str:
    """Return a PDF docinfo date string (D:YYYYMMDDHHmmSS+HH'mm') for the given datetime."""
    offset = dt.utcoffset()
    if offset is None:
        return f"D:{dt.strftime('%Y%m%d%H%M%S')}"
    total = int(offset.total_seconds())
    sign = '+' if total >= 0 else '-'
    h, m = divmod(abs(total), 3600)
    return f"D:{dt.strftime('%Y%m%d%H%M%S')}{sign}{h:02d}'{m // 60:02d}'"


def _xmp_date_string(dt: datetime) -> str:
    """Return an ISO-8601 XMP date string (YYYY-MM-DDTHH:mm:ss+HH:mm) for the given datetime."""
    offset = dt.utcoffset()
    if offset is None:
        return dt.strftime('%Y-%m-%dT%H:%M:%S')
    total = int(offset.total_seconds())
    sign = '+' if total >= 0 else '-'
    h, m = divmod(abs(total), 3600)
    return f"{dt.strftime('%Y-%m-%dT%H:%M:%S')}{sign}{h:02d}:{m // 60:02d}"


def apply_properties(input_path: str, output_path: str, password: str = "") -> None:
    """Set Producer to KWSP on a single PDF, preserving all other metadata."""
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print(f"[INFO] Opening (apply properties): {input_path}  ({get_size_mb(input_path):.2f} MB)")

    with Pdf.open(input_path, password=password) as pdf:
        try:
            with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
                meta["pdf:Producer"] = "KWSP"
        except Exception:
            pass

        pdf.docinfo["/Producer"] = String("KWSP")

        pdf.save(
            output_path,
            encryption=None,
            compress_streams=True,
            object_stream_mode=__import__("pikepdf").ObjectStreamMode.disable,
            recompress_flate=True,
        )

    try:
        ensure_pdf_header(output_path, "1.4")
    except Exception:
        pass

    final_size = get_size_mb(output_path)
    print(f"\n[DONE] Properties applied and saved: {output_path}")
    print(f"       File Size   : {final_size:.2f} MB")


def patch_metadata_only(input_pdf: str, output_pdf: str, password: str = "") -> None:
    """Apply KWSP producer metadata without any recompression."""
    if not os.path.isfile(input_pdf):
        raise FileNotFoundError(f"Input file not found: {input_pdf}")

    print(f"[INFO] Patching metadata (no compression): {input_pdf}")

    with Pdf.open(input_pdf, password=password) as pdf:
        try:
            with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
                meta["pdf:Producer"] = "KWSP"
        except Exception:
            pass

        pdf.docinfo["/Producer"] = String("KWSP")
        pdf.save(output_pdf, encryption=None)

    try:
        ensure_pdf_header(output_pdf, "1.4")
    except Exception:
        pass

    final_size = get_size_mb(output_pdf)
    print(f"[DONE] Metadata patched: {output_pdf}")
    print(f"       File Size : {final_size:.2f} MB")


def patch_version_only(input_pdf: str, output_pdf: str, password: str = "", original_producer: str = None, today_dates: bool = False) -> None:
    """Patch PDF version to 1.4. Restores original_producer if provided, else keeps current. No recompression."""
    if not os.path.isfile(input_pdf):
        raise FileNotFoundError(f"Input file not found: {input_pdf}")

    print(f"[INFO] Patching version only (keep producer): {input_pdf}")

    with Pdf.open(input_pdf, password=password) as pdf:
        # Resolve producer from cache arg, then docinfo, then XMP — in that priority order
        producer = original_producer
        if not producer:
            if "/Producer" in pdf.docinfo:
                producer = str(pdf.docinfo["/Producer"])
            if not producer:
                try:
                    with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
                        producer = meta.get("pdf:Producer")
                except Exception:
                    pass

        # Resolve current local datetime strings before entering the XMP block
        today_pdf_date = None
        today_xmp_date = None
        now = None
        if today_dates:
            now = datetime.now().astimezone()  # local time with local timezone offset
            today_pdf_date = _pdf_date_string(now)
            today_xmp_date = _xmp_date_string(now)

        # Single XMP write — avoids two open_metadata calls overwriting each other
        try:
            with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
                if producer:
                    meta["{http://ns.adobe.com/pdf/1.3/}Producer"] = producer
                if today_xmp_date:
                    meta["{http://ns.adobe.com/xap/1.0/}CreateDate"] = today_xmp_date
                    meta["{http://ns.adobe.com/xap/1.0/}ModifyDate"] = today_xmp_date
        except Exception as xmp_err:
            print(f"[WARNING] XMP metadata write failed: {xmp_err}", file=sys.stderr)

        # Docinfo (classic PDF Info dict) — always set alongside XMP
        if producer:
            pdf.docinfo["/Producer"] = String(producer)
        if today_pdf_date:
            pdf.docinfo["/CreationDate"] = String(today_pdf_date)
            pdf.docinfo["/ModDate"] = String(today_pdf_date)
            print(f"[INFO] Dates set to: {now.strftime('%Y-%m-%d %H:%M:%S %z')}")

        pdf.save(output_pdf, encryption=None)

    try:
        ensure_pdf_header(output_pdf, "1.4")
    except Exception:
        pass

    final_size = get_size_mb(output_pdf)
    print(f"[DONE] Version patched: {output_pdf}")
    print(f"       Producer  : {producer or '(unknown)'}")
    print(f"       File Size : {final_size:.2f} MB")


def patch_metadata_folder(input_dir: str, output_dir: str, password: str = "") -> int:
    """Apply KWSP metadata to all PDFs in input_dir (no recompression)."""
    if not os.path.isdir(input_dir):
        print(f"[ERROR] Input directory not found: {input_dir}", file=sys.stderr)
        return 0
    os.makedirs(output_dir, exist_ok=True)

    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
    if not pdf_files:
        print(f"[WARNING] No PDF files found in {input_dir}")
        return 0

    count = 0
    for pdf_path in sorted(pdf_files):
        try:
            basename = os.path.basename(pdf_path)
            output_path = os.path.join(output_dir, basename)
            patch_metadata_only(pdf_path, output_path, password=password)
            count += 1
        except Exception as e:
            print(f"[ERROR] Failed to patch {pdf_path}: {e}", file=sys.stderr)
    return count


def patch_version_folder(input_dir: str, output_dir: str, password: str = "", today_dates: bool = False) -> int:
    """Patch PDF version to 1.4 for all PDFs, restoring original producer from cache."""
    if not os.path.isdir(input_dir):
        print(f"[ERROR] Input directory not found: {input_dir}", file=sys.stderr)
        return 0
    os.makedirs(output_dir, exist_ok=True)

    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
    if not pdf_files:
        print(f"[WARNING] No PDF files found in {input_dir}")
        return 0

    cache = load_producer_cache()
    count = 0
    for pdf_path in sorted(pdf_files):
        try:
            basename = os.path.basename(pdf_path)
            output_path = os.path.join(output_dir, basename)

            stem = os.path.splitext(basename)[0]
            for suffix in ("_compressed", "_compress", "_comp"):
                if stem.endswith(suffix):
                    stem = stem[: -len(suffix)]
                    break
            original_producer = cache.get(stem)
            if original_producer:
                print(f"[INFO] Restoring producer from cache: '{original_producer}' for {basename}")

            patch_version_only(pdf_path, output_path, password=password, original_producer=original_producer, today_dates=today_dates)
            count += 1
        except Exception as e:
            print(f"[ERROR] Failed to patch {pdf_path}: {e}", file=sys.stderr)
    return count
