import json
import unittest
from datetime import datetime
from urllib.parse import parse_qs, urlparse

from commerce import CommerceOffer, lookup_offers


def search_page(count=1):
    links = "".join(f'<a href="/prodotto/cibo-{i}/0000000{i}.html">Food {i}</a>' for i in range(count))
    return f"<html><body>{links}</body></html>".encode()


def product_page(availability="http://schema.org/InStock", name="Special Dog Adult 3 kg", brand="Special Dog"):
    product = {
        "@context": "http://schema.org/",
        "@type": "Product",
        "name": name,
        "brand": {"@type": "Thing", "name": brand},
        "offers": {"@type": "Offer", "priceCurrency": "EUR", "price": "12.49", "availability": availability},
    }
    return f'<html><head><script type="application/ld+json">{json.dumps(product)}</script></head></html>'.encode()


class CommerceConnectorTests(unittest.TestCase):
    def test_reads_only_structured_online_offer_and_timestamps_each_result(self):
        pages = {
            "/search/": search_page(),
            "/prodotto/cibo-0/00000000.html": product_page(),
        }
        requested = []

        def fetch(url):
            requested.append(url)
            return url, pages[urlparse(url).path]

        offers = lookup_offers("Special Dog adult", fetch_page=fetch)

        self.assertEqual(len(offers), 1)
        offer = offers[0]
        self.assertEqual(offer.retailer, "L'Isola dei Tesori")
        self.assertEqual(offer.brand, "Special Dog")
        self.assertEqual(offer.price_amount, "12.49")
        self.assertEqual(offer.availability, "available")
        self.assertEqual(offer.availability_scope, "online")
        self.assertEqual(datetime.fromisoformat(offer.fetched_at).utcoffset().total_seconds(), 0)
        self.assertEqual(len(requested), 2)
        self.assertEqual(parse_qs(urlparse(requested[0]).query)["q"], ["Special Dog adult"])

    def test_preserves_explicit_out_of_stock_status(self):
        pages = {"/search/": search_page(), "/prodotto/cibo-0/00000000.html": product_page("http://schema.org/OutOfStock")}
        offer = lookup_offers("Special Dog", fetch_page=lambda url: (url, pages[urlparse(url).path]))[0]
        self.assertEqual(offer.availability, "unavailable")
        self.assertEqual(offer.availability_scope, "online")

    def test_caps_product_fetches_at_three(self):
        pages = {"/search/": search_page(count=9)}
        requested = []

        def fetch(url):
            requested.append(url)
            if urlparse(url).path == "/search/":
                return url, pages["/search/"]
            return url, product_page()

        offers = lookup_offers("food", fetch_page=fetch)
        self.assertLessEqual(len(offers), 2)
        self.assertEqual(len(requested), 3)

    def test_fails_closed_if_a_product_fetch_fails(self):
        calls = 0

        def fetch(url):
            nonlocal calls
            calls += 1
            if calls == 1:
                return url, search_page(count=2)
            if calls == 2:
                return url, product_page()
            raise TimeoutError("retailer unavailable")

        self.assertEqual(lookup_offers("food", fetch_page=fetch), [])

    def test_rejects_redirects_or_product_links_outside_allowlist(self):
        self.assertEqual(lookup_offers("food", fetch_page=lambda url: ("https://attacker.example/", search_page())), [])
        page = b'<a href="https://attacker.example/prodotto/fake.html">fake</a>'
        self.assertEqual(lookup_offers("food", fetch_page=lambda url: (url, page)), [])

    def test_does_not_substitute_isola_when_user_requested_another_shop(self):
        calls = []
        self.assertEqual(lookup_offers("Royal Canin price at Arcaplanet", fetch_page=lambda url: calls.append(url)), [])
        self.assertEqual(calls, [])

    def test_normalizes_italian_price_question_and_filters_unrelated_results(self):
        requested_searches = []

        def fetch(url):
            path = urlparse(url).path
            if path == "/search/":
                requested_searches.append(parse_qs(urlparse(url).query)["q"][0])
                return url, search_page(count=2)
            if "00000000" in path:
                return url, product_page(name="Royal Canin Mini Adult 2 kg", brand="Royal Canin")
            return url, product_page(name="Royal Canin Gastrointestinal 2 kg", brand="Royal Canin")

        offers = lookup_offers("Quanto costa Royal Canin Mini Adult 2 kg?", fetch_page=fetch)
        self.assertEqual(requested_searches, ["Royal Canin Mini Adult 2 kg"])
        self.assertEqual([offer.product_name for offer in offers], ["Royal Canin Mini Adult 2 kg"])

    def test_abstains_for_local_shop_stock_questions_without_fetching(self):
        calls = []
        self.assertEqual(lookup_offers("Quale negozio a Torino vende Royal Canin?", fetch_page=lambda url: calls.append(url)), [])
        self.assertEqual(lookup_offers("Is Royal Canin available in Turin?", fetch_page=lambda url: calls.append(url)), [])
        self.assertEqual(calls, [])

    def test_offer_contract_has_separate_store_scope(self):
        offer = CommerceOffer("Shop", "Food", "Brand", "https://www.isoladeitesori.it/p", "9.99", "EUR", "available", "online", "2026-11-05T00:00:00+00:00")
        self.assertEqual(offer.as_dict()["availability_scope"], "online")


if __name__ == "__main__":
    unittest.main()
