import pathlib
import sys
import unittest

from bs4 import BeautifulSoup


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import modules.inject as inject
import modules.userscript as userscript


def linkedScript(runAt):
    return userscript.Userscript(
        name="Linked test",
        version=None,
        content="",
        runAt=runAt,
        noframes=False,
        matchPatterns=[],
        includePatternRegexes=[],
        excludePatternRegexes=[],
        downloadURL="https://scripts.example/test.js",
        unsafeSequences=[],
    )


class InjectTests(unittest.TestCase):
    def test_linked_document_idle_child_reuses_nonce(self):
        soup = BeautifulSoup("<html><head></head><body></body></html>", "html.parser")
        result = inject.inject(
            linkedScript(userscript.document_idle),
            soup,
            inject.Options(inline=False, nonce="native"),
        )
        self.assertIs(result, soup)
        tag = soup.find("script")
        self.assertEqual(tag.get("nonce"), "native")
        self.assertIn(
            's.setAttribute("nonce", "native");',
            tag.string,
        )
        self.assertIn(
            's.src = "https://scripts.example/test.js";',
            tag.string,
        )

    def test_linked_document_start_tag_reuses_nonce(self):
        soup = BeautifulSoup("<html><head></head><body></body></html>", "html.parser")
        result = inject.inject(
            linkedScript(userscript.document_start),
            soup,
            inject.Options(inline=False, nonce="native"),
        )
        self.assertIs(result, soup)
        tag = soup.find("script")
        self.assertEqual(tag.get("nonce"), "native")
        self.assertEqual(tag.get("src"), "https://scripts.example/test.js")


if __name__ == "__main__":
    unittest.main()
