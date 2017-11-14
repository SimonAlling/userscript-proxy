from typing import Tuple, List, Pattern, Match, Optional, Union, Callable, NamedTuple
import re
from string import Template
from functools import reduce
from utilities import A, B, first, second, isSomething
import warnings

class MetadataError(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)


TagValue = Union[str, bool]
Predicate = Optional[Callable[[TagValue], bool]]
TagDeclaration = NamedTuple("TagDeclaration", [
    ("name", str),
    ("type", type),
    ("unique", bool),
    ("default", Optional[TagValue]),
    ("required", bool),
    ("predicate", Predicate),
])

MetadataItem = Tuple[str, TagValue]
TMetadata = List[MetadataItem]

PREFIX_COMMENT: str = "//"
PREFIX_TAG: str = "@"
BLOCK_START: str = "==UserScript=="
BLOCK_END: str = "==/UserScript=="


REGEX_EMPTY_LINE_COMMENT: Pattern = re.compile(r"^(?:\/\/)?\s*$")
REGEX_METADATA_BLOCK: Pattern = re.compile(
    PREFIX_COMMENT + r"\s*" + BLOCK_START + r"\n"
    + r"(.*)"
    + PREFIX_COMMENT + r"\s*" + BLOCK_END,
    re.DOTALL
)
REGEX_METADATA_LINE: Pattern = re.compile(
    r"^" + PREFIX_COMMENT
    + r"\s*" + PREFIX_TAG
    + r"([^\s]+)(?:\s+?(\S.*)?)?$"
)
INDEX_GROUP_TAGNAME: int = 1
INDEX_GROUP_TAGVALUE: int = 2


def f(s: str) -> str:
    # Instead of f"bar" which requires Python 3.6.
    # Uses globals() in a possibly confusing or dangerous way; be careful!
    return s.format(**globals())

STRING_ERROR_NO_METADATA_BLOCK: str = f("""No metadata block found. The metadata block must follow this format:

    {PREFIX_COMMENT} {BLOCK_START}
    {PREFIX_COMMENT} {PREFIX_TAG}key    value
    {PREFIX_COMMENT} {BLOCK_END}

It must start with `{PREFIX_COMMENT} {BLOCK_START}` and end with `{PREFIX_COMMENT} {BLOCK_END}`, and every line must be a line comment starting with an {PREFIX_TAG}-prefixed tag name, then whitespace, then a tag value (with the exception of boolean directives such as {PREFIX_TAG}noframes, which are automatically true if present).

""")

STRING_ERROR_MISSING_TAG: Template = Template(f("""The {PREFIX_TAG}$tagName metadata directive is required, but was not found."""))

STRING_ERROR_MISSING_VALUE: Template = Template(f("""The {PREFIX_TAG}$tagName metadata directive requires a value, like so:

    {PREFIX_COMMENT} {PREFIX_TAG}$tagName    something

"""))

STRING_ERROR_PREDICATE_FAILED: Template = Template(f("""Detected a {PREFIX_TAG}$tagName metadata directive with an invalid value, namely:

    $tagValue

"""))

STRING_WARNING_NO_MATCH: Template = Template(f("""This metadata line did not match the expected pattern and was ignored:

    $line

"""))


def regex_metadataTag(tag: str) -> Pattern:
    return re.compile(PREFIX_TAG + tag + r"\s+[^\n]*")


class Metadata(object):
    def __init__(self, tags: List[TagDeclaration]) -> None:
        self.METADATA_TAGS: List[TagDeclaration] = tags

    def extract(self, userscriptContent: str) -> str: # raises MetadataError
        match_metadataBlock: Optional[Match] = REGEX_METADATA_BLOCK.search(userscriptContent)
        if (match_metadataBlock == None):
            raise MetadataError(STRING_ERROR_NO_METADATA_BLOCK)
        return match_metadataBlock.group(1)

    def parse(self, metadataContent: str) -> TMetadata:
        def parseLine(line: str) -> Optional[Tuple[str, TagValue]]:
            match: Optional[Match] = REGEX_METADATA_LINE.search(line)
            if match == None:
                # if not REGEX_EMPTY_LINE_COMMENT.match(line): # TODO: uncomment when we can handle warnings
                #     warnings.warn(STRING_WARNING_NO_MATCH.substitute(line=line))
                return None
            else:
                tagName: str = match.group(INDEX_GROUP_TAGNAME)
                tagValue: Optional[str] = match.group(INDEX_GROUP_TAGVALUE)
                return (tagName, True if tagValue == None else tagValue) # Boolean metadata tags have no explicit value; if they are present, they are true.

        return list(filter(isSomething,
            map(parseLine, metadataContent.splitlines())
        ))

    def validate(self, metadata: TMetadata) -> TMetadata: # raises MetadataError
        def tagDeclaration(tagName: str) -> Optional[TagDeclaration]:
            return next((x for x in self.METADATA_TAGS if x.name == tagName), None)

        def handleDuplicate(acc: TMetadata, pair: MetadataItem) -> TMetadata:
            (name, val) = pair
            tagDec: TagDeclaration = tagDeclaration(name)
            if tagDec == None:
                # Unrecognized tag. Just let it pass.
                return acc + [pair]
            else:
                # Recognized tag! Skip it if it is a duplicate of a unique key.
                seenTagNames: List[str] = list(map(first, acc))
                return acc if tagDec.unique and name in seenTagNames else acc + [pair]

        def withoutDuplicates(metadata: TMetadata) -> TMetadata:
            return reduce(handleDuplicate, metadata, [])

        def withDefaults(metadata: TMetadata) -> TMetadata:
            tagNamesThatWeHave: List[str] = list(map(first, metadata))
            def hasDefaultAndNotAlreadyParsed(tagDec: TagDeclaration) -> bool:
                return isSomething(tagDec.default) and tagDec.name not in tagNamesThatWeHave
            neededDefaults: TMetadata = list(map(
                lambda tagDec: (tagDec.name, tagDec.default),
                list(filter(
                    hasDefaultAndNotAlreadyParsed,
                    self.METADATA_TAGS
                ))
            ))
            return metadata + neededDefaults

        def validatePair(pair: MetadataItem) -> MetadataItem:
            (tagName, tagValue) = pair
            tagDec: TagDeclaration = tagDeclaration(tagName)
            if tagDec == None:
                # Unrecognized key.
                return (tagName, tagValue)
            else:
                # Recognized key! Check if it has the correct type.
                tagType: type = tagDec.type
                tagPredicate: Predicate = tagDec.predicate
                if type(tagValue) is not tagType:
                    if tagType == str:
                        raise MetadataError(STRING_ERROR_MISSING_VALUE.substitute(tagName=tagName))
                if isSomething(tagDec.predicate):
                    if not tagPredicate(tagValue):
                        raise MetadataError(STRING_ERROR_PREDICATE_FAILED.substitute(tagName=tagName, tagValue=str(tagValue)))
                return (tagName, tagValue)

        def assertRequiredPresent(metadata: TMetadata) -> TMetadata:
            ourTagNames: List[str] = list(map(first, metadata))
            tagDecls_required: List[TagDeclaration] = list(filter(lambda tagDec: tagDec.required== True, self.METADATA_TAGS))
            for tagDec in tagDecls_required:
                if (tagDec.name not in ourTagNames):
                    raise MetadataError(STRING_ERROR_MISSING_TAG.substitute(tagName=tagDec.name))
            return metadata

        return list(map(validatePair,
            withDefaults(withoutDuplicates(
                assertRequiredPresent(metadata)
            ))
        ))
