# tools/utils.py
import hashlib

def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_vrom(answer: str) -> str:
    for size in ["XS", "S", "M", "L", "XL", "XXL"]:
        if "T-shirt size" in answer and size in answer:
            return size
    n_words = len(answer.split())
    if n_words < 30:
        return "XS"
    if n_words < 80:
        return "S"
    if n_words < 150:
        return "M"
    if n_words < 250:
        return "L"
    if n_words < 350:
        return "XL"
    return "XXL"
