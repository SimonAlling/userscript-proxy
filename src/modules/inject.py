from typing import NamedTuple, Union

from bs4 import BeautifulSoup, Tag

import modules.constants as C
import modules.userscript as userscript
from modules.userscript import Userscript, document_end, document_idle
from modules.utilities import fromOptional, idem, stripIndentation

class Options(NamedTuple):
    inline: bool


def inject(script: Userscript, soup: BeautifulSoup, options: Options) -> Union[BeautifulSoup, Exception]:
    useInline = options.inline or script.downloadURL is None
    tag = soup.new_tag("script")
    tag[C.ATTRIBUTE_UP_VERSION] = C.VERSION
    withLoadListenerIfRunAtIdle = userscript.withEventListener("load") if script.runAt == document_idle else idem
    withNoframesIfNoframes = userscript.withNoframes if script.noframes else idem
    try:
        if useInline:
            tag.string = "\n" + withNoframesIfNoframes(withLoadListenerIfRunAtIdle(script.content))
            if script.runAt == document_end:
                insertLateIn(soup, tag)
            else:
                insertEarlyIn(soup, tag)
        else:
            s = "s" # JS variable name
            src = userscript.withVersionSuffix(script.downloadURL, script.version)
            JS_insertScriptTag = f"""document.head.appendChild({s});"""
            JS_insertionCode = (stripIndentation(f"""
                const {s} = document.createElement("script");
                {s}.setAttribute("{C.ATTRIBUTE_UP_VERSION}", "{C.VERSION}");
                {s}.src = "{src}";
                {withLoadListenerIfRunAtIdle(JS_insertScriptTag)}
            """))
            if script.runAt == document_idle or script.noframes:
                tag.string = withNoframesIfNoframes(JS_insertionCode)
            else:
                tag["src"] = src
            # Tag prepared. Insert it:
            if script.runAt == document_end:
                insertLateIn(soup, tag)
            else:
                insertEarlyIn(soup, tag)
        return soup
    except Exception as e:
        return e



def insertEarlyIn(soup: BeautifulSoup, tag: Tag):
    if soup.body is not None and soup.body.find() is not None:
        soup.body.find().insert_before(tag)
    elif soup.title is not None:
        soup.title.insert_after(tag)
    elif soup.find() is not None:
        soup.find().insert_after(tag) # after first element
    else:
        soup.append(tag)


def insertLateIn(soup: BeautifulSoup, tag: Tag):
    fromOptional(soup.body, soup).append(tag)
