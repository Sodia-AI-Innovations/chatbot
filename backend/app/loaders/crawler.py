import re 
import time
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from app.core.errors import AppError, UrlContentError
from app.loaders.base import PageContent
from app.loaders.url_loader import HEADERS, _render, load_url

SKIP_EXT = re.compile(r"\.(jpe?g|png|gif|svg|webp|ico|css|js|pdf|zip|mp4|mp3|woff2?)$", re.I)
SKIP_PATH = re.compile(r"/(cart|checkout|login|signin|sign-in|register|account|admin|wp-admin|search)\b", re.I)

def _get(url: str)-> str:
    try:
        r = httpx.get(url, timeout=20, headers=HEADERS, follow_redirects=True)
        return r.text if r.status_code == 200 else ""
    except httpx.HTTPError:
        return ""

def _host(url: str) -> str:
    h = (urlparse(url).hostname or ""). lower()
    return h[4:] if h.startswith("www.") else h
def _ok(url: str, host: str) -> bool:
    p = urlparse(url)
    return (p.scheme in ("http", "https") and _host(url) == host 
            and not SKIP_EXT.search(p.path) and not SKIP_PATH.search(p.path))

def _sitemap_urls(base: str) -> list[str]:
    robots = _get(base + "/robots.txt")
    maps = re.findall(r"(?im)^sitemap:\s*(\S+)", robots) or [base + "/stemap.xml"]
    urls: list[str] = []
    for sm in maps[:3]:
        for loc in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", _get(sm)):
            if loc.endswith(".xml"):
                urls += re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", _get(loc))
            else:
                urls.append(loc)
    return urls

def _links(html: str, page_url:str, host: str) -> list[str]:
    found = []
    for href in re.findall(r'href=["\']([^"\']+)["\']', html, re.I):
        u = urldefrag(urljoin(page_url, href))[0]
        if _ok(u, host):
            found.append(u)
    return found

def load_site(start_url: str, max_pages: int = 15) -> list[PageContent]:
    parts = urlparse(start_url)
    base = f"{parts.scheme}://{parts.netloc}"
    host = _host(start_url)

    queue = [start_url] + [u for u in _sitemap_urls(base) if _ok(u, host)]
    if len(queue) == 1:
        links = _links(_get(start_url), start_url, host)
        if not links:
            links = _links(_render(start_url), start_url, host)
        queue += links

    pages: list[PageContent] = []
    seen_urls: set[str] = set()
    seen_text: set[str] = set()
    for url in queue: 
        if len(pages) >= max_pages:
            break
        if url in seen_urls:
            continue
        seen_urls.add(url)
        try:
            got = load_url(url)
        except AppError:
            continue
        for pc in got:
            if pc.text in seen_text:
                continue
            seen_text.add(pc.text)
            pages.append(PageContent(page_number=None, text=f"Page: {url}\n{pc.text}"))
        time.sleep(0.5)
    if not pages:
        raise UrlContentError()
    return pages                