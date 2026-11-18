import pathlib
import sys
import unittest

from bs4 import BeautifulSoup


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import modules.inject as inject
import modules.userscript as userscript


def inlineScript(runAt):
    return userscript.Userscript(
        name="Inline test",
        version=None,
        content="window.inlineTest = true;",
        runAt=runAt,
        noframes=False,
        matchPatterns=[],
        includePatternRegexes=[],
        excludePatternRegexes=[],
        downloadURL=None,
        unsafeSequences=[],
    )


class InjectTests(unittest.TestCase):
    def test_inline_document_start_tag_uses_selected_nonce(self):
        soup = BeautifulSoup("<html><head></head><body></body></html>", "html.parser")
        result = inject.inject(
            inlineScript(userscript.document_start),
            soup,
            inject.Options(inline=False, nonce="native"),
        )
        self.assertIs(result, soup)
        tag = soup.find("script")
        self.assertEqual(tag.get("nonce"), "native")
        self.assertIn("window.inlineTest = true;", tag.string)

    def test_inline_without_csp_nonce_keeps_nonce_absent(self):
        soup = BeautifulSoup("<html><head></head><body></body></html>", "html.parser")
        result = inject.inject(
            inlineScript(userscript.document_start),
            soup,
            inject.Options(inline=False, nonce=None),
        )
        self.assertIs(result, soup)
        tag = soup.find("script")
        self.assertIsNone(tag.get("nonce"))


if __name__ == "__main__":
    unittest.main()
