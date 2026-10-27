
from urllib.parse import urlparse
def normalize_domain(value:str) -> str:
    v = (value or "").strip().lower()
    if "//" not in v:
        v = "//" + v
    host = urlparse(v).hostname or ""
    return host[4:] if host.startswith("www.") else host   