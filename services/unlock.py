import os
import sys
import glob

from pikepdf import Pdf

from .utils import get_size_mb, ensure_pdf_header, load_producer_cache, save_producer_cache, PRODUCER_CACHE_FILE


def unlock_pdf(input_path: str, output_path: str, password: str = "") -> None:
    """Remove encryption from a PDF, preserving original version and metadata."""
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print(f"[INFO] Opening (for unlock): {input_path}  ({get_size_mb(input_path):.2f} MB)")

    with Pdf.open(input_path, password=password) as pdf:
        original_version = pdf.pdf_version

        try:
            with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
                pass
        except Exception:
            pass

        if "/Producer" in pdf.docinfo:
            producer = pdf.docinfo.get("/Producer")
            pdf.docinfo["/Producer"] = producer

        pdf.save(
            output_path,
            encryption=None,
            compress_streams=True,
            object_stream_mode=__import__("pikepdf").ObjectStreamMode.disable,
            recompress_flate=True,
        )

    final_size = get_size_mb(output_path)
    print(f"\n[DONE] Unlocked and saved: {output_path}")
    print(f"       PDF Version : {original_version}")
    print(f"       File Size   : {final_size:.2f} MB")

    try:
        ensure_pdf_header(output_path, original_version)
    except Exception:
        pass


def unlock_folder(input_dir: str, output_dir: str, password: str = "") -> int:
    """Unlock all PDFs in input_dir, save to output_dir, and cache original producers."""
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
            print(f"[INFO] Unlocking: {pdf_path}")

            with Pdf.open(pdf_path, password=password) as src:
                producer = None
                if "/Producer" in src.docinfo:
                    producer = str(src.docinfo["/Producer"])
                if not producer:
                    try:
                        with src.open_metadata(set_pikepdf_as_editor=False) as meta:
                            producer = meta.get("pdf:Producer")
                    except Exception:
                        pass
                if producer:
                    stem = os.path.splitext(basename)[0]
                    cache[stem] = producer

            unlock_pdf(pdf_path, output_path, password=password)
            count += 1
        except Exception as e:
            print(f"[ERROR] Failed to unlock {pdf_path}: {e}", file=sys.stderr)

    save_producer_cache(cache)
    print(f"[INFO] Producer cache saved to {PRODUCER_CACHE_FILE}")
    return count
