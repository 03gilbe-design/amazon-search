# -*- coding: utf-8 -*-
"""Regression tests for pure-logic core (no API, no network, no images).

Run: python -m unittest discover tests
"""
import html
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from amazon_search.dedup import (numeric_fingerprint, spec_families, price_spread,
                                 pseudo_brand_score, rebrand_confidence)
from amazon_search.video_review import coverage, _vtt_to_text
from amazon_search.enrich import text_ok


class TestNumericFingerprint(unittest.TestCase):
    def test_rebrand_same_mold_matches(self):
        a = numeric_fingerprint("BRANDX Collare 9.5x14cm Memory Foam 250g")
        b = numeric_fingerprint("OTHER Supporto 9,5 x 14 cm, 250 g")
        self.assertGreaterEqual(len(a & b), 2)

    def test_no_numbers_empty(self):
        self.assertEqual(numeric_fingerprint("Collare cervicale regolabile"), frozenset())
        self.assertEqual(numeric_fingerprint(""), frozenset())
        self.assertEqual(numeric_fingerprint(None), frozenset())

    def test_unit_word_boundary(self):
        # "10 giorni" NON è "10g", "150 minuti" NON è "150m"
        self.assertEqual(numeric_fingerprint("garanzia 10 giorni"), frozenset())
        self.assertEqual(numeric_fingerprint("batteria dura 150 minuti"), frozenset())
        # ma l'unità vera a fine parola resta
        self.assertIn("250g", numeric_fingerprint("peso 250g netto"))

    def test_ohm_symbol_normalized(self):
        self.assertEqual(numeric_fingerprint("altoparlante 4Ω"),
                         numeric_fingerprint("altoparlante 4 ohm"))

    def test_comma_dot_equivalent(self):
        self.assertEqual(numeric_fingerprint("20,3 cm"), numeric_fingerprint("20.3cm"))


class TestSpecFamilies(unittest.TestCase):
    TITLES = {
        "A": "BRANDX Subwoofer Slim 20.3x7.6x33 cm 150W attivo",
        "B": "NoName Sub sottile 20,3 x 7,6 x 33cm 150 W bass",
        "C": "JBL BassPro SL2 125W compatto",
        "D": "Collare cervicale taglia unica",
    }

    def test_groups_rebrands_only(self):
        fams = spec_families(self.TITLES)
        self.assertEqual(len(fams), 1)
        self.assertEqual(set(fams[0]["items"]), {"A", "B"})

    def test_singleton_pool(self):
        self.assertEqual(spec_families({"A": self.TITLES["A"]}), [])
        self.assertEqual(spec_families({}), [])

    def test_price_spread(self):
        self.assertAlmostEqual(price_spread(["A", "B"], {"A": 12.99, "B": 24.99}), 12.0)
        self.assertIsNone(price_spread(["A", "B"], {"A": 12.99}))
        self.assertIsNone(price_spread(["A"], {"A": 5.0}))


class TestCrossCategory(unittest.TestCase):
    """Le idee devono reggere su categorie DIVERSE, non solo quella su cui sono nate."""

    CATEGORIES = {
        "subwoofer": ({"A": "BRANDX Subwoofer Slim 20.3x7.6x33 cm 150W",
                       "B": "NoName Sub 20,3x7,6x33cm 150 W"}, {"A", "B"}),
        "collare": ({"A": "XKJIYU Collare Cervicale 9.5x14cm 250g",
                     "B": "Supporto collo memory 9,5 x 14 cm 250 g"}, {"A", "B"}),
        "sleep_mask": ({"A": "Mascherina 3D 22x9.5cm 30g seta",
                        "B": "BZDQM Sleep Mask 22 x 9,5 cm, 30 g"}, {"A", "B"}),
        "smart_ring": ({"A": "Anello smart 2.5g titanio 20mm",
                        "B": "Ring fitness 20 mm 2,5 g nero"}, {"A", "B"}),
    }

    def test_fingerprint_matches_in_every_category(self):
        for name, (titles, expected) in self.CATEGORIES.items():
            fams = spec_families(titles)
            self.assertEqual(len(fams), 1, f"categoria {name}: {fams}")
            self.assertEqual(set(fams[0]["items"]), expected, f"categoria {name}")

    def test_no_false_positive_across_categories(self):
        # prodotti di categorie diverse nello stesso pool NON devono raggrupparsi
        pool = {f"{cat}_{k}": t for cat, (ts, _) in self.CATEGORIES.items()
                for k, t in ts.items()}
        fams = spec_families(pool)
        for f in fams:
            cats = {i.rsplit("_", 1)[0] for i in f["items"]}
            self.assertEqual(len(cats), 1, f"famiglia cross-categoria spuria: {f}")


class TestPseudoBrand(unittest.TestCase):
    def test_generated_names_flagged(self):
        for b in ("XKJIYU", "BZDZMQM", "HJKGFD"):
            self.assertGreaterEqual(pseudo_brand_score(b), 0.5, b)

    def test_real_brands_pass(self):
        for b in ("VELPEAU", "Philips", "Bose", "Eezyflow", "JBL", "Sony"):
            self.assertLess(pseudo_brand_score(b), 0.5, b)

    def test_empty_safe(self):
        self.assertEqual(pseudo_brand_score(""), 0.0)
        self.assertEqual(pseudo_brand_score(None), 0.0)

    def test_rebrand_confidence_combines(self):
        hi = rebrand_confidence(["20.3x7.6x33cm", "150w", "250g", "9.5x14cm"], ["XKJIYU"])
        lo = rebrand_confidence(["150w"], ["Bose"])
        self.assertGreaterEqual(hi, 0.7)
        self.assertLess(lo, 0.5)


class TestCoverage(unittest.TestCase):
    def _claim(self, **kw):
        base = {"product": "VELPEAU", "attribute": "comfort", "sentiment": "pos",
                "video": "v1", "channel": "ch1", "title": "recensione", "affiliate": False}
        base.update(kw)
        return base

    def test_channel_diversity(self):
        cov = coverage([self._claim(video="a", channel="c1"),
                        self._claim(video="b", channel="c2"),
                        self._claim(video="c", channel="c1")])
        v = cov["VELPEAU"]
        self.assertEqual(v["video_count"], 3)
        self.assertEqual(v["channel_count"], 2)
        self.assertFalse(v["single_source"])

    def test_single_source_flag(self):
        cov = coverage([self._claim(video="a"), self._claim(video="b")])
        self.assertTrue(cov["VELPEAU"]["single_source"])

    def test_listicle_not_dedicated(self):
        cov = coverage([self._claim(video="a", title="TOP 10 collari migliori")])
        self.assertEqual(cov["VELPEAU"]["dedicated_count"], 0)

    def test_all_affiliate(self):
        cov = coverage([self._claim(video="a", affiliate=True),
                        self._claim(video="b", affiliate=True)])
        self.assertTrue(cov["VELPEAU"]["all_affiliate"])

    def test_malformed_claims_skipped(self):
        # senza "video" o senza "product": ignorati, niente KeyError
        cov = coverage([{"product": "X"}, {"video": "v"}, {"product": "generic", "video": "v"}])
        self.assertEqual(cov, {})


class TestPhashTransforms(unittest.TestCase):
    """Foto ridimensionata/specchiata/ruotata dello stesso prodotto = stessa famiglia."""

    def test_transformed_copies_grouped(self):
        try:
            from PIL import Image, ImageOps
            import imagehash  # noqa: F401
        except ImportError:
            self.skipTest("PIL/imagehash non installati")
        from amazon_search.dedup import phash_families
        import tempfile, os
        # immagine sintetica asimmetrica (le rotazioni devono cambiare l'hash naive)
        im = Image.new("RGB", (200, 160), "white")
        for i in range(0, 120, 12):
            im.paste((200 - i, 30 + i, 60), (10 + i, 8 + i // 2, 60 + i, 50 + i // 2))
        tdir = tempfile.mkdtemp()
        inset = ImageOps.expand(im.resize((100, 80)), border=70, fill="white")
        corner = Image.new("RGB", (400, 320), "white"); corner.paste(im.resize((100, 80)), (15, 20))
        cases = {"orig": im, "small": im.resize((100, 80)), "mirror": ImageOps.mirror(im),
                 "rot90": im.rotate(90, expand=True), "rot180": im.rotate(180),
                 "inset": inset, "corner": corner,
                 "other": Image.new("RGB", (200, 160), (10, 10, 10))}
        paths = {}
        for name, img in cases.items():
            fp = os.path.join(tdir, f"{name}.png")
            img.save(fp)
            paths[name] = fp
        fams = phash_families(paths, threshold=8)
        self.assertEqual(len(fams), 1, fams)
        self.assertEqual(set(fams[0]["items"]),
                         {"orig", "small", "mirror", "rot90", "rot180", "inset", "corner"}, fams)


class TestVttToText(unittest.TestCase):
    def test_strip_and_dedup(self):
        import tempfile, os
        vtt = ("WEBVTT\nKind: captions\n\n00:01.000 --> 00:02.000\n"
               "<c>hello</c> world\n\n00:02.000 --> 00:03.000\nhello world\n[Music]\n")
        fp = tempfile.NamedTemporaryFile("w", suffix=".vtt", delete=False, encoding="utf-8")
        fp.write(vtt); fp.close()
        try:
            self.assertEqual(_vtt_to_text(fp.name), "hello world")
        finally:
            os.unlink(fp.name)


class TestTextOk(unittest.TestCase):
    def test_real_text_passes(self):
        self.assertTrue(text_ok("parola " * 100))

    def test_short_fails(self):
        self.assertFalse(text_ok("ok"))
        self.assertFalse(text_ok(""))
        self.assertFalse(text_ok(None))

    def test_binary_garbage_fails(self):
        self.assertFalse(text_ok("%PDF-1.4" + "\x00\x01\x02\x03" * 300))


class TestHtmlEscaping(unittest.TestCase):
    def test_escape_covers_script(self):
        # html_gen usa html.escape ovunque sui campi utente (verificato a grep);
        # qui blindiamo il comportamento base su cui si appoggia.
        s = html.escape('<script>alert(1)</script> "x" & y')
        self.assertNotIn("<script>", s)
        self.assertNotIn('"x"', s)


if __name__ == "__main__":
    unittest.main()
