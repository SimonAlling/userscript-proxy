import re
from string import Template
from functools import reduce
import warnings

class MetadataError(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)


tag_name = "name"
tag_type = "type"
tag_unique = "unique"
tag_default = "default"
tag_required = "required"
tag_predicate = "predicate"


PREFIX_COMMENT = "//"
PREFIX_TAG = "@"
BLOCK_START = "==UserScript=="
BLOCK_END = "==/UserScript=="


REGEX_EMPTY_LINE_COMMENT = re.compile(r"^(?:\/\/)?\s*$")
REGEX_METADATA_BLOCK = re.compile(
    PREFIX_COMMENT + r"\s*" + BLOCK_START + r"\n"
    + r"(.*)"
    + PREFIX_COMMENT + r"\s*" + BLOCK_END,
    re.DOTALL
)
REGEX_METADATA_LINE = re.compile(
    r"^" + PREFIX_COMMENT
    + r"\s*" + PREFIX_TAG
    + r"([^\s]+)(?:\s+?(\S.*)?)?$"
)
INDEX_GROUP_TAGNAME = 1
INDEX_GROUP_TAGVALUE = 2


STRING_ERROR_NO_METADATA_BLOCK = """No metadata block found. The metadata block must follow this format:

    """+PREFIX_COMMENT             +""" ==UserScript==
    """+PREFIX_COMMENT+" "+PREFIX_TAG+"""key    value
    """+PREFIX_COMMENT             +""" ==/UserScript==

It must start with `"""+PREFIX_COMMENT+" "+BLOCK_START+"""` and end with `"""+PREFIX_COMMENT+" "+BLOCK_END+"""`, and every line must be a line comment starting with an @-prefixed tag name, then whitespace, then a tag value (with the exception of boolean directives such as @noframes, which are automatically true if present).

"""

STRING_ERROR_MISSING_TAG = Template("""The """+PREFIX_TAG+"""$tagName metadata directive is required, but was not found.""")

STRING_ERROR_MISSING_VALUE = Template("""The """+PREFIX_TAG+"""$tagName metadata directive requires a value, like so:

    """+PREFIX_COMMENT+" "+PREFIX_TAG+"""$tagName    something

""")

STRING_ERROR_PREDICATE_FAILED = Template("""Detected a """+PREFIX_TAG+"""$tagName metadata directive with an invalid value, namely:

    $tagValue

""")

STRING_WARNING_NO_MATCH = Template("""This metadata line did not match the expected pattern and was ignored:

    $line

""")


def first(tuple):
    (a, b) = tuple
    return a


def second(tuple):
    (a, b) = tuple
    return b


def isSomething(x):
    return x != None


def regex_metadataTag(tag):
    return re.compile(PREFIX_TAG + tag + r"\s+[^\n]*")


class Metadata(object):
    def __init__(self, tags):
        self.METADATA_TAGS = tags

    def extract(self, userscriptContent: str): # raises MetadataError
        match_metadataBlock = REGEX_METADATA_BLOCK.search(userscriptContent)
        if (match_metadataBlock == None):
            raise MetadataError(STRING_ERROR_NO_METADATA_BLOCK)
        return match_metadataBlock.group(1)

    def parse(self, metadataContent: str):
        def parseLine(line):
            match = REGEX_METADATA_LINE.search(line)
            if match == None:
                # if not REGEX_EMPTY_LINE_COMMENT.match(line): # TODO: uncomment when we can handle warnings
                #     warnings.warn(STRING_WARNING_NO_MATCH.substitute(line=line))
                return None
            else:
                tagName = match.group(INDEX_GROUP_TAGNAME)
                tagValue = match.group(INDEX_GROUP_TAGVALUE)
                return (tagName, True if tagValue == None else tagValue) # Boolean metadata tags have no explicit value; if they are present, they are true.

        return list(filter(isSomething,
            map(parseLine, metadataContent.splitlines())
        ))

    def validate(self, metadata): # raises MetadataError
        def tagDeclaration(tagName):
            return next((x for x in self.METADATA_TAGS if x[tag_name] == tagName), None)

        def handleDuplicate(acc, pair):
            (name, val) = pair
            tagDec = tagDeclaration(name)
            if tagDec == None:
                # Unrecognized tag. Just let it pass.
                return acc + [pair]
            else:
                # Recognized tag! Skip it if it is a duplicate of a unique key.
                return acc if tagDec[tag_unique] and name in map(first, acc) else acc + [pair]

        def withoutDuplicates(metadata):
            return reduce(handleDuplicate, metadata, [])

        def withDefaults(metadata):
            return metadata + list(map(lambda tagDec: (tagDec[tag_name], tagDec[tag_default]),
                list(filter(lambda tagDec: tagDec[tag_default] != None and tagDec[tag_name] not in list(map(first, metadata)),
                    self.METADATA_TAGS
                ))
            ))

        def validatePair(pair):
            (tagName, tagValue) = pair
            tagDec = tagDeclaration(tagName)
            if tagDec == None:
                # Unrecognized key.
                return (tagName, tagValue)
            else:
                # Recognized key! Check if it has the correct type.
                tagType = tagDec[tag_type]
                tagPredicate = tagDec[tag_predicate]
                if type(tagValue) is not tagType:
                    if tagType == str:
                        raise MetadataError(STRING_ERROR_MISSING_VALUE.substitute(tagName=tagName))
                if isSomething(tagDec[tag_predicate]):
                    if not tagPredicate(tagValue):
                        raise MetadataError(STRING_ERROR_PREDICATE_FAILED.substitute(tagName=tagName, tagValue=tagValue))
                return (tagName, tagValue)

        def assertRequiredPresent(metadata):
            for tagDec in filter(lambda tagDec: tagDec[tag_required] == True, self.METADATA_TAGS):
                if (tagDec[tag_name] not in map(first, metadata)):
                    raise MetadataError(STRING_ERROR_MISSING_TAG.substitute(tagName=tagDec[tag_name]))
            return metadata

        return list(map(validatePair,
            withDefaults(withoutDuplicates(
                assertRequiredPresent(metadata)
            ))
        ))
