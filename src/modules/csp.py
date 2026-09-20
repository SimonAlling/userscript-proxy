import secrets
from dataclasses import dataclass
from typing import Any, NamedTuple, Optional, Protocol, Sequence

from modules.userscript import Userscript


class Injection(NamedTuple):
    userscript: Userscript
    nonce: Optional[str]


class HeaderCollection(Protocol):
    def __contains__(self, key: object) -> bool:
        ...

    def __delitem__(self, key: str) -> None:
        ...

    def get_all(self, key: str) -> list[str]:
        ...

    def set_all(self, key: str, values: list[str]) -> None:
        ...


@dataclass
class Directive:
    name: str
    values: list[str]


CSP_HEADER = "Content-Security-Policy"

SCRIPT_DIRECTIVE_CHAIN = ("script-src-elem", "script-src", "default-src")
HASH_PREFIXES = ("'sha256-", "'sha384-", "'sha512-")


def parsePolicy(cspHeaderValue: str) -> list[Directive]:
    directives: list[Directive] = []
    for rawDirective in cspHeaderValue.split(";"):
        rawDirective = rawDirective.strip()
        if not rawDirective:
            continue
        parts = rawDirective.split()
        directives.append(Directive(parts[0], parts[1:]))
    return directives


def serializePolicy(directives: Sequence[Directive]) -> str:
    serialized: list[str] = []
    for directive in directives:
        if directive.values:
            serialized.append(directive.name + " " + " ".join(directive.values))
        else:
            serialized.append(directive.name)
    return "; ".join(serialized)


def _firstDirective(
    directives: Sequence[Directive],
    name: str,
) -> Optional[Directive]:
    normalizedName = name.lower()
    return next(
        (d for d in directives if d.name.lower() == normalizedName),
        None,
    )


def _effectiveScriptDirective(
    directives: Sequence[Directive],
) -> Optional[Directive]:
    for name in SCRIPT_DIRECTIVE_CHAIN:
        directive = _firstDirective(directives, name)
        if directive is not None:
            return directive
    return None


def effectiveScriptSources(cspHeaderValue: str) -> Optional[list[str]]:
    directive = _effectiveScriptDirective(parsePolicy(cspHeaderValue))
    return None if directive is None else list(directive.values)


def _isNonceOrHash(sourceExpression: str) -> bool:
    normalized = sourceExpression.lower()
    return (
        normalized.startswith("'nonce-")
        or normalized.startswith(HASH_PREFIXES)
    )


def _hasNonceOrHash(sources: Sequence[str]) -> bool:
    return any(_isNonceOrHash(source) for source in sources)


def _hasKeyword(sources: Sequence[str], keyword: str) -> bool:
    lowered = keyword.lower()
    return any(source.lower() == lowered for source in sources)


def _policyAllowsInlineScript(
    directives: Sequence[Directive],
    nonce: Optional[str],
) -> bool:
    directive = _effectiveScriptDirective(directives)
    if directive is None:
        return True
    sources = directive.values
    if nonce is not None and f"'nonce-{nonce}'" in sources:
        return True
    if _hasKeyword(sources, "'strict-dynamic'"):
        return False
    return (
        _hasKeyword(sources, "'unsafe-inline'")
        and not _hasNonceOrHash(sources)
    )


def policyAllowsInlineScript(
    cspHeaderValue: str,
    nonce: Optional[str],
) -> bool:
    return _policyAllowsInlineScript(parsePolicy(cspHeaderValue), nonce)


def _policyCanSafelyAddNonce(
    directives: Sequence[Directive],
) -> bool:
    directive = _effectiveScriptDirective(directives)
    if directive is None:
        return True
    sources = directive.values
    return not (
        _hasKeyword(sources, "'strict-dynamic'")
        and not _hasNonceOrHash(sources)
    )


def policyCanSafelyAddNonce(cspHeaderValue: str) -> bool:
    return _policyCanSafelyAddNonce(parsePolicy(cspHeaderValue))


def reusableNonce(
    policies: Sequence[str],
    candidates: Sequence[str],
) -> Optional[str]:
    for nonce in candidates:
        if nonce and all(
            policyAllowsInlineScript(policy, nonce)
            for policy in policies
        ):
            return nonce
    return None


def nonceCandidates(soup: Any) -> list[str]:
    candidates: list[str] = []
    for tag in soup.find_all("script"):
        nonce = tag.get("nonce")
        if isinstance(nonce, str) and nonce and nonce not in candidates:
            candidates.append(nonce)
    return candidates


def chooseInlineNonce(
    policies: Sequence[str],
    candidates: Sequence[str],
) -> str:
    nativeNonce = reusableNonce(policies, candidates)
    if nativeNonce is not None:
        return nativeNonce
    return generateNonce()


def _removeNoneWhenAddingSource(values: Sequence[str]) -> list[str]:
    return [value for value in values if value.lower() != "'none'"]


def _appendSource(
    directives: list[Directive],
    sourceExpression: str,
) -> None:
    directive = _effectiveScriptDirective(directives)
    if directive is None:
        return

    if sourceExpression in directive.values:
        return

    if directive.name.lower() == "default-src":
        values = _removeNoneWhenAddingSource(directive.values)
        values.append(sourceExpression)
        directives.append(Directive("script-src", values))
        return

    directive.values = _removeNoneWhenAddingSource(directive.values)
    directive.values.append(sourceExpression)


def headerWithScriptsAllowed(
    cspHeaderValue: str,
    injections: Sequence[Injection],
) -> str:
    if not injections:
        return cspHeaderValue

    directives = parsePolicy(cspHeaderValue)
    for injection in injections:
        if injection.nonce is not None:
            if _policyAllowsInlineScript(directives, injection.nonce):
                continue
            if not _policyCanSafelyAddNonce(directives):
                continue
        _appendSource(directives, source(injection))
    return serializePolicy(directives)


def headerValuesWithScriptsAllowed(
    cspHeaderValues: Sequence[str],
    injections: Sequence[Injection],
) -> list[str]:
    return [
        headerWithScriptsAllowed(headerValue, injections)
        for headerValue in cspHeaderValues
    ]


def enforcingPolicyValues(
    headers: HeaderCollection,
    soup: Any,
) -> list[str]:
    return headers.get_all(CSP_HEADER) + metaPolicyValues(soup)


def rewriteCspHeaders(
    headers: HeaderCollection,
    bypassMode: str,
    injections: Sequence[Injection],
) -> None:
    if not injections:
        return
    headerValues = headers.get_all(CSP_HEADER)
    if not headerValues:
        return

    if bypassMode == "everything":
        del headers[CSP_HEADER]
    elif bypassMode == "script":
        headers.set_all(
            CSP_HEADER,
            headerValuesWithScriptsAllowed(headerValues, injections),
        )
    elif bypassMode == "nothing":
        return
    else:
        raise ValueError(f"Unknown CSP bypass mode: {bypassMode}")


def _metaPolicyTags(soup: Any) -> list[Any]:
    tags: list[Any] = []
    head = soup.find("head")
    if head is None:
        return tags
    for tag in head.find_all("meta"):
        httpEquiv = tag.get("http-equiv")
        content = tag.get("content")
        if (
            isinstance(httpEquiv, str)
            and httpEquiv.lower() == "content-security-policy"
            and isinstance(content, str)
        ):
            tags.append(tag)
    return tags


def metaPolicyValues(soup: Any) -> list[str]:
    return [tag["content"] for tag in _metaPolicyTags(soup)]


def rewriteMetaPolicies(
    soup: Any,
    bypassMode: str,
    injections: Sequence[Injection],
) -> None:
    if not injections:
        return
    tags = _metaPolicyTags(soup)
    if bypassMode == "everything":
        for tag in tags:
            tag.decompose()
    elif bypassMode == "script":
        for tag in tags:
            tag["content"] = headerWithScriptsAllowed(
                tag["content"],
                injections,
            )
    elif bypassMode == "nothing":
        return
    else:
        raise ValueError(f"Unknown CSP bypass mode: {bypassMode}")


def source(injection: Injection) -> str:
    if injection.nonce is not None:
        return f"'nonce-{injection.nonce}'"
    downloadURL = injection.userscript.downloadURL
    if downloadURL is None:
        raise ValueError("A linked userscript requires a download URL")
    return downloadURL


def generateNonce() -> str:
    return secrets.token_hex()
