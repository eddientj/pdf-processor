import os
import sys
import io
import glob

import pikepdf
from pikepdf import Pdf, Name, String
from PIL import Image

from .utils import get_size_mb, ensure_pdf_header


def compress_images(pdf: Pdf, quality: int = 60, scale: float = 1.0) -> None:
    """Re-compress inline JPEG images to reduce file size."""
    for page in pdf.pages:
        if "/Resources" not in page:
            continue
        resources = page["/Resources"]
        if "/XObject" not in resources:
            continue
        xobjects = resources["/XObject"]
        for key in xobjects.keys():
            xobj = xobjects[key]
            if xobj.get("/Subtype") == Name("/Image"):
                try:
                    if xobj.get("/Filter") in (Name("/DCTDecode"), None):
                        raw = xobj.read_raw_bytes()
                        img = Image.open(io.BytesIO(raw))
                        if scale and scale < 1.0:
                            new_size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
                            img = img.resize(new_size, Image.LANCZOS)
                        buf = io.BytesIO()
                        img.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
                        compressed = buf.getvalue()
                        if len(compressed) < len(raw):
                            xobj.write(compressed, filter=Name("/DCTDecode"))
                except Exception:
                    pass


def process_pdf(
    input_path: str,
    output_path: str,
    user_password: str = "",
    owner_password: str = "",
    target_max_mb: float = 14.0,
) -> None:
    """Full single-file pipeline: set version + KWSP metadata, compress, optionally encrypt."""
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not owner_password:
        owner_password = user_password

    print(f"[INFO] Opening: {input_path}  ({get_size_mb(input_path):.2f} MB)")

    save_kwargs = dict(
        compress_streams=True,
        object_stream_mode=pikepdf.ObjectStreamMode.disable,
        recompress_flate=True,
    )

    with Pdf.open(input_path) as pdf:
        pdf.pdf_version = "1.4"
        with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
            meta["pdf:Producer"] = "KWSP"
        pdf.docinfo["/Producer"] = String("KWSP")

        tmp_path = output_path + ".tmp.pdf"
        pdf.save(tmp_path, **save_kwargs)

    size_mb = get_size_mb(tmp_path)
    print(f"[INFO] Size after initial compression: {size_mb:.2f} MB")

    for quality in [75, 60, 45, 30]:
        for scale in [1.0, 0.9, 0.75, 0.5]:
            if size_mb <= target_max_mb:
                break
            print(f"[INFO] Over {target_max_mb} MB — re-compressing images at quality={quality}, scale={scale}...")
            with Pdf.open(tmp_path) as pdf2:
                compress_images(pdf2, quality=quality, scale=scale)
                pdf2.save(tmp_path, **save_kwargs)
            size_mb = get_size_mb(tmp_path)
            print(f"[INFO] Size after image compression (q={quality}, s={scale}): {size_mb:.2f} MB")

    if size_mb > target_max_mb:
        print(
            f"[WARNING] Could not reduce file below {target_max_mb} MB automatically "
            f"(current: {size_mb:.2f} MB)."
        )

    with Pdf.open(tmp_path) as pdf_final:
        pdf_final.pdf_version = "1.4"
        with pdf_final.open_metadata(set_pikepdf_as_editor=False) as meta:
            meta["pdf:Producer"] = "KWSP"
        pdf_final.docinfo["/Producer"] = String("KWSP")

        encryption = None
        if user_password or owner_password:
            encryption = pikepdf.Encryption(
                user=user_password,
                owner=owner_password,
                R=3,
                allow=pikepdf.Permissions(
                    print_lowres=True,
                    print_highres=False,
                    modify_other=False,
                    extract=False,
                    annotate=False,
                ),
            )

        pdf_final.save(output_path, encryption=encryption, **save_kwargs)

    try:
        ensure_pdf_header(output_path, "1.4")
    except Exception:
        pass

    if os.path.exists(tmp_path):
        os.remove(tmp_path)

    final_size = get_size_mb(output_path)
    print(f"\n[DONE] Saved: {output_path}")
    print(f"       PDF Version : 1.4")
    print(f"       Producer    : KWSP")
    print(f"       File Size   : {final_size:.2f} MB")
    print(f"       Locked      : {'Yes' if user_password else 'No'}")


def compress_folder_ilovepdf(input_dir: str, output_dir: str) -> int:
    """Compress all PDFs in input_dir via iLovePDF API and save to output_dir."""
    try:
        from ilovepdf import CompressTask
    except ImportError:
        print("[ERROR] ilovepdf package not installed. Run: pip install ilovepdf", file=sys.stderr)
        return 0

    public_key = os.environ.get("ILOVEPDF_PUBLIC_KEY", "")
    secret_key = os.environ.get("ILOVEPDF_SECRET_KEY", "")

    if not public_key or not secret_key:
        print(
            "[ERROR] Missing iLovePDF API keys.\n"
            "  Add them to a .env file in this directory:\n"
            "    ILOVEPDF_PUBLIC_KEY=your_public_key\n"
            "    ILOVEPDF_SECRET_KEY=your_secret_key\n"
            "  Get your keys at: https://developer.ilovepdf.com",
            file=sys.stderr,
        )
        return 0

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
        basename = os.path.basename(pdf_path)
        print(f"[INFO] Compressing via iLovePDF: {pdf_path}  ({get_size_mb(pdf_path):.2f} MB)")
        try:
            task = CompressTask(public_key=public_key, secret_key=secret_key)
            task.add_file(pdf_path)
            task.execute()
            task.download(output_dir)

            stem = os.path.splitext(basename)[0]
            downloaded = glob.glob(os.path.join(output_dir, f"{stem}_compress*.pdf"))
            if not downloaded:
                downloaded = glob.glob(os.path.join(output_dir, f"{stem}*.pdf"))

            if downloaded:
                out_path = downloaded[0]
                print(f"[DONE] Compressed: {out_path}  ({get_size_mb(out_path):.2f} MB)")
            else:
                print(f"[WARNING] Could not locate downloaded file for {basename}")

            count += 1
            try:
                task.delete_current_task()
            except Exception:
                pass
        except Exception as e:
            print(f"[ERROR] Failed to compress {pdf_path}: {e}", file=sys.stderr)

    return count
