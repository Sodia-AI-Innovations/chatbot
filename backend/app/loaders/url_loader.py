import ipaddress
import socket
from urllib.parse import urlparse

import httpx
import trafilatura
import re

from app.core.errors import UrlContentError
from app.loaders.base import PageContent
from app.loaders.product_loader import load_products

HEADERS = {"User-Agent": "Mozilla/5.0 RAGBot"}


def _check_public(url: str) -> None:
    host = urlparse(url).hostname
    if not host:
        raise UrlContentError()
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
    except OSError as e:
        raise UrlContentError() from e
    if ip.is_private or ip.is_loopback or ip.is_link_local:
        raise UrlContentError()


def _render_page(url: str) -> tuple[str, str]:
    """Open the page in a real browser. Returns (html, visible_text)."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)                    # let late content appear
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)                    # lazy-loaded items
            html = page.content()
            visible = page.inner_text("body")
            browser.close()
        return html, visible
    except Exception as e:
        raise UrlContentError() from e

def _render(url: str)-> str:
    return _render_page(url)[0]    

def _text(html: str) -> str | None:
    return trafilatura.extract(html, include_comments=False, include_tables=True)

def _visible_text(html: str) -> str:
    """Everything a visitor sees: keeps short items like product names and prices."""
    html = re.sub(r"<(script|style|noscript|svg)[\s\S]*?</\1>", " ", html, flags=re.I)
    html = re.sub(r"</(div|p|li|h[1-6]|tr|section|article|a|button)>|<br\s*/?>", "\n", html, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.split("\n")]
    out, last = [], ""
    for ln in lines:
        if ln and ln != last:
            out.append(ln)
        last = ln
    return "\n".join(out)
    


def load_url(url: str) -> list[PageContent]:
    _check_public(url)

    products = load_products(url)
    if products:
        return products

    try:
        resp = httpx.get(url, timeout=20, follow_redirects=True, headers=HEADERS)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise UrlContentError() from e

    text = _text(resp.text)
    if not text or not text.strip():
        html, visible = _render_page(url)
        article = _text(html) or ""
        text = visible if len(visible) > 2 * len(article) else article      
                  
    if not text or not text.strip():
        raise UrlContentError()
    return [PageContent(page_number=None, text=text)]