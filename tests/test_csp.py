import importlib.util
import pathlib
import sys
import types
import unittest

from bs4 import BeautifulSoup


ROOT = pathlib.Path(__file__).resolve().parents[1]

savedModules = {
    name: sys.modules.get(name)
    for name in ("modules", "modules.userscript", "modules.csp")
}
userscriptModule = types.ModuleType("modules.userscript")
userscriptModule.Userscript = object
modulesPackage = types.ModuleType("modules")
modulesPackage.__path__ = []
sys.modules["modules"] = modulesPackage
sys.modules["modules.userscript"] = userscriptModule

spec = importlib.util.spec_from_file_location(
    "modules.csp",
    ROOT / "src" / "modules" / "csp.py",
)
assert spec is not None and spec.loader is not None
csp = importlib.util.module_from_spec(spec)
sys.modules["modules.csp"] = csp
spec.loader.exec_module(csp)

for name, previous in savedModules.items():
    if previous is None:
        sys.modules.pop(name, None)
    else:
        sys.modules[name] = previous


class FakeUserscript:
    def __init__(self, downloadURL=None):
        self.downloadURL = downloadURL


def inlineInjection(nonce="proxy-nonce"):
    return csp.Injection(FakeUserscript(), nonce)


def linkedInjection(url="https://scripts.example/userscript.js"):
    return csp.Injection(FakeUserscript(url), None)


class FakeHeaders:
    def __init__(self, fields):
        self.fields = list(fields)

    def __contains__(self, key):
        lowered = key.lower()
        return any(name.lower() == lowered for name, _ in self.fields)

    def __delitem__(self, key):
        lowered = key.lower()
        self.fields = [
            (name, value)
            for name, value in self.fields
            if name.lower() != lowered
        ]
    def get_all(self, key):
        lowered = key.lower()
        return [
            value
            for name, value in self.fields
            if name.lower() == lowered
        ]

    def set_all(self, key, values):
        values = list(values)
        lowered = key.lower()
        rewritten = []
        for name, value in self.fields:
            if name.lower() == lowered:
                if values:
                    rewritten.append((name, values.pop(0)))
            else:
                rewritten.append((name, value))
        rewritten.extend((key, value) for value in values)
        self.fields = rewritten


class CspTests(unittest.TestCase):
    def test_parser_preserves_order_duplicates_and_valueless_directives(self):
        original = (
            "default-src 'self'; upgrade-insecure-requests; "
            "script-src 'nonce-a'; script-src 'nonce-b'; report-to csp"
        )
        parsed = csp.parsePolicy(original)
        self.assertEqual(
            [(directive.name, directive.values) for directive in parsed],
            [
                ("default-src", ["'self'"]),
                ("upgrade-insecure-requests", []),
                ("script-src", ["'nonce-a'"]),
                ("script-src", ["'nonce-b'"]),
                ("report-to", ["csp"]),
            ],
        )
        self.assertEqual(csp.serializePolicy(parsed), original)

    def test_script_src_elem_is_the_effective_script_element_directive(self):
        policy = "default-src 'none'; script-src 'self'; script-src-elem https:"
        self.assertEqual(csp.effectiveScriptSources(policy), ["https:"])

    def test_matching_native_nonce_allows_inline_script(self):
        policy = "script-src 'nonce-native' 'strict-dynamic' https:"
        self.assertTrue(csp.policyAllowsInlineScript(policy, "native"))
        self.assertFalse(csp.policyAllowsInlineScript(policy, "other"))

    def test_unsafe_inline_without_nonce_or_hash_needs_no_rewrite(self):
        policy = "script-src 'self' 'unsafe-inline'"
        self.assertTrue(csp.policyAllowsInlineScript(policy, None))
        self.assertEqual(
            csp.headerWithScriptsAllowed(policy, [inlineInjection()]),
            policy,
        )

    def test_inline_script_still_gets_nonce_when_policy_needs_no_rewrite(self):
        policy = "script-src 'self' 'unsafe-inline'"
        originalGenerator = csp.generateNonce
        csp.generateNonce = lambda: "generated"
        try:
            nonce = csp.chooseInlineNonce([policy], [])
        finally:
            csp.generateNonce = originalGenerator
        self.assertEqual(nonce, "generated")
        self.assertEqual(
            csp.headerWithScriptsAllowed(policy, [inlineInjection(nonce)]),
            policy,
        )
    def test_youtube_style_multiple_policies_reuse_native_nonce_without_rewrite(self):
        policies = [
            (
                "script-src 'unsafe-eval' 'self' 'unsafe-inline' "
                "https://www.google.com https://www.youtube.com"
            ),
            (
                "base-uri 'self'; object-src 'none'; "
                "script-src 'nonce-native' 'unsafe-inline' 'strict-dynamic' "
                "https: http: 'unsafe-eval'"
            ),
            "require-trusted-types-for 'script'",
        ]
        self.assertEqual(
            csp.reusableNonce(policies, ["native", "irrelevant"]),
            "native",
        )
        for policy in policies:
            self.assertEqual(
                csp.headerWithScriptsAllowed(
                    policy,
                    [inlineInjection("native")],
                ),
                policy,
            )

    def test_generated_nonce_rewrites_only_policy_that_blocks_it(self):
        permissive = "script-src 'self' 'unsafe-inline'"
        restrictive = "script-src 'self'"
        rewritten = csp.headerValuesWithScriptsAllowed(
            [permissive, restrictive],
            [inlineInjection()],
        )
        self.assertEqual(rewritten[0], permissive)
        self.assertEqual(
            rewritten[1],
            "script-src 'self' 'nonce-proxy-nonce'",
        )
    def test_strict_dynamic_without_existing_trust_is_not_activated(self):
        policy = "script-src 'strict-dynamic' https: 'self'"
        self.assertFalse(csp.policyCanSafelyAddNonce(policy))
        self.assertEqual(
            csp.headerWithScriptsAllowed(policy, [inlineInjection()]),
            policy,
        )

    def test_strict_dynamic_with_existing_hash_can_accept_extra_nonce(self):
        policy = "script-src 'strict-dynamic' 'sha256-abc' https:"
        self.assertTrue(csp.policyCanSafelyAddNonce(policy))
        self.assertEqual(
            csp.headerWithScriptsAllowed(policy, [inlineInjection()]),
            (
                "script-src 'strict-dynamic' 'sha256-abc' https: "
                "'nonce-proxy-nonce'"
            ),
        )

    def test_script_src_is_synthesized_from_default_src(self):
        rewritten = csp.headerWithScriptsAllowed(
            "default-src 'self'; img-src data:",
            [inlineInjection()],
        )
        self.assertEqual(
            rewritten,
            "default-src 'self'; img-src data:; "
            "script-src 'self' 'nonce-proxy-nonce'",
        )
    def test_linked_script_modifies_only_effective_script_src_elem(self):
        rewritten = csp.headerWithScriptsAllowed(
            "script-src 'self'; script-src-elem 'self'",
            [linkedInjection()],
        )
        self.assertEqual(
            rewritten,
            (
                "script-src 'self'; "
                "script-src-elem 'self' https://scripts.example/userscript.js"
            ),
        )

    def test_multiple_csp_headers_are_rewritten_independently(self):
        headers = FakeHeaders([
            ("Content-Security-Policy", "script-src 'self' 'unsafe-inline'"),
            ("X-Test", "kept"),
            ("Content-Security-Policy", "script-src 'self'"),
            (
                "Content-Security-Policy-Report-Only",
                "script-src 'nonce-report'",
            ),
        ])
        csp.rewriteCspHeaders(headers, "script", [inlineInjection()])
        enforcing = headers.get_all("Content-Security-Policy")
        self.assertEqual(
            enforcing,
            [
                "script-src 'self' 'unsafe-inline'",
                "script-src 'self' 'nonce-proxy-nonce'",
            ],
        )
        self.assertEqual(
            headers.get_all("Content-Security-Policy-Report-Only"),
            ["script-src 'nonce-report'"],
        )
        self.assertIn(("X-Test", "kept"), headers.fields)
    def test_meta_csp_participates_in_nonce_selection_and_rewrite(self):
        soup = BeautifulSoup(
            (
                "<html><head>"
                "<meta http-equiv='Content-Security-Policy' "
                "content=\"script-src 'nonce-native' 'strict-dynamic'\">"
                "<script nonce='native'>window.nativeRan = true</script>"
                "</head><body></body></html>"
            ),
            "html.parser",
        )
        policies = csp.metaPolicyValues(soup)
        self.assertEqual(
            csp.reusableNonce(policies, csp.nonceCandidates(soup)),
            "native",
        )
        csp.rewriteMetaPolicies(soup, "script", [inlineInjection("native")])
        self.assertEqual(csp.metaPolicyValues(soup), policies)

    def test_meta_csp_is_safely_extended_when_needed(self):
        soup = BeautifulSoup(
            (
                "<html><head>"
                "<meta http-equiv='content-security-policy' "
                "content=\"script-src 'self'\">"
                "</head><body></body></html>"
            ),
            "html.parser",
        )
        csp.rewriteMetaPolicies(soup, "script", [inlineInjection()])
        self.assertEqual(
            csp.metaPolicyValues(soup),
            ["script-src 'self' 'nonce-proxy-nonce'"],
        )

    def test_meta_csp_outside_head_is_ignored(self):
        soup = BeautifulSoup(
            (
                "<html><head></head><body>"
                "<meta http-equiv='Content-Security-Policy' "
                "content=\"script-src 'none'\">"
                "</body></html>"
            ),
            "html.parser",
        )
        self.assertEqual(csp.metaPolicyValues(soup), [])
    def test_everything_mode_removes_enforcing_header_and_meta_only_when_injecting(self):
        headers = FakeHeaders([
            ("Content-Security-Policy", "default-src 'self'"),
            ("Content-Security-Policy-Report-Only", "default-src 'self'"),
        ])
        soup = BeautifulSoup(
            (
                "<html><head><meta http-equiv='Content-Security-Policy' "
                "content=\"default-src 'self'\"></head><body></body></html>"
            ),
            "html.parser",
        )

        csp.rewriteCspHeaders(headers, "everything", [])
        csp.rewriteMetaPolicies(soup, "everything", [])
        self.assertTrue(headers.get_all("Content-Security-Policy"))
        self.assertTrue(csp.metaPolicyValues(soup))

        csp.rewriteCspHeaders(headers, "everything", [inlineInjection()])
        csp.rewriteMetaPolicies(soup, "everything", [inlineInjection()])
        self.assertFalse(headers.get_all("Content-Security-Policy"))
        self.assertTrue(headers.get_all("Content-Security-Policy-Report-Only"))
        self.assertEqual(csp.metaPolicyValues(soup), [])

    def test_nonce_candidates_are_unique_and_nonempty(self):
        soup = BeautifulSoup(
            (
                "<script nonce='alpha'></script>"
                "<script nonce='alpha'></script>"
                "<script nonce=''></script>"
                "<script nonce='beta'></script>"
            ),
            "html.parser",
        )
        self.assertEqual(csp.nonceCandidates(soup), ["alpha", "beta"])


if __name__ == "__main__":
    unittest.main()
