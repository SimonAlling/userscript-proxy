import functools
import re
from string import Template
from typing import Callable, Iterable, Iterator, List, Match, NamedTuple, Optional, Pattern, Tuple, TypeVar, Union

from modules.utilities import first, isSomething, second

class MetadataError(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)


# TYPES
T = TypeVar("T")
Predicate = Callable[[T], bool]
TagValue = Union[str, bool]
MetadataItem = Tuple[str, TagValue]
Metadata = List[MetadataItem]

class Tag_string(NamedTuple):
    name: str
    unique: bool
    default: Optional[str]
    required: bool
    predicate: Optional[Predicate[str]] = None

class Tag_boolean(NamedTuple):
    name: str
    unique: bool
    default: Optional[bool]
    required: bool
    predicate: Optional[Predicate[bool]] = None

Tag = Union[Tag_string, Tag_boolean]


PREFIX_COMMENT: str = "//"
PREFIX_TAG: str = "@"
BLOCK_START: str = "==UserScript=="
BLOCK_END: str = "==/UserScript=="

def tag(name: str) -> str:
    return PREFIX_TAG + name

REGEXGROUP_CONTENT: str = "content"
REGEX_METADATA_BLOCK: Pattern = re.compile(
    PREFIX_COMMENT + r"\s*" + BLOCK_START + r"\n"
    + r"(?P<" + REGEXGROUP_CONTENT + r">.*)"
    + PREFIX_COMMENT + r"\s*" + BLOCK_END,
    re.DOTALL
)
REGEXGROUP_TAGNAME: str = "tagname"
REGEXGROUP_TAGVALUE: str = "tagvalue"
REGEX_METADATA_LINE: Pattern = re.compile(
    r"^\s*" + PREFIX_COMMENT
    + r"\s*" + PREFIX_TAG
    + r"(?P<" + REGEXGROUP_TAGNAME + r">[^\s]+)"
    + r"(?:\s+?(?P<" + REGEXGROUP_TAGVALUE + r">\S.*)?)?$"
)

STRING_ERROR_MISSING_BLOCK: str = f"""No metadata block found. The metadata block must follow this format:

    {PREFIX_COMMENT} {BLOCK_START}
    {PREFIX_COMMENT} {tag("key1")}    value1
    {PREFIX_COMMENT} {tag("key2")}    value2
    {PREFIX_COMMENT} ...
    {PREFIX_COMMENT} {tag("keyN")}    valueN
    {PREFIX_COMMENT} {BLOCK_END}

It must start with `{PREFIX_COMMENT} {BLOCK_START}` and end with `{PREFIX_COMMENT} {BLOCK_END}`, and every line must be a line comment starting with an {PREFIX_TAG}-prefixed tag name, then whitespace, then a tag value (with the exception of boolean directives such as {tag("noframes")}, which are automatically true if present).

"""

STRING_ERROR_INVALID_BLOCK: Template = Template(f"""Invalid metadata block. Only comments are allowed, and each line should follow this format:

    {PREFIX_COMMENT} {tag("key")}    value

This line does not:

    $line

""")

STRING_ERROR_MISSING_TAG: Template = Template(f"""The {tag("$tagName")} metadata directive is required, but was not found.""")

STRING_ERROR_MISSING_VALUE: Template = Template(f"""The {tag("$tagName")} metadata directive requires a value, like so:

    {PREFIX_COMMENT} {tag("$tagName")}    something

""")

STRING_ERROR_PREDICATE_FAILED: Template = Template(f"""Detected a {tag("$tagName")} metadata directive with an invalid value, namely:

    $tagValue

""")


def isWhitespaceLine(s: str) -> bool:
    return isSomething(re.compile(r"^\s*$").match(s))

def isCommentLine(s: str) -> bool:
    return isSomething(re.compile(r"^\s*" + PREFIX_COMMENT + r".*$").match(s))

def extract(userscriptContent: str) -> str: # raises MetadataError
    match_metadataBlock: Optional[Match] = REGEX_METADATA_BLOCK.search(userscriptContent)
    if (match_metadataBlock is None):
        raise MetadataError(STRING_ERROR_MISSING_BLOCK)
    block: str = match_metadataBlock.group(REGEXGROUP_CONTENT)
    for line in block.splitlines():
        if not isWhitespaceLine(line) and not isCommentLine(line) and not REGEX_METADATA_LINE.match(line):
            raise MetadataError(STRING_ERROR_INVALID_BLOCK.substitute(line=line))
    return block


def parse(metadataContent: str) -> Metadata:
    def parseLine(line: str) -> Optional[MetadataItem]:
        match: Optional[Match] = REGEX_METADATA_LINE.search(line)
        if match is None:
            return None
        else:
            tagName: str = match.group(REGEXGROUP_TAGNAME)
            tagValue: Optional[str] = match.group(REGEXGROUP_TAGVALUE)
            # Boolean tags have no explicit value; if they are present, they are true:
            if tagValue is None:
                return (tagName, True)
            else:
                return (tagName, tagValue)

    # filter did not play well with mypy:
    parsedItems: Metadata = []
    for item in map(parseLine, metadataContent.splitlines()):
        if item is not None:
            parsedItems.append(item)
    return parsedItems


def tagByName(tags: List[Tag], tagName: str) -> Optional[Tag]:
    return next((x for x in tags if x.name == tagName), None)


def validatePair(tags: List[Tag], pair: MetadataItem) -> MetadataItem:
    (tagName, tagValue) = pair
    tag: Optional[Tag] = tagByName(tags, tagName)
    if tag is None:
        # Unrecognized key.
        return (tagName, tagValue)
    else:
        # Recognized key! Check if it has the correct type.
        tagPredicate: Optional[Predicate] = tag.predicate
        if type(tag) is Tag_string and type(tagValue) is not str:
            raise MetadataError(STRING_ERROR_MISSING_VALUE.substitute(tagName=tagName))
        if type(tag) is Tag_boolean:
            tagValue = tagValue is not False # This handles cases like `@noframes blabla`; a boolean directive is true no matter what comes after it.
        if tagPredicate is not None:
            if not tagPredicate(tagValue):
                raise MetadataError(STRING_ERROR_PREDICATE_FAILED.substitute(tagName=tagName, tagValue=str(tagValue)))
        return (tagName, tagValue)


def validate(tags: List[Tag], metadata: Metadata) -> Metadata: # raises MetadataError
    def handleDuplicate(acc: Iterable[MetadataItem], pair: MetadataItem) -> Iterable[MetadataItem]:
        name: str = first(pair)
        tag: Optional[Tag] = tagByName(tags, name)
        seenTagNames: Iterator[str] = map(first, acc)
        # Throw away pair if it has the same tag name as some already seen, known, unique directive:
        return acc if tag is not None and tag.unique and name in seenTagNames else list(acc) + [pair]

    def withoutDuplicates(metadata: Metadata) -> Metadata:
        empty: Iterable[Tuple[str, Union[str, bool]]] = [] # to satisfy mypy
        return list(functools.reduce(handleDuplicate, metadata, empty))

    # Awkwardly written to satisfy mypy:
    def withDefaults(metadata: Metadata) -> Metadata:
        tagNamesThatWeHave: List[str] = list(map(first, metadata))
        unseenItems = map(
            lambda tag: (tag.name, tag.default),
            filter(
                lambda tag: tag.name not in tagNamesThatWeHave,
                tags
            )
        )
        neededDefaults: Metadata = []
        for (tagName, default) in unseenItems:
            if default is not None:
                neededDefaults.append((tagName, default))
        return metadata + neededDefaults

    def assertRequiredPresent(metadata: Metadata) -> Metadata:
        ourTagNames: Iterator[str] = map(first, metadata)
        requiredTags: Iterator[Tag] = filter(lambda tag: tag.required, tags)
        for tag in requiredTags:
            if (tag.name not in ourTagNames):
                raise MetadataError(STRING_ERROR_MISSING_TAG.substitute(tagName=tag.name))
        return metadata

    return list(map(
        lambda *args: validatePair(tags, *args),
        withDefaults(withoutDuplicates(
            assertRequiredPresent(metadata)
        ))
    ))


def validator(tags: List[Tag]) -> Callable[[Metadata], Metadata]:
    return lambda metadata: validate(tags, metadata)


def valueGetter_all(metadata: Metadata) -> Callable[[Tag], List[TagValue]]:
    return lambda tag: [second(pair) for pair in metadata if first(pair) == tag.name]


def valueGetter_one(metadata: Metadata) -> Callable[[Tag], Optional[TagValue]]:
    v = valueGetter_all(metadata)
    return lambda tag: None if len(v(tag)) == 0 else v(tag)[0]
