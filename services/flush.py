import os
import sys
import glob

from .constants import FLUSH_FOLDERS


def flush_all_except_input(base_dir: str = ".") -> int:
    """Delete all PDF files from Output, 'To Compress', and 'Compressed' folders."""
    folders_to_clear = FLUSH_FOLDERS
    deleted_count = 0

    for folder in folders_to_clear:
        folder_path = os.path.join(base_dir, folder)
        if not os.path.isdir(folder_path):
            continue
        try:
            pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
            for pdf_file in pdf_files:
                try:
                    os.remove(pdf_file)
                    deleted_count += 1
                except Exception as e:
                    print(f"[WARNING] Failed to delete {pdf_file}: {e}", file=sys.stderr)
            if pdf_files:
                print(f"[INFO] Cleared {len(pdf_files)} PDF files from '{folder}' folder")
        except Exception as e:
            print(f"[WARNING] Failed to access '{folder}': {e}", file=sys.stderr)

    return deleted_count
