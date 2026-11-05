"""Bounded, read-only live offers from public retailer product pages."""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Callable
from urllib.parse import urljoin, urlparse


RETAILER_HOST = "www.isoladeitesori.it"
RETAILER_NAME = "L'Isola dei Tesori"
SEARCH_URL = f"https://{RETAILER_HOST}/search/"
MAX_PRODUCT_PAGES = 2
MAX_RESPONSE_BYTES = 1_000_000
REQUEST_TIMEOUT_SECONDS = 3
LOOKUP_BUDGET_SECONDS = 11


@dataclass(frozen=True)
class CommerceOffer:
    retailer: str
    product_name: str
    brand: str
    product_url: str
    price_amount: str
    currency: str
    availability: str
    availability_scope: str
    fetched_at: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


FetchPage = Callable[[str], tuple[str, bytes]]


class _AllowlistedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        if not _allowed_retailer_url(new_url):
            raise ValueError("Retailer redirected outside the allowlist")
        return super().redirect_request(request, response, code, message, headers, new_url)


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.product_links: list[str] = []
        self.jsonld: list[str] = []
        self.canonical: str | None = None
        self._in_jsonld = False
        self._script_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "a" and values.get("href"):
            self.product_links.append(values["href"] or "")
        if tag == "link" and "canonical" in (values.get("rel") or "").lower().split():
            self.canonical = values.get("href")
        if tag == "script" and "ld+json" in (values.get("type") or "").lower():
            self._in_jsonld = True
            self._script_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_jsonld:
            self._script_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._in_jsonld:
            self.jsonld.append("".join(self._script_parts))
            self._in_jsonld = False
            self._script_parts = []


def _allowed_retailer_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return (
            parsed.scheme == "https"
            and parsed.hostname == RETAILER_HOST
            and parsed.port in (None, 443)
            and parsed.username is None
            and parsed.password is None
        )
    except ValueError:
        return False


def _fetch_page(url: str, deadline: float) -> tuple[str, bytes]:
    if not _allowed_retailer_url(url):
        raise ValueError("Retailer URL is not allowlisted")
    request = urllib.request.Request(url, headers={"User-Agent": "PetMatch public offer lookup/1.0", "Accept": "text/html"})
    opener = urllib.request.build_opener(_AllowlistedRedirect())
    timeout = min(REQUEST_TIMEOUT_SECONDS, deadline - time.monotonic())
    if timeout <= 0:
        raise TimeoutError("Commerce lookup exceeded its time budget")
    with opener.open(request, timeout=timeout) as response:
        final_url = response.geturl()
        if not _allowed_retailer_url(final_url):
            raise ValueError("Retailer redirected outside the allowlist")
        chunks = []
        total_bytes = 0
        while chunk := response.read(min(16_384, MAX_RESPONSE_BYTES + 1 - total_bytes)):
            if time.monotonic() >= deadline:
                raise TimeoutError("Commerce lookup exceeded its time budget")
            chunks.append(chunk)
            total_bytes += len(chunk)
            if total_bytes > MAX_RESPONSE_BYTES:
                raise ValueError("Retailer page exceeds the response size limit")
        body = b"".join(chunks)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ValueError("Retailer page exceeds the response size limit")
    return final_url, body


def _product_urls(search_url: str, body: bytes) -> list[str]:
    parser = _PageParser()
    parser.feed(body.decode("utf-8", errors="strict"))
    urls = []
    for href in parser.product_links:
        candidate = urljoin(search_url, href)
        parsed = urlparse(candidate)
        if (
            _allowed_retailer_url(candidate)
            and parsed.path.startswith("/prodotto/")
            and parsed.path.lower().endswith(".html")
            and candidate not in urls
        ):
            urls.append(candidate)
        if len(urls) >= MAX_PRODUCT_PAGES:
            break
    return urls


def _walk_json(value: object):
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _walk_json(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_json(nested)


def _product_offer(final_url: str, body: bytes, fetched_at: str) -> CommerceOffer | None:
    parser = _PageParser()
    parser.feed(body.decode("utf-8", errors="strict"))
    product_url = urljoin(final_url, parser.canonical) if parser.canonical else final_url
    if not _allowed_retailer_url(product_url):
        raise ValueError("Canonical product URL is outside the allowlist")
    products = []
    for raw in parser.jsonld:
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, RecursionError) as error:
            raise ValueError("Malformed public structured data") from error
        products.extend(node for node in _walk_json(data) if node.get("@type") == "Product")
    if len(products) != 1:
        return None
    product = products[0]
    raw_offers = product.get("offers")
    offers = raw_offers if isinstance(raw_offers, list) else [raw_offers]
    if len(offers) != 1 or not isinstance(offers[0], dict):
        return None
    offer = offers[0]
    if str(offer.get("priceCurrency", "")).upper() != "EUR":
        return None
    price = str(offer.get("price", ""))
    if not re.fullmatch(r"\d+(?:\.\d{1,2})?", price):
        return None
    availability = str(offer.get("availability", "")).rstrip("/").rsplit("/", 1)[-1]
    if availability not in {"InStock", "OutOfStock"}:
        return None
    brand = product.get("brand", "")
    if isinstance(brand, dict):
        brand = brand.get("name", "")
    name = product.get("name")
    if not isinstance(name, str) or not name.strip():
        return None
    return CommerceOffer(
        retailer=RETAILER_NAME,
        product_name=name.strip()[:240],
        brand=str(brand or "")[:100],
        product_url=product_url,
        price_amount=price,
        currency="EUR",
        availability="available" if availability == "InStock" else "unavailable",
        # This retailer offer is the online product page's stock statement;
        # store pickup stock is never inferred from it.
        availability_scope="online",
        fetched_at=fetched_at,
    )


def normalize_product_query(query: str) -> str:
    """Remove common commerce phrasing while preserving brand/product terms."""
    clean = " ".join(query.split())[:120]
    clean = re.sub(
        r"\b(?:quanto\s+(?:costa|viene)|qual(?:e|['’]è)\s+il\s+prezzo(?:\s+di)?|dove\s+(?:posso\s+)?comprare|where\s+(?:can\s+i\s+buy|to\s+buy)|how\s+much(?:\s+is)?|what(?:['’]s|\s+is)\s+the\s+price(?:\s+of)?|prices?\s+(?:for|of)|costs?\s+(?:for|of)|prezzi?\s+di|prezzi?|costo|costa|disponibil\w*|availability|available|in\s+stock|stock|negozi?\s+(?:di\s+animali\s+)?(?:a\s+)?|shops?|stores?|arcaplanet|zooplus|bitiba|amazon|isola(?:\s+dei\s+tesori)?)\b",
        " ",
        clean,
        flags=re.I,
    )
    return " ".join(re.sub(r"[^\w\s.'-]", " ", clean).split())[:120]


def _matches_requested_product(query: str, offer: CommerceOffer) -> bool:
    tokens = re.findall(r"[a-z0-9]+", query.casefold())
    ignored = {"a", "ad", "al", "alla", "an", "and", "at", "cane", "cani", "cat", "cats", "dog", "dogs", "for", "gatto", "gatti", "il", "in", "la", "le", "lo", "of", "per", "pet", "the", "un", "una"}
    required = [token for token in tokens if token not in ignored]
    if not required:
        return False
    product_tokens = set(re.findall(r"[a-z0-9]+", f"{offer.brand} {offer.product_name}".casefold()))
    return all(token in product_tokens for token in required)


def _is_local_store_query(query: str) -> bool:
    text = query.casefold()
    location = re.search(r"\b(?:a|in|at|near|vicino\s+a)\s+[A-ZÀ-ÖØ-Þ][\w'-]+", query)
    asks_about_stock = re.search(r"\b(?:available|availability|stock|disponibil\w*|ritiro|pickup|click\s*(?:and|&)\s*collect)\b", text)
    asks_for_store = re.search(r"\b(?:negozi?\w*|shops?|stores?|fisic\w*)\b", text)
    return bool(
        (location and (asks_about_stock or asks_for_store))
        or re.search(r"\b(?:in\s+store|in\s+negozio|local\s+store|ritiro\s+in\s+negozio|pickup\s+in\s+store)\b", text)
    )


def lookup_offers(query: str, fetch_page: FetchPage | None = None) -> list[CommerceOffer]:
    """Fetch one search page and at most three official product pages.

    Any fetch or parse error fails closed for the whole lookup. Store-level
    inventory is not exposed by this connector and is never inferred.
    """
    clean_query = normalize_product_query(query)
    if len(clean_query) < 2 or _is_local_store_query(query):
        return []
    # Do not silently substitute this retailer when the user requested another.
    explicit_retailer = bool(re.search(r"\b(arcaplanet|zooplus|bitiba|amazon)\b", clean_query, re.I))
    explicit_isola = bool(re.search(r"\b(isola(?:\s+dei\s+tesori)?|l['’]isola)\b", clean_query, re.I))
    if explicit_retailer and not explicit_isola:
        return []

    deadline = time.monotonic() + LOOKUP_BUDGET_SECONDS

    def fetch(url: str) -> tuple[str, bytes]:
        if time.monotonic() >= deadline:
            raise TimeoutError("Commerce lookup exceeded its time budget")
        return fetch_page(url) if fetch_page else _fetch_page(url, deadline)

    search_url = SEARCH_URL + "?" + urllib.parse.urlencode({"q": clean_query})
    try:
        final_search_url, search_body = fetch(search_url)
        if not _allowed_retailer_url(final_search_url):
            return []
        product_urls = _product_urls(final_search_url, search_body)[:MAX_PRODUCT_PAGES]
        if not product_urls:
            return []
        offers = []
        for product_url in product_urls:
            final_url, body = fetch(product_url)
            if not _allowed_retailer_url(final_url):
                return []
            fetched_at = datetime.now(timezone.utc).isoformat()
            offer = _product_offer(final_url, body, fetched_at)
            if offer and _matches_requested_product(clean_query, offer):
                offers.append(offer)
        return offers
    except (OSError, urllib.error.URLError, TimeoutError, ValueError, UnicodeError, RecursionError):
        return []

