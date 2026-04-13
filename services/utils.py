import os
import json

PRODUCER_CACHE_FILE = ".producer_cache.json"


def get_size_mb(path: str) -> float:
    return os.path.getsize(path) / (1024 * 1024)


def ensure_pdf_header(path: str, version: str = "1.4") -> None:
    """Binary-patch the PDF header to report the given version."""
    if not os.path.isfile(path):
        return
    with open(path, "r+b") as f:
        head = f.read(1024)
        idx = head.find(b"%PDF-1.")
        if idx != -1:
            old_header = head[idx:idx + 8]
            new_token = b"%PDF-" + version.encode("ascii")
            if len(new_token) < len(old_header):
                new_token = new_token + b" " * (len(old_header) - len(new_token))
            new_head = head.replace(old_header, new_token, 1)
            f.seek(0)
            f.write(new_head[:1024])


def load_metadata_cache() -> dict:
    """Load the metadata cache.

    Returns a dict mapping file stem → entry dict with keys:
      ``producer``  – str (may be empty)
      ``docinfo``   – dict of extra PDF Info dict fields (keys include leading slash)

    Handles the old format where values were plain producer strings.
    """
    if os.path.isfile(PRODUCER_CACHE_FILE):
        with open(PRODUCER_CACHE_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        migrated = {}
        for stem, value in raw.items():
            if isinstance(value, str):
                migrated[stem] = {"producer": value, "docinfo": {}}
            else:
                migrated[stem] = value
        return migrated
    return {}


def load_producer_cache() -> dict:
    """Backward-compat alias — returns the metadata cache."""
    return load_metadata_cache()


def save_producer_cache(cache: dict) -> None:
    with open(PRODUCER_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
