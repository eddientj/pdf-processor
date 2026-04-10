"""
PDF Processor — CLI entry point.

Usage:
  python pdfprocessor.py <input> <output> [OPTIONS]
  python pdfprocessor.py <input_dir> <output_dir> --unlock-folder
  python pdfprocessor.py <input_dir> <output_dir> --compress-folder
  python pdfprocessor.py <input_dir> <output_dir> --patch-version-folder
  python pdfprocessor.py <input_dir> <output_dir> --patch-metadata-folder
  python pdfprocessor.py --flush
"""

import sys
import argparse

# Load .env if present (for ILOVEPDF_PUBLIC_KEY / ILOVEPDF_SECRET_KEY)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from services.unlock import unlock_pdf, unlock_folder
from services.compress import process_pdf, compress_folder_ilovepdf
from services.metadata import apply_properties, patch_metadata_folder, patch_version_folder
from services.flush import flush_all_except_input


def main():
    parser = argparse.ArgumentParser(
        description="Unlock, compress, and patch metadata for PDF files."
    )
    parser.add_argument("input", nargs="?", default=None, help="Path to input PDF file or folder")
    parser.add_argument("output", nargs="?", default=None, help="Path for output PDF file or folder")
    parser.add_argument("--user-password", "-u", default="", help="Password to open the PDF")
    parser.add_argument("--owner-password", "-o", default="", help="Owner/permissions password")
    parser.add_argument("--max-size", "-s", type=float, default=14.0, help="Max output size in MB (default: 14.0)")
    parser.add_argument("--unlock", action="store_true", help="Unlock a single encrypted PDF")
    parser.add_argument("--apply-properties", action="store_true", help="Apply KWSP producer to a single PDF")
    parser.add_argument("--unlock-folder", action="store_true", help="Unlock all PDFs in input folder")
    parser.add_argument("--compress-folder", action="store_true", help="Compress all PDFs via iLovePDF API")
    parser.add_argument("--patch-metadata-folder", action="store_true", help="Apply KWSP producer to all PDFs in input folder")
    parser.add_argument("--patch-version-folder", action="store_true", help="Patch version to 1.4, restore original producer for all PDFs in input folder")
    parser.add_argument("--today-dates", action="store_true", help="Set CreationDate and ModDate to today's date (use with --patch-version-folder)")
    parser.add_argument("--flush", action="store_true", help="Clear Output, 'To Compress', and 'Compressed' folders")
    args = parser.parse_args()

    try:
        if args.flush:
            count = flush_all_except_input()
            print(f"[SUMMARY] Flushed {count} files from working folders")
            return

        if args.input is None or args.output is None:
            parser.print_help()
            print("\n[ERROR] input and output are required", file=sys.stderr)
            sys.exit(1)

        if args.unlock:
            unlock_pdf(args.input, args.output, password=args.user_password)
        elif args.apply_properties:
            apply_properties(args.input, args.output, password=args.user_password)
        elif args.unlock_folder:
            count = unlock_folder(args.input, args.output, password=args.user_password)
            print(f"[SUMMARY] Unlocked {count} PDFs from {args.input} to {args.output}")
        elif args.compress_folder:
            count = compress_folder_ilovepdf(args.input, args.output)
            print(f"[SUMMARY] Compressed {count} PDFs from {args.input} to {args.output}")
        elif args.patch_metadata_folder:
            count = patch_metadata_folder(args.input, args.output, password=args.user_password)
            print(f"[SUMMARY] Patched metadata for {count} PDFs from {args.input} to {args.output}")
        elif args.patch_version_folder:
            count = patch_version_folder(args.input, args.output, password=args.user_password, today_dates=args.today_dates)
            print(f"[SUMMARY] Patched version for {count} PDFs from {args.input} to {args.output}")
        else:
            process_pdf(
                input_path=args.input,
                output_path=args.output,
                user_password=args.user_password,
                owner_password=args.owner_password,
                target_max_mb=args.max_size,
            )

    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
