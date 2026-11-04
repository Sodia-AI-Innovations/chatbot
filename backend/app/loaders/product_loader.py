import json
import re
from urllib.parse import urlparse

import httpx

from app.loaders.base import PageContent

HEADERS = {"User-Agent": "Mozilla/5.0 RAGBot"}

def _strip_html(s: str)-> str:
    return re.sub(r"\s+", "", re.sub(r"<[^>]+>", " ", s or "")).strip()

def _shopify_products(base: str) -> list[PageContent]:
    out: list[PageContent] = []
    for page in range(1, 11):
        try:
            r= httpx.get(f"{base}/products.json?limit=250&page={page}", timeout=20, headers=HEADERS, follow_redirects=True)
            items = r.json().get("products", []) if r.status_code == 200 else []
        except (httpx.HTTPError, ValueError):
            break
        if not items:
            break
        for p in items:
            variants = p.get("variants", [])
            prices = [float(v["price"]) for v in variants if v.get("price")]
            price = ""
            if prices:
                lo, hi = min(prices), max(prices)
                price = f"{lo:g}" if lo == hi else f"{lo:g} - {hi:g}"
            in_stock = any(v.get("available") for v in variants)
            out.append(PageContent(page_number=None, text="\n".join([
                f"Product: {p.get('title', '')}",
                f"Brand: {p.get('vendor', '')}",
                f"Category: {p.get('product_type', '')}",
                f"Price: {price}",
                f"In stock: {'yes' if in_stock else 'no'}",
                f"Tags: {', '.join(p.get('tags', [])) if isinstance(p.get('tags'), list) else p.get('tags', '')}",
                f"Description: {_strip_html(p.get('body_html', ''))}",
                f"Link: {base}/products/{p.get('handle', '')}",
            ])))
    return out


def _is_product(node) -> bool:
        t = node.get("@type") if isinstance(node, dict) else None
        return t == "Product" or (isinstance(t, list) and "Product" in t)

def _jsonld_products(html: str, url: str) -> list[PageContent]:
        out: list[PageContent] = []
        pattern = r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>'
        for m in re.finditer(pattern, html, re.S | re.I):
            try:
                data = json.loads(m.group(1))
            except ValueError:
                continue
            nodes = data if isinstance(data, list) else data.get("@graph", [data])
            for n in nodes:
                if not _is_product(n):
                    continue
                offer = n.get("offers") or {}
                if isinstance(offer, list):
                    offer = offer[0] if offer else {}
                rating = n.get("aggregateRating") or {}
                lines = [
                    f"Product: {n.get('name', '')}",
                f"Price: {offer.get('price', '')} {offer.get('priceCurrency', '')}".strip(),
                f"Availability: {str(offer.get('availability', '')).rsplit('/', 1)[-1]}",
                f"Rating: {rating.get('ratingValue', '')} from {rating.get('reviewCount', '')} reviews",
                f"Description: {_strip_html(n.get('description', ''))}",
                f"Link: {n.get('url') or url}",
                ]
                reviews = n.get("review") or []
                if isinstance(reviews, dict):
                    reviews = [reviews]
                for rv in reviews[:5]:
                    score = (rv.get("reviewRating") or {}).get("ratingValue", "")
                    lines.append(f"Review ({score}/5): {_strip_html(rv.get('reviewBody', ''))}")
                out.append(PageContent(page_number=None, text="\n".join(lines)))
        return out

def load_products(url: str) -> list[PageContent]:
        """Return one PageContent per product, or [] if the site has no product data."""
        parts = urlparse(url)
        base = f"{parts.scheme}://{parts.netloc}"
        found = _shopify_products(base)
        if found:
            return found
        try:
            html = httpx.get(url, timeout=20, headers=HEADERS, follow_redirects=True).text
        except httpx.HTTPError:
            return []
        return _jsonld_products(html, url)
                           
